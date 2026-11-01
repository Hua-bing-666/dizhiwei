"""Recheck frozen science/geometry and add explicit sampling-window arithmetic.

New receipts go to quality_review. Legacy scripts, evidence and receipts stay intact.
"""
from pathlib import Path
import json,hashlib,math,csv,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/quality_review';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute_readonly(relative):
    script=ROOT/relative;receipts=[];old_open=Path.open
    def redirected_open(path,mode='r',*args,**kwargs):
        if any(letter in mode for letter in 'wax') and path.resolve().is_relative_to(ROOT):
            destination=OUT/'rechecks'/path.relative_to(ROOT)
            destination.parent.mkdir(parents=True,exist_ok=True)
            receipts.append(destination.relative_to(ROOT).as_posix())
            return old_open(destination,mode,*args,**kwargs)
        return old_open(path,mode,*args,**kwargs)
    Path.open=redirected_open
    try:
        sys.path.insert(0,str(script.parent))
        exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
    finally:Path.open=old_open
    return {'script':relative,'script_sha256':sha(script),'status':'passed_in_original_scope','new_receipts':receipts}
def sampling():
    model=ROOT/'application/models/collection_review/bench_layout.json'
    capacity=json.loads(model.read_text(encoding='utf-8'))['collection_design']
    geometry=math.pi*capacity['inner_radius_mm']**2*capacity['inner_height_mm']/1000
    grid=ROOT/'simulation/hardware_results/range_grid.csv'
    rows=list(csv.DictReader(grid.open(encoding='utf-8')))
    hardware=json.loads((ROOT/'simulation/hardware_results/summary.json').read_text(encoding='utf-8'))
    maximum=max((float(r['c'])-hardware['healthy_c'])*math.sqrt(float(r['p1_kpa'])) for r in rows if math.isclose(float(r['c']),hardware['leak_max_c']))
    tests=[{'usable_fraction_assumption':fraction,'usable_capacity_ml_assumption':geometry*fraction,'maximum_seconds_with_1_25_margin':geometry*fraction/(maximum*1000/60*1.25),'twenty_seconds_fits_assumed_capacity':maximum*1000/60*20*1.25<=geometry*fraction,'thirty_seconds_fits_assumed_capacity':maximum*1000/60*30*1.25<=geometry*fraction} for fraction in [0.6,0.75,0.9,1.0]]
    pulse=[{'window_s':w,'pulse_step_l_min':60/(540*w),'phase_only_max_error_l_min':60/(540*w),'minimum_expected_pulses_at_0_3_l_min':0.3*540*w/60,'causal_window_mean_delay_s':w/2} for w in [1,5,10,20]]
    # Exhaustive ideal pulse phase: two boundaries of a constant-rate counter.
    cases=[]
    for flow in [0.3,1.85,3.0,4.34,5.0]:
        for w in [1,5,10,20]:
            ideal=flow*540*w/60;largest=0
            for j in range(1000):
                phase=j/1000;count=math.floor(ideal+phase)-math.floor(phase)
                measured=count*60/(540*w);largest=max(largest,abs(measured-flow))
            assert largest<=60/(540*w)+1e-12
            cases.append({'flow_l_min':flow,'window_s':w,'phases':1000,'maximum_phase_only_error_l_min':largest})
    result={'date':'2026-10-05','classification':'ideal_pulse_and_usable_capacity_sensitivity_not_calibration','physical_validation':False,'geometric_capacity_ml':geometry,'model_maximum_leak_l_min':maximum,'sample_20s_required_ml_with_1_25_margin':maximum*1000/60*20*1.25,'sample_30s_required_ml_with_1_25_margin':maximum*1000/60*30*1.25,'capacity_sensitivity':tests,'recommended_provisional_sample_s':20,'required_calibrated_usable_capacity_ml_min':math.ceil(maximum*1000/60*20*1.25),'pulse_windows':pulse,'ideal_constant_flow_phase_checks':cases,'phase_checks_total':20000,'limitations':['Usable fractions are assumptions, not measured capacity','No sensor pulse jitter, missed edges or MCU firmware modeled','Long experiments require independent drainage; cup only for discrete sampling','Ten-second windows create lag and are not reproduced by the Gaussian replay filter'],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),model,grid,ROOT/'simulation/hardware_results/summary.json']}}
    (OUT/'sampling_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'Capacity sensitivity:20s needs{result["sample_20s_required_ml_with_1_25_margin"]:.1f}mL usable; 20000 ideal pulse-phase checks passed; not calibrated.')
def main():
    results=[]
    for path in ['scripts/validate_diagnosis_review.py','scripts/check_hardware_interfaces.py','scripts/check_interface_protocol.py']:
        results.append(execute_readonly(path))
    if '--cad' in sys.argv:
        original=sys.argv[:];sys.argv=[str(ROOT/'scripts/validate_bench_model.py'),'--collection-review']
        try:results.append(execute_readonly('scripts/validate_bench_model.py'))
        finally:sys.argv=original
        results.append(execute_readonly('scripts/audit_bench_collection.py'))
    sampling()
    result={'date':'2026-10-05','status':'passed_scoped_rechecks','physical_validation':False,'rechecks':results,'legacy_outputs_overwritten':False,'source_sha256':sha(Path(__file__))}
    (OUT/('recheck_cad.json' if '--cad' in sys.argv else 'recheck_science.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
