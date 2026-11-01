"""Separate directed-input, wire/receiver and final replay acceptance gates."""
from pathlib import Path
import csv,json,sys
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_acquisition_pipeline as m
from acquisition_pipeline import AcquisitionPipeline,SessionResetRequired
from compact_protocol import Frame,Snapshot,EVENT,TELEMETRY,decode,MISSING
from session_transport import SessionReceiver
def finish(name,checks,**kw):
    m.dump(name+'_acceptance.json',dict(passed=True,physical_data=False,parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),
                                    validator_sha256=m.sha(Path(__file__)),checks=checks,**kw))
def inputs():
    m.parameters();args=m.compile_bridge();checks=[]
    for name,reason in [('nonfinite',1),('range',2),('not_ready',4),('stale',4),('repeated',4),('overlap',4),('future',4),('span',4),('late_counter',4),('nan_latch',4)]:
        rows=m.fixed_trace(name);r=rows[420];assert r['fields']['status']==3 and r['fields']['quality_reason']==reason
        assert r['fields']['pattern']==4 and not r['fields']['rapid_active']
        assert all(e['code']<3 for e in r['events'])
        if name=='range':assert r['issue']==2 and r['snapshot'].p0==0
        if name in ('late_counter','nan_latch'):
            assert r['snapshot'].cumulative_pulses==rows[419]['snapshot'].cumulative_pulses
            assert r['snapshot'].q10==MISSING and r['counter_value_is_held']
            assert all(x['snapshot'].q10==MISSING for x in rows[420:431])
            assert not rows[423]['fields']['rapid_valid'] and rows[424]['fields']['rapid_valid']
            assert rows[430]['fields']['status']==4 and rows[431]['fields']['status']==0
        checks.append(name+'_never_valid_at_fault_endpoint')
    rows=m.fixed_trace('counter_reset');assert rows[420]['fields']['quality_reason']==3 and rows[430]['fields']['status']==0
    checks.append('known_counter_reset_endpoint_rebuilds_differently_from_missing_endpoint')
    for bad,reason in [(dict(t=2,count=162),'sequence_or_clock_gap'),(dict(t=0,count=54),'sequence_or_clock_gap'),
                       (dict(t=1,count=2**32),'counter_representation'),(dict(t=1,count=505),'C_input_contract_rejection')]:
        with AcquisitionPipeline(m.fixture_profile(),m.EXE) as p:
            p.update(0,54,1000,m.reads(0));before=len(p.records)
            try:p.update(bad['t'],bad['count'],(bad['t']+1)*1000,m.reads(bad['t']))
            except SessionResetRequired as e:assert str(e)==reason
            else:raise AssertionError('Input accepted')
            assert p.halted and p.clock==0 and len(p.records)==before
            try:p.update(1,108,2000,m.reads(1))
            except SessionResetRequired:pass
            else:raise AssertionError('Halted session resumed silently')
        checks.append(reason+'_halts_without_new_snapshot')
    with AcquisitionPipeline(m.fixture_profile(),m.EXE) as p:r,_=p.update(0,54,1000,m.reads(0));assert r['sample_index']==0
    checks.append('explicit_new_instance_starts_new_measurement_not_gap_filling')
    for kwargs in [dict(config_id=0),dict(reference_id=0)]:
        try:AcquisitionPipeline(m.fixture_profile(),m.EXE,**kwargs)
        except ValueError:pass
        else:raise AssertionError('Invalid identity accepted')
    checks.append('invalid_identity_rejected_before_starting_worker')
    finish('input',checks,compiler_command=args)
    print(f'11A passed: {len(checks)} directed groups',flush=True)
