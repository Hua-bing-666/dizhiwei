"""Causal paired replay of acquisition and reporting; no energy model.

Uses frozen observations from the earlier hydraulic review, not new experiments.
The scheduler is fed only acquired observations. Truth is read by the evaluator.
Thresholds below are candidate constants, not tuned on replay outcomes.
"""
from pathlib import Path
import csv, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'simulation/event_sampling_review'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'simulation/diagnosis_review/raw_trials.npz'
OLD = json.loads((ROOT / 'simulation/diagnosis_review/protocol.json').read_text(encoding='utf-8'))
CFG = dict(version='candidate-20261005-v1', classification='offline_replay_not_hardware',
           monitor_period_s=5, high_period_s=1, low_period_s=60,
           normal_report_period_s=60, high_report_period_s=10,
           warmup_end_s=129, mean_window_s=10, confirm_elapsed_s=5,
           high_hold_s=30, trigger_k_relative=.03, trigger_r_absolute=.3,
           trigger_p1_relative=.05, energy_estimated=False,
           initial_monitor_phase_s=0,
           flow_count_continuous=True, guard_reads_all_three_channels=True,
           comparison='Same calibration, feature rules, causal 10s window, 5s and >=2 observed confirmations.',
           seed_correlation='20 base noise sequences reused across scenarios and levels; not 480 independent physical trials.',
           parameters_tuned_on_this_batch=False)
STRATEGIES = ('fixed_high', 'fixed_low', 'report_only', 'adaptive')
KINDS = OLD['random_trials']['kinds']

def replay(obs, strategy):
    assert strategy in STRATEGIES
    history = []
    ref = []
    k0 = r0 = p10 = None
    pending = active = None
    pending_at = pending_count = 0
    events, acquired, sent = [], [], []
    high_until = -1
    next_t = 0
    last_send = 129
    guard_count = high_count = 0
    first_watch = 130 + CFG['initial_monitor_phase_s']
    next_guard = first_watch
    wake_count = 0
    for t in range(len(obs)):
        if t != next_t:
            continue
        x = np.asarray(obs[t], float)
        acquired.append(t)
        history.append((t, x.copy()))
        history = [(tt, xx) for tt, xx in history if tt > t-CFG['mean_window_s']]
        avg = np.mean([xx for _, xx in history], axis=0)
        p0, p1, q = avg
        k = q/np.sqrt(max(p1, .001))
        r = (p0-p1)/max(q*q, .001)
        if 20 <= t < 120:
            ref.append((k, r, p1))
        if t == 129:
            k0, r0, p10 = np.median(ref, axis=0)
        event = False
        is_high = False
        if t >= 130:
            assert k0 is not None
            guard = strategy == 'adaptive' and t >= next_guard
            if guard:
                guard_count += 1
                next_guard = t + CFG['monitor_period_s']
            # Any actual adaptive read may extend alert acquisition. No future read.
            trigger = (abs(k/k0-1) > CFG['trigger_k_relative'] or
                       abs(r-r0) > CFG['trigger_r_absolute'] or
                       abs(p1/p10-1) > CFG['trigger_p1_relative'])
            if strategy == 'adaptive' and trigger:
                if t > high_until:
                    wake_count += 1
                high_until = t + CFG['high_hold_s']
            is_high = strategy == 'adaptive' and t <= high_until
            if strategy == 'adaptive' and not guard:
                high_count += 1
            valid = p1 > OLD['rules']['valid_p1_min_kpa'] and q > OLD['rules']['valid_flow_min_l_min']
            leak = k/k0-1 > OLD['rules']['k_relative_threshold']
            restriction = r-r0 > OLD['rules']['r_absolute_threshold_kpa_min2_l2']
            label = ('invalid' if not valid else 'uncertain' if leak and restriction else
                     'leak_pattern' if leak else 'restriction_pattern' if restriction else 'normal')
            if label in ('normal', 'invalid'):
                pending = active = None
                pending_count = 0
            else:
                if pending != label:
                    pending, pending_at, pending_count = label, t, 1
                else:
                    pending_count += 1
                if t-pending_at >= CFG['confirm_elapsed_s'] and pending_count >= 2 and active != label:
                    events.append(dict(t_s=t, pattern=label))
                    active = label
                    event = True
            if strategy == 'fixed_low':
                send = True
            elif strategy == 'fixed_high':
                send = event or t-last_send >= CFG['high_report_period_s']
            else:
                # report_only sees fixed-high samples; adaptive sees its own samples.
                period = CFG['high_report_period_s'] if active or is_high else CFG['normal_report_period_s']
                send = event or t-last_send >= period
            if send:
                sent.append(t)
                last_send = t
        if t < 129:
            next_t = t+1
        elif strategy in ('fixed_high', 'report_only'):
            next_t = t+1
        elif strategy == 'fixed_low':
            next_t = first_watch if t == 129 else t+CFG['low_period_s']
        else:
            next_t = first_watch if t == 129 else t+1 if is_high else next_guard
    watched = [t for t in acquired if t >= 130]
    assert len(watched) == len(set(watched))
    assert not any(t >= len(obs) for t in acquired)
    if strategy == 'adaptive':
        assert guard_count+high_count == len(watched), (guard_count, high_count, len(watched))
    return dict(events=events, acquired=acquired, sent=sent,
                frames_after_warmup=len(watched), pressure_conversions_after_warmup=2*len(watched),
                guard_frames=guard_count, extra_high_frames=high_count, wake_count=wake_count,
                first_interval_after_warmup=watched[1]-watched[0] if len(watched)>1 else None)

