"""Verify the editable execution draft and its native WPS pagination."""
from pathlib import Path
import hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from docx import Document
from PIL import Image
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/quality_review'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def norm(s):return re.sub(r'[\s\x00-\x1f]','',s)

directory=ROOT/'tmp/quality_book';docx=directory/'实施项目书.docx';pdf=directory/'实施项目书.pdf'
source=ROOT/'application/实施项目书.md';contract=read(directory/'layout_contract.json');native=read(directory/'native_layout.json')
pages=PdfReader(pdf).pages;texts=[norm(p.extract_text() or '') for p in pages];alltext=''.join(texts)
assert len(pages)==native['pages']==13
assert len(contract['figures'])==len(native['figures'])==5 and len(contract['tables'])==6
document=Document(docx);assert len(document.tables)==6
headings=re.findall(r'^## (.+)$',source.read_text(encoding='utf-8'),re.M);assert len(headings)==9
heading_checks=[]
for heading in headings:
    index=next(i for i,p in enumerate(native['paragraphs']) if norm(p['text'])==norm(heading))
    p=native['paragraphs'][index];following=native['paragraphs'][index+1]
    assert p['start_page']==p['end_page']==following['start_page'],heading
    heading_checks.append({'heading':heading,'page':p['start_page'],'following_content_same_page':True})
for line in source.read_text(encoding='utf-8').splitlines():
    line=line.strip()
    if not line or line.startswith(('|','![')):continue
    content=re.sub(r'^#{1,3} ','',line)
    assert norm(content) in alltext,('Missing prose',content[:70])
assert all(p['start_page']==p['end_page'] for p in native['paragraphs']), 'A paragraph crosses a page'
assert all(p['start_page']==p['end_page'] for p in native['table_rows']), 'A table row crosses a page'
table_checks=[]
for table,record in zip(document.tables,contract['tables']):
    assert [c.text for c in table.rows[0].cells]==record['header'] and len(table.rows)==record['rows']
    assert all(norm(c.text) in alltext for row in table.rows for c in row.cells)
    assert table.rows[0]._tr.find('w:trPr/w:tblHeader',NS) is not None
    assert all(row._tr.find('w:trPr/w:cantSplit',NS) is not None for row in table.rows)
    actual=[int(c.get('{'+NS['w']+'}w'))/20 for c in table._tbl.findall('w:tblGrid/w:gridCol',NS)]
    assert all(abs(a-b)<.1 for a,b in zip(actual,record['widths_pt']))
    matches=[p for p in native['table_rows'] if norm(p['text'])==norm(''.join(c.text for c in table.rows[-1].cells))]
    assert len(matches)==1
    header_pages=[p['start_page'] for p in native['table_rows'] if norm(p['text'])==norm(''.join(record['header']))]
    assert len(header_pages)==1 and header_pages[0]==matches[0]['start_page'],'Split compact table'
    table_checks.append({**record,'page':header_pages[0],'all_rows_on_one_page':True,'body_font_pt':10.5})
