"""Host reference pipeline; no hardware control, radio or MCU firmware."""
import hashlib
import json
import sqlite3

import numpy as np

from reliable_outbox import encode
from sampling_quality_runtime import SamplingNode
from streaming_rapid_runtime import StreamingRapid


class Monitor:
    def __init__(self, reference, limits, run_id, healthy_reference_approved=False):
        if not run_id:
            raise ValueError('A stable run identity is required')
        self.node = SamplingNode(reference, limits, period=1, phase=0, quality='range')
        self.rapid = StreamingRapid(reference)
        self.run_id = run_id
        self.approved = bool(healthy_reference_approved)
        self.events = []
        self.records = []
        self.last_quality = None

    def update(self, t, count, pressure):
        main = self.node.update(t, count, pressure)
        short = self.rapid.update(t, count, pressure, self.node.context if t == 129 else None)
        if t < 130:
            return None, []
        if not self.approved:
            quality = 'healthy_reference_unconfirmed'
        else:
            quality = main['status']
        enabled = self.approved and self.node.context is not None
        new = []

        def event(kind, **details):
            e = dict(event_id=f'{self.run_id}:{t}:{len(new)}:{kind}', t_s=t, kind=kind, **details)
            new.append(e)

        if quality != self.last_quality:
            event('quality_transition', previous=self.last_quality, current=quality)
            self.last_quality = quality
        if enabled:
            for e in self.rapid.events[-1:]:
                if e['t_s'] == t:
                    event('rapid_review')
            for e in self.node.state['guarded_fast']['events'][-1:]:
                if e['t_s'] == t:
                    event(e['pattern'])
            for e in self.node.quality_events[-1:]:
                if e['t_s'] == t:
                    event('measurement_quality', reason=e['reason'])
        state = self.node.state['guarded_fast']
        label = state['active'] if enabled and main['valid'] and state['pending'] == state['active'] and state['count'] >= 5 else 0
        pattern = {0: 'no_current_evidence', 1: 'leak_pattern', 2: 'restriction_pattern', 3: 'uncertain'}[label]
        if quality != 'valid':
            pattern = 'unavailable'
        record = dict(t_s=t, run_id=self.run_id,
                      pressure_kpa=[float(v) if np.isfinite(v) else None for v in pressure],
                      cumulative_pulses=int(count), flow_q10_l_min=main['flow_q10'],
                      measurement_status=quality, numeric_baseline_available=self.node.context is not None,
                      healthy_reference_approved=self.approved,
                      rapid_window_valid=bool(enabled and short is not None and short['valid']),
                      rapid_attention_active=bool(enabled and short is not None and self.rapid.active),
                      diagnostic_pattern=pattern, physical_valve_verified=False)
        self.records.append(record)
        self.events.extend(new)
        return record, new


class PacketReceiver:
    """Persist the full JSON body and events in one transaction before ACK.

    One sender packet-ID namespace. Old packets remain historical records;
    latest_sample uses acquisition time, never arrival order.
    """
    def __init__(self, path=':memory:'):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL, received INTEGER NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, payload TEXT NOT NULL, received INTEGER NOT NULL)')
        self.db.commit()

    def accept(self, packet, t):
        pid = packet['packet_id']
        body = packet['payload']
        json.dumps(body, allow_nan=False)
        text = encode(body)
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        sample = body['sample']
        if sample['run_id'] != body['run_id']:
            raise ValueError('Sample identity differs from packet identity')
        with self.db:
            old = self.db.execute('SELECT digest FROM receipts WHERE id=?', (pid,)).fetchone()
            if old and old[0] != digest:
                raise ValueError('Conflicting packet contents')
            if old is None:
                self.db.execute('INSERT INTO receipts VALUES(?,?,?,?)', (pid, digest, text, t))
            for e in body['events']:
                if not e['event_id'].startswith(body['run_id'] + ':'):
                    raise ValueError('Event identity differs from packet identity')
                payload = encode(e)
                previous = self.db.execute('SELECT payload FROM events WHERE id=?', (e['event_id'],)).fetchone()
                if previous and previous[0] != payload:
                    raise ValueError('Conflicting event contents')
                if previous is None:
                    self.db.execute('INSERT INTO events VALUES(?,?,?)', (e['event_id'], payload, t))
        return pid

    def events(self):
        return [dict(event=json.loads(p), received=t) for p, t in
                self.db.execute('SELECT payload,received FROM events ORDER BY id')]

    def packets(self):
        return [dict(packet_id=pid, payload=json.loads(p), received=t) for pid, p, t in
                self.db.execute('SELECT id,payload,received FROM receipts ORDER BY id')]

    def latest_sample(self):
        packets = self.packets()
        return max((p['payload']['sample'] for p in packets), key=lambda s: s['t_s'], default=None)

    def monitor_view(self, now, max_sample_age_s=65):
        sample = self.latest_sample()
        if sample is None:
            return dict(sample=None, sample_age_s=None, data_fresh=False, remote_status='no_data')
        age = now - sample['t_s']
        if age < 0 or max_sample_age_s < 0:
            raise ValueError('Acquisition and observation clocks must share the test time base')
        fresh = age <= max_sample_age_s
        return dict(sample=sample, sample_age_s=age, data_fresh=fresh,
                    remote_status=sample['measurement_status'] if fresh else 'stale')

    def close(self):
        self.db.close()
