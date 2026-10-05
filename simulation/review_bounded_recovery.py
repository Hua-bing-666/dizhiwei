"""Frozen paired byte-link recovery experiment; all sensor inputs are synthetic."""
from pathlib import Path
from collections import Counter
import csv
import json
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from compact_protocol import EVENT,TELEMETRY,SAMPLE,Snapshot,decode,StreamDecoder,event_payload,snapshot_from_record
from session_transport import SessionSender,SessionReceiver
from recovery_transport import RecoverySender
from review_integrated_monitor import collect
from review_quality_intervals import sha
import review_protocol_session as previous

OUT=ROOT/'simulation/bounded_recovery_review'
CFG=dict(version='20261006-bounded-recovery-v2',physical_data=False,
         initial_attempts=8,recovery_attempts=4,business_capacity=16,history_capacity=64,
         retention_ms=300000,probe_interval_ms=30000,ack_proof_limit_ms=8000,
         dispatch_interval_ms=1000,flush_s=310,policies=['burst_backoff','bounded_recovery'],
         scenes=previous.CFG['scenes'],sigmas=previous.CFG['sigmas'],seeds=previous.CFG['seeds'],
         modes=['clean','loss','outage'],boundary_scenes=previous.CFG['boundary_scenes'],
         boundary_sigmas=previous.CFG['boundary_sigmas'],boundary_seeds=previous.CFG['boundary_seeds'],
         boundary_outage_seconds=[20,120,360],new_seeds=[48000,48001],
         new_modes=['double_outage','ack_blackout','dead'],
         probe_condition='dispatched unresolved message waiting >=8s AND no ACK within 8s',
         holdout_seeds=[49000,49001],holdout_modes=['loss','double_outage','ack_blackout'])


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def freeze():
    previous.parameters()
    OUT.mkdir(exist_ok=True)
    files=[Path(__file__),ROOT/'prototype/recovery_transport.py',ROOT/'scripts/validate_bounded_recovery.py',
           ROOT/'prototype/session_transport.py',ROOT/'prototype/compact_protocol.py',
           ROOT/'simulation/review_integrated_monitor.py',previous.OUT/'frozen_parameters.json',
           previous.OUT/'byte_link_results.csv',previous.OUT/'boundary_results.csv']
    dump('frozen_parameters.json',dict(config=CFG,previous_parameters_sha256=sha(previous.OUT/'frozen_parameters.json'),
                                     sources={p.relative_to(ROOT).as_posix():sha(p) for p in files}))
    print('Stage-eight configuration frozen before evaluation.')


def parameters():
    previous.parameters()
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    assert p['config']==CFG
    for file,digest in p['sources'].items():assert sha(ROOT/file)==digest,file
    return p


def link_blocked(mode,t,duration):
    return mode=='dead' or mode=='outage' and 350<=t<350+duration or mode=='double_outage' and (350<=t<410 or 440<=t<500)


