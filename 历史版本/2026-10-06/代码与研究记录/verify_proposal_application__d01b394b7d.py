"""Structural, source-data and rendered-layout checks for this exact document."""
from pathlib import Path
from zipfile import ZipFile
import csv,hashlib,io,json,re,subprocess
from collections import Counter
from PIL import Image
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'application/proposal_revision';TMP=ROOT/'tmp/proposal_review';PREVIOUS=ROOT/'application/method_revision'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}';tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
edit=json.loads((DATA/'edit_record.json').read_text(encoding='utf-8'));source=TMP/'source.docx';output=ROOT/edit['output']
assert source.read_bytes()==subprocess.check_output(['git','show',edit['source_commit']+':'+edit['source']],cwd=ROOT)
assert sha(source)==edit['source_sha256'] and sha(output)==edit['output_sha256']
with ZipFile(source) as a,ZipFile(output) as b:
    assert a.namelist()==b.namelist()
    assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==edit['changed_parts']
    before=E.fromstring(a.read('word/document.xml'));root=E.fromstring(b.read('word/document.xml'))
    rows=root.find(W+'body/'+W+'tbl').findall(W+'tr');old=before.find(W+'body/'+W+'tbl').findall(W+'tr');assert len(rows)==31
    for i in edit['protected_rows']:assert E.tostring(rows[i])==E.tostring(old[i]),i
    assert len(root.xpath('.//m:oMath',namespaces=NS))==edit['native_math']
    rel={e.get('Id'):e.get('Target') for e in E.fromstring(b.read('word/_rels/document.xml.rels'))}
    figures=[]
    for p in root.xpath('.//w:p',namespaces=NS):
        if not re.match(r'^图\d+\s',tx(p)):continue
        shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0]
        id=shape.xpath('.//v:imagedata/@r:id',namespaces=NS)[0];part='word/'+rel[id]
        im=Image.open(io.BytesIO(b.read(part)));iw,ih=im.size
        dims={k:float(v) for k,v in re.findall(r'(width|height):([\d.]+)pt',shape.get('style'))}
        assert abs(dims['width']*ih/iw-dims['height'])<.12,(tx(p),dims,im.size)
        assert iw/dims['width']*72>=300
        figures.append(dict(caption=tx(p),part=part,px=[iw,ih],print_width_pt=dims['width'],dpi=iw/dims['width']*72,
                            sha256=hashlib.sha256(b.read(part)).hexdigest(),preserved=b.read(part)==a.read(part)))
assert len(figures)==10 and all(f['preserved'] for f in figures)
old_shapes=before.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)
new_shapes=root.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)
assert len(old_shapes)==len(new_shapes)
assert [x.get('style') for x in old_shapes]==[x.get('style') for x in new_shapes]

refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
assert len(refs)==8
assert all(re.search('[\u4e00-\u9fff]',s) for s in refs[:5]) and all(not re.search('[\u4e00-\u9fff]',s) for s in refs[5:])
citations=[]
for ri in [17,18,19]:
    for p in rows[ri].xpath('.//w:p',namespaces=NS):
        if re.match(r'^\[[1-8]\]',tx(p)):continue
        for r in p.findall(W+'r'):
            if re.search(r'\[[1-8](?:,[1-8])*\]',tx(r)):
                v=r.find(W+'rPr/'+W+'vertAlign');assert v is not None and v.get(W+'val')=='superscript'
                citations.append(tx(r))
assert citations
tables=[]
for t in root.xpath('.//w:tbl',namespaces=NS)[1:]:
    if len(t.find(W+'tr').findall(W+'tc'))<3:continue
    jc=t.find(W+'tblPr/'+W+'jc');assert jc is not None and jc.get(W+'val')=='center'
    assert t.find(W+'tr/'+W+'trPr/'+W+'tblHeader') is not None
    tables.append(dict(header=tx(t.find(W+'tr')),rows=len(t.findall(W+'tr'))))
assert len(tables)==3
for p in root.xpath('.//w:p',namespaces=NS):
    if re.match(r'^(图\d+|表\d+)\s',tx(p)):
        jc=p.find(W+'pPr/'+W+'jc');assert jc is not None and jc.get(W+'val')=='center'
