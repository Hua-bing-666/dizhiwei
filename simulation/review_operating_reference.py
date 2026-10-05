"""Healthy-reference and transition-gate challenges; synthetic evidence only.

Offline healthy references are fitted before the independent test runs. The
online detector accepts only measured P0/P1/Q and a branch reference file.
It never receives the valve schedule, fault onset, load exponent or severity.
"""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import sys
import numpy as np
from review_diagnosis import means, hydraulics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'simulation/operating_reference_review'
EXPONENTS=[0.,.3,.5,.8]
SIGMAS=[.3,3.,10.]
REF_SEEDS=list(range(23000,23012))
LIMIT_SEEDS=list(range(24000,24012))
TEST_SEEDS=list(range(25000,25020))
METHODS=['flow','sqrt','reference','reference_gate','cusum','ewma']
SCENES=['normal','long_normal','supply_step','supply_up','supply_ramp','leak','restriction',
        'leak_switch','restriction_switch','fast_leak_switch','drift','load_unknown']
CFG=dict(version='20261006-reference-v1', monitor_start=130,
         calibration_start=20,calibration_end=120,dt_s=1,mean_samples=10,confirm_samples=5,
         q_relative_threshold=.06,r_absolute_threshold=.6,cusum_k=.5,ewma_lambda=.2,
         relative_scale_floor=.003,r_scale_floor=.03,healthy_peak_margin=1.1,
         gate_relative_pressure_change=.10,gate_lag_s=10,gate_duration_s=20,gate_rearm_s=40,
         calibration_supplies_kpa=[80,100,120,140,160],calibration_pressure_sigma_kpa=.3,
         calibration_flow_sigma_l_min=.02,reference_seeds=REF_SEEDS,limit_seeds=LIMIT_SEEDS,
         test_seeds=TEST_SEEDS,exponents=EXPONENTS,pressure_sigmas_kpa=SIGMAS,
         fixed_acquisition=True,online_rebaseline=False,energy_measured=False,
         allowed_online_inputs=['P0','P1','Q','fixed_branch_reference'],
         denied_online_inputs=['true_fault_start','true_severity','true_load_exponent','B_valve_state','future_samples'])

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
def write_csv(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def plant(ps,exponent,b,r=0.8,leak_c=0.):
    """Steady-state shared supply, nonconstant load law and additive bypass."""
    ps,b,r,leak_c=np.broadcast_arrays(np.asarray(ps,float),np.asarray(b,bool),np.asarray(r,float),np.asarray(leak_c,float))
    lo=np.zeros_like(ps);hi=ps.copy()
    gb=.35/np.sqrt(1+.8*.35**2)
    for _ in range(55):
        p1=(lo+hi)/2
        q=2.8*(p1/100)**exponent+leak_c*np.sqrt(p1)
        p0=p1+r*q*q
        source=p0+.4*(q+b*gb*np.sqrt(p0))**2
        low=source<ps;lo=np.where(low,p1,lo);hi=np.where(low,hi,p1)
    return np.column_stack([np.atleast_1d(p0),np.atleast_1d(p1),np.atleast_1d(q)])

def trajectory(scene,exponent):
    last=3600 if scene=='long_normal' else 600
    t=np.arange(last+1);b=(t%600>=180)&(t%600<300)
    ps=np.full(t.shape,120.,dtype=float);r=np.full(t.shape,.8,dtype=float);leak=np.zeros(t.shape)
    target='leak_pattern' if scene in ('leak','leak_switch','fast_leak_switch') else 'restriction_pattern' if scene in ('restriction','restriction_switch') else None
    start=180 if scene.endswith('switch') else 360
    ramp_s=45 if scene=='fast_leak_switch' else 60 if scene.endswith('switch') else 180
    ramp=np.clip((t-start)/ramp_s,0,1)
    if scene in ('supply_step','leak_switch','restriction_switch','fast_leak_switch'):
        ps[(t>=180)&(t<300)]=80.
    if scene=='supply_up':ps[(t>=180)&(t<300)]=160.
    if scene=='supply_ramp':ps-=30*np.clip((t-360)/180,0,1)
    if target=='leak_pattern' or scene=='load_unknown':leak=.09*ramp
    if target=='restriction_pattern':r+=7.2*ramp
    values=plant(ps,exponent,b,r,leak)
    healthy=plant(ps,exponent,b)
    severity=abs(values[:,2]/healthy[:,2]-1)
    return dict(t=t,values=values,healthy_q=healthy[:,2],severity=severity,
                fault_start=start if target else None,target=target,ramp_seconds=ramp_s,
                b=b,supply=ps)

def observe(tr,sigma,seed,scene):
    x=tr['values']+np.random.default_rng(seed).normal(0,[sigma,sigma,.02],tr['values'].shape)
    if scene=='drift':x[:,0]+=10*np.clip((tr['t']-360)/180,0,1)
    return x

def features(obs,reference):
    avg=means(obs);p0,p1,q=avg.T
    valid=(p1>10)&(q>.5)
    a,b=20,120
    k=q/np.sqrt(np.maximum(p1,.001));r=(p0-p1)/np.maximum(q*q,.001)
    k0=np.median(k[a:b]);r0=np.median(r[a:b]);q0=np.median(q[a:b])
    predicted=reference['a_l_min']*(np.maximum(p1,.001)/100)**reference['n_fitted']
    # A gain offset uses only the run's initial confirmed healthy calibration.
    gain=np.median(q[a:b]/predicted[a:b])
    x=np.column_stack([q/(gain*predicted)-1,r-r0])
    scale=np.maximum(1.4826*np.median(abs(x[a:b]-np.median(x[a:b],axis=0)),axis=0),[.003,.03])
    z=x/scale;cs=np.zeros_like(x);ew=np.zeros_like(x)
    gate=np.zeros(len(obs),bool);change=np.zeros(len(obs),bool);until=-1;rearm=130
    for j in range(130,len(obs)):
        if valid[j]:
            cs[j]=np.maximum(0,cs[j-1]+z[j]-.5)
            ew[j]=.2*x[j]+.8*ew[j-1]
        # Measured pressure change is not a normal-operation label.
        change[j]=bool(np.any(abs(avg[j,:2]/np.maximum(avg[j-10,:2],10)-1)>.10))
        if change[j] and j>=rearm:
            until=j+19;rearm=j+40
        gate[j]=j<=until
    return dict(avg=avg,valid=valid,x=x,scale=scale,cs=cs,ew=ew,gate=gate,change=change,
                q_change=q/q0-1,sqrt_change=k/k0-1,r_change=r-r0,
                outside_reference=(p1<reference['p1_min_kpa'])|(p1>reference['p1_max_kpa']))

def confirm(state):
    # Numeric labels: 0 normal, 1 leak, 2 restriction, 3 uncertain,
    # -1 invalid, -2 transition-review (not treated as normal).
    stable=state>0
    for lag in range(1,5):stable[lag:] &= state[lag:]==state[:-lag]
    stable[:134]=False
    events=[];active=0
    names={1:'leak_pattern',2:'restriction_pattern',3:'uncertain'}
    for j in range(130,len(state)):
        label=int(state[j])
        if label<=0:active=0
        elif stable[j]:
            if active!=label:events.append(dict(t_s=j,pattern=names[label]))
            active=label
    return events

def decision(f,method,params):
    if method=='flow':a=f['q_change']>.06;b=f['q_change']<-.06
    elif method=='sqrt':a=f['sqrt_change']>.06;b=f['r_change']>.6
    elif method in ('reference','reference_gate'):a=f['x'][:,0]>.06;b=f['x'][:,1]>.6
    elif method=='cusum':a=f['cs'][:,0]>params['h_cusum'][0];b=f['cs'][:,1]>params['h_cusum'][1]
    elif method=='ewma':a=f['ew'][:,0]>params['h_ewma'][0];b=f['ew'][:,1]>params['h_ewma'][1]
    else:raise ValueError(method)
    state=a.astype(np.int8)+2*b.astype(np.int8)
    state[~f['valid']]=-1
    if method=='reference_gate':state[f['gate']&f['valid']]=-2
    return dict(state=state,events=confirm(state))

def evaluate(d,tr,f,method):
    fault=tr['target'] is not None;start=tr['fault_start'];events=d['events']
    pre=[e for e in events if e['t_s']<start] if fault else events
    post=[e for e in events if e['t_s']>=start] if fault else []
    first=post[0] if post else None
    hits=np.flatnonzero((tr['t']>=start)&(tr['severity']>=.15)) if fault else []
    critical=int(hits[0]) if len(hits) else None
    correct=[e for e in post if e['pattern']==tr['target']]
    detected=correct[0]['t_s'] if correct else None
    good=bool(fault and not pre and first and first['pattern']==tr['target'] and critical is not None and first['t_s']<critical)
    outcome='control' if not fault else 'prior_false_alarm' if pre else 'no_detection' if not first else 'wrong_first' if first['pattern']!=tr['target'] else 'valid_early' if good else 'late_or_no_reference'
    gate=f['gate'] if method=='reference_gate' else np.zeros(len(f['gate']),bool)
    onset=gate&~np.r_[False,gate[:-1]]
    exposure=(start if fault else len(tr['t'])-1)-130
    return dict(false_onsets=len(pre),false_exposure_s=exposure,
                early_valid=good,outcome=outcome,first_post_s=first['t_s'] if first else None,
                first_pattern=first['pattern'] if first else None,first_correct_s=detected,critical_s=critical,
                lead_s=critical-first['t_s'] if good else None,
                missed_correct_pattern=bool(fault and detected is None),
                transition_review_onsets=int(onset[130:].sum()),
                paused_observations=int(gate[130:].sum()),
                paused_before_reference=int(gate[start:critical].sum()) if critical is not None else 0,
                outside_reference_observations=int(f['outside_reference'][130:].sum()))

def fit():
    OUT.mkdir(parents=True,exist_ok=True)
    refs={};points=[]
    for exponent in EXPONENTS:
        rp=[]
        for supply,b,seed in itertools.product(CFG['calibration_supplies_kpa'],[False,True],REF_SEEDS):
            v=np.repeat(plant(supply,exponent,b),60,axis=0)
            obs=v+np.random.default_rng(seed+int(supply)*100+int(b)).normal(0,[.3,.3,.02],v.shape)
            avg=obs[10:].mean(axis=0)
            rp.append(avg);points.append(dict(recipe=f'n{exponent:g}',supply_kpa=supply,b_open=b,seed=seed,
                                             mean_p0=float(avg[0]),mean_p1=float(avg[1]),mean_q=float(avg[2])))
        rp=np.array(rp);n,loga=np.polyfit(np.log(rp[:,1]/100),np.log(rp[:,2]),1)
        refs[f'n{exponent:g}']=dict(n_fitted=float(n),a_l_min=float(np.exp(loga)),
                                   p1_min_kpa=float(rp[:,1].min()),p1_max_kpa=float(rp[:,1].max()),
                                   healthy_points=len(rp),synthetic_calibration=True)
    limits=[]
    for exponent,sigma,scene,seed in itertools.product(EXPONENTS,SIGMAS,['normal','supply_step','supply_up','supply_ramp'],LIMIT_SEEDS):
        tr=trajectory(scene,exponent);f=features(observe(tr,sigma,seed,scene),refs[f'n{exponent:g}'])
        limits.append(dict(recipe=f'n{exponent:g}',sigma=sigma,scene=scene,seed=seed,
                           peak_cs_q=float(f['cs'][130:,0].max()),peak_cs_r=float(f['cs'][130:,1].max()),
                           peak_ew_q=float(f['ew'][130:,0].max()),peak_ew_r=float(f['ew'][130:,1].max())))
    params=dict(config=CFG,references=refs,
                h_cusum=[max(5.,1.1*max(r[f'peak_cs_{k}'] for r in limits)) for k in ['q','r']],
                h_ewma=[max(floor,1.1*max(r[f'peak_ew_{k}'] for r in limits)) for k,floor in [('q',.06),('r',.6)]],
                selection='Health-only full trajectory maxima with 10% margin; no fault or test outcomes.',
                sources={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'simulation/review_diagnosis.py',ROOT/'simulation/diagnosis_review/protocol.json']})
    write_csv('healthy_reference_points.csv',points);write_csv('healthy_limit_training.csv',limits)
    dump('frozen_parameters.json',params)
    print(json.dumps(dict(references=refs,h_cusum=params['h_cusum'],h_ewma=params['h_ewma']),ensure_ascii=False))

