"""Unseen operating points challenge a frozen C profile; no retuning on test."""
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'prototype'),str(ROOT/'simulation')]
from platform_service import *
from review_operating_reference import plant,observe
from review_hybrid_sampling import pulse_frontend

def run():
    profiles={sigma:reference_profile(sigma) for sigma in (.3,3.)};exe,digest=compile_bridge();rows=[]
    for sigma in (.3,3.):
        for seed in (72001,72002):
            for ps in (90.,150.):
                for exponent in (.3,.5,.8):
                    for scene in ('normal','leak','restriction'):
                        t=np.arange(631);b=(t>=180)&(t<300);ramp=np.clip((t-360)/90,0,1)
                        leak=.09*ramp if scene=='leak' else 0
                        resistance=.8+7.2*ramp if scene=='restriction' else .8
                        values=plant(np.full(len(t),ps),exponent,b,resistance,leak);healthy=plant(np.full(len(t),ps),exponent,b)
                        tr=dict(t=t,values=values,healthy_q=healthy[:,2],b=b,supply=np.full(len(t),ps))
                        obs=observe(tr,sigma,seed,'normal');counts=pulse_frontend(obs,seed)['cumulative'];onsets=[];invalid=0
                        with AcquisitionPipeline(profiles[sigma],exe,synthetic=True) as p:
                            for tt,count in enumerate(counts):
                                r,fresh=p.update(tt,int(count),(tt+1)*1000,pressure_reads(tt,obs[tt,:2]))
                                invalid+=tt>=130 and r['snapshot'].status!=0
                                onsets.extend(dict(t=tt,pattern=e['code']-3) for e in fresh if e['code']>=4)
                        fault=scene!='normal';before=[e for e in onsets if not fault or e['t']<360];after=[e for e in onsets if fault and e['t']>=360]
                        severity=abs(values[:,2]/healthy[:,2]-1);critical=np.flatnonzero((t>=360)&(severity>=.15)) if fault else []
                        critical=int(critical[0]) if len(critical) else None;first=after[0] if after else None;target=1 if scene=='leak' else 2
                        early=bool(fault and not before and first and first['pattern']==target and critical is not None and first['t']<critical)
                        rows.append(dict(seed=seed,sigma=sigma,supply_kpa=ps,load_exponent=exponent,scene=scene,false_onsets=len(before),
                                         first_post=first,critical_s=critical,early_valid=early,invalid_updates=invalid,
                                         outcome='control' if not fault else 'prior_false_alarm' if before else 'no_detection' if not first else 'wrong_pattern' if first['pattern']!=target else 'early' if early else 'late'))
    data=dict(classification='unseen_operating_points_same_steady_model',physical_data=False,energy_measured=False,
              c_sha256=digest,frozen_training_seed=69001,test_seeds=[72001,72002],profile_retuned_on_test=False,
              note='Fixed reference exponent about 0.5; changed load law is deliberately outside calibration. Failure is not hidden.',trials=rows)
    out=ROOT/'simulation/platform_upgrade';(out/'cross_operating_points.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    summary=[]
    for exponent in (.3,.5,.8):
        for scene in ('normal','leak','restriction'):
            rr=[r for r in rows if r['load_exponent']==exponent and r['scene']==scene]
            summary.append(dict(exponent=exponent,scene=scene,trials=len(rr),false_onsets=sum(r['false_onsets'] for r in rr),early_valid=sum(r['early_valid'] for r in rr),outcomes={k:sum(r['outcome']==k for r in rr) for k in sorted(set(r['outcome'] for r in rr))}))
    (out/'cross_operating_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':run()
