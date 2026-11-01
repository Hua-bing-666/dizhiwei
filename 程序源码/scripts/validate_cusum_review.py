"""Independent arithmetic, causality, pairing and evidence checks."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'simulation'))
from review_cusum import METHODS, SETTINGS, TRAIN, TEST, feature_scores, cusum_classify, observe
from review_diagnosis import classify, evaluate, truth

OUT = ROOT/'simulation/cusum_review'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def main():
    summary = json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    params = json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    assert summary['parameters_sha256']==sha(OUT/'frozen_parameters.json')
    assert params['settings']==SETTINGS and not set(TRAIN)&set(TEST)
    for p, digest in params['source_hashes'].items(): assert sha(ROOT/p)==digest
    for p, digest in summary['source_sha256'].items(): assert sha(OUT/p)==digest
    train = rows(OUT/'healthy_training.csv')
    assert len(train)==320 and set(r['kind'] for r in train)=={'normal','supply'}
    assert params['h_k']==max(5., 1.1*max(float(r['peak_k']) for r in train))
    assert params['h_r']==max(5., 1.1*max(float(r['peak_r']) for r in train))
    data = np.load(OUT/'heldout_observations.npz', allow_pickle=False)
    results = rows(OUT/'paired_results.csv')
    assert data['observed'].shape==(960,601,3) and len(results)==2880
    lookup = {(r['trial_id'],r['method']):r for r in results}
    assert len(lookup)==2880
    reproduced = 0
    truths = {kind:truth(kind) for kind in ['normal','supply','leak','restriction','drift','load_unknown']}
    for i, tid in enumerate(data['trial_ids']):
        kind, noise, seed = str(tid).split('|')
        assert int(seed) in TEST
        obs = data['observed'][i]
        severity = truths[kind][3]
        # Raw replay reconstruction uses stored seed and documented noise only.
        assert np.array_equal(obs, observe(truths[kind][1], float(noise), int(seed), kind=='drift'))
        for method in METHODS:
            diagnostic = cusum_classify(obs, params) if method=='cusum' else classify(obs, method)
            calculated = evaluate(kind, diagnostic, severity)
            stored = lookup[(str(tid),method)]
            for key, value in calculated.items():
                if value is None: assert stored[key]==''
                elif isinstance(value, float): assert np.isclose(float(stored[key]), value, rtol=1e-12, atol=1e-12)
                else: assert stored[key]==str(value), (tid,method,key)
            reproduced += 1
    # Manual recurrence is deliberately separate from the vector/row implementation.
    obs = data['observed'][list(data['trial_ids']).index('leak|3|22000')]
    f = feature_scores(obs)
    kscore = rscore = 0.
    for j in range(130, len(obs)):
        kscore = max(0., kscore+float(f['z'][j,0])-.5) if f['valid'][j] else 0.
        rscore = max(0., rscore+float(f['z'][j,1])-.5) if f['valid'][j] else 0.
        assert np.allclose(f['scores'][j], [kscore,rscore], rtol=1e-12)
    # Alter future values: no past statistic, label, or confirmed onset may change.
    cut = 355
    altered = obs.copy(); altered[cut+1:] = 999
    a,b = cusum_classify(obs,params),cusum_classify(altered,params)
    for key in ('x','z','scores','state'):
        assert np.array_equal(a[key][:cut+1],b[key][:cut+1]), key
    assert [e for e in a['events'] if e['t_s']<=cut]==[e for e in b['events'] if e['t_s']<=cut]
    # All invalid observations must reset the cumulative evidence, not count as zero-noise normal.
    invalid = obs.copy(); invalid[200:240,1]=0; invalid[200:240,2]=0
    bad = feature_scores(invalid)
    assert np.any(~bad['valid'][200:240]) and np.all(bad['scores'][~bad['valid']]==0)
    # This ambiguity cannot be cured by CUSUM: observations and all outputs coincide.
    for sigma in [.3,1.,3.,10.]:
        for seed in TEST:
            le = data['observed'][list(data['trial_ids']).index(f'leak|{sigma:g}|{seed}')]
            lu = data['observed'][list(data['trial_ids']).index(f'load_unknown|{sigma:g}|{seed}')]
            assert np.array_equal(le,lu)
            assert cusum_classify(le,params)['events']==cusum_classify(lu,params)['events']
    for g in summary['groups']:
        rr=[r for r in results if r['kind']==g['kind'] and float(r['pressure_sigma_kpa'])==g['pressure_sigma_kpa'] and r['method']==g['method']]
        assert len(rr)==40 and sum(r['early_valid']=='True' for r in rr)==g['early_trials']
        assert sum(int(r['false_onsets'])>0 for r in rr)==g['false_alarm_trials']
        assert sum(int(r['false_onsets']) for r in rr)==g['false_onsets']
        assert sum(r['outcome']=='wrong_first_pattern' for r in rr)==g['wrong_first_trials']
        assert all(r['early_valid']!='True' or (int(r['false_onsets'])==0 and int(r['first_correct_s'])<int(r['critical_s'])) for r in rr)
    long=rows(OUT/'long_healthy_results.csv'); stress=rows(OUT/'stress_results.csv')
    assert len(long)==480 and len(stress)==36
    for g in summary['long_healthy']:
        rr=[r for r in long if r['method']==g['method'] and float(r['pressure_sigma_kpa'])==g['pressure_sigma_kpa']]
        assert sum(int(r['alarm_onsets'])>0 for r in rr)==g['false_alarm_trials']
        assert sum(int(r['alarm_onsets']) for r in rr)==g['alarm_onsets']
        assert all(int(r['exposure_seconds'])==3470 for r in rr)
    record=dict(status='passed', synthetic_only=True, reproduced_paired_results=reproduced,
                new_noise_seeds_only=True, no_fault_outcomes_used_in_limit_fitting=True,
                parameter_lock_and_source_hashes=True, manual_recurrence=True,
                future_invariance=True, invalid_resets=True, unknown_load_ambiguity=True,
                grouped_counts_recomputed=True, stress_records=36, long_healthy_records=480,
                inference_limits='No acceptance, publication, field accuracy or energy conclusion.',
                source_hashes={'validator':sha(Path(__file__)), 'summary':sha(OUT/'summary.json')})
    (OUT/'acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(record,ensure_ascii=False))

if __name__=='__main__': main()
