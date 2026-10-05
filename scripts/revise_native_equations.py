"""Patch the latest application with editable Office Math and revised figures."""
from pathlib import Path
from copy import deepcopy
import hashlib, json, re, zipfile
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'deliverables/大创申报书_语言与范围修订稿.docx'
OUT = ROOT / 'deliverables/大创申报书_公式与插图修订稿.docx'
DATA = ROOT / 'application/equation_figure_revision'
TMP = ROOT / 'tmp/equation_figure_review'
DATA.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'v': 'urn:schemas-microsoft-com:vml',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W, M = ('{' + NS[k] + '}' for k in ['w', 'm'])
R = '{' + NS['r'] + '}'
E.register_namespace('m', NS['m'])
sha = lambda value: hashlib.sha256(value).hexdigest()
text = lambda e: ''.join(e.xpath('.//w:t/text()', namespaces=NS))

def mr(value, plain=False):
    r = E.Element(M + 'r')
    if plain:
        pr = E.SubElement(r, M + 'rPr')
        E.SubElement(pr, M + 'sty').set(M + 'val', 'p')
    pr = E.SubElement(r, W + 'rPr')
    font = E.SubElement(pr, W + 'rFonts')
    for key in ['ascii', 'hAnsi', 'eastAsia']:
        font.set(W + key, 'Cambria Math')
    E.SubElement(pr, W + 'sz').set(W + 'val', '21')
    E.SubElement(pr, W + 'szCs').set(W + 'val', '21')
    E.SubElement(r, M + 't').text = value
    return r

def group(tag, *nodes):
    result = E.Element(M + tag)
    for node in nodes:
        result.append(node)
    return result

def sub(base, index):
    return group('sSub', group('e', mr(base)), group('sub', mr(index, True)))

def sup(base, index='2'):
    return group('sSup', group('e', base), group('sup', mr(index, True)))

def rad(base):
    r = E.Element(M + 'rad')
    pr = E.SubElement(r, M + 'radPr')
    E.SubElement(pr, M + 'degHide').set(M + 'val', '1')
    E.SubElement(r, M + 'deg')
    r.append(group('e', base))
    return r

def frac(numerator, denominator):
    return group('f', group('num', *numerator), group('den', *denominator))

def hat():
    a = E.Element(M + 'acc')
    pr = E.SubElement(a, M + 'accPr')
    E.SubElement(pr, M + 'chr').set(M + 'val', '\u0302')
    a.append(group('e', mr('R')))
    return a

def p(index):
    return sub('P', index)

def difference():
    return [p('0'), mr('−', True), p('1')]

def math_expr(token):
    result = E.Element(M + 'oMath')
    if token == 'P0−P1=R·Q²':
        nodes = difference() + [mr('=', True), mr('R'), mr('·', True), sup(mr('Q'))]
    elif token == 'Q=(Cₙ+Cₗ)√P1':
        nodes = [mr('Q'), mr('=', True), mr('(', True), sub('C', 'n'),
                 mr('+', True), sub('C', 'l'), mr(')', True), rad(p('1'))]
    elif token == 'K=Q/√P1':
        nodes = [mr('K'), mr('=', True), frac([mr('Q')], [rad(p('1'))])]
    elif token == 'R̂=(P0−P1)/Q²':
        nodes = [hat(), mr('=', True), frac(difference(), [sup(mr('Q'))])]
    elif token == 'kPa/(L/min)²':
        nodes = [frac([mr('kPa', True)], [sup(mr('(L/min)', True))])]
    elif token == '(L/min)/√kPa':
        nodes = [frac([mr('(L/min)', True)], [rad(mr('kPa', True))])]
    elif token in ['P0', 'P1']:
        nodes = [p(token[-1])]
    elif token in ['Cₙ', 'Cₗ']:
        nodes = [sub('C', 'n' if token == 'Cₙ' else 'l')]
    elif token == 'R̂':
        nodes = [hat()]
    elif token == 'Cₙ=0.28':
        nodes = [sub('C', 'n'), mr('=', True), mr('0.28', True)]
    elif token == 'R=0.8':
        nodes = [mr('R'), mr('=', True), mr('0.8', True)]
    else:
        assert token == 'σ'
        nodes = [mr('σ')]
    for node in nodes:
        result.append(node)
    return result

TOKENS = ['P0−P1=R·Q²', 'Q=(Cₙ+Cₗ)√P1', 'K=Q/√P1', 'R̂=(P0−P1)/Q²',
          'kPa/(L/min)²', '(L/min)/√kPa', 'Cₙ=0.28', 'R=0.8', 'P0', 'P1', 'Cₙ', 'Cₗ', 'R̂', 'σ']
PATTERN = re.compile('|'.join(
    r'(?<![A-Za-z0-9_])' + re.escape(t) + r'(?![A-Za-z0-9_])'
    if t in ['P0', 'P1'] else re.escape(t)
    for t in sorted(TOKENS, key=len, reverse=True)))
REWRITE = {
    '，可采用满足相应规格的MPM489系列产品': '',
    '底板初步采用900×520mm、管中心高度140mm的布局。': '结构布局兼顾测点访问、活接拆装和收集容器取放。'
}
original = SOURCE.read_bytes()
(TMP / 'input.docx').write_bytes(original)
with zipfile.ZipFile(SOURCE) as z:
    entries = {info.filename: z.read(info.filename) for info in z.infolist()}
