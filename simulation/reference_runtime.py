"""Causal 1-Hz host prototype, verified against the offline six-method replay.

This is not STM32 firmware. Initial [20,120) readings must be confirmed
healthy by the operator. Nonuniform sampling is rejected, not interpolated.
"""
from collections import deque
import math
import numpy as np

class ReferenceDiagnostic:
    def __init__(self, reference, parameters, method='reference'):
        if method not in ('flow','sqrt','reference','reference_gate','cusum','ewma'):
            raise ValueError('Unknown diagnostic method')
        self.ref=dict(reference);self.params=parameters;self.method=method
        self.window=deque(maxlen=10);self.pressure_history=deque(maxlen=11)
        self.calibration=[];self.baseline=None;self.last_t=-1
        self.cs=np.zeros(2);self.ew=np.zeros(2)
        self.until=-1;self.rearm=130;self.pending=0;self.count=0;self.active=0

    def update(self,t,p0_kpa,p1_kpa,q_l_min):
        if t!=self.last_t+1:
            raise ValueError('This prototype requires consecutive integer 1-second timestamps from zero.')
        x=np.array([p0_kpa,p1_kpa,q_l_min],float)
        if not np.isfinite(x).all():
            raise ValueError('Non-finite readings require separate quality/recovery handling.')
        self.last_t=t;self.window.append(x)
        avg=np.mean(self.window,axis=0);p0,p1,q=avg
        self.pressure_history.append(avg[:2].copy())
        k=q/math.sqrt(max(p1,.001));r=(p0-p1)/max(q*q,.001)
        predicted=self.ref['a_l_min']*(max(p1,.001)/100)**self.ref['n_fitted']
        if 20<=t<120:self.calibration.append([k,r,q,q/predicted])
        if t==120:
            c=np.array(self.calibration);k0,r0,q0,gain=np.median(c,axis=0)
            residual=np.column_stack([c[:,3]/gain-1,c[:,1]-r0])
            scale=np.maximum(1.4826*np.median(abs(residual-np.median(residual,axis=0)),axis=0),[.003,.03])
            self.baseline=(k0,r0,q0,gain,scale)
        if t<130:return dict(t_s=t,state='calibrating',event=None)
        k0,r0,q0,gain,scale=self.baseline
        residual=np.array([q/(gain*predicted)-1,r-r0]);valid=p1>10 and q>.5
        self.cs=np.maximum(0,self.cs+residual/scale-.5) if valid else np.zeros(2)
        self.ew=.2*residual+.8*self.ew if valid else np.zeros(2)
        change=bool(np.any(abs(avg[:2]/np.maximum(self.pressure_history[0],10)-1)>.10))
        if change and t>=self.rearm:self.until=t+19;self.rearm=t+40
        gate=t<=self.until
        if self.method=='flow':a=q/q0-1>.06;b=q/q0-1<-.06
        elif self.method=='sqrt':a=k/k0-1>.06;b=r-r0>.6
        elif self.method in ('reference','reference_gate'):a=residual[0]>.06;b=residual[1]>.6
        elif self.method=='cusum':a=self.cs[0]>self.params['h_cusum'][0];b=self.cs[1]>self.params['h_cusum'][1]
        else:a=self.ew[0]>self.params['h_ewma'][0];b=self.ew[1]>self.params['h_ewma'][1]
        label=int(a)+2*int(b)
        if not valid:label=-1
        elif self.method=='reference_gate' and gate:label=-2
        if label<=0:self.pending=self.active=self.count=0
        elif self.pending!=label:self.pending=label;self.count=1
        else:self.count+=1
        names={0:'normal_observation',1:'leak_pattern',2:'restriction_pattern',3:'uncertain',-1:'invalid',-2:'transition_review'}
        event=None
        if label>0 and self.count>=5 and self.active!=label:
            event=dict(t_s=t,pattern=names[label]);self.active=label
        return dict(t_s=t,state=names[label],event=event,residual=residual.tolist(),
                    cusum=self.cs.tolist(),ewma=self.ew.tolist(),
                    transition_flag=gate,
                    outside_reference=bool(p1<self.ref['p1_min_kpa'] or p1>self.ref['p1_max_kpa']))
