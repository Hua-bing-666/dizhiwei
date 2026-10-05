"""Independent acceptance gates for stage-six integration."""
from pathlib import Path
import csv
import json
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulation'))
sys.path.insert(0, str(ROOT / 'prototype'))
import review_integrated_monitor as m
from integrated_monitor import Monitor, PacketReceiver
from reliable_outbox import Outbox
from review_hybrid_sampling import residual
from sampling_quality_runtime import SamplingNode
from streaming_rapid_runtime import StreamingRapid


def read(name):
    with (m.OUT / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def compare(row, actual):
    for key, value in actual.items():
        assert row[key] == ('' if value is None else str(value)), (key, row[key], value)


def finish(name, **details):
    m.dump(name, dict(passed=True, physical_data=False,
                      parameters_sha256=m.sha(m.OUT / 'frozen_parameters.json'),
                      validator_sha256=m.sha(Path(__file__)), **details))


def streaming(p):
    rows = read('streaming_results.csv')
    assert len(rows) == 144 and all(r['identical'] == 'True' for r in rows)
    for row in rows:
        _, obs, counts, monitor = m.collect(row['scene'], dict(m.CASES)[row['scene']],
                                           float(row['sigma']), int(row['seed']), p)
        batch = m.rapid_review(obs, counts, p['baseline']['reference'], monitor.node.context, 3)
        assert monitor.rapid.events == batch['events']
        assert len(monitor.rapid.records) == len(batch['records'])
        for actual, expected in zip(monitor.rapid.records, batch['records']):
            assert actual['t'] == expected['t'] and actual['valid'] == expected['valid']
            assert actual['attention'] == expected['attention']
            assert np.allclose(actual['x'], expected['x'], atol=1e-12)
        compare(row, dict(records_compared=len(batch['records']), events_compared=len(batch['events']), identical=True))
    independent = causal = 0
    reference = p['baseline']['reference']
    limits = p['baseline']['limits']['1']
    for scene, quality in [('pulse8', False), ('leak_r90', False), ('nan_pressure', True),
                           ('counter_reset', True), ('bad_calibration', True)]:
        tr, obs, counts, monitor = m.collect(scene, quality, .3, 45000, p)
        stream = monitor.rapid
        lookup = {r['t']: r for r in stream.records}
        for record in stream.records:
            t = record['t']
            pp = obs[t-2:t+1, :2]
            cc = counts[t-3:t+1]
            q = 60 * (cc[-1] - cc[0]) / (540 * 3)
            valid = bool(np.all(np.isfinite(pp)) and np.all((pp >= 0) & (pp <= 200))
                         and np.all(pp[:, 1] > 10) and np.all(np.diff(cc) >= 0) and q > .5)
            assert record['valid'] == valid
            if valid:
                expected = residual(*pp.mean(axis=0), q, reference, monitor.node.context['gain'], monitor.node.context['r0'])
                assert np.allclose(expected, record['x'], atol=1e-12)
        for event in stream.events:
            assert lookup[event['t_s']]['attention'] and lookup[event['t_s']-1]['attention']
        independent += 1
        altered = obs.copy()
        altered[371:, :2] = 999
        modified_counts = counts.copy()
        modified_counts[371:] += 999999
        node = SamplingNode(reference, limits)
        candidate = StreamingRapid(reference)
        for t, count in enumerate(modified_counts):
            node.update(t, int(count), altered[t, :2])
            candidate.update(t, int(count), altered[t, :2], node.context if t == 129 else None)
        assert [r for r in stream.records if r['t'] <= 370] == [r for r in candidate.records if r['t'] <= 370]
        assert [e for e in stream.events if e['t_s'] <= 370] == [e for e in candidate.events if e['t_s'] <= 370]
        causal += 1
    finish('streaming_acceptance.json', stage='6A', trajectories=144,
           reference_records_compared=sum(int(r['records_compared']) for r in rows),
           reference_events_compared=sum(int(r['events_compared']) for r in rows),
           independent_window_cases=independent, future_invariance_cases=causal)
    print('6A accepted: 144 reference comparisons; five independent windows and future-invariance cases.')


def semantics(p):
    gate = json.loads((m.OUT / 'streaming_acceptance.json').read_text(encoding='utf-8'))
    assert gate['passed'] and gate['parameters_sha256'] == m.sha(m.OUT / 'frozen_parameters.json')
    rows = read('semantics_results.csv')
    assert len(rows) == 144
    for row in rows:
        quality = dict(m.CASES)[row['scene']]
        _, _, _, monitor = m.collect(row['scene'], quality, float(row['sigma']), int(row['seed']), p)
        m.semantics(monitor)
        compare(row, dict(records=len(monitor.records), events=len(monitor.events),
                          quality_transitions=sum(e['kind'] == 'quality_transition' for e in monitor.events),
                          baseline_numeric=monitor.node.context is not None, health_approved=monitor.approved,
                          unavailable_records=sum(r['measurement_status'] != 'valid' for r in monitor.records)))
    # Explicitly deny an otherwise numerically valid initial reference.
    _, obs, counts = m.inputs('leak_r90', .3, 45000)
    denied = Monitor(p['baseline']['reference'], p['baseline']['limits']['1'], 'denied', False)
    for t, count in enumerate(counts):
        denied.update(t, int(count), obs[t, :2])
    assert denied.node.context is not None
    assert all(r['measurement_status'] == 'healthy_reference_unconfirmed' for r in denied.records)
    assert all(e['kind'] == 'quality_transition' for e in denied.events)
    # Exact recovery boundaries, derived from actual window endpoints.
    for scene, start, end in [('nan_pressure', 360, 374), ('spike_range', 360, 370), ('counter_reset', 420, 430)]:
        _, _, _, monitor = m.collect(scene, True, .3, 45000, p)
        by = {r['t_s']: r for r in monitor.records}
        assert all(by[t]['diagnostic_pattern'] == 'unavailable' for t in range(start, end))
        assert by[end]['measurement_status'] == 'valid'
        assert not any(e['kind'] == 'resolved' for e in monitor.events)
    # Full payload transaction rollback, actual file reopen and out-of-order arrival.
    (ROOT / 'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='integrated_qa_', dir=ROOT / 'tmp') as directory:
        receiver_path = str(Path(directory) / 'receiver.sqlite')
        sender_path = str(Path(directory) / 'sender.sqlite')
        receiver = PacketReceiver(receiver_path)
        sender = Outbox(sender_path)
        base = dict(run_id='qa', sample=dict(run_id='qa', t_s=200, pressure_kpa=[100., 90.], measurement_status='valid'),
                    events=[dict(event_id='qa:200:0', t_s=200, kind='rapid_review')])
        pid = sender.enqueue(base, 200, 1)
        packet = sender.pick(200)
        assert receiver.accept(packet, 201) == pid
        sender.close()
        receiver.close()
        sender = Outbox(sender_path)
        receiver = PacketReceiver(receiver_path)
        assert sender.count() == 1 and receiver.latest_sample() == base['sample']
        assert receiver.accept(sender.pick(202), 203) == pid
        assert len(receiver.events()) == len(receiver.packets()) == 1
        old = dict(run_id='qa', sample=dict(run_id='qa', t_s=150, pressure_kpa=[101., 91.]), events=[])
        receiver.accept(dict(packet_id=2, payload=old), 204)
        assert receiver.latest_sample()['t_s'] == 200
        # A recent receipt does not make an old acquisition current.
        receiver.accept(dict(packet_id=5, payload=dict(run_id='qa', sample=base['sample'], events=[])), 264)
        assert receiver.monitor_view(265)['data_fresh'] is True
        assert receiver.monitor_view(266)['remote_status'] == 'stale'
        conflict = json.loads(json.dumps(base))
        conflict['events'][0]['kind'] = 'restriction_pattern'
        try:
            receiver.accept(dict(packet_id=3, payload=conflict), 205)
            raise AssertionError('Conflicting event was accepted')
        except ValueError:
            pass
        assert receiver.db.execute('SELECT COUNT(*) FROM receipts WHERE id=3').fetchone()[0] == 0
        assert len(receiver.events()) == 1
        invalid = json.loads(json.dumps(base))
        invalid['sample']['pressure_kpa'][0] = float('nan')
        try:
            receiver.accept(dict(packet_id=4, payload=invalid), 206)
            raise AssertionError('Nonfinite JSON was accepted')
        except ValueError:
            pass
        assert len(receiver.packets()) == 3
        sender.ack(pid)
        assert sender.count() == 0
        sender.close()
        receiver.close()
    finish('semantics_acceptance.json', stage='6B', trajectories_reproduced=144,
           explicit_healthy_approval_gate=True, exact_invalid_window_cases=3,
           full_payload_orderly_restart=True, lost_ack_dedup=True,
           conflict_transaction_rollback=True, nonfinite_json_rejected=True,
           old_arrival_cannot_replace_new_sample=True,
           freshness_uses_acquisition_time=True,
           exclusions=['MCU firmware', 'radio', 'sudden power loss', 'automatic diagnosis of initial fault'])
    print('6B accepted: 144 state records; full-payload SQLite reopen, rollback and stale-arrival checks.')


def transport(p):
    for filename in ['streaming_acceptance.json', 'semantics_acceptance.json']:
        gate = json.loads((m.OUT / filename).read_text(encoding='utf-8'))
        assert gate['passed'] and gate['parameters_sha256'] == m.sha(m.OUT / 'frozen_parameters.json')
    rows = read('transport_results.csv')
    assert len(rows) == 432
    groups = {}
    for row in rows:
        groups.setdefault((row['scene'], float(row['sigma']), int(row['seed'])), []).append(row)
    for (scene, sigma, seed), saved in groups.items():
        _, _, _, monitor = m.collect(scene, dict(m.CASES)[scene], sigma, seed, p)
        for row in saved:
            result, packets, events, views = m.transport(monitor.records, monitor.events, row['mode'], seed)
            compare(row, result)
            assert result['missing_events'] == result['unexpected_events'] == result['duplicate_event_rows'] == 0
            assert result['outstanding_packets'] == 0 and result['latest_acquisition_monotonic']
            assert result['event_contents_equal'] and result['sample_contents_equal']
            assert result['latest_sample_t'] == monitor.records[-1]['t_s']
            for x in packets:
                assert x['received'] >= x['payload']['sample']['t_s']
            for x in events:
                assert x['received'] >= x['event']['t_s']
            for view in views:
                if view['sample_t_s'] is not None:
                    assert view['sample_age_s'] == view['t_s'] - view['sample_t_s']
                    assert view['data_fresh'] == (view['sample_age_s'] <= m.CFG['max_sample_age_s'])
                    if not view['data_fresh']:
                        assert view['remote_status'] == 'stale'
    # Future records never change packets accepted before the cutoff.
    _, _, _, monitor = m.collect('pulse8', False, .3, 45000, p)
    records = json.loads(json.dumps(monitor.records))
    for r in records:
        if r['t_s'] > 370:
            r['pressure_kpa'] = [150., 150.]
    _, first, _, first_views = m.transport(monitor.records, monitor.events, 'outage', 45000)
    _, second, _, second_views = m.transport(records, monitor.events, 'outage', 45000)
    assert [x for x in first if x['received'] <= 370] == [x for x in second if x['received'] <= 370]
    assert [x for x in first_views if x['t_s'] <= 370] == [x for x in second_views if x['t_s'] <= 370]
    finish('transport_acceptance.json', stage='6C', records_reproduced=432,
           acquisition_trajectories=144, network_causal_prefix_check=True,
           acquisition_age_checked_all_views=True,
           results_sha256=m.sha(m.OUT / 'transport_results.csv'),
           examples_sha256=m.sha(m.OUT / 'examples.json'),
           exclusions=['real radio timing', 'frame sizing', 'multiple sender namespaces', 'energy', 'unbounded outage recovery'])
    print('6C accepted: 432 transport replays; full sample/event equality, final drain and causal prefix.')


if __name__ == '__main__':
    p = m.parameters()
    stage = sys.argv[1]
    filename = dict(A='streaming_results.csv', B='semantics_results.csv', C='transport_results.csv')[stage]
    summary = json.loads((m.OUT / f'{stage}_summary.json').read_text(encoding='utf-8'))
    assert summary['parameters_sha256'] == m.sha(m.OUT / 'frozen_parameters.json')
    assert summary['results_sha256'] == m.sha(m.OUT / filename)
    dict(A=streaming, B=semantics, C=transport)[stage](p)
