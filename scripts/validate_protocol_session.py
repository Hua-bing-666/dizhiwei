"""Separate byte, identity, timing and link acceptance gates."""
from pathlib import Path
from dataclasses import replace
import csv
import json
import random
import struct
import subprocess
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'));sys.path.insert(0,str(ROOT/'simulation'))
import compact_protocol as c
import review_protocol_session as m
from session_transport import SessionSender,SessionReceiver
from acquisition_timing import Counter16,PressureRead,TimingGuard,nominal_schedule
from timed_monitor import TimedMonitor
from review_integrated_monitor import collect


def fails(action,error=(ValueError,OverflowError,RuntimeError)):
    try:action()
    except error:return
    raise AssertionError('Expected rejection')


def finish(name,**details):
    m.dump(name+'_acceptance.json',dict(passed=True,physical_data=False,
                                       parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),
                                       validator_sha256=m.sha(Path(__file__)),**details))


def golden():
    return c.Snapshot(1000,1,7,1,540,12000,11000,6000,0,0x87,0,20,10)


def codec():
    s=golden();event=c.Frame(c.EVENT,1,1,1,s.pack()+b'\x01\xff')
    telemetry=c.Frame(c.TELEMETRY,1,1,2,s.pack())
    ack=c.Frame(c.ACK,*event.key,struct.pack('<I',event.fingerprint))
    assert event.body.hex()=='02012500010000000100000001000000e8030000010000000700000001001c020000e02e0000f82a000070170000008700140a01ff'
    assert event.wire().hex()=='0402012502010101020101010201010103e8030102010101020701010201031c020103e02e0103f82a010370170101028707140a01ff1efa00'
    assert c.crc16(b'123456789')==0x29b1
    frames=[event,telemetry,ack];fragment_cases=0
    for frame in frames:
        wire=frame.wire();assert c.decode(wire)==frame
        for split in range(1,len(wire)):
            parser=c.StreamDecoder();assert parser.feed(wire[:split])+parser.feed(wire[split:])==[frame]
            fragment_cases+=1
    parser=c.StreamDecoder()
    assert parser.feed(event.wire()+telemetry.wire()+ack.wire())==frames
    parser=c.StreamDecoder();assert parser.feed(b'\x01'*100+b'\x00'+event.wire())==[event]
    example=json.loads((ROOT/'simulation/integrated_monitor_review/examples.json').read_text(encoding='utf-8'))
    rows=[];max_pressure_error=max_flow_error=0.
    for ref_id,scene in enumerate(['pulse8','nan_pressure','counter_reset'],1):
        x=example[scene+':clean'];records={r['t_s']:r for r in x['records']}
        for record in x['records']:
            snap=c.snapshot_from_record(record,7,ref_id)
            frame=c.Frame(c.TELEMETRY,1,1,len(frames)+1,snap.pack());frames.append(frame)
            restored=c.Snapshot.unpack(c.decode(frame.wire()).payload)
            for original,number in zip(record['pressure_kpa'],[restored.p0,restored.p1]):
                if original is None:assert number==c.MISSING
                else:max_pressure_error=max(max_pressure_error,abs(original-number/100))
            if record['flow_q10_l_min'] is None:assert restored.q10==c.MISSING
            else:max_flow_error=max(max_flow_error,abs(record['flow_q10_l_min']-restored.q10/1000))
            rows.append(dict(scene=scene,t_s=record['t_s'],kind='telemetry',bytes=len(frame.wire()),roundtrip_equal=restored==snap))
        for e in x['generated']:
            snap=c.snapshot_from_record(records[e['t_s']],7,ref_id)
            frame=c.Frame(c.EVENT,1,1,len(frames)+1,c.event_payload(snap,e));frames.append(frame)
            rows.append(dict(scene=scene,t_s=e['t_s'],kind=e['kind'],bytes=len(frame.wire()),roundtrip_equal=c.decode(frame.wire())==frame))
    assert max_pressure_error<=.005+1e-12 and max_flow_error<=.0005+1e-12
    # Exercise states absent from the three sixth-round figure examples.
    state_vectors=[replace(s,status=1,flags=0x81,pattern=4),
                   replace(s,status=2,flags=0x82,reference_id=0,pattern=4,q10=c.MISSING),
                   replace(s,status=5,flags=0x83,pattern=4,q10=400),
                   replace(s,status=4,flags=0x83,pattern=4,q10=c.MISSING),
                   replace(s,status=3,flags=0x83,pattern=4,p0=c.MISSING,p0_age_ms=255),
                   replace(s,uptime_ms=2**32-1,sample_seq=2**32-1)]
    for snap in state_vectors:
        frame=c.Frame(c.TELEMETRY,1,1,len(frames)+1,snap.pack())
        frames.append(frame)
        assert c.Snapshot.unpack(c.decode(frame.wire()).payload)==snap
    invalid=[]
    for field,value in [('flags',0x97),('status',6),('pattern',4),('p0_age_ms',31),
                        ('p0',c.MISSING),('reference_id',0),('sample_seq',0),('config_id',0)]:
        altered=replace(s,**{field:value})
        fails(altered.pack)
        body=telemetry.body[:16]+c.SAMPLE.pack(*altered.__dict__.values())
        invalid.append(c.cobs_encode(body+struct.pack('<H',c.crc16(body)))+b'\x00')
    for value in [float('nan'),float('inf'),2147483648.]:fails(lambda:c.quantize(value,100))
    for offset,value in [(0,1),(1,9),(8,0),(12,0)]:
        body=bytearray(telemetry.body);body[offset]=value
        if offset in (8,12):body[offset:offset+4]=b'\x00'*4
        invalid.append(c.cobs_encode(bytes(body)+struct.pack('<H',c.crc16(body)))+b'\x00')
        fails(lambda:c.decode(invalid[-1]),ValueError)
    fails(lambda:replace(s,uptime_ms=2**32).pack())
    damaged=[]
    for index in range(len(event.wire())):
        for bit in range(8):
            wire=bytearray(event.wire());wire[index]^=1<<bit
            fails(lambda:c.decode(bytes(wire)),ValueError);damaged.append(bytes(wire))
    # Compile portable C independently; it validates fields as well as CRC/COBS.
    executable=ROOT/'tmp/protocol_session/protocol_v2_codec.exe'
    compile_run=subprocess.run(['D:/bin/gcc.exe','-std=c99','-Wall','-Wextra','-Werror','-O2','-DBUILD_HARNESS',
                                str(ROOT/'firmware/protocol_v2_codec.c'),'-o',str(executable)],capture_output=True,text=True)
    assert compile_run.returncode==0,compile_run.stderr
    commands=[];expected=[]
    for frame in frames:
        commands.extend(['E '+frame.body.hex(),'D '+frame.wire().hex()]);expected.extend([frame.wire().hex(),frame.body.hex()])
    for wire in damaged+invalid:
        commands.append('D '+wire.hex());expected.append('ERR')
    run=subprocess.run([str(executable)],input='\n'.join(commands)+'\n',capture_output=True,text=True,check=True)
    assert run.stdout.splitlines()==expected
    m.write('codec_results.csv',rows)
    m.dump('golden_vectors.json',dict(event_body=event.body.hex(),event_wire=event.wire().hex(),
                                     telemetry_wire=telemetry.wire().hex(),ack_wire=ack.wire().hex()))
    finish('codec',stage='7A',records=len(rows),fragment_boundaries=fragment_cases,
           all_single_bit_corruptions=len(damaged),illegal_semantic_frames=len(invalid),
           c_python_commands=len(commands),portable_c_compilation='gcc -std=c99 -Wall -Wextra -Werror -O2',
           source_c_sha256=m.sha(ROOT/'firmware/protocol_v2_codec.c'),
           pressure_max_error_kpa=max_pressure_error,flow_max_error_l_min=max_flow_error,
           event_bytes=len(event.wire()),telemetry_bytes=len(telemetry.wire()),ack_bytes=len(ack.wire()),
           additional_state_and_uint_boundary_vectors=len(state_vectors),
           results_sha256=m.sha(m.OUT/'codec_results.csv'),
           exclusions=['STM32 compilation/execution','quantized input diagnosis equivalence','RF'])
    print(f'7A passed: {len(rows)} records, {fragment_cases} splits, {len(damaged)} bit corruptions, {len(commands)} C/Python commands.')


