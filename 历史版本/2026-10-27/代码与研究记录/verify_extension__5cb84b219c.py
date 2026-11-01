"""Independent conservation, aggregation, exported-series and layout checks."""
from pathlib import Path
import json,csv,hashlib,sys,math
import numpy as np
from PIL import Image
from docx import Document
B=Path(__file__).resolve().parents[1];E=B/'evidence'
sys.path.insert(0,str(B/'code/snapshot'))
import review_operating_reference as o
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(name):return list(csv.DictReader((E/name).open(encoding='utf-8-sig')))
def ci95(k,n):
    z=1.959963984540054;p=k/n
    return [(2*k+z*z+s*z*math.sqrt(z*z+4*k*(1-p)))/(2*(n+z*z)) for s in [-1,1]]
D=json.loads((E/'extension_report.json').read_text(encoding='utf-8'))
P=json.loads((E/'frozen_parameters.json').read_text(encoding='utf-8'))
SP=json.loads((E/'sampling_frozen_parameters.json').read_text(encoding='utf-8'))
rr=rows('amplitude_trials.csv');assert len(rr)==3000
assert len({(r['scene'],r['amplitude'],r['sigma'],r['seed']) for r in rr})==3000
for g in D['amplitude_groups']:
    subset=[r for r in rr if (r['scene'],float(r['sigma']),float(r['amplitude']))==(g['scene'],g['sigma'],g['amplitude'])]
    k=sum(r['correct']=='True' for r in subset)
    assert len(subset)==100 and k==g['correct']
    assert np.allclose(ci95(k,100),g['ci95'],atol=1e-14)
    for r in subset:
        assert (r['outcome']=='correct')==(r['correct']=='True')
        if r['first_post_s']:assert 360<=int(r['first_post_s'])<=600
control=rows('amplitude_healthy_controls.csv');assert len(control)==300
for g in D['amplitude_healthy_controls']:
    subset=[r for r in control if float(r['sigma'])==g['sigma']]
    assert sum(r['any_false']=='True' for r in subset)==g['false_trials']
# Closed-form independent inverse from Ps=Q²(C^-2+R+Rc).
q0=math.sqrt(120/(.28**-2+.8+.4));max_parameter_error=0.
for r in rows('amplitude_parameters.csv'):
    a=float(r['target_amplitude']);q=q0*(1+a if r['scene']=='leak' else 1-a)
    parameter=(120/q**2-1.2)**-.5-.28 if r['scene']=='leak' else 120/q**2-.28**-2-.4
    max_parameter_error=max(max_parameter_error,abs(parameter-float(r['terminal_parameter'])))
    assert abs(float(r['realized_amplitude'])-a)<1e-12 and abs(float(r['terminal_flow_l_min'])-q)<1e-12
assert max_parameter_error<1e-10
Z=np.load(E/'extension_curves.npz');max_frontend_error=0.
for scene in ['normal','leak','restriction']:
    tr=o.trajectory(scene,.5)
    for index in [0,50]:
        seed=62000+index
        obs=tr['values']+np.random.default_rng(seed).normal(0,[3.,3.,.02],tr['values'].shape)
        cumulative=np.floor((seed*.6180339887498949)%1+np.cumsum(np.maximum(obs[:,2],0))*9).astype(np.int64)
        for t in [130,359,400,540,600]:
            pressure=float(np.mean(obs[t-9:t+1,1]));flow=(cumulative[t]-cumulative[t-10])/90
            max_frontend_error=max(max_frontend_error,abs(pressure-Z[scene+'_p1'][index,t]),abs(flow-Z[scene+'_q10'][index,t]))
assert max_frontend_error<1e-12
sr=rows('sampling_extension_trials.csv');assert len(sr)==256
for g in D['sampling_groups']:
    subset=[r for r in sr if r['scene']==g['scene'] and int(r['period'])==g['period']]
    assert len(subset)==16*g['period']
    perseed_reads=[];perseed_leads=[]
    for seed in range(63000,63016):
        ss=[r for r in subset if int(r['seed'])==seed]
        perseed_reads.append(np.mean([int(r['pressure_reads']) for r in ss]))
        lead=[int(r['critical_s'])-int(r['first_post_s']) for r in ss if r['early']=='True']
        perseed_leads.append(np.mean(lead))
        assert all(0<=int(r['pressure_reads'])<=471 for r in ss)
    assert np.isclose(np.median(perseed_reads),g['pressure_reads_median'])
    assert np.isclose(np.median(perseed_leads),g['lead_median_s'])
    assert np.allclose(np.quantile(perseed_reads,[.25,.75]),g['pressure_reads_iqr'])
    assert np.allclose(np.quantile(perseed_leads,[.25,.75]),g['lead_iqr_s'])
