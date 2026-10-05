"""Paired admission experiment, keeping the previous recovery and sensor logic."""
from pathlib import Path
from collections import Counter,defaultdict
import csv
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from compact_protocol import EVENT,TELEMETRY,decode
from recovery_transport import RecoverySender
from admission_transport import AdmissionSender
from review_integrated_monitor import collect
import review_bounded_recovery as previous

OUT=ROOT/'simulation/event_admission_review'
CFG=dict(version='20261006-event-admission-v1',physical_data=False,
         policies=['bounded_recovery','event_priority'],business_capacity=16,history_capacity=64,
         telemetry_limit=1,initial_attempts=8,recovery_attempts=4,retention_ms=300000,
         new_seeds=[50000,50001],new_scenes=['pulse8','nan_pressure','restriction_r90'],
         new_sigmas=[.3,10.],new_modes=['loss','double_outage','ack_blackout','dead'],
         previous_datasets=['paired_results.csv','boundary_results.csv','new_seed_results.csv','holdout_results.csv'])


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def freeze():
    previous.parameters();OUT.mkdir(exist_ok=True)
    sources=[Path(__file__),ROOT/'prototype/admission_transport.py',ROOT/'scripts/validate_event_admission.py',
             ROOT/'prototype/recovery_transport.py',ROOT/'scripts/validate_bounded_recovery.py',
             ROOT/'simulation/review_bounded_recovery.py',previous.OUT/'frozen_parameters.json']
    sources.extend(previous.OUT/name for name in CFG['previous_datasets'])
    dump('frozen_parameters.json',dict(config=CFG,previous_config=previous.CFG,
                                     sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources}))
    print('Stage-nine admission contract frozen before evaluation.')


def parameters():
    previous.parameters()
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    assert p['config']==CFG and p['previous_config']==previous.CFG
    for file,digest in p['sources'].items():assert sha(ROOT/file)==digest,file
    return p


def byte_replay(monitor,mode,seed,policy,duration=60,save_trace=False):
    captured={};requests=[];input_digest=hashlib.sha256();accepted={};dispositions=Counter()
    stats=dict(max_telemetry_slots=0,max_total_rows=0)
    cls=AdmissionSender if policy=='event_priority' else RecoverySender

    class ObservedSender(cls):
        def set_snapshot(self,payload,now_ms):
            input_digest.update(b'S'+now_ms.to_bytes(8,'little')+payload)
            return super().set_snapshot(payload,now_ms)

        def enqueue(self,kind,payload,now_ms):
            input_digest.update(bytes([kind])+now_ms.to_bytes(8,'little')+payload)
            frame=super().enqueue(kind,payload,now_ms)
            requests.append(dict(now_ms=now_ms,kind=kind,source_payload_hex=payload.hex(),
                                 accepted=frame is not None,key=list(frame.key) if frame else None))
            if frame is not None:accepted[frame.key]=kind
            return frame

        def _archive(self,session,seq,wire,initial,recovery,state,now_ms,source=None):
            result=super()._archive(session,seq,wire,initial,recovery,state,now_ms,source)
            if wire is not None and state=='expired':dispositions['expired_events' if decode(wire).kind==EVENT else 'expired_telemetry']+=1
            return result

        def storage(self):
            result=super().storage()
            count=self.db.execute('SELECT COUNT(*) FROM recovery_live WHERE kind=?',(TELEMETRY,)).fetchone()[0]
            stats['max_telemetry_slots']=max(stats['max_telemetry_slots'],count)
            stats['max_total_rows']=max(stats['max_total_rows'],sum(result['rows'].values()))
            if policy=='event_priority':assert count<=1 and stats['max_total_rows']<=83
            return result

        def close(self):
            captured['metrics']=self.metrics();captured['remaining']=self.states()
            captured['audit']=[dict(session=s,seq=q,state=state,kind=kind,at_ms=t,initial=i,recovery=r) for s,q,state,kind,t,i,r in
                               self.db.execute('SELECT session,seq,state,kind,at_ms,initial_attempts,recovery_attempts FROM recovery_audit ORDER BY audit_seq')]
            super().close()

    original=previous.RecoverySender;previous.RecoverySender=ObservedSender
    try:result=previous.byte_replay(monitor,mode,seed,'bounded_recovery',duration)
    finally:previous.RecoverySender=original
    result['policy']=policy
    metrics=captured['metrics']
    result.update(input_sha256=input_digest.hexdigest(),generated_telemetry=sum(r['kind']==TELEMETRY for r in requests),
                  accepted_telemetry=sum(kind==TELEMETRY for kind in accepted.values()),
                  rejected_events_capacity=metrics.get('rejected_events_capacity',sum(not r['accepted'] and r['kind']==EVENT for r in requests)),
                  rejected_telemetry_capacity=metrics.get('rejected_telemetry_capacity',sum(not r['accepted'] and r['kind']==TELEMETRY for r in requests)),
                  telemetry_superseded=metrics.get('telemetry_superseded',0),
                  telemetry_evicted_for_event=metrics.get('telemetry_evicted_for_event',0),
                  expired_events=dispositions['expired_events'],expired_telemetry=dispositions['expired_telemetry'],
                  max_telemetry_slots=stats['max_telemetry_slots'],max_total_rows=stats['max_total_rows'])
    assert result['expired_events']+result['expired_telemetry']==result['expired_messages']
    if save_trace:
        dump('admission_example.json',dict(run_id=monitor.run_id,policy=policy,mode=mode,result=result,
                                          requests=requests,terminal_retained=captured['audit'],
                                          terminal_metrics=metrics))
    return result


