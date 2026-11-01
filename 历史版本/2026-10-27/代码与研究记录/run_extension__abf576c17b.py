"""Additional physical amplitudes, measured-window waveforms, and sampling cost."""
from pathlib import Path
import sys,json,csv,itertools,hashlib,time
import numpy as np
B=Path(__file__).resolve().parents[1];E=B/'evidence'
sys.path.insert(0,str(B/'code/snapshot'))
import review_operating_reference as o
import review_hybrid_sampling as h
from sampling_quality_runtime import SamplingNode
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=json.loads((E/'frozen_parameters.json').read_text(encoding='utf-8'))
SP=json.loads((E/'sampling_frozen_parameters.json').read_text(encoding='utf-8'))
REF=P['baseline']['references']['n0.5']
SEEDS=list(range(62000,62100));SSEEDS=list(range(63000,63016))
METHOD='guarded_fast';SIGMAS=[.3,3.,10.];AMPLITUDES=[.05,.1,.15,.2,.3]
def write(name,rows):
    with (E/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ci(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den
    r=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,mid-r),min(1.,mid+r)]
def amplitude_trace(scene,amp):
    tr=o.trajectory(scene,.5);base=float(o.plant(120,.5,False)[0,2])
    target=base*(1+amp if scene=='leak' else 1-amp)
    lo,hi=(0.,2.) if scene=='leak' else (.8,200.)
    for _ in range(65):
        mid=(lo+hi)/2
        q=float(o.plant(120,.5,False,leak_c=mid)[0,2]) if scene=='leak' else float(o.plant(120,.5,False,r=mid)[0,2])
        if (q<target if scene=='leak' else q>target):lo=mid
        else:hi=mid
    end=(lo+hi)/2;t=tr['t'];ramp=np.clip((t-360)/180,0,1)
    r=.8+((end-.8)*ramp if scene=='restriction' else np.zeros(len(t)))
    c=end*ramp if scene=='leak' else np.zeros(len(t))
    tr['values']=o.plant(tr['supply'],.5,tr['b'],r,c)
    tr['severity']=abs(tr['values'][:,2]/tr['healthy_q']-1)
    assert abs(tr['severity'][-1]-amp)<1e-12
    return tr,end