def receiver():
    m.parameters();m.compile_bridge();checks=[]
    r=m.fixed_trace('late_counter')[420];snap=r['snapshot'];frame=Frame(TELEMETRY,1,1,1,snap.pack());wire=frame.wire()
    rx=SessionReceiver(':memory:')
    try:
        try:rx.accept(wire,snap.uptime_ms)
        except ValueError:pass
        else:raise AssertionError('Unregistered evidence accepted')
        assert not rx.frames();checks.append('unknown_evidence_has_no_commit_or_ACK')
        rx.register(1,11,1,dict(synthetic=True,healthy_reference_approved=True));rx.register_time_mapping(1,1,0,0,'Host clock')
        try:rx.accept(wire,snap.uptime_ms,crash='before_commit')
        except RuntimeError:pass
        else:raise AssertionError('Missing injection')
        assert not rx.frames();checks.append('pre_commit_fault_rolls_back_without_ACK')
        try:rx.accept(wire,snap.uptime_ms,crash='after_commit')
        except RuntimeError:pass
        else:raise AssertionError('Missing injection')
        assert rx.frames()[0]['body']==frame.body
        ack=rx.accept(wire,snap.uptime_ms+1000);assert decode(ack).key==frame.key and len(rx.frames())==1
        checks.append('post_commit_replay_is_idempotent_and_ACKs_original_identity')
        assert rx.current(1,snap.uptime_ms+66000)['fresh'] is False
        assert rx.frames()[0]['received_ms']==snap.uptime_ms
        checks.append('old_snapshot_age_and_first_receipt_never_refreshed_by_retransmission')
        assert rx.current(1,snap.uptime_ms)['snapshot'].q10==MISSING
        checks.append('held_counter_is_unavailable_not_current_flow_evidence')
        conflict=Frame(TELEMETRY,1,1,1,replace(snap,cumulative_pulses=snap.cumulative_pulses+1).pack())
        try:rx.accept(conflict.wire(),snap.uptime_ms)
        except ValueError:pass
        else:raise AssertionError('Content conflict accepted')
        assert len(rx.frames())==1;checks.append('same_identity_conflict_never_overwrites_original')
    finally:rx.close()
    finish('receiver',checks);print(f'11B passed: {len(checks)} receiver groups',flush=True)
def final():
    m.parameters()
    for n in ['input','receiver']:assert json.loads((m.OUT/(n+'_acceptance.json')).read_text(encoding='utf-8'))['passed']
    s=json.loads((m.OUT/'results_summary.json').read_text(encoding='utf-8'))
    assert s['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    for name,digest in s['datasets'].items():assert m.sha(m.OUT/name)==digest
    rows=list(csv.DictReader((m.OUT/'results.csv').open(encoding='utf-8')))
    old=list(csv.DictReader((m.previous.OUT/'results.csv').open(encoding='utf-8')))
    assert len(rows)==216==len(old) and s['field_differences']==0
    for a,b in zip(rows,old):
        for key in ['dataset','scene','sigma','seed']:assert a[key]==b[key],key
        assert a['updates']==b['c_oracle_records'] and a['monitored_updates']==b['records']
    links=list(csv.DictReader((m.OUT/'link_results.csv').open(encoding='utf-8')))
    assert len(links)==80 and all(int(r['max_live'])<=16 and int(r['max_total_rows'])<=83 and int(r['max_telemetry'])<=1 for r in links)
    clean=[r for r in links if r['mode']=='clean'];assert len(clean)==20
    assert all(r['generated_events']==r['received_events'] and r['rejected_events']=='0' for r in clean)
    finish('final',['216_profiles_and_130896_updates_match_frozen_oracle','all_wire_frames_fragment_decode_and_validate',
                    '80_end_to_end_runs_with_bounded_queues','20_clean_runs_receive_every_generated_event',
                    'loss_rejection_and_expiry_recorded_separately','directed_fault_traces_preserved'],summary=s)
    print('11C passed: 216 trajectories, 80 link runs; host software scope closed',flush=True)
if __name__=='__main__':{'A':inputs,'B':receiver,'C':final}[sys.argv[1]]()