def replay():
    parameters()
    for name in ['admission','storage']:
        a=json.loads((OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==sha(OUT/'frozen_parameters.json')
    baseline=previous.previous.parameters()['baseline'];rows=[];new=[]
    for filename in CFG['previous_datasets']:
        with (previous.OUT/filename).open(encoding='utf-8') as f:saved=[r for r in csv.DictReader(f) if r['policy']=='bounded_recovery']
        grouped=defaultdict(list)
        for r in saved:grouped[(r['scene'],float(r['sigma']),int(r['seed']))].append(r)
        for (scene,sigma,seed),conditions in grouped.items():
            _,_,_,monitor=collect(scene,scene in ['nan_pressure','counter_reset','drift_p0'],sigma,seed,baseline)
            for r in conditions:
                duration=int(r.get('outage_seconds',60))
                for policy in CFG['policies']:
                    value=byte_replay(monitor,r['mode'],seed,policy,duration,
                                      save_trace=(filename=='holdout_results.csv' and scene=='restriction_r90' and sigma==10 and seed==49001 and r['mode']=='ack_blackout' and policy=='event_priority'))
                    rows.append(dict(dataset=filename,scene=scene,sigma=sigma,seed=seed,outage_seconds=duration,**value))
    for sigma in CFG['new_sigmas']:
        for scene in CFG['new_scenes']:
            for seed in CFG['new_seeds']:
                _,_,_,monitor=collect(scene,scene=='nan_pressure',sigma,seed,baseline)
                for mode in CFG['new_modes']:
                    for policy in CFG['policies']:
                        new.append(dict(dataset='unused_seeds',scene=scene,sigma=sigma,seed=seed,outage_seconds=60,
                                        **byte_replay(monitor,mode,seed,policy)))
    write('paired_results.csv',rows);write('holdout_results.csv',new)
    dump('results_summary.json',dict(parameters_sha256=sha(OUT/'frozen_parameters.json'),physical_data=False,
                                    datasets={name:dict(rows=len(records),sha256=sha(OUT/name)) for name,records in
                                              [('paired_results.csv',rows),('holdout_results.csv',new)]},
                                    note='Matched generated snapshots and business requests; same synthetic model, not physical trials'))
    print('648 regression/paired and 96 previously unused-seed records generated; independent replay check pending.')


if __name__=='__main__':
    if '--freeze' in sys.argv:freeze()
    else:replay()
