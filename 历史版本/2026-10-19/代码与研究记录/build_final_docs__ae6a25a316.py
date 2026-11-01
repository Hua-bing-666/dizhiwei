# -*- coding: utf-8 -*-
"""生成三份最终文档（技术路线 / 项目实施方案 / 申报书）。

输入：docs/ 下三份 markdown（已含 v2.2 口径与图标记）
输出：deliverables/ 下三份 .docx
特性：
  - 封面 + 章节标题（按“一、/ 1.1 / ###”模式归一层级）+ 表格 + 内联插图 + 图注
  - 中文排版：正文宋体、标题黑体、首行缩进 2 字符、1.5 倍行距、页脚页码
  - 图宽自适应（横图 15cm，竖图按高≤19cm 反算），不存在则跳过并告警
"""
import os, re, sys
import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables")
BODY_FONT = "宋体"
HEAD_FONT = "黑体"
BODY_PT = 12.0      # 小四
TABLE_PT = 9.5
INK = RGBColor(0x1a, 0x1a, 0x1a)
GRAY = RGBColor(0x59, 0x59, 0x59)

PROJECT = "基于 LoRa 的南疆滴灌支管道早期故障诊断物联网原型系统"


def set_cn_font(run, name, size=None, bold=None, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.append(rf)
    rf.set(qn('w:eastAsia'), name)
    rf.set(qn('w:ascii'), name)
    rf.set(qn('w:hAnsi'), name)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if color is not None: run.font.color.rgb = color


def add_page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("— ")
    set_cn_font(r, BODY_FONT, 9, color=GRAY)
    # PAGE field
    fld1 = OxmlElement('w:fldSimple'); fld1.set(qn('w:instr'), 'PAGE')
    run = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = '1'; run.append(t); fld1.append(run)
    p._p.append(fld1)
    r2 = p.add_run(" —")
    set_cn_font(r2, BODY_FONT, 9, color=GRAY)


def setup_page(doc):
    s = doc.sections[0]
    s.page_width = Cm(21.0); s.page_height = Cm(29.7)
    s.top_margin = Cm(2.5); s.bottom_margin = Cm(2.5)
    s.left_margin = Cm(3.0); s.right_margin = Cm(2.5)  # 左侧装订留宽
    st = doc.styles['Normal']
    st.font.name = BODY_FONT
    st.font.size = Pt(BODY_PT)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), BODY_FONT)
    add_page_number_footer(s)


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(12 if level == 1 else 8)
    pf.space_after = Pt(6)
    pf.keep_with_next = True
    sizes = {1: 16, 2: 14, 3: 12.5}
    r = p.add_run(text)
    set_cn_font(r, HEAD_FONT, sizes.get(level, 12), bold=True, color=INK)
    # 大纲级别（便于生成目录/导航）
    pPr = p._p.get_or_add_pPr()
    ol = OxmlElement('w:outlineLvl'); ol.set(qn('w:val'), str(level - 1)); pPr.append(ol)
    return p


