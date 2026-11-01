"""Three-way integer diagnosis replay. No MCU or physical measurements."""
from pathlib import Path
import csv,hashlib,json,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from integer_diagnosis_reference import IntegerOracle,FIELDS
from integrated_monitor import Monitor
from compact_protocol import STATUS,PATTERN,EVENT_KIND,REASON,MISSING
from review_integrated_monitor import collect,CASES
from review_quality_intervals import inputs
import review_event_admission as previous
OUT=ROOT/'simulation/integer_diagnosis_review'
EXE=ROOT/'tmp/integer_diagnosis/core.exe'
CFG=dict(version='20261006-integer-diagnosis-v1',physical_data=False,
         old_seeds=list(range(45000,45004)),new_seeds=[51000,51001],sigmas=[.3,3.,10.],cases=CASES,
         pressure_unit_kpa=.01,lut_pressure_kpa=[10,200],lut_step_kpa=.5,
         parameter_scale=1000000,max_pulses_per_second=450,pulses_per_litre_assumption=540,
         main_window_s=10,rapid_window_s=3,main_confirmation=5,rapid_confirmation=2,
         monitor_start_index=130,calibration_on_host_only=True,parameter_tuning_on_test=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,obj):
    OUT.mkdir(exist_ok=True)
    (OUT/n).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def write(n,rows):
    with (OUT/n).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def freeze():
    previous.parameters()
    files=[Path(__file__),ROOT/'simulation/integer_diagnosis_reference.py',ROOT/'firmware/integer_diagnosis.c',ROOT/'firmware/integer_diagnosis.h',ROOT/'scripts/validate_integer_diagnosis.py',ROOT/'simulation/event_admission_review/frozen_parameters.json']
    dump('frozen_parameters.json',dict(config=CFG,sources={p.relative_to(ROOT).as_posix():sha(p) for p in files}))
def parameters():
    previous.parameters();p=json.loads((OUT/'frozen_parameters.json').read_text(encoding='utf-8'))
    assert p['config']==json.loads(json.dumps(CFG))
    for path,d in p['sources'].items():assert sha(ROOT/path)==d,path
    return p
def compile_core():
    EXE.parent.mkdir(exist_ok=True,parents=True)
    args=['D:/bin/gcc.exe','-std=c11','-Wall','-Wextra','-Werror','-Wconversion','-O2','-ftrapv','-DBUILD_HARNESS',str(ROOT/'firmware/integer_diagnosis.c'),'-o',str(EXE)]
    run=subprocess.run(args,capture_output=True,text=True)
    if run.returncode:raise RuntimeError(run.stderr)
    return args
def run_core(commands):
    r=subprocess.run([str(EXE)],input='\n'.join(commands)+'\n',capture_output=True,text=True,check=True)
    return r.stdout.splitlines()
def profile(monitor,reference):
    c=monitor.node.context
    if c is None:return dict(numeric=0,approved=int(monitor.approved),rapid_available=0,r0=0,main=[0,0],rapid=[0,0],lut=[0]*381)
    pressures=np.arange(10,200.01,.5)
    values=c['gain']*reference['a_l_min']*(pressures/100)**reference['n_fitted']
    main=np.maximum([.06,.6],6*c['scale']);rapid=monitor.rapid.threshold
    return dict(numeric=1,approved=int(monitor.approved),rapid_available=int(rapid is not None),
                r0=round(c['r0']*1000000),main=[round(x*1000000) for x in main],
                rapid=[round(x*1000000) for x in rapid] if rapid is not None else [0,0],lut=[round(x*1000000) for x in values])
def config_command(c):return 'C '+' '.join(map(str,[c['numeric'],c['approved'],c['rapid_available'],c['r0'],*c['main'],*c['rapid'],*c['lut']]))
def integer_input(t,count,pressure):
    finite=np.all(np.isfinite(pressure));in_range=finite and np.all((pressure>=0)&(pressure<=200))
    pp=[round(float(x)*100) if np.isfinite(x) else MISSING for x in pressure]
    return [t,int(count),*pp,0 if in_range else 2 if finite else 1]
