"""Analytical boundary counterexamples, separate from the frozen trajectory set."""
from pathlib import Path
import hashlib,json,math,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
import review_integer_diagnosis as m
from integer_diagnosis_reference import flags
def main():
    m.parameters();m.compile_core()
    # These are constructed predicates, not new field traces or tuned thresholds.
    p=120.25;threshold=6/(5*math.sqrt(p/120))-1
    contract=dict(pressure_case_kpa=119.999,table_case_kpa=p,table_threshold=threshold,
                  table_threshold_micro=round(threshold*1000000),domain_case_kpa=10.004,
                  prediction='5*sqrt(p1/120) L/min',flow_l_min=6,window_s=3,
                  script_sha256=m.sha(Path(__file__)),parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),physical_data=False)
    m.dump('counterexample_parameters.json',contract)
    c=dict(numeric=1,approved=1,rapid_available=1,r0=0,main=[200000,100000000],rapid=[200000,100000000],
           lut=[round(5*math.sqrt((10+i*.5)/120)*1000000) for i in range(381)])
    raw=contract['pressure_case_kpa'];raw_positive=6/(5*math.sqrt(raw/120))-1>.2
    quant_positive=6/(5*math.sqrt(round(raw*100)/100/120))-1>.2
    got=m.run_core([m.config_command(c),'F 36000 36000 162 3 0'])
    assert got==['OK','0'] and raw_positive and not quant_positive
    cases=[dict(case='pressure_rounding_near_threshold',raw_pressure_kpa=raw,pressure_sum_integer=36000,window=3,
                float_raw_decision=int(raw_positive),float_quantized_decision=int(quant_positive),integer_decision=0,
                meaning='leak comparison; scalar predicate, not a confirmed event')]
    c['main'][0]=contract['table_threshold_micro'];c['rapid'][0]=c['main'][0]
    x=6/(5*math.sqrt(p/120))-1
    assert x==threshold and not x>c['main'][0]/1000000
    got=m.run_core([m.config_command(c),'F 36075 36075 162 3 0'])
    assert got==['OK','1'] and flags(c,36075,36075,162,3)==1
    cases.append(dict(case='interpolation_near_threshold',raw_pressure_kpa=p,pressure_sum_integer=36075,window=3,
                      float_raw_decision=0,float_quantized_decision=0,integer_decision=1,
                      threshold_original=threshold,threshold_micro=c['main'][0],
                      meaning='interpolation shifts scalar decision even with quantized threshold in floating comparator'))
    c['main'][0]=200000;c['rapid'][0]=200000
    commands=[m.config_command(c)]+[f'U {t} {54*(t+1)} 12000 10000 0' for t in range(130)]+['U 130 7074 12000 1000 0']
    got=m.run_core(commands);last=list(map(int,got[-1].split()))
    assert raw_positive and contract['domain_case_kpa']>10 and round(contract['domain_case_kpa']*100)==1000 and last[0]==5 and last[2]==0
    cases.append(dict(case='strict_operating_domain_after_rounding',raw_pressure_kpa=contract['domain_case_kpa'],pressure_integer=1000,
                      float_raw_domain_valid=True,float_quantized_domain_valid=False,integer_status=5,
                      meaning='domain availability only; output 5 means operating_domain, not fault'))
    # Calibration must not depend on observations after monitoring begins.
    base=m.previous.previous.previous.parameters()['baseline']
    _,obs,counts,original=m.collect('normal',False,.3,51000,base)
    changed=m.Monitor(base['baseline']['reference'],base['baseline']['limits']['1'],original.run_id,
                      healthy_reference_approved=original.approved)
    for t,count in enumerate(counts):changed.update(t,int(count),obs[t,:2] if t<130 else [0.,200.])
    assert m.profile(original,base['baseline']['reference'])==m.profile(changed,base['baseline']['reference'])
    time_check=m.run_core([m.config_command(c),'U 4294967 0 12000 10000 0','U 0 54 12000 10000 0'])
    assert time_check[0:2]==['OK','ERR'] and time_check[2]!='ERR'
    m.dump('counterexample_acceptance.json',dict(passed=True,physical_data=False,strict_universal_float_equivalence=False,
        parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),counterexample_parameters_sha256=m.sha(m.OUT/'counterexample_parameters.json'),
        script_sha256=m.sha(Path(__file__)),cases=cases,
        additional_checks=['calibration_profile_independent_of_modified_future_measurements','millisecond_horizon_rejected_without_state_mutation'],
        scope='Three constructed boundary cases; no change to trajectory parameters or thresholds'))
    print('Three analytical boundary cases passed; universal float equivalence is false.')
if __name__=='__main__':main()
