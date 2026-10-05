"""Separate acceptance gates for identity, finite budgets and paired replay."""
from pathlib import Path
from dataclasses import replace
import csv
import json
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'));sys.path.insert(0,str(ROOT/'simulation'))
from compact_protocol import EVENT,TELEMETRY,ACK,Frame,Snapshot,decode
from recovery_transport import RecoverySender
from session_transport import SessionReceiver
from review_integrated_monitor import collect
import review_bounded_recovery as m


def snapshot(index=1):
    return Snapshot(index*1000,index,7,1,45*index,12000,11000,6000,0,0x87,0,20,10)


def payload(index=1):
    return snapshot(index).pack()+b'\x01\xff'


def ack(frame):
    return Frame(ACK,*frame.key,struct.pack('<I',frame.fingerprint)).wire()


def fails(action):
    try:action()
    except (ValueError,OverflowError,RuntimeError):return
    raise AssertionError('Expected rejection')


def finish(name,checks,**details):
    m.dump(name+'_acceptance.json',dict(passed=True,physical_data=False,
                                       parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),
                                       validator_sha256=m.sha(Path(__file__)),checks=checks,**details))


def exhaust_initial(sender):
    wires=[]
    for now in [1000,3000,5000,7000,27000,47000,67000,87000]:
        wire=sender.pick(now);assert wire is not None;wires.append(wire)
    assert len(set(wires))==1
    assert sender.pick(107000) is None and sender.states()[0]['state']=='parked'
    return wires[0]


def identity():
    checks=[]
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'sender.sqlite';rpath=Path(directory)/'receiver.sqlite'
        s=RecoverySender(path);r=SessionReceiver(rpath)
        r.register(1,7,1,dict(synthetic=True,healthy_reference_approved=True))
        r.register_time_mapping(1,1,0,0,'Independent test mapping')
        frame=s.enqueue(EVENT,payload(),1000)
        assert s.enqueue(EVENT,payload(),1000)==frame
        assert s.metrics()['accepted']==1
        fails(lambda:s.enqueue(EVENT,replace(snapshot(),p0=12001).pack()+b'\x01\xff',1000))
        checks.append('source_idempotence_and_conflict')
        assert not s.acknowledge(ack(frame),1000)
        checks.append('undispatched_frame_cannot_prove_link')
        original=exhaust_initial(s)
        s.set_snapshot(snapshot().pack(),108000)
        probe=decode(s.pick(108000))
        assert probe.kind==TELEMETRY and probe.payload==snapshot().pack()
        wrong=Frame(ACK,*probe.key,struct.pack('<I',probe.fingerprint^1)).wire()
        assert not s.acknowledge(wrong,108000)
        assert s.states()[0]['state']=='parked'
        checks.append('wrong_fingerprint_cannot_reactivate')
        assert not s.acknowledge(Frame(ACK,2,probe.session,probe.seq,struct.pack('<I',probe.fingerprint)).wire(),108000)
        assert not s.acknowledge(Frame(ACK,1,probe.session,probe.seq+100,struct.pack('<I',probe.fingerprint)).wire(),108000)
        checks.append('wrong_device_and_sequence_rejected')
        reply=r.accept(probe.wire(),108000)
        assert r.current(1,108000)['status']=='stale'
        assert s.acknowledge(reply,108000)
        assert s.states()[0]['state']=='recovering'
        assert s.pick(108000) is None
        retried=s.pick(109000);assert retried==original
        assert s.acknowledge(r.accept(retried,109000),109000)
        assert len([x for x in r.frames() if x['body'][1]==EVENT])==1
        checks.extend(['probe_preserves_old_acquisition_time','timely_ack_reactivates_without_oracle',
                       'original_identity_and_bytes_unchanged','receiver_deduplicates_original_event'])
        metrics=s.metrics().copy()
        assert s.acknowledge(reply,109000) and s.metrics()==metrics
        checks.append('duplicate_historical_ack_cannot_reactivate')
        s.close();r.close()
        s=RecoverySender(Path(directory)/'late.sqlite');f=s.enqueue(EVENT,payload(),1000)
        exhaust_initial(s);s.set_snapshot(snapshot().pack(),108000)
        probe=decode(s.pick(108000))
        assert s.acknowledge(ack(probe),117000)
        assert s.states()[0]['state']=='parked' and s.metrics()['reactivated']==0
        assert s.acknowledge(ack(f),118000)
        assert s.metrics()['recovery_observations']==0
        checks.append('ack_older_than_eight_seconds_not_link_proof')
        s.close()
        s=RecoverySender(Path(directory)/'restart.sqlite');f=s.enqueue(EVENT,payload(),1000)
        original=exhaust_initial(s)
        owner=s;n=RecoverySender(Path(directory)/'restart.sqlite')
        fails(lambda:owner.pick(108000))
        assert n.session==2 and n._meta('snapshot') is None
        assert n.states()[0]['initial_attempts']==8
        n.set_snapshot(snapshot().pack(),108000);probe=decode(n.pick(108000))
        assert probe.session==2
        assert n.acknowledge(ack(probe),108000)
        assert n.pick(109000)==original and decode(original).session==1
        checks.extend(['owner_fencing_and_new_session','restart_preserves_old_identity_and_budget',
                       'restart_does_not_repackage_old_snapshot'])
        before=n.metrics().copy();fails(lambda:n.pick(108000));assert n.metrics()==before
        checks.append('host_clock_regression_rolls_back')
        n.set_snapshot(snapshot(2).pack(),110000)
        fails(lambda:n.set_snapshot(snapshot().pack(),110000))
        fails(lambda:n.set_snapshot(replace(snapshot(3),uptime_ms=2000).pack(),110000))
        checks.append('snapshot_order_and_timestamp_regression_rejected')
        n.close();owner.close()
        s=RecoverySender(Path(directory)/'expiry.sqlite');f=s.enqueue(EVENT,payload(),1000)
        assert not s.acknowledge(ack(f),301000)
        assert s.metrics()['expired_business']==1
        checks.append('never_dispatched_expired_frame_cannot_be_acknowledged')
        g=s.enqueue(EVENT,payload(2),301000);assert s.pick(301000)==g.wire()
        assert s.acknowledge(ack(g),601000)
        assert s.metrics()['reactivated']==0
        assert s.db.execute("SELECT state FROM recovery_audit WHERE seq=?",(g.seq,)).fetchone()[0]=='acknowledged_late'
        checks.append('late_expired_ack_records_receipt_without_reactivation')
        s.close()
    finish('identity',checks,actual_sqlite_files=True,power_loss_tested=False)
    print('8A passed:',len(checks),'identity, ACK, age and restart checks.')


