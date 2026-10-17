# -*- coding: utf-8 -*-
"""从 docs/新申报书_重写稿_20261017.md 生成独立 docx（从头新建，不改动正式稿6）。
md 约定：# / ## 标题；普通段落；[图: 路径 | 图注]；markdown 表格；> 引用段。"""
import re
import sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import parse_xml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'docs/新申报书_重写稿_20261017.md')
OUT = ROOT / (sys.argv[2] if len(sys.argv) > 2 else 'deliverables/大创申报书_重写稿_20261017.docx')

doc = Document()
# 页面 A4 与边距
for sec in doc.sections:
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.6)
    sec.top_margin = sec.bottom_margin = Cm(2.8)

# ── 页眉与页脚页码 ──
hdr = doc.sections[0].header
hp = hdr.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
hr = hp.add_run('塔里木大学大学生创新创业训练计划项目 · 技术路线与项目实施')
hr.font.size = Pt(9); hr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
hr.font.name = 'Times New Roman'; hr.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
ftr = doc.sections[0].footer
fp = ftr.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fld = fp.add_run()
fld.element.append(parse_xml(
    '<w:fldSimple xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:instr=" PAGE "/>'))

# ── 封面页 ──
def cover_line(text, size, bold=False, before=0, after=6):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.bold = bold
    r.font.name = 'Times New Roman'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    return p

if '申报书' in str(SRC):
    cover_line('大学生创新创业训练计划项目', 22, True, before=90, after=10)
else:
    cover_line(SRC.stem.replace('_',' '), 22, True, before=90, after=10)
cover_line('申  报  书', 26, True, after=60)
for label, value in [
    ('文档名称：' + SRC.stem.replace('_',' '), ''),
    ('　　　　　物联网原型系统', ''),
    ('项 目 类 别：创新训练项目', ''),
    ('项 目 负 责 人：＿＿＿＿＿＿＿＿＿＿', ''),
    ('指导教　　师：＿＿＿＿＿＿＿＿＿＿', ''),
    ('所 在 学 院：＿＿＿＿＿＿＿＿＿＿', ''),
    ('专　　　　业：通信工程', ''),
    ('申 报 单 位：塔里木大学', ''),
    ('编制日期：2026 年 10 月', ''),
]:
    cover_line(label, 14, after=14)
doc.add_page_break()

def set_font(style, name_cn, size, bold=False, color=None):
    style.font.name = 'Times New Roman'
    style.font.size = Pt(size)
    style.font.bold = bold
    if color: style.font.color.rgb = color
    style.element.rPr.rFonts.set(qn('w:eastAsia'), name_cn)

normal = doc.styles['Normal']
set_font(normal, '宋体', 12)
normal.paragraph_format.line_spacing = 1.4
normal.paragraph_format.space_after = Pt(4)

for lvl, (cn, size) in {1: ('黑体', 16), 2: ('黑体', 14), 3: ('黑体', 12.5)}.items():
    st = doc.styles[f'Heading {lvl}']
    set_font(st, cn, size, bold=True, color=RGBColor(0, 0, 0))
    st.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
    st.paragraph_format.space_after = Pt(6)

def add_para(text, size=12, italic=False, gray=False, align=None, cn='宋体'):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.italic = italic
    r.font.name = 'Times New Roman'
    r.element.rPr.rFonts.set(qn('w:eastAsia'), cn)
    if gray: r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    if align: p.alignment = align
    return p

def add_image(path, caption):
    fp = ROOT / path
    if not fp.exists():
        add_para(f'［缺图：{path}］', gray=True); return
    im = Image.open(fp); w, h = im.size
    # 优先按版心宽 15.4cm 放置（保证图内字号印刷可读），
    # 仅当高度超出 19cm（版心 24.1cm，余量留给图注）时才按高度收缩。
    ratio = w / h
    width = Cm(15.4)
    height = width / ratio
    if height > Cm(19.0):
        height = Cm(19.0)
        width = height * ratio
    doc.add_picture(str(fp), width=int(width), height=int(height))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_before = Pt(6)
    cap = add_para(caption, size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, gray=True, cn='黑体')
    cap.paragraph_format.space_after = Pt(12)

def add_table(rows):
    header = [c.strip() for c in rows[0].strip('|').split('|')]
    body = [[c.strip() for c in r.strip('|').split('|')] for r in rows[2:]]
    t = doc.add_table(rows=1 + len(body), cols=len(header))
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        cell = t.rows[0].cells[j]
        cell.text = ''
        r = cell.paragraphs[0].add_run(h)
        r.font.bold = True; r.font.size = Pt(10.5)
        r.font.name = 'Times New Roman'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    for i, row in enumerate(body):
        for j, v in enumerate(row):
            if j >= len(header): continue
            cell = t.rows[i+1].cells[j]
            cell.text = ''
            r = cell.paragraphs[0].add_run(re.sub(r'\*\*(.+?)\*\*', r'\1', v))
            r.font.size = Pt(10.5)
            r.font.name = 'Times New Roman'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

lines = SRC.read_text(encoding='utf-8').splitlines()
i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith('[图:'):
        m = re.match(r'\[图:\s*(.+?)\s*\|\s*(.+?)\]', line)
        if m: add_image(m.group(1), m.group(2))
        i += 1; continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].startswith('|'):
            rows.append(lines[i]); i += 1
        if len(rows) >= 2: add_table(rows)
        continue
    if line.startswith('# '):
        doc.add_heading(line[2:].strip(), level=1)
    elif line.startswith('## '):
        doc.add_heading(line[3:].strip(), level=2)
    elif line.startswith('### '):
        doc.add_heading(line[4:].strip(), level=3)
    elif line.startswith('> '):
        add_para(line[2:].strip(), size=10.5, gray=True, italic=True)
    elif line.strip() in ('---', ''):
        pass
    elif line.startswith('*') and line.endswith('*') and not line.startswith('**'):
        add_para(line.strip('*'), size=10, gray=True)
    else:
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', line).replace('\\*', '*')
        add_para(text)
    i += 1

OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print('saved', OUT, OUT.stat().st_size, 'bytes')
