"""Short-window attention only; does not confirm water-fault identity."""
import numpy as np
from review_hybrid_sampling import residual
from sampling_quality_runtime import mad

def rapid_review(obs,counts,reference,baseline,window):
    assert window in (1,3)
    if baseline is None:return dict(events=[],records=[],calibration_available=False)
    # Every pressure point is actually acquired at 1 Hz in this comparison.
    x=np.zeros((len(obs),2));valid=np.zeros(len(obs),bool)
    for t in range(window,len(obs)):
        pp=obs[t-window+1:t+1,:2];cc=counts[t-window:t+1]
        q=60*(cc[-1]-cc[0])/(540*window)
        valid[t]=bool(np.all(np.isfinite(pp)) and np.all((pp>=0)&(pp<=200)) and np.all(pp[:,1]>10) and np.all(np.diff(cc)>=0) and q>.5)
        if valid[t]:x[t]=residual(*pp.mean(axis=0),q,reference,baseline['gain'],baseline['r0'])
    if not np.all(valid[20:120]):return dict(events=[],records=[],calibration_available=False)
    scale=np.maximum(mad(x[20:120],axis=0),[.003,.03]);threshold=np.maximum([.06,.6],6*scale)
    records=[];events=[];pending=0;active=False
    for t in range(130,len(obs)):
        positive=bool(valid[t] and np.any(x[t]>threshold))
        if not positive:pending=0;active=False
        else:pending+=1
        if pending>=2 and not active:events.append(dict(t_s=t,kind='rapid_review'));active=True
        records.append(dict(t=t,valid=bool(valid[t]),x=x[t].tolist(),attention=positive))
    return dict(events=events,records=records,calibration_available=True,scale=scale.tolist(),threshold=threshold.tolist())
