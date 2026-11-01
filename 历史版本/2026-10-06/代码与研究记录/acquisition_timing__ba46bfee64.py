"""Timing guard and 16-bit counter model; no ADC or interrupt hardware."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PressureRead:
    started_ms: float
    completed_ms: float
    value_kpa: float
    ready: bool = True


class TimingGuard:
    def __init__(self):
        self.last_endpoint = None
        self.last_completed = [-math.inf, -math.inf]

    def frame(self, endpoint_ms, latch_ms, reads):
        if not isinstance(endpoint_ms,int) or endpoint_ms <= 0 or endpoint_ms % 1000 or len(reads) != 2:
            raise ValueError('Two reads and a positive one-second endpoint required')
        if self.last_endpoint is not None and endpoint_ms != self.last_endpoint + 1000:
            raise ValueError('Missing timer endpoint requires explicit session/window reset')
        self.last_endpoint = endpoint_ms
        problems = []
        if not math.isfinite(latch_ms) or abs(latch_ms-endpoint_ms) > 1:
            problems.append('late_counter_latch')
        pressure = []
        ages = []
        for channel, read in enumerate(reads):
            valid = (read.ready and math.isfinite(read.value_kpa)
                     and endpoint_ms-30 <= read.started_ms <= read.completed_ms <= endpoint_ms
                     and read.completed_ms > self.last_completed[channel])
            if valid:
                pressure.append(read.value_kpa)
                ages.append(round(endpoint_ms-read.completed_ms))
            else:
                pressure.append(None)
                ages.append(255)
                problems.append(f'pressure{channel}_timing_or_missing')
            # Completed timestamp remains evidence; repeated old samples cannot pass.
            if math.isfinite(read.completed_ms):
                self.last_completed[channel] = max(self.last_completed[channel], read.completed_ms)
        if reads[0].completed_ms > reads[1].started_ms:
            problems.append('overlapping_mux_conversions')
        if problems:
            pressure = [None,None]
            ages = [255,255]
        return dict(endpoint_ms=endpoint_ms,pressure_kpa=pressure,ages_ms=ages,
                    timing_valid=not problems,reasons=problems)


class Counter16:
    def __init__(self, max_pulses_per_second=45):
        if max_pulses_per_second <= 0:
            raise ValueError('A positive bounded rate is required')
        self.last_raw = 0
        self.last_time = 0
        self.total = 0
        self.maximum = max_pulses_per_second

    def snapshot(self, raw, time_ms):
        if not isinstance(raw,int) or not 0 <= raw < 65536 or time_ms <= self.last_time:
            raise ValueError('Invalid counter snapshot')
        elapsed = time_ms-self.last_time
        bound = math.ceil(self.maximum*elapsed/1000)+2
        if bound >= 65536:
            raise ValueError('Snapshot interval cannot disambiguate counter wraps')
        delta = (raw-self.last_raw) % 65536
        if delta > bound:
            raise ValueError('Counter discontinuity; reset/re-enrolment requires explicit handling')
        if self.total+delta >= 2**32:
            raise OverflowError('Counter width exhausted; explicit new measurement session required')
        self.total += delta
        self.last_raw,self.last_time = raw,time_ms
        return self.total


def nominal_schedule(endpoint_ms, rate_factor=1., extra_ms=0.):
    # Datasheet: conversion 1/DR. 0.36ms config + 0.45ms result read and
    # 0.18ms one readiness transaction at the candidate 100kHz I2C clock.
    conversion = 1000/(128*rate_factor)+.025
    slot = .36+conversion+.18+.45+extra_ms
    start = endpoint_ms-30
    first = PressureRead(start,start+slot,120.)
    second = PressureRead(start+slot,start+2*slot,110.)
    return [first,second]
