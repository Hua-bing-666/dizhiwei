"""Frozen stage-six tests: streaming, payload semantics, then transport."""
from pathlib import Path
import csv
import itertools
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'prototype'))
from integrated_monitor import Monitor, PacketReceiver
from reliable_outbox import Outbox, encode
from rapid_review_runtime import rapid_review
from review_quality_intervals import inputs, sha

OUT = ROOT / 'simulation/integrated_monitor_review'
BASE = ROOT / 'simulation/quality_interval_review/frozen_parameters.json'
CASES = [('normal', False), ('supply_step', False), ('leak_r90', False),
         ('restriction_r90', False), ('pulse8', False), ('fast_leak_switch', False),
         ('nan_pressure', True), ('spike_range', True), ('counter_reset', True),
         ('bad_calibration', True), ('fault_initial', True), ('drift_p0', True)]
CFG = dict(version='20261006-integrated-v1', cases=CASES, seeds=list(range(45000, 45004)),
           sigmas=[.3, 3., 10.], pressure_period_s=1, main_method='guarded_fast',
           rapid_window_s=3, status_interval_s=60, retry_interval_s=2,
           max_sample_age_s=65,
           link_modes=['clean', 'loss', 'outage'], outage=[350, 410],
           data_loss=.2, ack_loss=.25, link_seed_offset=10000, flush_s=120,
           healthy_approval='explicit experiment assumption; absent for initial-fault case',
           physical_data=False, energy_measured=False, radio_timing_modelled=False)


def dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def write(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def parameters():
    p = json.loads((OUT / 'frozen_parameters.json').read_text(encoding='utf-8'))
    assert p['config'] == json.loads(json.dumps(CFG))
    for path, digest in p['sources'].items():
        assert sha(ROOT / path) == digest, path
    return p


def cases():
    return itertools.product(CFG['sigmas'], CASES, CFG['seeds'])


def collect(scene, quality, sigma, seed, p):
    tr, obs, counts = inputs(scene, sigma, seed, quality)
    # An explicit experiment manifest assumption, never a detector using truth.
    approved = scene != 'fault_initial'
    monitor = Monitor(p['baseline']['reference'], p['baseline']['limits']['1'],
                      f'{scene}:{sigma:g}:{seed}', healthy_reference_approved=approved)
    for t, count in enumerate(counts):
        monitor.update(t, int(count), obs[t, :2])
    return tr, obs, counts, monitor


def payload(sample, events):
    return dict(run_id=sample['run_id'], sample=sample, events=events)


def transport(records, events, mode, seed, paths=None):
    sender = Outbox(paths[0] if paths else ':memory:')
    receiver = PacketReceiver(paths[1] if paths else ':memory:')
    by_t = {r['t_s']: r for r in records}
    event_t = {}
    for e in events:
        event_t.setdefault(e['t_s'], []).append(e)
    last = records[-1]['t_s']
    rng = np.random.default_rng(seed + CFG['link_seed_offset'])
    draws = rng.random((last + CFG['flush_s'] + 1, 2))
    attempts = byte_attempts = enqueued = latest_t = 0
    latest_monotonic = True
    views = []
    for t in range(130, last + CFG['flush_s'] + 1):
        if t in by_t:
            fresh = event_t.get(t, [])
            if fresh or (t - 130) % CFG['status_interval_s'] == 0 or t == last:
                body = payload(by_t[t], fresh)
                json.dumps(body, allow_nan=False)
                sender.enqueue(body, t, priority=int(bool(fresh)))
                enqueued += 1
        packet = sender.pick(t)
        if packet is not None:
            attempts += 1
            byte_attempts += len(encode(packet).encode('utf-8'))
            blocked = mode == 'outage' and CFG['outage'][0] <= t < CFG['outage'][1]
            dropped = mode == 'loss' and draws[t, 0] < CFG['data_loss']
            if not blocked and not dropped:
                ack = receiver.accept(packet, t)
                current = receiver.latest_sample()['t_s']
                latest_monotonic &= current >= latest_t
                latest_t = current
                if mode != 'loss' or draws[t, 1] >= CFG['ack_loss']:
                    sender.ack(ack)
        if t <= last:
            view = receiver.monitor_view(t, CFG['max_sample_age_s'])
            views.append(dict(t_s=t, sample_t_s=view['sample']['t_s'] if view['sample'] else None,
                              sample_age_s=view['sample_age_s'], data_fresh=view['data_fresh'],
                              remote_status=view['remote_status']))
    got = receiver.events()
    expected = {e['event_id']: e for e in events}
    actual = {e['event']['event_id']: e['event'] for e in got}
    contents_ok = all(expected.get(k) == v for k, v in actual.items())
    lags = [x['received'] - x['event']['t_s'] for x in got]
    packets = receiver.packets()
    samples_ok = all(by_t[x['payload']['sample']['t_s']] == x['payload']['sample'] for x in packets)
    result = dict(mode=mode, generated_events=len(events), received_events=len(got),
                  missing_events=len(expected.keys() - actual.keys()), unexpected_events=len(actual.keys() - expected.keys()),
                  event_contents_equal=contents_ok, sample_contents_equal=samples_ok,
                  duplicate_event_rows=len(got) - len(actual), enqueued_packets=enqueued,
                  received_unique_packets=len(packets), outstanding_packets=sender.count(),
                  attempts=attempts, attempted_json_utf8_bytes=byte_attempts,
                  max_event_lag_s=max(lags) if lags else None, latest_sample_t=latest_t,
                  stale_monitoring_seconds=sum(v['remote_status'] == 'stale' for v in views),
                  latest_acquisition_monotonic=bool(latest_monotonic))
    sender.close()
    receiver.close()
    return result, packets, got, views


def freeze():
    OUT.mkdir(exist_ok=True)
    source_paths = [Path(__file__), ROOT / 'simulation/streaming_rapid_runtime.py',
                    ROOT / 'prototype/integrated_monitor.py', ROOT / 'prototype/reliable_outbox.py',
                    ROOT / 'simulation/rapid_review_runtime.py', ROOT / 'simulation/sampling_quality_runtime.py',
                    ROOT / 'simulation/review_quality_intervals.py', ROOT / 'simulation/review_hybrid_sampling.py',
                    ROOT / 'simulation/review_operating_reference.py', BASE]
    dump('frozen_parameters.json', dict(config=CFG, baseline=json.loads(BASE.read_text(encoding='utf-8')),
                                      sources={x.relative_to(ROOT).as_posix(): sha(x) for x in source_paths}))
    print('Stage-six protocol frozen; existing thresholds unchanged.')


def semantics(monitor):
    for r in monitor.records:
        json.dumps(r, allow_nan=False)
        assert r['diagnostic_pattern'] != 'healthy'
        assert r['physical_valve_verified'] is False
        if r['measurement_status'] != 'valid':
            assert r['diagnostic_pattern'] == 'unavailable'
        if not r['healthy_reference_approved'] or not r['numeric_baseline_available']:
            assert not r['rapid_attention_active'] and not r['rapid_window_valid']
    if not monitor.approved:
        assert not [e for e in monitor.events if e['kind'] in ('rapid_review', 'leak_pattern', 'restriction_pattern', 'uncertain')]
    assert not [e for e in monitor.events if e['kind'] in ('resolved', 'valve_closed')]


def main(stage):
    p = parameters()
    locked = sha(OUT / 'frozen_parameters.json')
    if stage == 'C':
        for name in ['streaming_acceptance.json', 'semantics_acceptance.json']:
            a = json.loads((OUT / name).read_text(encoding='utf-8'))
            assert a['parameters_sha256'] == locked and a['passed'] is True
    rows = []
    examples = {}
    for sigma, (scene, quality), seed in cases():
        tr, obs, counts, monitor = collect(scene, quality, sigma, seed, p)
        if stage == 'A':
            reference = rapid_review(obs, counts, p['baseline']['reference'], monitor.node.context, 3)
            assert monitor.rapid.events == reference['events']
            assert len(monitor.rapid.records) == len(reference['records'])
            for a, b in zip(monitor.rapid.records, reference['records']):
                assert a['t'] == b['t'] and a['valid'] == b['valid'] and a['attention'] == b['attention']
                assert np.allclose(a['x'], b['x'], atol=1e-12)
            rows.append(dict(scene=scene, sigma=sigma, seed=seed,
                             records_compared=len(reference['records']), events_compared=len(reference['events']), identical=True))
        elif stage == 'B':
            semantics(monitor)
            rows.append(dict(scene=scene, sigma=sigma, seed=seed, records=len(monitor.records),
                             events=len(monitor.events), quality_transitions=sum(e['kind'] == 'quality_transition' for e in monitor.events),
                             baseline_numeric=monitor.node.context is not None, health_approved=monitor.approved,
                             unavailable_records=sum(r['measurement_status'] != 'valid' for r in monitor.records)))
        else:
            for mode in CFG['link_modes']:
                result, packets, events, views = transport(monitor.records, monitor.events, mode, seed)
                rows.append(dict(scene=scene, sigma=sigma, seed=seed, **result))
                assert result['missing_events'] == result['unexpected_events'] == result['duplicate_event_rows'] == 0
                assert result['outstanding_packets'] == 0
                assert result['event_contents_equal'] and result['sample_contents_equal'] and result['latest_acquisition_monotonic']
                assert result['latest_sample_t'] == int(tr['t'][-1])
                if sigma == .3 and seed == CFG['seeds'][0] and scene in ('pulse8', 'nan_pressure', 'counter_reset'):
                    examples[f'{scene}:{mode}'] = dict(records=monitor.records, generated=monitor.events,
                                                     received=events, packets=packets, remote_views=views)
    filename = dict(A='streaming_results.csv', B='semantics_results.csv', C='transport_results.csv')[stage]
    write(filename, rows)
    dump(f'{stage}_summary.json', dict(stage=stage, rows=len(rows), physical_data=False,
                                      parameters_sha256=locked, results_sha256=sha(OUT / filename)))
    if stage == 'C':
        dump('examples.json', examples)
    print(f'Stage {stage}: {len(rows)} records complete; independent acceptance pending.', flush=True)


if __name__ == '__main__':
    if '--freeze' in sys.argv:
        freeze()
    else:
        main(sys.argv[1])
