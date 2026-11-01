"""Fifth round: frozen rapid attention and a separate synthetic link replay."""
from pathlib import Path
import csv,itertools,json,sys
import numpy as np
from review_quality_intervals import inputs,replay,sha
from rapid_review_runtime import rapid_review
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'prototype'))
from reliable_outbox import Outbox,Receiver
OUT=ROOT/'simulation/rapid_delivery_review';BASE=ROOT/'simulation/quality_interval_review/frozen_parameters.json'
SEEDS=list(range(43000,43016));SIGMAS=[.3,3.,10.]
SCENES=['normal','long_normal','supply_step','supply_ramp','leak_r90','leak_r720','pulse8','pulse20','pulse40','fast_leak_switch']
CFG=dict(version='20261006-rapid-delivery-v1',seeds=SEEDS,pressure_sigmas=SIGMAS,scenes=SCENES,windows=[1,3],
    fixed_pressure_acquisition_hz=1,short_confirmation_points=2,fast_scale_multiplier=6,
    rapid_output='attention_requires_review_not_confirmed_water_fault',quality_range_assumption=[0,200],
    allowed_initial_reference='externally_confirmed_healthy_plus_numeric_checks',
    link_modes=['clean','loss','outage'],link_seeds=list(range(44000,44012)),
    data_loss_probability=.2,ack_loss_probability=.25,outage=[180,210],retry_interval_s=2,
    send_cap_packets_per_second=1,flush_seconds=120,strategies=['periodic10','periodic60','event60'],
    payload_scope='event records and status timestamps; not full sensor payload',physical_data=False,energy_measured=False)

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def write(name,rr):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]),lineterminator='\n');w.writeheader();w.writerows(rr)

def attention_metrics(events,tr):
    fault=tr['target'] is not None;start=tr['fault_start'];end=tr['fault_end']
    pre=[e for e in events if e['t_s']<start] if fault else events
    after=[e for e in events if e['t_s']>=start] if fault else []
    hit=np.flatnonzero((tr['t']>=start)&(tr['severity']>=.15)) if fault else []
    critical=int(hit[0]) if len(hit) else None
    early=bool(fault and not pre and after and critical is not None and after[0]['t_s']<critical)
    during=[e for e in after if end is None or e['t_s']<end]
    return dict(false_attention=len(pre),during_fault_attention=bool(during),early_attention=early,
        first_post_s=after[0]['t_s'] if after else None,critical_s=critical,
        outcome='control' if not fault else 'prior_attention' if pre else 'none' if not after else 'after_recovery' if not during else 'early' if early else 'during_late')

def link_replay(events,last,strategy,mode,seed):
    outbox=Outbox();receiver=Receiver();rng=np.random.default_rng(seed);network=rng.random((last+121,2))
    by={}
    for event in events:by.setdefault(event['t_s'],[]).append(event)
    waiting=[];attempts=accepted=acknowledged=0
    interval=10 if strategy=='periodic10' else 60
    for t in range(130,last+121):
        fresh=by.get(t,[])
        if strategy=='event60':
            for e in fresh:outbox.enqueue(dict(events=[e]),t,priority=1)
        else:waiting.extend(fresh)
        if t<=last and (t-130)%interval==0:
            outbox.enqueue(dict(events=waiting.copy(),status_t_s=t),t,priority=bool(waiting));waiting=[]
        if t==last+1 and waiting:outbox.enqueue(dict(events=waiting.copy()),t,priority=1);waiting=[]
        packet=outbox.pick(t)
        if packet is None:continue
        attempts+=1;blocked=mode=='outage' and 180<=t<210
        if blocked or (mode=='loss' and network[t,0]<.2):continue
        ack=receiver.accept(packet,t);accepted+=1
        if mode=='loss' and network[t,1]<.25:continue
        outbox.ack(ack);acknowledged+=1
    got=receiver.events();lags=[x['received']-x['event']['t_s'] for x in got]
    result=dict(strategy=strategy,mode=mode,seed=seed,generated_events=len(events),unique_received_events=len(got),
        missing_events=len(events)-len(got),attempts=attempts,accepted_packets=accepted,acknowledged_packets=acknowledged,
        outstanding_packets=outbox.count(),median_delivery_lag_s=float(np.median(lags)) if lags else None,
        max_delivery_lag_s=max(lags) if lags else None,duplicate_event_rows=len(got)-len({x['event']['event_id'] for x in got}))
    outbox.close();receiver.close();return result

def freeze():
    OUT.mkdir(exist_ok=True);base=json.loads(BASE.read_text(encoding='utf-8'))
    dump('frozen_parameters.json',dict(config=CFG,baseline=base,sources={p.relative_to(ROOT).as_posix():sha(p) for p in
        [Path(__file__),ROOT/'simulation/rapid_review_runtime.py',ROOT/'prototype/reliable_outbox.py',BASE,
         ROOT/'simulation/review_quality_intervals.py',ROOT/'simulation/sampling_quality_runtime.py']}))
    print('Fifth-round protocol frozen before test.')

