"""Locked-parameter, paired synthetic comparison. No hardware evidence.

Train alarm limits on healthy sequences only; freeze them before evaluating
new seeds. All methods see the same causal 10-s averages at a fixed 1 Hz.
Local robust scales come only from each run's initial healthy calibration.
Overlapping windows are preserved during empirical limit calibration, rather
than treating the filtered observations as independent Gaussian samples.
"""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import sys
import numpy as np
from review_diagnosis import CONFIG, classify, evaluate, means, truth, hydraulics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'simulation/cusum_review'
METHODS = ('flow_only', 'physical', 'cusum')
KINDS = CONFIG['random_trials']['kinds']
SIGMAS = CONFIG['random_trials']['pressure_sigma_kpa']
TRAIN = list(range(21000, 21040))
TEST = list(range(22000, 22040))
SETTINGS = dict(version='20261006-cusum-v1', k=.5, min_h=5.,
                healthy_peak_margin=1.10, k_relative_scale_floor=.003,
                r_absolute_scale_floor=.03, fixed_acquisition_s=1,
                training_seeds=TRAIN, test_seeds=TEST,
                parameter_selection='Healthy-only maximum path score, per channel; no fault outcomes used.',
                training_kinds=['normal', 'supply'],
                operating_state_gating=False, missing_observations_filled=False,
                scale_estimator='1.4826*MAD over initial healthy [20,120), with declared floors',
                uncertainty='Random pressure sigma is not manufacturer accuracy; no physical measurements.',
                controls_horizon_s=470, long_healthy_horizon_s=3470,
                controls_observations=471, long_healthy_observations=3471)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(name, obj):
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False),
                          encoding='utf-8', newline='\n')

def csv_dump(name, rows):
    with (OUT/name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)

def observe(values, sigma, seed, drift=False):
    rng = np.random.default_rng(seed)
    obs = values + rng.normal(0, [sigma, sigma, .02], values.shape)
    if drift:
        obs[:, 0] += 10*np.clip((np.arange(len(obs))-360)/180, 0, 1)
    return obs

def feature_scores(obs):
    avg = means(obs)
    p0, p1, q = avg.T
    valid = (p1 > 10) & (q > .5)
    k = q / np.sqrt(np.maximum(p1, .001))
    r = (p0-p1) / np.maximum(q*q, .001)
    a, b = CONFIG['sampling']['reference_indices']
    k0, r0 = np.median(k[a:b]), np.median(r[a:b])
    x = np.column_stack([k/k0-1, r-r0])
    scale = 1.4826*np.median(abs(x[a:b]-np.median(x[a:b], axis=0)), axis=0)
    scale = np.maximum(scale, [.003, .03])
    z = x/scale
    scores = np.zeros_like(z)
    start = CONFIG['sampling']['monitor_start_s']
    for j in range(start, len(obs)):
        if valid[j]:
            scores[j] = np.maximum(0, scores[j-1]+z[j]-SETTINGS['k'])
    return dict(mean=avg, x=x, scale=scale, valid=valid, z=z, scores=scores)

def cusum_classify(obs, params):
    data = feature_scores(obs)
    exceed = data['scores'] > np.array([params['h_k'], params['h_r']])
    state = np.where(exceed[:, 0] & exceed[:, 1], 'uncertain',
                     np.where(exceed[:, 0], 'leak_pattern',
                              np.where(exceed[:, 1], 'restriction_pattern', 'normal')))
    state[~data['valid']] = 'invalid'
    events = []
    active = None
    n = CONFIG['sampling']['persistence_samples']
    for j in range(CONFIG['sampling']['monitor_start_s'], len(obs)):
        label = str(state[j])
        if label in ('normal', 'invalid'):
            active = None
            continue
        if len(set(state[j-n+1:j+1])) == 1:
            if active != label:
                events.append(dict(t_s=j, pattern=label))
            active = label
    return dict(**data, state=state, events=events)