def evaluate(result, kind, severity):
    events = result['events']
    fault = kind in ('leak', 'restriction')
    pre = [e for e in events if e['t_s'] < 360] if fault else events
    post = [e for e in events if e['t_s'] >= 360] if fault else []
    target = 'leak_pattern' if kind == 'leak' else 'restriction_pattern'
    indices = np.flatnonzero((np.arange(len(severity)) >= 360) & (severity >= .15)) if fault else []
    critical = int(indices[0]) if len(indices) else None
    first = post[0] if post else None
    good = bool(fault and not pre and first and first['pattern'] == target and critical is not None and first['t_s'] < critical)
    return dict(false_onsets=len(pre), early_valid=good,
                critical_s=critical, first_postfault_s=first['t_s'] if first else None,
                first_postfault_pattern=first['pattern'] if first else None,
                lead_s=critical-first['t_s'] if good else None,
                observed_frames=result['frames_after_warmup'], pressure_conversions=result['pressure_conversions_after_warmup'],
                send_attempts=len(result['sent']), guard_frames=result['guard_frames'],
                extra_high_frames=result['extra_high_frames'], wake_count=result['wake_count'])

def causal_check(obs):
    # Hidden/future samples cannot alter anything observable at or before cutoff.
    base = replay(obs, 'adaptive')
    cut = 355
    changed = obs.copy()
    changed[cut+1:] = 999
    again = replay(changed, 'adaptive')
    for key in ('acquired', 'sent'):
        assert [t for t in base[key] if t <= cut] == [t for t in again[key] if t <= cut]
    assert [e for e in base['events'] if e['t_s'] <= cut] == [e for e in again['events'] if e['t_s'] <= cut]
    hidden = sorted(set(range(len(obs)))-set(base['acquired']))
    changed = obs.copy()
    changed[hidden] = 999
    again = replay(changed, 'adaptive')
    assert base == again
    return {'future_invariance': True, 'unsampled_observation_invariance': True,
            'hidden_samples_modified': len(hidden)}

