"""Frozen fourth-round sensor quality and 1/2/5-second scheduling challenges."""
from pathlib import Path
import csv,itertools,json,sys
import numpy as np
from review_operating_reference import plant,observe,trajectory,sha
from review_hybrid_sampling import pulse_frontend
from sampling_quality_runtime import SamplingNode,METHODS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/quality_interval_review'
BASE=ROOT/'simulation/hybrid_sampling_review/frozen_parameters.json'
TRAIN=list(range(40000,40012));TEST=list(range(41000,41016));SIGMAS=[.3,3.,10.];PERIODS=[1,2,5]
SCENES=['normal','long_normal','supply_step','supply_ramp','leak_r30','leak_r90','leak_r360','leak_r720',
        'restriction_r30','restriction_r90','restriction_r360','pulse8','pulse20','pulse40','fast_leak_switch']
QUALITY_CASES=['normal','supply_step','drift_p0','bias_p0','bias_p1','bias_initial','spike_range','nan_pressure',
               'stuck_p0','counter_reset','bad_calibration','fault_initial']
CFG=dict(version='20261006-quality-interval-v1',training_seeds=TRAIN,test_seeds=TEST,pressure_sigmas=SIGMAS,
    periods_s=PERIODS,all_integer_phases=True,quality_modes=['finite','range'],pressure_range_assumption_kpa=[0,200],
    model_exponent=.5,pressure_window_actual_points=10,pulse_window_bins=10,pulses_per_litre_assumption=540,
    continuous_one_second_counter_snapshots=True,confirmation_points=5,high_hold_observations=30,
    initial_calibration=[20,120],monitor_start=130,healthy_peak_margin=1.1,fast_scale_multiplier=6,
    online_drift_recalibration=False,physical_data=False,energy_measured=False,
    input_to_runtime=['timestamp','cumulative_counter','requested_pressure_read'],
    excluded_runtime_inputs=['scenario','fault_time','fault_duration','true_severity','unread_pressure','future'])

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def write(name,rr):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]),lineterminator='\n');w.writeheader();w.writerows(rr)

def scene_trace(scene):
    if scene in ['normal','supply_step','supply_ramp','fast_leak_switch']:
        tr=trajectory(scene,.5);tr['fault_end']=None;return tr
    if scene=='long_normal':
        tr=trajectory('long_normal',.5)
        for k,v in list(tr.items()):
            if isinstance(v,np.ndarray):tr[k]=v[:1801]
        tr['fault_end']=None;return tr
    prefix,number=('pulse',scene[5:]) if scene.startswith('pulse') else scene.rsplit('_r',1)
    ramp_s=int(number);start=360;last=max(600,start+ramp_s+180);t=np.arange(last+1)
    b=(t%600>=180)&(t%600<300);ps=np.full(len(t),120.);r=np.full(len(t),.8);leak=np.zeros(len(t));end=None
    if prefix=='pulse':
        end=start+ramp_s;leak=.12*np.where((t>=start)&(t<end),np.minimum((t-start)/4,1),0)
        target='leak_pattern'
    else:
        ramp=np.clip((t-start)/ramp_s,0,1);target='leak_pattern' if prefix=='leak' else 'restriction_pattern'
        if prefix=='leak':leak=.09*ramp
        else:r+=7.2*ramp
    values=plant(ps,.5,b,r,leak);healthy=plant(ps,.5,b)
    return dict(t=t,values=values,healthy_q=healthy[:,2],severity=abs(values[:,2]/healthy[:,2]-1),
        fault_start=start,fault_end=end,target=target,ramp_seconds=ramp_s,b=b,supply=ps)

