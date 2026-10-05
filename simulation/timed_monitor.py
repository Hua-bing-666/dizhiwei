"""Adapt rejected timing to actual missing inputs, retaining prior algorithms."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'prototype'))
from integrated_monitor import Monitor
from acquisition_timing import TimingGuard


class TimedMonitor:
    def __init__(self, reference, limits, run_id, approved):
        self.monitor = Monitor(reference,limits,run_id,approved)
        self.guard = TimingGuard()
        self.timing_records = []

    def update(self, t, count, latch_ms, reads):
        endpoint = (t+1)*1000
        timing = self.guard.frame(endpoint,latch_ms,reads)
        pressures = [float('nan') if v is None else v for v in timing['pressure_kpa']]
        record,events = self.monitor.update(t,count,pressures)
        if not timing['timing_valid']:
            for event in events:
                if event['kind'] == 'measurement_quality':
                    event['reason'] = 'timing_fault'
        if 'late_counter_latch' in timing['reasons']:
            # Exclude the untrusted counter endpoint, including as a future
            # window's start. Never retain a late endpoint to estimate Q10.
            self.monitor.node.counts.clear()
            self.monitor.rapid.history.clear()
            if record is not None:
                record['flow_q10_l_min'] = None
        timing['sample_index'] = t
        self.timing_records.append(timing)
        return record,events,timing
