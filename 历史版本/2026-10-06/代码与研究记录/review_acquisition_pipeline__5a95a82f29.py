"""Final host-only acquisition/C/wire integration, with frozen earlier methods."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
from dataclasses import asdict
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from acquisition_pipeline import AcquisitionPipeline,SessionResetRequired
from acquisition_timing import PressureRead
from compact_protocol import Frame,Snapshot,StreamDecoder,decode,EVENT,TELEMETRY,MISSING
from admission_transport import AdmissionSender
from session_transport import SessionReceiver
from integer_diagnosis_reference import IntegerOracle,FIELDS
import review_integer_diagnosis as previous
OUT=ROOT/'simulation/acquisition_pipeline_review'
EXE=ROOT/'tmp/acquisition_pipeline/bridge.exe'
CFG=dict(version='20261006-acquisition-closeout-v1',physical_data=False,
         input_period_ms=1000,pressure_span_ms=30,counter_tolerance_ms=1,
         configuration_id=11,reference_id=1,monitor_start=130,
         telemetry_period_s=60,modes=['clean','loss','outage60','ack_blackout'],
         channel_seed=52000,link_scenes=['normal','pulse8','restriction_r90','nan_pressure'],
         link_sigmas=[.3,10.],link_seed=51000,live_capacity=16,history_capacity=64,
         tune_on_results=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def freeze():
    previous.parameters()
    sources=[Path(__file__),ROOT/'prototype/acquisition_pipeline.py',ROOT/'firmware/acquisition_bridge.c',
             ROOT/'scripts/validate_acquisition_pipeline.py',ROOT/'simulation/acquisition_timing.py',
             ROOT/'prototype/compact_protocol.py',ROOT/'prototype/session_transport.py',
             previous.OUT/'frozen_parameters.json',previous.OUT/'profiles.json']
    dump('frozen_parameters.json',dict(config=CFG,sources={p.relative_to(ROOT).as_posix():sha(p) for p in sources}))
def parameters():
    previous.parameters();p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    assert p['config']==CFG
    for file,digest in p['sources'].items():assert sha(ROOT/file)==digest,file
    return p
def compile_bridge():
    EXE.parent.mkdir(parents=True,exist_ok=True)
    args=['D:/bin/gcc.exe','-std=c11','-Wall','-Wextra','-Werror','-Wconversion','-O2','-ftrapv',
          str(ROOT/'firmware/integer_diagnosis.c'),str(ROOT/'firmware/acquisition_bridge.c'),'-o',str(EXE)]
    r=subprocess.run(args,capture_output=True,text=True,check=True)
    assert not r.stderr;return args
def reads(t,p0=120.,p1=100.):
    end=(t+1)*1000
    return [PressureRead(end-28,end-19,float(p0)),PressureRead(end-18,end-9,float(p1))]
def fixture_profile():
    return dict(numeric=1,approved=1,rapid_available=1,r0=555556,
                main=[60000,600000],rapid=[60000,600000],lut=[6000000]*381)
def serial(record):
    return dict(sample_index=record['sample_index'],snapshot=asdict(record['snapshot']),fields=record['fields'],
                issue=record['issue'],counter_endpoint_trusted=record['counter_endpoint_trusted'],
                counter_value_is_held=record['counter_value_is_held'],raw_cumulative_pulses=record['raw_cumulative_pulses'],
                timing=record['timing'],events=record['events'])
def fixed_trace(fault):
    with AcquisitionPipeline(fixture_profile(),EXE) as p:
        for t in range(446):
            rr=reads(t);latch=(t+1)*1000
            if t==420:
                a,b=rr;end=(t+1)*1000
                if fault=='nonfinite':rr=[PressureRead(a.started_ms,a.completed_ms,float('nan')),b]
                elif fault=='range':rr=reads(t,-.001,100)
                elif fault=='not_ready':rr=[PressureRead(a.started_ms,a.completed_ms,120,False),b]
                elif fault in ('stale','repeated'):rr=[PressureRead(end-1028,end-1019,120),b]
                elif fault=='overlap':rr=[a,PressureRead(a.completed_ms-1,b.completed_ms,100)]
                elif fault=='future':rr=[a,PressureRead(b.started_ms,end+1,100)]
                elif fault=='span':rr=[PressureRead(end-31,a.completed_ms,120),b]
                elif fault=='late_counter':latch=end+2
                elif fault=='nan_latch':latch=float('nan')
                elif fault=='counter_reset':pass
            count=54*(t+1) if fault!='counter_reset' or t<420 else 54*(t-420)
            p.update(t,count,latch,rr)
        return p.records
def replay_link(records,profile,mode,seed=52000):
    source={r['sample_index']:r for r in records if r['sample_index']>=130}
    sender=AdmissionSender(':memory:');receiver=SessionReceiver(':memory:')
    rng=np.random.default_rng(seed);accepted={};requested=0;rejected=0;maxlive=maxrows=maxtm=0;sent=0;seen=set()
    receiver.register(1,11,1 if profile['numeric'] else 0,dict(synthetic=True,healthy_reference_approved=bool(profile['approved'])))
    receiver.register_time_mapping(1,sender.session,0,0,'Shared clock of host replay only')
    last=max(source)
    try:
        for t in range(130,last+311):
            now=(t+1)*1000
            if t in source:
                r=source[t];snap=r['snapshot'];payload=snap.pack();sender.set_snapshot(payload,now)
                for e in r['events']:
                    requested+=1;f=sender.enqueue(EVENT,payload+bytes([e['code'],e['detail']]),now)
                    if f:accepted[f.key]=f
                    else:rejected+=1
                if t%60==0 or t==last:
                    f=sender.enqueue(TELEMETRY,payload,now)
                    if f:accepted[f.key]=f
            wire=sender.pick(now)
            if wire:
                f=decode(wire);sent+=1;assert len(wire)<=64
                if f.key in accepted:assert f.body==accepted[f.key].body
                uplink=not(mode=='outage60' and 400<=t<460) and (mode!='loss' or rng.random()>=.2)
                if uplink:
                    ack=receiver.accept(wire,now)
                    stored=receiver.db.execute('SELECT body FROM frames WHERE device=? AND session=? AND seq=?',f.key).fetchone()
                    assert stored and stored[0]==f.body and not receiver.db.in_transaction
                    seen.add(f.key)
                    if mode!='ack_blackout' and (mode!='loss' or rng.random()>=.2):assert sender.acknowledge(ack,now)
            storage=sender.storage();live=storage['rows']['recovery_live'];total=sum(storage['rows'].values())
            tm=sender.db.execute('SELECT count(*) FROM recovery_live WHERE kind=?',(TELEMETRY,)).fetchone()[0]
            maxlive=max(maxlive,live);maxrows=max(maxrows,total);maxtm=max(maxtm,tm)
            assert live<=16 and total<=83 and tm<=1
            assert not sender.db.execute('SELECT 1 FROM recovery_live WHERE initial_attempts>8 OR recovery_attempts>4').fetchone()
        received_events=sum(f.kind==EVENT and k in seen for k,f in accepted.items())
        accepted_events=sum(f.kind==EVENT for f in accepted.values())
        if mode=='clean':assert received_events==requested and rejected==0
        metrics=sender.metrics()
        return dict(mode=mode,generated_events=requested,accepted_events=accepted_events,received_events=received_events,
                    rejected_events=rejected,missing_accepted_events=accepted_events-received_events,
                    source_expired_events=metrics['expired_events'],dispatched_frames=sent,max_live=maxlive,
                    max_total_rows=maxrows,max_telemetry=maxtm,all_stored_bodies_verified=True)
    finally:sender.close();receiver.close()
def evaluate():
    parameters();compile_bridge()
    profiles=json.loads((previous.OUT/'profiles.json').read_text(encoding='utf-8'))
    base=previous.previous.previous.previous.parameters()['baseline'];rows=[];links=[];examples={}
    for i,item in enumerate(profiles):
        scene=item['scene'];sigma=item['sigma'];seed=item['seed'];c=item['config']
        quality=dict(previous.CASES)[scene]
        _,obs,counts,_=previous.collect(scene,quality,sigma,seed,base)
        oracle=IntegerOracle(c);events=0;different=0;wire_count=0
        with AcquisitionPipeline(c,EXE) as p:
            for t,count in enumerate(counts):
                expected=oracle.update(*previous.integer_input(t,count,obs[t,:2]))
                r,fresh=p.update(t,int(count),(t+1)*1000,reads(t,*obs[t,:2]))
                actual=[r['fields'][key] for key in FIELDS];different+=actual!=expected
                for kind,payload in [(TELEMETRY,r['snapshot'].pack())]+[(EVENT,e['payload']) for e in fresh]:
                    frame=Frame(kind,1,1,wire_count+1,payload);wire=frame.wire();parser=StreamDecoder()
                    decoded=parser.feed(wire[:7])+parser.feed(wire[7:]);assert decoded==[frame] and parser.errors==0
                    wire_count+=1
                events+=len(fresh)
            assert different==0,(scene,sigma,seed,different)
            rows.append(dict(dataset=item['dataset'],scene=scene,sigma=sigma,seed=seed,
                             updates=len(counts),monitored_updates=len(counts)-130,field_differences=different,
                             events=events,validated_wire_frames=wire_count))
            if seed==CFG['link_seed'] and scene in CFG['link_scenes'] and sigma in CFG['link_sigmas']:
                for mode in CFG['modes']:links.append(dict(scene=scene,sigma=sigma,seed=seed,**replay_link(p.records,c,mode)))
        if i%36==35:print(f'{i+1}/216 acquisition trajectories verified',flush=True)
    for name in ['none','nonfinite','range','not_ready','stale','repeated','overlap','future','span','late_counter','nan_latch','counter_reset']:
        records=fixed_trace(name);examples[name]=[serial(r) for r in records[418:434]]
        for mode in CFG['modes']:links.append(dict(scene='fault_'+name,sigma=0,seed=0,**replay_link(records,fixture_profile(),mode)))
    write('results.csv',rows);write('link_results.csv',links);dump('fault_examples.json',examples)
    dump('results_summary.json',dict(physical_data=False,parameters_sha256=sha(OUT/'frozen_parameters.json'),
         runs=len(rows),updates=sum(r['updates'] for r in rows),monitored_updates=sum(r['monitored_updates'] for r in rows),
         field_differences=sum(r['field_differences'] for r in rows),wire_frames=sum(r['validated_wire_frames'] for r in rows),
         link_runs=len(links),clean_link_runs=sum(r['mode']=='clean' for r in links),
         datasets={n:sha(OUT/n) for n in ['results.csv','link_results.csv','fault_examples.json']}))
    print('Replay complete; separate acceptance required.',flush=True)
if __name__=='__main__':
    if '--freeze' in sys.argv:freeze()
    else:evaluate()
