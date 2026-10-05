"""Frozen hybrid ablation and a separate physical-window acquisition replay.

Phase A isolates fusion on 1-Hz Gaussian observations. Phase B changes the
frontend: one ten-bin pulse-count flow estimate, actually acquired pressures
only. Diagnosis requires a full consecutive pressure window, with scores reset
across gaps. No copied irregular-time CUSUM or second smoothing of Q10.
"""
from pathlib import Path
from collections import deque
import csv,hashlib,itertools,json,sys
import numpy as np
from review_operating_reference import (EXPONENTS,SIGMAS,SCENES,trajectory,observe,
    features,confirm,evaluate,sha)
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'simulation/hybrid_sampling_review'
BASE=ROOT/'simulation/operating_reference_review/frozen_parameters.json'
TRAIN=list(range(26000,26012));TEST=list(range(27000,27020));SENSOR_TEST=list(range(28000,28012))
FUSIONS=['threshold','cusum','plain_or','plain_and','guarded_fast','bounded','hybrid']
SENSOR_METHODS=['threshold','guarded_fast','hybrid']
CFG=dict(version='20261006-hybrid-v1',training_seeds=TRAIN,test_seeds=TEST,
         sensor_test_seeds=SENSOR_TEST,bounded_window_s=60,cusum_k=.5,
         fast_scale_multiplier=6,thresholds=[.06,.6],healthy_peak_margin=1.1,
         pressure_window_s=10,pulses_per_litre_assumption=540,flow_count_continuous=True,
         pulse_window_bins=10,flow_reaveraged=False,monitor_period_s=5,high_hold_observations=30,
         trigger_scale_multiplier=3,trigger_floor=[.03,.3],pressure_change_floor=.05,
         diagnostic_min_consecutive_pressure_points=10,confirmation_samples=5,
         normal_send_interval_s=60,high_send_interval_s=10,
         sensor_exponents=[.5],diagnosis_during_missing_pressure_window='insufficient_data',
         statistic_reset_on_gap=True,parameters_tuned_on_test=False,energy_estimated=False)

