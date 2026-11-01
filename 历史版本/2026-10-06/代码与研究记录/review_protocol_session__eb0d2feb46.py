"""Stage-seven frozen protocol tests and a finite byte-link replay."""
from pathlib import Path
import csv
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from compact_protocol import EVENT,TELEMETRY,SAMPLE,StreamDecoder,decode,event_payload,snapshot_from_record
from session_transport import SessionSender,SessionReceiver
from review_integrated_monitor import collect
from review_quality_intervals import sha

OUT = ROOT/'simulation/protocol_session_review'
BASE = ROOT/'simulation/integrated_monitor_review/frozen_parameters.json'
CFG = dict(version='20261006-compact-session-v2',frame_version=2,limit_bytes=64,
           policies=['rapid8','burst_backoff'],burst_backoff_delays_ms=[2000]*3+[20000]*5,
           status_interval_s=60,retry_ms=2000,capacity=16,max_attempts=8,retention_ms=300000,
           pressure_age_limit_ms=30,counter_latch_tolerance_ms=1,
           scenes=['normal','pulse8','restriction_r90','nan_pressure','counter_reset','drift_p0'],
           seeds=list(range(46000,46004)),sigmas=[.3,3.,10.],link_modes=['clean','loss','outage'],
           data_loss=.2,ack_loss=.25,outage=[350,410],flush_s=120,physical_data=False,energy_measured=False)
CFG.update(boundary_scenes=['pulse8','nan_pressure','restriction_r90'],boundary_sigmas=[.3,10.],
           boundary_seeds=[47000,47001],boundary_outage_seconds=[20,120,360])


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def freeze():
    OUT.mkdir(exist_ok=True)
    sources=[Path(__file__),ROOT/'prototype/compact_protocol.py',ROOT/'prototype/session_transport.py',
             ROOT/'simulation/acquisition_timing.py',ROOT/'simulation/timed_monitor.py',
             ROOT/'firmware/protocol_v2_codec.c',ROOT/'scripts/validate_protocol_session.py',
             ROOT/'simulation/interface_review/event_protocol.py',BASE,
             ROOT/'simulation/integrated_monitor_review/examples.json']
    dump('frozen_parameters.json',dict(config=CFG,baseline=json.loads(BASE.read_text(encoding='utf-8')),
                                     sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources}))
    source=ROOT/'tmp/protocol_session/manufacturer_sources.json'
    dump('manufacturer_sources.json',json.loads(source.read_text(encoding='utf-8')))
    print('Protocol/session/timing configuration frozen before acceptance.')


def parameters():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    assert p['config']==CFG
    for file,digest in p['sources'].items():assert sha(ROOT/file)==digest,file
    return p


