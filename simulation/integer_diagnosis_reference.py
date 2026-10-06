"""Independent rational-arithmetic oracle for the portable integer core."""
from fractions import Fraction

MISSING=-(2**31)
FIELDS=['status','pattern','rapid_valid','rapid_active','rapid_positive','main_label','event_mask','quality_reason','flow_milli']

def predict(c,total,n):
    position=Fraction(total-1000*n,50*n)
    i=position.numerator//position.denominator
    if i>=380:return c['lut'][-1]
    f=position-i
    return round(c['lut'][i]*(1-f)+c['lut'][i+1]*f)

def flags(c,p0,p1,d,n,rapid=False):
    q=Fraction(d,9*n)
    pred=Fraction(predict(c,p1,n),1000000)
    threshold=c['rapid'] if rapid else c['main']
    x0=q/pred-1
    x1=Fraction(p0-p1,100*n)/(q*q)-Fraction(c['r0'],1000000) if d else Fraction(0)
    return int(x0>Fraction(threshold[0],1000000))+2*int(x1>Fraction(threshold[1],1000000))

class IntegerOracle:
    def __init__(self,config):
        self.c=config;self.t=-1;self.history=[];self.pressure_run=0;self.counter_run=0
        self.pending=0;self.confirmed=0;self.active=0;self.rapid_pending=0;self.rapid_active=0;self.status=255

    def update(self,t,count,p0,p1,issue):
        if not 0<=t<4294967 or t!=self.t+1 or not 0<=count<2**32 or issue not in range(4):return None
        if issue==0 and not (0<=p0<=20000 and 0<=p1<=20000):return None
        prior=self.history[-1][0] if self.history else 0
        if count>=prior and count-prior>450:return None
        reason=0
        if self.history and count<prior:self.counter_run=0;self.pressure_run=0;reason=3
        self.counter_run=min(11,self.counter_run+1)
        if issue:self.pressure_run=0;reason={1:1,2:2,3:4}[issue]
        else:self.pressure_run=min(10,self.pressure_run+1)
        self.history=(self.history+[(count,p0,p1,issue)])[-11:];self.t=t
        flow=round(Fraction((count-self.history[0][0])*1000,90)) if self.counter_run>=11 else MISSING
        if t<130:return [4,4,0,0,0,-1,0,0,flow]
        def window(n):
            if len(self.history)<n+1:return None
            part=self.history[-n-1:]
            if any(p[3] or p[2]<=1000 for p in part[1:]) or any(b[0]<a[0] for a,b in zip(part,part[1:])):return None
            d=part[-1][0]-part[0][0]
            if Fraction(d,9*n)<=Fraction(1,2):return None
            return sum(p[1] for p in part[1:]),sum(p[2] for p in part[1:]),d
        ready=self.pressure_run>=10;counter=self.counter_run>=11;w=window(10)
        valid=bool(ready and counter and w and self.c['numeric'])
        label=flags(self.c,*w,10) if valid else -1
        status=0 if valid else 2 if not self.c['numeric'] else 3 if issue else 4 if not ready or not counter else 5
        events=0
        if label<=0:self.pending=self.confirmed=self.active=0
        elif label!=self.pending:self.pending=label;self.confirmed=1
        else:self.confirmed=min(5,self.confirmed+1)
        if label>0 and self.confirmed>=5 and self.active!=label:
            self.active=label
            if self.c['approved']:events|=1<<{1:4,2:5,3:6}[label]
        w=window(3);rv=bool(w and self.c['numeric'] and self.c['rapid_available'])
        pos=bool(rv and flags(self.c,*w,3,rapid=True))
        if not pos:self.rapid_pending=0;self.rapid_active=0
        else:self.rapid_pending=min(2,self.rapid_pending+1)
        if self.rapid_pending>=2 and not self.rapid_active:
            self.rapid_active=1
            if self.c['approved']:events|=1<<3
        status=status if self.c['approved'] else 1
        pattern=4 if status else self.active if self.pending==self.active and self.confirmed>=5 else 0
        if status!=self.status:events|=1<<1;self.status=status
        quality_reason=0
        if reason and self.c['numeric'] and self.c['approved']:events|=1<<2;quality_reason=reason
        return [status,pattern,int(rv and self.c['approved']),int(rv and self.c['approved'] and self.rapid_active),int(pos and self.c['approved']),label,events,quality_reason,flow]
