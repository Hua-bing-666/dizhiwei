"""Reproduce Section 8 and evaluate 100 new paired noise seeds, without retuning."""
from pathlib import Path
import sys, json, csv, hashlib, itertools, time, shutil
import numpy as np

BASE=Path(__file__).resolve().parents[1]
PROJECT=BASE.parents[1]
SRC=BASE/'code'/'snapshot'
if not SRC.exists():
    SRC.mkdir(parents=True)
    for name in ['review_hybrid_sampling.py','review_operating_reference.py','review_diagnosis.py','diagnosis_feasibility.py']:
        shutil.copy2(PROJECT/'simulation'/name,SRC/name)
    # Imported modules resolve ROOT as code/. All their output functions are unused.
    p=BASE/'code'/'simulation'/'diagnosis_review';p.mkdir(parents=True)
    shutil.copy2(PROJECT/'simulation/diagnosis_review/protocol.json',p/'protocol.json')
    shutil.copy2(PROJECT/'simulation/hybrid_sampling_review/frozen_parameters.json',BASE/'evidence/frozen_parameters.json')
    shutil.copy2(PROJECT/'simulation/hybrid_sampling_review/sensor_results.csv',BASE/'evidence/original_sensor_results.csv')
sys.path.insert(0,str(SRC))
import review_hybrid_sampling as h
import review_operating_reference as o
import review_diagnosis as d

E=BASE/'evidence'; E.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x): (E/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def csvwrite(name,rows):
    with (E/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;delta=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,mid-delta),min(1.,mid+delta)]