def byte_replay(monitor,context,mode,seed,policy='rapid8',outage_seconds=60):
    sender=SessionSender(':memory:',policy=policy);receiver=SessionReceiver(':memory:')
    config_id=7 if policy=='rapid8' else 8
    metadata=dict(synthetic=True,healthy_reference_approved=monitor.approved,
                  initial_numeric_reference=context,run_id=monitor.run_id,retry_policy=policy,
                  parameters_sha256=sha(BASE),evidence='Synthetic calibration; no actual sensor reference')
    receiver.register(1,config_id,1 if monitor.node.context else 0,metadata)
    receiver.register_time_mapping(1,1,0,0,'Explicit common clock of this software experiment')
    by={r['t_s']:r for r in monitor.records};events={}
    for e in monitor.events:events.setdefault(e['t_s'],[]).append(e)
    last=monitor.records[-1]['t_s'];rng=np.random.default_rng(seed+20000)
    network=rng.random((last+CFG['flush_s']+1,2))
    expected={};generated_event_count=len(monitor.events);attempts=wire_bytes=0
    errors=0;max_age=None
    data_decoder=StreamDecoder();ack_decoder=StreamDecoder()
    for t in range(130,last+CFG['flush_s']+1):
        now=(t+1)*1000
        if t in by:
            record=by[t];snap=snapshot_from_record(record,config_id,1)
            fresh=events.get(t,[])
            messages=[(EVENT,event_payload(snap,e)) for e in fresh]
            if not fresh and ((t-130)%60==0 or t==last):messages.append((TELEMETRY,snap.pack()))
            for kind,payload in messages:
                frame=sender.enqueue(kind,payload,now)
                if frame is not None:expected[frame.key]=frame
        wire=sender.pick(now)
        if wire is None:continue
        attempts+=1;wire_bytes+=len(wire)
        blocked=mode=='outage' and 350<=t<350+outage_seconds
        if blocked or mode=='loss' and network[t,0]<.2:continue
        # Fragment independently of network randomness; retain parser state.
        frames=[]
        for start in range(0,len(wire),7):frames.extend(data_decoder.feed(wire[start:start+7]))
        assert len(frames)==1
        ack=receiver.accept(frames[0].wire(),now)
        wire_bytes+=len(ack)
        current=receiver.current(1,now)
        assert current['status'] in ('current','stale')
        max_age=max(max_age or 0,current['age_interval_ms'][1])
        if mode=='loss' and network[t,1]<.25:continue
        ack_frames=[]
        for start in range(0,len(ack),5):ack_frames.extend(ack_decoder.feed(ack[start:start+5]))
        assert len(ack_frames)==1 and sender.acknowledge(ack_frames[0].wire())
    received=receiver.frames();event_rows=[r for r in received if r['body'][1]==EVENT]
    lags=[]
    for r in received:
        f=expected[r['key']];assert r['body']==f.body
        if f.kind==EVENT:
            snap=__import__('compact_protocol').Snapshot.unpack(f.payload[:SAMPLE.size])
            lags.append(r['received_ms']-snap.uptime_ms)
    states=sender.states();counts={state:sum(v['state']==state for v in states) for state in sorted({v['state'] for v in states})}
    result=dict(policy=policy,mode=mode,generated_events=generated_event_count,enqueued_events=sum(f.kind==EVENT for f in expected.values()),
                received_events=len(event_rows),missing_events=generated_event_count-len(event_rows),
                rejected_messages=sender.db.execute('SELECT COUNT(*) FROM rejected').fetchone()[0],
                enqueued_messages=len(expected),received_messages=len(received),
                content_conflicts=errors,attempts=attempts,attempted_uart_wire_bytes_including_ack=wire_bytes,
                pending=counts.get('pending',0),unconfirmed=counts.get('unconfirmed',0),expired=counts.get('expired',0),
                max_event_lag_ms=max(lags) if lags else None,
                stream_parser_errors=data_decoder.errors+ack_decoder.errors,
                duplicate_received_rows=len(received)-len({r['key'] for r in received}),
                latest_session=receiver.current(1,(last+1)*1000)['session'])
    sender.close();receiver.close()
    return result


def replay():
    p=parameters();locked=sha(OUT/'frozen_parameters.json')
    for stage in ['codec','session','timing']:
        a=json.loads((OUT/f'{stage}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==locked
    rows=[]
    for sigma in CFG['sigmas']:
        for scene in CFG['scenes']:
            for seed in CFG['seeds']:
                _,_,_,monitor=collect(scene,scene in ['nan_pressure','counter_reset','drift_p0'],sigma,seed,p['baseline'])
                context=monitor.node.output()['context']
                for mode in CFG['link_modes']:
                    for policy in CFG['policies']:
                        result=byte_replay(monitor,context,mode,seed,policy)
                        rows.append(dict(scene=scene,sigma=sigma,seed=seed,**result))
    write('byte_link_results.csv',rows)
    boundary=[]
    for sigma in CFG['boundary_sigmas']:
        for scene in CFG['boundary_scenes']:
            for seed in CFG['boundary_seeds']:
                _,_,_,monitor=collect(scene,scene=='nan_pressure',sigma,seed,p['baseline'])
                for duration in CFG['boundary_outage_seconds']:
                    for policy in CFG['policies']:
                        result=byte_replay(monitor,monitor.node.output()['context'],'outage',seed,policy,duration)
                        boundary.append(dict(scene=scene,sigma=sigma,seed=seed,outage_seconds=duration,**result))
    write('boundary_results.csv',boundary)
    dump('byte_link_summary.json',dict(rows=len(rows),source_trajectories=72,physical_data=False,
                                      parameters_sha256=locked,results_sha256=sha(OUT/'byte_link_results.csv'),
                                      boundary_rows=len(boundary),boundary_sha256=sha(OUT/'boundary_results.csv'),
                                      dependence='Paired scenarios and network modes reuse seeds. These are host byte replays, not RF trials.'))
    print(f'{len(rows)} byte-link replays complete; independent replay acceptance pending.')


if __name__=='__main__':
    if '--freeze' in sys.argv:freeze()
    else:replay()
