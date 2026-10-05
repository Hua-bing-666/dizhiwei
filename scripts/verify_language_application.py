"""Verify rewritten project claims, native layout and retained school form."""
from pathlib import Path
import hashlib, json, re, unicodedata, zipfile
from lxml import etree as E
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/language_scope_review';DATA.mkdir(parents=True,exist_ok=True)
DOCX=ROOT/'deliverables/大创申报书_语言与范围修订稿.docx'
PDF=ROOT/'deliverables/大创申报书_语言与范围修订审阅版.pdf'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda s:''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and c.isprintable())
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','v':'urn:schemas-microsoft-com:vml'}
W='{'+NS['w']+'}'
text=lambda e:''.join(e.xpath('.//w:t/text()',namespaces=NS))
record=read(ROOT/'application/language_scope_revision/build_record.json')
assert sha(Path(record['input']))==record['input_sha256'],'The user input changed'
md=(ROOT/'application/正式模板正文.md').read_text(encoding='utf-8')
assert md==(ROOT/'application/language_scope_revision/body.md').read_text(encoding='utf-8')
refs=read(ROOT/'application/申报精选参考文献.json')['references']
assert len(refs)==8 and sum(r['language']=='中文' for r in refs)==5
assert all(r['citation'] in md for r in refs)
cited={int(v) for g in re.findall(r'\[([\d,]+)\]',re.sub(r'^\[\d+\].*$', '', md,flags=re.M)) for v in g.split(',')}
assert cited==set(range(1,9))
old_library=read(ROOT/'application/references.json')
assert len(old_library['references'])==17