def add_para(doc, text, indent=True, size=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(4)
    if indent:
        pf.first_line_indent = Pt((size or BODY_PT) * 2)
    _write_inline(p, text, size or BODY_PT)
    return p


def _write_inline(p, text, size):
    # 处理 **bold**、`code`、*italic*
    tokens = re.split(r'(\*\*.+?\*\*|`[^`]+`)', text)
    for tk in tokens:
        if not tk:
            continue
        if tk.startswith('**') and tk.endswith('**') and len(tk) > 4:
            r = p.add_run(tk[2:-2]); set_cn_font(r, BODY_FONT, size, bold=True, color=INK)
        elif tk.startswith('`') and tk.endswith('`'):
            r = p.add_run(tk[1:-1]); set_cn_font(r, "Consolas", size - 0.5, color=RGBColor(0x33, 0x33, 0x33))
        else:
            r = p.add_run(tk); set_cn_font(r, BODY_FONT, size, color=INK)


def add_blockquote(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(0.6); pf.line_spacing = 1.35; pf.space_after = Pt(4)
    _write_inline(p, text, BODY_PT - 1)
    for r in p.runs:
        r.font.color.rgb = GRAY
    # 左竖线
    pPr = p._p.get_or_add_pPr()
    bdr = OxmlElement('w:pBdr'); left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single'); left.set(qn('w:sz'), '18')
    left.set(qn('w:space'), '8'); left.set(qn('w:color'), 'AAAAAA')
    bdr.append(left); pPr.append(bdr)


def add_code(doc, code_lines):
    for ln in code_lines:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.line_spacing = 1.1; pf.space_after = Pt(0); pf.left_indent = Cm(0.5)
        r = p.add_run(ln if ln else " ")
        set_cn_font(r, "Consolas", 8.5, color=RGBColor(0x33, 0x33, 0x33))


def add_list(doc, text, ordered=False):
    p = doc.add_paragraph(style='List Number' if ordered else 'List Bullet')
    pf = p.paragraph_format; pf.line_spacing = 1.4; pf.space_after = Pt(2)
    _write_inline(p, text, BODY_PT)
    return p


def _img_width_cm(path):
    try:
        w, h = Image.open(path).size
    except Exception:
        return 14.0
    aspect = w / h
    if aspect >= 1:
        width = 15.0
    else:
        # 竖图：先按宽 11cm，若高>19cm 则按高反算
        width = min(11.0, 19.0 * aspect)
    # 极高图兜底
    if width / aspect > 19.0:
        width = 19.0 * aspect
    return max(6.0, width)


def add_figure(doc, path, caption):
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    if not os.path.exists(full):
        print("  [WARN] 图缺失，跳过:", path)
        return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(full, width=Cm(_img_width_cm(full)))
    # 图注
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(8)
    r = cp.add_run(caption); set_cn_font(r, BODY_FONT, 9.5, color=GRAY)


def _shade(cell, hexfill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hexfill)
    tcPr.append(shd)


def add_table(doc, rows):
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    # 表格宽度 = 版心 100%，防止横向溢出
    tblPr = t._tbl.tblPr
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None:
        tblW = OxmlElement('w:tblW'); tblPr.append(tblW)
    tblW.set(qn('w:w'), '5000'); tblW.set(qn('w:type'), 'pct')
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ''
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(0)
            _write_inline(p, val, TABLE_PT)
            if i == 0:
                _shade(cell, 'E9EDF2')
                for r in p.runs:
                    r.font.bold = True
    # 表格后留白
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_cover(doc, big_title, subtitle, meta_lines=None):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(PROJECT); set_cn_font(r, HEAD_FONT, 15, bold=True, color=INK)
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(big_title); set_cn_font(r, HEAD_FONT, 30, bold=True, color=INK)
    if subtitle:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(subtitle); set_cn_font(r, HEAD_FONT, 16, bold=False, color=GRAY)
    for _ in range(6):
        doc.add_paragraph()
    if meta_lines:
        for line in meta_lines:
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(line); set_cn_font(r, BODY_FONT, 12, color=INK)
    for _ in range(4):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("2026 年 10 月"); set_cn_font(r, BODY_FONT, 12, color=GRAY)
    doc.add_page_break()


FIG_RE = re.compile(r"\[图:\s*([^|\]]+?)\s*\|\s*([^\]]+?)\]")


def build(md_path, out_name, big_title, subtitle, meta_lines, insert_figs=None, renumber_figs=False):
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    doc = Document()
    setup_page(doc)
    add_cover(doc, big_title, subtitle, meta_lines)

    i, n = 0, len(lines)
    title_skipped = False
    insert_figs = insert_figs or {}
    figno = [0]

    def cap_fix(c):
        if renumber_figs:
            figno[0] += 1
            return re.sub(r"^图\s*\d+", "图 %d" % figno[0], c)
        return c
    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        s = line.strip()
        # 还原 markdown 转义（h\*=26 -> h*=26）
        s = s.replace('\\*', '*').replace('\\_', '_')
        if not s:
            i += 1; continue
        # 首个 H1 作为标题，跳过（已在封面）
        if s.startswith("# ") and not title_skipped:
            title_skipped = True; i += 1; continue
        # 内部元信息 blockquote 跳过
        if s.startswith(">"):
            txt = s.lstrip(">").strip()
            plain = re.sub(r"^\*+|\*+$", "", txt).strip()
            if re.match(r"^(生成日期|本稿|数值口径|本稿范围|项目名称：)", plain):
                i += 1; continue
            # 聚合连续 >
            buf = [txt]
            i += 1
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            add_blockquote(doc, " ".join(buf)); continue
        # 表格
        if s.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:\-\|]+\|?\s*$", lines[i + 1].strip()):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip().replace('\\*', '*').replace('\\_', '_') for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s:\-]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            add_table(doc, rows); continue
        # 分隔线
        if re.match(r"^-{3,}$", s):
            i += 1; continue
        # 内部注记（不应进入正式稿）
        if re.match(r"^\*{0,2}(口径核对|本稿|生成日期)", s) or "现行文档零冲突" in s:
            i += 1; continue
        # 代码围栏
        if s.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i].rstrip()); i += 1
            i += 1  # 跳过收尾围栏
            add_code(doc, code); continue
        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            hashes, text = m.group(1), m.group(2).strip()
            if re.match(r"^[〇一二三四五六七八九十]+、", text):
                lvl = 1
            elif re.match(r"^\d+\.\d+\.\d+", text):
                lvl = 3
            elif re.match(r"^\d+\.\d+", text):
                lvl = 2
            elif len(hashes) >= 3:
                lvl = 3
            else:
                lvl = min(len(hashes), 3)
            add_heading(doc, text, lvl)
            i += 1
            # 章节插图
            for key, figs in insert_figs.items():
                if key in text:
                    for fp, cap in figs:
                        add_figure(doc, fp, cap_fix(cap))
                    break
            continue
        # 图标记（可多个）
        if "[图:" in s:
            found = FIG_RE.findall(s)
            if found:
                for fp, cap in found:
                    add_figure(doc, fp.strip(), cap_fix(cap.strip()))
                i += 1; continue
        # 列表
        m = re.match(r"^([-*])\s+(.*)$", s)
        if m:
            add_list(doc, m.group(2), ordered=False); i += 1; continue
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Cm(0.9); pf.line_spacing = 1.45; pf.space_after = Pt(2)
            _write_inline(p, f"{m.group(1)}. {m.group(2)}", BODY_PT)
            i += 1; continue
        # 普通段落
        add_para(doc, s)
        i += 1

    out = os.path.join(OUT, out_name)
    doc.save(out)
    print("  ✓", out_name, os.path.getsize(out), "B")
    return out


