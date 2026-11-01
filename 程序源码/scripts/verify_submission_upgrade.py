"""Verify final OOXML and native print layout; manual review is recorded separately."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image
import hashlib, json, re, pdfplumber

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'application/submission_upgrade'
TMP = ROOT / 'tmp/submission_document_review'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'v':'urn:schemas-microsoft-com:vml'}
W = '{'+NS['w']+'}'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
tx = lambda p: ''.join(p.xpath('.//w:t/text()', namespaces=NS))
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
record = load(DATA/'build_record.json')
source = ROOT/record['source']; output = ROOT/record['output']
assert sha(source) == record['source_sha256']
assert sha(output) == record['output_sha256']
with ZipFile(source) as z: original = E.fromstring(z.read('word/document.xml'))
with ZipFile(output) as z:
    parts = {n:z.read(n) for n in z.namelist()}
root = E.fromstring(parts['word/document.xml'])
math = lambda r:[E.tostring(x) for x in r.xpath('.//m:oMath', namespaces=NS)]
assert len(math(root)) == 27 and math(root) == math(original)
rows = root.find(W+'body/'+W+'tbl').findall(W+'tr')
oldrows = original.find(W+'body/'+W+'tbl').findall(W+'tr')
assert len(rows) == 31
for i in list(range(16))+list(range(25,31)):
    assert E.tostring(rows[i]) == E.tostring(oldrows[i]), i
assert tx(rows[24]) == '九、项目经费使用计划'
for p in rows[24].xpath('.//w:p', namespaces=NS):
    spacing = p.find(W+'pPr/'+W+'spacing')
    assert spacing is None or spacing.get(W+'lineRule') != 'exact'
refs = [tx(p) for p in rows[19].xpath('.//w:p', namespaces=NS) if re.match(r'^\[\d\]',tx(p))]
assert refs == record['references'] and len(refs) == 8
assert all(re.search('[\u4e00-\u9fff]', r) for r in refs[:5])
assert all(not re.search('[\u4e00-\u9fff]', r) for r in refs[5:])

tables=[]
for index in (18,22):
    for t in rows[index].xpath('.//w:tbl', namespaces=NS):
        tr=t.find(W+'tr')
        if tr is not None and len(tr.findall(W+'tc')) >= 3: tables.append(t)
assert len(tables) == 3
for t in tables:
    assert t.find(W+'tblPr/'+W+'jc').get(W+'val') == 'center'
    for p in t.find(W+'tr').xpath('.//w:p', namespaces=NS):
        assert p.find(W+'pPr/'+W+'jc').get(W+'val') == 'center'

captions=[]
for p in root.xpath('.//w:p', namespaces=NS):
    match=re.match(r'^图(\d+)\s',tx(p))
    if not match: continue
    assert p.find('.//{'+NS['v']+'}imagedata') is not None
    assert p.find(W+'pPr/'+W+'jc').get(W+'val') == 'center'
    assert p.getparent().getparent().find(W+'trPr/'+W+'cantSplit') is not None
    captions.append(int(match[1]))
assert captions == list(range(1,11))
for item in record['figure_replacements']:
    png=ROOT/item['png']
    assert sha(png) == item['sha256']
    assert hashlib.sha256(parts[item['part']]).hexdigest() == item['sha256']
    w,h=Image.open(png).size
    assert abs(item['height_pt']-420*h/w) < 0.001

native=load(TMP/'native_layout.json')
assert native['pages'] == 21 and native['native_math_count'] == 27
page_map={}
for p in native['paragraphs']:
    clean=re.sub(r'^[\x00-\x20]+','',p['text'])
    match=re.match(r'^图\s*(\d+)\s',clean)
    if not match: continue
    assert p['start_page'] == p['end_page'], clean
    page_map[int(match[1])] = p['start_page']
assert sorted(page_map) == list(range(1,11))

pdf_images=[]
with pdfplumber.open(TMP/'application.pdf') as pdf:
    assert len(pdf.pages) == 21
    for number,page in enumerate(pdf.pages,1):
        for im in page.images:
            if number == 1: continue # The untouched school logo.
            assert 0 <= im['x0'] < im['x1'] <= page.width
            assert 0 <= im['top'] < im['bottom'] <= page.height
            # Figure 8 retains its original 390 pt platform screenshot.
            target_width = 390 if number == page_map[8] else 420
            assert abs((im['x1']-im['x0'])-target_width) < 0.5
            assert abs((im['x0']+im['x1'])/2-page.width/2) < 1.5
            pdf_images.append({'page':number,'x0':im['x0'],'x1':im['x1'],
                               'top':im['top'],'bottom':im['bottom']})
    assert len(pdf_images) == 10
    assert [x['page'] for x in pdf_images] == [page_map[i] for i in range(1,11)]

figure_checks=load(ROOT/'simulation/submission_upgrade/figure_checks.json')
assert len(figure_checks['figures']) == 9
for f in figure_checks['figures']:
    assert not f['outside'] and not f['boxIntersections'] and not f['textOutsideOwnBox']
    assert f['minFontPt'] >= 9.5
    assert sha(ROOT/'application/figures/submission_upgrade'/f"{f['name']}.png") == f['png_sha256']

sampling=load(ROOT/'simulation/event_sampling_review/summary.json')
assert sha(ROOT/sampling['source']) == sampling['source_sha256']
assert sampling['replay_rows'] == 1920 and sampling['physical_validation'] is False
assert sampling['energy_claim'] is None
control=load(ROOT/'simulation/control_review/checks.json')
assert len(control['checks']) == 12 and all(x['passed'] for x in control['checks'])
assert control['hardware_compiled'] is False and control['physical_execution'] is False

pages=load(TMP/'final_pages/pages.json')
assert len(pages) == 21
for p in pages: assert sha(ROOT/p['file']) == p['sha256']
result={'date':'2026-10-05','scope':'application document and figures; local WPS print layout',
        'status':'automated_checks_passed','output':record['output'],
        'output_sha256':sha(output),'source_sha256':sha(source),'pages':21,
        'native_math_count':27,'references':{'Chinese':5,'English':3},
        'figure_count':10,'revised_figure_count':9,'figure_pages':page_map,
        'centered_body_tables':3,'revised_figure_width_pt':420,
        'unchanged_platform_figure_width_pt':390,'pdf_images':pdf_images,
        'physical_validation':False,'energy_claim':None,'page_receipts':pages}
visual_path=DATA/'visual_review.json'
if visual_path.exists():
    visual=load(visual_path)
    # A saved visual review is valid only for this exact document and page images.
    if visual['output_sha256']==sha(output) and visual['page_receipts']==pages:
        result['status']='automated_checks_and_visual_review_passed_with_stated_scope'
        result['visual_review']='application/submission_upgrade/visual_review.json'
(DATA/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Verified: 21 pages, 10 same-page figures, 3 centered tables, 27 preserved equations, 5+3 references.')