with zipfile.ZipFile(DOCX) as z:
    root=E.fromstring(z.read('word/document.xml'));full=text(root)
    media={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
    assert media==record['image_binary_sha256'],'A retained illustration changed'
    outer=root.find(W+'body/'+W+'tbl');rows=outer.findall(W+'tr')
    assert len(rows)==31
    for ri,ci in record['blank_field_cells']:
        assert not text(rows[ri].findall(W+'tc')[ci]).strip(),('Field not blank',ri,ci)
    for el in root.find(W+'body'):
        if el is outer:break
        if '：' in text(el):assert not text(el).split('：',1)[1].strip()
    project_text=''.join(text(r) for r in rows[16:25])
    assert not any(x in project_text for x in ['待填写','待本人','尚待确认','具体支持尚待','负责人为','负责人会焊接','实际成员名单','预算帽','立项级别不能','不是学校资助'])
    assert all(x in project_text for x in ['南疆规模化棉田','膜下滴灌','轮灌支管','局部过流受限','具体漏点由人工检查确认','实物制造后','合成试次','480','960','18次','1/20','2/20','61秒','田间迁移仍需重新标定','少量健康数据重新标定','多支管分区诊断','误导次数'])
    # Validate every drafted block against the actual editable document.
    for section in record['blocks']:
        for block in section:
            if block['kind']=='paragraph':assert block['text'] in full,block['text'][:35]
            else:assert block['caption'] in full
    for ri in range(16,25):
        for run in rows[ri].xpath('.//w:r[w:t]',namespaces=NS):
            value=text(run)
            expected='19' if re.match(r'^图[1-9]\s',value) else '21'
            assert run.find(W+'rPr/'+W+'sz').get(W+'val')==expected
    with zipfile.ZipFile(ROOT/'tmp/language_scope_review/user_input.docx') as old:
        before=E.fromstring(old.read('word/document.xml'))
        old_rows=before.find(W+'body/'+W+'tbl').findall(W+'tr')
        assert [text(r) for r in rows[25:]]==[text(r) for r in old_rows[25:]]
        old_shapes=[s for s in before.xpath('.//v:shape',namespaces=NS) if (s.get('alt') or '').startswith('图')]
    shapes=[s for s in root.xpath('.//v:shape',namespaces=NS) if (s.get('alt') or '').startswith('图')]
    assert len(shapes)==len(old_shapes)==9
    assert [s.get('style') for s in shapes]==[s.get('style') for s in old_shapes]
    tables=[];caps=[]
    for table in root.xpath('.//w:tbl',namespaces=NS):
        trs=table.findall(W+'tr');head=[text(c) for c in trs[0].findall(W+'tc')]
        if head[0] not in ['工作包','层次','时段','用途']:continue
        assert table.find(W+'tblPr/'+W+'jc').get(W+'val')=='center'
        assert sum(int(c.get(W+'w')) for c in table.find(W+'tblGrid'))==9070
        assert trs[0].find(W+'trPr/'+W+'tblHeader') is not None
        assert all(r.find(W+'trPr/'+W+'cantSplit') is not None for r in trs)
        assert all(p.find(W+'pPr/'+W+'jc').get(W+'val')=='center' for p in trs[0].xpath('./w:tc/w:p',namespaces=NS))
        wrapper=table.getparent().getparent().getparent()
        assert wrapper.find(W+'tblPr/'+W+'tblW').get(W+'w')=='9070'
        cap=next(p for p in table.getparent().findall(W+'p') if text(p).startswith('表'))
        assert cap.find(W+'pPr/'+W+'jc').get(W+'val')=='center'
        caps.append(cap);tables.append(table)
    assert len(tables)==4
    budget=[int(text(r.findall(W+'tc')[1])) for r in tables[-1].findall(W+'tr')[1:]]
    assert sum(budget[:-1])==budget[-1]==2000

native=read(ROOT/'tmp/language_scope_review/native_layout.json')
pdf=PdfReader(PDF);assert len(pdf.pages)==native['pages']
page_text=[]
for page in pdf.pages:
    value=page.extract_text() or ''
    value=re.sub(r'(?m)^\s*-\s*\d+\s*-\s*$', '', value)
    page_text.append(norm(value))
joined=''.join(page_text)
for section in record['blocks']:
    for block in section:
        target=block['text'] if block['kind']=='paragraph' else block['caption']
        assert norm(target) in joined,('Missing or corrupted PDF text',target[:60])
assert '\u0302' in ''.join(p.extract_text() or '' for p in pdf.pages),'Math accent dropped'
ref_pages=[]
for r in refs:
    matches=[i+1 for i,s in enumerate(page_text) if norm(r['citation']) in s]
    assert len(matches)==1,('Reference split or missing',r['number'],matches)
    ref_pages.append({'number':r['number'],'page':matches[0]})
for heading,section in zip(record['school_sections'],record['blocks']):
    first=next(b['text'] for b in section if b['kind']=='paragraph')
    assert any(norm(heading) in s and norm(first) in s for s in page_text),('Orphaned heading',heading)
figure_pages=[]
for shape in shapes:
    cap=shape.get('alt');positions=[i+1 for i,s in enumerate(page_text) if norm(cap) in s]
    assert len(positions)==1
    para=next(p for p in native['paragraphs'] if norm(cap) in norm(p['text']))
    assert para['start_page']==para['end_page']==positions[0]
    figure_pages.append({'caption':cap,'page':positions[0],'figure_and_caption_together':True})

doc=pdfium.PdfDocument(str(PDF));centers=[];gaps=[];geometry=[]
for index in range(len(doc)):
    page=doc[index];width,height=page.get_size();tp=page.get_textpage();chars=[];body_boxes=[]
    for ci in range(tp.count_chars()):
        ch=tp.get_text_range(ci,1)
        if not ch.strip() or not ch.isprintable():continue
        b=tp.get_charbox(ci);l,bot,r,top=b
        assert l>=-.5 and bot>=-.5 and r<=width+.5 and top<=height+.5
        chars.extend((c,b) for c in norm(ch))
        if bot>=71 and top<=height-69:body_boxes.append(b)
    geometry.append({'page':index+1,'glyphs_checked':len(chars),'inside_A4':True})
    images=[o.get_bounds() for o in page.get_objects() if o.type==pdfium.raw.FPDF_PAGEOBJ_IMAGE]
    body_boxes.extend(images)
    if 3<=index<len(doc)-2:
        gap=max(0,min(b[1] for b in body_boxes)-70.9)
        gaps.append({'page':index+1,'bottom_gap_pt':round(gap,1),'ratio':round(gap/(height-141.8),3)})
    value=''.join(c for c,_ in chars)
    for table,cap in zip(tables,caps):
        where=value.find(norm(text(cap)))
        if where<0:continue
        boxes=[b for _,b in chars[where:where+len(norm(text(cap)))]]
        cap_center=(min(b[0] for b in boxes)+max(b[2] for b in boxes))/2
        paths=[o.get_bounds() for o in page.get_objects() if o.type==pdfium.raw.FPDF_PAGEOBJ_PATH]
        lines=[b for b in paths if b[2]-b[0]>450 and b[3]-b[1]<3.5]
        near=min(lines,key=lambda b:abs((b[1]+b[3])/2-min(x[1] for x in boxes)))
        table_center=(near[0]+near[2])/2
        assert abs(cap_center-table_center)<.75
        assert all(norm(text(c)) in page_text[index] for c in table.xpath('./w:tr/w:tc',namespaces=NS)),('Table split',text(cap))
        centers.append({'caption':text(cap),'page':index+1,'caption_center_pt':cap_center,
                        'table_center_pt':table_center,'error_pt':abs(cap_center-table_center),'complete_on_one_page':True})
    tp.close();page.close()
doc.close();assert len(centers)==4
result={'status':'programmatic_pass_visual_record_required','date':'2026-10-05','pages':len(pdf.pages),
        'blank_field_cells':len(record['blank_field_cells']),'school_template_retained':True,
        'images':figure_pages,'image_binaries_and_sizes_unchanged':True,
        'tables':centers,'references':ref_pages,'chinese':5,'english':3,
        'all_drafted_text_in_docx_and_pdf':True,'math_accent_preserved':True,
        'budget_total':2000,'input_preserved':True,'physical_validation':False,
        'trailing_whitespace':gaps,'body_pages_over_25_percent':[g['page'] for g in gaps if g['ratio']>.25],
        'page_geometry':geometry,'render_method':'Native WPS PDF and bundled PDFium; packaged renderer missing LibreOffice',
        'artifact_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [DOCX,PDF,ROOT/'application/正式模板正文.md',ROOT/'application/申报精选参考文献.json',ROOT/'deliverables/index.html']}}
(DATA/'document_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(f'Verified: {len(pdf.pages)} pages; 42 blank fields; 9 retained illustrations; 4 centered complete tables; 8 references (5 CN / 3 EN); complete prose and math in DOCX/PDF; user input preserved.')
print('Body pages with trailing whitespace >25%:',result['body_pages_over_25_percent'])