def budget():
    checks=[]
    with tempfile.TemporaryDirectory() as directory:
        s=RecoverySender(Path(directory)/'budget.sqlite');s.enqueue(EVENT,payload(),1000)
        exhaust_initial(s);s.set_snapshot(snapshot().pack(),108000)
        proof=decode(s.pick(108000));assert s.acknowledge(ack(proof),108000)
        for now in [109000,111000,113000,115000]:assert decode(s.pick(now)).kind==EVENT
        assert s.pick(117000) is None
        state=s.states()[0];assert state['initial_attempts']==8 and state['recovery_attempts']==4 and state['state']=='parked'
        proof=decode(s.pick(138000));assert s.acknowledge(ack(proof),138000)
        assert s.pick(139000) is None and s.states()[0]['recovery_attempts']==4
        checks.extend(['eight_initial_plus_four_recovery_cap','repeated_restoration_cannot_reset_budget'])
        n=RecoverySender(Path(directory)/'budget.sqlite')
        assert n.states()[0]['recovery_attempts']==4 and n.pick(150000) is None
        checks.append('reopen_cannot_reset_recovery_budget')
        n.close();s.close()
        s=RecoverySender(':memory:')
        f=s.enqueue(EVENT,payload(),1000)
        assert s.pick(1000,False) is None and s.metrics()['initial_dispatch']==0
        assert s.pick(2000)==f.wire() and s.pick(2000) is None
        checks.extend(['aux_not_ready_consumes_no_attempt','one_dispatch_per_second_enforced'])
        s.close()
        s=RecoverySender(Path(directory)/'capacity.sqlite',capacity=1)
        f=s.enqueue(EVENT,payload(),1000);exhaust_initial(s)
        assert s.enqueue(EVENT,payload(2),108000) is None
        assert s.metrics()['rejected_capacity']==1 and s.storage()['rows']['recovery_live']==1
        assert s.db.execute("SELECT sample_seq,code,detail FROM recovery_audit WHERE state='rejected_capacity'").fetchone()==(2,1,255)
        s.set_snapshot(snapshot(2).pack(),108000);probe=decode(s.pick(108000))
        assert probe.kind==TELEMETRY and s.storage()['rows']['recovery_probe']==1
        assert s.acknowledge(ack(probe),108000)
        assert s.pick(109000)==f.wire()
        assert s.pick(301000) is not None  # Reserved probe remains available after business expiry.
        assert s.storage()['rows']['recovery_live']==0 and s.metrics()['expired_business']==1
        assert s.enqueue(EVENT,payload(3),301000) is not None
        checks.extend(['parked_records_count_toward_capacity','reserved_probe_available_when_full',
                       'expiry_frees_capacity_without_claiming_delivery','rejected_source_recorded_without_issued_identity'])
        s.close()
        s=RecoverySender(':memory:',capacity=1,history_capacity=1)
        s.enqueue(EVENT,payload(),1000)
        for now in range(2000,7000,1000):assert s.enqueue(EVENT,payload(2),now) is None
        assert s._meta('source_floor')==0
        assert s.enqueue(EVENT,payload(2),301000) is not None
        checks.append('evicting_rejections_does_not_forbid_later_admission')
        s.close()
        path=Path(directory)/'stress.sqlite';s=RecoverySender(path)
        first=None;recent=None;peak=0
        for index in range(1,1001):
            now=index*1000;frame=s.enqueue(EVENT,payload(index),now)
            first=frame if first is None else first;recent=frame
            assert s.pick(now)==frame.wire();assert s.acknowledge(ack(frame),now)
            storage=s.storage();assert storage['rows']['recovery_live']==0 and storage['rows']['recovery_audit']<=64
            peak=max(peak,storage['retained_wire_bytes'])
        assert s.metrics()['history_evicted']==936
        assert s.enqueue(EVENT,payload(),1000000) is None
        assert s.metrics()['rejected_old_source']==1
        assert s.enqueue(EVENT,payload(1000),1000000)==recent
        assert s.metrics()['accepted']==1000
        assert peak<=64*64
        storage=s.storage();db_size=path.stat().st_size
        checks.extend(['one_thousand_records_bounded_history','evicted_source_watermark_prevents_reenqueue',
                       'retained_recent_source_stays_idempotent'])
        fails(lambda:RecoverySender(path,device=2))
        checks.append('database_enrolment_cannot_change_device')
        with s.db:s.db.execute('UPDATE recovery_meta SET seq=?',(2**32-1,))
        fails(lambda:s.enqueue(EVENT,payload(1001),1000001))
        checks.append('sequence_exhaustion_rejected')
        with s.db:s.db.execute('UPDATE recovery_meta SET session=?',(2**32-1,))
        fails(lambda:RecoverySender(path))
        checks.append('session_exhaustion_rejected_and_handle_closed')
        s.close()
        s=RecoverySender(':memory:');s.enqueue(EVENT,payload(),1000)
        assert s.pick(301000) is None
        assert s.metrics()['initial_dispatch']==0 and s.metrics()['expired_business']==1
        checks.append('exact_ttl_boundary_never_dispatches_expired_message')
        s.close()
    finish('budget',checks,stress_records=1000,stress_storage=storage,observed_host_database_bytes=db_size,
           peak_stress_wire_bytes=peak,scope='Logical rows and bounded blobs; not a Flash or SQLite file-size limit')
    print('8B passed:',len(checks),'budget/storage checks and 1000-message retention stress.')


