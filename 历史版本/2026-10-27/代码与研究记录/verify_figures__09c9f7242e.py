"""Independent checks of every visual encoding against original trial records."""
from pathlib import Path
import csv,json,hashlib,zipfile,math
import numpy as np
from PIL import Image
from pypdf import PdfReader
from docx import Document
B=Path(__file__).resolve().parents[1];E=B/'evidence'
records=json.loads((E/'figure_checks.json').read_text(encoding='utf-8'))
z=np.load(E/'mechanism_observations.npz');trials=list(csv.DictReader((E/'paired_method_results.csv').open(encoding='utf-8-sig')))
amp=list(csv.DictReader((E/'amplitude_trials.csv').open(encoding='utf-8-sig')))
sampling=list(csv.DictReader((E/'sampling_extension_trials.csv').open(encoding='utf-8-sig')))
cfg=json.loads((B/'code/simulation/diagnosis_review/protocol.json').read_text(encoding='utf-8'))
replay=json.loads((E/'mechanism_replay.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ci(k,n=100):
 zz=1.959963984540054**2;den=1+zz/n;p=k/n
 center=(p+zz/(2*n))/den;half=math.sqrt(zz)*math.sqrt(p*(1-p)/n+zz/(4*n*n))/den
 return np.array([max(0,center-half),min(1,center+half)])*100

# Rebuild the hydraulic plant without calling any source-model functions.
t=np.arange(601);ramp=np.clip((t-360)/180,0,1);switch=(t>=180)&(t<300)
counter=list(csv.DictReader((E/'counterexample_results.csv').open(encoding='utf-8-sig')))
for scene in ['leak','restriction','load_unknown','drift']:
 c=.28+(.09*ramp if scene in ['leak','load_unknown'] else 0)
 resistance=.8+(7.2*ramp if scene=='restriction' else 0)
 ga=c/np.sqrt(1+resistance*c*c);gb=np.where(switch,.35/np.sqrt(1+.8*.35**2),0)
 p0=120/(1+.4*(ga+gb)**2);p1=p0/(1+resistance*c*c);q=c*np.sqrt(p1)
 truth=np.column_stack([p0,p1,q]);np.testing.assert_allclose(z[scene+'_truth'],truth,atol=4e-14,rtol=1e-14)
 observed=truth+np.random.default_rng(10300).normal(0,[3,3,.02],truth.shape)
 if scene=='drift':observed[:,0]+=10*ramp
 np.testing.assert_allclose(observed,z[scene+'_observed'],atol=5e-14,rtol=1e-14)
 mean=np.array([observed[max(0,j-9):j+1].mean(axis=0) for j in t])
 np.testing.assert_allclose(mean,z[scene+'_mean'],atol=4e-12,rtol=1e-12)
 k=mean[:,2]/np.sqrt(mean[:,1]);r=(mean[:,0]-mean[:,1])/mean[:,2]**2
 np.testing.assert_allclose(k,z[scene+'_k'],atol=3e-14,rtol=1e-12)
 np.testing.assert_allclose(r,z[scene+'_r'],atol=3e-12,rtol=1e-11)
 # Counterexample CSV stores all post-360 candidates; evaluate() deliberately
 # calls all events false on nonfault controls and leaves its fault fields null.
 k0=np.median(k[20:120]);r0=np.median(r[20:120])
 leak=k/k0-1>.06;restrict=r-r0>.6
 state=np.where(leak&restrict,'uncertain',np.where(leak,'leak_pattern',np.where(restrict,'restriction_pattern','normal')))
 events=[];active=None
 for j in range(130,601):
  label=state[j]
  if label=='normal':active=None;continue
  if np.all(state[j-4:j+1]==label):
   if active!=label:events.append((j,label))
   active=label
 if scene!='restriction':
  old=next(row for row in counter if row['scene']==scene and float(row['sigma'])==3 and int(row['seed'])==10300)
  post=[event for event in events if event[0]>=360]
  assert (str(post[0][0]) if post else '')==old['first_post_s']
  assert any(event[0]<360 for event in events)==(old['prior_false']=='True')
assert np.array_equal(z['leak_observed'],z['load_unknown_observed'])
assert replay['leak']['valid_lead_s']==51 and replay['restriction']['valid_lead_s']==109

checked_groups=0;checked_amps=0;checked_cdfs=0
for record in records:
 data=record['data'];kind=record['type']
 if kind=='point_interval_comparison':
  for g in data['groups']:
   rr=[r for r in trials if r['batch']=='holdout100' and r['scene']==g['scene'] and float(r['sigma'])==10 and r['method']==g['method']]
   assert len(rr)==100
   k=sum((int(r['false_onsets'])>0) if g['scene']=='long_normal' else r['early_valid']=='True' for r in rr)
   assert g['k']==k;np.testing.assert_allclose(g['ci95_percent'],ci(k),atol=3e-14);checked_groups+=1
 elif kind=='discrete_response_with_binomial_intervals':
  for g in data['groups']:
   for a,k,interval in zip(g['amplitude_percent'],g['correct'],g['wilson95_percent']):
    rr=[r for r in amp if r['scene']==g['scene'] and float(r['sigma'])==g['sigma'] and math.isclose(float(r['amplitude']),a/100)]
    assert len(rr)==100 and sum(r['correct']=='True' for r in rr)==k
    np.testing.assert_allclose(interval,ci(k),atol=3e-14);checked_amps+=1
 elif kind=='conditional_empirical_cdf':
  for g in data['groups']:
   vals=[float(r['lead_s']) for r in trials if r['batch']=='holdout100' and r['scene']==g['scene'] and float(r['sigma'])==10 and r['method']==g['method'] and r['early_valid']=='True']
   assert len(vals)==g['n'];np.testing.assert_array_equal(vals,g['values_s'])
   xx,count=np.unique(vals,return_counts=True);np.testing.assert_array_equal(xx,g['x_s'])
   np.testing.assert_allclose(np.cumsum(count)/len(vals)*100,g['cdf_percent']);checked_cdfs+=1
 elif kind=='paired_feature_trajectories':
  for path in data['paths']:
   s=path['scene'];np.testing.assert_allclose(path['k_ratio'],z[s+'_k'][360:]/replay[s]['k0'])
   np.testing.assert_allclose(path['delta_r'],z[s+'_r'][360:]-replay[s]['r0'])
 elif kind=='acquisition_tradeoff_with_iqr':
  for line in data:
   for g in line['groups']:
    rr=[r for r in sampling if r['scene']==line['scene'] and int(r['period'])==g['period']]
    byseed=[]
    for seed in range(63000,63016):
     subset=[r for r in rr if int(r['seed'])==seed]
     assert len(subset)==g['period']
     byseed.append([np.mean([float(r['pressure_reads']) for r in subset]),np.mean([int(r['critical_s'])-int(r['first_post_s']) for r in subset])])
    a=np.array(byseed)
    np.testing.assert_allclose(np.median(a,axis=0),[g['pressure_reads_median'],g['lead_median_s']])
    np.testing.assert_allclose(np.quantile(a,[.25,.75],axis=0)[:,0],g['pressure_reads_iqr'])
    np.testing.assert_allclose(np.quantile(a,[.25,.75],axis=0)[:,1],g['lead_iqr_s'])
 assert record['all_text_inside'] and record['minimum_font_pt']>=8.5
 for ext,digest in record['sha256'].items():assert sha(B/'figures'/f'{record["name"]}.{ext}')==digest
 with Image.open(B/'figures'/f'{record["name"]}.png') as im:assert all(abs(x-600)<.1 for x in im.info['dpi'])
 assert '<text' in (B/'figures'/f'{record["name"]}.svg').read_text(encoding='utf-8')
 pdf=PdfReader(B/'figures'/f'{record["name"]}.pdf')
 for fontref in pdf.pages[0]['/Resources']['/Font'].values():
  font=fontref.get_object();assert font['/Subtype']!='/Type3'
  descendant=font['/DescendantFonts'][0].get_object() if '/DescendantFonts' in font else font
  desc=descendant['/FontDescriptor'].get_object()
  assert any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3'])
assert (checked_groups,checked_amps,checked_cdfs)==(9,30,6)
doc=B/'第八部分_机制与轨迹修订稿.docx';word=Document(doc);assert len(word.inline_shapes)==5
with zipfile.ZipFile(doc) as archive:
 assert archive.read('word/document.xml').count(b'<m:oMath>')==2
 embedded={hashlib.sha256(archive.read(p)).hexdigest() for p in archive.namelist() if p.startswith('word/media/')}
expected={r['sha256']['png'] for r in records if r['name'].startswith('图8-')};assert expected==embedded
oldtexts=[p.text for p in Document(B/'code/source.docx').paragraphs];newtexts=[p.text for p in word.paragraphs]
for i in [1,8,9,10,11,12,13,14,15,16,17,18]:assert oldtexts[i] in newtexts
layout=json.loads((E/'document_layout.json').read_text(encoding='utf-8-sig'));assert layout['pages']==4
assert all(p['start_page']==p['end_page'] for p in layout['paragraphs'])
result=dict(passed=True,figure_count=len(records),independent_hydraulic_replay=True,strict_leak_load_identity=True,
 comparison_groups_recounted=checked_groups,amplitude_cells_recounted=checked_amps,ecdf_groups_recounted=checked_cdfs,
 phase_aggregation_checked=True,raw_seed=10300,negative_trigger_boundaries_removed=True,docx_pages=4,docx_embedded_images=5,
 source_paragraphs_preserved=12,editable_word_equations=2,all_figures_600_dpi=True,pdf_fonts_embedded=True,svg_text_editable=True,
 min_native_font_pt=min(r['minimum_font_pt'] for r in records),min_print_font_pt=min(r['minimum_font_pt'] for r in records)*146/168.91,
 physical_data=False,docx_sha256=sha(doc))
(E/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
