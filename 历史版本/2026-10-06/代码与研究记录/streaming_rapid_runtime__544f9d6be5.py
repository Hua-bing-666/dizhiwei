"""Causal three-second attention reference, using current samples only."""
from collections import deque

import numpy as np

from review_hybrid_sampling import residual
from sampling_quality_runtime import mad


class StreamingRapid:
    def __init__(self, reference):
        self.reference = reference
        self.clock = -1
        self.history = deque(maxlen=4)
        self.calibration = []
        self.calibration_bad = False
        self.baseline = None
        self.threshold = None
        self.scale = None
        self.pending = 0
        self.active = False
        self.records = []
        self.events = []

    def update(self, t, count, pressure, baseline=None):
        if t != self.clock + 1:
            raise ValueError('Input timestamps must advance by one second')
        self.clock = t
        p = np.asarray(pressure, dtype=float)
        if p.shape != (2,):
            raise ValueError('Two pressure readings required')
        self.history.append((t, int(count), p.copy()))
        valid = False
        meanp = None
        q = None
        if len(self.history) == 4:
            counts = np.array([v[1] for v in self.history])
            pp = np.array([v[2] for v in list(self.history)[1:]])
            q = 60 * (counts[-1] - counts[0]) / (540 * 3)
            valid = bool(np.all(np.isfinite(pp)) and np.all((pp >= 0) & (pp <= 200))
                         and np.all(pp[:, 1] > 10) and np.all(np.diff(counts) >= 0) and q > .5)
            if valid:
                meanp = pp.mean(axis=0)
        if 20 <= t < 120:
            if valid:
                self.calibration.append((meanp.copy(), q))
            else:
                self.calibration_bad = True
        if t == 129 and baseline is not None and not self.calibration_bad and len(self.calibration) == 100:
            self.baseline = dict(baseline)
            x = np.array([residual(*p0, q0, self.reference, baseline['gain'], baseline['r0'])
                          for p0, q0 in self.calibration])
            self.scale = np.maximum(mad(x, axis=0), [.003, .03])
            self.threshold = np.maximum([.06, .6], 6 * self.scale)
        if t < 130 or self.threshold is None:
            return None
        x = residual(*meanp, q, self.reference, self.baseline['gain'], self.baseline['r0']) if valid else np.zeros(2)
        positive = bool(valid and np.any(x > self.threshold))
        if positive:
            self.pending += 1
        else:
            self.pending = 0
            self.active = False
        if self.pending >= 2 and not self.active:
            self.events.append(dict(t_s=t, kind='rapid_review'))
            self.active = True
        record = dict(t=t, valid=valid, x=x.tolist(), attention=positive)
        self.records.append(record)
        return record
