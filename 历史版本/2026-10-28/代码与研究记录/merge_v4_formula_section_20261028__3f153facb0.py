"""Replace only sections 3.3.3 and 3.3.4, preserving all other package parts."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from hashlib import sha256
from lxml import etree as E
import json, re, shutil

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('C:/Users/Lenovo/Desktop/大创申报书v4.docx')
SNIPPET=ROOT/'deliverables/3_测量平台与软件设计_公式规范精简稿.docx'
QA=ROOT/'tmp/v4_section_merge_20261028'
QA.mkdir(parents=True,exist_ok=True)
OUT=QA/'大创申报书v4_替换校核稿.docx'
BACKUP=QA/'大创申报书v4_原始备份.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'rel':'http://schemas.openxmlformats.org/package/2006/relationships'}
def q(prefix,tag): return '{'+NS[prefix]+'}'+tag
def text(n): return ''.join(n.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))
def canon(n): return E.tostring(n,method='c14n')
base_hash=sha256(BASE.read_bytes()).hexdigest()
if not BACKUP.exists(): shutil.copy2(BASE,BACKUP)
else: assert sha256(BACKUP.read_bytes()).hexdigest()==base_hash,'Input changed since the recorded backup'
with ZipFile(BASE) as z:
    infos=z.infolist();original={n.filename:z.read(n.filename) for n in infos}
with ZipFile(SNIPPET) as z: src={n.filename:z.read(n.filename) for n in z.infolist()}
base=E.fromstring(original['word/document.xml'])
source=E.fromstring(src['word/document.xml'])
rels=E.fromstring(original['word/_rels/document.xml.rels'])
src_rels=E.fromstring(src['word/_rels/document.xml.rels'])
start=next(p for p in base.xpath('//w:p',namespaces=NS) if text(p).startswith('3.3.3.'))
cell=start.getparent();assert cell.tag==q('w','tc')
end=next(c for c in cell if text(c).startswith('3.4.'))
begin=cell.index(start);finish=cell.index(end)
removed=list(cell)[begin:finish]
new=[deepcopy(n) for n in source.find(q('w','body')) if n.tag!=q('w','sectPr')]
assert text(new[0]).startswith('3.3.3')
assert any(text(n).startswith('3.3.4') for n in new)
assert len([n for n in new if n.tag==q('w','tbl')])==6
normal=E.fromstring(src['word/styles.xml']).xpath('//w:style[w:name/@w:val="Normal"]',namespaces=NS)[0]
default_pp=normal.find(q('w','pPr'))
default_rp=normal.find(q('w','rPr'))
punctuation=set('，。；：、！？（）【】《》“”‘’…—')
ascii_to_chinese={',':'，',';':'；',':':'：','!':'！','?':'？'}

def font_song(run,math=False):
    wp=run.find(q('w','rPr'))
    if wp is None:
        wp=E.Element(q('w','rPr'))
        run.insert(1 if math and run.find(q('m','rPr')) is not None else 0,wp)
    f=wp.find(q('w','rFonts'))
    if f is None: f=E.Element(q('w','rFonts'));wp.insert(0,f)
    for key in ('ascii','hAnsi','eastAsia','cs'): f.set(q('w',key),'宋体')
    if math:
        mp=run.find(q('m','rPr'))
        if mp is None: mp=E.Element(q('m','rPr'));run.insert(0,mp)
        sty=mp.find(q('m','sty'))
        if sty is None: sty=E.Element(q('m','sty'));mp.append(sty)
        sty.set(q('m','val'),'p')
        if mp.find(q('m','nor')) is None: mp.insert(0,E.Element(q('m','nor')))

space_removed=0
punct_runs=0
for block in new:
    # Freeze the imported section's paragraph defaults locally, leaving v4
    # styles.xml and all unrelated paragraphs unchanged.
    paragraphs=([block] if block.tag==q('w','p') else [])+block.xpath('.//w:p',namespaces=NS)
    for p in paragraphs:
        pp=p.find(q('w','pPr'))
        if pp is None: pp=E.Element(q('w','pPr'));p.insert(0,pp)
        for prop in default_pp:
            old=pp.find(prop.tag)
            if old is None: pp.append(deepcopy(prop))
            else:
                for key,value in prop.attrib.items():
                    if key not in old.attrib: old.set(key,value)
        if pp.find(q('w','rPr')) is None: pp.append(deepcopy(default_rp))
    # The final sentence punctuation is outside the display equation by request.
    for om in block.xpath('.//m:oMathPara/m:oMath',namespaces=NS):
        while len(om) and om[-1].tag==q('m','r') and text(om[-1]).strip() in ('，',',','。',';','；'):
            om.remove(om[-1])
    # Split punctuation into explicit Song-font runs. Mathematical index commas
    # and delimiter symbols retain their syntax; prose uses Chinese punctuation.
    for run in list(block.xpath('.//w:r[w:t]|.//m:r[m:t]',namespaces=NS)):
        math=run.tag==q('m','r'); tn=run.find(q('m' if math else 'w','t'))
        if tn is None: continue
        value=tn.text or ''
        cleaned=''.join(ch for ch in value if ch not in ' \u00a0\u2002\u2003\u2009\u202f\u3000')
        space_removed+=len(value)-len(cleaned)
        if not math: cleaned=''.join(ascii_to_chinese.get(ch,ch) for ch in cleaned)
        if not cleaned:
            run.getparent().remove(run);continue
        def is_punc(ch): return ch in punctuation or ch in ',;:'
        segments=[]
        for ch in cleaned:
            flag=is_punc(ch)
            if segments and segments[-1][0]==flag: segments[-1]=(flag,segments[-1][1]+ch)
            else: segments.append((flag,ch))
        parent=run.getparent();at=parent.index(run)
        for flag,value in segments:
            clone=deepcopy(run);ct=clone.find(q('m' if math else 'w','t'));ct.text=value
            ct.attrib.pop('{http://www.w3.org/XML/1998/namespace}space',None)
            if flag: font_song(clone,math);punct_runs+=1
            parent.insert(at,clone);at+=1
        parent.remove(run)

# Keep each inserted image and its caption in one non-splitting paragraph.
# WPS may ignore keepNext between paragraphs in a long enclosing template cell.
for index in range(len(new)-2,-1,-1):
    picture,caption=new[index:index+2]
    if picture.tag!=q('w','p') or not picture.xpath('.//wp:inline',namespaces=NS): continue
    if caption.tag!=q('w','p') or not text(caption).startswith('图3-'): continue
    br=E.SubElement(picture,q('w','r'));E.SubElement(br,q('w','br'))
    for child in caption:
        if child.tag!=q('w','pPr'): picture.append(deepcopy(child))
    pp=picture.find(q('w','pPr'))
    keep=pp.find(q('w','keepNext'))
    if keep is not None: keep.set(q('w','val'),'0')
    spacing=pp.find(q('w','spacing'));spacing.set(q('w','after'),'60')
    new.pop(index+1)

# Preserve media by content hash; add only genuinely new section images.
target_rel_by_id={n.get('Id'):n for n in rels}
target_by_hash={}
for n in rels:
    if n.get('Type','').endswith('/image'):
        part=str(PurePosixPath('word')/n.get('Target'))
        if part in original: target_by_hash[sha256(original[part]).hexdigest()]=n.get('Id')
src_rel_by_id={n.get('Id'):n for n in src_rels}
used={v for b in new for n in b.iter() for k,v in n.attrib.items() if k.startswith('{'+NS['r']+'}')}
additions={};mapping={}
next_rel=max([int(n.get('Id')[3:]) for n in rels if re.fullmatch(r'rId\d+',n.get('Id',''))]+[0])+1
for old_id in sorted(used):
    relation=src_rel_by_id[old_id]
    assert relation.get('Type','').endswith('/image'),'Unexpected source relationship'
    original_part=str(PurePosixPath('word')/relation.get('Target'))
    payload=src[original_part];digest=sha256(payload).hexdigest()
    if digest in target_by_hash: mapping[old_id]=target_by_hash[digest];continue
    name='section_formula_20261028_'+digest[:16]+PurePosixPath(original_part).suffix
    part='word/media/'+name
    additions[part]=payload
    rid='rId'+str(next_rel);next_rel+=1
    n=E.SubElement(rels,'{'+NS['rel']+'}Relationship')
    n.set('Id',rid);n.set('Type',relation.get('Type'));n.set('Target','media/'+name)
    mapping[old_id]=rid;target_by_hash[digest]=rid
docpr=max([int(n.get('id','0')) for n in base.xpath('//wp:docPr',namespaces=NS)]+[0])+1
for b in new:
    for n in b.iter():
        for key,value in list(n.attrib.items()):
            if key.startswith('{'+NS['r']+'}'): n.set(key,mapping[value])
    for n in b.xpath('.//wp:docPr',namespaces=NS): n.set('id',str(docpr));docpr+=1

# Replacing the blocks is the only body mutation.
before_outside=deepcopy(base)
old_start=next(p for p in before_outside.xpath('//w:p',namespaces=NS) if text(p).startswith('3.3.3.'))
oc=old_start.getparent();oe=next(c for c in oc if text(c).startswith('3.4.'))
for n in list(oc)[oc.index(old_start):oc.index(oe)]: oc.remove(n)
for n in removed: cell.remove(n)
for i,n in enumerate(new): cell.insert(begin+i,n)
after_outside=deepcopy(base)
ns=next(p for p in after_outside.xpath('//w:p',namespaces=NS) if text(p).startswith('3.3.3'))
nc=ns.getparent();ne=next(c for c in nc if text(c).startswith('3.4.'))
for n in list(nc)[nc.index(ns):nc.index(ne)]: nc.remove(n)
assert canon(before_outside)==canon(after_outside),'Content outside authorized range changed'

new_math=[n for b in new for n in b.xpath('.//m:oMathPara/m:oMath',namespaces=NS)]
assert len(new_math)==6
assert all(not text(n).endswith(('，',',','。','；')) for n in new_math)
assert not any(ch in text(b) for b in new for ch in ('\u3000','\u00a0','□','⬚','\u2003'))
assert not any(' ' in t for b in new for t in b.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))
assert not any(b.xpath('.//m:e[not(*)]|.//m:num[not(*)]|.//m:den[not(*)]',namespaces=NS) for b in new)
for b in new:
    for run in b.xpath('.//w:r[w:t]|.//m:r[m:t]',namespaces=NS):
        if any(ch in punctuation for ch in text(run)):
            fonts=run.find(q('w','rPr')).find(q('w','rFonts'))
            assert all(fonts.get(q('w',key))=='宋体' for key in ('ascii','hAnsi','eastAsia','cs'))
numbering=[text(b) for b in new if b.tag==q('w','tbl')]
assert all(numbering[i].endswith('（3-'+str(i+1)+'）') for i in range(6))
changes={'word/document.xml':E.tostring(base,xml_declaration=True,encoding='UTF-8',standalone=True),
         'word/_rels/document.xml.rels':E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)}
with ZipFile(OUT,'w') as z:
    for info in infos: z.writestr(info,changes.get(info.filename,original[info.filename]))
    for name,data in additions.items(): z.writestr(name,data,compress_type=ZIP_DEFLATED)
with ZipFile(OUT) as z:
    unchanged=[name for name,value in original.items() if name not in changes and z.read(name)==value]
    assert len(unchanged)==len(original)-len(changes)
assert sha256(BASE.read_bytes()).hexdigest()==base_hash
receipt={'base':str(BASE),'base_sha256':base_hash,'backup':str(BACKUP),'candidate':str(OUT),
 'section_range':'3.3.3 through 3.3.4; 3.4 and all other content preserved',
 'removed_blocks':len(removed),'inserted_blocks':len(new),'display_equations':6,
 'trailing_equation_commas':0,'literal_spaces_in_replaced_text':0,'empty_math_arguments':0,
 'punctuation_font':'宋体; Chinese prose punctuation','punctuation_runs':punct_runs,
 'removed_spaces':space_removed,'new_media_parts':list(additions),
 'outside_range_canonical_xml_identical':True,'unchanged_original_package_parts':len(unchanged),
 'styles_and_settings_unchanged':True,'render_review':'pending','installed':False}
(QA/'merge_checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