def reference_fields(monitor):
    events={}
    for e in monitor.events:events.setdefault(e['t_s'],[]).append(e)
    main={r['t']:r for r in monitor.node.records};short={r['t']:r for r in monitor.rapid.records}
    labels=monitor.node.state['guarded_fast']['labels'];rows=[]
    for i,r in enumerate(monitor.records):
        t=r['t_s'];mask=0;reason=0
        for e in events.get(t,[]):
            mask|=1<<EVENT_KIND[e['kind']]
            if e['kind']=='measurement_quality':reason=REASON[e['reason']]
        sr=short.get(t)
        rows.append([STATUS[r['measurement_status']],PATTERN[r['diagnostic_pattern']],int(r['rapid_window_valid']),int(r['rapid_attention_active']),int(bool(sr and sr['attention'] and monitor.approved)),labels[i],mask,reason,round(main[t]['flow_q10']*1000) if main[t]['flow_q10'] is not None else MISSING])
    return rows
def quantized_monitor(obs,counts,original,reference,limits):
    m=Monitor(reference,limits,original.run_id,healthy_reference_approved=original.approved)
    for t,count in enumerate(counts):
        pp=np.array([round(float(v)*100)/100 if np.isfinite(v) else v for v in obs[t,:2]])
        m.update(t,int(count),pp)
        if t==129:
            m.node.context=original.node.context
            m.rapid.baseline=original.rapid.baseline;m.rapid.threshold=original.rapid.threshold;m.rapid.scale=original.rapid.scale
    return m
def evaluate():
    parameters();compile_core();base=previous.previous.previous.parameters()['baseline']
    ref=base['baseline']['reference'];limits=base['baseline']['limits']['1'];rows=[];differences=[];profiles=[];examples={}
    for dataset,seeds in [('regression',CFG['old_seeds']),('unused_seeds',CFG['new_seeds'])]:
        for sigma in CFG['sigmas']:
            for scene,quality in CASES:
                for seed in seeds:
                    _,obs,counts,monitor=collect(scene,quality,sigma,seed,base)
                    c=profile(monitor,ref);profiles.append(dict(dataset=dataset,scene=scene,sigma=sigma,seed=seed,config=c))
                    values=[integer_input(t,count,obs[t,:2]) for t,count in enumerate(counts)]
                    commands=[config_command(c)]+['U '+' '.join(map(str,v)) for v in values]
                    actual=run_core(commands);assert actual[0]=='OK',(scene,sigma,seed)
                    oracle=IntegerOracle(c);expected=[oracle.update(*v) for v in values]
                    assert actual[1:]==[' '.join(map(str,v)) if v is not None else 'ERR' for v in expected]
                    assert all(v is not None for v in expected)
                    integer=expected[130:];floating=reference_fields(monitor)
                    quant=reference_fields(quantized_monitor(obs,counts,monitor,ref,limits))
                    assert len(integer)==len(floating)==len(quant)
                    stats={}
                    for name,left,right in [('input_quantization',floating,quant),('integer_approximation',quant,integer),('end_to_end',floating,integer)]:
                        mask=[a!=b for a,b in zip(left,right)];stats[name+'_different_records']=sum(mask)
                        stats[name+'_event_mask_differences']=sum(a[6]!=b[6] for a,b in zip(left,right))
                        stats[name+'_pattern_differences']=sum(a[1]!=b[1] for a,b in zip(left,right))
                        for j,flag in enumerate(mask):
                            if flag:differences.append(dict(dataset=dataset,scene=scene,sigma=sigma,seed=seed,t_s=j+130,comparison=name,fields=[FIELDS[k] for k,(a,b) in enumerate(zip(left[j],right[j])) if a!=b],left=left[j],right=right[j]))
                    row=dict(dataset=dataset,scene=scene,sigma=sigma,seed=seed,records=len(integer),c_oracle_records=len(expected),c_oracle_equal=True,config_sha256=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),**stats)
                    rows.append(row)
                    if scene in ['pulse8','counter_reset'] and sigma==.3 and seed==51000:examples[scene]=dict(t_s=list(range(130,len(obs))),original=floating,quantized=quant,integer=integer)
    write('results.csv',rows);dump('differences.json',differences);dump('profiles.json',profiles);dump('examples.json',examples)
    dump('results_summary.json',dict(parameters_sha256=sha(OUT/'frozen_parameters.json'),physical_data=False,runs=len(rows),records=sum(r['records'] for r in rows),c_oracle_records=sum(r['c_oracle_records'] for r in rows),
                                   datasets={n:sha(OUT/n) for n in ['results.csv','differences.json','profiles.json','examples.json']},
                                   totals={key:sum(r[key] for r in rows) for key in stats}))
    print('216 trajectories evaluated. Differences preserved; independent acceptance pending.',flush=True)
if __name__=='__main__':
    if '--freeze' in sys.argv:freeze()
    else:evaluate()