def register(receiver,device=1):
    receiver.register(device,7,1,dict(synthetic=True,healthy_reference_approved=True,evidence='Software unit-test fixture'))


def session():
    checks=[]
    with tempfile.TemporaryDirectory(prefix='protocol_identity_',dir=ROOT/'tmp') as folder:
        node=str(Path(folder)/'node.sqlite');rx=str(Path(folder)/'receiver.sqlite')
        sender=SessionSender(node);receiver=SessionReceiver(rx);register(receiver)
        original=sender.enqueue(c.EVENT,golden().pack()+b'\x01\xff',1000)
        assert sender.enqueue(c.EVENT,original.payload,1001)==original
        assert len(sender.states())==1
        wire=sender.pick(1000);ack=receiver.accept(wire,1100)
        assert sender.pick(1100) is None
        separate=__import__('sqlite3').connect(rx)
        assert separate.execute('SELECT COUNT(*) FROM frames').fetchone()[0]==1
        separate.close()
        # ACK intentionally withheld, then reopen the sender while old owner remains.
        reboot=SessionSender(node);assert reboot.session==2
        fails(lambda:sender.pick(3000),RuntimeError)
        assert reboot.pick(3000)==wire
        receiver.close();receiver=SessionReceiver(rx)
        assert receiver.accept(wire,3100)==ack
        assert reboot.acknowledge(ack)
        new=reboot.enqueue(c.EVENT,golden().pack()+b'\x01\xff',5001000)
        assert new.key==(1,2,1) and original.key==(1,1,1)
        receiver.accept(new.wire(),5001000)
        assert receiver.current(1,5001000)['status']=='clock_unmapped'
        receiver.register_time_mapping(1,2,5000000,0,'Independent simulated epoch mapping')
        assert receiver.current(1,5001000)['fresh'] is True
        older=replace(golden(),uptime_ms=3000000,sample_seq=3000)
        receiver.accept(c.Frame(c.TELEMETRY,1,1,3000,older.pack()).wire(),5002000)
        assert receiver.current(1,5002000)['session']==2
        # Same sequence on a second device remains a separate identity.
        second=SessionSender(node,device=2);register(receiver,2)
        other=second.enqueue(c.EVENT,golden().pack()+b'\x01\xff',5003000)
        receiver.accept(other.wire(),5003000)
        assert other.key==(2,1,1)
        checks.extend(['event_source_idempotence','owner_fencing','old_pending_identity_preserved',
                       'commit_visible_before_ack','restart_session_sequence','two_device_namespace',
                       'new_session_selected_before_old_uptime','unmapped_clock_is_not_current'])
        count=receiver.db.execute('SELECT COUNT(*) FROM frames').fetchone()[0]
        conflict=replace(golden(),p0=12001)
        fails(lambda:receiver.accept(c.Frame(c.TELEMETRY,1,2,99,conflict.pack()).wire(),5004000))
        assert receiver.db.execute('SELECT COUNT(*) FROM frames').fetchone()[0]==count
        unknown=replace(golden(),config_id=8)
        fails(lambda:receiver.accept(c.Frame(c.TELEMETRY,1,2,100,unknown.pack()).wire(),5004000))
        reset=replace(golden(),sample_seq=2,uptime_ms=500)
        fails(lambda:receiver.accept(c.Frame(c.TELEMETRY,1,2,101,reset.pack()).wire(),5004000))
        fails(lambda:receiver.register(1,7,1,dict(synthetic=True,healthy_reference_approved=True,evidence='changed')))
        next_snap=replace(golden(),uptime_ms=2000,sample_seq=2)
        next_frame=reboot.enqueue(c.TELEMETRY,next_snap.pack(),5002000)
        fails(lambda:receiver.accept(next_frame.wire(),5002000,crash='before_commit'))
        assert receiver.db.execute('SELECT COUNT(*) FROM frames').fetchone()[0]==count
        fails(lambda:receiver.accept(next_frame.wire(),5002000,crash='after_commit'))
        receiver.close();receiver=SessionReceiver(rx)
        next_ack=receiver.accept(next_frame.wire(),5003000)
        wrong=c.Frame(c.ACK,1,2,next_frame.seq,b'\x00'*4)
        assert reboot.acknowledge(wrong.wire()) is False
        assert reboot.acknowledge(next_ack)
        receiver.register_time_mapping(1,1,0,100,'Explicit unit-test mapping with error bound')
        assert receiver.current(1,5067001)['status']=='stale'
        # A 100ms mapping uncertainty around the freshness boundary is retained.
        receiver.register_time_mapping(2,1,5000000,100,'Independent bounded mapping')
        assert receiver.current(2,5066000)['status']=='time_uncertain'
        checks.extend(['sample_conflict_full_rollback','unknown_config_rejected','uptime_regression_rejected',
                       'registry_immutable','pre_commit_rollback','post_commit_reopen_dedup',
                       'wrong_ack_rejected','age_from_independent_mapping','mapping_uncertainty_retained'])
        sender.close();reboot.close();second.close();receiver.close()
    tiny=SessionSender(':memory:',capacity=2)
    for i in [1,2]:assert tiny.enqueue(c.TELEMETRY,replace(golden(),sample_seq=i,uptime_ms=i*1000).pack(),i*1000)
    assert tiny.enqueue(c.TELEMETRY,replace(golden(),sample_seq=3,uptime_ms=3000).pack(),3000) is None
    assert len(tiny.states())==2 and tiny.db.execute('SELECT COUNT(*) FROM rejected').fetchone()[0]==1
    tiny.close()
    fair=SessionSender(':memory:')
    head=fair.enqueue(c.EVENT,golden().pack()+b'\x01\xff',0);assert fair.pick(0)==head.wire()
    tail=fair.enqueue(c.EVENT,replace(golden(),sample_seq=2,uptime_ms=2000).pack()+b'\x01\x00',1000)
    assert fair.pick(1000)==tail.wire()
    fair.close()
    bounded=SessionSender(':memory:');frame=bounded.enqueue(c.EVENT,golden().pack()+b'\x01\xff',0)
    assert [t for t in range(0,18001,1000) if bounded.pick(t) is not None]==list(range(0,16000,2000))
    assert bounded.states()[0]['state']=='unconfirmed'
    ack=c.Frame(c.ACK,*frame.key,struct.pack('<I',frame.fingerprint))
    assert bounded.acknowledge(ack.wire()) and bounded.states()[0]['state']=='acknowledged_late'
    expired=bounded.enqueue(c.TELEMETRY,replace(golden(),sample_seq=2,uptime_ms=2000).pack(),20000)
    assert expired and bounded.pick(320000) is None and bounded.states()[-1]['state']=='expired'
    bounded.close()
    exhausted=SessionSender(':memory:')
    with exhausted.db:exhausted.db.execute('UPDATE meta SET seq=? WHERE device=1',(2**32-1,))
    fails(lambda:exhausted.enqueue(c.TELEMETRY,golden().pack(),0),OverflowError)
    with exhausted.db:exhausted.db.execute('UPDATE meta SET session=? WHERE device=1',(2**32-1,))
    # Preserve the database to verify next-boot overflow at construction.
    with tempfile.TemporaryDirectory(prefix='boot_exhaust_',dir=ROOT/'tmp') as folder:
        path=str(Path(folder)/'exhaust.sqlite')
        target=__import__('sqlite3').connect(path);exhausted.db.backup(target);target.close()
        fails(lambda:SessionSender(path),OverflowError)
    exhausted.close()
    checks.extend(['capacity_rejection_keeps_pending','eligible_second_frame_not_fifo_blocked',
                   'bounded_attempts_and_late_ack','expired_record_retained','session_and_sequence_exhaustion_rejected'])
    backoff=SessionSender(':memory:',policy='burst_backoff')
    backoff.enqueue(c.EVENT,golden().pack()+b'\x01\xff',0)
    sent=[t for t in range(0,108001,1000) if backoff.pick(t) is not None]
    assert sent==[0,2000,4000,6000,26000,46000,66000,86000]
    assert backoff.states()[0]['state']=='unconfirmed'
    backoff.close();checks.append('burst_backoff_is_bounded_and_preserves_later_attempts')
    finish('session',stage='7B',checks=checks,actual_sqlite_files=True,power_loss_tested=False,
           exclusions=['Flash atomic allocation','SD journal','authentication','actual clock synchronisation'])
    print(f'7B passed: {len(checks)} named identity/transaction/scheduling checks.')