def main():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'));assert p['config']==CFG
    for path,digest in p['sources'].items():assert sha(ROOT/path)==digest,path
    locked=sha(OUT/'frozen_parameters.json');ref=p['baseline']['reference'];limits=p['baseline']['limits']['1']
    if '--delivery-only' in sys.argv:
        example=json.loads((OUT/'delivery_source_events.json').read_text(encoding='utf-8'))
        assert example['parameters_sha256']==locked
        links=[link_replay(example['events'],example['last'],strategy,mode,seed) for strategy,mode,seed in itertools.product(CFG['strategies'],CFG['link_modes'],CFG['link_seeds'])]
        write('delivery_results.csv',links)
        dump('delivery_summary.json',dict(physical_data=False,records=len(links),parameters_sha256=locked,
            source_events_sha256=sha(OUT/'delivery_source_events.json'),results_sha256=sha(OUT/'delivery_results.csv'),
            dependence='One fixed event stream; common random draws across strategies. Not independent physical link trials.'))
        print(f'Delivery {len(links)} records. Attention files unchanged.');return
    rr=[];quality=[];example={};source_events=None
    for sigma,scene,seed in itertools.product(SIGMAS,SCENES,SEEDS):
        tr,obs,counts=inputs(scene,sigma,seed);full=replay(obs,counts,ref,limits,1,0)
        for name,events in [(m,full['decisions'][m]['events']) for m in ['guarded_fast','hybrid']]+[(f'rapid{w}',rapid_review(obs,counts,ref,full['context'],w)['events']) for w in [1,3]]:
            rr.append(dict(sigma=sigma,scene=scene,seed=seed,method=name,**attention_metrics(events,tr)))
        if sigma==.3 and scene=='fast_leak_switch' and seed==SEEDS[0]:
            rapid=rapid_review(obs,counts,ref,full['context'],3)
            source_events=[dict(event_id=f'rapid3:{e["t_s"]}',t_s=e['t_s'],kind='rapid_review') for e in rapid['events']]
            source_events += [dict(event_id=f'guard:{e["t_s"]}',t_s=e['t_s'],kind=e['pattern']) for e in full['decisions']['guarded_fast']['events']]
            source_events.sort(key=lambda e:(e['t_s'],e['event_id']));example=dict(scene=scene,sigma=sigma,seed=seed,events=source_events,last=int(tr['t'][-1]),parameters_sha256=locked)
    for sigma,scene,seed in itertools.product(SIGMAS,['drift_p0','bias_p1','spike_range','nan_pressure','counter_reset','fault_initial'],SEEDS):
        tr,obs,counts=inputs(scene,sigma,seed,True);full=replay(obs,counts,ref,limits,1,0)
        for w in [1,3]:
            rapid=rapid_review(obs,counts,ref,full['context'],w)
            quality.append(dict(sigma=sigma,scene=scene,seed=seed,method=f'rapid{w}',baseline_accepted=full['baseline_accepted'],**attention_metrics(rapid['events'],tr)))
    write('attention_results.csv',rr);write('quality_attention_results.csv',quality);dump('delivery_source_events.json',example)
    groups=[]
    for sigma,scene,method in itertools.product(SIGMAS,SCENES,['guarded_fast','hybrid','rapid1','rapid3']):
        r=[x for x in rr if x['sigma']==sigma and x['scene']==scene and x['method']==method]
        groups.append(dict(sigma=sigma,scene=scene,method=method,trials=len(r),during=sum(x['during_fault_attention'] for x in r),
            early=sum(x['early_attention'] for x in r),false_trials=sum(x['false_attention']>0 for x in r),
            median_first_post_s=float(np.median([x['first_post_s'] for x in r if x['first_post_s'] is not None])) if any(x['first_post_s'] is not None for x in r) else None))
    assert locked==sha(OUT/'frozen_parameters.json')
    dump('attention_summary.json',dict(physical_data=False,attention_trajectories=480,attention_records=len(rr),quality_records=len(quality),
        parameters_sha256=locked,groups=groups,
        warning='All methods here compared as attention signals. rapid1/3 do not identify confirmed fault type.',
        dependence='Seeds reused across scenarios/sigma. Link replay uses one fixed source event stream and common random network draws.',
        source_hashes={name:sha(OUT/name) for name in ['attention_results.csv','quality_attention_results.csv','delivery_source_events.json']}))
    print(f'Attention {len(rr)}; quality {len(quality)} records. Delivery not run yet.')

if __name__=='__main__':
    if '--freeze' in sys.argv:freeze()
    else:main()
