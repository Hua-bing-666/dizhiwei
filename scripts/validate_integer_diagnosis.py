"""Separate host input/resource, core boundary and replay acceptance gates."""
from pathlib import Path
from fractions import Fraction
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
import review_integer_diagnosis as m
from integer_diagnosis_reference import IntegerOracle,flags

def finish(name,checks,**kwargs):
    m.dump(name+'_acceptance.json',dict(passed=True,physical_data=False,checks=checks,
        parameters_sha256=m.sha(m.OUT/'frozen_parameters.json'),validator_sha256=m.sha(Path(__file__)),**kwargs))
def example(**kwargs):
    c=dict(numeric=1,approved=1,rapid_available=1,r0=800000,main=[60000,600000],rapid=[60000,600000],lut=[6000000]*381)
    c.update(kwargs);return c
def check_sequence(c,values):
    oracle=IntegerOracle(c);outputs=[oracle.update(*v) for v in values]
    commands=[m.config_command(c)]+['U '+' '.join(map(str,v)) for v in values]
    got=m.run_core(commands);want=['OK']+['ERR' if r is None else ' '.join(map(str,r)) for r in outputs]
    assert got==want
    return outputs
def prefix():return [[t,54*(t+1),12000,10000,0] for t in range(130)]
def inputs():
    m.parameters();args=m.compile_core();checks=[]
    c=example();out=check_sequence(c,[[0,54,12000,10000,0],[0,54,12000,10000,0],[2,162,12000,10000,0],[1,108,12000,10000,0],[2,559,12000,10000,0],[2,162,12000,10000,0]])
    assert out[1] is out[2] is out[4] is None and out[-1] is not None
    checks.append('duplicate_gap_and_excess_counter_delta_rejected_without_mutation')
    out=check_sequence(c,[[0,0,-1,10000,0],[0,0,0,20001,0],[0,0,20000,20000,0]])
    assert out[:2]==[None,None] and out[2] is not None;checks.append('representation_bounds_checked_before_state_update')
    out=check_sequence(c,prefix()+[[130,0,12000,10000,0]]+[[t,54*(t-130),12000,10000,0] for t in range(131,142)])
    assert out[130][0]==4 and out[130][7]==3 and out[140][0]==0
    checks.append('counter_rollback_rebuilds_window_and_emits_quality_reason')
    sizes=list(map(int,m.run_core(['M'])[0].split()));assert sizes[3]<=8192 and sizes[0]+sizes[1]+sizes[3]<12288
    checks.append('fixed_capacity_layout_and_host_size_observation')
    # Exact upper bounds, not a measured MCU stack or whole-program budget.
    bounds=dict(leak_left=4500*10**12,leak_right=90*50000000*9000000,
                resistance_left=200000*81*10*1000000,resistance_right=100*4500**2*1000000000)
    assert max(bounds.values())<2**63
    checks.append('signed_64_bit_products_bounded_by_input_and_configuration_contract')
    invalid=[example(main=[8000001,600000]),example(r0=1000000000,main=[60000,1]),example(lut=[0]*381),example(lut=[6000000]*380+[5999999])]
    assert m.run_core([m.config_command(c) for c in invalid])==['ERR']*len(invalid)
    checks.append('configuration_zero_decrease_or_out_of_contract_threshold_rejected')
    finish('input_resource',checks,compile_command=args,host_sizeof=dict(state=sizes[0],configuration=sizes[1],candidate_slot=sizes[2],candidate_storage=sizes[3]),
           arithmetic_max_products=bounds,scope='Host widths, static schema and arithmetic; no target map, ISR or persistence',
           documentation='docs/MCU输入与整数诊断_分项执行计划.md')
    print(f'10A passed: {len(checks)} input/resource checks.',flush=True)
