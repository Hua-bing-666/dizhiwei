"""Admission, bounded storage and paired replay acceptance gates."""
from pathlib import Path
from dataclasses import replace
from collections import defaultdict
import csv
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'));sys.path.insert(0,str(ROOT/'simulation'));sys.path.insert(0,str(ROOT/'scripts'))
from compact_protocol import EVENT,TELEMETRY,Snapshot,decode
from admission_transport import AdmissionSender
from recovery_transport import RecoverySender
from review_integrated_monitor import collect
import review_event_admission as m
import validate_bounded_recovery as inherited

snapshot=inherited.snapshot;payload=inherited.payload;ack=inherited.ack;fails=inherited.fails


def finish(name,checks,**details):
    m.dump(name+'_acceptance.json',dict(passed=True,physical_data=False,
                                       parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),
                                       validator_sha256=m.sha(Path(__file__)),checks=checks,**details))


def regress(name):
    original_cls=inherited.RecoverySender;original_finish=inherited.finish
    inherited.RecoverySender=AdmissionSender
    inherited.finish=lambda stage,checks,**details:finish('recovery_'+stage,checks,
                                                        inherited_validator_sha256=m.sha(ROOT/'scripts/validate_bounded_recovery.py'),**details)
    try:{'identity':inherited.identity,'budget':inherited.budget}[name]()
    finally:inherited.RecoverySender=original_cls;inherited.finish=original_finish


