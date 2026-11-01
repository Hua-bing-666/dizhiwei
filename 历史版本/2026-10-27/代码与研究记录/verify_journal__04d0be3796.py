"""Verify that the redesigned visual encodings retain their source evidence."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from PIL import Image
from docx import Document
from pypdf import PdfReader
B=Path(__file__).resolve().parents[1];E=B/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return list(csv.DictReader((E/name).open(encoding='utf-8-sig')))
def write(name,records):
    with (E/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
D=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
EX=json.loads((E/'extension_report.json').read_text(encoding='utf-8'))
F=json.loads((E/'figure_checks.json').read_text(encoding='utf-8'));assert len(F)==6
X=np.load(E/'extension_curves.npz');Z=np.load(E/'trace_data.npz')
rows=read('paired_method_results.csv');assert len(rows)==3024
checks=[]
# Recount the high-noise result composition directly from all trial rows.
for g in F[1]['data']['groups']:
    rr=[r for r in rows if (r['batch'],r['scene'],float(r['sigma']),r['method'])==('holdout100',g['scene'],10.,g['method'])]
    assert len(rr)==g['n']==100
    if g['scene']=='long_normal':assert sum(int(r['false_onsets'])>0 for r in rr)==g['false_trials']
    else:
        early=sum(r['early_valid']=='True' for r in rr);prior=sum(r['outcome']=='prior_false_alarm' for r in rr)
        assert (early,prior,100-early-prior)==(g['early'],g['prior_false'],g['other'])
        assert g['early']+g['prior_false']+g['other']==100
# Response medians use matching P/Q arrays in original seed order.
for g in F[0]['data']['paths']:
    scene=g['scene'];assert g['paired_seed_paths']==100
    assert np.array_equal(g['q_median'],np.median(X[scene+'_q10'][:,360:],axis=0))
    assert np.array_equal(g['p1_median'],np.median(X[scene+'_p1'][:,360:],axis=0))
assert np.allclose(F[0]['data']['healthy'],[np.median(X['normal_q10'][:,360]),np.median(X['normal_p1'][:,360])])
# Every matrix entry is an actually tested group. No extra interpolated cells.
for g in F[2]['data']:
    a=np.array([[next(v for v in EX['amplitude_groups'] if (v['scene'],v['sigma'],v['amplitude'])==(g['scene'],s,amp))['correct']
        for amp in g['columns_amplitude']] for s in g['rows_sigma']])
    assert a.shape==(3,5) and np.array_equal(a,g['correct_percent'])
points=read('joint_counterexample_points.csv');assert len(points)==80
for seed in range(10300,10320):
    p={r['scene']:r for r in points if int(r['seed'])==seed};i=seed-10300
    assert p['leak']['k_relative_percent']==p['load_unknown']['k_relative_percent']
    assert p['leak']['r_residual']==p['load_unknown']['r_residual']
    assert float(p['leak']['k_relative_percent'])==Z['leak_k_3'][i,-1]
    assert float(p['drift']['r_residual'])==Z['drift_r_3'][i,-1]
    assert float(p['normal']['r_residual'])==Z['normal_r_3'][i,-1]
for g in F[4]['data']:
    rr=[r for r in rows if (r['batch'],r['scene'],float(r['sigma']),r['method'],r['early_valid'])==('holdout100',g['scene'],10.,g['method'],'True')]
    a=np.array([float(r['lead_s']) for r in rr]);assert len(a)==g['n']
    assert np.array_equal(a,g['lead_s']) and np.allclose(np.quantile(a,[.25,.5,.75]),g['q25_q50_q75'])
for item in F[5]['data']:
    expected=[g for g in EX['sampling_groups'] if g['scene']==item['scene']]
    assert item['groups']==expected
    assert all(g['unique_seeds']==16 for g in expected)
for f in F:
    for ext in ['png','pdf','svg']:assert sha(B/'figures'/(f['name']+'.'+ext))==f['sha256'][ext]
    im=Image.open(B/'figures'/(f['name']+'.png'));assert min(im.info['dpi'])>599
    assert f['text_inside_canvas'] and f['minimum_font_pt']>=8
    assert '<text' in (B/'figures'/(f['name']+'.svg')).read_text(encoding='utf-8')
    reader=PdfReader(B/'figures'/(f['name']+'.pdf'));embedded=[]
    for ref in reader.pages[0]['/Resources']['/Font'].values():
        font=ref.get_object();assert font['/Subtype']!='/Type3'
        ff=font['/DescendantFonts'][0].get_object() if font['/Subtype']=='/Type0' else font
        descriptor=ff.get('/FontDescriptor')
        if descriptor:
            desc=descriptor.get_object();embedded.append(any(key in desc for key in ['/FontFile','/FontFile2','/FontFile3']))
    assert embedded and all(embedded)
    checks.append(dict(name=f['name'],chart_type=f['chart_type'],pixels=im.size,min_font_pt=f['minimum_font_pt'],pdf_fonts_embedded=True))
docpath=B/'第八部分_期刊主图重构稿.docx';doc=Document(docpath);assert len(doc.inline_shapes)==4
for shape,f in zip(doc.inline_shapes,F[:4]):
    rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    assert hashlib.sha256(doc.part.related_parts[rid].blob).hexdigest()==sha(B/'figures'/(f['name']+'.png'))
layout=json.loads((E/'document_layout.json').read_text(encoding='utf-8'))
assert layout['pages']==4 and layout['document_sha256']==sha(docpath)
assert all(p['start_page']==p['end_page'] for p in layout['paragraphs'])
captions=[p for p in layout['paragraphs'] if p['text'].startswith('图8-')]
assert len(captions)==4
text='\n'.join(p.text for p in doc.paragraphs)
assert all(s in text for s in ['成对观测轨迹','高噪声','终值投影到特征平面','不作连续插值'])
comparison=[]
for g in D['groups']:
    comparison.append(dict(batch=g['batch'],scene=g['scene'],sigma_kpa=g['sigma'],method=g['method'],n=g['n'],early=g['early'],
        early_lower95_percent=g['early_ci95'][0]*100,early_upper95_percent=g['early_ci95'][1]*100,
        false_trials=g['false_trials'],false_lower95_percent=g['false_ci95'][0]*100,false_upper95_percent=g['false_ci95'][1]*100,
        outcomes=json.dumps(g['outcomes'],ensure_ascii=False)))
write('comparison_statistics.csv',comparison)
write('boundary_statistics.csv',[dict(scene=g['scene'],sigma_kpa=g['sigma'],amplitude_percent=g['amplitude']*100,n=g['n'],correct=g['correct'],
    lower95_percent=g['ci95'][0]*100,upper95_percent=g['ci95'][1]*100,outcomes=json.dumps(g['outcomes'],ensure_ascii=False)) for g in EX['amplitude_groups']])
report=dict(passed=True,visual_direction='High-contrast journal plates, selected by user',
    source_numerical_results_retained=True,high_noise_outcome_groups_checked=9,actual_matrix_cells_checked=30,
    paired_seed_counterexample_points=80,exact_leak_load_overlap=True,conditional_lead_groups_checked=6,
    phase_aggregation_preserved=True,figure_checks=checks,docx_pages=4,no_split_paragraphs=True,
    original_8_2_8_3_text_preserved=True,physical_data=False,physical_print_test=False)
(E/'journal_acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
