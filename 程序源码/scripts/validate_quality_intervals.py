"""Independent window/count checks plus full frozen-result reproduction."""
from pathlib import Path
import csv,itertools,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_quality_intervals as m
from sampling_quality_runtime import SamplingNode
from review_hybrid_sampling import BoundedEvidence,sensor_replay,residual
OUT=m.OUT

def read(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def compare(a,b):
    for k,v in b.items():
        if v is None:assert a[k]==''
        elif isinstance(v,float):assert np.isclose(float(a[k]),v,atol=1e-10,rtol=1e-10),(k,a[k],v)
        else:assert a[k]==str(v),(k,a[k],v)

def window_oracle(out,obs,counts,mode):
    acq=set(out['acquired']);last=-1;increments=[];c=out['context']
    resets=np.flatnonzero(np.diff(np.r_[0,counts])<0)
    for rec in out['records']:
        t=rec['t'];assert t in acq
        if rec['valid']:
            assert all(j in acq for j in range(t-9,t+1))
            pp=obs[t-9:t+1,:2];assert np.all(np.isfinite(pp))
            if mode=='range':assert np.all((pp>=0)&(pp<=200))
            assert not np.any((resets>t-10)&(resets<=t))
            q=60*(counts[t]-counts[t-10])/(540*10);assert rec['flow_q10']==q
            x=residual(*pp.mean(axis=0),q,m.PARAM['reference'],c['gain'],c['r0'])
            assert np.allclose(rec['x'],x,atol=1e-12)
            if t!=last+1:increments=[]
            increments.append(x/np.array(c['scale'])-.5)
            oracle=np.maximum(0,np.cumsum(np.array(increments[-60:])[::-1],axis=0).max(axis=0))
            assert np.allclose(rec['bounded'],oracle,atol=1e-9)
        else:
            assert rec['bounded']==[0.,0.];increments=[]
        last=t
    for method in m.METHODS:
        ll=dict(zip([r['t'] for r in out['records']],out['decisions'][method]['labels']))
        for e in out['decisions'][method]['events']:
            code={'leak_pattern':1,'restriction_pattern':2,'uncertain':3}[e['pattern']]
            assert all(ll.get(t)==code for t in range(e['t_s']-4,e['t_s']+1))

def main():
    p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'));m.PARAM=p
    summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    assert p['config']==m.CFG and summary['parameters_sha256']==m.sha(OUT/'frozen_parameters.json')
    for name,digest in p['sources'].items():assert m.sha(ROOT/name)==digest,name
    for name,digest in summary['source_hashes'].items():assert m.sha(OUT/name)==digest,name
    assert p['training_sha256']==m.sha(OUT/'healthy_training.csv')
    assert not set(m.TRAIN)&set(m.TEST)
    assert not (set(m.TRAIN)|set(m.TEST))&set(range(21000,29000))
    training=read('healthy_training.csv');assert len(training)==1152
    assert {r['scene'] for r in training}=={'normal','long_normal','supply_step','supply_ramp'}
    for r in training:
        period=int(r['period']);phase=int(r['phase']);tr,obs,counts=m.inputs(r['scene'],float(r['sigma']),int(r['seed']))
        out=m.replay(obs,counts,p['reference'],[1e9,1e9],period,phase)
        bs=np.array([a['bounded'] for a in out['records']])
        compare(r,dict(peak_q=float(bs[:,0].max()),peak_r=float(bs[:,1].max()),eligible_frames=sum(a['valid'] for a in out['records'])))
    for period in m.PERIODS:
        for k,key in enumerate(['q','r']):assert p['limits'][str(period)][k]==max(5.,1.1*max(float(r[f'peak_{key}']) for r in training if int(r['period'])==period))
    print('1152 healthy training records and limits reproduced.',flush=True)
    sampling=read('sampling_results.csv');quality=read('quality_results.csv')
    assert (len(sampling),len(quality))==(11520,2304)
    for stage,rr in [('sampling',sampling),('quality',quality)]:
        lookup={}
        for r in rr:
            key=(float(r['sigma']),r['scene'],int(r['seed']),int(r['period']),int(r['phase']),r['quality'])
            lookup.setdefault(key,[]).append(r)
        checked=0
        for (sigma,scene,seed,period,phase,mode),saved in lookup.items():
            assert len(saved)==2 and {r['method'] for r in saved}==set(m.METHODS)
            tr,obs,counts=m.inputs(scene,sigma,seed,stage=='quality')
            out=m.replay(obs,counts,p['reference'],p['limits'][str(period)],period,phase,mode)
            for r in saved:compare(r,m.metrics(out,tr,r['method']));checked+=1
        print(f'{checked} {stage} records reproduced.',flush=True)
    invariants=oracles=0
    for scene,quality_case in [('normal',False),('pulse8',False),('leak_r720',False),('drift_p0',True),('spike_range',True),('nan_pressure',True),('counter_reset',True),('bad_calibration',True)]:
        tr,obs,counts=m.inputs(scene,10.,41000,quality_case)
        for period in m.PERIODS:
            phase=period-1;out=m.replay(obs,counts,p['reference'],p['limits'][str(period)],period,phase)
            window_oracle(out,obs,counts,'range');oracles+=1
            changed=obs.copy();unread=sorted(set(range(len(obs)))-set(out['acquired']));changed[unread,:2]=999.
            assert out==m.replay(changed,counts,p['reference'],p['limits'][str(period)],period,phase)
            cut=370;changed=obs.copy();changed[cut+1:,:2]=999.;future_counts=counts.copy();future_counts[cut+1:]+=1000000
            ff=m.replay(changed,future_counts,p['reference'],p['limits'][str(period)],period,phase)
            for key in ['acquired','triggers']:assert [t for t in out[key] if t<=cut]==[t for t in ff[key] if t<=cut]
            for key in ['records','quality_events']:
                field='t' if key=='records' else 't_s'
                assert [r for r in out[key] if r[field]<=cut]==[r for r in ff[key] if r[field]<=cut]
            for method in m.METHODS:assert [e for e in out['decisions'][method]['events'] if e['t_s']<=cut]==[e for e in ff['decisions'][method]['events'] if e['t_s']<=cut]
            invariants+=1
    # The sequential fixed-rate runtime must preserve the prior clean-data frontend.
    old=json.loads(m.BASE.read_text(encoding='utf-8'));equiv=0
    for sigma,scene in itertools.product(m.SIGMAS,['normal','fast_leak_switch','leak_r90']):
        tr,obs,counts=m.inputs(scene,sigma,41000)
        out=m.replay(obs,counts,p['reference'],old['h_bounded_sensor']['fixed'],1,0)
        other=sensor_replay(obs,41000,p['reference'],'fixed',old['h_bounded_sensor']['fixed'])
        assert out['acquired']==other['acquired']
        for method in m.METHODS:
            assert out['decisions'][method]=={k:other['decisions'][method][k] for k in ['events','labels']}
        assert np.allclose([r['x'] for r in out['records']],[r['x'] for r in other['records']],atol=1e-12);equiv+=1
    # Explicit counter recovery and bad-commissioning tests.
    tr,obs,counts=m.inputs('counter_reset',.3,41000,True);out=m.replay(obs,counts,p['reference'],p['limits']['1'],1,0)
    assert {'t_s':420,'reason':'counter_reset'} in out['quality_events']
    assert all(not r['valid'] for r in out['records'] if 420<=r['t']<430)
    assert next(r for r in out['records'] if r['t']==430)['valid']
    tr,obs,counts=m.inputs('bad_calibration',.3,41000,True);out=m.replay(obs,counts,p['reference'],p['limits']['1'],1,0)
    assert not out['baseline_accepted'] and all(not r['valid'] for r in out['records'])
    # Runtime rejects hidden pressure, duplicated timestamps and unsupported phases.
    node=SamplingNode(p['reference'],p['limits']['1'],5,0);node.update(0,20,[100,90])
    try:node.update(0,20,[100,90]);raise RuntimeError('Duplicate accepted')
    except AssertionError:pass
    m.dump('acceptance.json',dict(status='passed_synthetic_logic',physical_data=False,healthy_rows_reproduced=1152,
        sampling_rows_reproduced=len(sampling),quality_rows_reproduced=len(quality),window_oracle_cases=oracles,
        causal_and_unread_pressure_cases=invariants,prior_frontend_equivalence_cases=equiv,
        counter_reset_recovery_checked=True,bad_calibration_blocked=True,
        validator_sha256=m.sha(Path(__file__)),parameters_sha256=m.sha(OUT/'frozen_parameters.json'),
        exclusions=['sensor accuracy','physical health of commissioning','real sleep or energy','field performance','Word layout']))
    print('Window, pulse, confirmation, future/unread-pressure, reset and commissioning checks passed.')

if __name__=='__main__':main()