def admission():
    regress('identity');checks=[]
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'telemetry.sqlite';s=AdmissionSender(path)
        old=s.enqueue(TELEMETRY,snapshot().pack(),1000);assert s.pick(1000)==old.wire()
        before=s.states();assert s.enqueue(TELEMETRY,snapshot().pack(),2000)==old and s.states()==before
        checks.append('same_latest_telemetry_preserves_identity_and_budget')
        new=s.enqueue(TELEMETRY,snapshot(2).pack(),2000)
        assert new.key!=old.key and new.payload==snapshot(2).pack()
        assert len(s.states())==1 and s.states()[0]['seq']==new.seq
        assert s.metrics()['telemetry_superseded']==1 and s.metrics()['ack_business']==0
        assert s.db.execute('SELECT wire FROM recovery_audit WHERE seq=?',(old.seq,)).fetchone()[0]==old.wire()
        checks.extend(['new_source_gets_new_immutable_frame','supersession_is_not_acknowledgement'])
        assert s.acknowledge(ack(old),3000)
        assert s.states()[0]['seq']==new.seq and s.states()[0]['initial_attempts']==0
        assert s.metrics()['reactivated']==s.metrics()['recovery_observations']==0
        assert s.metrics()['late_retired_telemetry_ack']==1
        assert s.acknowledge(ack(old),3000) and s.metrics()['late_retired_telemetry_ack']==1
        checks.append('old_ack_only_marks_old_retired_frame_once')
        before=s.states();metrics=s.metrics().copy()
        fails(lambda:s.enqueue(TELEMETRY,replace(snapshot(2),p0=12001).pack(),3000))
        fails(lambda:s.enqueue(TELEMETRY,snapshot().pack(),3000))
        fails(lambda:s.enqueue(TELEMETRY,replace(snapshot(3),uptime_ms=2000).pack(),3000))
        assert s.states()==before and s.metrics()==metrics
        checks.append('conflicting_or_older_telemetry_does_not_replace_queue')
        with s.db:s.db.execute('UPDATE recovery_meta SET seq=?',(2**32-1,))
        before=s.states();metrics=s.metrics().copy();audit=s.db.execute('SELECT * FROM recovery_audit').fetchall()
        fails(lambda:s.enqueue(TELEMETRY,snapshot(3).pack(),3000))
        assert s.states()==before and s.metrics()==metrics and s.db.execute('SELECT * FROM recovery_audit').fetchall()==audit
        checks.append('sequence_failure_rolls_back_supersession_and_metrics')
        s.close()
        s=AdmissionSender(Path(directory)/'priority.sqlite',capacity=2)
        old=s.enqueue(TELEMETRY,snapshot().pack(),1000);assert s.pick(1000)==old.wire()
        e2=s.enqueue(EVENT,payload(2),2000);e3=s.enqueue(EVENT,payload(3),3000)
        assert {r['seq'] for r in s.states()}=={e2.seq,e3.seq}
        assert s.metrics()['telemetry_evicted_for_event']==1 and s.metrics()['telemetry_superseded']==0
        assert s.db.execute('SELECT wire FROM recovery_live WHERE seq=?',(e2.seq,)).fetchone()[0]==e2.wire()
        checks.append('full_queue_event_retires_telemetry_only')
        assert s.acknowledge(ack(old),3000)
        assert s.metrics()['ack_business']==s.metrics()['reactivated']==0 and len(s.states())==2
        checks.append('evicted_telemetry_ack_cannot_confirm_events')
        before=s.states()
        assert s.enqueue(EVENT,payload(4),4000) is None
        assert s.enqueue(TELEMETRY,snapshot(5).pack(),5000) is None
        assert s.states()==before and s.metrics()['rejected_events_capacity']==s.metrics()['rejected_telemetry_capacity']==1
        checks.append('all_event_queue_rejects_new_event_and_telemetry')
        s.set_snapshot(snapshot(5).pack(),5000);assert decode(s.pick(6000)).kind==EVENT
        assert decode(s.pick(14000)).kind==TELEMETRY
        assert len(s.states())==2 and s.storage()['rows']['recovery_probe']==1
        checks.append('reserved_probe_does_not_evict_events')
        owner=s;n=AdmissionSender(Path(directory)/'priority.sqlite',capacity=2)
        assert n.session==2 and n.db.execute('SELECT last_telemetry_wire FROM admission_policy').fetchone()[0] is None
        assert {r['seq'] for r in n.states()}=={e2.seq,e3.seq}
        fails(lambda:owner.pick(15000))
        checks.append('reopen_preserves_events_and_clears_new_session_telemetry_identity')
        n.close();owner.close()
        p=Path(directory)/'rollback.sqlite';s=AdmissionSender(p,capacity=1)
        old=s.enqueue(TELEMETRY,snapshot().pack(),1000)
        with s.db:s.db.execute('UPDATE recovery_meta SET seq=?',(2**32-1,))
        metrics=s.metrics().copy();states=s.states()
        fails(lambda:s.enqueue(EVENT,payload(2),2000))
        assert s.states()==states and s.metrics()==metrics
        assert s.db.execute('SELECT wire FROM recovery_live').fetchone()[0]==old.wire()
        checks.append('event_insert_failure_rolls_back_telemetry_eviction')
        s.close()
        plain=RecoverySender(Path(directory)/'previous.sqlite');plain.close()
        fails(lambda:AdmissionSender(Path(directory)/'previous.sqlite'))
        s=AdmissionSender(Path(directory)/'fixed.sqlite',capacity=2);s.close()
        fails(lambda:AdmissionSender(Path(directory)/'fixed.sqlite',capacity=3))
        checks.append('database_policy_and_capacity_cannot_silently_change')
    example=AdmissionSender(':memory:',capacity=4);steps=[]
    for i,kind in enumerate([TELEMETRY,EVENT,EVENT,EVENT,EVENT,TELEMETRY,EVENT],1):
        frame=example.enqueue(kind,snapshot(i).pack() if kind==TELEMETRY else payload(i),i*1000)
        events=example.db.execute('SELECT COUNT(*) FROM recovery_live WHERE kind=?',(EVENT,)).fetchone()[0]
        telemetry=example.db.execute('SELECT COUNT(*) FROM recovery_live WHERE kind=?',(TELEMETRY,)).fetchone()[0]
        steps.append(dict(step=i,source_seq=i,kind=kind,accepted=frame is not None,events=events,telemetry=telemetry))
    assert [(r['events'],r['telemetry']) for r in steps]==[(0,1),(1,1),(2,1),(3,1),(4,0),(4,0),(4,0)]
    m.dump('queue_example.json',dict(capacity=4,steps=steps,metrics=example.metrics(),physical_data=False))
    example.close();checks.append('four_slot_illustration_matches_actual_admission_states')
    finish('admission',checks,inherited_identity_checks=17,actual_sqlite_files=True,power_loss_tested=False)
    print('9A passed:',len(checks),'admission checks plus 17 inherited identity checks.')