budget=document.tables[3] if document.tables[3].rows[0].cells[0].text=='用途' else next(t for t in document.tables if t.rows[0].cells[0].text=='用途')
assert sum(int(r.cells[1].text) for r in budget.rows[1:-1])==int(budget.rows[-1].cells[1].text)==2000
figures=[]
with zipfile.ZipFile(docx) as archive:
    media={hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.startswith('word/media/')}
    styles=ET.fromstring(archive.read('word/styles.xml'))
    for name in ['Title','Heading 1','Heading 2']:
        style=next(s for s in styles.findall('w:style',NS) if s.find('w:name',NS).get('{'+NS['w']+'}val').casefold()==name.casefold())
        assert style.find('.//w:pBdr',NS) is None
        color=style.find('w:rPr/w:color',NS);assert color is not None and color.get('{'+NS['w']+'}val')=='000000'
    xml=ET.fromstring(archive.read('word/document.xml'));extents=xml.findall('.//wp:extent',NS);assert len(extents)==5
    figure_pdf=pdfium.PdfDocument(str(pdf))
    for record,n,extent in zip(contract['figures'],native['figures'],extents):
        path=ROOT/record['path'];digest=sha(path);assert digest in media
        assert norm(record['caption']) in norm(n['caption'])
        assert n['start_page']==n['end_page'] and norm(record['caption']) in texts[n['start_page']-1]
        width=int(extent.get('cx'))/12700;height=int(extent.get('cy'))/12700
        dimensions=Image.open(path).size;ratio=abs((height/width)/(dimensions[1]/dimensions[0])-1)
        assert abs(width-record['width_pt'])<.001 and ratio<.0002
        page=figure_pdf[n['start_page']-1];images=[o for o in page.get_objects() if o.type==3];assert len(images)==1
        l,b,r,t=images[0].get_bounds();pdf_width=r-l;pdf_height=t-b
        assert abs(pdf_width-width)<.02 and abs(pdf_height-height)<.02
        assert abs((pdf_height/pdf_width)/(dimensions[1]/dimensions[0])-1)<.0002
        # WPS COM reports dimensions rounded to screen pixels. Use encoded EMU
        # and actual native PDF image bounds to verify preserved aspect instead.
        assert abs(n['width_pt']-width)<=.75 and abs(n['height_pt']-height)<=.75
        page.close()
        if 'website_diagnosis_panel' in record['path']:
            c=read(OUT/'website_capture_checks.json')['screenshots'][0];minimum=c['minimumTextPx']*n['width_pt']/c['clip']['width']
        else:
            c=next(c for c in read(OUT/'figure_checks.json')['figures'] if c['name']==path.stem);minimum=c['minFontPt']*n['width_pt']/420
        assert minimum>=9.5
        figures.append({**record,'sha256':digest,'height_pt':height,'page':n['start_page'],'minimum_major_font_pt':minimum,'relative_aspect_error':ratio,'pdf_width_pt':pdf_width,'pdf_height_pt':pdf_height,'com_reported_height_pt':n['height_pt'],'image_and_caption_same_page':True})
    figure_pdf.close()
geometry=[];outside=[];reader=pdfium.PdfDocument(str(pdf))
for i in range(len(reader)):
    page=reader[i];width,height=page.get_size();tp=page.get_textpage()
    assert 594<width<597 and 840<height<843
    for j in range(tp.count_chars()):
        char=tp.get_text_range(j,1)
        if not char.strip():continue
        l,b,r,t=tp.get_charbox(j)
        if l<-.5 or b<-.5 or r>width+.5 or t>height+.5:outside.append({'page':i+1,'char':char})
    geometry.append({'page':i+1,'width_pt':width,'height_pt':height,'characters':tp.count_chars()});tp.close();page.close()
reader.close();assert not outside
pngs=sorted((directory/'render-v4').glob('page-*.png'));assert len(pngs)==len(pages)
comparison=[]
for p in pngs[:12]:
    old=directory/'render-v3'/p.name;assert sha(p)==sha(old),'Earlier inspected page changed'
    comparison.append({'page':int(p.stem.split('-')[1]),'sha256':sha(p),'matches_individually_viewed_previous_render':True})
result={'date':'2026-10-05','status':'passed_programmatic_checks_manual_review_pending','purpose':contract['purpose'],'official_taskbook_template_obtained':False,'physical_validation':False,'native_pdf_pages':len(pages),'figures':figures,'editable_tables':table_checks,'headings':heading_checks,'all_prose_present':True,'all_paragraphs_and_compact_tables_within_single_page':True,'pdf_character_bounds':geometry,'outside_page_characters':outside,'unchanged_reviewed_pages':comparison,'rendered_pages':[{'page':i+1,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for i,p in enumerate(pngs)],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),source,docx,pdf,directory/'native_layout.json',directory/'layout_contract.json',ROOT/'scripts/build_execution_book.py',ROOT/'scripts/export_quality_book.ps1']}}
(OUT/'execution_book_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('13 native pages; all prose/9 chapters/6 editable compact tables/5 exact images verified; prior pages unchanged, last page inspected separately.')
