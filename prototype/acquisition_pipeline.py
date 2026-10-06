"""Host acquisition adapter feeding the compiled C bridge. No hardware driver."""
from pathlib import Path
from copy import deepcopy
import math,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from acquisition_timing import TimingGuard
from integer_diagnosis_reference import FIELDS
from compact_protocol import Snapshot,EVENT,MISSING

class SessionResetRequired(ValueError):pass

class AcquisitionPipeline:
    def __init__(self,profile,executable,config_id=11,reference_id=1,synthetic=True):
        from integer_profile import config_command
        self.profile=deepcopy(profile);self.config_id=config_id
        self.reference_id=reference_id if profile['numeric'] else 0;self.synthetic=synthetic
        self.guard=TimingGuard();self.clock=-1;self.halted=False;self.records=[];self.events=[];self.faults=[]
        Snapshot(1000,1,self.config_id,self.reference_id,0,MISSING,MISSING,MISSING,4,
                 int(profile['numeric'])+2*int(profile['approved'])+(128 if synthetic else 0),4,255,255).validate()
        self.worker=subprocess.Popen([str(executable)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,text=True,bufsize=1,
                                     creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        try:
            if self.command(config_command(self.profile))!='OK':raise ValueError('Invalid registered profile')
        except Exception:self.close();raise
    def command(self,line):
        self.worker.stdin.write(line+'\n');self.worker.stdin.flush()
        result=self.worker.stdout.readline().strip()
        if not result:raise RuntimeError('C bridge stopped')
        return result
    def fail(self,t,reason):
        self.halted=True;self.faults.append(dict(sample_index=t,reason=reason,session_halted=True))
        raise SessionResetRequired(reason)
    def update(self,t,count,latch_ms,reads):
        if self.halted:raise SessionResetRequired('Explicit new measurement session required')
        if not isinstance(t,int) or isinstance(t,bool) or t!=self.clock+1 or not 0<=t<4294967:self.fail(t,'sequence_or_clock_gap')
        if not isinstance(count,int) or isinstance(count,bool) or not 0<=count<2**32:self.fail(t,'counter_representation')
        if len(reads)!=2:self.fail(t,'two_pressure_reads_required')
        endpoint=(t+1)*1000;candidate=deepcopy(self.guard)
        counter_trusted=math.isfinite(latch_ms) and abs(latch_ms-endpoint)<=1
        temporal_ok=counter_trusted
        for ch,r in enumerate(reads):
            temporal_ok &= bool(r.ready and math.isfinite(r.started_ms) and math.isfinite(r.completed_ms)
                and endpoint-30<=r.started_ms<=r.completed_ms<=endpoint
                and r.completed_ms>self.guard.last_completed[ch])
        temporal_ok &= reads[0].completed_ms<=reads[1].started_ms
        timing=candidate.frame(endpoint,latch_ms,reads)
        finite=all(math.isfinite(r.value_kpa) for r in reads)
        in_range=finite and all(0<=r.value_kpa<=200 for r in reads)
        issue=3 if not temporal_ok else 1 if not finite else 2 if not in_range else 0
        if issue in (1,3):p0=p1=MISSING;ages=(255,255)
        else:
            p0,p1=[round(r.value_kpa*100) for r in reads];ages=tuple(timing['ages_ms'])
            if not all(MISSING<v<2**31 for v in (p0,p1)):self.fail(t,'pressure_representation')
        line='U '+' '.join(map(str,[t,count,p0,p1,issue,int(counter_trusted)]))
        response=self.command(line)
        if response=='ERR':self.fail(t,'C_input_contract_rejection')
        output=list(map(int,response.split()));assert len(output)==11
        fields=dict(zip(FIELDS,output[:9]));previous,accepted_count=output[9:]
        flags=self.profile['numeric']+2*self.profile['approved']+4*fields['rapid_valid']+8*fields['rapid_active']+(128 if self.synthetic else 0)
        snap=Snapshot(endpoint,t+1,self.config_id,self.reference_id,accepted_count,p0,p1,fields['flow_milli'],fields['status'],flags,fields['pattern'],*ages)
        try:snap.validate()
        except ValueError:self.fail(t,'snapshot_contract_rejection')
        fresh=[]
        for code in range(1,7):
            if fields['event_mask']&(1<<code):
                detail=previous if code==1 else fields['quality_reason'] if code==2 else 0
                payload=snap.pack()+bytes([code,detail]);fresh.append(dict(kind=EVENT,code=code,detail=detail,payload=payload))
        self.guard=candidate;self.clock=t
        record=dict(sample_index=t,snapshot=snap,fields=fields,issue=issue,counter_endpoint_trusted=bool(counter_trusted),
                    counter_value_is_held=not counter_trusted,raw_cumulative_pulses=count,
                    timing=timing,events=[dict(code=e['code'],detail=e['detail']) for e in fresh])
        self.records.append(record);self.events.extend(fresh)
        return record,fresh
    def close(self):
        if getattr(self,'worker',None) is not None:
            if self.worker.stdin and not self.worker.stdin.closed:self.worker.stdin.close()
            try:self.worker.wait(timeout=5)
            except subprocess.TimeoutExpired:self.worker.terminate();self.worker.wait(timeout=5)
            if self.worker.stdout:self.worker.stdout.close()
            if self.worker.stderr:self.worker.stderr.close()
            self.worker=None
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