def timing(p):
    rows=[]
    for rate in [.9,1.,1.1]:
        for extra in [0.,2.,7.]:
            guard=TimingGuard();reads=nominal_schedule(1000,rate,extra)
            record=guard.frame(1000,1000,reads)
            expected=reads[1].completed_ms<=1000
            assert record['timing_valid']==expected
            rows.append(dict(rate_factor=rate,extra_per_channel_ms=extra,
                             pair_duration_ms=reads[1].completed_ms-reads[0].started_ms,
                             valid=record['timing_valid'],p0_age_ms=record['ages_ms'][0],p1_age_ms=record['ages_ms'][1]))
    guard=TimingGuard();reads=nominal_schedule(1000)
    assert guard.frame(1000,1000,reads)['timing_valid']
    assert not guard.frame(2000,2000,reads)['timing_valid']
    fails(lambda:guard.frame(4000,4000,nominal_schedule(4000)))
    first=PressureRead(970,980,120);overlap=PressureRead(975,985,110)
    assert not TimingGuard().frame(1000,1000,[first,overlap])['timing_valid']
    assert not TimingGuard().frame(1000,1002,nominal_schedule(1000))['timing_valid']
    assert not TimingGuard().frame(1000,float('nan'),nominal_schedule(1000))['timing_valid']
    fails(lambda:TimingGuard().frame(1000,1000,[]))
    missing=nominal_schedule(1000);missing[0]=replace(missing[0],ready=False)
    assert not TimingGuard().frame(1000,1000,missing)['timing_valid']
    counter=Counter16()
    for t in range(1,2001):assert counter.snapshot((45*t)%65536,t*1000)==45*t
    fails(lambda:Counter16().snapshot(0,2000000))
    counter=Counter16();assert counter.snapshot(40,1000)==40
    fails(lambda:counter.snapshot(0,2000))
    # Rejected timing becomes actual missing pressure in the unmodified algorithms.
    _,obs,counts,base=collect('normal',False,.3,45000,p['baseline'])
    adapter=TimedMonitor(p['baseline']['baseline']['reference'],p['baseline']['baseline']['limits']['1'],'timing-check',True)
    for t,count in enumerate(counts):
        reads=nominal_schedule((t+1)*1000)
        reads=[replace(r,value_kpa=float(obs[t,i])) for i,r in enumerate(reads)]
        adapter.update(t,int(count),(t+1)*1000+(5 if t==360 else 0),reads)
    by={r['t_s']:r for r in adapter.monitor.records}
    assert all(by[t]['diagnostic_pattern']=='unavailable' for t in range(360,371))
    assert by[371]['measurement_status']=='valid'
    assert by[360]['flow_q10_l_min'] is None
    assert any(e.get('reason')=='timing_fault' for e in adapter.monitor.events)
    assert not any(e['kind'] in ('leak_pattern','restriction_pattern','uncertain') for e in adapter.monitor.events)
    initial=TimedMonitor(p['baseline']['baseline']['reference'],p['baseline']['baseline']['limits']['1'],'initial-timing',True)
    for t,count in enumerate(counts[:151]):
        reads=[replace(r,value_kpa=float(obs[t,i])) for i,r in enumerate(nominal_schedule((t+1)*1000))]
        initial.update(t,int(count),(t+1)*1000+(5 if t==40 else 0),reads)
    assert initial.monitor.node.context is None
    assert all(r['measurement_status']=='baseline_unavailable' for r in initial.monitor.records)
    for record in adapter.monitor.records:
        # Missing timing is encoded as missing values, never recycled old pressures.
        c.snapshot_from_record(record,7,1).pack()
    m.write('timing_results.csv',rows)
    m.dump('timing_example.json',dict(records=[r for r in adapter.monitor.records if 350<=r['t_s']<=385],
                                    timing=[r for r in adapter.timing_records if 350<=r['sample_index']<=385],
                                    events=adapter.monitor.events))
    finish('timing',stage='7C',schedule_cases=9,counter_snapshots=2000,
           stale_read_rejected=True,mux_overlap_rejected=True,late_counter_latch_rejected=True,
           missing_ready_rejected=True,timer_gap_requires_explicit_reset=True,
           counter_reset_counterexample=True,ambiguous_wrap_interval_rejected=True,
           invalid_counter_endpoint_excluded_from_future_windows=True,
           timing_fault_index=360,next_valid_index=371,physical_timing_measured=False,
           exclusions=['actual timer interrupt latency','actual ADC timestamps','race-free hardware counter latch','sensor response bandwidth'])
    print('7C passed: nine schedules, 2000 wrap snapshots, timing-to-missing adapter and window recovery.')