def main():
    tick=time.time();locked=[sha(E/n) for n in ['frozen_parameters.json','sampling_frozen_parameters.json']]
    training=set(P['config']['training_seeds'])|set(P['baseline']['config']['reference_seeds'])|set(P['baseline']['config']['limit_seeds'])|set(SP['config']['training_seeds'])
    assert not training.intersection(SEEDS+SSEEDS)
    arrays={};rows=[];pars=[];balance=0.
    # 100 matched noise realizations per waveform scenario, causal ten-second estimates.
    for scene in ['normal','leak','restriction']:
        tr=o.trajectory(scene,.5);p1=[];flow=[]
        for seed in SEEDS:
            obs=o.observe(tr,3.,seed,scene);p=np.array([obs[max(0,t-9):t+1,1].mean() for t in tr['t']])
            p1.append(p);flow.append(h.pulse_frontend(obs,seed)['q10'])
        arrays[scene+'_p1']=np.array(p1);arrays[scene+'_q10']=np.array(flow)
        arrays[scene+'_true']=tr['values']
    print('Waveforms: 300 trajectories',flush=True)
    controls=[]
    tr=o.trajectory('normal',.5)
    for sigma,seed in itertools.product(SIGMAS,SEEDS):
        obs=o.observe(tr,sigma,seed,'normal')
        replay=h.sensor_replay(obs,seed,REF,'fixed',P['h_bounded_sensor']['fixed'])
        events=replay['decisions'][METHOD]['events']
        controls.append(dict(sigma=sigma,seed=seed,any_false=bool(events),
            post360_false=any(e['t_s']>=360 for e in events),onsets=len(events)))
    write('amplitude_healthy_controls.csv',controls)
    # Correct first-pattern detection by 600 s; explicitly not the 15%-early metric.
    for scene,amp in itertools.product(['leak','restriction'],AMPLITUDES):
        tr,end=amplitude_trace(scene,amp);p0,p1,q=tr['values'].T
        qb=np.where(tr['b'],.35/np.sqrt(1+.8*.35**2)*np.sqrt(p0),0.)
        balance=max(balance,float(abs(tr['supply']-p0-.4*(q+qb)**2).max()))
        pars.append(dict(scene=scene,target_amplitude=amp,terminal_parameter=end,
                         terminal_flow_l_min=float(q[-1]),realized_amplitude=float(tr['severity'][-1])))
        for sigma in SIGMAS:
            for seed in SEEDS:
                obs=o.observe(tr,sigma,seed,scene)
                replay=h.sensor_replay(obs,seed,REF,'fixed',P['h_bounded_sensor']['fixed'])
                events=replay['decisions'][METHOD]['events']
                before=[e for e in events if e['t_s']<360];after=[e for e in events if e['t_s']>=360]
                correct=bool(not before and after and after[0]['pattern']==tr['target'])
                reason='prior_false' if before else 'no_confirmation' if not after else 'correct' if correct else 'wrong_first'
                rows.append(dict(scene=scene,amplitude=amp,sigma=sigma,seed=seed,correct=correct,outcome=reason,
                    first_post_s=after[0]['t_s'] if after else None,first_pattern=after[0]['pattern'] if after else None))
            print(f'Amplitude {scene} {amp:g}, sigma={sigma:g}: {time.time()-tick:.1f}s',flush=True)
    write('amplitude_trials.csv',rows);write('amplitude_parameters.csv',pars)
    groups=[]
    for scene,sigma,amp in itertools.product(['leak','restriction'],SIGMAS,AMPLITUDES):
        rr=[r for r in rows if (r['scene'],r['sigma'],r['amplitude'])==(scene,sigma,amp)];k=sum(r['correct'] for r in rr)
        groups.append(dict(scene=scene,sigma=sigma,amplitude=amp,n=len(rr),correct=k,ci95=ci(k,len(rr)),
            outcomes={key:sum(r['outcome']==key for r in rr) for key in sorted({r['outcome'] for r in rr})}))
    # Actual requested pressure reads enter the scheduling runtime; no imputation.
    sampling=[]
    for scene,seed in itertools.product(['leak','fast_leak_switch'],SSEEDS):
        tr=o.trajectory(scene,.5);obs=o.observe(tr,3.,seed,scene);counts=h.pulse_frontend(obs,seed)['cumulative']
        for period in [1,2,5]:
            for phase in range(period):
                node=SamplingNode(SP['reference'],SP['limits'][str(period)],period,phase,'range')
                for t,count in enumerate(counts):node.update(t,int(count),obs[t,:2] if node.pressure_due(t) else None)
                out=node.output();events=out['decisions'][METHOD]['events'];start=tr['fault_start']
                before=[e for e in events if e['t_s']<start];after=[e for e in events if e['t_s']>=start]
                hits=np.flatnonzero(tr['severity']>=.15);crit=int(hits[0]) if len(hits) else None
                early=bool(not before and after and after[0]['pattern']==tr['target'] and crit is not None and after[0]['t_s']<crit)
                sampling.append(dict(scene=scene,seed=seed,period=period,phase=phase,early=early,
                    pressure_reads=sum(t>=130 for t in out['acquired']),eligible_windows=sum(r['valid'] for r in out['records']),
                    first_post_s=after[0]['t_s'] if after else None,critical_s=crit))
    write('sampling_extension_trials.csv',sampling)
    sg=[]
    for scene,period in itertools.product(['leak','fast_leak_switch'],[1,2,5]):
        rr=[r for r in sampling if r['scene']==scene and r['period']==period]
        phase_rates=[np.mean([r['early'] for r in rr if r['phase']==phase])*100 for phase in range(period)]
        # Average phases within each seed before describing noise-seed variation.
        perseed=[np.mean([r['pressure_reads'] for r in rr if r['seed']==seed]) for seed in SSEEDS]
        leads=[np.mean([r['critical_s']-r['first_post_s'] for r in rr if r['seed']==seed and r['early']]) for seed in SSEEDS]
        sg.append(dict(scene=scene,period=period,unique_seeds=16,replays=len(rr),early_percent=float(np.mean(phase_rates)),
            early_phase_range=[float(min(phase_rates)),float(max(phase_rates))],phase_rates=phase_rates,
            pressure_reads_median=float(np.median(perseed)),pressure_reads_iqr=np.quantile(perseed,[.25,.75]).tolist(),
            lead_median_s=float(np.median(leads)),lead_iqr_s=np.quantile(leads,[.25,.75]).tolist()))
    # Fix the first original holdout seed; retain every confirmation outcome.
    timing=[]
    for scene in ['leak','restriction']:
        tr=o.trajectory(scene,.5);obs=o.observe(tr,3.,61000,scene)
        replay=h.sensor_replay(obs,61000,REF,'fixed',P['h_bounded_sensor']['fixed'])
        arrays['timing_'+scene+'_severity']=tr['severity']
        for method in h.SENSOR_METHODS:
            timing.append(dict(scene=scene,method=method,seed=61000,sigma=3.,**h.sensor_evaluate(replay,tr,method)))
    write('timing_examples.csv',timing);np.savez_compressed(E/'extension_curves.npz',**arrays)
    assert len(rows)==3000 and len(sampling)==256 and balance<1e-9
    assert locked==[sha(E/n) for n in ['frozen_parameters.json','sampling_frozen_parameters.json']]
    report=dict(physical_data=False,new_waveform_trajectories=300,new_amplitude_trajectories=3000,amplitude_healthy_control_trajectories=300,
        new_sampling_observation_trajectories=32,sampling_phase_replays=256,timing_replayed_trajectories=2,
        amplitude_seeds=SEEDS,sampling_seeds=SSEEDS,training_seed_overlap=False,parameters_retuned=False,
        amplitude_metric='No pre-fault alarm; first post-fault pattern correct by t=600. Not 15%-early detection.',
        amplitude_ramp_s=180,amplitude_fault_start_s=360,amplitude_max_balance_residual_kpa=balance,
        amplitude_groups=groups,sampling_groups=sg,
        amplitude_healthy_controls=[dict(sigma=sigma,n=100,false_trials=sum(r['any_false'] for r in controls if r['sigma']==sigma),
            post360_false_trials=sum(r['post360_false'] for r in controls if r['sigma']==sigma)) for sigma in SIGMAS],
        dependencies='Same seeds paired across amplitudes, scenes, sigma. Waveform seeds reused for amplitudes. Sampling phases share identical observation traces; never pool as independent seeds.',
        sampling_metric='15%-early rule; phase range, not independent-repeat confidence intervals. Read counts are not energy measurements.',
        seconds=round(time.time()-tick,2),source_sha256={p.name:sha(p) for p in (B/'code/snapshot').glob('*.py')})
    (E/'extension_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print('COMPLETE '+json.dumps({k:report[k] for k in ['new_amplitude_trajectories','sampling_phase_replays','seconds']}),flush=True)

if __name__=='__main__':main()