layout=json.loads((TMP/'native_layout.json').read_text(encoding='utf-8-sig'));assert layout['pages']==20 and layout['native_math_count']==edit['native_math']
captions=[p for p in layout['paragraphs'] if re.match(r'^(图\d+|表\d+)\s',p['text'].replace('\x01','').replace('\x0b','').strip())]
assert len(captions)==13 and all(p['start_page']==p['end_page'] for p in captions)
protocol=next(p for p in layout['paragraphs'] if p['text'].startswith('3 协议与平台软件'))
protocol_body=next(p for p in layout['paragraphs'] if p['text'].startswith('已完成采集适配'))
assert protocol['start_page']==protocol['end_page']==protocol_body['start_page']
assert protocol_body['start_page']==protocol_body['end_page']
data=json.loads((PREVIOUS/'figure_sources.json').read_text(encoding='utf-8'))
assert sha(ROOT/data['source'])==data['source_sha256']
assert sha(ROOT/'simulation/hybrid_sampling_review/acceptance.json')==data['previous_acceptance_sha256']
assert sha(ROOT/'simulation/hybrid_sampling_review/frozen_parameters.json')==data['parameters_sha256']
selected=list(csv.DictReader((PREVIOUS/'figure9_selected_records.csv').open(encoding='utf-8')));assert len(selected)==324
original_records=list(csv.DictReader((ROOT/data['source']).open(encoding='utf-8')))
expected=[r for r in original_records if r['scene'] in ['leak','restriction','long_normal']
          and float(r['sigma']) in [.3,3,10] and r['method'] in ['threshold','guarded_fast','hybrid'] and r['profile']=='fixed']
record_key=lambda r:tuple(sorted(r.items()))
assert Counter(map(record_key,selected))==Counter(map(record_key,expected))
for g in data['groups']:
    rr=[r for r in selected if r['scene']==g['scene'] and float(r['sigma'])==g['sigma'] and r['method']==g['method']]
    assert len(rr)==g['n']==12
    assert {int(r['seed']) for r in rr}==set(range(28000,28012))
    assert sum(r['early_valid']=='True' for r in rr)==g['early']
    assert sum(int(r['false_onsets'])>0 for r in rr)==g['false_trials']
review=json.loads((DATA/'visual_review.json').read_text(encoding='utf-8'))
pages=json.loads((TMP/'pages/pages.json').read_text(encoding='utf-8'))
assert review['output_sha256']==sha(output) and review['pages']==pages and review['all_pages_individually_viewed']
assert review['all_ten_figures_reviewed']
assert review['grayscale_basis']=='prior exact-image review'
prior_review=json.loads((PREVIOUS/'visual_review.json').read_text(encoding='utf-8'))
prior_accept=json.loads((PREVIOUS/'acceptance.json').read_text(encoding='utf-8'))
assert prior_review['grayscale_reviewed']
assert [f['sha256'] for f in figures]==[f['sha256'] for f in prior_accept['figures']]
assert review['prior_grayscale_review_sha256']==sha(PREVIOUS/'visual_review.json')
for p in pages:assert sha(ROOT/p['file'])==p['sha256']
checks=json.loads((PREVIOUS/'figure_checks.json').read_text(encoding='utf-8'))
assert len(checks['figures'])==1
fc=checks['figures'][0];assert not fc['outside'] and not fc['boxIntersections'] and not fc['textOutsideOwnBox'] and fc['minFontPt']>=10
assert fc['png_sha256']==sha(ROOT/'application/figures/method_revision/dual_window_diagnosis.png')
assert fc['svg_sha256']==sha(ROOT/'application/figures/method_revision/dual_window_diagnosis.svg')
accept=dict(passed=True,scope='Application-style prose revision, unchanged figure assets and source-backed evidence; exact final WPS rendering, no physical performance validation.',
 output_sha256=sha(output),source_sha256=sha(source),pages=layout['pages'],native_math=edit['native_math'],figures=figures,tables=tables,
 information_budget_approvals_preserved=True,references={'Chinese':5,'English':3},superscript_citation_runs=len(citations),
 same_page_figure_caption_paragraphs=True,figure9_independently_counted_records=324,
 references_and_source_results_unchanged=True,prior_grayscale_basis='byte-identical images from prior reviewed version',
 visual_review_sha256=sha(DATA/'visual_review.json'),pdf_sha256=sha(TMP/'application.pdf'),
 renderer='Bundled renderer attempted; LibreOffice unavailable; WPS read-only native export and bundled PDFium',
 limitations=['synthetic candidate comparison has shared seeds and fixed model assumptions',
              'MCU, RF, physical measurement, energy and valve actuation still require independent implementation verification'])
(DATA/'acceptance.json').write_text(json.dumps(accept,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Accepted exact 20-page application revision: 10 unchanged figures, 3 centered complete data tables, 8 references, 11 native math objects; 324 plot records checked.')
