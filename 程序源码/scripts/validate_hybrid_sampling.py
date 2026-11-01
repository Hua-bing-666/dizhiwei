"""Reproduce frozen comparisons and challenge acquisition observability."""
from pathlib import Path
import csv, itertools, json, sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
import review_hybrid_sampling as m
OUT=m.OUT

def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def compare(saved,actual):
    for k,v in actual.items():
        if v is None:assert saved[k]==''
        elif isinstance(v,float):assert np.isclose(float(saved[k]),v,rtol=1e-11,atol=1e-11),(k,saved[k],v)
        else:assert saved[k]==str(v),(k,saved[k],v)

def main():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    assert p['config']==m.CFG
    assert summary['parameters_sha256']==m.sha(OUT/'frozen_parameters.json')
    for name,digest in p['sources'].items():assert m.sha(ROOT/name)==digest,name
    for name,digest in summary['source_hashes'].items():assert m.sha(OUT/name)==digest,name
    assert not set(m.TRAIN)&set(m.TEST) and not set(m.TRAIN)&set(m.SENSOR_TEST)
    assert not set(m.TEST)&set(m.SENSOR_TEST)
    assert not (set(m.TRAIN)|set(m.TEST)|set(m.SENSOR_TEST)) & set(range(23000,23012))
    training=rows('fusion_healthy_training.csv');st=rows('sensor_healthy_training.csv')
    assert len(training)==576 and len(st)==288
    for rr in [training,st]:
        assert {r['scene'] for r in rr}=={'normal','supply_step','supply_up','supply_ramp'}
        assert {int(r['seed']) for r in rr}==set(m.TRAIN)
    for k,key in enumerate(['q','r']):
        assert p['h_bounded_gaussian'][k]==max(5.,1.1*max(float(r[f'peak_{key}']) for r in training))
        for profile in ['fixed','adaptive']:
            assert p['h_bounded_sensor'][profile][k]==max(5.,1.1*max(float(r[f'peak_{key}']) for r in st if r['profile']==profile))
    # Recompute every healthy training maximum, beyond just checking CSV hashes.
    for r in training:
        ex=float(r['exponent']);sigma=float(r['sigma']);seed=int(r['seed']);scene=r['scene']
        tr=m.trajectory(scene,ex);obs=m.observe(tr,sigma,seed,scene)
        f=m.features(obs,p['baseline']['references'][f'n{ex:g}']);score=m.bounded_scores(f)
        compare(r,dict(peak_q=float(score[130:,0].max()),peak_r=float(score[130:,1].max())))
    for r in st:
        sigma=float(r['sigma']);seed=int(r['seed']);scene=r['scene'];profile=r['profile']
        tr=m.trajectory(scene,.5);obs=m.observe(tr,sigma,seed,scene)
        replay=m.sensor_replay(obs,seed,p['baseline']['references']['n0.5'],profile)
        score=np.array([rec['bounded'] for rec in replay['records']])
        compare(r,dict(peak_q=float(score[:,0].max()),peak_r=float(score[:,1].max()),eligible_frames=sum(rec['valid'] for rec in replay['records'])))
    # Independent O(window) oracle; randomized gaps reset every statistic.
    rng=np.random.default_rng(30001);stat=m.BoundedEvidence();history=[]
    for i in range(2000):
        if i%137==0:stat.reset();history=[]
        z=rng.normal([.7,.3],[2.,3.]);history.append(z-.5)
        reverse=np.cumsum(np.array(history[-60:])[::-1],axis=0)
        expected=np.maximum(0,reverse.max(axis=0))
        assert np.allclose(stat.update(z),expected,atol=1e-10)
    print('Frozen hashes, healthy-only limits and bounded-suffix arithmetic passed.',flush=True)
    cache={(ex,sc):m.trajectory(sc,ex) for ex in m.EXPONENTS for sc in m.SCENES}
    fusion=rows('fusion_results.csv');sensor=rows('sensor_results.csv');phase=rows('wake_phase_results.csv')
    assert (len(fusion),len(sensor),len(phase))==(20160,2592,540)
    lookup={(float(r['exponent']),float(r['sigma']),r['scene'],int(r['seed']),r['method']):r for r in fusion}
    assert len(lookup)==len(fusion)
    checked=0
    for ex,sigma,scene,seed in itertools.product(m.EXPONENTS,m.SIGMAS,m.SCENES,m.TEST):
        tr=cache[ex,scene];obs=m.observe(tr,sigma,seed,scene)
        f=m.features(obs,p['baseline']['references'][f'n{ex:g}']);bs=m.bounded_scores(f)
        for method in m.FUSIONS:
            compare(lookup[ex,sigma,scene,seed,method],m.evaluate(m.fusion_decision(f,bs,p,method),tr,f,'reference'));checked+=1
    print(f'{checked} fusion records reproduced.',flush=True)
    sl={(float(r['sigma']),r['scene'],int(r['seed']),r['profile'],r['method']):r for r in sensor}
    pl={(float(r['sigma']),int(r['seed']),int(r['phase']),r['method']):r for r in phase}
    assert len(sl)==len(sensor) and len(pl)==len(phase)
    ref=p['baseline']['references']['n0.5'];coverage=[];scount=pcount=0
    for sigma,scene,seed in itertools.product(m.SIGMAS,m.SCENES,m.SENSOR_TEST):
        tr=cache[.5,scene];obs=m.observe(tr,sigma,seed,scene)
        pulses=m.pulse_frontend(obs,seed)
        assert np.all(np.diff(pulses['cumulative'])>=0)
        for t in [9,10,129,180,len(obs)-1]:
            start=max(-1,t-10);prior=pulses['cumulative'][start] if start>=0 else 0
            assert pulses['q10'][t]==60*(pulses['cumulative'][t]-prior)/(540*(t-start))
        for profile in ['fixed','adaptive']:
            replay=m.sensor_replay(obs,seed,ref,profile,p['h_bounded_sensor'][profile])
            acq=set(replay['acquired']);c=replay['context'];last=-1;history=[]
            for rec in replay['records']:
                t=rec['t'];assert t in acq and rec['flow_q10']==pulses['q10'][t]
                ready=all(j in acq for j in range(t-9,t+1));assert ready==rec['ready']
                if not rec['valid']:
                    assert rec['bounded']==[0.,0.];history=[]
                else:
                    assert ready
                    x=m.residual(*obs[t-9:t+1,:2].mean(axis=0),pulses['q10'][t],ref,c['gain'],c['r0'])
                    assert np.allclose(rec['x'],x,atol=1e-12)
                    if t!=last+1:history=[]
                    history.append(x/np.array(c['scale'])-.5)
                    expected=np.maximum(0,np.cumsum(np.array(history[-60:])[::-1],axis=0).max(axis=0))
                    assert np.allclose(rec['bounded'],expected,atol=1e-9)
                last=t
            for method in m.SENSOR_METHODS:
                compare(sl[sigma,scene,seed,profile,method],m.sensor_evaluate(replay,tr,method));scount+=1
                labels=dict(zip([r['t'] for r in replay['records']],replay['decisions'][method]['labels']))
                for event in replay['decisions'][method]['events']:
                    t=event['t_s'];label={'leak_pattern':1,'restriction_pattern':2,'uncertain':3}[event['pattern']]
                    assert all(labels.get(j)==label for j in range(t-4,t+1))
            coverage.append(dict(sigma=sigma,scene=scene,seed=seed,profile=profile,
                monitoring_lattice_points=len(obs)-130,actual_pressure_frames=sum(t>=130 for t in acq),
                eligible_diagnostic_frames=sum(r['valid'] for r in replay['records']),
                unavailable_lattice_points=len(obs)-130-sum(r['valid'] for r in replay['records'])))
        if scene=='fast_leak_switch':
            for ph in range(5):
                replay=m.sensor_replay(obs,seed,ref,'adaptive',p['h_bounded_sensor']['adaptive'],ph)
                for method in m.SENSOR_METHODS:
                    compare(pl[sigma,seed,ph,method],m.sensor_evaluate(replay,tr,method));pcount+=1
    print(f'{scount} sensor and {pcount} phase records reproduced; windows independently checked.',flush=True)
    # Future samples cannot influence decisions already emitted. Initial calibration ends before every cut.
    invariants=0
    for scene,sigma in itertools.product(['normal','leak','fast_leak_switch'],[.3,10.]):
        obs=m.observe(cache[.5,scene],sigma,28000,scene)
        original=m.sensor_replay(obs,28000,ref,'adaptive',p['h_bounded_sensor']['adaptive'])
        hidden=obs.copy();unread=sorted(set(range(len(obs)))-set(original['acquired']))
        hidden[unread,:2]=999.
        altered=m.sensor_replay(hidden,28000,ref,'adaptive',p['h_bounded_sensor']['adaptive'])
        assert original==altered  # continuous Q counter remains allowed, unacquired pressures do not
        cut=185;future=obs.copy();future[cut+1:]=999.
        future_r=m.sensor_replay(future,28000,ref,'adaptive',p['h_bounded_sensor']['adaptive'])
        for key in ['acquired','triggers']:assert [t for t in original[key] if t<=cut]==[t for t in future_r[key] if t<=cut]
        assert [r for r in original['records'] if r['t']<=cut]==[r for r in future_r['records'] if r['t']<=cut]
        for method in m.SENSOR_METHODS:
            assert [e for e in original['decisions'][method]['events'] if e['t_s']<=cut]==[e for e in future_r['decisions'][method]['events'] if e['t_s']<=cut]
        invariants+=1
    leak=m.observe(cache[.5,'leak'],.3,28000,'leak');unknown=m.observe(cache[.5,'load_unknown'],.3,28000,'load_unknown')
    assert np.array_equal(leak,unknown)
    # A fixed-rate prefix checks fusion causality as well, without using the truth labels.
    f=m.features(leak,ref);altered=leak.copy();altered[401:]=999.;ff=m.features(altered,ref)
    bs=m.bounded_scores(f);bb=m.bounded_scores(ff)
    for method in m.FUSIONS:assert np.array_equal(m.fusion_decision(f,bs,p,method)['state'][:401],m.fusion_decision(ff,bb,p,method)['state'][:401])
    m.write_csv('diagnostic_coverage.csv',coverage)
    m.dump('acceptance.json',dict(status='passed_for_synthetic_replay',physical_validation=False,
        fusion_records_reproduced=checked,sensor_records_reproduced=scount,phase_records_reproduced=pcount,
        fusion_healthy_training_rows_reproduced=len(training),sensor_healthy_training_rows_reproduced=len(st),
        randomized_bounded_oracle_updates=2000,causal_and_unread_pressure_cases=invariants,
        pulse_window_checked=True,pressure_windows_and_confirmation_independently_checked=True,
        unknown_load_ambiguity_preserved=True,coverage_rows=len(coverage),coverage_sha256=m.sha(OUT/'diagnostic_coverage.csv'),
        source_parameters_sha256=m.sha(OUT/'frozen_parameters.json'),validator_sha256=m.sha(Path(__file__)),
        exclusions=['hardware timing','energy consumption','real field accuracy','firmware deployment','valve control']))
    print('Causality and hidden-pressure invariants passed; coverage and acceptance saved.')

if __name__=='__main__':main()
