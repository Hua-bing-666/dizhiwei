"""Check the saved application against its source, native print layout and image receipts."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image
import hashlib, json, re, subprocess, pdfplumber

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'application/print_polish'; TMP=ROOT/'tmp/print_polish_document'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v':'urn:schemas-microsoft-com:vml'}
W='{'+NS['w']+'}'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
record=load(DATA/'build_record.json');source=ROOT/record['source'];output=ROOT/record['output']
assert sha(source)==record['source_sha256']
assert sha(output)==record['output_sha256']
assert sha(ROOT/'deliverables/11.docx')=='192a3405403ea9bb8a2404fd87cd354c339f33e5f0f96a6f81a91672de7645fb'
with ZipFile(source) as z:old=E.fromstring(z.read('word/document.xml'))
with ZipFile(output) as z:parts={n:z.read(n) for n in z.namelist()}
root=E.fromstring(parts['word/document.xml'])
math=lambda r:[E.tostring(x) for x in r.xpath('.//m:oMath',namespaces=NS)]
assert len(math(root))==27 and math(root)==math(old)
rows=root.find(W+'body/'+W+'tbl').findall(W+'tr');oldrows=old.find(W+'body/'+W+'tbl').findall(W+'tr')
assert len(rows)==31
for i in list(range(16))+list(range(25,31)):assert E.tostring(rows[i])==E.tostring(oldrows[i]),i
assert tx(rows[24])=='九、项目经费使用计划'
body='\n'.join(tx(row) for row in rows[16:25])
assert '四、国、内外' not in body
assert '四、国内外研究现状与发展动态' in body
headings=[]
for row in rows[16:25]:
    for t in row.xpath('.//w:r/w:t',namespaces=NS):
        if t.text and re.match(r'^(?:[一二三四五六七八九]、|[1-7] )',t.text) and len(t.text)<70:
            headings.append(t.text)
            b=t.getparent().find(W+'rPr/'+W+'b')
            assert b is not None and b.get(W+'val')!='0',t.text
assert len([t for t in headings if re.match(r'^[一二三四五六七八九]、',t)])==9
protocol_heading=next(t for t in rows[23].xpath('.//w:r/w:t',namespaces=NS) if t.text=='3 协议与平台软件')
assert next(a for a in protocol_heading.iterancestors() if a.tag==W+'tbl') is root.find(W+'body/'+W+'tbl')
assert len(rows[23].xpath('.//w:tbl',namespaces=NS))==4
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[\d\]',tx(p))]
assert refs==record['references'] and len(refs)==8
assert all(re.search('[\u4e00-\u9fff]',r) for r in refs[:5])
assert all(not re.search('[\u4e00-\u9fff]',r) for r in refs[5:])
citations=[]
for row in rows[16:25]:
    for p in row.xpath('.//w:p',namespaces=NS):
        if re.match(r'^\[\d\]',tx(p)):
            assert not p.xpath('./w:r/w:rPr/w:vertAlign[@w:val="superscript"]',namespaces=NS)
            continue
        for r in p.findall(W+'r'):
            for token in re.findall(r'\[[1-8](?:[,，][1-8])*\]',tx(r)):
                va=r.find(W+'rPr/'+W+'vertAlign')
                assert va is not None and va.get(W+'val')=='superscript',token
                citations.append(token)
assert citations==record['citations'] and len(citations)==11
assert set(re.findall(r'[1-8]',''.join(citations)))==set('12345678')
tables=[]
for i in (18,22):
    for t in rows[i].xpath('.//w:tbl',namespaces=NS):
        tr=t.find(W+'tr')
        if tr is not None and len(tr.findall(W+'tc'))>=3:tables.append(t)
assert len(tables)==3
for t in tables:
    assert t.find(W+'tblPr/'+W+'jc').get(W+'val')=='center'
    for p in t.find(W+'tr').xpath('.//w:p',namespaces=NS):assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center'
captions=[];table_captions=[]
for p in root.xpath('.//w:p',namespaces=NS):
    if re.match(r'^表[1-3] ',tx(p)):
        assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center';table_captions.append(tx(p))
    m=re.match(r'^图(\d+)\s',tx(p))
    if m:
        assert p.find('.//{'+NS['v']+'}imagedata') is not None
        assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center'
        assert p.getparent().getparent().find(W+'trPr/'+W+'cantSplit') is not None
        captions.append(int(m[1]))
assert captions==list(range(1,11)) and len(table_captions)==3
for f in record['figures']:
    png=ROOT/f['png'];w,h=Image.open(png).size
    assert sha(png)==f['sha256']==hashlib.sha256(parts[f['part']]).hexdigest()
    assert f['width_pt']==420 and abs(f['height_pt']-420*h/w)<.001
native=load(TMP/'native_layout.json');assert native['pages']==20 and native['native_math_count']==27
figure_pages={};table_pages={}
for p in native['paragraphs']:
    clean=re.sub(r'^[\x00-\x20]+','',p['text'])
    m=re.match(r'^图\s*(\d+)\s',clean)
    if m:
        assert p['start_page']==p['end_page'],clean
        figure_pages[int(m[1])]=p['start_page']
    m=re.match(r'^表\s*([1-3])\s',clean)
    if m:table_pages[int(m[1])]=p['start_page']
assert sorted(figure_pages)==list(range(1,11))
pdf_images=[]
with pdfplumber.open(TMP/'application.pdf') as pdf:
    assert len(pdf.pages)==20
    assert '四、国内外研究现状与发展动态' in re.sub(r'\s','',pdf.pages[12].extract_text())
    for n,page in enumerate(pdf.pages,1):
        for im in page.images:
            if n==1:continue
            assert 0<=im['x0']<im['x1']<=page.width
            assert 0<=im['top']<im['bottom']<=page.height
            assert abs(im['x1']-im['x0']-420)<.5
            assert abs((im['x0']+im['x1'])/2-page.width/2)<1.5
            pdf_images.append({'page':n,'x0':im['x0'],'x1':im['x1'],'top':im['top'],'bottom':im['bottom']})
assert len(pdf_images)==10
assert [f['page'] for f in pdf_images]==[figure_pages[i] for i in range(1,11)]
checks=load(ROOT/'simulation/print_polish/figure_checks.json');assert len(checks['figures'])==9
for f in checks['figures']:
    assert not f['outside'] and not f['boxIntersections'] and not f['textOutsideOwnBox']
    assert f['minFontPt']>=9.5
    for ext in ('png','svg'):assert sha(ROOT/'application/figures/print_polish'/f"{f['name']}.{ext}")==f[ext+'_sha256']
site=ROOT/'deliverables/index.html';ui=load(ROOT/'simulation/print_polish/website_capture_checks.json')
assert sha(site)==ui['source_sha256']['site']
assert not ui['dom_replaced'] and not ui['css_overridden'] and not ui['pixels_postprocessed']
assert ui['math']=={'unitCount':2,'radicalCount':1,'fractionCount':2,'exponentCount':1}
assert len(ui['responsive_units'])==4 and all(x['documentWidth']<=x['width'] and all(y['contained'] for y in x['units']) for x in ui['responsive_units'])
assert not ui['screenshots'][0]['overlaps']
# Website presentation edits must not change replay data, diagnosis or operations code.
prior=subprocess.run(['git','show','94ba9a1:deliverables/index.html'],cwd=ROOT,check=True,capture_output=True).stdout
scripts=lambda b:re.findall(rb'<script\b[^>]*>[\s\S]*?</script>',b)
assert scripts(site.read_bytes())==scripts(prior)
sampling=load(ROOT/'simulation/event_sampling_review/summary.json')
assert sha(ROOT/sampling['source'])==sampling['source_sha256'] and sampling['replay_rows']==1920
assert sampling['physical_validation'] is False and sampling['energy_claim'] is None
control=load(ROOT/'simulation/control_review/checks.json')
assert len(control['checks'])==12 and all(x['passed'] for x in control['checks'])
assert control['hardware_compiled'] is False and control['physical_execution'] is False
pages=load(TMP/'final_pages/pages.json');assert len(pages)==20
for p in pages:assert sha(ROOT/p['file'])==p['sha256']
result={'date':'2026-10-06','scope':'application language, figures, OOXML and local WPS print layout',
        'status':'automated_checks_passed','output':record['output'],'output_sha256':sha(output),
        'pages':20,'native_math_count':27,'superscript_citation_count':11,'references':{'Chinese':5,'English':3},
        'headings':headings,'figure_count':10,'figure_pages':figure_pages,'table_captions':table_captions,
        'centered_body_tables':3,'figure_width_pt':420,'pdf_images':pdf_images,
        'website_scripts_and_data_unchanged':True,'protocol_section_is_ordinary_prose':True,
        'physical_validation':False,'energy_claim':None,'page_receipts':pages}
visual_path=DATA/'visual_review.json'
if visual_path.exists():
    visual=load(visual_path)
    if visual['output_sha256']==sha(output) and visual['page_receipts']==pages:
        assert visual['reviewed_pages']==list(range(1,21))
        result['status']='automated_checks_and_visual_review_passed_with_stated_scope'
        result['visual_review']='application/print_polish/visual_review.json'
(DATA/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Verified:20 pages,10 same-page figures,3 centered tables,27 native equations,11 superscript citations,5+3 references; website logic unchanged.')