def aggregate(rows):
    gg=[]
    for exponent,sigma,scene,method in itertools.product(EXPONENTS,SIGMAS,SCENES,METHODS):
        rr=[r for r in rows if r['exponent']==exponent and r['sigma']==sigma and r['scene']==scene and r['method']==method]
        leads=[r['lead_s'] for r in rr if r['early_valid']]
        exposure=sum(r['false_exposure_s'] for r in rr)
        gg.append(dict(exponent=exponent,sigma=sigma,scene=scene,method=method,trials=len(rr),
                       early=sum(r['early_valid'] for r in rr),false_trials=sum(r['false_onsets']>0 for r in rr),
                       false_onsets=sum(r['false_onsets'] for r in rr),exposure_s=exposure,
                       false_onsets_per_hour=sum(r['false_onsets'] for r in rr)*3600/exposure,
                       misses=sum(r['missed_correct_pattern'] for r in rr),
                       median_valid_lead_s=float(np.median(leads)) if leads else None,
                       mean_review_onsets=float(np.mean([r['transition_review_onsets'] for r in rr])),
                       mean_paused_observations=float(np.mean([r['paused_observations'] for r in rr])),
                       mean_outside_reference_observations=float(np.mean([r['outside_reference_observations'] for r in rr])),
                       outcomes={o:sum(r['outcome']==o for r in rr) for o in sorted(set(r['outcome'] for r in rr))}))
    return gg