def main():
    frozen_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    d = np.load(SOURCE)
    rows, traces = [], {}
    for i, obs in enumerate(d['observed']):
        kind = KINDS[int(d['kind_index'][i])]
        for strategy in STRATEGIES:
            result = replay(obs, strategy)
            rows.append(dict(trial_id=str(d['trial_ids'][i]), kind=kind,
                             sigma_kpa=float(d['pressure_sigma'][i]), seed=int(d['seeds'][i]),
                             strategy=strategy, **evaluate(result, kind, d['severity_by_kind'][int(d['kind_index'][i])])) )
            if d['seeds'][i] == 10300 and d['pressure_sigma'][i] == .3 and kind in ('normal','leak','restriction'):
                traces[f'{kind}:{strategy}'] = result
    groups = []
    for sigma in (.3,1.,3.,10.):
        for kind in KINDS:
            for strategy in STRATEGIES:
                g = [r for r in rows if r['sigma_kpa']==sigma and r['kind']==kind and r['strategy']==strategy]
                groups.append(dict(sigma_kpa=sigma, kind=kind, strategy=strategy, trials=len(g),
                                   early_valid=sum(r['early_valid'] for r in g) if kind in ('leak','restriction') else None,
                                   mean_frames=float(np.mean([r['observed_frames'] for r in g])),
                                   mean_send_attempts=float(np.mean([r['send_attempts'] for r in g])),
                                   mean_false_onsets=float(np.mean([r['false_onsets'] for r in g])),
                                   median_valid_lead_s=float(np.median([r['lead_s'] for r in g if r['lead_s'] is not None])) if any(r['lead_s'] is not None for r in g) else None))
    with (OUT/'paired_results.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    checks=causal_check(d['observed'][0])
    # No actual acquisition saving is attributed to report-only.
    for i in range(0,len(rows),4):
        assert rows[i]['observed_frames']==rows[i+2]['observed_frames']==471
    summary=dict(config=CFG, source=str(SOURCE.relative_to(ROOT)).replace('\\','/'),
                 source_sha256=frozen_hash, replay_rows=len(rows), groups=groups,
                 causal_checks=checks, traces=traces, physical_validation=False,
                 radio_retries_modelled=False, energy_claim=None)
    for name,obj in [('protocol.json',CFG),('summary.json',summary)]:
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    sweep=[]
    for period in (5,10,30,60,120,300,600):
        CFG['monitor_period_s']=period
        phases=sorted(set(int(x) for x in np.linspace(0,period-1,min(period,6))))
        for phase in phases:
            CFG['initial_monitor_phase_s']=phase
            for i,obs in enumerate(d['observed']):
                kind=KINDS[int(d['kind_index'][i])]
                if d['pressure_sigma'][i] != .3 or kind not in ('normal','leak','restriction'):
                    continue
                r=replay(obs,'adaptive')
                sweep.append(dict(period_s=period,phase_s=phase,trial_id=str(d['trial_ids'][i]),kind=kind,
                                  sigma_kpa=float(d['pressure_sigma'][i]),seed=int(d['seeds'][i]),
                                  **evaluate(r,kind,d['severity_by_kind'][int(d['kind_index'][i])])))
    CFG['monitor_period_s']=5
    CFG['initial_monitor_phase_s']=0
    with (OUT/'period_sweep.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(sweep[0]),lineterminator='\n');w.writeheader();w.writerows(sweep)
    for period in (5,10,30,60,120,300,600):
        g=[r for r in sweep if r['period_s']==period and r['sigma_kpa']==.3 and r['kind'] in ('leak','restriction')]
        print('Period',period,'s; low-noise early=',sum(r['early_valid'] for r in g),'/',len(g),'; mean acquisition=',round(float(np.mean([r['observed_frames'] for r in g])),2))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==frozen_hash
    print('1920 paired replay rows; causal checks passed; no measured energy or physical RF.')
    for g in groups:
        if g['sigma_kpa']==.3 and g['kind'] in ('normal','leak','restriction'):
            print(g)

if __name__=='__main__':
    main()
