"""Rewrite project prose inside the retained school form; preserve user input."""
from pathlib import Path
from copy import deepcopy
import hashlib, json, re, zipfile
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'deliverables/大创申报书_紧凑排版稿.docx'
OUT = ROOT / 'deliverables/大创申报书_语言与范围修订稿.docx'
MD = ROOT / 'application/language_scope_revision/body.md'
TMP = ROOT / 'tmp/language_scope_review'
TMP.mkdir(parents=True, exist_ok=True)
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'v': 'urn:schemas-microsoft-com:vml'}
W = '{' + NS['w'] + '}'
text = lambda e: ''.join(e.xpath('.//w:t/text()', namespaces=NS))
sha = lambda b: hashlib.sha256(b).hexdigest()
original = SOURCE.read_bytes()
(TMP / 'user_input.docx').write_bytes(original)
with zipfile.ZipFile(SOURCE) as z:
    entries = {info.filename: z.read(info.filename) for info in z.infolist()}
root = E.fromstring(entries['word/document.xml'])
outer = root.find(W + 'body/' + W + 'tbl')
rows = outer.findall(W + 'tr')
assert len(rows) == 31
cells = [r.find(W + 'tc') for r in rows[16:25]]
normal = next(p for p in cells[2].findall(W+'p')
              if len(text(p)) > 80 and not p.xpath('.//v:shape', namespaces=NS))
heading_holder = deepcopy(cells[4].find(W + 'tbl'))
assert len(heading_holder.findall(W+'tr')) == 1
data_holders = {}
for t in root.xpath('.//w:tbl', namespaces=NS):
    rs = t.findall(W+'tr')
    if not rs: continue
    key = text(rs[0].find(W+'tc'))
    if key in ['工作包', '层次', '时段', '用途']:
        data_holders[key] = deepcopy(t.getparent().getparent().getparent())
assert len(data_holders) == 4
figures = {}
for p in root.xpath('.//w:p', namespaces=NS):
    shapes = p.xpath('.//v:shape', namespaces=NS)
    if shapes and re.match(r'^图[1-9]\s', text(p)):
        figures[int(re.match(r'^图(\d+)', text(p))[1])] = deepcopy(p)
assert set(figures) == set(range(1, 10))

def property(pr, name, value):
    node = pr.find(W+name)
    if node is None: node = E.SubElement(pr, W+name)
    node.set(W+'val', value)

def run(p, value, bold=False):
    # SimSun silently drops the combining accent in native WPS PDF output.
    # Keep the school body face, and use a math face for this accented symbol.
    for piece in re.split('(R\u0302)', value):
        if not piece:continue
        r = E.SubElement(p, W+'r'); pr = E.SubElement(r, W+'rPr')
        fonts = E.SubElement(pr, W+'rFonts')
        for a in ['ascii', 'hAnsi', 'eastAsia']:
            fonts.set(W+a, 'Cambria Math' if piece == 'R\u0302' else '宋体')
        if bold: E.SubElement(pr, W+'b')
        E.SubElement(pr, W+'sz').set(W+'val', '21')
        E.SubElement(pr, W+'szCs').set(W+'val', '21')
        t = E.SubElement(r, W+'t'); t.text = piece
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    return r

def paragraph(value='', bold=False, centered=False):
    p = deepcopy(normal)
    for child in list(p):
        if child.tag != W+'pPr': p.remove(child)
    pr = p.find(W+'pPr')
    for k in ['pageBreakBefore']:
        node = pr.find(W+k)
        if node is not None: pr.remove(node)
    property(pr, 'keepNext', '0'); property(pr, 'keepLines', '0')
    property(pr, 'widowControl', '1'); property(pr, 'jc', 'center' if centered else 'both')
    sp = pr.find(W+'spacing')
    if sp is None: sp = E.SubElement(pr, W+'spacing')
    sp.attrib.clear(); sp.set(W+'before', '0'); sp.set(W+'after', '80')
    sp.set(W+'line', '240'); sp.set(W+'lineRule', 'auto')
    if centered:
        ind=pr.find(W+'ind')
        if ind is not None: pr.remove(ind)
    if value: run(p, value, bold)
    return p