def storage():
    regress('budget');checks=[];s=AdmissionSender(':memory:');peak=0
    for index in range(1,1001):
        frame=s.enqueue(TELEMETRY,snapshot(index).pack(),index*1000)
        state=s.storage();assert state['rows']['recovery_live']==1 and state['rows']['recovery_audit']<=64
        assert state['last_telemetry_wire_bytes']==55 and sum(state['rows'].values())<=83
        peak=max(peak,state['retained_wire_bytes']+state['snapshot_bytes'])
    assert s.metrics()['telemetry_superseded']==999 and s.metrics()['history_evicted']==935
    checks.append('one_thousand_telemetry_updates_keep_one_live_and_bounded_history')
    latest=frame;assert s.pick(1000000)==latest.wire()
    initial=s.states()[0]['initial_attempts']
    assert s.enqueue(TELEMETRY,snapshot(1000).pack(),1000000)==latest
    assert s.states()[0]['initial_attempts']==initial
    assert s.enqueue(EVENT,payload(1001),1001000) is not None
    # Explicitly force the latest ordinary telemetry out with events, then prune its history.
    for index in range(1002,1017):assert s.enqueue(EVENT,payload(index),index*1000) is not None
    assert s.metrics()['telemetry_evicted_for_event']==1
    for index in range(1017,1090):s.enqueue(EVENT,payload(index),index*1000)
    assert s.db.execute('SELECT COUNT(*) FROM recovery_audit WHERE session=1 AND seq=?',(latest.seq,)).fetchone()[0]==0
    accepted=s.metrics()['accepted'];before=s.states()
    assert s.enqueue(TELEMETRY,snapshot(1000).pack(),1090000)==latest
    assert s.metrics()['accepted']==accepted and s.states()==before
    checks.append('latest_telemetry_identity_survives_history_pruning_without_requeue')
    s.close()
    s=AdmissionSender(':memory:');frames=[]
    for index in range(1,17):frames.append(s.enqueue(EVENT,payload(index),index*1000))
    assert s.enqueue(EVENT,payload(17),17000) is None
    assert len(s.states())==16 and s.metrics()['rejected_events_capacity']==1
    assert [r[0] for r in s.db.execute('SELECT wire FROM recovery_live ORDER BY seq')]==[f.wire() for f in frames]
    checks.append('seventeenth_dense_event_rejected_without_overwriting_sixteen')
    assert s.enqueue(EVENT,payload(18),301000) is not None
    assert s.metrics()['expired_events']==1 and s.metrics()['expired_telemetry']==0
    checks.append('exact_ttl_frees_event_slot_without_extending_deadline')
    state=s.storage();s.close()
    finish('storage',checks,telemetry_stress_records=1000,inherited_budget_checks=19,
           peak_telemetry_stress_wire_bytes=peak,last_dense_event_storage=state,
           conservative_wire_and_snapshot_bound_bytes=5283,
           exclusions=['SQLite pages and journal','Flash layout and wear','sudden power loss'])
    print('9B passed:',len(checks),'new storage checks plus 19 inherited budget checks.')


def replay():
    parameters=m.parameters();baseline=m.previous.previous.parameters()['baseline']
    summary=json.loads((m.OUT/'results_summary.json').read_text(encoding='utf-8'))
    assert summary['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    original={}
    for filename in m.CFG['previous_datasets']:
        with (m.previous.OUT/filename).open(encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['policy']=='bounded_recovery':original[(filename,r['scene'],float(r['sigma']),int(r['seed']),r['mode'],int(r.get('outage_seconds',60)))]=r
    total=previous_count=0
    for filename in ['paired_results.csv','holdout_results.csv']:
        assert summary['datasets'][filename]['sha256']==m.sha(m.OUT/filename)
        with (m.OUT/filename).open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
        assert len(rows)==summary['datasets'][filename]['rows']
        grouped=defaultdict(list);pairs=defaultdict(list)
        for r in rows:
            grouped[(r['scene'],float(r['sigma']),int(r['seed']))].append(r)
            pairs[(r['dataset'],r['scene'],r['sigma'],r['seed'],r['mode'],r['outage_seconds'])].append(r)
        for pair in pairs.values():
            assert len(pair)==2 and pair[0]['input_sha256']==pair[1]['input_sha256']
            assert pair[0]['generated_events']==pair[1]['generated_events'] and pair[0]['generated_telemetry']==pair[1]['generated_telemetry']
        for (scene,sigma,seed),saved in grouped.items():
            _,_,_,monitor=collect(scene,scene in ['nan_pressure','counter_reset','drift_p0'],sigma,seed,baseline)
            for r in saved:
                actual=m.byte_replay(monitor,r['mode'],seed,r['policy'],int(r['outage_seconds']))
                assert all(r[k]==('' if v is None else str(v)) for k,v in actual.items()),(filename,r)
                if r['policy']=='bounded_recovery' and filename=='paired_results.csv':
                    old=original[(r['dataset'],scene,sigma,seed,r['mode'],int(r['outage_seconds']))]
                    assert all(r[k]==v for k,v in old.items()),('previous',r)
                    previous_count+=1
                total+=1
    assert total==744 and previous_count==324
    finish('replay',['744_results_reproduced','324_previous_candidate_records_unchanged',
                     'paired_input_hashes_and_generated_counts_equal','original_body_and_dispatch_budget_checked_by_reference_runner',
                     'probe_bytes_included','telemetry_dispositions_and_event_expiry_separate'],
           records=total,previous_candidate_records=previous_count,datasets=summary['datasets'])
    print('9C passed: 744 records reproduced, 324 previous candidate records unchanged.')


if __name__=='__main__':
    m.parameters();stage=sys.argv[1]
    for name in {'A':[],'B':['admission'],'C':['admission','storage']}[stage]:
        a=json.loads((m.OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    {'A':admission,'B':storage,'C':replay}[stage]()