def replay(p):
    with (m.OUT/'byte_link_results.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    assert len(rows)==432
    summary=json.loads((m.OUT/'byte_link_summary.json').read_text(encoding='utf-8'))
    assert summary['results_sha256']==m.sha(m.OUT/'byte_link_results.csv')
    grouped={}
    for row in rows:grouped.setdefault((row['scene'],float(row['sigma']),int(row['seed'])),[]).append(row)
    for (scene,sigma,seed),saved in grouped.items():
        _,_,_,monitor=collect(scene,scene in ['nan_pressure','counter_reset','drift_p0'],sigma,seed,p['baseline'])
        for row in saved:
            actual=m.byte_replay(monitor,monitor.node.output()['context'],row['mode'],seed,row['policy'])
            for key,value in actual.items():assert row[key]==('' if value is None else str(value)),(key,row[key],value)
            assert actual['duplicate_received_rows']==0 and actual['stream_parser_errors']==0
    # The initial failed rapid8 experiment must still reproduce unchanged.
    with (m.OUT/'initial_byte_link_results.csv').open(encoding='utf-8') as f:initial=list(csv.DictReader(f))
    current={(r['scene'],r['sigma'],r['seed'],r['mode']):r for r in rows if r['policy']=='rapid8'}
    for r in initial:
        match=current[(r['scene'],r['sigma'],r['seed'],r['mode'])]
        assert all(match[k]==value for k,value in r.items())
    with (m.OUT/'boundary_results.csv').open(encoding='utf-8') as f:boundary=list(csv.DictReader(f))
    assert len(boundary)==72 and summary['boundary_sha256']==m.sha(m.OUT/'boundary_results.csv')
    groups={}
    for row in boundary:groups.setdefault((row['scene'],float(row['sigma']),int(row['seed'])),[]).append(row)
    for (scene,sigma,seed),saved in groups.items():
        _,_,_,monitor=collect(scene,scene=='nan_pressure',sigma,seed,p['baseline'])
        for row in saved:
            actual=m.byte_replay(monitor,monitor.node.output()['context'],'outage',seed,row['policy'],int(row['outage_seconds']))
            assert all(row[k]==('' if v is None else str(v)) for k,v in actual.items())
            assert actual['duplicate_received_rows']==actual['stream_parser_errors']==0
    finish('byte_link',stage='7D',records_reproduced=432,source_trajectories=72,
           initial_failed_baseline_records_reproduced=len(initial),
           independent_new_seed_boundary_records=len(boundary),boundary_results_sha256=m.sha(m.OUT/'boundary_results.csv'),
           results_sha256=m.sha(m.OUT/'byte_link_results.csv'),
           scope='Finite host byte streams with bounded queue/retries; not RF or guaranteed delivery')
    print('7D passed: 432 paired byte-link records; 216 initial failed baseline rows unchanged.')


if __name__=='__main__':
    p=m.parameters()
    stage=sys.argv[1]
    prereq={'A':[],'B':['codec'],'C':['codec','session'],'D':['codec','session','timing']}[stage]
    for name in prereq:
        a=json.loads((m.OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    {'A':codec,'B':session,'C':lambda:timing(p),'D':lambda:replay(p)}[stage]()