def heading_block(headings, body):
    table=deepcopy(heading_holder)
    cell=table.find('.//'+W+'tc')
    for el in list(cell):
        if el.tag != W+'tcPr': cell.remove(el)
    p=paragraph()
    property(p.find(W+'pPr'), 'keepLines', '1')
    for h in headings:
        run(p,h,True); E.SubElement(E.SubElement(p,W+'r'),W+'br')
    run(p,body);cell.append(p)
    return table

def figure(number, caption):
    p=deepcopy(figures[number])
    ts=p.xpath('.//w:t', namespaces=NS)
    ts[0].text=caption
    for t in ts[1:]: t.text=''
    for s in p.xpath('.//v:shape', namespaces=NS): s.set('alt',caption)
    return p

def data_table(caption, values):
    holder=deepcopy(data_holders[values[0][0]])
    row=next(r for r in holder.findall(W+'tr') if r.find(W+'tc/'+W+'tbl') is not None)
    for extra in holder.findall(W+'tr'):
        if extra is not row:holder.remove(extra)
    cell=row.find(W+'tc')
    holder.find(W+'tblPr/'+W+'tblW').set(W+'w','9070')
    grid=holder.find(W+'tblGrid')
    for col in list(grid):grid.remove(col)
    E.SubElement(grid,W+'gridCol').set(W+'w','9070')
    cell.find(W+'tcPr/'+W+'tcW').set(W+'w','9070')
    span=cell.find(W+'tcPr/'+W+'gridSpan')
    if span is not None:span.getparent().remove(span)
    table=cell.find(W+'tbl')
    assert table is not None
    rs=table.findall(W+'tr')
    header=deepcopy(rs[0]); body=deepcopy(rs[1]);last=deepcopy(rs[-1])
    for r in rs:table.remove(r)
    for i, vals in enumerate(values):
        row=deepcopy(header if i == 0 else last if i == len(values)-1 else body)
        cs=row.findall(W+'tc');assert len(cs)==len(vals)
        for c,v in zip(cs, vals):
            p=c.find(W+'p')
            for el in list(c):
                if el.tag not in [W+'tcPr', W+'p']: c.remove(el)
            for extra in c.findall(W+'p')[1:]:c.remove(extra)
            for el in list(p):
                if el.tag!=W+'pPr':p.remove(el)
            run(p,v,i==0)
        table.append(row)
    cap=next(p for p in cell.findall(W+'p') if text(p).startswith('表'))
    for el in list(cap):
        if el.tag!=W+'pPr':cap.remove(el)
    run(cap,caption)
    # Preserve all native widths, cell padding, centering and row/header rules.
    return holder

markdown=MD.read_text(encoding='utf-8')
parts=re.split(r'^## ',markdown,flags=re.M)[1:]
assert len(parts)==9
blocks=[];headers=[]
for part,cell in zip(parts,cells):
    lines=part.splitlines();main=lines[0].strip();headers.append(main)
    for el in list(cell):
        if el.tag != W+'tcPr':cell.remove(el)
    pending=[main]; i=1;section=[]
    while i<len(lines):
        value=lines[i].strip();i+=1
        if not value:continue
        if value.startswith('### '):pending.append(value[4:]);continue
        match=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',value)
        if match:
            assert not pending
            caption=match[1];num=int(re.match(r'图(\d+)',caption)[1])
            picture=figure(num,caption)
            if num==5:
                # WPS can separate a caption despite paragraph keepLines in a
                # continued outer form row; keep this image/caption in one row.
                holder=deepcopy(heading_holder);fc=holder.find('.//'+W+'tc')
                for el in list(fc):
                    if el.tag!=W+'tcPr':fc.remove(el)
                fc.append(picture);cell.append(holder)
            else:cell.append(picture)
            section.append({'kind':'figure','caption':caption})
            continue
        if re.match(r'^表\d+\s',value):
            assert not pending
            while i<len(lines) and not lines[i].strip():i+=1
            values=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                vals=[s.strip() for s in lines[i].strip().strip('|').split('|')];i+=1
                if all(re.fullmatch(r'[-: ]+',s) for s in vals):continue
                values.append(vals)
            if cell[-1].tag==W+'tbl':
                # WPS merges adjacent native tables and changes their grid.
                separator=paragraph();sp=separator.find(W+'pPr/'+W+'spacing')
                sp.set(W+'after','0');sp.set(W+'line','20');sp.set(W+'lineRule','exact')
                cell.append(separator)
            cell.append(data_table(value,values));section.append({'kind':'table','caption':value,'rows':len(values)})
            continue
        if pending:
            cell.append(heading_block(pending,value));pending=[]
        else:
            p=paragraph(value)
            if value=='参考文献':
                run_dummy=None
                for el in list(p):
                    if el.tag!=W+'pPr':p.remove(el)
                run(p,value,True);property(p.find(W+'pPr'),'keepNext','1')
            if re.match(r'^\[\d+\]',value):
                property(p.find(W+'pPr'),'keepLines','1')
            cell.append(p)
        section.append({'kind':'paragraph','text':value})
    assert not pending
    if cell[-1].tag!=W+'p':cell.append(paragraph())
    blocks.append(section)