root = E.fromstring(entries['word/document.xml'])
relationships = E.fromstring(entries['word/_rels/document.xml.rels'])
relmap = {el.get('Id'): el.get('Target') for el in relationships}
outer = root.find(W + 'body/' + W + 'tbl')
rows = outer.findall(W + 'tr')
equations, changed_paragraphs = [], []

def simple_run(child):
    return child.tag == W + 'r' and child.find(W + 't') is not None and all(
        x.tag in [W + 'rPr', W + 't'] for x in child)

for row in rows[16:25]:
    for paragraph in row.xpath('.//w:p', namespaces=NS):
        if paragraph.xpath('.//v:shape', namespaces=NS):
            continue
        children = list(paragraph)
        i = 0
        while i < len(children):
            if not simple_run(children[i]):
                i += 1
                continue
            start = i
            while i < len(children) and simple_run(children[i]):
                i += 1
            cluster = children[start:i]
            value = ''.join(text(run) for run in cluster)
            newvalue = value
            for old, new in REWRITE.items():
                newvalue = newvalue.replace(old, new)
            matches = list(PATTERN.finditer(newvalue))
            if not matches and newvalue == value:
                continue
            # Preserve the original text's formatting; heading breaks delimit clusters.
            template = cluster[0]
            nodes, offset = [], 0
            def plain_piece(piece):
                run = deepcopy(template)
                for el in list(run):
                    if el.tag != W + 'rPr':
                        run.remove(el)
                t = E.SubElement(run, W + 't')
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                t.text = piece
                return run
            for match in matches:
                if match.start() > offset:
                    nodes.append(plain_piece(newvalue[offset:match.start()]))
                nodes.append(math_expr(match[0]))
                equations.append({'source': match[0]})
                offset = match.end()
            if offset < len(newvalue):
                nodes.append(plain_piece(newvalue[offset:]))
            pos = paragraph.index(cluster[0])
            for old in cluster:
                paragraph.remove(old)
            for node in nodes:
                paragraph.insert(pos, node)
                pos += 1
            if newvalue != value:
                changed_paragraphs.append({'before': value, 'after': newvalue})

figure_names = {1: 'system_responsibilities', 2: 'water_layout', 3: 'collection_overview',
                4: 'measurement_interfaces', 5: 'diagnosis_proposal', 6: 'durable_event_sequence',
                8: 'noise_outcomes_print', 9: 'failure_counterexamples'}
replaced = []
for paragraph in root.xpath('.//w:p', namespaces=NS):
    caption = text(paragraph)
    match = re.match(r'^图([1-9])\s', caption)
    if not match:
        continue
    n = int(match[1])
    if n not in figure_names:
        continue
    image = paragraph.find('.//{' + NS['v'] + '}imagedata')
    assert image is not None
    part = 'word/' + relmap[image.get(R + 'id')]
    assert part.endswith('.png')
    source = ROOT / 'application/figures/equation_revision' / (figure_names[n] + '.png')
    entries[part] = source.read_bytes()
    replaced.append({'figure': n, 'part': part, 'source': source.relative_to(ROOT).as_posix(),
                     'sha256': sha(entries[part])})
assert len(replaced) == 8
assert all(any(x['source'] == token for x in equations) for token in TOKENS[:4])

settings = E.fromstring(entries['word/settings.xml'])
properties = settings.find(M + 'mathPr')
if properties is None:
    properties = E.SubElement(settings, M + 'mathPr')
font = properties.find(M + 'mathFont')
if font is None:
    font = E.SubElement(properties, M + 'mathFont')
font.set(M + 'val', 'Cambria Math')
entries['word/document.xml'] = E.tostring(root, encoding='utf-8', xml_declaration=True, standalone=True)
entries['word/settings.xml'] = E.tostring(settings, encoding='utf-8', xml_declaration=True, standalone=True)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in entries.items():
        z.writestr(name, data)
assert SOURCE.read_bytes() == original
md = (ROOT / 'application/language_scope_revision/body.md').read_text(encoding='utf-8')
for old, new in REWRITE.items():
    md = md.replace(old, new)
for name in figure_names.values():
    md = md.replace('figures/quality_review/' + name, 'figures/equation_revision/' + name)
(DATA / 'body.md').write_text(md, encoding='utf-8', newline='\n')
(ROOT / 'application/正式模板正文.md').write_text(md, encoding='utf-8', newline='\n')
record = {'input': SOURCE.relative_to(ROOT).as_posix(), 'input_sha256': sha(original),
          'output': OUT.relative_to(ROOT).as_posix(), 'native_equation_count': len(equations),
          'equations': equations, 'replaced_figures': replaced,
          'text_replacements': changed_paragraphs, 'physical_validation': False,
          'preserved_package_parts': {k: sha(v) for k, v in entries.items()
             if k not in ['word/document.xml', 'word/settings.xml'] and not k.startswith('word/media/')},
          'media_sha256': {k: sha(v) for k, v in entries.items() if k.startswith('word/media/')}}
(DATA / 'build_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n',
                                      encoding='utf-8', newline='\n')
(TMP / 'artifact.md').write_text('Retained reference: ' + str(SOURCE) + '\nSHA256: ' + sha(original) +
    '\nNarrow edit: inline native OMML, eight label-only figure variants, two local prose edits.\n' +
    'Preserve school page system, form, fonts, four centered tables, approval areas and blank fields.\n' +
    'Figure geometry and synthetic data unchanged. Inspect all new rendered pages.\n', encoding='utf-8')
print(f'Created application with {len(equations)} native Office Math objects and eight revised figures.')
