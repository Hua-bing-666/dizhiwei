"""Independent arithmetic/replay checks; this is not physical validation.

Does not import the simulation generator. Uses convolution instead of its
cumulative sums, streaks instead of its set window, and a numerical supply
balance instead of its closed-form hydraulic solver.
"""
from pathlib import Path
import csv, hashlib, itertools, json, math
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/diagnosis_review'
cfg=json.loads((DATA/'protocol.json').read_text(encoding='utf-8'))
summary=json.loads((DATA/'summary.json').read_text(encoding='utf-8'))
raw=np.load(DATA/'raw_trials.npz',allow_pickle=False)
checks=[]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(name):
    with (DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def close(a,b):assert np.allclose(a,b,atol=2e-10,rtol=2e-10),(a,b)
def check(name,detail):checks.append({'check':name,'result':'passed','detail':detail})
def csv_equal(a,b):
    if a is None:assert b==''
    elif isinstance(a,(bool,np.bool_,str)):assert str(a)==b,(a,b)
    else:close(float(a),float(b))

def solve(ps,c,r,b,common=.4,bc=.35,br=.8):
    # Solve ps - p0 - Rc*(Qa+Qb)^2 = 0 by bisection.
    lo,hi=0.,ps
    for _ in range(65):
        p0=(lo+hi)/2
        p1=p0/(1+r*c*c);q=c*math.sqrt(p1)
        qb=bc*math.sqrt(p0/(1+br*bc*bc)) if b else 0.
        if p0+common*(q+qb)**2<ps:lo=p0
        else:hi=p0
    return np.array([p0,p1,q])

def replay(observed,method):
    n=cfg['sampling']['averaging_samples'];length=len(observed)
    count=np.minimum(np.arange(length)+1,n)
    avg=np.stack([np.convolve(observed[:,i],np.ones(n),mode='full')[:length]/count for i in range(3)],axis=1)
    a,b=cfg['sampling']['reference_indices'];k=avg[:,2]/np.sqrt(np.maximum(avg[:,1],.001))
    r=(avg[:,0]-avg[:,1])/np.maximum(avg[:,2]**2,.001)
    k0=float(np.median(k[a:b]));r0=float(np.median(r[a:b]));q0=float(np.median(avg[a:b,2]))
    rules=cfg['rules'];states=[]
    for j in range(length):
        if avg[j,1]<=rules['valid_p1_min_kpa'] or avg[j,2]<=rules['valid_flow_min_l_min']:state='invalid'
        else:
            l=(k[j]/k0-1>rules['k_relative_threshold']) if method=='physical' else (avg[j,2]/q0-1>rules['flow_only_relative_threshold'])
            z=(r[j]-r0>rules['r_absolute_threshold_kpa_min2_l2']) if method=='physical' else (avg[j,2]/q0-1< -rules['flow_only_relative_threshold'])
            state='uncertain' if l and z else 'leak_pattern' if l else 'restriction_pattern' if z else 'normal'
        states.append(state)
    streak=0;previous=None;active=None;events=[]
    for j,state in enumerate(states):
        streak=streak+1 if state==previous else 1;previous=state
        if j<cfg['sampling']['monitor_start_s']:continue
        if state in ('normal','invalid'):active=None
        elif streak>=cfg['sampling']['persistence_samples']:
            if state!=active:events.append({'t_s':j,'pattern':state})
            active=state
    return avg,k,r,k0,r0,states,events

def evaluate(kind,states,events,severity):
    s=cfg['sampling'];fault=kind in ('leak','restriction');start=s['fault_start_s'];watch=s['monitor_start_s']
    expected='leak_pattern' if kind=='leak' else 'restriction_pattern'
    critical=next((j for j in range(start,len(severity)) if severity[j]>=cfg['early_reference']['hydraulic_fraction']),None) if fault else None
    pre=[e for e in events if e['t_s']<start] if fault else events
    post=[e for e in events if e['t_s']>=start] if fault else []
    first=post[0] if post else None
    detection=next((e['t_s'] for e in post if e['pattern']==expected),None)
    valid=bool(fault and not pre and first and first['pattern']==expected and detection is not None and critical is not None and detection<critical)
    outcome=('no_fault_control' if not fault else 'valid_early' if valid else 'prior_false_alarm' if pre else 'wrong_first_pattern' if first and first['pattern']!=expected else 'no_correct_detection' if detection is None else 'reference_not_reached' if critical is None else 'late_detection')
    return dict(false_onsets=len(pre),false_exposure_seconds=start-watch if fault else s['last_t_s']-watch,first_postfault_pattern=first['pattern'] if first else None,first_postfault_s=first['t_s'] if first else None,first_correct_s=detection,critical_s=critical,severity_at_first_correct=float(severity[detection]) if detection is not None else None,early_valid=valid,valid_lead_s=critical-detection if valid else None,outcome=outcome,wrong_postfault_onsets=sum(e['pattern']!=expected for e in post),invalid_samples=states[watch:].count('invalid'))

def main():
    for path,digest in summary['source_sha256'].items():assert sha(ROOT/path)==digest,path
    assert not summary['physical_data'] and not cfg['rules']['operation_state_gating_implemented']
    obs=raw['observed'];ids=raw['trial_ids'];kinds=cfg['random_trials']['kinds'];t=raw['t'];assert obs.shape==(480,601,3)
    assert len(set(ids.tolist()))==480 and np.isfinite(obs).all() and np.array_equal(t,np.arange(601))
    records=rows('method_results.csv');indexed={(r['trial_id'],r['method']):r for r in records};assert len(indexed)==len(records)==960
    expected_ids={f'{kind}|{sigma:g}|{seed}' for kind,sigma,seed in itertools.product(kinds,cfg['random_trials']['pressure_sigma_kpa'],range(10300,10320))};assert set(ids)==expected_ids
    m=cfg['model'];s=cfg['sampling']
    for ki,kind in enumerate(kinds):
        for j in t:
            ramp=np.clip((j-s['fault_start_s'])/s['ramp_seconds'],0,1);b=180<=j<300
            c=m['healthy_c']+(m['leak_final_c']-m['healthy_c'])*ramp if kind in ('leak','load_unknown') else m['healthy_c']
            r=m['healthy_r']+(m['restriction_final_r']-m['healthy_r'])*ramp if kind=='restriction' else m['healthy_r']
            ps=m['supply_kpa']+(m['supply_final_kpa']-m['supply_kpa'])*ramp if kind=='supply' else m['supply_kpa']
            point=solve(ps,c,r,b);healthy=solve(ps,m['healthy_c'],m['healthy_r'],b)
            close(point,raw['truth_by_kind'][ki,j]);close(healthy[2],raw['healthy_q_by_kind'][ki,j]);close(abs(point[2]/healthy[2]-1),raw['severity_by_kind'][ki,j])
    check('hydraulic_truth_numerical_supply_balance','3606 kind/time points; healthy references and severity independently recomputed')
    gridpath=ROOT/'simulation/hardware_results/range_grid.csv'
    with gridpath.open(encoding='utf-8',newline='') as f:grid=list(csv.DictReader(f))
    # Existing range grid also records total pump duty, checked from conservation.
    for g in grid:
        c=float(g['c']);r=float(g['r']);ps=float(g['ps_kpa']);b=g['b_open']=='True'
        point=solve(ps,c,r,b);close(point,[float(g['p0_kpa']),float(g['p1_kpa']),float(g['q_a_l_min'])])
        qb=.35*math.sqrt(point[0]/(1+.8*.35**2)) if b else 0.
        close(point[2]+qb,float(g['q_total_l_min']))
    check('existing_range_grid','24 rows independently solved, preserving the hardware-design parameters')
    recomputed={}
    for i,tid in enumerate(ids):
        kind=kinds[int(raw['kind_index'][i])];severity=raw['severity_by_kind'][int(raw['kind_index'][i])]
        rng=np.random.default_rng(int(raw['seeds'][i]));expected=raw['truth_by_kind'][int(raw['kind_index'][i])]+rng.normal(0,[raw['pressure_sigma'][i],raw['pressure_sigma'][i],cfg['random_trials']['flow_sigma_l_min']],(601,3))
        if kind=='drift':expected[:,0]+=cfg['random_trials']['drift_final_kpa']*np.clip((t-360)/180,0,1)
        close(expected,obs[i])
        for method in ('physical','flow_only'):
            avg,k,r,k0,r0,states,events=replay(obs[i],method);result=evaluate(kind,states,events,severity)
            record=indexed[(tid,method)]
            for key,value in result.items():csv_equal(value,record[key])
            recomputed[(tid,method)]=result
            if int(raw['seeds'][i])==10300 and method=='physical':
                trace=summary['traces'][f'{kind}_{raw["pressure_sigma"][i]:g}']
                for key,value in [('observed',obs[i]),('mean',avg),('k',k),('r',r),('k0',k0),('r0',r0)]:close(value,trace[key])
                assert states==trace['state'] and events==trace['events']
    check('raw_draws_and_paired_replay','480 saved noise draws; all 960 rule records and 24 selected traces independently checked')
    for g in summary['groups']:
        chosen=[recomputed[(tid,g['method'])] for i,tid in enumerate(ids) if kinds[int(raw['kind_index'][i])]==g['kind'] and raw['pressure_sigma'][i]==g['pressure_sigma_kpa']]
        assert len(chosen)==g['trials']==20
        valid=[r for r in chosen if r['early_valid']];assert len(valid)==g['early_trials']
        assert sum(g['outcomes'].values())==20
        for outcome,count in g['outcomes'].items():assert sum(r['outcome']==outcome for r in chosen)==count
        close(np.mean([r['false_onsets'] for r in chosen]),g['mean_false_onsets'])
        for key,field in [('median_valid_lead_s','valid_lead_s'),('median_valid_detection_fraction','severity_at_first_correct')]:
            if valid:close(np.median([r[field] for r in valid]),g[key])
            else:assert g[key] is None
        if g['early_wilson95'] is not None:
            n=20;k=len(valid);z=1.959963984540054;den=n+z*z
            centre=(k+z*z/2)/den;half=z*math.sqrt(k*(n-k)/n+z*z/4)/den
            close([max(0,centre-half),min(1,centre+half)],g['early_wilson95'])
    check('group_and_failure_accounting','48 groups, exclusive 20-trial outcomes, success-only medians and Wilson intervals')
    for sigma,seed in itertools.product(cfg['random_trials']['pressure_sigma_kpa'],range(10300,10320)):
        a=np.where(ids==f'leak|{sigma:g}|{seed}')[0][0];b=np.where(ids==f'load_unknown|{sigma:g}|{seed}')[0][0]
        assert np.array_equal(obs[a],obs[b])
    check('non_identifiability_counterexample','all 80 paired leak/unknown-normal-load raw observations are exactly equal')
    for method in ('physical','flow_only'):
        original=replay(obs[0],method);changed=obs[0].copy();changed[401:]+=np.array([100,30,2]);challenged=replay(changed,method)
        close(original[0][:401],challenged[0][:401]);assert original[5][:401]==challenged[5][:401]
        assert [e for e in original[6] if e['t_s']<=400]==[e for e in challenged[6] if e['t_s']<=400]
    check('future_perturbation','future samples do not affect the independent causal replay or earlier events')
    bounded=rows('error_intervals.csv');assert len(bounded)==288
    e=cfg['bounded_error_checks']
    for row in bounded:
        ps=float(row['supply_kpa']);b=row['b_open']=='True';kind=row['kind'];parameter=float(row['injected_c_or_r']);target=float(row['target_fraction'])
        h=solve(ps,m['healthy_c'],m['healthy_r'],b);f=solve(ps,parameter if kind=='leak' else m['healthy_c'],m['healthy_r'] if kind=='leak' else parameter,b);close(abs(f[2]/h[2]-1),target)
        boxes=[]
        for point in (h,f):
            p0,p1,q=point;u0=e['pressure_sensor_bound_kpa']+.001*(p0+50)+e['adc_step_pressure_kpa']/2+float(row['extra_per_channel_bound_kpa']);u1=e['pressure_sensor_bound_kpa']+.001*(p1+50)+e['adc_step_pressure_kpa']/2+float(row['extra_per_channel_bound_kpa'])
            uq=.01*(q if row['flow_error_basis']=='reading' else 5)+60/(540*10)
            corners=[(qq/math.sqrt(pp1),(pp0-pp1)/qq**2) for pp0,pp1,qq in itertools.product((p0-u0,p0+u0),(p1-u1,p1+u1),(q-uq,q+uq))]
            values=[v[0 if kind=='leak' else 1] for v in corners];boxes.append([min(values),max(values)])
        hl,hh=boxes[0];fl,fh=boxes[1]
        for key,value in [('healthy_low',hl),('healthy_high',hh),('fault_low',fl),('fault_high',fh),('interval_gap',fl-hh)]:csv_equal(value,row[key])
        tm=fl-hh*1.06 if kind=='leak' else fl-hh-.6;hm=hl*1.06-hh if kind=='leak' else hl+.6-hh
        for key,value in [('fixed_threshold_margin',tm),('healthy_no_false_trigger_margin',hm),('intervals_disjoint',fl>hh),('fault_feature_guarantees_fixed_threshold',tm>0),('healthy_feature_guarantees_no_false_trigger',hm>=0),('joint_stationary_threshold_guarantee',tm>0 and hm>=0)]:csv_equal(value,row[key])
    for g in summary['interval_summary']:
        chosen=[r for r in bounded if r['flow_error_basis']==g['flow_error_basis'] and float(r['extra_per_channel_bound_kpa'])==g['extra_per_channel_bound_kpa']];assert len(chosen)==36
        for field,col in [('disjoint_cases','intervals_disjoint'),('fixed_threshold_guarantee_cases','fault_feature_guarantees_fixed_threshold'),('joint_stationary_guarantee_cases','joint_stationary_threshold_guarantee')]:assert g[field]==sum(r[col]=='True' for r in chosen)
    check('bounded_boxes_and_threshold_margins','288 targets; all 4608 healthy/fault box corners and 8 grouped summaries independently checked; per-target feature only')
    for row in rows('timing_challenges.csv'):
        values=np.array([solve(120 if row['kind']=='normal_b_switch' or not 180<=j<300 else 80,.28,.8,row['kind']=='normal_b_switch' and 180<=j<300) for j in t])
        values[:,1]=np.interp(t-float(row['p1_delay_s']),t,values[:,1],left=values[0,1]);_,_,r,_,r0,states,events=replay(values,'physical')
        csv_equal(len(events),row['false_onsets']);csv_equal(events[0]['t_s'] if events else None,row['first_event_s']);csv_equal(np.max(r[130:]-r0),row['max_positive_r_excess'])
    check('timing_challenges','8 noiseless skew challenges independently replayed; not measured sensor response')
    for row in rows('model_mismatch_challenges.csv'):
        exponent=float(row['healthy_exponent']);step=float(row['step_supply_kpa']);values=[]
        for j in t:
            ps=step if 180<=j<300 else 120;lo,hi=0.,ps
            for _ in range(65):
                p1=(lo+hi)/2;q=.28*10*(p1/100)**exponent
                if p1+1.2*q*q<ps:lo=p1
                else:hi=p1
            values.append([p1+.8*q*q,p1,q])
        values=np.array(values);_,k,_,k0,_,states,events=replay(values,row['method'])
        csv_equal(len(events),row['false_onsets']);csv_equal(events[0]['t_s'] if events else None,row['first_event_s']);csv_equal(np.max(abs(k[130:]/k0-1)),row['max_abs_k_relative_change'])
        csv_equal(np.min(values[:,2]),row['q_min_l_min']);csv_equal(np.max(values[:,2]),row['q_max_l_min'])
    check('healthy_model_mismatch','16 method records independently solved/replayed; pressure exponents remain hypothetical')
    audit=json.loads((DATA/'legacy_audit.json').read_text(encoding='utf-8'))
    for path,digest in audit['source_sha256'].items():assert sha(ROOT/path)==digest
    assert audit['historical_rows_reproduced']==480
    check('historical_preservation','legacy reproduction record and its three source hashes checked; historical results not replaced')
    sources=[Path(__file__),DATA/'protocol.json',DATA/'summary.json',DATA/'raw_trials.npz',DATA/'method_results.csv',DATA/'error_intervals.csv',DATA/'timing_challenges.csv',DATA/'model_mismatch_challenges.csv',DATA/'legacy_audit.json',gridpath]
    report={'date':'2026-10-04','status':'passed_with_uncalibrated_simulation_scope','physical_validation':False,'independent_external_review':False,'generator_imported':False,'checks':checks,'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sources}}
    (DATA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print(f'{len(checks)} scoped arithmetic/replay checks passed; no physical validation.')
if __name__=='__main__':main()