DOC1_FIGS = {
    "〇、路线总览": [("application/figures/route_risk_chain.png", "图 A 五阶段风险收敛链（每阶段：风险 R + 两条对策 + 门控色条）")],
    "七、关键技术决策": [("application/figures/route_decision_fork.png", "图 B 八项决策的分叉与翻案条件")],
    "八、进度与里程碑": [("application/figures/route_gantt.png", "图 C 阶段推进与门控验收时点（甘特）")],
}


def main():
    os.makedirs(OUT, exist_ok=True)
    print("生成最终文档：")
    build("docs/技术路线_分块版_申报书用.md", "技术路线_最终版_20261019.docx",
          "技术路线", "六环节递进 · 门控 G1—G5",
          [f"项目名称：{PROJECT}", "执行期：2027 年 3 月 — 2028 年 2 月"],
          insert_figs=DOC1_FIGS)
    build("docs/项目实施方案_分块版_申报书用.md", "项目实施方案_最终版_20261019.docx",
          "项目实施方案", "研究现状 · 系统设计 · 感知层 · 台架 · 判据",
          [f"项目名称：{PROJECT}", "执行期：2027 年 3 月 — 2028 年 2 月"])
    build("docs/新申报书_重写稿_20261017.md", "大创申报书_最终稿_20261019.docx",
          "大学生创新创业训练计划项目申报书", "（创新训练项目）",
          [f"项目名称：{PROJECT}", "项目负责人：________", "所属学院：塔里木大学 信息工程学院",
           "指导教师：________", "起止时间：2027 年 3 月 — 2028 年 2 月"],
          renumber_figs=True)


if __name__ == "__main__":
    main()
