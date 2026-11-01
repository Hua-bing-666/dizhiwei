"""Check hydraulic identities, structural ambiguity and evidence eligibility."""
from pathlib import Path
import sys,json,csv,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
from diagnosis_feasibility import hydraulic
rng=np.random.default_rng(20261003)
for _ in range(600):
    ps=float(rng.uniform(40,180));rc=float(rng.uniform(0,2));c=float(rng.uniform(.1,.7));r=float(rng.uniform(.1,10))
    p0,p1,q=hydraulic(ps,rc,c,r,True)
    assert math.isclose(p0-p1,r*q*q,rel_tol=1e-10)
    assert math.isclose(q,c*math.sqrt(p1),rel_tol=1e-10)
    gb=.35/math.sqrt(1+.8*.35**2);qb=gb*math.sqrt(p0)
    assert math.isclose(ps-p0,rc*(q+qb)**2,rel_tol=1e-10)
    # A locally unchanged load coefficient is invariant to supply changes.
    a=hydraulic(ps,rc,c,r,False);assert math.isclose(a[2]/math.sqrt(a[1]),c,rel_tol=1e-12)
    assert np.allclose(hydraulic(ps,0,c,r,False),hydraulic(ps,0,c,r,True))
data=json.loads((ROOT/'simulation/diagnosis_results/summary.json').read_text(encoding='utf-8'))
rows=list(csv.DictReader((ROOT/'simulation/diagnosis_results/trials.csv').open(encoding='utf-8-sig')))
assert len(rows)==480 and len({(r['kind'],r['pressure_noise_kpa'],r['seed']) for r in rows})==480
for key in {r['pressure_noise_kpa'] for r in rows}:
    for kind in {r['kind'] for r in rows}:
        rr=[r for r in rows if r['kind']==kind and r['pressure_noise_kpa']==key]
        summary=next(r for r in data['summary'] if r['kind']==kind and r['pressure_noise_kpa']==float(key))
        successes=[r for r in rr if r['early_valid']=='True']
        assert summary['early_trials']==len(successes)
        assert math.isclose(summary['mean_false_onsets'],np.mean([int(r['false_onsets']) for r in rr]))
        for r in successes:
            assert float(r['severity_at_detection'])<data['critical_fraction']
            assert int(r['detected_s'])<int(r['critical_s']) and int(r['false_onsets'])==0
            assert r['first_pattern']==('leak_pattern' if kind=='leak' else 'restriction_pattern')
        if kind in ('normal','supply','drift','load_unknown'):assert not successes
    # A normal unknown load increase and a leak are the same physical signal in this model.
    a=data['traces']['leak_'+key];b=data['traces']['load_unknown_'+key]
    for field in ['p0','p1','q']:assert a[field]==b[field]
assert not data['physical_data']
print('600 hydraulic/conservation cases; 480 result records; early eligibility and unknown-load ambiguity passed.')
