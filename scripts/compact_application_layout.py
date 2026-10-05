"""Adjust pagination of the retained school form without rewriting its content."""
from pathlib import Path
from copy import deepcopy
from lxml import etree as ET
import hashlib, json, shutil, zipfile
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'deliverables/大创申报书_表格与文献修订稿.docx'
DEST = ROOT / 'deliverables/大创申报书_紧凑排版稿.docx'
TMP = ROOT / 'tmp/compact_layout_review'
TMP.mkdir(parents=True, exist_ok=True)
shutil.copy2(SOURCE, TMP / 'input.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS = {'w': W[1:-1], 'v': 'urn:schemas-microsoft-com:vml'}
text = lambda e: ''.join(e.xpath('.//w:t/text()', namespaces=NS))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

with zipfile.ZipFile(SOURCE) as original:
    xml = ET.fromstring(original.read('word/document.xml'))
    outer = xml.find('.//' + W + 'tbl')
    changed = {'empty_keep_next_removed': 0, 'body_paragraphs_may_flow': 0,
               'table_wrappers_may_flow': 0, 'unnecessary_breaks_removed': 0}
    for row in outer.findall(W + 'tr')[16:25]:
        for p in row.xpath('.//w:p', namespaces=NS):
            pr = p.find(W + 'pPr')
            if pr is None:
                continue
            value = text(p)
            has_image = bool(p.xpath('.//v:shape|.//w:drawing', namespaces=NS))
            if not value and not has_image:
                kn = pr.find(W + 'keepNext')
                if kn is not None:
                    kn.set(W + 'val', '0')
                    changed['empty_keep_next_removed'] += 1
                pb = pr.find(W + 'pageBreakBefore')
                if pb is not None and pb.get(W + 'val') != '0':
                    pr.remove(pb)
                    changed['unnecessary_breaks_removed'] += 1
                continue
            if has_image:
                continue  # Retain image size and its caption as one paragraph.
            # Ordinary paragraphs can continue on the next page. Small heading/body
            # holders and each bibliography entry retain their non-splitting rows.
            if p.getparent().getparent().getparent() is outer and len(value) > 50:
                kl = pr.find(W + 'keepLines')
                if kl is not None:
                    kl.set(W + 'val', '0')
                    changed['body_paragraphs_may_flow'] += 1
            spacing = pr.find(W + 'spacing')
            if spacing is not None and len(value) > 50:
                spacing.attrib.pop(W + 'beforeLines', None)
                spacing.attrib.pop(W + 'afterLines', None)
                spacing.set(W + 'before', '0')
                spacing.set(W + 'after', '80')
        for table in row.xpath('.//w:tbl', namespaces=NS):
            rows = table.findall(W + 'tr')
            if not rows:
                continue
            headers = [text(c) for c in rows[0].findall(W + 'tc')]
            if not headers or headers[0] not in ['工作包', '层次', '时段', '用途']:
                continue
            wrapper = table.getparent().getparent().getparent()
            if headers[0] == '时段':
                lock = wrapper.find(W + 'tr/' + W + 'trPr/' + W + 'cantSplit')
                if lock is not None:
                    lock.getparent().remove(lock)
                    changed['table_wrappers_may_flow'] += 1
            # School forms contain nested tables; native WPS does not repeat a
            # nested header reliably. Keep each compact data table together.
            for ri, data_row in enumerate(rows):
                for p in data_row.xpath('./w:tc/w:p', namespaces=NS):
                    pr = p.find(W + 'pPr')
                    kn = pr.find(W + 'keepNext')
                    if kn is not None:
                        kn.set(W + 'val', '1' if ri == 0 else '0')
                    sp = pr.find(W + 'spacing')
                    if sp is not None:
                        sp.attrib.pop(W + 'beforeLines', None)
                        sp.attrib.pop(W + 'afterLines', None)
                        sp.set(W + 'before', '0')
                        sp.set(W + 'after', '20')
    # A standalone section heading followed by a nested table creates an
    # oversized keep-next group in WPS. Pair just the heading and first paragraph.
    rows = outer.findall(W + 'tr')
    cell = rows[20].find(W + 'tc')
    heading = cell.find(W + 'p')
    first = cell.find(W + 'tbl').find('.//' + W + 'p')
    heading_runs = [deepcopy(e) for e in heading if e.tag != W + 'pPr']
    br = ET.Element(W + 'r'); ET.SubElement(br, W + 'br')
    for e in reversed(heading_runs + [br]): first.insert(1, e)
    cell.remove(heading)
    cell = rows[22].find(W + 'tc')
    ps = cell.findall(W + 'p')
    heading, intro = ps[0], ps[1]
    holder = deepcopy(rows[21].find(W + 'tc/' + W + 'tbl'))
    hp = holder.find('.//' + W + 'p')
    for e in list(hp):
        if e.tag != W + 'pPr': hp.remove(e)
    for e in heading:
        if e.tag != W + 'pPr': hp.append(deepcopy(e))
    br = ET.SubElement(hp, W + 'r'); ET.SubElement(br, W + 'br')
    for e in intro:
        if e.tag != W + 'pPr': hp.append(deepcopy(e))
    cell.insert(cell.index(heading), holder)
    cell.remove(heading); cell.remove(intro)
    # Replace only the water schematic with its more compact native-vector
    # layout. Same width, text size, labels, connections and measurement scope.
    rels = ET.fromstring(original.read('word/_rels/document.xml.rels'))
    water = next(s for s in xml.xpath('.//v:shape', namespaces=NS) if (s.get('alt') or '').startswith('图2 '))
    water.set('style', re.sub(r'height:[\d.]+pt', 'height:197.4pt', water.get('style')))
    image = water.find('{urn:schemas-microsoft-com:vml}imagedata')
    rid = image.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    target = next(r.get('Target') for r in rels if r.get('Id') == rid)
    media_path = 'word/' + target
    compact_png = ROOT / 'application/figures/compact_layout/water_layout.png'
    with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED) as out:
        for entry in original.infolist():
            if entry.filename == 'word/document.xml':
                data = ET.tostring(xml, encoding='UTF-8', xml_declaration=True, standalone=True)
            elif entry.filename == media_path:
                data = compact_png.read_bytes()
            else:
                data = original.read(entry.filename)
            out.writestr(entry, data)
record = {'input_path': str(SOURCE), 'input_sha256': sha(SOURCE),
          'output_path': str(DEST), 'changes': changed,
          'text_rewritten': False, 'image_sizes_changed': 'Only figure 2 height; width and printed font sizes retained',
          'compact_figure_sha256': sha(compact_png),
          'body_font_sizes_changed': False, 'school_form_retained': True}
(TMP / 'build_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(json.dumps(changed, ensure_ascii=False))
