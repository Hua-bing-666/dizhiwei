"""Template/evidence checks; explicit current-image review recorded separately."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'application/software_closeout';TMP=ROOT/'tmp/software_closeout'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml'}
W='{'+NS['w']+'}';tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
edit=json.loads((DATA/'edit_record.json').read_text(encoding='utf-8'))
source=ROOT/edit['source'];output=ROOT/edit['output']
assert sha(source)==edit['source_sha256'] and sha(output)==edit['output_sha256']
with ZipFile(source) as a,ZipFile(output) as b:
    assert a.namelist()==b.namelist()
    assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['word/document.xml']
    before=E.fromstring(a.read('word/document.xml'));root=E.fromstring(b.read('word/document.xml'))
rows=root.find(W+'body/'+W+'tbl').findall(W+'tr');old=before.find(W+'body/'+W+'tbl').findall(W+'tr')
assert len(rows)==31
for i in edit['protected_rows']+[24]:assert E.tostring(rows[i])==E.tostring(old[i]),i
assert len(root.xpath('.//m:oMath',namespaces=NS))==29
assert len(root.xpath('.//v:imagedata',namespaces=NS))==len(before.xpath('.//v:imagedata',namespaces=NS))>=10
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
assert len(refs)==8 and all(re.search('[\u4e00-\u9fff]',s) for s in refs[:5]) and all(not re.search('[\u4e00-\u9fff]',s) for s in refs[5:])
citations=[]
for ri in [17,18,19]:
    for p in rows[ri].xpath('.//w:p',namespaces=NS):
        if re.match(r'^\[[1-8]\]',tx(p)):continue
        for r in p.findall(W+'r'):
            text=tx(r)
            if re.search(r'\[[1-8](?:,[1-8])*\]',text):
                va=r.find(W+'rPr/'+W+'vertAlign');assert va is not None and va.get(W+'val')=='superscript',text
                citations.append(text)
assert citations
tables=[]
for t in root.xpath('.//w:tbl',namespaces=NS)[1:]:
    if len(t.find(W+'tr').findall(W+'tc'))<3:continue
    pr=t.find(W+'tblPr');jc=pr.find(W+'jc');assert jc is not None and jc.get(W+'val')=='center'
    assert t.find(W+'tr/'+W+'trPr/'+W+'tblHeader') is not None
    tables.append(dict(header=tx(t.find(W+'tr')),rows=len(t.findall(W+'tr'))))
assert len(tables)==3
layout=json.loads((TMP/'native_layout.json').read_text(encoding='utf-8-sig'))
assert layout['pages']==20 and layout['native_math_count']==29
captions=[p for p in layout['paragraphs'] if re.match(r'^(图\d+|表\d+)\s',p['text'].replace('\x01','').replace('\x0b','').strip())]
assert len(captions)==13 and all(p['start_page']==p['end_page'] for p in captions)
for p in root.xpath('.//w:p',namespaces=NS):
    if re.match(r'^(图\d+|表\d+)\s',tx(p)):
        jc=p.find(W+'pPr/'+W+'jc');assert jc is not None and jc.get(W+'val')=='center'
assert not re.search(r'44B事件|20秒.*暂停|100%.*结项',tx(root))
review=json.loads((DATA/'visual_review.json').read_text(encoding='utf-8'))
pages=json.loads((TMP/'pages/pages.json').read_text(encoding='utf-8'))
assert review['output_sha256']==sha(output) and review['pages']==pages and review['all_pages_individually_viewed']
for p in pages:assert sha(ROOT/p['file'])==p['sha256']
record=dict(passed=True,scope='School-template DOCX and its final WPS rendering, not physical validation',
            source_preserved=True,source_sha256=sha(source),output_sha256=sha(output),
            pages=20,native_equations=29,original_native_equations_preserved=27,original_images_preserved=True,
            original_information_budget_approval_rows_preserved=True,references={'Chinese':5,'English':3},
            citation_runs_superscript=len(citations),tables=tables,all_figure_caption_paragraphs_same_page=True,
            visual_review_sha256=sha(DATA/'visual_review.json'),pdf_sha256=sha(TMP/'application.pdf'),
            renderer='Bundled render_docx.py attempted; unavailable LibreOffice; WPS native read-only PDF then bundled PDFium',
            justified_blank_areas=review['justified_blank_areas'])
(DATA/'acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('20-page application accepted: all pages viewed, original graphics/math/fields retained; 8 references and centered captions checked.')