def byte_replay(monitor,mode,seed,policy,duration=60,save_trace=False):
    recovery=policy=='bounded_recovery'
    sender=RecoverySender(':memory:') if recovery else SessionSender(':memory:',policy='burst_backoff')
    receiver=SessionReceiver(':memory:')
    config_id=9
    receiver.register(1,config_id,1 if monitor.node.context else 0,
                      dict(synthetic=True,healthy_reference_approved=monitor.approved,policy=policy,
                           run_id=monitor.run_id,reference=monitor.node.output()['context']))
    receiver.register_time_mapping(1,1,0,0,'Explicit common simulation clock, not physical synchronisation')
    by={r['t_s']:r for r in monitor.records};events={}
    for e in monitor.events:events.setdefault(e['t_s'],[]).append(e)
    last=monitor.records[-1]['t_s'];end=max(last+CFG['flush_s'],350+duration+120 if mode=='outage' else 0)
    network=np.random.default_rng(seed+20000).random((end+1,2))
    expected={};attempts=wire_bytes=probes=0;max_live=max_audit=peak_bytes=0
    counts=Counter();trace=[];parser=StreamDecoder();ack_parser=StreamDecoder()
    for t in range(130,end+1):
        now=(t+1)*1000
        if t in by:
            snap=snapshot_from_record(by[t],config_id,1)
            if recovery:sender.set_snapshot(snap.pack(),now)
            fresh=events.get(t,[])
            messages=[(EVENT,event_payload(snap,e)) for e in fresh]
            if not fresh and ((t-130)%60==0 or t==last):messages.append((TELEMETRY,snap.pack()))
            for kind,payload in messages:
                frame=sender.enqueue(kind,payload,now)
                if frame is not None:expected[frame.key]=frame
        before=sender.metrics() if recovery else {}
        wire=sender.pick(now)
        if recovery:
            storage=sender.storage();max_live=max(max_live,storage['rows']['recovery_live'])
            max_audit=max(max_audit,storage['rows']['recovery_audit'])
            peak_bytes=max(peak_bytes,storage['retained_wire_bytes']+storage['snapshot_bytes'])
            assert max_live<=16 and max_audit<=64 and storage['rows']['recovery_probe']<=1
            assert peak_bytes<=(16+1+64)*64+35
        if wire is None:continue
        frame=decode(wire);counts[frame.key]+=1;is_probe=frame.key not in expected
        if not is_probe:assert counts[frame.key]<=12 if recovery else counts[frame.key]<=8
        else:assert recovery and frame.kind==TELEMETRY;probes+=1
        attempts+=1;wire_bytes+=len(wire)
        blocked=link_blocked(mode,t,duration) or mode=='loss' and network[t,0]<.2
        event=dict(t_s=t,key=list(frame.key),probe=is_probe,blocked=bool(blocked),ack=False,
                   acquired_ms=Snapshot.unpack(frame.payload[:SAMPLE.size]).uptime_ms)
        if not blocked:
            decoded=[]
            for start in range(0,len(wire),7):decoded.extend(parser.feed(wire[start:start+7]))
            assert len(decoded)==1
            ack=receiver.accept(decoded[0].wire(),now);wire_bytes+=len(ack)
            lost_ack=mode=='ack_blackout' or mode=='loss' and network[t,1]<.25
            if not lost_ack:
                decoded_ack=[]
                for start in range(0,len(ack),5):decoded_ack.extend(ack_parser.feed(ack[start:start+5]))
                assert len(decoded_ack)==1
                assert sender.acknowledge(decoded_ack[0].wire(),now) if recovery else sender.acknowledge(decoded_ack[0].wire())
                event['ack']=True
        if recovery:
            after=sender.metrics()
            event['reactivated']=after['reactivated']-before['reactivated']
        if save_trace:trace.append(event)
    received=receiver.frames();business=[r for r in received if r['key'] in expected]
    events_received=[r for r in business if expected[r['key']].kind==EVENT]
    delays=[]
    for r in business:
        f=expected[r['key']];assert r['body']==f.body
        if f.kind==EVENT:delays.append(r['received_ms']-Snapshot.unpack(f.payload[:SAMPLE.size]).uptime_ms)
    states=sender.states();state_counts=Counter(r['state'] for r in states)
    metrics=sender.metrics() if recovery else {}
    result=dict(policy=policy,mode=mode,generated_events=len(monitor.events),
                enqueued_events=sum(f.kind==EVENT for f in expected.values()),received_events=len(events_received),
                missing_events=len(monitor.events)-len(events_received),
                rejected_messages=metrics.get('rejected_capacity',sender.db.execute('SELECT COUNT(*) FROM rejected').fetchone()[0] if not recovery else 0),
                expired_messages=metrics.get('expired_business',state_counts['expired']),
                unresolved_messages=len(states) if recovery else state_counts['pending']+state_counts['unconfirmed'],
                enqueued_business=len(expected),received_business=len(business),
                attempts=attempts,probe_attempts=probes,attempted_uart_bytes_including_ack=wire_bytes,
                initial_attempts=metrics.get('initial_dispatch',attempts),recovery_attempts=metrics.get('recovery_dispatch',0),
                reactivated=metrics.get('reactivated',0),recovery_observations=metrics.get('recovery_observations',0),
                history_evicted=metrics.get('history_evicted',0),
                max_event_lag_ms=max(delays) if delays else None,
                stream_parser_errors=parser.errors+ack_parser.errors,
                duplicate_business_rows=len(business)-len({r['key'] for r in business}),
                max_business_slots=max_live if recovery else None,
                max_history_slots=max_audit if recovery else None,peak_retained_wire_and_snapshot_bytes=peak_bytes if recovery else None,
                latest_sample_seq=receiver.current(1,(end+1)*1000)['sample_seq'])
    assert result['received_events']<=result['enqueued_events']<=result['generated_events']
    assert result['duplicate_business_rows']==result['stream_parser_errors']==0
    if save_trace:
        dump('recovery_example.json',dict(scene=monitor.run_id,policy=policy,mode=mode,duration=duration,
                                          result=result,dispatch_trace=trace,
                                          final_current={k:v for k,v in receiver.current(1,(end+1)*1000).items() if k!='snapshot'}))
    sender.close();receiver.close();return result


