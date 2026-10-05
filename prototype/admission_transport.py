"""Event-preserving admission and latest ordinary telemetry; host reference only."""
from pathlib import Path
import json
import struct

from compact_protocol import ACK,EVENT,TELEMETRY,SAMPLE,Frame,Snapshot,decode
from recovery_transport import RecoverySender
from session_transport import connect


EXTRA_METRICS=['accepted_events','accepted_telemetry','rejected_events_capacity','rejected_telemetry_capacity',
               'telemetry_superseded','telemetry_evicted_for_event','late_retired_telemetry_ack',
               'expired_events','expired_telemetry']
TAG='event_priority_latest_telemetry_v1'


class AdmissionSender(RecoverySender):
    def __init__(self,path,device=1,capacity=16,history_capacity=64):
        if str(path)!=':memory:' and Path(path).exists():
            check=connect(path)
            try:
                exists=check.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recovery_meta'").fetchone()
                if exists and check.execute('SELECT COUNT(*) FROM recovery_meta').fetchone()[0]:
                    policy=check.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admission_policy'").fetchone()
                    if not policy:
                        raise ValueError('Use a separate database; do not silently migrate the previous sender')
                    saved=check.execute('SELECT tag,capacity,history_capacity FROM admission_policy WHERE id=1').fetchone()
                    if saved!=(TAG,capacity,history_capacity):
                        raise ValueError('Persisted admission contract cannot change at reopen')
            finally:check.close()
        super().__init__(path,device,capacity,history_capacity)
        try:
            with self.db:
                self.db.execute('CREATE TABLE IF NOT EXISTS admission_policy(id INTEGER PRIMARY KEY CHECK(id=1),tag TEXT,capacity INTEGER,history_capacity INTEGER,last_telemetry_wire BLOB CHECK(length(last_telemetry_wire)<=64))')
                self.db.execute('INSERT OR REPLACE INTO admission_policy VALUES(1,?,?,?,NULL)',(TAG,capacity,history_capacity))
                metrics=self.metrics()
                for field in EXTRA_METRICS:metrics.setdefault(field,0)
                self.db.execute('UPDATE recovery_meta SET metrics=? WHERE id=1',(json.dumps(metrics,sort_keys=True),))
        except Exception:
            self.db.close();raise

    def _archive(self,session,seq,wire,initial,recovery,state,now_ms,source=None):
        if state in ('telemetry_superseded','telemetry_evicted_for_event'):
            if wire is None or decode(wire).kind!=TELEMETRY:
                raise ValueError('Only ordinary telemetry may be retired for admission')
            self._metric(state)
        if state=='expired' and wire is not None:
            self._metric('expired_events' if decode(wire).kind==EVENT else 'expired_telemetry')
        super()._archive(session,seq,wire,initial,recovery,state,now_ms,source)

    def _retire_telemetry(self,state,now_ms):
        rows=self.db.execute('SELECT session,seq,wire,initial_attempts,recovery_attempts FROM recovery_live WHERE kind=?',(TELEMETRY,)).fetchall()
        for session,seq,wire,initial,recovery in rows:
            self._archive(session,seq,wire,initial,recovery,state,now_ms)
            self.db.execute('DELETE FROM recovery_live WHERE session=? AND seq=?',(session,seq))

    def enqueue(self,kind,payload,now_ms):
        if kind not in (EVENT,TELEMETRY):
            raise ValueError('Only uplink messages')
        Frame(kind,self.device,self.session,1,payload).wire()
        snap=Snapshot.unpack(payload[:SAMPLE.size])
        code,detail=payload[SAMPLE.size:] if kind==EVENT else (None,None)
        try:
            self._begin(now_ms)
            if kind==EVENT:
                key=(self.session,snap.sample_seq,code,detail)
                for table in ['recovery_live','recovery_audit']:
                    old=self.db.execute('SELECT wire FROM '+table+' WHERE session=? AND sample_seq=? AND code=? AND detail=? AND wire IS NOT NULL ORDER BY seq DESC LIMIT 1',key).fetchone()
                    if old:
                        frame=decode(old[0])
                        if frame.payload!=payload:
                            raise ValueError('Same event source, conflicting content')
                        self.db.commit();return frame
                if snap.sample_seq<=self._meta('source_floor'):
                    self._metric('rejected_old_source')
                    self._archive(self.session,None,None,0,0,'rejected_old_source',now_ms,(kind,snap.sample_seq,code,detail))
                    self.db.commit();return None
            else:
                old=self.db.execute('SELECT last_telemetry_wire FROM admission_policy WHERE id=1').fetchone()[0]
                if old is not None:
                    frame=decode(old);before=Snapshot.unpack(frame.payload)
                    if snap.sample_seq==before.sample_seq:
                        if payload!=frame.payload:
                            raise ValueError('Same telemetry source, conflicting content')
                        self.db.commit();return frame
                    if snap.sample_seq<before.sample_seq or snap.uptime_ms<=before.uptime_ms:
                        raise ValueError('Older telemetry cannot supersede newer telemetry')
                self._retire_telemetry('telemetry_superseded',now_ms)
            count=self.db.execute('SELECT COUNT(*) FROM recovery_live').fetchone()[0]
            if count>=self.capacity and kind==EVENT:
                self._retire_telemetry('telemetry_evicted_for_event',now_ms)
                count=self.db.execute('SELECT COUNT(*) FROM recovery_live').fetchone()[0]
            if count>=self.capacity:
                self._metric('rejected_capacity')
                self._metric('rejected_events_capacity' if kind==EVENT else 'rejected_telemetry_capacity')
                self._archive(self.session,None,None,0,0,'rejected_capacity',now_ms,(kind,snap.sample_seq,code,detail))
                self.db.commit();return None
            frame=Frame(kind,self.device,self.session,self._next_seq(),payload)
            self.db.execute('INSERT INTO recovery_live VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                            (self.session,frame.seq,frame.wire(),now_ms,now_ms,now_ms+300000,
                             0,0,'initial',-1,kind,snap.sample_seq,code,detail))
            self._metric('accepted');self._metric('accepted_events' if kind==EVENT else 'accepted_telemetry')
            if kind==TELEMETRY:
                self.db.execute('UPDATE admission_policy SET last_telemetry_wire=? WHERE id=1',(frame.wire(),))
            self.db.commit();return frame
        except Exception:
            self.db.rollback();raise

    def acknowledge(self,wire,now_ms):
        frame=decode(wire)
        if frame.kind!=ACK or frame.device!=self.device:
            return False
        try:
            self._begin(now_ms)
            key=(frame.session,frame.seq)
            live=self.db.execute('SELECT wire,initial_attempts,recovery_attempts,last_dispatch_ms FROM recovery_live WHERE session=? AND seq=?',key).fetchone()
            probe=self.db.execute('SELECT wire,dispatched_ms FROM recovery_probe WHERE session=? AND seq=?',key).fetchone()
            audit=self.db.execute('SELECT wire,audit_seq,initial_attempts,recovery_attempts,state FROM recovery_audit WHERE session=? AND seq=? ORDER BY audit_seq DESC LIMIT 1',key).fetchone()
            saved=live or probe or audit
            if saved is None or saved[0] is None or struct.unpack('<I',frame.payload)[0]!=decode(saved[0]).fingerprint:
                self.db.commit();return False
            dispatched=live[3] if live else probe[1] if probe else -1
            if live and dispatched<0:
                self.db.commit();return False
            if audit and not live and not probe and audit[2]+audit[3]==0 and not audit[4].startswith('probe_'):
                self.db.commit();return False
            timely=dispatched>=0 and 0<=now_ms-dispatched<=8000
            if live:
                self._archive(*key,live[0],live[1],live[2],'acknowledged',now_ms)
                self.db.execute('DELETE FROM recovery_live WHERE session=? AND seq=?',key)
                self._metric('ack_business')
            elif probe:
                self._archive(*key,probe[0],0,0,'probe_acknowledged',now_ms)
                self.db.execute('DELETE FROM recovery_probe WHERE session=? AND seq=?',key)
            else:
                state=audit[4]
                if state=='expired':
                    self.db.execute("UPDATE recovery_audit SET state='acknowledged_late' WHERE audit_seq=?",(audit[1],))
                elif state in ('telemetry_superseded','telemetry_evicted_for_event'):
                    self.db.execute("UPDATE recovery_audit SET state=state||'_acknowledged_late' WHERE audit_seq=?",(audit[1],))
                    self._metric('late_retired_telemetry_ack')
            if timely:
                last=self._meta('last_ack_ms')
                if last<0 or now_ms-last>8000:
                    count=self.db.execute("SELECT COUNT(*) FROM recovery_live WHERE phase!='recovering' AND initial_attempts>0 AND recovery_attempts<4 AND expires_ms>?",(now_ms,)).fetchone()[0]
                    self.db.execute("UPDATE recovery_live SET phase='recovering',due_ms=? WHERE phase!='recovering' AND initial_attempts>0 AND recovery_attempts<4 AND expires_ms>?",(now_ms,now_ms))
                    self._metric('reactivated',count);self._metric('recovery_observations')
                self.db.execute('UPDATE recovery_meta SET last_ack_ms=? WHERE id=1',(now_ms,))
            self.db.commit();return True
        except Exception:
            self.db.rollback();raise

    def storage(self):
        result=super().storage()
        row=self.db.execute('SELECT last_telemetry_wire FROM admission_policy WHERE id=1').fetchone()[0]
        result['rows']['admission_policy']=1
        result['last_telemetry_wire_bytes']=len(row or b'')
        result['retained_wire_bytes']+=len(row or b'')
        return result
