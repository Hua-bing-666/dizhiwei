"""Reproduce the paired records and challenge causal/physical invariants."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from review_operating_reference import (CFG,EXPONENTS,SIGMAS,METHODS,SCENES,TEST_SEEDS,
    REF_SEEDS,LIMIT_SEEDS,plant,trajectory,observe,features,decision,evaluate)
from review_diagnosis import hydraulics
from reference_runtime import ReferenceDiagnostic
OUT=ROOT/'simulation/operating_reference_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csv_rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    s=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    assert p['config']==CFG and s['parameters_sha256']==sha(OUT/'frozen_parameters.json')
    for name,digest in p['sources'].items():assert sha(ROOT/name)==digest
    for name,digest in s['source_hashes'].items():assert sha(OUT/name)==digest
    assert not(set(REF_SEEDS)&set(LIMIT_SEEDS)) and not (set(REF_SEEDS)|set(LIMIT_SEEDS))&set(TEST_SEEDS)
    points=csv_rows('healthy_reference_points.csv');limits=csv_rows('healthy_limit_training.csv')
    assert len(points)==480 and len(limits)==576
    assert set(r['scene'] for r in limits)=={'normal','supply_step','supply_up','supply_ramp'}
    # Independently fit the healthy regressions and recalculate the fixed limits.
    for exponent in EXPONENTS:
        recipe=f'n{exponent:g}';rr=[r for r in points if r['recipe']==recipe]
        xx=np.array([float(r['mean_p1']) for r in rr]);yy=np.array([float(r['mean_q']) for r in rr])
        n,intercept=np.polyfit(np.log(xx/100),np.log(yy),1)
        assert np.isclose(p['references'][recipe]['n_fitted'],n,atol=1e-14)
        assert np.isclose(p['references'][recipe]['a_l_min'],np.exp(intercept),atol=1e-14)
    for index,k in enumerate(['q','r']):
        assert p['h_cusum'][index]==max(5.,1.1*max(float(r[f'peak_cs_{k}']) for r in limits))
        assert p['h_ewma'][index]==max([.06,.6][index],1.1*max(float(r[f'peak_ew_{k}']) for r in limits))
    # Original square-root model must be recovered, not silently replaced.
    for ps in [80.,120.,160.]:
        for b in [False,True]:
            for r,leak in [(.8,0.),(8.,0.),(.8,.09)]:
                v=plant(ps,.5,b,r,leak)[0]
                assert np.allclose(v,hydraulics(ps,.28+leak,r,b),rtol=1e-12,atol=1e-10)
                assert np.isclose(v[0]-v[1],r*v[2]**2,rtol=1e-12)
    results=csv_rows('paired_results.csv');assert len(results)==17280
    lookup={(r['trial'],r['method']):r for r in results};assert len(lookup)==len(results)
    examples=np.load(OUT/'first_seed_examples.npz',allow_pickle=False)
    tested=0;cache={(ex,sc):trajectory(sc,ex) for ex in EXPONENTS for sc in SCENES}
    for ex in EXPONENTS:
        for sigma in SIGMAS:
            for scene in SCENES:
                tr=cache[(ex,scene)]
                for seed in TEST_SEEDS:
                    obs=observe(tr,sigma,seed,scene);f=features(obs,p['references'][f'n{ex:g}'])
                    tid=f'{ex:g}|{sigma:g}|{scene}|{seed}'
                    if seed==25000:
                        assert np.array_equal(obs,examples[f'{ex:g}|{sigma:g}|{scene}_observed'])
                        assert np.array_equal(tr['severity'],examples[f'{ex:g}|{sigma:g}|{scene}_severity'])
                    for method in METHODS:
                        v=evaluate(decision(f,method,p),tr,f,method);saved=lookup[(tid,method)]
                        for key,value in v.items():
                            if value is None:assert saved[key]==''
                            elif isinstance(value,float):assert np.isclose(float(saved[key]),value,rtol=1e-12,atol=1e-12)
                            else:assert saved[key]==str(value),(tid,method,key)
                        tested+=1
    # Detectors cannot react to future values or receive truth/schedule arrays.
    tr=cache[(.5,'fast_leak_switch')];obs=observe(tr,.3,25000,'fast_leak_switch')
    f=features(obs,p['references']['n0.5']);cut=185
    altered=obs.copy();altered[cut+1:]=999
    ff=features(altered,p['references']['n0.5'])
    for key in ['x','cs','ew','gate','change']:
        assert np.array_equal(f[key][:cut+1],ff[key][:cut+1]),key
    for method in METHODS:
        a,b=decision(f,method,p),decision(ff,method,p)
        assert np.array_equal(a['state'][:cut+1],b['state'][:cut+1])
        assert [e for e in a['events'] if e['t_s']<=cut]==[e for e in b['events'] if e['t_s']<=cut]
    # Independent EWMA scalar arithmetic for both residual channels.
    value=[0.,0.]
    for j in range(130,len(obs)):
        for k in range(2):
            value[k]=.2*float(f['x'][j,k])+.8*value[k] if f['valid'][j] else 0.
        assert np.allclose(value,f['ew'][j],rtol=1e-12,atol=1e-12)
    # Every transition episode is bounded and remains review, never 'healthy'.
    on=np.flatnonzero(f['gate']&~np.r_[False,f['gate'][:-1]])
    for t in on:
        assert f['change'][t]
        assert np.all(f['gate'][t:min(t+20,len(obs))])
        assert t+20>=len(obs) or not f['gate'][t+20]
    assert np.all(decision(f,'reference_gate',p)['state'][f['gate']&f['valid']]==-2)
    # An unannounced healthy load change stays observationally ambiguous.
    leak=observe(cache[(.5,'leak')],.3,25000,'leak')
    unknown=observe(cache[(.5,'load_unknown')],.3,25000,'load_unknown')
    assert np.array_equal(leak,unknown)
    assert decision(features(leak,p['references']['n0.5']),'reference',p)['events']==decision(features(unknown,p['references']['n0.5']),'reference',p)['events']
    # A separate streaming implementation cannot inspect a whole observation file.
    stream_runs=0
    for ex,sc in [(0.,'supply_step'),(.3,'leak'),(.5,'fast_leak_switch'),(.8,'long_normal')]:
        tr=cache[(ex,sc)];obs=observe(tr,3.,25000,sc);f=features(obs,p['references'][f'n{ex:g}'])
        for method in METHODS:
            stream=ReferenceDiagnostic(p['references'][f'n{ex:g}'],p,method);events=[]
            for t,x in enumerate(obs):
                got=stream.update(t,*x)
                if t>=130:
                    assert np.allclose(got['residual'],f['x'][t],rtol=1e-9,atol=1e-10)
                    assert np.allclose(got['cusum'],f['cs'][t],rtol=1e-9,atol=1e-8)
                    assert np.allclose(got['ewma'],f['ew'][t],rtol=1e-9,atol=1e-10)
                    assert got['transition_flag']==bool(f['gate'][t])
                    if got['event']:events.append(got['event'])
            assert events==decision(f,method,p)['events'],(ex,sc,method)
            stream_runs+=1
    rejected=False
    try:ReferenceDiagnostic(p['references']['n0.5'],p).update(5,120,110,3)
    except ValueError:rejected=True
    assert rejected
    for g in s['groups']:
        rr=[r for r in results if float(r['exponent'])==g['exponent'] and float(r['sigma'])==g['sigma'] and r['scene']==g['scene'] and r['method']==g['method']]
        assert len(rr)==20 and sum(r['early_valid']=='True' for r in rr)==g['early']
        assert sum(int(r['false_onsets'])>0 for r in rr)==g['false_trials']
        onsets=sum(int(r['false_onsets']) for r in rr);seconds=sum(int(r['false_exposure_s']) for r in rr)
        assert onsets==g['false_onsets'] and seconds==g['exposure_s']
        assert np.isclose(onsets*3600/seconds,g['false_onsets_per_hour'])
        assert sum(r['missed_correct_pattern']=='True' for r in rr)==g['misses']
    rec=dict(status='passed_for_listed_synthetic_checks',physical_data=False,
             reproduced_method_records=tested,healthy_reference_regression=True,healthy_only_limit_fitting=True,
             frozen_parameters_and_source_hashes=True,original_model_recovery=True,
             future_invariance_all_six_methods=True,scalar_ewma_recurrence=True,
             bounded_transition_review=True,unknown_load_ambiguity_preserved=True,
             statistics_and_exposure_recomputed=True,
             streaming_replay_equivalent_runs=stream_runs,nonuniform_sampling_rejected=True,
             inference_limits=['no real hydraulic validation','no energy validation','no independent model-family validation'],
             validator_sha256=sha(Path(__file__)),streaming_source_sha256=sha(ROOT/'simulation/reference_runtime.py'),
             summary_sha256=sha(OUT/'summary.json'))
    (OUT/'acceptance.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(rec,ensure_ascii=False))

if __name__=='__main__':main()