blank_cells=[]
for ri in range(16):
    cs=rows[ri].findall(W+'tc')
    indices=([1] if ri in [0,1,2,5,14,15] else
             list(range(len(cs))) if ri in [4,7,8,9,10] else
             [2,4] if ri in [11,12,13] else [])
    for ci in indices:
        c=cs[ci]
        for t in c.xpath('.//w:t',namespaces=NS):t.text=''
        blank_cells.append([ri,ci])

# Cover values are reserved for the applicant; retained labels and line breaks
# stay in their original positions, including the user's manual title split.
body=root.find(W+'body'); cover_values=[]
for p in body:
    if p is outer:break
    val=text(p)
    if '：' in val and p.tag==W+'p':
        label=val.split('：',1)[0]+'：'
        ts=p.xpath('.//w:t',namespaces=NS)
        if ts:
            ts[0].text=label+'                              '
            for t in ts[1:]:t.text=''
            cover_values.append(label)
    elif val=='障诊断物联网原型系统':
        for t in p.xpath('.//w:t',namespaces=NS):t.text=''

entries['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in entries.items():z.writestr(name,data)
assert SOURCE.read_bytes()==original
record={'input':str(SOURCE),'input_sha256':sha(original),'output':str(OUT),
        'source_markdown':str(MD),'school_sections':headers,'blank_field_cells':blank_cells,
        'blank_cover_values':cover_values,'body_font':'宋体 五号 单倍行距',
        'image_binary_sha256':{k:sha(v) for k,v in entries.items() if k.startswith('word/media/')},
        'image_geometry_unchanged':True,'original_user_file_preserved':True,
        'blocks':blocks,'physical_validation':False}
(ROOT/'application/language_scope_revision/build_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
(ROOT/'application/正式模板正文.md').write_text(markdown,encoding='utf-8',newline='\n')

selected_path=ROOT/'application/申报精选参考文献.json'
selected=json.loads(selected_path.read_text(encoding='utf-8-sig'))
selected['references'][3]={
    'language':'中文','authors':'张晔','title':'棉花膜下“一管四行”滴灌工程设计探讨',
    'journal':'水资源开发与管理','year':2019,'volume':'','issue':'2','pages':'16-19',
    'doi':'10.16616/j.cnki.10-1326/TV.2019.02.04',
    'url':'https://szy.sljsygl.com/UpFiles/2019-07-31/637001611926562500.pdf',
    'support':'新疆规模化棉田膜下滴灌的支管、辅管、毛管层级及轮灌实例',
    'limit':'昌吉工程实例，不作为南疆统一布置或本原型效益的证明',
    'verification':'期刊原文PDF及搜索可读元数据，核对作者、页码、DOI与管网章节',
    'number':4,'citation':next(s for s in markdown.splitlines() if s.startswith('[4]'))}
selected['scope']='language_scope_revision_application';selected['date']='2026-10-05'
selected_path.write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({'output':str(OUT),'source_preserved':True,'main_sections':len(parts),
                  'subheadings':len(re.findall(r'^### ',markdown,re.M)),
                  'blank_fields':len(blank_cells),'characters':len(markdown)},ensure_ascii=False))