def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
def write_csv(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

class BoundedEvidence:
    """Maximum positive suffix sum of at most 60 actual consecutive updates."""
    def __init__(self):self.reset()
    def reset(self):
        self.total=np.zeros(2);self.index=0;self.queues=[deque([(0,0.)]),deque([(0,0.)])]
    def update(self,z):
        self.index+=1;self.total+=np.asarray(z)-.5;score=np.zeros(2)
        for k,q in enumerate(self.queues):
            while q and q[0][0]<self.index-60:q.popleft()
            score[k]=max(0.,self.total[k]-q[0][1])
            while q and q[-1][1]>=self.total[k]:q.pop()
            q.append((self.index,float(self.total[k])))
        return score

def bounded_scores(f):
    scores=np.zeros_like(f['x']);stat=BoundedEvidence()
    for t in range(130,len(scores)):
        if f['valid'][t]:scores[t]=stat.update(f['x'][t]/f['scale'])
        else:stat.reset()
    return scores

def fusion_flags(f,bounded,p,method):
    thresholds=np.array([.06,.6]);t=f['x']>thresholds
    c=f['cs']>p['baseline']['h_cusum']
    fast=f['x']>np.maximum(thresholds,6*f['scale'])
    slow=bounded>p['h_bounded_gaussian']
    return {'threshold':t,'cusum':c,'plain_or':t|c,'plain_and':t&c,
            'guarded_fast':fast,'bounded':slow,'hybrid':fast|slow}[method]

def fusion_decision(f,bounded,p,method):
    flags=fusion_flags(f,bounded,p,method);state=flags[:,0].astype(np.int8)+2*flags[:,1].astype(np.int8)
    state[~f['valid']]=-1
    return dict(state=state,events=confirm(state))

def pulse_frontend(obs,seed):
    # t is the end of a one-second piecewise-constant rate bin (t-1,t].
    # This is a synthetic pulse process, not measured sensor timing or error.
    phase=(seed*.6180339887498949)%1
    cumulative=np.floor(phase+np.cumsum(np.maximum(obs[:,2],0))*9).astype(np.int64)
    ends=np.arange(len(obs));starts=np.maximum(-1,ends-10)
    prior=np.where(starts>=0,cumulative[np.maximum(starts,0)],0)
    q10=60*(cumulative-prior)/(540*(ends-starts))
    return dict(cumulative=cumulative,q10=q10,phase=phase)

def residual(p0,p1,q,ref,gain,r0):
    predicted=ref['a_l_min']*(max(p1,.001)/100)**ref['n_fitted']
    return np.array([q/(gain*predicted)-1,(p0-p1)/max(q*q,.001)-r0])

def sensor_context(obs,seed,ref):
    pulses=pulse_frontend(obs,seed);q10=pulses['q10']
    pp=obs[:130,:2];total=np.vstack([np.zeros((1,2)),np.cumsum(pp,axis=0)])
    end=np.arange(1,131);start=np.maximum(0,end-10)
    meanp=(total[end]-total[start])/(end-start)[:,None]
    predicted=ref['a_l_min']*(np.maximum(meanp[:,1],.001)/100)**ref['n_fitted']
    gain=float(np.median(q10[20:120]/predicted[20:120]))
    r0=float(np.median((meanp[20:120,0]-meanp[20:120,1])/q10[20:120]**2))
    x=np.array([residual(*meanp[t],q10[t],ref,gain,r0) for t in range(20,120)])
    raw=np.array([residual(*obs[t,:2],q10[t],ref,gain,r0) for t in range(20,120)])
    scale=np.maximum(1.4826*np.median(abs(x-np.median(x,axis=0)),axis=0),[.003,.03])
    rawscale=np.maximum(1.4826*np.median(abs(raw-np.median(raw,axis=0)),axis=0),[.003,.03])
    differences=np.diff(obs[20:120,1])/np.maximum(obs[20:119,1],10)
    pscale=1.4826*np.median(abs(differences-np.median(differences)))
    return dict(**pulses,gain=gain,r0=r0,scale=scale,rawscale=rawscale,
                pressure_change_trigger=max(.05,3*pscale))

def sensor_replay(obs,seed,ref,profile,h=None,phase=0):
    assert profile in ('fixed','adaptive') and 0<=phase<5
    context=sensor_context(obs,seed,ref);q10=context['q10']
    history=deque(maxlen=10);stat=BoundedEvidence();next_t=0;high_until=-1
    last_pressure=None;records=[];acquired=[];triggers=[]
    for t in range(len(obs)):
        if t!=next_t:continue
        current=obs[t,:2].copy();acquired.append(t);history.append((t,current))
        trigger=False
        if t>=130:
            raw=residual(*current,q10[t],ref,context['gain'],context['r0'])
            change=last_pressure is not None and abs(current[1]/max(last_pressure[1],10)-1)>context['pressure_change_trigger']
            trigger=bool(np.any(abs(raw)>np.maximum([.03,.3],3*context['rawscale'])) or change)
            if profile=='adaptive' and trigger:
                high_until=t+29;triggers.append(t)
            ready=len(history)==10 and history[0][0]==t-9
            valid=bool(ready and np.all(np.asarray([v for _,v in history])[:,1]>10) and q10[t]>.5)
            if valid:
                mp=np.mean([v for _,v in history],axis=0)
                x=residual(*mp,q10[t],ref,context['gain'],context['r0'])
                score=stat.update(x/context['scale'])
            else:x=np.zeros(2);score=np.zeros(2);stat.reset()
            records.append(dict(t=t,ready=ready,valid=valid,x=x.tolist(),bounded=score.tolist(),
                                high=profile=='fixed' or t<=high_until,
                                flow_q10=float(q10[t]),current_pressure=current.tolist()))
        last_pressure=current
        if t<129:next_t=t+1
        elif profile=='fixed':next_t=t+1
        elif t==129:next_t=130+phase
        else:next_t=t+1 if t<=high_until else t+5
    out=dict(acquired=acquired,records=records,triggers=triggers,context={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in context.items() if k not in ('cumulative','q10')},decisions={})
    if h is None:return out
    for method in SENSOR_METHODS:
        events=[];labels=[];pending=active=0;count=0;last_diagnostic_t=-1;sent=[];last_send=129
        for rec in records:
            t=rec['t'];x=np.array(rec['x']);score=np.array(rec['bounded'])
            fast=x>np.maximum([.06,.6],6*context['scale'])
            flags=x>[.06,.6] if method=='threshold' else fast if method=='guarded_fast' else fast|(score>h)
            label=int(flags[0])+2*int(flags[1]) if rec['valid'] else -1
            if t!=last_diagnostic_t+1:pending=active=count=0
            if label<=0:pending=active=count=0
            elif label!=pending:pending=label;count=1
            else:count+=1
            event=False
            if label>0 and count>=5 and active!=label:
                events.append(dict(t_s=t,pattern={1:'leak_pattern',2:'restriction_pattern',3:'uncertain'}[label]));active=label;event=True
            last_diagnostic_t=t;labels.append(label)
            if event or t-last_send>=(10 if rec['high'] or active else 60):sent.append(t);last_send=t
        out['decisions'][method]=dict(events=events,labels=labels,send_attempts=len(sent))
    return out

def sensor_evaluate(replay,tr,method):
    dummy=dict(gate=np.zeros(len(tr['t']),bool),outside_reference=np.zeros(len(tr['t']),bool))
    metric=evaluate(replay['decisions'][method],tr,dummy,'reference')
    return dict(**metric,observed_frames=sum(t>=130 for t in replay['acquired']),
                eligible_frames=sum(r['valid'] for r in replay['records']),
                insufficient_frames=sum(not r['valid'] for r in replay['records']),
                trigger_observations=len(replay['triggers']),send_attempts=replay['decisions'][method]['send_attempts'])

def fit():
    OUT.mkdir(exist_ok=True);base=json.loads(BASE.read_text(encoding='utf-8'))
    rows=[];sensor_rows=[]
    for ex,sigma,scene,seed in itertools.product(EXPONENTS,SIGMAS,['normal','supply_step','supply_up','supply_ramp'],TRAIN):
        tr=trajectory(scene,ex);obs=observe(tr,sigma,seed,scene);ref=base['references'][f'n{ex:g}']
        f=features(obs,ref);bounded=bounded_scores(f)
        rows.append(dict(exponent=ex,sigma=sigma,scene=scene,seed=seed,peak_q=float(bounded[130:,0].max()),peak_r=float(bounded[130:,1].max())))
        if ex==.5:
            for profile in ['fixed','adaptive']:
                replay=sensor_replay(obs,seed,ref,profile)
                scores=np.array([r['bounded'] for r in replay['records']])
                sensor_rows.append(dict(sigma=sigma,scene=scene,seed=seed,profile=profile,
                                        peak_q=float(scores[:,0].max()),peak_r=float(scores[:,1].max()),
                                        eligible_frames=sum(r['valid'] for r in replay['records'])))
    p=dict(config=CFG,baseline=base,h_bounded_gaussian=[max(5.,1.1*max(r[f'peak_{k}'] for r in rows)) for k in ['q','r']],
           h_bounded_sensor={profile:[max(5.,1.1*max(r[f'peak_{k}'] for r in sensor_rows if r['profile']==profile)) for k in ['q','r']] for profile in ['fixed','adaptive']},
           training='Healthy-only maxima. No fault/test metrics. Sensor profiles calibrated separately.',
           sources={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [Path(__file__),BASE,ROOT/'simulation/review_operating_reference.py',ROOT/'simulation/review_diagnosis.py',ROOT/'simulation/diagnosis_review/protocol.json']})
    write_csv('fusion_healthy_training.csv',rows);write_csv('sensor_healthy_training.csv',sensor_rows);dump('frozen_parameters.json',p)
    print(json.dumps(dict(h_fusion=p['h_bounded_gaussian'],h_sensor=p['h_bounded_sensor']),ensure_ascii=False))

def aggregate(rows,phase):
    by={}
    for r in rows:
        key=(r['exponent'],r['sigma'],r['scene'],r['method'],r.get('profile',''))
        by.setdefault(key,[]).append(r)
    out=[]
    for (ex,sigma,scene,method,profile),rr in by.items():
        leads=[r['lead_s'] for r in rr if r['early_valid']];exposure=sum(r['false_exposure_s'] for r in rr)
        g=dict(exponent=ex,sigma=sigma,scene=scene,method=method,profile=profile,trials=len(rr),
               early=sum(r['early_valid'] for r in rr),false_trials=sum(r['false_onsets']>0 for r in rr),
               false_onsets=sum(r['false_onsets'] for r in rr),false_per_hour=sum(r['false_onsets'] for r in rr)*3600/exposure,
               median_valid_lead_s=float(np.median(leads)) if leads else None,
               misses=sum(r['missed_correct_pattern'] for r in rr),outcomes={o:sum(r['outcome']==o for r in rr) for o in set(r['outcome'] for r in rr)})
        if phase=='sensor':
            for name in ['observed_frames','eligible_frames','insufficient_frames','trigger_observations','send_attempts']:g['mean_'+name]=float(np.mean([r[name] for r in rr]))
        out.append(g)
    return out

def main():
    paramfile=OUT/'frozen_parameters.json';p=json.loads(paramfile.read_text(encoding='utf-8'))
    assert p['config']==CFG
    for name,digest in p['sources'].items():assert sha(ROOT/name)==digest,name
    locked=sha(paramfile);fusion=[];sensor=[];examples={};phase_rows=[]
    for ex,sigma,scene in itertools.product(EXPONENTS,SIGMAS,SCENES):
        tr=trajectory(scene,ex);ref=p['baseline']['references'][f'n{ex:g}']
        for seed in TEST:
            obs=observe(tr,sigma,seed,scene);f=features(obs,ref);bs=bounded_scores(f)
            for method in FUSIONS:
                d=fusion_decision(f,bs,p,method)
                fusion.append(dict(exponent=ex,sigma=sigma,scene=scene,seed=seed,method=method,**evaluate(d,tr,f,'reference')))
            if seed==TEST[0] and ex==.5:
                examples[f'{sigma:g}|{scene}_observed']=obs
    for sigma,scene in itertools.product(SIGMAS,SCENES):
        tr=trajectory(scene,.5);ref=p['baseline']['references']['n0.5']
        for seed in SENSOR_TEST:
            obs=observe(tr,sigma,seed,scene)
            for profile in ['fixed','adaptive']:
                replay=sensor_replay(obs,seed,ref,profile,p['h_bounded_sensor'][profile])
                for method in SENSOR_METHODS:sensor.append(dict(exponent=.5,sigma=sigma,scene=scene,seed=seed,profile=profile,method=method,**sensor_evaluate(replay,tr,method)))
                if seed==SENSOR_TEST[0] and sigma==.3 and scene in ['normal','leak','restriction','fast_leak_switch']:
                    examples[f'sensor_{scene}_{profile}']=np.array([[r['t'],int(r['valid']),*r['x'],*r['bounded']] for r in replay['records']])
            if scene=='fast_leak_switch':
                for phase in range(5):
                    replay=sensor_replay(obs,seed,ref,'adaptive',p['h_bounded_sensor']['adaptive'],phase)
                    for method in SENSOR_METHODS:phase_rows.append(dict(sigma=sigma,seed=seed,phase=phase,method=method,**sensor_evaluate(replay,tr,method)))
    write_csv('fusion_results.csv',fusion);write_csv('sensor_results.csv',sensor);write_csv('wake_phase_results.csv',phase_rows)
    np.savez_compressed(OUT/'first_seed_examples.npz',**examples)
    assert locked==sha(paramfile)
    dump('summary.json',dict(classification='synthetic_hybrid_and_acquisition_ablation',physical_data=False,
                             fusion_trajectories=2880,fusion_records=len(fusion),sensor_trajectories=432,sensor_records=len(sensor),
                             phase_records=len(phase_rows),parameters_sha256=locked,parameters=p,
                             fusion_groups=aggregate(fusion,'fusion'),sensor_groups=aggregate(sensor,'sensor'),
                             seed_reuse='Seeds reused across scenarios and noise strata. Wake phases reuse the same trajectories; not independent experiments.',
                             limitations=['same steady-state power-law model family','no real sensor dynamics or energy measurements','pulse coefficient is an assumption',
                                          'phase A and B have different frontends and cannot be pooled','insufficient windows are not normal or confirmed healthy'],
                             source_hashes={n:sha(OUT/n) for n in ['fusion_healthy_training.csv','sensor_healthy_training.csv','fusion_results.csv','sensor_results.csv','wake_phase_results.csv','first_seed_examples.npz']}))
    print(f'Fusion {len(fusion)} records; pulse-window acquisition {len(sensor)} records; wake phase {len(phase_rows)}.')
    for sigma,scene in itertools.product([.3,10.],['leak','restriction','fast_leak_switch','long_normal']):
        print('fusion',sigma,scene,[(g['method'],g['early'],g['false_trials'],g['median_valid_lead_s']) for g in aggregate(fusion,'fusion') if g['exponent']==.5 and g['sigma']==sigma and g['scene']==scene])
    for sigma,scene in itertools.product([.3,10.],['normal','leak','restriction','fast_leak_switch']):
        print('sensor',sigma,scene,[(g['profile'],g['method'],g['early'],g['false_trials'],round(g['mean_observed_frames'],1)) for g in aggregate(sensor,'sensor') if g['sigma']==sigma and g['scene']==scene])

if __name__=='__main__':
    if '--fit' in sys.argv:fit()
    else:main()