def fit():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    # No fault traces, test seeds or test metrics enter this function.
    for kind, sigma, seed in itertools.product(('normal', 'supply'), SIGMAS, TRAIN):
        obs = observe(truth(kind)[1], sigma, seed)
        f = feature_scores(obs)
        peaks = np.max(f['scores'][130:], axis=0)
        rows.append(dict(kind=kind, pressure_sigma_kpa=sigma, seed=seed,
                         peak_k=float(peaks[0]), peak_r=float(peaks[1]),
                         calibration_scale_k=float(f['scale'][0]),
                         calibration_scale_r=float(f['scale'][1])))
    params = dict(settings=SETTINGS, training_trajectories=len(rows),
                  h_k=max(5., 1.10*max(r['peak_k'] for r in rows)),
                  h_r=max(5., 1.10*max(r['peak_r'] for r in rows)),
                  source_hashes={p.relative_to(ROOT).as_posix(): sha(p) for p in
                    [Path(__file__), ROOT/'simulation/review_diagnosis.py',
                     ROOT/'simulation/diagnosis_review/protocol.json']})
    csv_dump('healthy_training.csv', rows)
    dump('frozen_parameters.json', params)
    print(json.dumps({key: params[key] for key in ('training_trajectories', 'h_k', 'h_r')}))

def groups(rows):
    result = []
    for kind, sigma, method in itertools.product(KINDS, SIGMAS, METHODS):
        rr = [r for r in rows if r['kind']==kind and r['pressure_sigma_kpa']==sigma and r['method']==method]
        good = [r for r in rr if r['early_valid']]
        result.append(dict(kind=kind, pressure_sigma_kpa=sigma, method=method, trials=len(rr),
                           early_trials=len(good), false_alarm_trials=sum(r['false_onsets']>0 for r in rr),
                           false_onsets=sum(r['false_onsets'] for r in rr),
                           exposure_seconds=sum(r['false_exposure_seconds'] for r in rr),
                           median_valid_lead_s=float(np.median([r['valid_lead_s'] for r in good])) if good else None,
                           no_correct_detection_trials=sum(r['first_correct_s'] is None for r in rr) if kind in ('leak','restriction') else None,
                           wrong_first_trials=sum(r['outcome']=='wrong_first_pattern' for r in rr),
                           outcomes={k: sum(r['outcome']==k for r in rr) for k in sorted(set(r['outcome'] for r in rr))}))
    return result

def stresses(params):
    rows = []
    t = np.arange(601)
    def record(case, obs, context):
        for method in METHODS:
            d = cusum_classify(obs, params) if method=='cusum' else classify(obs, method)
            rows.append(dict(case=case, method=method, first_alarm_s=d['events'][0]['t_s'] if d['events'] else None,
                             first_pattern=d['events'][0]['pattern'] if d['events'] else None,
                             alarm_onsets=len(d['events']), **context))
    # Unknown load and drift are already present in the full held-out set.
    # Test deterministic channel misalignment and uncalibrated load laws here.
    for delay in [0., .1, 1., 5.]:
        values = np.array([hydraulics(80. if 180<=j<300 else 120., .28, .8, False) for j in t])
        skew = values.copy()
        skew[:, 1] = np.interp(t-delay, t, values[:, 1], left=values[0, 1])
        record(f'timestamp_delay_{delay:g}', skew, dict(challenge='pressure_time_skew', value=delay))
    for exponent, supply in itertools.product([0., .3, .5, .8], [80., 160.]):
        def solve(ps):
            lo, hi = 0., ps
            for _ in range(70):
                p1 = (lo+hi)/2
                q = .28*10*(p1/100)**exponent
                p0 = p1+.8*q*q
                if p0+.4*q*q<ps: lo=p1
                else: hi=p1
            return [p0, p1, q]
        values = np.array([solve(supply if 180<=j<300 else 120.) for j in t])
        record(f'load_exponent_{exponent:g}_supply_{supply:g}', values,
               dict(challenge='unfitted_healthy_load_law', value=f'{exponent:g}/{supply:g}'))
    csv_dump('stress_results.csv', rows)
    return rows