assert sha(B/'code/snapshot/sampling_quality_runtime.py')==SP['sources']['simulation/sampling_quality_runtime.py']
F=json.loads((E/'figure_checks.json').read_text(encoding='utf-8'));assert len(F)==6
figchecks=[]
for f in F:
    for ext in ['png','pdf','svg']:assert sha(B/'figures'/(f['name']+'.'+ext))==f['sha256'][ext]
    im=Image.open(B/'figures'/(f['name']+'.png'));assert min(im.info['dpi'])>599
    assert f['min_font_pt']>=7 and f['gridlines'] is False and f['canvas_check'] is True
    assert '<text' in (B/'figures'/(f['name']+'.svg')).read_text(encoding='utf-8')
    figchecks.append(dict(name=f['name'],pixels=im.size,min_font_pt=f['min_font_pt']))
for s in F[0]['data']:
    lo,mid,hi=np.quantile(Z[s['scene']+'_'+s['quantity']],[.025,.5,.975],axis=0)
    assert np.array_equal(s['median'],mid) and np.array_equal(s['low'],lo) and np.array_equal(s['high'],hi)
baseline=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
for s in F[1]['data']:
    gg=[next(g for g in baseline['groups'] if (g['batch'],g['scene'],g['sigma'],g['method'])==('holdout100',s['scene'],sigma,s['method'])) for sigma in [.3,3.,10.]]
    assert s['values']==[g[s['metric']] for g in gg]
    key='false_ci95' if s['metric']=='false_trials' else 'early_ci95'
    assert np.allclose(s['ci95_percent'],np.array([g[key] for g in gg])*100)
for s in F[2]['data']:
    gg=[next(g for g in D['amplitude_groups'] if (g['scene'],g['sigma'],g['amplitude'])==(s['scene'],s['sigma'],a)) for a in [.05,.1,.15,.2,.3]]
    assert s['correct']==[g['correct'] for g in gg]
for s in F[5]['data']:
    gg=[next(g for g in D['sampling_groups'] if g['scene']==s['scene'] and g['period']==p) for p in [1,2,5]]
    assert s['values']==[g[s['quantity']] for g in gg]
oldZ=np.load(E/'trace_data.npz')
for s in F[3]['data']:
    arr=oldZ['leak_k_3'] if s['panel']=='a' else oldZ['drift_r_3'] if s['curve']=='漂移' else oldZ['normal_r_3']
    lo,mid,hi=np.quantile(arr,[.025,.5,.975],axis=0)
    assert np.array_equal(s['median'],mid) and np.array_equal(s['low'],lo) and np.array_equal(s['high'],hi)
timing=rows('timing_examples.csv');oldtrials=rows('paired_method_results.csv')
for s in F[4]['data']:
    r=next(r for r in timing if r['scene']==s['scene'] and r['method']==s['method'])
    original=next(r for r in oldtrials if (r['batch'],r['scene'],float(r['sigma']),r['seed'],r['method'])==('holdout100',s['scene'],3.,'61000',s['method']))
    assert r['first_correct_s']==original['first_correct_s'] and r['early_valid']==original['early_valid']=='True'
    assert s['confirmation_s']==int(r['first_correct_s']) and s['reference_s']==int(r['critical_s'])
docpath=B/'第八部分_扩展仿真图文稿.docx';doc=Document(docpath);assert len(doc.inline_shapes)==4
names=[f['name'] for f in F[:4]]
for shape,name in zip(doc.inline_shapes,names):
    rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    assert hashlib.sha256(doc.part.related_parts[rid].blob).hexdigest()==sha(B/'figures'/(name+'.png'))
layout=json.loads((E/'document_layout.json').read_text(encoding='utf-8'))
assert layout['pages']==3 and layout['document_sha256']==sha(docpath)
assert all(p['start_page']==p['end_page'] for p in layout['paragraphs'])
assert all(s in '\n'.join(p.text for p in doc.paragraphs) for s in ['图8-1','图8-2','图8-3','图8-4','3000条故障轨迹'])
report=dict(passed=True,amplitude_records_checked=3000,healthy_controls_checked=300,sampling_replays_checked=256,
    independent_closed_form_parameter_max_error=max_parameter_error,independent_frontend_max_error=max_frontend_error,
    paired_seed_dependence_retained=True,phase_aggregation_per_seed=True,parameters_retuned=False,
    six_figures_exported=True,figure_checks=figchecks,docx_pages=3,no_paragraph_split=True,
    docx_sha256=sha(docpath),physical_data=False,physical_print_test=False)
(E/'expanded_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
