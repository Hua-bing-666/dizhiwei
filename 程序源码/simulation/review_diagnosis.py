"""Stage A06/A07: current-design Monte Carlo, bounds and failure challenges.

The 480 trials are uncalibrated noise draws, not independent bench operations.
Two rules see each same trial. Bounded intervals and timing challenges are
separate calculations; do not combine their counts into a success rate.
"""
from pathlib import Path
import csv,hashlib,itertools,json,math,sys
import numpy as np
from diagnosis_feasibility import run as legacy_run

ROOT=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
OUT=ROOT/'simulation/diagnosis_review'
CONFIG=json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
KINDS=CONFIG['random_trials']['kinds']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
def write_csv(name,rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
def hydraulics(ps,c,r,b):
    m=CONFIG['model'];ga=c/math.sqrt(1+r*c*c)
    gb=m['b_c']/math.sqrt(1+m['b_r']*m['b_c']**2) if b else 0.
    p0=ps/(1+m['common_r']*(ga+gb)**2);p1=p0/(1+r*c*c)
    return np.array([p0,p1,c*math.sqrt(p1)],dtype=float)
def truth(kind):
    m=CONFIG['model'];s=CONFIG['sampling'];t=np.arange(s['last_t_s']+1)
    b=(t>=s['b_on_interval_s'][0])&(t<s['b_on_interval_s'][1])
    ramp=np.clip((t-s['fault_start_s'])/s['ramp_seconds'],0,1)
    c=m['healthy_c']+(m['leak_final_c']-m['healthy_c'])*ramp if kind in ('leak','load_unknown') else np.full(t.shape,m['healthy_c'])
    r=m['healthy_r']+(m['restriction_final_r']-m['healthy_r'])*ramp if kind=='restriction' else np.full(t.shape,m['healthy_r'])
    ps=m['supply_kpa']+(m['supply_final_kpa']-m['supply_kpa'])*ramp if kind=='supply' else np.full(t.shape,m['supply_kpa'])
    values=np.array([hydraulics(float(p),float(cc),float(rr),bool(bb)) for p,cc,rr,bb in zip(ps,c,r,b)])
    healthy=np.array([hydraulics(float(p),m['healthy_c'],m['healthy_r'],bool(bb)) for p,bb in zip(ps,b)])
    severity=abs(values[:,2]/healthy[:,2]-1)
    return t,values,healthy[:,2],severity
def means(observed):
    n=CONFIG['sampling']['averaging_samples'];total=np.vstack([np.zeros((1,3)),np.cumsum(observed,axis=0)])
    ends=np.arange(1,len(observed)+1);starts=np.maximum(0,ends-n)
    return (total[ends]-total[starts])/(ends-starts)[:,None]
def classify(observed,method):
    avg=means(observed);rules=CONFIG['rules'];a,b=CONFIG['sampling']['reference_indices']
    valid=(avg[:,1]>rules['valid_p1_min_kpa'])&(avg[:,2]>rules['valid_flow_min_l_min'])
    k=avg[:,2]/np.sqrt(np.maximum(avg[:,1],.001));r=(avg[:,0]-avg[:,1])/np.maximum(avg[:,2]**2,.001)
    k0=float(np.median(k[a:b]));r0=float(np.median(r[a:b]));q0=float(np.median(avg[a:b,2]))
    if method=='physical':
        leak=k/k0-1>rules['k_relative_threshold'];restriction=r-r0>rules['r_absolute_threshold_kpa_min2_l2']
    else:
        leak=avg[:,2]/q0-1>rules['flow_only_relative_threshold'];restriction=avg[:,2]/q0-1< -rules['flow_only_relative_threshold']
    state=np.where(leak&restriction,'uncertain',np.where(leak,'leak_pattern',np.where(restriction,'restriction_pattern','normal')))
    state[~valid]='invalid'
    events=[];active=None;n=CONFIG['sampling']['persistence_samples'];start=CONFIG['sampling']['monitor_start_s']
    for j in range(start,len(state)):
        label=str(state[j])
        if label in ('normal','invalid'):active=None;continue
        if len(set(state[j-n+1:j+1]))==1:
            if active!=label:events.append({'t_s':j,'pattern':label})
            active=label
    return {'mean':avg,'k':k,'r':r,'k0':k0,'r0':r0,'q0':q0,'state':state,'events':events}
def evaluate(kind,diagnostic,severity):
    fault=kind in ('leak','restriction');start=CONFIG['sampling']['fault_start_s'];watch=CONFIG['sampling']['monitor_start_s']
    target='leak_pattern' if kind=='leak' else 'restriction_pattern'
    critical=np.flatnonzero((np.arange(len(severity))>=start)&(severity>=CONFIG['early_reference']['hydraulic_fraction'])) if fault else []
    critical=int(critical[0]) if len(critical) else None
    events=diagnostic['events'];pre=[e for e in events if e['t_s']<start] if fault else events
    post=[e for e in events if e['t_s']>=start] if fault else []
    first=post[0] if post else None
    correct=[e for e in post if e['pattern']==target];detected=correct[0]['t_s'] if correct else None
    valid=bool(fault and not pre and first and first['pattern']==target and detected is not None and critical is not None and detected<critical)
    if not fault:outcome='no_fault_control'
    elif valid:outcome='valid_early'
    elif pre:outcome='prior_false_alarm'
    elif first and first['pattern']!=target:outcome='wrong_first_pattern'
    elif detected is None:outcome='no_correct_detection'
    elif critical is None:outcome='reference_not_reached'
    else:outcome='late_detection'
    exposure=(start-watch) if fault else (CONFIG['sampling']['last_t_s']-watch)
    return {'false_onsets':len(pre),'false_exposure_seconds':exposure,'first_postfault_pattern':first['pattern'] if first else None,'first_postfault_s':first['t_s'] if first else None,'first_correct_s':detected,'critical_s':critical,'severity_at_first_correct':float(severity[detected]) if detected is not None else None,'early_valid':valid,'valid_lead_s':critical-detected if valid else None,'outcome':outcome,'wrong_postfault_onsets':sum(e['pattern']!=target for e in post),'invalid_samples':int(np.sum(diagnostic['state'][watch:]=='invalid'))}
def wilson(k,n):
    z=1.959963984540054;ph=k/n;den=1+z*z/n
    centre=(ph+z*z/(2*n))/den;half=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den
    return [max(0,centre-half),min(1,centre+half)]
def legacy_audit():
    path=ROOT/'simulation/diagnosis_results/trials.csv'
    with path.open(encoding='utf-8-sig',newline='') as f:old=list(csv.DictReader(f))
    assert len(old)==480
    for stored in old:
        reproduced,_=legacy_run(stored['kind'],float(stored['pressure_noise_kpa']),int(stored['seed']))
        for key,value in reproduced.items():
            text=stored[key]
            if value is None:assert text==''
            elif isinstance(value,float):assert math.isclose(float(text),value,rel_tol=1e-11,abs_tol=1e-11),(key,text,value)
            else:assert text==str(value),(key,text,value)
    write_json('legacy_audit.json',{'historical_rows_reproduced':480,'modified_historical_files':False,'historical_healthy_c':.35,'historical_leak_final_c':.44,'historical_restriction_final_r':4.8,'current_healthy_c':CONFIG['model']['healthy_c'],'current_leak_final_c':CONFIG['model']['leak_final_c'],'current_restriction_final_r':CONFIG['model']['restriction_final_r'],'gaussian_sigma_not_hardware_bound':True,'classification':'historical_reproduction_not_physical_validation','source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [path,ROOT/'simulation/diagnosis_results/summary.json',ROOT/'simulation/diagnosis_feasibility.py']}})
def feature_intervals(point,flow_basis,extra):
    p0,p1,q=map(float,point);e=CONFIG['bounded_error_checks']
    # Shunt tolerance maps through the 4mA live zero: dp=(p+50)*epsilon.
    u0=e['pressure_sensor_bound_kpa']+e['uncompensated_shunt_relative_tolerance']*(p0+50)+e['adc_step_pressure_kpa']/2+extra
    u1=e['pressure_sensor_bound_kpa']+e['uncompensated_shunt_relative_tolerance']*(p1+50)+e['adc_step_pressure_kpa']/2+extra
    uq=e['flow_fraction']*(q if flow_basis=='reading' else e['flow_upper_range_l_min'])+60/(e['pulses_per_litre']*e['count_window_s'])
    assert p1>u1 and q>uq
    # Conservative box enclosure. All four corners needed if dp can cross zero.
    k=[(q-uq)/math.sqrt(p1+u1),(q+uq)/math.sqrt(p1-u1)]
    r=[dp/qq**2 for dp in (p0-p1-u0-u1,p0-p1+u0+u1) for qq in (q-uq,q+uq)]
    return {'k':k,'r':[min(r),max(r)],'p0_bound_kpa':u0,'p1_bound_kpa':u1,'flow_bound_l_min':uq}
def target_point(ps,b,kind,degree):
    m=CONFIG['model'];healthy=hydraulics(ps,m['healthy_c'],m['healthy_r'],b)
    lo,hi=(m['healthy_c'],m['leak_final_c']) if kind=='leak' else (m['healthy_r'],m['restriction_final_r'])
    for _ in range(70):
        mid=(lo+hi)/2;changed=hydraulics(ps,mid if kind=='leak' else m['healthy_c'],m['healthy_r'] if kind=='leak' else mid,b)
        if abs(changed[2]/healthy[2]-1)<degree:lo=mid
        else:hi=mid
    assert abs(abs(changed[2]/healthy[2]-1)-degree)<1e-8
    return healthy,changed,mid
def interval_checks():
    e=CONFIG['bounded_error_checks'];rows=[]
    for ps,b,kind,degree,basis,extra in itertools.product(e['supply_grid_kpa'],[False,True],['leak','restriction'],e['target_fraction'],['reading','full_scale'],e['extra_per_channel_residual_bound_kpa']):
        healthy,changed,parameter=target_point(ps,b,kind,degree)
        hi=feature_intervals(healthy,basis,extra);fi=feature_intervals(changed,basis,extra);key='k' if kind=='leak' else 'r'
        health=hi[key];fault=fi[key];margin=fault[0]-health[1]
        threshold_margin=fault[0]-(health[1]*(1+CONFIG['rules']['k_relative_threshold']) if kind=='leak' else health[1]+CONFIG['rules']['r_absolute_threshold_kpa_min2_l2'])
        health_margin=(health[0]*(1+CONFIG['rules']['k_relative_threshold'])-health[1]) if kind=='leak' else health[0]+CONFIG['rules']['r_absolute_threshold_kpa_min2_l2']-health[1]
        rows.append({'supply_kpa':ps,'b_open':b,'kind':kind,'target_fraction':degree,'flow_error_basis':basis,'extra_per_channel_bound_kpa':extra,'feature':key.upper(),'injected_c_or_r':parameter,'healthy_low':health[0],'healthy_high':health[1],'fault_low':fault[0],'fault_high':fault[1],'interval_gap':margin,'intervals_disjoint':margin>0,'fixed_threshold_margin':threshold_margin,'fault_feature_guarantees_fixed_threshold':threshold_margin>0,'healthy_no_false_trigger_margin':health_margin,'healthy_feature_guarantees_no_false_trigger':health_margin>=0,'joint_stationary_threshold_guarantee':threshold_margin>0 and health_margin>=0,'full_physical_error_budget':False})
    write_csv('error_intervals.csv',rows)
    return rows
def timing_checks():
    m=CONFIG['model'];t=np.arange(CONFIG['sampling']['last_t_s']+1);results=[]
    for kind,delay in itertools.product(CONFIG['timing_challenge']['kinds'],CONFIG['timing_challenge']['p1_delay_s']):
        values=np.array([hydraulics(m['supply_kpa'] if kind=='normal_b_switch' or not 180<=j<300 else 80,m['healthy_c'],m['healthy_r'],kind=='normal_b_switch' and 180<=j<300) for j in t])
        skewed=values.copy();skewed[:,1]=np.interp(t-delay,t,values[:,1],left=values[0,1])
        diag=classify(skewed,'physical');result=evaluate('normal',diag,np.zeros(t.shape))
        results.append({'kind':kind,'p1_delay_s':delay,'pressure_random_sigma_kpa':0,'false_onsets':result['false_onsets'],'max_positive_r_excess':float(np.max(diag['r'][130:]-diag['r0'])),'first_event_s':diag['events'][0]['t_s'] if diag['events'] else None,'hypothetical_skew_not_measured_hardware':True})
    write_csv('timing_challenges.csv',results)
    return results
def mismatch_checks():
    m=CONFIG['model'];spec=CONFIG['model_mismatch_challenge'];t=np.arange(CONFIG['sampling']['last_t_s']+1);rows=[]
    for exponent,step in itertools.product(spec['healthy_load_exponents'],spec['step_supply_kpa']):
        def solve(ps):
            lo,hi=0.,float(ps)
            for _ in range(70):
                p1=(lo+hi)/2;q=m['healthy_c']*math.sqrt(spec['reference_pressure_kpa'])*(p1/spec['reference_pressure_kpa'])**exponent
                p0=p1+m['healthy_r']*q*q
                if p0+m['common_r']*q*q<ps:lo=p1
                else:hi=p1
            return np.array([p0,p1,q])
        values=np.array([solve(step if 180<=j<300 else m['supply_kpa']) for j in t])
        for method in ['physical','flow_only']:
            diag=classify(values,method);result=evaluate('normal',diag,np.zeros(t.shape))
            rows.append({'healthy_exponent':exponent,'step_supply_kpa':step,'method':method,'false_onsets':result['false_onsets'],'first_event_s':diag['events'][0]['t_s'] if diag['events'] else None,'max_abs_k_relative_change':float(np.max(abs(diag['k'][130:]/diag['k0']-1))),'q_min_l_min':float(np.min(values[:,2])),'q_max_l_min':float(np.max(values[:,2])),'exponent_fitted_to_hardware':False})
        if exponent==.5:
            for ps in (m['supply_kpa'],step):assert np.allclose(solve(ps),hydraulics(ps,m['healthy_c'],m['healthy_r'],False),atol=1e-10)
    write_csv('model_mismatch_challenges.csv',rows)
    return rows
def main():
    m=CONFIG['model'];hw=json.loads((ROOT/'simulation/hardware_results/summary.json').read_text(encoding='utf-8'))
    assert [m['healthy_c'],m['leak_final_c'],m['healthy_r'],m['restriction_final_r']]==[hw['healthy_c'],hw['leak_max_c'],*hw['r_range']]
    legacy_audit()
    truths=[truth(kind) for kind in KINDS];samples=[];rows=[];traces={};ids=[];kind_indices=[];sigmas=[];seeds=[]
    for sigma,kind,seed in itertools.product(CONFIG['random_trials']['pressure_sigma_kpa'],KINDS,range(CONFIG['random_trials']['seed_first'],CONFIG['random_trials']['seed_last']+1)):
        t,values,hq,severity=truths[KINDS.index(kind)];rng=np.random.default_rng(seed)
        observed=values+rng.normal(0,[sigma,sigma,CONFIG['random_trials']['flow_sigma_l_min']],values.shape)
        if kind=='drift':observed[:,0]+=CONFIG['random_trials']['drift_final_kpa']*np.clip((t-360)/180,0,1)
        tid=f'{kind}|{sigma:g}|{seed}';samples.append(observed);ids.append(tid);kind_indices.append(KINDS.index(kind));sigmas.append(sigma);seeds.append(seed)
        for method in ['physical','flow_only']:
            diagnostic=classify(observed,method);result=evaluate(kind,diagnostic,severity)
            row={'trial_id':tid,'kind':kind,'pressure_sigma_kpa':sigma,'seed':seed,'method':method,**result};rows.append(row)
            if seed==CONFIG['random_trials']['seed_first'] and method=='physical':
                traces[f'{kind}_{sigma:g}']={'t':t.tolist(),'true':values.tolist(),'observed':observed.tolist(),'mean':diagnostic['mean'].tolist(),'healthy_q':hq.tolist(),'severity':severity.tolist(),'k':diagnostic['k'].tolist(),'r':diagnostic['r'].tolist(),'k0':diagnostic['k0'],'r0':diagnostic['r0'],'state':diagnostic['state'].tolist(),'events':diagnostic['events'],**row}
    assert len(samples)==480 and len(rows)==960
    np.savez_compressed(OUT/'raw_trials.npz',observed=np.array(samples),trial_ids=np.array(ids),kind_index=np.array(kind_indices),pressure_sigma=np.array(sigmas),seeds=np.array(seeds),t=truths[0][0],truth_by_kind=np.array([v[1] for v in truths]),healthy_q_by_kind=np.array([v[2] for v in truths]),severity_by_kind=np.array([v[3] for v in truths]))
    write_csv('method_results.csv',rows)
    groups=[]
    for sigma,kind,method in itertools.product(CONFIG['random_trials']['pressure_sigma_kpa'],KINDS,['physical','flow_only']):
        selected=[r for r in rows if r['kind']==kind and r['pressure_sigma_kpa']==sigma and r['method']==method];valid=[r for r in selected if r['early_valid']]
        groups.append({'kind':kind,'method':method,'pressure_sigma_kpa':sigma,'trials':len(selected),'early_trials':len(valid),'early_wilson95':wilson(len(valid),len(selected)) if kind in ('leak','restriction') else None,'outcomes':{outcome:sum(r['outcome']==outcome for r in selected) for outcome in ['valid_early','prior_false_alarm','wrong_first_pattern','no_correct_detection','reference_not_reached','late_detection','no_fault_control']},'mean_false_onsets':float(np.mean([r['false_onsets'] for r in selected])),'false_exposure_seconds_per_trial':selected[0]['false_exposure_seconds'],'median_valid_lead_s':float(np.median([r['valid_lead_s'] for r in valid])) if valid else None,'median_valid_detection_fraction':float(np.median([r['severity_at_first_correct'] for r in valid])) if valid else None,'no_correct_detection_trials':sum(r['first_correct_s'] is None for r in selected) if kind in ('leak','restriction') else None})
    intervals=interval_checks();timing=timing_checks();mismatch=mismatch_checks()
    data={'classification':'uncalibrated_current_design_simulation_candidate','physical_data':False,'protocol_version':CONFIG['version'],'trials':480,'method_evaluations':960,'samples_per_trial':601,'bounded_error_cases':len(intervals),'timing_challenges':len(timing),'mismatch_method_records':len(mismatch),'unknown_load_observationally_identical_to_leak':True,'settings':CONFIG,'groups':groups,'traces':traces,'interval_summary':[{'flow_error_basis':basis,'extra_per_channel_bound_kpa':extra,'cases':36,'disjoint_cases':sum(r['intervals_disjoint'] for r in intervals if r['flow_error_basis']==basis and r['extra_per_channel_bound_kpa']==extra),'fixed_threshold_guarantee_cases':sum(r['fault_feature_guarantees_fixed_threshold'] for r in intervals if r['flow_error_basis']==basis and r['extra_per_channel_bound_kpa']==extra),'joint_stationary_guarantee_cases':sum(r['joint_stationary_threshold_guarantee'] for r in intervals if r['flow_error_basis']==basis and r['extra_per_channel_bound_kpa']==extra)} for basis,extra in itertools.product(['reading','full_scale'],CONFIG['bounded_error_checks']['extra_per_channel_residual_bound_kpa'])], 'timing':timing,'model_mismatch':mismatch,'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),OUT/'protocol.json',ROOT/'simulation/hardware_results/summary.json',ROOT/'simulation/hardware_results/range_grid.csv']}}
    a=data['traces']['leak_0.3'];b=data['traces']['load_unknown_0.3'];assert a['true']==b['true'] and a['observed']==b['observed']
    write_json('summary.json',data)
    print('Historical 480 rows reproduced. New: 480 trials / 960 paired rule records / 288 bound cases / 8 timing challenges; no physical data.')
    for group in groups:
        if group['method']=='physical' and group['kind'] in ('leak','restriction'):
            print(group['kind'],group['pressure_sigma_kpa'],group['early_trials'],group['outcomes'],group['median_valid_lead_s'])
    print('Bounds:',data['interval_summary']);print('Timing:',timing);print('Model mismatch:',mismatch)
if __name__=='__main__':main()