def replay():
    parameters()
    for name in ['identity','budget']:
        a=json.loads((OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==sha(OUT/'frozen_parameters.json')
    baseline=previous.parameters()['baseline'];rows=[];boundary=[];new=[];holdout=[]
    for sigma in CFG['sigmas']:
        for scene in CFG['scenes']:
            for seed in CFG['seeds']:
                _,_,_,monitor=collect(scene,scene in ['nan_pressure','counter_reset','drift_p0'],sigma,seed,baseline)
                for mode in CFG['modes']:
                    for policy in CFG['policies']:
                        result=byte_replay(monitor,mode,seed,policy,save_trace=(scene=='restriction_r90' and sigma==3 and seed==46000 and mode=='outage' and policy=='bounded_recovery'))
                        rows.append(dict(scene=scene,sigma=sigma,seed=seed,**result))
    for sigma in CFG['boundary_sigmas']:
        for scene in CFG['boundary_scenes']:
            for seed in CFG['boundary_seeds']:
                _,_,_,monitor=collect(scene,scene=='nan_pressure',sigma,seed,baseline)
                for duration in CFG['boundary_outage_seconds']:
                    for policy in CFG['policies']:
                        boundary.append(dict(scene=scene,sigma=sigma,seed=seed,outage_seconds=duration,
                                             **byte_replay(monitor,'outage',seed,policy,duration)))
            for seed in CFG['new_seeds']:
                _,_,_,monitor=collect(scene,scene=='nan_pressure',sigma,seed,baseline)
                for mode in CFG['new_modes']:
                    for policy in CFG['policies']:
                        new.append(dict(scene=scene,sigma=sigma,seed=seed,**byte_replay(monitor,mode,seed,policy)))
            for seed in CFG['holdout_seeds']:
                _,_,_,monitor=collect(scene,scene=='nan_pressure',sigma,seed,baseline)
                for mode in CFG['holdout_modes']:
                    for policy in CFG['policies']:
                        holdout.append(dict(scene=scene,sigma=sigma,seed=seed,**byte_replay(monitor,mode,seed,policy)))
    datasets=[('paired_results.csv',rows),('boundary_results.csv',boundary),('new_seed_results.csv',new),('holdout_results.csv',holdout)]
    for name,records in datasets:write(name,records)
    dump('results_summary.json',dict(physical_data=False,parameters_sha256=sha(OUT/'frozen_parameters.json'),
                                    datasets={name:dict(rows=len(records),sha256=sha(OUT/name)) for name,records in datasets}))
    print('432 main, 72 boundary, 72 repeated-challenge and 72 unused-seed records generated; acceptance pending.')


if __name__=='__main__':
    if '--freeze' in sys.argv:freeze()
    else:replay()
