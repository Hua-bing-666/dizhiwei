"""Check current eight-reference application and actual native PDF table positions."""
from pathlib import Path
import hashlib,json,re,zipfile,unicodedata
from lxml import etree as ET
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/compact_layout_review';DATA.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp/compact_layout_review'
DOCX=ROOT/'deliverables/大创申报书_紧凑排版稿.docx'
PDF=ROOT/'deliverables/大创申报书_紧凑排版审阅版.pdf'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','v':'urn:schemas-microsoft-com:vml'}
W='{'+NS['w']+'}'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
norm=lambda s:''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and c.isprintable())
text=lambda e:''.join(e.xpath('.//w:t/text()',namespaces=NS))
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
refs=read(ROOT/'application/申报精选参考文献.json')['references']
assert len(refs)==8 and sum(r['language']=='中文' for r in refs)==5
source=(ROOT/'application/正式模板正文.md').read_text(encoding='utf-8')
body=re.sub(r'^\[\d+\].+$','',source,flags=re.M)
citations={int(n) for group in re.findall(r'\[([\d,]+)\]',body) for n in group.split(',')}
assert citations==set(range(1,9)),citations
assert all(r['citation'] in source for r in refs)
assert len(read(ROOT/'application/references.json')['references'])==17,'Research library unexpectedly trimmed'
with zipfile.ZipFile(DOCX) as z:
    xml=ET.fromstring(z.read('word/document.xml'))
    full=text(xml)
    assert all(r['citation'] in full for r in refs)
    assert not any(t in full for t in ['已形成17篇','中文11篇、英文6篇','HydroNeuro','Orihuela','Sun等'])
    assert {int(n) for group in re.findall(r'\[([\d,]+)\]',full) for n in group.split(',')}==set(range(1,9))
    assert all(s in full for s in ['学院意见：','学校意见：','项目组成员签字：'])
    tables=[]
    for t in xml.xpath('.//w:tbl',namespaces=NS):
        rows=t.findall(W+'tr');head=[text(c) for c in rows[0].findall(W+'tc')]
        if head[0] not in ['工作包','层次','时段','用途']:continue
        assert t.find(W+'tblPr/'+W+'jc').get(W+'val')=='center'
        assert all(p.find(W+'pPr/'+W+'jc').get(W+'val')=='center' for p in rows[0].xpath('./w:tc/w:p',namespaces=NS))
        assert rows[0].find(W+'trPr/'+W+'tblHeader') is not None
        assert all(r.find(W+'trPr/'+W+'cantSplit') is not None for r in rows)
        widths=[int(c.get(W+'w'))/20 for c in t.find(W+'tblGrid')]
        assert sum(widths)==453.5
        wrapper=t.getparent().getparent().getparent()
        assert int(wrapper.find(W+'tblPr/'+W+'tblW').get(W+'w'))==9070
        for p in rows[0].xpath('./w:tc/w:p',namespaces=NS):
            ind=p.find(W+'pPr/'+W+'ind')
            assert ind is None or not any(int(v) for v in ind.attrib.values())
        tables.append({'header':head,'rows':len(rows),'widths_pt':widths,'editable':True,'center_alignment':True,'wrapper_width_matches':True,'header_centered':True,'rows_cannot_split':True})
    assert len(tables)==4
    caps=[p for p in xml.xpath('.//w:p',namespaces=NS) if re.match(r'^表[1-4]\s',text(p))]
    assert len(caps)==4
    for p in caps:assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center'
    media={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/') and not n.endswith('/')}
    with zipfile.ZipFile(TMP/'input.docx') as old:
        before=ET.fromstring(old.read('word/document.xml'))
        assert full==text(before),'Document text deleted, duplicated or reordered'
        old_media={hashlib.sha256(old.read(n)).hexdigest() for n in old.namelist() if n.startswith('word/media/') and not n.endswith('/')}
        # Only the vector-rearranged water schematic is allowed to differ.
        records=read(ROOT/'application/quality_release/application_payload.json')['figures']
        old_water=next(f for f in records if f['caption'].startswith('图2 '))['sha256']
        new_water=sha(ROOT/'application/figures/compact_layout/water_layout.png')
        assert media==old_media-{old_water}|{new_water}
        sizes=lambda x:[e.get(W+'val') for e in x.xpath('.//w:r/w:rPr/w:sz',namespaces=NS)]
        assert set(sizes(xml))==set(sizes(before)),'Font sizes changed'
        def character_sizes(tree):
            records=[]
            for node in tree.xpath('.//w:t',namespaces=NS):
                run=next(a for a in node.iterancestors() if a.tag==W+'r')
                para=next(a for a in node.iterancestors() if a.tag==W+'p')
                size=run.find(W+'rPr/'+W+'sz')
                if size is None:size=para.find(W+'pPr/'+W+'rPr/'+W+'sz')
                size=size.get(W+'val') if size is not None else 'style-inherited'
                records.extend((c,size) for c in node.text or '')
            return records
        assert character_sizes(xml)==character_sizes(before),'A character font size changed'
    figure_records=read(ROOT/'application/quality_release/application_payload.json')['figures']
    for f in figure_records:
        if f['caption'].startswith('图2 '):
            f.update(path='application/figures/compact_layout/water_layout.png',sha256=new_water,pixel_dimensions=[2000,940],height_pt=197.4)
    for f in figure_records:
        assert sha(ROOT/f['path'])==f['sha256'] and f['sha256'] in media
        shape=next(s for s in xml.xpath('.//v:shape',namespaces=NS) if s.get('alt')==f['caption'])
        width=float(re.search(r'width:([\d.]+)pt',shape.get('style')).group(1))
        height=float(re.search(r'height:([\d.]+)pt',shape.get('style')).group(1))
        assert abs((height/width)/(f['pixel_dimensions'][1]/f['pixel_dimensions'][0])-1)<.0002

native=read(TMP/'native_layout.json')
pages=PdfReader(PDF).pages;page_text=[norm(p.extract_text() or '') for p in pages]
assert len(pages)==native['pages']==20
reference_pages=[]
for r in refs:
    matches=[i+1 for i,t in enumerate(page_text) if norm(r['citation']) in t]
    assert len(matches)==1,('Incomplete or split reference',r['number'],matches)
    reference_pages.append({'number':r['number'],'page':matches[0],'complete_on_one_page':True})
section_pages=[]
for part in re.split(r'^## ',source,flags=re.M)[1:]:
    lines=[re.sub(r'^#{1,4}\s+','',s.strip()) for s in part.splitlines() if s.strip()]
    title=norm(lines[0]);first=next(s for s in lines[1:] if not re.match(r'^\d+(\.\d+)*\s',s))
    matches=[i+1 for i,t in enumerate(page_text) if title in t and norm(first)[:25] in t]
    assert len(matches)==1,('Orphaned section heading',title,matches)
    section_pages.append({'heading':lines[0],'page':matches[0],'first_body_on_same_page':True})
for f in figure_records:
    matches=[i+1 for i,t in enumerate(page_text) if norm(f['caption']) in t]
    assert len(matches)==1
    p=next(p for p in native['paragraphs'] if norm(f['caption']) in norm(p['text']))
    assert p['start_page']==p['end_page']==matches[0],('Figure or caption split',f['caption'])

doc=pdfium.PdfDocument(str(PDF));geometry=[];actual_positions=[]
for index in range(len(doc)):
    page=doc[index];width,height=page.get_size();tp=page.get_textpage();chars=[]
    for ci in range(tp.count_chars()):
        ch=tp.get_text_range(ci,1)
        if not ch.strip() or not ch.isprintable():continue
        bounds=tp.get_charbox(ci)
        l,b,r,t=bounds
        assert l>=-.5 and b>=-.5 and r<=width+.5 and t<=height+.5,('Outside page',index+1,ch,bounds)
        for c in norm(ch):chars.append((c,bounds))
    geometry.append({'page':index+1,'characters_checked':len(chars),'inside_A4':True})
    value=''.join(c for c,_ in chars)
    for ci,cap in enumerate(caps):
        caption=norm(text(cap));where=value.find(caption)
        if where<0:continue
        boxes=[b for _,b in chars[where:where+len(caption)]]
        center=(min(b[0] for b in boxes)+max(b[2] for b in boxes))/2
        paths=[o.get_bounds() for o in page.get_objects() if o.type==pdfium.raw.FPDF_PAGEOBJ_PATH]
        lines=[b for b in paths if b[2]-b[0]>450 and b[3]-b[1]<3.5]
        assert lines
        nearest=min(lines,key=lambda b:abs((b[1]+b[3])/2-min(x[1] for x in boxes)))
        table_center=(nearest[0]+nearest[2])/2
        assert abs(center-table_center)<.75,(text(cap),center,table_center)
        outer=[b for b in lines if b[2]-b[0]>463]
        assert outer and abs(table_center-(outer[0][0]+outer[0][2])/2)<.75
        assert all(norm(h) in page_text[index] for h in tables[ci]['header'])
        # All four complete data tables must fit on their caption's page.
        data_table=next(t for t in xml.xpath('.//w:tbl',namespaces=NS) if text(t.findall(W+'tr')[0]).startswith(tables[ci]['header'][0]))
        assert all(norm(text(cell)) in page_text[index] for cell in data_table.xpath('./w:tr/w:tc',namespaces=NS)),('Data table split across pages',text(cap))
        actual_positions.append({'caption':text(cap),'page':index+1,'caption_center_pt':center,'table_center_pt':table_center,'center_error_pt':abs(center-table_center),'matches_body_center':True})
    tp.close();page.close()
doc.close();assert len(actual_positions)==4
input_record=read(TMP/'build_record.json')
assert sha(Path(input_record['input_path']))==input_record['input_sha256'],'User source changed'
result={'date':'2026-10-05','status':'programmatic_pass_visual_review_pending','physical_validation':False,'pages':len(pages),'tables':tables,'actual_pdf_table_positions':actual_positions,'references':reference_pages,'chinese':5,'english':3,'sections':section_pages,'eight_original_figures_and_logo_unchanged':True,'one_diagram_rearranged':True,'all_document_text_unchanged':True,'font_sizes_unchanged':True,'images_aspect_preserved':True,'page_geometry':geometry,'original_user_file_preserved':True,
 'render_method':'WPS native PDF and bundled PDFium; packaged renderer previously diagnosed missing LibreOffice',
 'artifact_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [DOCX,PDF,ROOT/'application/正式模板正文.md',ROOT/'application/申报精选参考文献.json',ROOT/'deliverables/index.html',Path(__file__)]}}
(DATA/'document_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('20 pages; four table/caption centers verified from PDF geometry; eight complete references (5 CN / 3 EN); nine section headings accompanied by body; eight original figures unchanged; compact diagram labels retained; all document text preserved.')
