"""Persistent host session and compact-frame receiver, not Flash/SD code."""
import json
import sqlite3
import struct

from compact_protocol import ACK, EVENT, TELEMETRY, SAMPLE, Frame, Snapshot, decode


def connect(path):
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=DELETE')
    db.execute('PRAGMA synchronous=EXTRA')
    return db


class SessionSender:
    def __init__(self, path, device=1, capacity=16, policy='rapid8'):
        if not 0 < device < 2**32 or capacity < 1:
            raise ValueError('Invalid device or capacity')
        self.device = device
        self.capacity = capacity
        if policy not in ('rapid8','burst_backoff'):
            raise ValueError('Unknown retry policy')
        self.policy = policy
        self.delays = [2000]*8 if policy == 'rapid8' else [2000]*3+[20000]*5
        self.db = connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS meta(device INTEGER PRIMARY KEY, session INTEGER NOT NULL, seq INTEGER NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS pending(device INTEGER, session INTEGER, seq INTEGER, wire BLOB NOT NULL, created_ms INTEGER NOT NULL, due_ms INTEGER NOT NULL, expires_ms INTEGER NOT NULL, attempts INTEGER NOT NULL, state TEXT NOT NULL, priority INTEGER NOT NULL, PRIMARY KEY(device,session,seq))')
        self.db.execute('CREATE TABLE IF NOT EXISTS rejected(device INTEGER, created_ms INTEGER, reason TEXT, payload BLOB)')
        self.db.execute('CREATE TABLE IF NOT EXISTS event_identity(device INTEGER, session INTEGER, sample_seq INTEGER, code INTEGER, detail INTEGER, seq INTEGER, payload BLOB NOT NULL, PRIMARY KEY(device,session,sample_seq,code,detail))')
        self.db.commit()
        try:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.db.execute('SELECT session FROM meta WHERE device=?', (device,)).fetchone()
            self.session = (old[0] if old else 0) + 1
            if self.session >= 2**32:
                raise OverflowError('Session exhausted; explicit re-enrolment required')
            self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?,0)', (device, self.session))
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.db.close()
            raise

    def owner(self):
        if self.db.execute('SELECT session FROM meta WHERE device=?', (self.device,)).fetchone()[0] != self.session:
            raise RuntimeError('Sender superseded by another session owner')

    def enqueue(self, kind, payload, now_ms):
        if kind not in (EVENT, TELEMETRY):
            raise ValueError('Only uplink frames may be queued')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            self.owner()
            source_key = None
            if kind == EVENT:
                snapshot = Snapshot.unpack(payload[:SAMPLE.size])
                code, detail = payload[SAMPLE.size:]
                source_key = (self.device,self.session,snapshot.sample_seq,code,detail)
                old = self.db.execute('SELECT seq,payload FROM event_identity WHERE device=? AND session=? AND sample_seq=? AND code=? AND detail=?', source_key).fetchone()
                if old:
                    if old[1] != payload:
                        raise ValueError('Same local event source, different snapshot')
                    saved = self.db.execute('SELECT wire FROM pending WHERE device=? AND session=? AND seq=?', (self.device,self.session,old[0])).fetchone()
                    self.db.commit()
                    return decode(saved[0])
            count = self.db.execute("SELECT COUNT(*) FROM pending WHERE device=? AND state='pending'", (self.device,)).fetchone()[0]
            if count >= self.capacity:
                self.db.execute('INSERT INTO rejected VALUES(?,?,?,?)', (self.device, now_ms, 'queue_full_keep_existing', payload))
                self.db.commit()
                return None
            seq = self.db.execute('SELECT seq FROM meta WHERE device=?', (self.device,)).fetchone()[0] + 1
            if seq >= 2**32:
                raise OverflowError('Message sequence exhausted')
            frame = Frame(kind, self.device, self.session, seq, payload)
            wire = frame.wire()
            self.db.execute('UPDATE meta SET seq=? WHERE device=?', (seq, self.device))
            self.db.execute('INSERT INTO pending VALUES(?,?,?,?,?,?,?,?,?,?)',
                            (*frame.key, wire, now_ms, now_ms, now_ms+300000, 0, 'pending', int(kind == EVENT)))
            if source_key is not None:
                self.db.execute('INSERT INTO event_identity VALUES(?,?,?,?,?,?,?)', (*source_key,seq,payload))
            self.db.commit()
            return frame
        except Exception:
            self.db.rollback()
            raise

    def pick(self, now_ms, aux_ready=True):
        self.owner()
        with self.db:
            self.db.execute("UPDATE pending SET state='expired' WHERE device=? AND state='pending' AND expires_ms<=?", (self.device, now_ms))
            self.db.execute("UPDATE pending SET state='unconfirmed' WHERE device=? AND state='pending' AND attempts>=8 AND due_ms<=?", (self.device, now_ms))
        if not aux_ready:
            return None
        # Future-due head entries do not prevent dispatch of other eligible entries.
        row = self.db.execute("SELECT session,seq,wire,attempts FROM pending WHERE device=? AND state='pending' AND attempts<8 AND due_ms<=? ORDER BY priority DESC,due_ms,created_ms,session,seq LIMIT 1", (self.device, now_ms)).fetchone()
        if row is None:
            return None
        with self.db:
            self.db.execute('UPDATE pending SET attempts=attempts+1,due_ms=? WHERE device=? AND session=? AND seq=?', (now_ms+self.delays[row[3]], self.device, row[0], row[1]))
        return row[2]

    def acknowledge(self, wire):
        self.owner()
        frame = decode(wire)
        if frame.kind != ACK or frame.device != self.device:
            return False
        old = self.db.execute('SELECT wire,state FROM pending WHERE device=? AND session=? AND seq=?', frame.key).fetchone()
        if old is None or struct.unpack('<I', frame.payload)[0] != decode(old[0]).fingerprint:
            return False
        state = 'acknowledged' if old[1] in ('pending', 'acknowledged') else 'acknowledged_late'
        with self.db:
            self.db.execute('UPDATE pending SET state=? WHERE device=? AND session=? AND seq=?', (state, *frame.key))
        return True

    def states(self):
        return [dict(device=d, session=s, seq=q, attempts=a, state=state) for d,s,q,a,state in
                self.db.execute('SELECT device,session,seq,attempts,state FROM pending WHERE device=? ORDER BY session,seq', (self.device,))]

    def close(self):
        self.db.close()