def long_healthy(params):
    t = np.arange(3601)
    # Repeated known-to-evaluator healthy B transitions; detectors see no labels.
    values = np.array([hydraulics(120., .28, .8, 180<=j%600<300) for j in t])
    rows = []
    for sigma, seed in itertools.product(SIGMAS, TEST):
        obs = observe(values, sigma, seed)
        for method in METHODS:
            d = cusum_classify(obs, params) if method=='cusum' else classify(obs, method)
            rows.append(dict(pressure_sigma_kpa=sigma, seed=seed, method=method,
                             alarm_onsets=len(d['events']),
                             first_alarm_s=d['events'][0]['t_s'] if d['events'] else None,
                             exposure_seconds=3600-130))
    csv_dump('long_healthy_results.csv', rows)
    return [dict(pressure_sigma_kpa=sigma, method=method, trials=40,
                 false_alarm_trials=sum(r['alarm_onsets']>0 for r in rows if r['pressure_sigma_kpa']==sigma and r['method']==method),
                 alarm_onsets=sum(r['alarm_onsets'] for r in rows if r['pressure_sigma_kpa']==sigma and r['method']==method))
            for sigma, method in itertools.product(SIGMAS, METHODS)]

def main():
    params_path = OUT/'frozen_parameters.json'
    params = json.loads(params_path.read_text(encoding='utf-8'))
    assert params['settings'] == SETTINGS, 'Refit explicitly after protocol change.'
    for file, expected in params['source_hashes'].items():
        assert sha(ROOT/file)==expected, f'Frozen source changed: {file}'
    assert not set(TRAIN)&set(TEST)
    param_hash = sha(params_path)
    truths = {kind: truth(kind) for kind in KINDS}
    rows, raw, ids = [], [], []
    for kind, sigma, seed in itertools.product(KINDS, SIGMAS, TEST):
        t, values, healthy, severity = truths[kind]
        obs = observe(values, sigma, seed, kind=='drift')
        trial_id = f'{kind}|{sigma:g}|{seed}'
        raw.append(obs); ids.append(trial_id)
        for method in METHODS:
            d = cusum_classify(obs, params) if method=='cusum' else classify(obs, method)
            rows.append(dict(trial_id=trial_id, kind=kind, pressure_sigma_kpa=sigma, seed=seed,
                             method=method, **evaluate(kind, d, severity)))
    np.savez_compressed(OUT/'heldout_observations.npz', observed=np.array(raw),
                        trial_ids=np.array(ids), t=t,
                        truth_by_kind=np.array([truths[k][1] for k in KINDS]),
                        severity_by_kind=np.array([truths[k][3] for k in KINDS]))
    csv_dump('paired_results.csv', rows)
    stress = stresses(params)
    long = long_healthy(params)
    assert sha(params_path)==param_hash
    dump('summary.json', dict(classification='uncalibrated_synthetic_heldout_noise_test', physical_data=False,
                             fresh_trajectories=960, paired_method_records=len(rows),
                             unique_test_noise_seeds=40, training_seed_overlap=False,
                             seed_reuse='Same base noise sequence reused across all six kinds and four sigmas; not 960 independent experiments.',
                             generalization='New random seeds only. Same hydraulic law, fixed timing and severity; no field or model-domain validation.',
                             thresholds_optimized_on_test=False, parameters_sha256=param_hash,
                             parameters=params, groups=groups(rows), stresses=stress, long_healthy=long,
                             long_healthy_note='Reuses held-out seeds; separate horizon challenge, not new independent trials.',
                             source_sha256={f:sha(OUT/f) for f in ['heldout_observations.npz','paired_results.csv','healthy_training.csv','stress_results.csv','long_healthy_results.csv']}))
    print(f'960 synthetic trajectories / {len(rows)} paired method records; no physical data.')
    for g in groups(rows):
        if g['kind'] in ('leak','restriction','normal','supply'):
            print(g['kind'],g['pressure_sigma_kpa'],g['method'], 'early',g['early_trials'], 'FA trials',g['false_alarm_trials'], 'lead',g['median_valid_lead_s'])
    print('Long healthy:', json.dumps(long))

if __name__=='__main__':
    if '--fit' in sys.argv: fit()
    else: main()
