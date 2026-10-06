"""Publish C-derived offline replay and run held-out scheduling challenges."""
from pathlib import Path
import csv,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'prototype'),str(ROOT/'simulation')]
from platform_service import *
from sampling_quality_runtime import SamplingNode
from review_quality_intervals import metrics
OUT=ROOT/'simulation/platform_upgrade'

def write(name,data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(clean(data),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def publish(manifest=None):
    if manifest is None:manifest=json.loads((OUT/'web_data.json').read_text(encoding='utf-8'))
    template=(ROOT/'scripts/workspace.template.html').read_text(encoding='utf-8')
    template=template.replace('__WORKSPACE_CONTRACT__',(ROOT/'application/config/workspace.json').read_text(encoding='utf-8'))
    css=(ROOT/'scripts/platform_upgrade.css').read_text(encoding='utf-8')+'\n'+(ROOT/'scripts/workspace.css').read_text(encoding='utf-8')
    js=(ROOT/'scripts/platform_upgrade.js').read_text(encoding='utf-8').replace('/* WORKSPACE_VIEWS */',(ROOT/'scripts/workspace_views.js').read_text(encoding='utf-8'))
    html=template.replace('__PLATFORM_DATA__',dump(manifest).replace('</','<\\/')).replace('__PLATFORM_CSS__',css).replace('__PLATFORM_JS__',js)
    (ROOT/'deliverables/index.html').write_text(html,encoding='utf-8',newline='\n')

def main():
    exe,digest=compile_bridge();traces={};checks=[]
    for sigma in (.3,3.,10.):
        p=reference_profile(sigma)
        for scene in SCENES:
            tr,obs,counts=observation_trace(scene,sigma)
            rows=[];events=[]
            with AcquisitionPipeline(p,exe,synthetic=True) as pipe:
                for t,count in enumerate(counts):
                    r,fresh=pipe.update(t,int(count),(t+1)*1000,pressure_reads(t,obs[t,:2]))
                    rows.append(display_snapshot(r['snapshot']))
                    for e in fresh:events.append(dict(id=f'{scene}:{sigma}:{t}:{e["code"]}',code=e['code'],label=EVENT_LABELS[e['code']],snapshot=rows[-1],stage='open',notes=[],transport='offline_C_replay_not_sent'))
            traces[f'{scene}_{sigma:g}']=dict(samples=rows,events=events,profile=p,calibration_seed=69001,monitoring_seed=70001)
            checks.append(dict(scene=scene,sigma=sigma,samples=len(rows),candidate_onsets=sum(e['code']>=4 for e in events),quality_onsets=sum(e['code']==2 for e in events)))
    # Sparse-pressure policy is a separate Python reference. Every point is
    # delivered only when pressure_due() requests it; no interpolated samples.
    baseline=json.loads((ROOT/'simulation/quality_interval_review/frozen_parameters.json').read_text(encoding='utf-8'))
    trials=[]
    for seed in (71001,71002,71003):
        for sigma in (.3,3.,10.):
            for scene in ('normal','supply','leak','restriction','pulse','drift'):
                tr,obs,counts=observation_trace(scene,sigma,seed)
                for period in (1,2,5):
                    for phase in range(period):
                        node=SamplingNode(baseline['reference'],baseline['limits'][str(period)],period,phase,'range')
                        for t,count in enumerate(counts):node.update(t,int(count),obs[t,:2] if node.pressure_due(t) else None)
                        out=node.output();m=metrics(out,tr,'guarded_fast')
                        trials.append(dict(seed=seed,sigma=sigma,scene=scene,period=period,phase=phase,pressure_reads=len(node.acquired),**m))
    summaries=[]
    for scene in ('normal','supply','leak','restriction','pulse','drift'):
        for period in (1,2,5):
            rr=[r for r in trials if r['scene']==scene and r['period']==period]
            summaries.append(dict(scene=scene,period=period,trials=len(rr),early_valid=sum(bool(r['early_valid']) for r in rr),
                                  false_onsets=sum(r.get('false_onsets',0) for r in rr),pressure_reads_mean=sum(r['pressure_reads'] for r in rr)/len(rr),
                                  outcomes={v:sum(r['outcome']==v for r in rr) for v in sorted(set(r['outcome'] for r in rr))}))
    cross=OUT/'cross_operating_summary.json'
    manifest=dict(version=VERSION,physical_data=False,energy_measured=False,c_sha256=digest,
                  classification='independent_seed_same_uncalibrated_model_not_field_generalization',
                  c_calibration_seed=69001,c_replay_seed=70001,scheduling_test_seeds=[71001,71002,71003],
                  algorithm='frozen robust residual; main 10s/5 confirmations; rapid 3s/2 attention',
                  sparse_runtime='separate Python policy; not C firmware',traces=traces,research=summaries,
                  cross_operating=json.loads(cross.read_text(encoding='utf-8')) if cross.exists() else [])
    write('web_data.json',manifest);write('replay_checks.json',checks);write('scheduling_trials.json',trials)
    with (OUT/'scheduling_trials.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trials[0]),lineterminator='\n');w.writeheader();w.writerows(trials)
    print(f'C replay: {len(traces)} traces; scheduling: {len(trials)} trials')
    publish(manifest)
if __name__=='__main__':main()
