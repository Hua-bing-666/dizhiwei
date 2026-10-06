"""Check the exact updated proposal and independently recount new software evidence."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image
import json,re,hashlib,io
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'application/current_revision';TMP=ROOT/'tmp/current_application_review'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'};W='{'+NS['w']+'}'
tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((DATA/'edit_record.json').read_text(encoding='utf-8'));source=ROOT/record['source'];output=ROOT/record['output'];assert sha(source)==record['source_sha256'];assert sha(output)==record['output_sha256']
with ZipFile(source) as a,ZipFile(output) as b:
 assert a.namelist()==b.namelist();assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==record['changed_parts']
 old=E.fromstring(a.read('word/document.xml'));root=E.fromstring(b.read('word/document.xml'))
 rows=root.find(W+'body/'+W+'tbl').findall(W+'tr');oldrows=old.find(W+'body/'+W+'tbl').findall(W+'tr');assert len(rows)==31
 for i in record['protected_rows']:assert E.tostring(rows[i])==E.tostring(oldrows[i])
 assert len(root.xpath('.//m:oMath',namespaces=NS))==11
 refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
 assert len(refs)==8 and all(re.search('[\u4e00-\u9fff]',t) for t in refs[:5]) and all(not re.search('[\u4e00-\u9fff]',t) for t in refs[5:])
 assert refs==[tx(p) for p in oldrows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
 citations=0
 for i in [17,18,19]:
  for p in rows[i].xpath('.//w:p',namespaces=NS):
   if re.match(r'^\[[1-8]\]',tx(p)):continue
   for r in p.findall(W+'r'):
    if re.search(r'\[[1-8](?:,[1-8])*\]',tx(r)):
     v=r.find(W+'rPr/'+W+'vertAlign');assert v is not None and v.get(W+'val')=='superscript';citations+=1
 rel={e.get('Id'):e.get('Target') for e in E.fromstring(b.read('word/_rels/document.xml.rels'))};figs=[]
 for p in root.xpath('.//w:p',namespaces=NS):
  if not re.match(r'^(图\d+|表\d+)\s',tx(p)):continue
  assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center'
  if tx(p).startswith('表'):continue
  shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0];id=shape.xpath('.//v:imagedata/@r:id',namespaces=NS)[0];part='word/'+rel[id];im=Image.open(io.BytesIO(b.read(part)));iw,ih=im.size
  dims={k:float(v) for k,v in re.findall(r'(width|height):([\d.]+)pt',shape.get('style'))}
  assert abs(dims['width']*ih/iw-dims['height'])<.13
  assert iw/dims['width']*72>=300
  figs.append({'caption':tx(p),'media':part,'preserved_bytes':a.read(part)==b.read(part),'dpi':round(iw/dims['width']*72,1),'width_pt':dims['width']})
 assert len(figs)==10 and sum(f['preserved_bytes'] for f in figs)==8
 tables=[]
 for t in root.xpath('.//w:tbl',namespaces=NS)[1:]:
  if len(t.find(W+'tr').findall(W+'tc'))<3:continue
  assert t.find(W+'tblPr/'+W+'jc').get(W+'val')=='center';assert t.find(W+'tr/'+W+'trPr/'+W+'tblHeader') is not None
  tables.append(tx(t.find(W+'tr')))
 assert len(tables)==3
layout=json.loads((TMP/'native_layout.json').read_text(encoding='utf-8-sig'));assert layout['pages']==20 and layout['native_math_count']==11
clean=lambda x:x.replace('\x01','').replace('\x0b','').strip()
caps=[p for p in layout['paragraphs'] if re.match(r'^(图\d+|表\d+)\s',clean(p['text']))];assert len(caps)==13 and all(p['start_page']==p['end_page'] for p in caps)
for prefix in ['节点设置短窗关注','控制联动服务于','（2）围绕健康参照','本地巡检平台已形成']:
 p=next(p for p in layout['paragraphs'] if clean(p['text']).startswith(prefix));assert p['start_page']==p['end_page'],prefix
trials=json.loads((ROOT/'simulation/platform_upgrade/scheduling_trials.json').read_text(encoding='utf-8'));assert len(trials)==432
for scene,expect in [('leak',[9,17,39]),('restriction',[9,17,42])]:
 for period,n,early in zip([1,2,5],[9,18,45],expect):
  rs=[r for r in trials if r['scene']==scene and r['period']==period];assert len(rs)==n and sum(r['early_valid'] for r in rs)==early
for period,mean in zip([1,2,5],[601.0,411.6,273.6]):
 rs=[r for r in trials if r['scene']=='normal' and r['period']==period];assert round(sum(r['pressure_reads'] for r in rs)/len(rs),1)==mean
cross=json.loads((ROOT/'simulation/platform_upgrade/cross_operating_points.json').read_text(encoding='utf-8'));assert len(cross['trials'])==72
summary=json.loads((ROOT/'simulation/platform_upgrade/cross_operating_summary.json').read_text(encoding='utf-8'))
assert all(r['trials']==8 and (r['false_onsets']==0 if r['scene']=='normal' else r['early_valid']==8) for r in summary if r['exponent']==.5)
assert any(r['false_onsets']>0 for r in summary if r['exponent']!=.5 and r['scene']=='normal')
web=json.loads((ROOT/'simulation/platform_upgrade/web_data.json').read_text(encoding='utf-8'));assert len(web['traces'])==27 and not web['physical_data'] and not web['energy_measured']
guard=json.loads((ROOT/'application/models/system_upgrade/guard_checks.json').read_text(encoding='utf-8'));assert all(r['overlap_volume_mm3']==0 for r in guard['checks'])
scene=json.loads((ROOT/'application/models/system_upgrade/bench_scene.json').read_text(encoding='utf-8'));assert len(scene['meshes'])==207
pages=json.loads((TMP/'pages/pages.json').read_text(encoding='utf-8'));assert len(pages)==20
for p in pages:assert sha(ROOT/p['file'])==p['sha256']
review={'output_sha256':sha(output),'pages':pages,'all_pages_individually_viewed':True,'figures_reviewed':10,'updated_figures_grayscale_reviewed':True,'corrected':['native residual formula matches current method','figure3 numbered current CAD mesh and black-white legend','figure8 actual C replay publication view','single-opening-line paragraph splits','figure9 interpretation stays with plot'],'unchanged_figure_basis':'8 byte-identical images retained from approved source; all viewed again in current document','renderer':'Bundled renderer failed because LibreOffice is absent; WPS read-only native PDF export and bundled PDFium rasterization.'}
(DATA/'visual_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
accept={'passed':True,'output_sha256':sha(output),'source_sha256':sha(source),'pages':20,'paragraph_updates':21,'figures':figs,'centered_data_tables':3,'references':{'Chinese':5,'English':3},'superscript_citation_runs':citations,'native_math':11,'protected_information_budget_signature_rows':record['protected_rows'],'sampling_combinations_independently_recounted':432,'cross_operating_combinations':72,'trace_groups':27,'concept_mesh_entities':207,'physical_performance_verified':False,'limitations':['simulations share model assumptions','adaptive schedule not deployed on STM32','physical LoRa, sensor, energy and valve performance not measured','desktop executable remains a planned packaging task'],'visual_review_sha256':sha(DATA/'visual_review.json'),'pdf_sha256':sha(TMP/'application.pdf'),'evidence_sha256':{f:sha(ROOT/f) for f in record['evidence_files']}}
(DATA/'acceptance.json').write_text(json.dumps(accept,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
record['visual_review_status']='passed';(DATA/'edit_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Accepted exact 20-page DOCX: 10 figures, 3 centered data tables, 8 references, 11 native equations; new counts independently verified; original retained.')