def inputs(scene,sigma,seed,quality_case=False):
    if not quality_case:
        tr=scene_trace(scene);obs=observe(tr,sigma,seed,scene);counts=pulse_frontend(obs,seed)['cumulative']
        return tr,obs,counts
    tr=scene_trace('supply_step' if scene=='supply_step' else 'normal')
    if scene=='fault_initial':
        tr['values']=plant(tr['supply'],.5,tr['b'],leak_c=.09)
        tr['severity']=abs(tr['values'][:,2]/tr['healthy_q']-1)
        tr['fault_start']=0;tr['target']='leak_pattern'
    obs=observe(tr,sigma,seed,'normal');t=tr['t']
    if scene=='drift_p0':obs[:,0]+=10*np.clip((t-360)/180,0,1)
    if scene=='bias_p0':obs[t>=360,0]+=10
    if scene=='bias_p1':obs[t>=360,1]-=10
    if scene=='bias_initial':obs[:,0]+=10
    if scene=='spike_range':obs[360,0]=250
    if scene=='nan_pressure':obs[360:365,1]=np.nan
    if scene=='stuck_p0':obs[360:,0]=obs[359,0]
    if scene=='bad_calibration':obs[40,1]=np.nan
    counts=pulse_frontend(obs,seed)['cumulative']
    if scene=='counter_reset':counts[420:]-=counts[419]
    return tr,obs,counts

def replay(obs,counts,reference,limits,period,phase,quality='range'):
    node=SamplingNode(reference,limits,period,phase,quality)
    for t,count in enumerate(counts):node.update(t,int(count),obs[t,:2] if node.pressure_due(t) else None)
    return node.output()

def metrics(out,tr,method):
    events=out['decisions'][method]['events'];start=tr['fault_start'];end=tr['fault_end'];fault=tr['target'] is not None
    before=[e for e in events if e['t_s']<start] if fault else events
    after=[e for e in events if e['t_s']>=start] if fault else []
    first=after[0] if after else None
    hit=np.flatnonzero((tr['t']>=start)&(tr['severity']>=.15)) if fault else []
    critical=int(hit[0]) if len(hit) else None
    correct=[e for e in after if e['pattern']==tr['target'] and (end is None or e['t_s']<end)]
    good=bool(fault and not before and first and first['pattern']==tr['target'] and critical is not None and first['t_s']<critical)
    reason='control' if not fault else 'prior_false_alarm' if before else 'no_detection' if not first else 'wrong_first' if first['pattern']!=tr['target'] else 'valid_early' if good else 'after_recovery' if end is not None and first['t_s']>=end else 'late'
    rr=out['records'];eligible=sum(r['valid'] for r in rr);wall=len(tr['t'])-130
    return dict(early_valid=good,outcome=reason,first_post_s=first['t_s'] if first else None,
        first_pattern=first['pattern'] if first else None,critical_s=critical,lead_s=critical-first['t_s'] if good else None,
        correct_during_fault=bool(correct),false_onsets=len(before),baseline_accepted=out['baseline_accepted'],
        monitoring_points=wall,observed_frames=len(rr),eligible_frames=eligible,unavailable_points=wall-eligible,
        quality_events=sum(e['t_s']>=130 for e in out['quality_events']),trigger_observations=len(out['triggers']),
        diagnostic_status_counts=json.dumps({k:sum(r['status']==k for r in rr) for k in sorted({r['status'] for r in rr})},sort_keys=True))

def fit():
    OUT.mkdir(exist_ok=True);base=json.loads(BASE.read_text(encoding='utf-8'));ref=base['baseline']['references']['n0.5'];rows=[]
    for sigma,scene,seed,period in itertools.product(SIGMAS,['normal','supply_step','supply_ramp','long_normal'],TRAIN,PERIODS):
        tr,obs,counts=inputs(scene,sigma,seed)
        for phase in range(period):
            out=replay(obs,counts,ref,[1e9,1e9],period,phase)
            scores=np.array([r['bounded'] for r in out['records']])
            rows.append(dict(sigma=sigma,scene=scene,seed=seed,period=period,phase=phase,
                peak_q=float(scores[:,0].max()),peak_r=float(scores[:,1].max()),eligible_frames=sum(r['valid'] for r in out['records'])))
    limits={str(period):[max(5.,1.1*max(r[f'peak_{k}'] for r in rows if r['period']==period)) for k in ['q','r']] for period in PERIODS}
    write('healthy_training.csv',rows)
    dump('frozen_parameters.json',dict(config=CFG,reference=ref,limits=limits,
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'simulation/sampling_quality_runtime.py',BASE,ROOT/'simulation/review_hybrid_sampling.py',ROOT/'simulation/review_operating_reference.py']},
        training_sha256=sha(OUT/'healthy_training.csv'),selection='Healthy maxima including long-normal and every integer phase. No test faults.'))
    print(json.dumps(dict(training_rows=len(rows),limits=limits)),flush=True)