class SessionReceiver:
    def __init__(self, path):
        self.db = connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS registry(device INTEGER, config INTEGER, reference INTEGER, metadata TEXT NOT NULL, PRIMARY KEY(device,config,reference))')
        self.db.execute('CREATE TABLE IF NOT EXISTS time_maps(device INTEGER, session INTEGER, origin_ms INTEGER, error_ms INTEGER, evidence TEXT, PRIMARY KEY(device,session))')
        self.db.execute('CREATE TABLE IF NOT EXISTS frames(device INTEGER, session INTEGER, seq INTEGER, body BLOB NOT NULL, received_ms INTEGER NOT NULL, PRIMARY KEY(device,session,seq))')
        self.db.execute('CREATE TABLE IF NOT EXISTS samples(device INTEGER, session INTEGER, sample_seq INTEGER, body BLOB NOT NULL, PRIMARY KEY(device,session,sample_seq))')
        self.db.commit()

    def register(self, device, config, reference, metadata):
        text = json.dumps(metadata, ensure_ascii=False, sort_keys=True, allow_nan=False)
        with self.db:
            old = self.db.execute('SELECT metadata FROM registry WHERE device=? AND config=? AND reference=?', (device,config,reference)).fetchone()
            if old and old[0] != text:
                raise ValueError('Configuration/reference identity cannot change contents')
            if old is None:
                self.db.execute('INSERT INTO registry VALUES(?,?,?,?)', (device,config,reference,text))

    def register_time_mapping(self, device, session, origin_ms, error_ms, evidence):
        if error_ms < 0 or not evidence:
            raise ValueError('An explicit independent time-mapping record is required')
        with self.db:
            old = self.db.execute('SELECT origin_ms,error_ms,evidence FROM time_maps WHERE device=? AND session=?', (device,session)).fetchone()
            values = (origin_ms,error_ms,evidence)
            if old and old != values:
                raise ValueError('Immutable time mapping conflict')
            if old is None:
                self.db.execute('INSERT INTO time_maps VALUES(?,?,?,?,?)', (device,session,*values))

    def accept(self, wire, now_ms, crash=None):
        frame = decode(wire)
        if frame.kind not in (EVENT, TELEMETRY):
            raise ValueError('Not an uplink frame')
        snap = Snapshot.unpack(frame.payload[:SAMPLE.size])
        registered = self.db.execute('SELECT metadata FROM registry WHERE device=? AND config=? AND reference=?', (frame.device,snap.config_id,snap.reference_id)).fetchone()
        if registered is None:
            raise ValueError('Unknown configuration/reference; no ACK')
        metadata = json.loads(registered[0])
        if bool(snap.flags & 0x80) != metadata['synthetic'] or bool(snap.flags & 2) != metadata['healthy_reference_approved']:
            raise ValueError('Frame flags conflict with registered evidence')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            old = self.db.execute('SELECT body FROM frames WHERE device=? AND session=? AND seq=?', frame.key).fetchone()
            if old and old[0] != frame.body:
                raise ValueError('Same message identity, different content')
            sample_key = (frame.device,frame.session,snap.sample_seq)
            sample = self.db.execute('SELECT body FROM samples WHERE device=? AND session=? AND sample_seq=?', sample_key).fetchone()
            if sample and sample[0] != frame.payload[:SAMPLE.size]:
                raise ValueError('Same acquisition identity, different snapshot')
            # Session-local sample order and uptime must agree, including wrap avoidance.
            lower = self.db.execute('SELECT body FROM samples WHERE device=? AND session=? AND sample_seq<? ORDER BY sample_seq DESC LIMIT 1', (frame.device,frame.session,snap.sample_seq)).fetchone()
            upper = self.db.execute('SELECT body FROM samples WHERE device=? AND session=? AND sample_seq>? ORDER BY sample_seq LIMIT 1', (frame.device,frame.session,snap.sample_seq)).fetchone()
            if lower and Snapshot.unpack(lower[0]).uptime_ms >= snap.uptime_ms or upper and Snapshot.unpack(upper[0]).uptime_ms <= snap.uptime_ms:
                raise ValueError('Uptime regression or acquisition-order conflict')
            if old is None:
                self.db.execute('INSERT INTO frames VALUES(?,?,?,?,?)', (*frame.key,frame.body,now_ms))
            if sample is None:
                self.db.execute('INSERT INTO samples VALUES(?,?,?,?)', (*sample_key,frame.payload[:SAMPLE.size]))
            if crash == 'before_commit':
                raise RuntimeError('Injected before commit')
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        if crash == 'after_commit':
            raise RuntimeError('Injected after commit, before ACK')
        # Both EVENT and TELEMETRY are acknowledged in version 2.
        return Frame(ACK,*frame.key,struct.pack('<I',frame.fingerprint)).wire()

    def current(self, device, now_ms, max_age_ms=65000):
        row = self.db.execute('SELECT session,sample_seq,body FROM samples WHERE device=? ORDER BY session DESC,sample_seq DESC LIMIT 1', (device,)).fetchone()
        if row is None:
            return dict(status='no_data', fresh=None, session=None, sample_seq=None)
        session, seq, body = row
        snap = Snapshot.unpack(body)
        mapping = self.db.execute('SELECT origin_ms,error_ms FROM time_maps WHERE device=? AND session=?', (device,session)).fetchone()
        base = dict(session=session, sample_seq=seq, snapshot=snap)
        if mapping is None:
            return dict(**base,status='clock_unmapped',fresh=None)
        age = now_ms - mapping[0] - snap.uptime_ms
        low, high = age-mapping[1], age+mapping[1]
        if low < 0:
            return dict(**base,status='clock_inconsistent',fresh=None,age_interval_ms=[low,high])
        if high <= max_age_ms:
            return dict(**base,status='current',fresh=True,age_interval_ms=[low,high])
        if low > max_age_ms:
            return dict(**base,status='stale',fresh=False,age_interval_ms=[low,high])
        return dict(**base,status='time_uncertain',fresh=None,age_interval_ms=[low,high])

    def frames(self):
        return [dict(key=(d,s,q),body=body,received_ms=t) for d,s,q,body,t in
                self.db.execute('SELECT device,session,seq,body,received_ms FROM frames ORDER BY device,session,seq')]

    def close(self):
        self.db.close()