def main():
    paramfile=OUT/'frozen_parameters.json';p=json.loads(paramfile.read_text(encoding='utf-8'))
    assert p['config']==CFG
    for name,digest in p['sources'].items():assert sha(ROOT/name)==digest,name
    assert not set(REF_SEEDS)&set(LIMIT_SEEDS) and not (set(REF_SEEDS)|set(LIMIT_SEEDS))&set(TEST_SEEDS)
    locked_hash=sha(paramfile);rows=[];examples={}
    # Inputs are reproducible from the frozen script and seeds. Save explicit
    # first-seed observations for every scenario; no favourable example selection.
    for exponent,sigma,scene in itertools.product(EXPONENTS,SIGMAS,SCENES):
        tr=trajectory(scene,exponent)
        for seed in TEST_SEEDS:
            obs=observe(tr,sigma,seed,scene);f=features(obs,p['references'][f'n{exponent:g}'])
            for method in METHODS:
                d=decision(f,method,p)
                rows.append(dict(trial=f'{exponent:g}|{sigma:g}|{scene}|{seed}',exponent=exponent,
                                 sigma=sigma,scene=scene,seed=seed,method=method,**evaluate(d,tr,f,method)))
            if seed==TEST_SEEDS[0]:
                key=f'{exponent:g}|{sigma:g}|{scene}'
                examples[key+'_observed']=obs;examples[key+'_severity']=tr['severity']
    write_csv('paired_results.csv',rows);np.savez_compressed(OUT/'first_seed_examples.npz',**examples)
    assert sha(paramfile)==locked_hash
    summary=dict(classification='synthetic_operating_reference_comparison',physical_data=False,
                 paired_records=len(rows),scenario_trajectories=len(rows)//len(METHODS),unique_test_seeds=len(TEST_SEEDS),
                 parameters_sha256=locked_hash,parameters=p,groups=aggregate(rows),
                 seed_reuse='20 base noise seeds reused across exponents, scenarios and sigmas. Long traces share initial samples. Not independent physical runs.',
                 assumptions=['steady-state branch model','single equivalent fault','healthy recipe pre-calibrated','no real sensor dynamics'],
                 gate_output='transition_review, not healthy or confirmed valve operation',
                 reference_domain='Out-of-calibration observations are counted, not suppressed. Predictions there are extrapolations.',
                 examples_seed=TEST_SEEDS[0],full_raw_storage='First-seed examples stored; all runs deterministically regenerable from locked source and seed CSV.',
                 source_hashes={name:sha(OUT/name) for name in ['healthy_reference_points.csv','healthy_limit_training.csv','paired_results.csv','first_seed_examples.npz']})
    dump('summary.json',summary)
    print(f'{summary["scenario_trajectories"]} synthetic trajectories, {len(rows)} paired records.')
    for sigma,scene in itertools.product([.3,10.],['supply_step','leak','restriction','fast_leak_switch','long_normal']):
        print(sigma,scene,[(g['method'],g['early'],g['false_trials'],g['median_valid_lead_s']) for g in summary['groups'] if g['exponent']==.5 and g['sigma']==sigma and g['scene']==scene])

if __name__=='__main__':
    if '--fit' in sys.argv:fit()
    else:main()
