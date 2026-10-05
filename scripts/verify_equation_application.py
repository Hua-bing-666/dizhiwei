"""Verify native equations after WPS save and preserve all school-form content."""
from pathlib import Path
from collections import Counter
import hashlib, json, re, unicodedata, zipfile
from lxml import etree as E
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'simulation/equation_figure_review'
DOCX = ROOT / 'deliverables/大创申报书_公式与插图修订稿.docx'
PDF = ROOT / 'deliverables/大创申报书_公式与插图审阅版.pdf'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'v': 'urn:schemas-microsoft-com:vml'}
W, M = ('{' + NS[k] + '}' for k in ['w', 'm'])
read = lambda path: json.loads(path.read_text(encoding='utf-8-sig'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
norm = lambda s: ''.join(c for c in unicodedata.normalize('NFKC', s) if c.isprintable() and not c.isspace())

def content(el):
    if el.tag in [W+'t', M+'t']:
        return el.text or ''
    if el.tag in [M+'sSub', M+'sSup']:
        base = content(el.find(M+'e'))
        index = content(el.find(M+('sub' if el.tag == M+'sSub' else 'sup')))
        if el.tag == M+'sSub':
            if base == 'C':
                return base + {'n': 'ₙ', 'l': 'ₗ'}[index]
            return base + index
        assert index == '2'
        return base + '²'
    if el.tag == M+'rad':
        return '√' + content(el.find(M+'e'))
    if el.tag == M+'acc':
        assert el.find(M+'accPr/'+M+'chr').get(M+'val') in ['̂', '^']
        return content(el.find(M+'e')) + '̂'
    if el.tag == M+'f':
        numerator, denominator = (content(el.find(M+k)) for k in ['num', 'den'])
        if '−' in numerator:
            numerator = '(' + numerator + ')'
        return numerator + '/' + denominator
    if el.tag.endswith('Pr') or el.tag in [M+'deg', M+'ctrlPr']:
        return ''
    return ''.join(content(c) for c in el)

record = read(ROOT/'application/equation_figure_revision/build_record.json')
assert sha(ROOT/record['input']) == record['input_sha256'], 'Input was changed'
prior = read(ROOT/'application/language_scope_revision/build_record.json')
with zipfile.ZipFile(DOCX) as z:
    entries = {name: z.read(name) for name in z.namelist()}
with zipfile.ZipFile(ROOT/record['input']) as z:
    old_entries = {name: z.read(name) for name in z.namelist()}
root, old = (E.fromstring(e['word/document.xml']) for e in [entries, old_entries])
maths = root.xpath('.//m:oMath', namespaces=NS)
assert len(maths) == record['native_equation_count'] == 27
assert Counter(content(m) for m in maths) == Counter(m['source'] for m in record['equations'])
for source in ['P0−P1=R·Q²', 'Q=(Cₙ+Cₗ)√P1', 'K=Q/√P1', 'R̂=(P0−P1)/Q²']:
    assert any(content(m) == source for m in maths), source
assert len(root.xpath('.//m:f', namespaces=NS)) == 4
assert len(root.xpath('.//m:rad', namespaces=NS)) == 3
assert len(root.xpath('.//m:acc', namespaces=NS)) >= 4
assert all(not any(ch in content(el) for ch in ['√', 'R̂', 'Cₙ', 'Cₗ'])
           for el in root.xpath('.//w:r[w:t]', namespaces=NS)), 'A structured symbol remains plain text'

old_text = content(old)
for replacement in record['text_replacements']:
    old_text = old_text.replace(replacement['before'], replacement['after'])
assert content(root) == old_text, 'Unexpected prose change or damaged equation'
assert all(hashlib.sha256(entries[name]).hexdigest() == digest for name, digest in record['media_sha256'].items())
unchanged_parts = [name for name, digest in record['preserved_package_parts'].items()
                   if hashlib.sha256(entries[name]).hexdigest() == digest]
changed_parts = sorted(set(record['preserved_package_parts']) - set(unchanged_parts))
assert not set(changed_parts) - {'docProps/core.xml'}, changed_parts
assert root.find(W+'body/'+W+'sectPr') is not None
assert E.tostring(root.find(W+'body/'+W+'sectPr')) == E.tostring(old.find(W+'body/'+W+'sectPr'))
rows = root.find(W+'body/'+W+'tbl').findall(W+'tr')
assert len(rows) == 31
for ri, ci in prior['blank_field_cells']:
    assert not content(rows[ri].findall(W+'tc')[ci]).strip()
assert 'MPM489' not in content(root)
assert '底板初步采用' not in content(root)
new_shapes = root.xpath('.//v:shape', namespaces=NS)
old_shapes = old.xpath('.//v:shape', namespaces=NS)
assert [s.get('style') for s in new_shapes] == [s.get('style') for s in old_shapes]

native = read(ROOT/'tmp/equation_figure_review/native_layout.json')
assert native['native_math_count'] == record['native_equation_count']
pdf = PdfReader(PDF)
assert len(pdf.pages) == native['pages'] == 20
pages = [norm(re.sub(r'(?m)^\s*-\s*\d+\s*-\s*$', '', p.extract_text() or '')) for p in pdf.pages]
joined = ''.join(pages)
for run in root.xpath('.//w:r[w:t]', namespaces=NS):
    value = content(run)
    if len(value.strip()) > 15:
        assert norm(value) in joined, ('Prose missing from PDF', value[:70])

figures = []
for paragraph in root.xpath('.//w:p', namespaces=NS):
    cap = content(paragraph)
    if re.match(r'^图[1-9]\s', cap):
        where = [i+1 for i, t in enumerate(pages) if norm(cap) in t]
        assert len(where) == 1, cap
        positions = [p for p in native['paragraphs'] if norm(p['text']) == norm(cap)]
        assert len(positions) == 1 and positions[0]['start_page'] == positions[0]['end_page'] == where[0], cap
        figures.append({'caption': cap, 'page': where[0], 'figure_caption_same_page': True})
assert len(figures) == 9
references = read(ROOT/'application/申报精选参考文献.json')['references']
assert len(references) == 8 and sum(r['language'] == '中文' for r in references) == 5
ref_pages = [next(i+1 for i, t in enumerate(pages) if norm(ref['citation']) in t) for ref in references]
assert len(set(ref_pages)) == 1

tables = []
document = pdfium.PdfDocument(str(PDF))
for table in root.xpath('.//w:tbl', namespaces=NS):
    table_rows = table.findall(W+'tr')
    head = [content(c) for c in table_rows[0].findall(W+'tc')]
    if head[0] not in ['工作包', '层次', '时段', '用途']:
        continue
    assert table.find(W+'tblPr/'+W+'jc').get(W+'val') == 'center'
    assert sum(int(c.get(W+'w')) for c in table.find(W+'tblGrid')) == 9070
    assert table_rows[0].find(W+'trPr/'+W+'tblHeader') is not None
    assert all(row.find(W+'trPr/'+W+'cantSplit') is not None for row in table_rows)
    caption = next(p for p in table.getparent().findall(W+'p') if content(p).startswith('表'))
    assert caption.find(W+'pPr/'+W+'jc').get(W+'val') == 'center'
    index = next(i for i, t in enumerate(pages) if norm(content(caption)) in t)
    assert all(norm(content(c)) in pages[index] for c in table.xpath('./w:tr/w:tc', namespaces=NS)), 'Table split'
    page = document[index]
    tp = page.get_textpage()
    chars = [(norm(tp.get_text_range(i,1)), tp.get_charbox(i)) for i in range(tp.count_chars())]
    chars = [(c,b) for c,b in chars if c]
    target = norm(content(caption))
    start = ''.join(c for c,b in chars).find(target)
    assert start >= 0
    boxes = [b for c,b in chars[start:start+len(target)]]
    center = (min(b[0] for b in boxes)+max(b[2] for b in boxes))/2
    lines = [o.get_bounds() for o in page.get_objects() if o.type == pdfium.raw.FPDF_PAGEOBJ_PATH]
    lines = [b for b in lines if b[2]-b[0] > 450 and b[3]-b[1] < 3.5]
    line = min(lines, key=lambda b: abs((b[1]+b[3])/2-min(x[1] for x in boxes)))
    error = abs(center-(line[0]+line[2])/2)
    assert error < .75
    tables.append({'caption':content(caption),'page':index+1,'center_error_pt':error,'complete_on_one_page':True})
    tp.close();page.close()
assert len(tables) == 4

geometry, gaps = [], []
for i in range(len(document)):
    page = document[i];tp = page.get_textpage();w,h = page.get_size()
    boxes = [tp.get_charbox(j) for j in range(tp.count_chars()) if tp.get_text_range(j,1).strip()]
    assert all(min(b[0],b[1]) >= -.5 and b[2] <= w+.5 and b[3] <= h+.5 for b in boxes)
    geometry.append({'page':i+1,'glyphs_inside_page':True})
    if 3 <= i <= 17:
        content_boxes = [b for b in boxes if b[1] > 55]
        images = [o.get_bounds() for o in page.get_objects() if o.type == pdfium.raw.FPDF_PAGEOBJ_IMAGE]
        content_boxes.extend(images)
        bottom = min(b[1] for b in content_boxes)
        gap = max(0, bottom-72)
        gaps.append({'page':i+1,'bottom_gap_pt':round(gap,1),'ratio':round(gap/(h-144),3)})
    tp.close();page.close()
document.close()
figure_checks = read(DATA/'figure_checks.json')
assert len(figure_checks['figures']) == 8
for f in figure_checks['figures']:
    assert not f['outside']
    assert f['png_sha256'] == sha(ROOT/'application/figures/equation_revision'/(f['name']+'.png'))
result = {'status':'programmatic_pass_visual_review_required', 'date':'2026-10-05',
          'pages':20,'native_math_objects':len(maths),'WPS_equation_API_count':native['native_math_count'],
          'equation_semantics_retained_after_save':True,'four_core_equations_native':True,
          'body_and_form_content_preserved_except_two_recorded_edits':True,
          'preserved_package_parts':len(unchanged_parts),'changed_metadata_parts':changed_parts,
          'input_preserved':True,'blank_fields':42,'figure_dimensions_preserved':True,
          'figures':figures,'tables':tables,'references':{'chinese':5,'english':3,'page':ref_pages[0]},
          'page_geometry':geometry,'trailing_whitespace':gaps,
          'pages_with_over_25_percent_trailing_whitespace':[g['page'] for g in gaps if g['ratio']>.25],
          'physical_validation':False,
          'artifact_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in
             [DOCX,PDF,ROOT/'application/正式模板正文.md',ROOT/'deliverables/index.html']}}
(DATA/'document_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8',newline='\n')
print(f'Verified: {len(maths)} editable native equations recognized by WPS; exact equation semantics after save; 20 pages, 9 figures, 4 centered tables, 8 references, blank information and original input preserved.')
print('Pages with trailing whitespace >25%:', result['pages_with_over_25_percent_trailing_whitespace'])