def replay():
    p=m.parameters();baseline=m.previous.parameters()['baseline']
    summary=json.loads((m.OUT/'results_summary.json').read_text(encoding='utf-8'))
    assert summary['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    total=0;previous_reproduced=0
    with (m.previous.OUT/'byte_link_results.csv').open(encoding='utf-8') as f:
        old_main={(r['scene'],r['sigma'],r['seed'],r['mode']):r for r in csv.DictReader(f) if r['policy']=='burst_backoff'}
    with (m.previous.OUT/'boundary_results.csv').open(encoding='utf-8') as f:
        old_boundary={(r['scene'],r['sigma'],r['seed'],r['outage_seconds']):r for r in csv.DictReader(f) if r['policy']=='burst_backoff'}
    for filename in ['paired_results.csv','boundary_results.csv','new_seed_results.csv']:
        assert summary['datasets'][filename]['sha256']==m.sha(m.OUT/filename)
        with (m.OUT/filename).open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
        assert len(rows)==summary['datasets'][filename]['rows']
        groups={}
        for row in rows:groups.setdefault((row['scene'],float(row['sigma']),int(row['seed'])),[]).append(row)
        for (scene,sigma,seed),saved in groups.items():
            _,_,_,monitor=collect(scene,scene in ['nan_pressure','counter_reset','drift_p0'],sigma,seed,baseline)
            for row in saved:
                actual=m.byte_replay(monitor,row['mode'],seed,row['policy'],int(row.get('outage_seconds',60)))
                for key,value in actual.items():assert row[key]==('' if value is None else str(value)),(filename,key,row[key],value)
                if row['policy']=='burst_backoff' and filename!='new_seed_results.csv':
                    key=(scene,row['sigma'],row['seed'],row['outage_seconds'] if filename=='boundary_results.csv' else row['mode'])
                    old=(old_boundary if filename=='boundary_results.csv' else old_main)[key]
                    for before,after in [('generated_events','generated_events'),('received_events','received_events'),
                                         ('missing_events','missing_events'),('max_event_lag_ms','max_event_lag_ms'),
                                         ('attempts','attempts'),('attempted_uart_wire_bytes_including_ack','attempted_uart_bytes_including_ack')]:
                        assert row[after]==old[before],(key,before,row[after],old[before])
                    previous_reproduced+=1
                total+=1
    assert total==576 and previous_reproduced==252
    finish('replay',['all_576_records_reproduced','252_previous_candidate_rows_match',
                     'identity_body_and_acquisition_time_checked','finite_dispatch_budget_checked_each_frame',
                     'probes_included_in_byte_cost','storage_limits_checked_during_replay'],
           records=total,previous_baseline_records=previous_reproduced,
           datasets=summary['datasets'],scope='Synthetic host-byte experiments, not guaranteed physical delivery')
    print('8C passed: 576 records reproduced; 252 previous candidate baselines unchanged.')


if __name__=='__main__':
    m.parameters();stage=sys.argv[1]
    for name in {'A':[],'B':['identity'],'C':['identity','budget']}[stage]:
        a=json.loads((m.OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    {'A':identity,'B':budget,'C':replay}[stage]()
