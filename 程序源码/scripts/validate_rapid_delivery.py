"""Separate acceptance gates for attention and delivery work packages."""
from pathlib import Path
import csv,json,sys,tempfile
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'));sys.path.insert(0,str(ROOT/'prototype'))
import review_rapid_delivery as m
from rapid_review_runtime import rapid_review
from review_hybrid_sampling import residual
from reliable_outbox import Outbox,Receiver
OUT=m.OUT
def read(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def compare(saved,new):
    for k,v in new.items():
        if v is None:assert saved[k]==''
        elif isinstance(v,float):assert np.isclose(float(saved[k]),v,atol=1e-12)
        else:assert saved[k]==str(v),(k,saved[k],v)
def parameters():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'));assert p['config']==m.CFG
    for path,digest in p['sources'].items():assert m.sha(ROOT/path)==digest,path
    return p

def attention():
    p=parameters();s=json.loads((OUT/'attention_summary.json').read_text(encoding='utf-8'))
    assert s['parameters_sha256']==m.sha(OUT/'frozen_parameters.json')
    for path,digest in s['source_hashes'].items():assert m.sha(OUT/path)==digest
    ref=p['baseline']['reference'];limits=p['baseline']['limits']['1'];checked=0;oracle=causal=0
    for filename,quality in [('attention_results.csv',False),('quality_attention_results.csv',True)]:
        rr=read(filename);assert len(rr)==(576 if quality else 1920);groups={}
        for r in rr:groups.setdefault((float(r['sigma']),r['scene'],int(r['seed'])),[]).append(r)
        for (sigma,scene,seed),saved in groups.items():
            tr,obs,counts=m.inputs(scene,sigma,seed,quality);full=m.replay(obs,counts,ref,limits,1,0)
            outputs={f'rapid{w}':rapid_review(obs,counts,ref,full['context'],w) for w in [1,3]}
            events={name:out['events'] for name,out in outputs.items()}
            events.update({name:out['events'] for name,out in full['decisions'].items()})
            for r in saved:
                v=m.attention_metrics(events[r['method']],tr)
                if quality:v['baseline_accepted']=full['baseline_accepted']
                compare(r,v);checked+=1
            if seed==43000 and sigma==.3 and not quality:
                for w in [1,3]:
                    short=outputs[f'rapid{w}'];by={r['t']:r for r in short['records']}
                    for r in short['records']:
                        if r['valid']:
                            t=r['t'];q=60*(counts[t]-counts[t-w])/(540*w)
                            xx=residual(*obs[t-w+1:t+1,:2].mean(axis=0),q,ref,full['context']['gain'],full['context']['r0'])
                            assert np.allclose(xx,r['x'],atol=1e-12)
                    for e in short['events']:assert by[e['t_s']]['attention'] and by[e['t_s']-1]['attention']
                    future=obs.copy();future[371:,:2]=999.;fc=counts.copy();fc[371:]+=1000000
                    altered=rapid_review(future,fc,ref,full['context'],w)
                    assert [r for r in short['records'] if r['t']<=370]==[r for r in altered['records'] if r['t']<=370]
                    assert [e for e in short['events'] if e['t_s']<=370]==[e for e in altered['events'] if e['t_s']<=370]
                    oracle+=1;causal+=1
    m.dump('attention_acceptance.json',dict(status='passed_synthetic_attention',physical_data=False,rows_reproduced=checked,
        window_and_confirmation_cases=oracle,future_invariance_cases=causal,parameters_sha256=m.sha(OUT/'frozen_parameters.json'),
        validator_sha256=m.sha(Path(__file__)),exclusions=['confirmed fault identity','real sensor timing','field accuracy','energy']))
    print(f'Attention gate passed: {checked} records, {oracle} independent window/confirmation cases.')

def delivery():
    p=parameters();s=json.loads((OUT/'delivery_summary.json').read_text(encoding='utf-8'))
    assert s['parameters_sha256']==m.sha(OUT/'frozen_parameters.json')
    assert s['source_events_sha256']==m.sha(OUT/'delivery_source_events.json') and s['results_sha256']==m.sha(OUT/'delivery_results.csv')
    src=json.loads((OUT/'delivery_source_events.json').read_text(encoding='utf-8'));rr=read('delivery_results.csv');assert len(rr)==108
    for r in rr:
        v=m.link_replay(src['events'],src['last'],r['strategy'],r['mode'],int(r['seed']));compare(r,v)
        assert v['duplicate_event_rows']==0
    # Actual SQLite files, orderly restarts, lost ACK and conflicting packet/event identity.
    with tempfile.TemporaryDirectory(prefix='delivery_qa_',dir=ROOT/'tmp') as directory:
        sender_path=str(Path(directory)/'sender.sqlite');receiver_path=str(Path(directory)/'receiver.sqlite')
        sender=Outbox(sender_path);receiver=Receiver(receiver_path)
        event=dict(event_id='station1:1',t_s=150,kind='rapid_review')
        pid=sender.enqueue(dict(events=[event]),150,1);packet=sender.pick(150)
        assert receiver.accept(packet,151)==pid
        assert len(receiver.events())==1 and sender.count()==1  # ACK deliberately not delivered
        sender.close();receiver.close();sender=Outbox(sender_path);receiver=Receiver(receiver_path)
        repeated=sender.pick(152);assert repeated==packet
        assert receiver.accept(repeated,153)==pid and len(receiver.events())==1
        conflict=dict(packet_id=pid,payload=dict(events=[dict(event_id='station1:1',t_s=999,kind='rapid_review')]))
        try:receiver.accept(conflict,154);raise RuntimeError('Conflicting packet accepted')
        except ValueError:pass
        assert len(receiver.events())==1 and sender.count()==1
        conflict['packet_id']=pid+100
        try:receiver.accept(conflict,155);raise RuntimeError('Conflicting event accepted')
        except ValueError:pass
        assert receiver.db.execute('SELECT COUNT(*) FROM packets WHERE id=?',(pid+100,)).fetchone()[0]==0
        receiver.close();receiver=Receiver(receiver_path);assert len(receiver.events())==1
        sender.ack(pid);assert sender.count()==0
        new_pid=sender.enqueue(dict(events=[]),156);assert new_pid>pid
        sender.close();receiver.close()
    m.dump('delivery_acceptance.json',dict(status='passed_sqlite_and_synthetic_transport',physical_data=False,records_reproduced=len(rr),
        orderly_restart_test=True,lost_ack_dedup_test=True,conflicting_packet_and_event_rollback_test=True,
        ack_after_commit_checked_by_reopen=True,persistent_packet_sequence_checked=True,
        validator_sha256=m.sha(Path(__file__)),parameters_sha256=m.sha(OUT/'frozen_parameters.json'),
        exclusions=['real serial or radio','sudden power-loss durability','multiple sender ID namespaces','full sensor payload fragmentation','energy']))
    print('Delivery gate passed: 108 replays; SQLite restart, ACK loss, dedup and rollback checked.')

if __name__=='__main__':
    if '--delivery' in sys.argv:delivery()
    else:attention()
