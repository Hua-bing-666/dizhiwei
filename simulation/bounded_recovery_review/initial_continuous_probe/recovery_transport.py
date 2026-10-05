"""Bounded host recovery reference. No radio driver or power-cut guarantee."""
import json
import struct

from compact_protocol import ACK, EVENT, TELEMETRY, SAMPLE, Frame, Snapshot, decode
from session_transport import connect


METRICS = ['accepted', 'initial_dispatch', 'recovery_dispatch', 'probe_dispatch',
           'ack_business', 'expired_business', 'rejected_capacity', 'rejected_old_source',
           'history_evicted', 'reactivated', 'recovery_observations']


class RecoverySender:
    def __init__(self, path, device=1, capacity=16, history_capacity=64):
        if not isinstance(device, int) or not 0 < device < 2**32:
            raise ValueError('Invalid device')
        if not 1 <= capacity <= 64 or not 1 <= history_capacity <= 1024:
            raise ValueError('Invalid logical storage capacity')
        self.device, self.capacity, self.history_capacity = device, capacity, history_capacity
        self.db = connect(path)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS recovery_meta(
          id INTEGER PRIMARY KEY CHECK(id=1), device INTEGER, session INTEGER, seq INTEGER,
          now_ms INTEGER, last_ack_ms INTEGER, next_probe_ms INTEGER, next_dispatch_ms INTEGER,
          source_floor INTEGER, audit_seq INTEGER, snapshot BLOB, metrics TEXT);
        CREATE TABLE IF NOT EXISTS recovery_live(
          session INTEGER, seq INTEGER, wire BLOB CHECK(length(wire)<=64), created_ms INTEGER,
          due_ms INTEGER, expires_ms INTEGER, initial_attempts INTEGER, recovery_attempts INTEGER,
          phase TEXT, last_dispatch_ms INTEGER, kind INTEGER, sample_seq INTEGER,
          code INTEGER, detail INTEGER, PRIMARY KEY(session,seq));
        CREATE TABLE IF NOT EXISTS recovery_probe(
          id INTEGER PRIMARY KEY CHECK(id=1), session INTEGER, seq INTEGER,
          wire BLOB CHECK(length(wire)<=64), dispatched_ms INTEGER);
        CREATE TABLE IF NOT EXISTS recovery_audit(
          audit_seq INTEGER PRIMARY KEY, session INTEGER, seq INTEGER,
          wire BLOB CHECK(length(wire)<=64), initial_attempts INTEGER, recovery_attempts INTEGER,
          state TEXT, at_ms INTEGER, kind INTEGER, sample_seq INTEGER, code INTEGER, detail INTEGER);
        ''')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            meta = self.db.execute('SELECT device,session FROM recovery_meta').fetchone()
            if meta and meta[0] != device:
                raise ValueError('One enrolled device per sender database')
            if self.db.execute('SELECT COUNT(*) FROM recovery_live').fetchone()[0] > capacity:
                raise ValueError('Existing unresolved records exceed requested capacity')
            self.session = (meta[1] if meta else 0) + 1
            if self.session >= 2**32:
                raise OverflowError('Session exhausted; re-enrol explicitly')
            if meta:
                self.db.execute('UPDATE recovery_meta SET session=?,seq=0,source_floor=0,snapshot=NULL,last_ack_ms=-1 WHERE id=1', (self.session,))
                old = self.db.execute('SELECT session,seq,wire FROM recovery_probe').fetchone()
                if old:
                    self._archive(*old, 0, 0, 'probe_abandoned', self._meta('now_ms'))
                    self.db.execute('DELETE FROM recovery_probe')
            else:
                self.db.execute('INSERT INTO recovery_meta VALUES(1,?,?,0,-1,-1,0,0,0,0,NULL,?)',
                                (device,self.session,json.dumps(dict.fromkeys(METRICS,0))))
            self._prune()
            self.db.commit()
        except Exception:
            self.db.rollback(); self.db.close(); raise

    def _meta(self, field):
        if field not in ('now_ms','last_ack_ms','seq','snapshot','next_probe_ms','next_dispatch_ms','source_floor','audit_seq'):
            raise ValueError('Unknown metadata field')
        return self.db.execute('SELECT '+field+' FROM recovery_meta WHERE id=1').fetchone()[0]

    def _metric(self, field, amount=1):
        metrics = self.metrics()
        if field not in metrics:
            raise ValueError('Unknown counter')
        metrics[field] += amount
        self.db.execute('UPDATE recovery_meta SET metrics=? WHERE id=1', (json.dumps(metrics,sort_keys=True),))

    def _begin(self, now_ms):
        if not isinstance(now_ms, int) or now_ms < 0:
            raise ValueError('Use nonnegative host-clock milliseconds')
        self.db.execute('BEGIN IMMEDIATE')
        owner = self.db.execute('SELECT session FROM recovery_meta WHERE id=1').fetchone()[0]
        if owner != self.session:
            raise RuntimeError('Sender superseded')
        if now_ms < self._meta('now_ms'):
            raise ValueError('Host clock regression; explicit mapping required')
        self.db.execute('UPDATE recovery_meta SET now_ms=? WHERE id=1', (now_ms,))
        self._expire(now_ms)

    def _next_seq(self):
        seq = self._meta('seq') + 1
        if seq >= 2**32:
            raise OverflowError('Message sequence exhausted')
        self.db.execute('UPDATE recovery_meta SET seq=? WHERE id=1', (seq,))
        return seq

    def _archive(self, session, seq, wire, initial, recovery, state, now_ms, source=None):
        frame = decode(wire) if wire is not None else None
        sample = Snapshot.unpack(frame.payload[:SAMPLE.size]) if frame else None
        code, detail = frame.payload[SAMPLE.size:] if frame and frame.kind == EVENT else (None,None)
        identity=(frame.kind,sample.sample_seq,code,detail) if frame else source or (None,None,None,None)
        audit_seq = self._meta('audit_seq') + 1
        self.db.execute('UPDATE recovery_meta SET audit_seq=? WHERE id=1', (audit_seq,))
        self.db.execute('INSERT INTO recovery_audit VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                        (audit_seq,session,seq,wire,initial,recovery,state,now_ms,
                         *identity))
        self._prune()

    def _prune(self):
        excess = self.db.execute('SELECT COUNT(*) FROM recovery_audit').fetchone()[0] - self.history_capacity
        if excess <= 0:
            return
        rows = self.db.execute('SELECT audit_seq,session,kind,sample_seq,wire FROM recovery_audit ORDER BY audit_seq LIMIT ?', (excess,)).fetchall()
        for audit_seq,session,kind,sample_seq,wire in rows:
            if session == self.session and kind == EVENT and wire is not None:
                self.db.execute('UPDATE recovery_meta SET source_floor=MAX(source_floor,?) WHERE id=1', (sample_seq,))
            self.db.execute('DELETE FROM recovery_audit WHERE audit_seq=?', (audit_seq,))
        self._metric('history_evicted',excess)

    def _expire(self, now_ms):
        rows = self.db.execute('SELECT session,seq,wire,initial_attempts,recovery_attempts FROM recovery_live WHERE expires_ms<=?', (now_ms,)).fetchall()
        for session,seq,wire,initial,recovery in rows:
            self._archive(session,seq,wire,initial,recovery,'expired',now_ms)
            self.db.execute('DELETE FROM recovery_live WHERE session=? AND seq=?', (session,seq))
            self._metric('expired_business')
        self.db.execute("UPDATE recovery_live SET phase='parked' WHERE due_ms<=? AND ((phase='initial' AND initial_attempts>=8) OR (phase='recovering' AND recovery_attempts>=4))", (now_ms,))

    def enqueue(self, kind, payload, now_ms):
        if kind not in (EVENT,TELEMETRY):
            raise ValueError('Only uplink messages')
        # Validate even rejected messages; do not issue an identity until admitted.
        candidate = Frame(kind,self.device,self.session,1,payload)
        candidate.wire()
        snap = Snapshot.unpack(payload[:SAMPLE.size])
        code, detail = payload[SAMPLE.size:] if kind == EVENT else (None,None)
        try:
            self._begin(now_ms)
            if kind == EVENT:
                key=(self.session,snap.sample_seq,code,detail)
                for table in ['recovery_live','recovery_audit']:
                    old=self.db.execute('SELECT wire FROM '+table+' WHERE session=? AND sample_seq=? AND code=? AND detail=? AND wire IS NOT NULL ORDER BY seq DESC LIMIT 1',key).fetchone()
                    if old:
                        frame=decode(old[0])
                        if frame.payload != payload:
                            raise ValueError('Same source identity, conflicting content')
                        self.db.commit(); return frame
                if snap.sample_seq <= self._meta('source_floor'):
                    self._metric('rejected_old_source')
                    self._archive(self.session,None,None,0,0,'rejected_old_source',now_ms,(kind,snap.sample_seq,code,detail))
                    self.db.commit(); return None
            if self.db.execute('SELECT COUNT(*) FROM recovery_live').fetchone()[0] >= self.capacity:
                self._metric('rejected_capacity')
                self._archive(self.session,None,None,0,0,'rejected_capacity',now_ms,(kind,snap.sample_seq,code,detail))
                self.db.commit(); return None
            frame=Frame(kind,self.device,self.session,self._next_seq(),payload)
            self.db.execute('INSERT INTO recovery_live VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (self.session,frame.seq,frame.wire(),now_ms,now_ms,now_ms+300000,
                             0,0,'initial',-1,kind,snap.sample_seq,code,detail))
            self._metric('accepted')
            self.db.commit(); return frame
        except Exception:
            self.db.rollback(); raise

    def set_snapshot(self, payload, now_ms):
        snap=Snapshot.unpack(payload)
        try:
            self._begin(now_ms)
            old=self._meta('snapshot')
            if old:
                before=Snapshot.unpack(old)
                if snap.sample_seq < before.sample_seq or snap.uptime_ms < before.uptime_ms or snap.sample_seq > before.sample_seq and snap.uptime_ms <= before.uptime_ms:
                    raise ValueError('Snapshot order regression')
                if snap.sample_seq == before.sample_seq and payload != old:
                    raise ValueError('Same sample, conflicting snapshot')
            self.db.execute('UPDATE recovery_meta SET snapshot=? WHERE id=1', (payload,))
            self.db.commit()
        except Exception:
            self.db.rollback(); raise

    def pick(self, now_ms, aux_ready=True):
        try:
            self._begin(now_ms)
            wire=None
            if aux_ready and now_ms >= self._meta('next_dispatch_ms'):
                snapshot=self._meta('snapshot')
                if snapshot is not None and now_ms >= self._meta('next_probe_ms'):
                    old=self.db.execute('SELECT session,seq,wire FROM recovery_probe').fetchone()
                    if old:
                        self._archive(*old,0,0,'probe_unconfirmed',now_ms)
                    frame=Frame(TELEMETRY,self.device,self.session,self._next_seq(),snapshot)
                    wire=frame.wire()
                    self.db.execute('INSERT OR REPLACE INTO recovery_probe VALUES(1,?,?,?,?)', (self.session,frame.seq,wire,now_ms))
                    self.db.execute('UPDATE recovery_meta SET next_probe_ms=? WHERE id=1', (now_ms+30000,))
                    self._metric('probe_dispatch')
                else:
                    row=self.db.execute("SELECT session,seq,wire,initial_attempts,recovery_attempts,phase FROM recovery_live WHERE due_ms<=? AND ((phase='initial' AND initial_attempts<8) OR (phase='recovering' AND recovery_attempts<4)) ORDER BY (kind=1) DESC,due_ms,created_ms,session,seq LIMIT 1",(now_ms,)).fetchone()
                    if row:
                        session,seq,wire,initial,recovery,phase=row
                        delay=([2000]*3+[20000]*5)[initial] if phase=='initial' else 2000
                        column='initial_attempts' if phase=='initial' else 'recovery_attempts'
                        self.db.execute('UPDATE recovery_live SET '+column+'='+column+'+1,due_ms=?,last_dispatch_ms=? WHERE session=? AND seq=?', (now_ms+delay,now_ms,session,seq))
                        self._metric('initial_dispatch' if phase=='initial' else 'recovery_dispatch')
                if wire is not None:
                    self.db.execute('UPDATE recovery_meta SET next_dispatch_ms=? WHERE id=1', (now_ms+1000,))
            self.db.commit(); return wire
        except Exception:
            self.db.rollback(); raise

    def acknowledge(self, wire, now_ms):
        frame=decode(wire)
        if frame.kind != ACK or frame.device != self.device:
            return False
        try:
            self._begin(now_ms)
            key=(frame.session,frame.seq)
            live=self.db.execute('SELECT wire,initial_attempts,recovery_attempts,last_dispatch_ms FROM recovery_live WHERE session=? AND seq=?',key).fetchone()
            probe=self.db.execute('SELECT wire,dispatched_ms FROM recovery_probe WHERE session=? AND seq=?',key).fetchone()
            audit=self.db.execute('SELECT wire,audit_seq,initial_attempts,recovery_attempts,state FROM recovery_audit WHERE session=? AND seq=? ORDER BY audit_seq DESC LIMIT 1',key).fetchone()
            saved=live or probe or audit
            if saved is None or saved[0] is None or struct.unpack('<I',frame.payload)[0] != decode(saved[0]).fingerprint:
                self.db.commit(); return False
            dispatched=live[3] if live else probe[1] if probe else -1
            # An undispatched local frame is never a valid link proof or ACK target.
            if live and dispatched < 0:
                self.db.commit(); return False
            if audit and not live and not probe and audit[2]+audit[3] == 0 and not audit[4].startswith('probe_'):
                self.db.commit(); return False
            timely=dispatched>=0 and 0<=now_ms-dispatched<=8000
            if live:
                self._archive(*key,live[0],live[1],live[2],'acknowledged',now_ms)
                self.db.execute('DELETE FROM recovery_live WHERE session=? AND seq=?',key)
                self._metric('ack_business')
            elif probe:
                self._archive(*key,probe[0],0,0,'probe_acknowledged',now_ms)
                self.db.execute('DELETE FROM recovery_probe WHERE session=? AND seq=?',key)
            else:
                self.db.execute("UPDATE recovery_audit SET state=CASE WHEN state='expired' THEN 'acknowledged_late' ELSE state END WHERE audit_seq=?", (audit[1],))
            if timely:
                last=self._meta('last_ack_ms')
                if last < 0 or now_ms-last > 8000:
                    count=self.db.execute("SELECT COUNT(*) FROM recovery_live WHERE phase!='recovering' AND initial_attempts>0 AND recovery_attempts<4 AND expires_ms>?",(now_ms,)).fetchone()[0]
                    self.db.execute("UPDATE recovery_live SET phase='recovering',due_ms=? WHERE phase!='recovering' AND initial_attempts>0 AND recovery_attempts<4 AND expires_ms>?",(now_ms,now_ms))
                    self._metric('reactivated',count)
                    self._metric('recovery_observations')
                self.db.execute('UPDATE recovery_meta SET last_ack_ms=? WHERE id=1',(now_ms,))
            self.db.commit(); return True
        except Exception:
            self.db.rollback(); raise

    def metrics(self):
        return json.loads(self.db.execute('SELECT metrics FROM recovery_meta WHERE id=1').fetchone()[0])

    def states(self):
        return [dict(session=s,seq=q,initial_attempts=i,recovery_attempts=r,state=p) for s,q,i,r,p in
                self.db.execute('SELECT session,seq,initial_attempts,recovery_attempts,phase FROM recovery_live ORDER BY session,seq')]

    def storage(self):
        tables=['recovery_meta','recovery_live','recovery_probe','recovery_audit']
        counts={t:self.db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in tables}
        wire_bytes=sum(self.db.execute('SELECT COALESCE(SUM(length(wire)),0) FROM '+t).fetchone()[0] for t in tables[1:])
        return dict(rows=counts,retained_wire_bytes=wire_bytes,snapshot_bytes=len(self._meta('snapshot') or b''))

    def close(self):
        self.db.close()
