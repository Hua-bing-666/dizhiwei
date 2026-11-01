"""Sequential reference runtime. No trajectory, fault or future-array inputs.

One-second counter snapshots are assumed available continuously. Pressure is
provided only on requested reads. This is a Python logic prototype, not MCU
firmware or a measurement of hardware sleep/energy behaviour.
"""
from collections import deque
import numpy as np
from review_hybrid_sampling import BoundedEvidence, residual

METHODS=['guarded_fast','hybrid']

def mad(x,axis=None):
    return 1.4826*np.median(abs(x-np.median(x,axis=axis)),axis=axis)

class SamplingNode:
    def __init__(self,reference,limits,period=1,phase=0,quality='range'):
        assert period in (1,2,5) and 0<=phase<period and quality in ('finite','range')
        self.reference=reference;self.limits=np.array(limits);self.period=period;self.phase=phase;self.quality=quality
        self.clock=-1;self.next_t=0;self.high_until=-1;self.last_pressure=None;self.last_count=0
        self.counts=deque([(-1,0)],maxlen=11);self.pressures=deque(maxlen=10)
        self.cal=[];self.cal_raw=[];self.cal_bad=False;self.context=None;self.stat=BoundedEvidence()
        self.acquired=[];self.records=[];self.quality_events=[];self.triggers=[]
        self.state={m:dict(pending=0,count=0,active=0,last_t=-1,events=[],labels=[]) for m in METHODS}

    def pressure_due(self,t):return t==self.next_t

    def finish_calibration(self):
        if self.cal_bad or len(self.cal)!=100:return
        pp=np.array([v[:2] for v in self.cal]);q=np.array([v[2] for v in self.cal]);raw=np.array(self.cal_raw)
        ref=self.reference;predicted=ref['a_l_min']*(pp[:,1]/100)**ref['n_fitted']
        gain=float(np.median(q/predicted));r0=float(np.median((pp[:,0]-pp[:,1])/q**2))
        x=np.array([residual(*p,qq,ref,gain,r0) for p,qq in zip(pp,q)])
        rx=np.array([residual(*p,qq,ref,gain,r0) for p,qq in zip(raw,q)])
        diff=np.diff(raw[:,1])/np.maximum(raw[:-1,1],10)
        self.context=dict(gain=gain,r0=r0,scale=np.maximum(mad(x,axis=0),[.003,.03]),
            rawscale=np.maximum(mad(rx,axis=0),[.003,.03]),pressure_change_trigger=max(.05,3*mad(diff)))

    def update(self,t,count,pressure=None):
        assert t==self.clock+1,'Counter timestamps must be consecutive one-second ends.'
        due=self.pressure_due(t);assert (pressure is not None)==due,'Pressure must only enter on requested reads.'
        self.clock=t;count=int(count)
        if count<self.last_count:
            self.quality_events.append(dict(t_s=t,reason='counter_reset'))
            self.counts.clear();self.pressures.clear();self.stat.reset()
            if t<130:self.cal_bad=True
            self.high_until=max(self.high_until,t+29)
            if not due:self.next_t=t+1
        self.counts.append((t,count));self.last_count=count
        counter_ready=len(self.counts)==11 and self.counts[0][0]==t-10
        q10=60*(count-self.counts[0][1])/(540*10) if counter_ready else None
        if not due:return None
        self.acquired.append(t);current=np.array(pressure,dtype=float)
        finite=bool(np.all(np.isfinite(current)))
        pressure_ok=finite and (self.quality=='finite' or bool(np.all((current>=0)&(current<=200))))
        if not pressure_ok:
            self.quality_events.append(dict(t_s=t,reason='nonfinite_pressure' if not finite else 'pressure_out_of_range'))
            self.pressures.clear();self.stat.reset();self.high_until=max(self.high_until,t+29)
            if t<130:self.cal_bad=True
        else:self.pressures.append((t,current.copy()))
        ready=len(self.pressures)==10 and self.pressures[0][0]==t-9
        mp=np.mean([p for _,p in self.pressures],axis=0) if ready else None
        domain_ok=bool(ready and counter_ready and np.all([p[1]>10 for _,p in self.pressures]) and q10>.5)
        if 20<=t<120:
            if domain_ok:self.cal.append([*mp,q10]);self.cal_raw.append(current.copy())
            else:self.cal_bad=True
        if t==129:self.finish_calibration()
        rec=None
        if t>=130:
            trigger=False;c=self.context
            if pressure_ok and counter_ready and c is not None:
                raw=residual(*current,q10,self.reference,c['gain'],c['r0'])
                change=self.last_pressure is not None and abs(current[1]/max(self.last_pressure[1],10)-1)>c['pressure_change_trigger']
                trigger=bool(np.any(abs(raw)>np.maximum([.03,.3],3*c['rawscale'])) or change)
                if self.period>1 and trigger:self.high_until=t+29;self.triggers.append(t)
            valid=bool(pressure_ok and domain_ok and c is not None)
            if valid:
                x=residual(*mp,q10,self.reference,c['gain'],c['r0']);score=self.stat.update(x/c['scale'])
                status='valid'
            else:
                x=score=np.zeros(2);self.stat.reset()
                status='baseline_unavailable' if c is None else 'pressure_quality' if not pressure_ok else 'window_incomplete' if not ready or not counter_ready else 'operating_domain'
            rec=dict(t=t,valid=valid,status=status,ready=ready,counter_ready=counter_ready,
                x=x.tolist(),bounded=score.tolist(),flow_q10=q10,
                current_pressure=[float(v) if np.isfinite(v) else None for v in current],
                high=self.period==1 or t<=self.high_until)
            self.records.append(rec)
            for method,state in self.state.items():
                if valid:
                    flags=x>np.maximum([.06,.6],6*c['scale'])
                    if method=='hybrid':flags|=score>self.limits
                    label=int(flags[0])+2*int(flags[1])
                else:label=-1
                if t!=state['last_t']+1:state.update(pending=0,count=0,active=0)
                if label<=0:state.update(pending=0,count=0,active=0)
                elif label!=state['pending']:state.update(pending=label,count=1)
                else:state['count']+=1
                if label>0 and state['count']>=5 and state['active']!=label:
                    state['events'].append(dict(t_s=t,pattern={1:'leak_pattern',2:'restriction_pattern',3:'uncertain'}[label]));state['active']=label
                state['last_t']=t;state['labels'].append(label)
        if pressure_ok:self.last_pressure=current.copy()
        if t<129:self.next_t=t+1
        elif t==129:self.next_t=130+self.phase
        else:self.next_t=t+1 if self.period==1 or t<=self.high_until else t+self.period
        return rec

    def output(self):
        return dict(acquired=self.acquired,records=self.records,triggers=self.triggers,quality_events=self.quality_events,
            baseline_accepted=self.context is not None,
            context={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in self.context.items()} if self.context else None,
            decisions={m:dict(events=s['events'],labels=s['labels']) for m,s in self.state.items()})
