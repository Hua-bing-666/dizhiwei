# -*- coding: utf-8 -*-
"""膜下滴灌管网三层结构示意图（分干管 → 支管 → 毛管），标注本项目监测对象与测点位置。
手写 SVG + Edge 无头渲染；出图三查（版式/配色/目视）由 verify_figure_layout.mjs 与人工目视完成。"""
from pathlib import Path
import subprocess, time, uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures'
TMP = ROOT / 'tmp/network_topology'
TMP.mkdir(parents=True, exist_ok=True)
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

BLUE = '#2c4a63'   # 分干管（深蓝灰，相对亮度 0.063）
GREEN = '#4e7d57'  # 支管——监测对象（绿，相对亮度 0.170）
BROWN = '#ad8046'  # 毛管/滴头（棕，相对亮度 0.248）
# 三色亮度两两差 0.107 / 0.184 / 0.078，均 ≥0.05，黑白打印可区分。
# 放置宽度 420pt 口径：最小字号 23px ⇒ 9.66pt ≥ 9.5pt；标题 24px ⇒ 10.08pt。
# 棕字 #ad8046 于白底对比度 3.53 ≥ 3.0（大字阈值）；绿字于 #eef4ee 底 4.32 ≥ 3.0。

parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560"><defs>'
         '<marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L7 4 L0 8 Z" fill="black"/></marker>'
         '</defs><rect width="1000" height="560" fill="white"/><g font-family="Microsoft YaHei, SimSun, sans-serif" fill="black">']

def line(pts, color='black', w=2.5, arrow=False, dash=''):
    d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
    parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}"{dash}'+(' marker-end="url(#ar)"' if arrow else '')+'/>')

def box(x, y, w, h, fill, stroke):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')

def text(x, y, s, size=24, bold=False, anchor='middle', color='black'):
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{s}</text>')

# ── 首部水源 ──
box(10, 60, 190, 90, '#f4f7f9', BLUE)
text(105, 98, '水源与首部', 24, True)
text(105, 130, '水泵·过滤·施肥', 23)

# ── 分干管（蓝色主干）──
line([(200, 105), (940, 105)], BLUE, 4)
text(570, 88, '分干管（全田共用）', 24, True, color=BLUE)

# ── 三个轮灌阀组，各自引出一条支管 ──
# 支管框心 210 / 500 / 790，框宽 200 / 330 / 200（支管2 标签 12 余字 @23px 需宽框），
# 框间空隙 25px 等距，左右外距 110px 对称。
for i, vx in enumerate([210, 500, 790]):
    box(vx-16, 98, 32, 14, 'white', BLUE)
for i, (vx, bw2, label) in enumerate([(210, 200, '支管1·轮灌组A'), (500, 330, '支管2·轮灌组B（监测对象）'), (790, 200, '支管3·轮灌组C')]):
    line([(vx, 112), (vx, 205)], GREEN, 4)
    box(vx-bw2/2, 205, bw2, 46, '#eef4ee', GREEN)
    text(vx, 234, label, 23, i == 1, color='#1f3a24' if i == 1 else GREEN)

# ── 监测支管放大：测点布置 ──
mx = 500
line([(mx, 251), (mx, 320)], GREEN, 4)
# 支管放大框
box(180, 320, 640, 150, 'white', GREEN)
text(500, 350, '支管放大（监测布置）', 23, True, color='#1f3a24')
# 管内流程
line([(230, 415), (770, 415)], GREEN, 3.5, arrow=True)
text(258, 395, 'Q 流量计', 23, True)
text(390, 395, '取压嘴A', 23, True)
text(505, 395, '区段R', 23, True)
text(622, 395, '取压嘴B', 23, True)
text(742, 395, '泄漏阀', 23, True)
# 元件
box(233, 402, 52, 26, '#f7f7f7', 'black')
box(366, 402, 50, 26, '#f7f7f7', 'black')
box(480, 398, 52, 34, '#fbf1db', BROWN)
box(598, 402, 50, 26, '#f7f7f7', 'black')
box(716, 402, 54, 26, '#faede2', BROWN)

# ── 毛管层 ──
line([(180, 470), (820, 470)], BROWN, 3)
for i in range(6):
    y = 470
    x = 230 + i*118
    line([(x, y), (x, y+55)], BROWN, 2, arrow=True)
text(500, 545, '毛管与滴头（覆膜下铺设）', 23, color=BROWN)

parts.append('</g></svg>')
svg = ''.join(parts)
(OUT/'network_topology.svg').write_text(svg, encoding='utf-8', newline='\n')

html = TMP/'network_topology.html'
html.write_text('<html><meta charset="utf-8"><style>html,body{margin:0;width:1000px}svg{display:block}</style>'+svg+'</html>', encoding='utf-8')
dest = OUT/'network_topology.png'
dest.unlink(missing_ok=True)
profile = TMP/('edge-'+uuid.uuid4().hex[:12])
subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                '--force-device-scale-factor=2', '--window-size=1000,560', '--screenshot='+str(dest.resolve()), html.resolve().as_uri()],
               capture_output=True, check=True, timeout=35, creationflags=subprocess.CREATE_NO_WINDOW)
deadline = time.monotonic()+25
while not dest.exists() or dest.stat().st_size < 1000:
    if time.monotonic() > deadline: raise RuntimeError('png not produced')
    time.sleep(.2)
print('network_topology rendered,', dest.stat().st_size, 'bytes')