def boundary():
    m.parameters();m.compile_core();checks=[];total=0
    leak=example(r0=0,main=[200000,100000000],rapid=[200000,100000000],lut=[5000000]*381)
    rr=example(r0=0,main=[8000000,1000000],rapid=[8000000,1000000],lut=[1000000]*381)
    for c,values in [(leak,[(36000,36000,d,3,r) for d in [161,162,163] for r in [0,1]]),
                     (rr,[(a,36000,27,3,r) for a in [36299,36300,36301] for r in [0,1]])]:
        commands=[m.config_command(c)]+[f'F {a} {b} {d} {n} {r}' for a,b,d,n,r in values]
        wanted=['OK']+[str(flags(c,a,b,d,n,bool(r))) for a,b,d,n,r in values]
        assert m.run_core(commands)==wanted;total+=len(values)
    assert flags(leak,36000,36000,162,3)==0 and flags(rr,36300,36000,27,3)==0
    checks.append('strict_threshold_equality_and_one_unit_either_side')
    for issue,reason in [(1,1),(2,2),(3,4)]:
        pp=m.MISSING if issue==1 else 25000 if issue==2 else 12000
        out=check_sequence(example(),prefix()+[[130,7074,pp,10000,issue]]+[[t,54*(t+1),12000,10000,0] for t in range(131,141)])
        assert out[130][0]==3 and out[130][7]==reason and out[130][3]==0 and out[140][0]==0
    checks.append('missing_raw_range_and_timing_quality_rebuild_both_windows')
    out=check_sequence(example(),prefix()+[[t,54*(t+1),12000,1000,0] for t in range(130,140)])
    assert out[130][0]==5 and all(r[2]==0 for r in out[130:]);checks.append('downstream_pressure_strict_domain_boundary')
    out=check_sequence(example(),prefix()+[[t,54*130+4*(t-129),12000,10000,0] for t in range(130,144)])
    assert out[-1][0]==5;checks.append('flow_below_half_litre_domain_is_not_normal_evidence')
    for c,status in [(example(approved=0),1),(example(numeric=0,rapid_available=0,lut=[0]*381),2)]:
        out=check_sequence(c,prefix()+[[t,54*130+108*(t-129),12000,10000,0] for t in range(130,145)])
        assert all(r[0]==status and r[1]==4 and not r[2] and not r[3] and r[6] in [0,2] for r in out[130:])
    checks.append('missing_health_permission_or_numeric_configuration_suppresses_diagnostic_events')
    out=check_sequence(example(),prefix()+[[t,54*130+108*(t-129),12000,10000,0] for t in range(130,145)])
    rt=[t for t,r in enumerate(out) if r[6]&(1<<3)];mt=[t for t,r in enumerate(out) if r[6]&(1<<4)]
    assert rt and mt and rt[0]<mt[0] and out[rt[0]][1]==0
    checks.append('rapid_attention_precedes_main_confirmation_without_becoming_fault_label')
    # Extreme valid arithmetic operands execute with signed-overflow trapping.
    extreme=example(r0=0,main=[8000000,1000000000],rapid=[8000000,1000000000],lut=[50000000]*381)
    commands=[m.config_command(extreme)]+[f'F {a} {b} {450*n} {n} {r}' for n in [3,10] for a,b in [(0,1000*n),(20000*n,1000*n),(20000*n,20000*n)] for r in [0,1]]
    wanted=['OK']+[str(flags(extreme,a,b,450*n,n,bool(r))) for n in [3,10] for a,b in [(0,1000*n),(20000*n,1000*n),(20000*n,20000*n)] for r in [0,1]]
    assert m.run_core(commands)==wanted;total+=len(commands)-1
    check_sequence(example(),[[t,450*(t+1),20000,20000,0] for t in range(145)])
    checks.append('extreme_valid_products_and_maximum_rate_execute_without_overflow_trap')
    finish('boundary',checks,exact_comparator_vectors=total,scope='Portable host C against independent Fraction oracle; no target execution')
    print(f'10B passed: {len(checks)} boundary groups, {total} exact comparator vectors.',flush=True)
def replay():
    m.parameters()
    for n in ['input_resource','boundary']:assert json.loads((m.OUT/(n+'_acceptance.json')).read_text(encoding='utf-8'))['passed']
    names=['results.csv','differences.json','profiles.json','examples.json','results_summary.json']
    saved={n:(m.OUT/n).read_bytes() for n in names}
    m.evaluate()
    for n,data in saved.items():assert (m.OUT/n).read_bytes()==data,n
    rows=list(csv.DictReader((m.OUT/'results.csv').open(encoding='utf-8')))
    assert len(rows)==216 and sum(r['dataset']=='regression' for r in rows)==144 and sum(r['dataset']=='unused_seeds' for r in rows)==72
    assert all(r['c_oracle_equal']=='True' for r in rows)
    summary=json.loads((m.OUT/'results_summary.json').read_text(encoding='utf-8'))
    diff=json.loads((m.OUT/'differences.json').read_text(encoding='utf-8'))
    assert len(diff)==sum(v for k,v in summary['totals'].items() if k.endswith('_different_records'))
    finish('replay',['216_trajectories_and_all_artifacts_reproduced','144_regression_and_72_unused_seed_runs','all_C_outputs_equal_independent_integer_oracle','all_three_way_differences_preserved'],
           runs=216,records=summary['records'],c_oracle_records=summary['c_oracle_records'],differences=summary['totals'],strict_output_equivalence_on_this_dataset=summary['totals']['end_to_end_different_records']==0,
           datasets={n:m.sha(m.OUT/n) for n in names})
    print('10C reproduced all 216 trajectories; approximation differences are reported separately.',flush=True)
if __name__=='__main__':{'A':inputs,'B':boundary,'C':replay}[sys.argv[1]]()