def main():
    tick=time.time();p=json.loads((E/'frozen_parameters.json').read_text(encoding='utf-8'))
    lock=sha(E/'frozen_parameters.json');ref=p['baseline']['references']['n0.5']
    scenes=['leak','restriction','long_normal'];sigmas=[.3,3.,10.]
    newseeds=list(range(61000,61100));oldseeds=list(range(28000,28012))
    train=set(p['config']['training_seeds'])|set(p['baseline']['config']['reference_seeds'])|set(p['baseline']['config']['limit_seeds'])
    assert not train.intersection(newseeds+oldseeds)
    originals=list(csv.DictReader((E/'original_sensor_results.csv').open(encoding='utf-8-sig')))
    index={(r['scene'],float(r['sigma']),int(r['seed']),r['method']):r for r in originals if r['profile']=='fixed'}
    rows=[];raw={};checked=0
    for batch,seeds in [('reproduction',oldseeds),('holdout100',newseeds)]:
        for scene,sigma in itertools.product(scenes,sigmas):
            tr=o.trajectory(scene,.5)
            for seed in seeds:
                obs=o.observe(tr,sigma,seed,scene)
                replay=h.sensor_replay(obs,seed,ref,'fixed',p['h_bounded_sensor']['fixed'])
                for method in h.SENSOR_METHODS:
                    metric=h.sensor_evaluate(replay,tr,method)
                    if batch=='reproduction':
                        old=index[(scene,sigma,seed,method)]
                        for key,val in metric.items():
                            if val is None: assert old[key]=='',(key,val,old[key])
                            elif isinstance(val,bool): assert old[key]==str(val),(key,val,old[key])
                            elif isinstance(val,(int,float,np.number)): assert np.isclose(float(old[key]),val,rtol=1e-10,atol=1e-10),(key,val,old[key])
                            else: assert old[key]==str(val),(key,val,old[key])
                        checked+=1
                    rows.append(dict(batch=batch,scene=scene,sigma=sigma,seed=seed,method=method,**metric))
                if seed==newseeds[0] and scene!='long_normal':
                    stem=f'{scene}_{sigma:g}'
                    raw[stem+'_observed']=obs;raw[stem+'_truth']=tr['values'];raw[stem+'_severity']=tr['severity']
                    raw[stem+'_features']=np.array([[r['t'],*r['x']] for r in replay['records']])
                    raw[stem+'_thresholds']=np.maximum([.06,.6],6*np.array(replay['context']['scale']))
            print(f'{batch} {scene} sigma={sigma:g}: {len(seeds)} traces, {time.time()-tick:.1f}s',flush=True)
    csvwrite('paired_method_results.csv',rows)
    groups=[]
    for batch,scene,sigma,method in itertools.product(['reproduction','holdout100'],scenes,sigmas,h.SENSOR_METHODS):
        rr=[r for r in rows if (r['batch'],r['scene'],r['sigma'],r['method'])==(batch,scene,sigma,method)]
        n=len(rr);early=sum(r['early_valid'] for r in rr);false=sum(r['false_onsets']>0 for r in rr)
        leads=[r['lead_s'] for r in rr if r['early_valid']]
        groups.append(dict(batch=batch,scene=scene,sigma=sigma,method=method,n=n,early=early,false_trials=false,
            early_ci95=wilson(early,n),false_ci95=wilson(false,n),median_lead_s=float(np.median(leads)) if leads else None,
            lead_q25_q75=np.quantile(leads,[.25,.75]).tolist() if leads else None,
            outcomes={k:sum(r['outcome']==k for r in rr) for k in sorted({r['outcome'] for r in rr})}))
    # Initial K/R counterexamples: keep their model and their 20 original seeds distinct.
    counter=[];counterarrays={};maxdiff=0.;maxmass=0.;maxbalance=0.
    for sigma in [.3,1.,3.,10.]:
        arrays={kind:[] for kind in ['leak_k','load_k','drift_r','normal_r']}
        for seed in range(10300,10320):
            bykind={}
            for kind in ['leak','load_unknown','drift','normal']:
                t,values,_,severity=d.truth(kind)
                obs=values+np.random.default_rng(seed).normal(0,[sigma,sigma,.02],values.shape)
                if kind=='drift':obs[:,0]+=10*np.clip((t-360)/180,0,1)
                fit=d.classify(obs,'physical');bykind[kind]=obs
                arrays[{'leak':'leak_k','load_unknown':'load_k','drift':'drift_r','normal':'normal_r'}[kind]].append(
                    (fit['k']/fit['k0']-1)*100 if kind in ['leak','load_unknown'] else fit['r']-fit['r0'])
                post=[e for e in fit['events'] if e['t_s']>=360]
                counter.append(dict(sigma=sigma,seed=seed,scene=kind,any_post_candidate=bool(post),
                    first_post_s=post[0]['t_s'] if post else None,first_pattern=post[0]['pattern'] if post else None,
                    prior_false=any(e['t_s']<360 for e in fit['events'])))
            maxdiff=max(maxdiff,float(np.max(abs(bykind['leak']-bykind['load_unknown']))))
        for kind,a in arrays.items():counterarrays[f'{kind}_{sigma:g}']=np.array(a)
    # Independent conservation checks on the new plant, away from detector calculations.
    for scene in ['normal','leak','restriction','supply_step']:
        tr=o.trajectory(scene,.5);p0,p1,q=tr['values'].T
        qb=np.where(tr['b'],.35/np.sqrt(1+.8*.35**2)*np.sqrt(p0),0.)
        maxbalance=max(maxbalance,float(np.max(abs(tr['supply']-p0-.4*(q+qb)**2))))
        ramp=np.clip((tr['t']-360)/180,0,1)
        c=.09*ramp if scene=='leak' else np.zeros(len(q))
        maxmass=max(maxmass,float(np.max(abs(q-(2.8*np.sqrt(p1/100)+c*np.sqrt(p1))))))
    assert maxdiff==0. and maxmass<1e-10 and maxbalance<1e-9
    assert checked==324 and len(rows)==3024 and lock==sha(E/'frozen_parameters.json')
    csvwrite('counterexample_results.csv',counter)
    np.savez_compressed(E/'trace_data.npz',**raw,**counterarrays)
    report=dict(physical_data=False,parameter_retuning=False,training_test_seed_disjoint=True,
        original_method_records_reproduced=checked,original_trajectories=108,new_holdout_trajectories=900,
        new_holdout_method_records=2700,unique_new_noise_seeds=100,counterexample_trajectories=320,
        seed_dependence='Noise seeds are reused across scene and sigma strata. Never pool as independent physical experiments.',
        early_criterion='No pre-fault alarm; first post-fault pattern correct; confirmed before 15% truth-derived flow deviation.',
        normal_exposure_per_trace_s=3470,normal_observations_per_trace=3471,
        time_step_s=1,pressure_window_s=10,confirmation_updates=5,
        gaussian_pressure_noise='Independent channels; sigma is a synthetic stochastic assumption, not an accuracy specification.',
        frozen_parameter_sha256=lock,groups=groups,
        model_checks=dict(max_leak_load_observation_difference=maxdiff,max_flow_equation_residual=maxmass,
            max_supply_pressure_balance_residual_kpa=maxbalance),
        source_sha256={str(f.relative_to(BASE)):sha(f) for f in sorted(SRC.glob('*.py'))},seconds=round(time.time()-tick,2))
    dump('simulation_report.json',report)
    print('COMPLETE '+json.dumps({k:report[k] for k in ['original_method_records_reproduced','new_holdout_trajectories','seconds']}),flush=True)

if __name__=='__main__':main()
