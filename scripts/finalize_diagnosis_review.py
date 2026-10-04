"""Freeze A06/A07 scoped evidence after numerical, image and preservation checks."""
from pathlib import Path
import csv,hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/diagnosis_review';FIG=ROOT/'application/figures/diagnosis_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
def close(a,b):assert np.allclose(a,b,rtol=1e-11,atol=1e-11)

def main():
    validation=read(DATA/'validation.json');summary=read(DATA/'summary.json');proof=read(FIG/'figure_provenance.json');layout=read(DATA/'figure_layout_checks.json')
    assert validation['status']=='passed_with_uncalibrated_simulation_scope' and not validation['physical_validation']
    assert layout['status']=='passed' and len(layout['figures'])==len(proof['figures'])==5
    for record in (validation,summary,proof):
        for path,digest in record['source_sha256'].items():assert sha(ROOT/path)==digest,('Stale source',path)
    assert sha(ROOT/'scripts/verify_diagnosis_figures.mjs')==layout['source_sha256']['script']
    assert sha(FIG/'figure_provenance.json')==layout['source_sha256']['provenance']
    for image in layout['figures']:
        assert not image['outside'] and not image['overlaps'] and image['minimumFontPtAt425pt']>=9
        figure=next(f for f in proof['figures'] if f['name']==image['name'])
        for ext,digest in image['sha256'].items():assert sha(FIG/(image['name']+'.'+ext))==digest==figure['sha256'][ext]
    # Independently verify that the figure provenance actually points to the
    # plotted data, including counts, intervals and annotation coordinates.
    nseries=0;nannotations=0
    with (ROOT/'simulation/hardware_results/range_grid.csv').open(encoding='utf-8',newline='') as f:grid=list(csv.DictReader(f))
    for fig in proof['figures']:
        for curve in fig['series']:
            if fig['name']=='range_and_measurement':
                if curve['curve']=='grid_flow':close(curve['q'],[float(g['q_a_l_min']) for g in grid])
                else:close(curve['dp_kpa'],.8*np.array(curve['q'])**2)
            elif fig['name']=='early_reference_example':
                trace=summary['traces'][curve['trace_key']];close(curve['t'],trace['t']);close(curve['severity_percent'],100*np.array(trace['severity']))
            elif fig['name']=='noise_outcomes':
                groups=[next(g for g in summary['groups'] if g['kind']==curve['kind'] and g['method']==curve['method'] and g['pressure_sigma_kpa']==sigma) for sigma in curve['sigma']]
                close(curve['values'],[g['early_trials'] for g in groups]);close(curve['ci_low_counts'],[20*g['early_wilson95'][0] for g in groups]);close(curve['ci_high_counts'],[20*g['early_wilson95'][1] for g in groups])
            elif fig['name']=='failure_counterexamples':
                key='leak_0.3' if curve['curve']=='leak_unknown_k' else 'drift_0.3';trace=summary['traces'][key]
                expected=100*(np.array(trace['k'])/trace['k0']-1) if key=='leak_0.3' else np.array(trace['r'])-trace['r0'];close(curve['t'],trace['t']);close(curve['values'],expected)
            elif fig['name']=='bounded_error_margin':
                groups=[g for g in summary['interval_summary'] if g['flow_error_basis']==curve['basis']]
                close(curve['extra_bound'],[g['extra_per_channel_bound_kpa'] for g in groups]);close(curve['values'],[g[curve['quantity']] for g in groups])
            else:raise AssertionError('Unknown figure')
            nseries+=1
        for a in fig['annotations']:
            trace=summary['traces'][a['kind']+'_0.3'];key='first_correct_s' if a['label']=='first_correct' else 'critical_s';assert a['t']==trace[key];close(a['y'],100*trace['severity'][a['t']]);nannotations+=1
    preserved_names=['deliverables/大创申报书_模板填写稿.docx','deliverables/大创申报书_模板审阅版.pdf','deliverables/项目书审阅版.pdf','deliverables/立项答辩.pptx','deliverables/立项答辩审阅版.pdf','deliverables/index.html','deliverables/研究与答辩资料.html','deliverables/台架三维结构交互模型.html','deliverables/台架三维结构交互模型_收集优化候选版.html','deliverables/三维分项验收记录.json','application/references.json','simulation/diagnosis_feasibility.py','docs/三维台架建模论证与本轮验收.md']
    prefixes=['application/models/','application/figures/collection_review/','simulation/diagnosis_results/','simulation/hardware_results/']
    tracked=subprocess.run(['git','ls-tree','-r','--name-only','-z','HEAD'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').split('\0')
    names=sorted(set(preserved_names+[p for p in tracked if any(p.startswith(x) for x in prefixes)]));unchanged=[]
    for path in names:
        prior=subprocess.run(['git','show','HEAD:'+path],cwd=ROOT,capture_output=True,check=True).stdout
        assert (ROOT/path).read_bytes()==prior,('Unexpected scope change',path)
        unchanged.append({'path':path,'sha256':sha(ROOT/path)})
    sources=read(DATA/'source_checks.json');assert len(sources['sources'])==4 and not sources['physical_data']
    progress=read(ROOT/'deliverables/分项验收进度.json');before=next(t for t in progress['tasks'] if t['id']=='A05').copy()
    assert before['status']=='candidate_internal_checks_passed_physical_unverified'
    progress.update(date='2026-10-04',scope='A05 concept package plus A06/A07 uncalibrated model and diagnosis evidence; application integration pending',plan_sha256=sha(ROOT/'docs/三阶段分项执行与验收标准.md'),this_turn='A06/A07 scoped numerical checks and five evidence figures passed; no physical validation',next='A04/A08 hardware interfaces and LoRa communication evidence')
    for task in progress['tasks']:
        if task['id'] in ('A06','A07'):task.update(status='candidate_internal_checks_passed_physical_unverified',record='deliverables/仿真分项验收记录.json')
    assert next(t for t in progress['tasks'] if t['id']=='A05')==before
    write(ROOT/'deliverables/分项验收进度.json',progress)
    report={'date':'2026-10-04','status':'passed_with_uncalibrated_model_scope','task_ids':['A06','A07'],'physical_validation':False,'application_integration_complete':False,'numerical_checks':validation['checks'],'figure_checks':[{'name':f['name'],'text_count':f['textCount'],'outside':f['outside'],'overlaps':f['overlaps'],'minimum_font_pt_at_425pt':f['minimumFontPtAt425pt'],'sha256':f['sha256']} for f in layout['figures']],'plotted_series_checked':nseries,'annotation_coordinates_checked':nannotations,'manual_png_review':{'all_five_pngs_viewed':True,'independent_external_review':False,'checks':['axes, units and population definitions','legend clear of data, titles and count labels','reference/detection point coordinates and leader endpoints','true numeric spacing on bounded-error x axis','caption and x-axis clearance; simulation identity'],'repairs':['shared legends outside plotting areas','counts moved above confidence interval upper ends','counterexample legend removed from overlapping curves','bounded-error axis changed from equal-spaced ordinal positions to actual kPa positions','footer space increased']},'limitations':['uncalibrated concentrated hydraulic model','20 paired random streams reused across scenario/sigma cells','Gaussian noise not sensor precision; pulses not dynamically simulated','static box checks only for target feature, not full classifier','unknown normal load observationally identical to leak','fixed thresholds not tuned at equal false-alarm rates','no measured LoRa, timing or power; two simulations not merged','Word/PDF/PPT integration pending'],'original_artifacts_unchanged':unchanged,'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),DATA/'validation.json',DATA/'figure_layout_checks.json',DATA/'source_checks.json',FIG/'figure_provenance.json',ROOT/'docs/仿真建模与诊断证据分项验收.md',ROOT/'docs/三阶段分项执行与验收标准.md']}}
    write(ROOT/'deliverables/仿真分项验收记录.json',report)
    delivery=read(ROOT/'deliverables/交付检查.json');delivery['staged_diagnosis_review']={'task_ids':['A06','A07'],'status':report['status'],'record':'仿真分项验收记录.json','report':'../docs/仿真建模与诊断证据分项验收.md','figures':5,'trials':480,'paired_method_records':960,'physical_validation':False,'application_integration_complete':False};write(ROOT/'deliverables/交付检查.json',delivery)
    print(f'A06/A07: {nseries} plotted series, {nannotations} annotation coordinates; 5 SVG/PNG pairs; {len(names)} original artifacts preserved; A05 status retained.')
if __name__=='__main__':main()