def aggregate(rows,stage):
    lookup={}
    for r in rows:
        key=(r['sigma'],r['scene'],r['period'],r['phase'],r['quality'],r['method']);lookup.setdefault(key,[]).append(r)
    groups=[]
    for (sigma,scene,period,phase,quality,method),rr in lookup.items():
        lead=[r['lead_s'] for r in rr if r['early_valid']]
        groups.append(dict(sigma=sigma,scene=scene,period=period,phase=phase,quality=quality,method=method,trials=len(rr),
            early=sum(r['early_valid'] for r in rr),correct_during_fault=sum(r['correct_during_fault'] for r in rr),
            false_trials=sum(r['false_onsets']>0 for r in rr),baseline_accepted=sum(r['baseline_accepted'] for r in rr),
            quality_flagged_trials=sum(r['quality_events']>0 for r in rr),
            mean_observed_frames=float(np.mean([r['observed_frames'] for r in rr])),
            mean_eligible_frames=float(np.mean([r['eligible_frames'] for r in rr])),
            mean_monitoring_points=float(np.mean([r['monitoring_points'] for r in rr])),
            median_valid_lead_s=float(np.median(lead)) if lead else None,
            outcomes={k:sum(r['outcome']==k for r in rr) for k in sorted({r['outcome'] for r in rr})}))
    return groups

def main():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'));assert p['config']==CFG
    for name,digest in p['sources'].items():assert sha(ROOT/name)==digest,name
    assert sha(OUT/'healthy_training.csv')==p['training_sha256'];locked=sha(OUT/'frozen_parameters.json')
    sampling=[];quality=[];examples={}
    for sigma,scene,seed,period in itertools.product(SIGMAS,SCENES,TEST,PERIODS):
        tr,obs,counts=inputs(scene,sigma,seed)
        for phase in range(period):
            out=replay(obs,counts,p['reference'],p['limits'][str(period)],period,phase)
            for method in METHODS:sampling.append(dict(sigma=sigma,scene=scene,seed=seed,period=period,phase=phase,quality='range',method=method,**metrics(out,tr,method)))
        if seed==TEST[0] and sigma==.3 and period==1:examples[scene]=obs
    print(f'Sampling records: {len(sampling)}',flush=True)
    for sigma,scene,seed,mode in itertools.product(SIGMAS,QUALITY_CASES,TEST,['finite','range']):
        tr,obs,counts=inputs(scene,sigma,seed,True)
        out=replay(obs,counts,p['reference'],p['limits']['1'],1,0,mode)
        for method in METHODS:quality.append(dict(sigma=sigma,scene=scene,seed=seed,period=1,phase=0,quality=mode,method=method,**metrics(out,tr,method)))
        if seed==TEST[0] and sigma==.3 and mode=='range':examples['quality_'+scene]=obs
    write('sampling_results.csv',sampling);write('quality_results.csv',quality)
    np.savez_compressed(OUT/'first_seed_examples.npz',**examples)
    assert locked==sha(OUT/'frozen_parameters.json')
    dump('summary.json',dict(physical_data=False,stage='fourth_round_quality_and_intervals',parameters_sha256=locked,
        sampling_records=len(sampling),quality_records=len(quality),parameters=p,
        sampling_groups=aggregate(sampling,'sampling'),quality_groups=aggregate(quality,'quality'),
        dependence='Same seeds across cases, sigma and periods. Phases reuse traces; not independent physical trials.',
        limitations=['same quasi-steady hydraulic model','one-second synthetic counter snapshot dependency','no measured energy or ADC timing',
                     'range checks cannot establish sensor accuracy or healthy calibration','no pressure imputation','finite episode detection must precede recovery'],
        source_hashes={name:sha(OUT/name) for name in ['sampling_results.csv','quality_results.csv','first_seed_examples.npz']}))
    print(f'Quality records: {len(quality)}. Frozen files unchanged.',flush=True)

if __name__=='__main__':
    if '--fit' in sys.argv:fit()
    else:main()
