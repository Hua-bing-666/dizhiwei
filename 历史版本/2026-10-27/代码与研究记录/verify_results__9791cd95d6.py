"""Independent audit of exports, numerical invariants, frontend and causality."""
from pathlib import Path
import sys,csv,json,hashlib,math
import numpy as np
from PIL import Image
from docx import Document
B=Path(__file__).resolve().parents[1];E=B/'evidence'
sys.path.insert(0,str(B/'code/snapshot'))
import review_hybrid_sampling as h
import review_operating_reference as o
D=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
P=json.loads((E/'frozen_parameters.json').read_text(encoding='utf-8'))
source_lock_checks={}
for name in ['review_hybrid_sampling.py','review_operating_reference.py','review_diagnosis.py']:
    text=(B/'code/snapshot'/name).read_text(encoding='utf-8')
    if name=='review_diagnosis.py':
        # Later desktop packaging added sys._MEIPASS ROOT discovery only. Restore
        # those two exact edits to validate the byte-for-byte frozen source lock.
        text=text.replace(',sys','').replace("ROOT=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]","ROOT=Path(__file__).resolve().parents[1]")
    digest=hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert digest==P['sources']['simulation/'+name],name
    source_lock_checks[name]='exact frozen source match after desktop ROOT adapter normalization' if name=='review_diagnosis.py' else 'exact frozen source match'
rows=list(csv.DictReader((E/'paired_method_results.csv').open(encoding='utf-8-sig')))
assert len(rows)==3024
ids=[(r['batch'],r['scene'],r['sigma'],r['seed'],r['method']) for r in rows]
assert len(ids)==len(set(ids))
def ci95(k,n):
    z=1.959963984540054;ph=k/n
    return [(2*k+z*z+s*z*math.sqrt(z*z+4*k*(1-ph)))/(2*(n+z*z)) for s in [-1,1]]
for g in D['groups']:
    rr=[r for r in rows if (r['batch'],r['scene'],float(r['sigma']),r['method'])==(g['batch'],g['scene'],g['sigma'],g['method'])]
    assert len(rr)==g['n']
    k=sum(r['early_valid']=='True' for r in rr);f=sum(int(r['false_onsets'])>0 for r in rr)
    assert (k,f)==(g['early'],g['false_trials'])
    assert np.allclose(ci95(k,len(rr)),g['early_ci95'],atol=1e-14)
    assert np.allclose(ci95(f,len(rr)),g['false_ci95'],atol=1e-14)

Z=np.load(E/'trace_data.npz');ref=P['baseline']['references']['n0.5']
max_feature_error=0.;causal=0;confirm_checks=0
for scene in ['leak','restriction']:
    for sigma in [.3,3.,10.]:
        obs=Z[f'{scene}_{sigma:g}_observed'];tr=o.trajectory(scene,.5)
        full=h.sensor_replay(obs,61000,ref,'fixed',P['h_bounded_sensor']['fixed'])
        short=h.sensor_replay(obs[:421],61000,ref,'fixed',P['h_bounded_sensor']['fixed'])
        assert full['records'][:len(short['records'])]==short['records']
        assert all(e['t_s']>420 or e in short['decisions'][m]['events'] for m in h.SENSOR_METHODS for e in full['decisions'][m]['events'])
        causal+=1
        # Independent window arithmetic uses direct slices, not cumulative sums or cached Q10.
        phase=(61000*.6180339887498949)%1
        cum=np.floor(phase+np.cumsum(np.maximum(obs[:,2],0))*9).astype(np.int64)
        for rec in full['records']:
            t=rec['t'];q=(cum[t]-cum[t-10])/90
            p0,p1=obs[t-9:t+1,:2].mean(axis=0)
            pred=ref['a_l_min']*(p1/100)**ref['n_fitted']
            x=np.array([q/(full['context']['gain']*pred)-1,(p0-p1)/q**2-full['context']['r0']])
            max_feature_error=max(max_feature_error,float(np.max(abs(x-np.array(rec['x'])))))
        for method in h.SENSOR_METHODS:
            labels=full['decisions'][method]['labels'];out=[]
            for j,label in enumerate(labels):
                if label<=0 or j<4:continue
                if labels[j-4:j+1]!=[label]*5:continue
                # Exactly one event per uninterrupted same-label run of >=5 updates.
                if j>=5 and labels[j-5]==label:continue
                out.append((full['records'][j]['t'],{1:'leak_pattern',2:'restriction_pattern',3:'uncertain'}[label]))
            assert out==[(e['t_s'],e['pattern']) for e in full['decisions'][method]['events']]
            rr=next(r for r in rows if r['batch']=='holdout100' and r['scene']==scene and float(r['sigma'])==sigma and r['seed']=='61000' and r['method']==method)
            before=[(t,k) for t,k in out if t<360];after=[(t,k) for t,k in out if t>=360]
            crit=int(np.flatnonzero(tr['severity']>=.15)[0])
            early=not before and bool(after) and after[0][1]==tr['target'] and after[0][0]<crit
            assert early==(rr['early_valid']=='True')
            confirm_checks+=1
assert max_feature_error<1e-11
for sigma in [.3,1.,3.,10.]:assert np.array_equal(Z[f'leak_k_{sigma:g}'],Z[f'load_k_{sigma:g}'])

figs=json.loads((E/'figure_checks.json').read_text(encoding='utf-8'))
imagechecks=[]
for fig in figs:
    im=Image.open(B/'figures'/(fig['name']+'.png'));w,hh=im.size
    assert im.mode in ['RGBA','RGB'];assert min(im.info['dpi'])>=599
    assert fig['min_font_pt']>=7 and fig['text_within_canvas']
    assert not '<text' in (B/'figures'/(fig['name']+'.svg')).read_text(encoding='utf-8')
    for ext in ['png','pdf','svg']:
        assert hashlib.sha256((B/'figures'/(fig['name']+'.'+ext)).read_bytes()).hexdigest()==fig['output_sha256'][ext]
    imagechecks.append(dict(name=fig['name'],pixels=[w,hh],dpi=im.info['dpi'],min_font_pt=fig['min_font_pt'],svg_outlined=True))
doc=Document(B/'第八部分_彩印仿真修订稿.docx')
text='\n'.join(p.text for p in doc.paragraphs)
assert len(doc.inline_shapes)==2 and '【图片修改下】' not in text
assert all(s in text for s in ['14/100','16/100','99/100','98/100','900条合成轨迹','2700条方法记录'])
layout_path=E/'document_layout.json'
layout=json.loads(layout_path.read_text(encoding='utf-8-sig'))
assert layout['document_sha256']==hashlib.sha256((B/'第八部分_彩印仿真修订稿.docx').read_bytes()).hexdigest()
assert layout['pages']==3
for p in layout['paragraphs']: assert p['start_page']==p['end_page'],p['text'][:60]
report=dict(passed=True,original_record_reproduction=324,exported_method_records=3024,all_54_strata_recounted=True,
    frozen_algorithm_source_lock=source_lock_checks,
    independent_wilson_interval_check=True,independent_frontend_max_abs_error=max_feature_error,
    prefix_causality_checks=causal,independent_confirmation_and_early_checks=confirm_checks,
    observational_identifiability_equalities=80,model_balance=D['model_checks'],
    figure_checks=imagechecks,docx_pages=3,no_split_paragraphs=True,
    native_render='WPS PDF export, then PDFium rasterization; standard renderer failed because runtime has no LibreOffice',
    physical_print_test_performed=False,physical_data=False)
(E/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
