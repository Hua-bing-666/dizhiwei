"""P6 可视化整改 · 台架图重绘（摒弃旧烘焙 3D，改正确水路口径 2D 学术示意）。

口径唯一真源：docs/硬件软件匹配度审查_v2.2.md（水路安装顺序不可调换）：
  Q(流量计) → P0(取压嘴A) → 区段R(φ5.0 孔板+针阀) → P1(取压嘴B)
    → 三通分流 → A 正常等效负载 / 泄漏球阀 → 独立收集杯
    B 健康负载切换为并联对照支路（P1 之后引出）
  LoRa 节点(8) 采集 P0/P1/Q 三路。

绘制：1000 px 画布字符串直构 SVG，Edge 无头截图 → PNG（×2 + 裁白边）。
生成期自检：tw() 防文字撑破盒子（box 内拦）；徽标不压元件、不互压。
用法：python scripts/draw_bench_p6.py [bench|collection|all]
"""
import subprocess, sys, time, uuid
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables'
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'

INK = '#142a30'
GRAY = '#52636a'
FILL = '#eef5f2'
FILL2 = '#eaf1f7'
WHITE = '#ffffff'
ACC = '#b8543f'

def tw(s, fs):
    return sum(fs if ord(c) > 0x2000 and c != '·' else fs * 0.56 for c in s)

def render_png(name, w, h):
    svg = (OUT / (name + '.svg')).read_text(encoding='utf-8')
    html = ('<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;background:white}svg{display:block}</style>' + svg)
    tmp = ROOT / 'tmp' / 'p6_render'
    tmp.mkdir(parents=True, exist_ok=True)
    hp = tmp / (name + '.html'); hp.write_text(html, encoding='utf-8')
    png = tmp / (name + '.png'); png.unlink(missing_ok=True)
    prof = tmp / ('p-' + uuid.uuid4().hex[:8])
    kw = {'creationflags': subprocess.CREATE_NO_WINDOW} if hasattr(subprocess, 'CREATE_NO_WINDOW') else {}
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                    '--force-device-scale-factor=2', f'--window-size={w},{h}',
                    f'--user-data-dir={prof}', f'--screenshot={png}', hp.as_uri()],
                   capture_output=True, timeout=120, **kw)
    deadline = time.monotonic() + 40
    while not png.exists() or png.stat().st_size < 2000:
        if time.monotonic() > deadline:
            raise RuntimeError(f'{name}: png 未生成')
        time.sleep(0.25)
    dest = OUT / (name + '.png')
    try:
        from PIL import Image
        import numpy as np
        im = Image.open(png).convert('RGB')
        a = np.array(im.convert('L'))
        rows = np.where((a < 250).any(axis=1))[0]
        cols = np.where((a < 250).any(axis=0))[0]
        pad = 14
        im = im.crop((max(0, cols[0]-pad), max(0, rows[0]-pad),
                      min(im.width, cols[-1]+pad), min(im.height, rows[-1]+pad)))
        im.save(dest)
    except ImportError:
        dest.write_bytes(png.read_bytes())

class Fig:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.items = []; self.minsize = 99
    def text(self, x, y, s, size=24, bold=False, anchor='middle', color=INK):
        self.minsize = min(self.minsize, size)
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-family="Microsoft YaHei, SimSun, sans-serif" font-weight="{700 if bold else 400}" '
            f'text-anchor="{anchor}" fill="{color}">{escape(s)}</text>')
    def box(self, x, y, w, h, lines, fill=WHITE, dash=False, fs=23, lead=30, stroke=INK, padx=8):
        for ln in lines:
            if tw(ln, fs) > w - 2*padx:
                raise SystemExit(f'[{self.name}] 盒内文字撑破：{ln!r} 估宽 {tw(ln,fs):.0f} > {w-2*padx:.0f} (盒宽 {w})')
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"'
            + (' stroke-dasharray="7 5"' if dash else '') + '/>')
        n = len(lines); start = y + h/2 - (n-1)*lead/2 + fs*0.35
        if start + (n-1)*lead > y + h - 6:
            raise SystemExit(f'[{self.name}] 行溢出盒底：{lines!r}')
        for i, ln in enumerate(lines):
            self.text(x+w/2, start+i*lead, ln, fs, i == 0)
    def line(self, pts, arrow=False, dash=False, w=2.0, color=INK):
        self.items.append('<path d="M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in pts)
            + f'" fill="none" stroke="{color}" stroke-width="{w}"'
            + (' stroke-dasharray="7 5"' if dash else '')
            + (' marker-end="url(#ar)"' if arrow else '') + '/>')
    def badge(self, x, y, n, r=16, color=INK):
        self.items.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{WHITE}" stroke="{color}" stroke-width="2"/>')
        self.text(x, y+7, str(n), 23, True, 'middle', color)
    def fit_text(self, x, y, s, fs=23, anchor='start', color=INK, limit=None):
        if limit is None:
            limit = (self.w - 2*12) if anchor == 'start' else 2*x
        if tw(s, fs) > limit:
            raise SystemExit(f'[{self.name}] 单行超宽：{s!r} 估宽 {tw(s,fs):.0f} > {limit:.0f}')
        self.text(x, y, s, fs, False, anchor, color)
    def save(self):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
               '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
               f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker></defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="white"/>'
               '<g font-family="Microsoft YaHei, SimSun, sans-serif">' + ''.join(self.items) + '</g></svg>\n')
        (OUT / (self.name + '.svg')).write_text(svg, encoding='utf-8', newline='\n')
        render_png(self.name, self.w, self.h)
        print(f'written: {self.name} ({self.w}x{self.h}, min {self.minsize}px, '
              f'@1000→{round(self.minsize*420/self.w,2)}pt)')

# ───────────────── bench_isometric：双支路台架总览（正确水路口径） ─────────────────
def bench():
    f = Fig('bench_isometric', 1000, 700)
    f.text(28, 42, '可控实验台架（双支路清水）· 水路口径 Q 最上游', 28, True, 'start')
    f.text(28, 78, '候选结构；尚未制造 · 流量 Q 最先量取，再取 P0 / P1 压差', 23, False, 'start', GRAY)
    y0 = 300
    BW, BH = 140, 100
    f.line([(80, y0), (900, y0)], w=7, color=GRAY)
    cx = {'Q':150, 'P0':320, 'R':490, 'P1':660}
    f.box(cx['Q']-BW/2, y0-BH/2, BW, BH, ['① Q', '流量计'], FILL2)
    f.box(cx['P0']-BW/2, y0-BH/2, BW, BH, ['② P0', '取压嘴A'], FILL)
    f.box(cx['R']-BW/2, y0-BH/2, BW, BH, ['③ R', '等效受限'], FILL)
    f.box(cx['P1']-BW/2, y0-BH/2, BW, BH, ['④ P1', '取压嘴B'], FILL)
    f.line([(740, y0), (740, 470)], w=7, color=GRAY)
    f.line([(890, y0), (890, 470)], w=7, color=GRAY)
    f.box(670, 470, 140, 95, ['⑤ A', '正常负载'], FILL)
    f.box(820, 470, 140, 95, ['⑦ 泄漏', '独立收集'], WHITE, stroke=ACC)
    f.line([(660, y0-BH/2), (660, 168)], w=7, color=GRAY)
    f.line([(660, 168), (545, 168)], w=7, color=GRAY)
    f.box(370, 128, 175, 80, ['⑥ B', '健康负载切换'], FILL2, fs=23)
    f.line([(900, y0), (900, 205)], w=7, color=GRAY)
    f.box(855, 105, 125, 100, ['⑧', '采集', 'LoRa'], FILL, lead=30)
    taps_b = [(cx['Q'], 'Q'), (cx['P0'], 'P0'), (cx['P1'], 'P1')]
    ybus = y0 + BH/2 + 52
    for (tx, lab) in taps_b:
        f.line([(tx, y0+BH/2), (tx, ybus)], w=1.4, color=INK, dash=True)
        f.text(tx, y0+BH/2+30, lab, 23, False, 'middle', GRAY)
    f.line([(taps_b[0][0], ybus), (850, ybus)], w=1.4, color=INK, dash=True)
    f.line([(850, ybus), (850, 205)], w=1.4, color=INK, dash=True)
    f.line([(850, 205), (855, 205)], w=1.4, color=INK, dash=True)
    f.text(28, 596, '图注：Q → P0 → ③R → P1 → ⑤A 正常负载 / ⑦泄漏独立收集（水路 Q 最上游）。', 23, False, 'start', GRAY)
    f.text(28, 634, '⑥B 为并联健康负载对照，不参与故障注入；⑧节点采集 Q/P0/P1 并经 LoRa 上报。', 23, False, 'start', GRAY)
    f.save()

# ───────────────── collection_overview：测量/注入/独立计量（正确水路口径） ─────────────────
def collection():
    f = Fig('collection_overview_p6', 1000, 930)
    f.text(28, 42, '清水台架：测量、注入与独立计量', 28, True, 'start')
    f.text(28, 78, '候选结构；尚未制造 · 水路口径 Q 最上游（与图3-9、网络拓扑一致）', 23, False, 'start', GRAY)
    y0 = 350
    BW, BH = 130, 100
    f.line([(70, y0), (900, y0)], w=7, color=GRAY)
    cx = {'Q':150, 'P0':315, 'R':480, 'P1':645}
    f.box(cx['Q']-BW/2, y0-BH/2, BW, BH, ['① Q', '流量计'], FILL2)
    f.box(cx['P0']-BW/2, y0-BH/2, BW, BH, ['② P0', '取压嘴A'], FILL)
    f.box(cx['R']-BW/2, y0-BH/2, BW, BH, ['③ R', '等效受限'], FILL)
    f.box(cx['P1']-BW/2, y0-BH/2, BW, BH, ['④ P1', '取压嘴B'], FILL)
    f.line([(740, y0), (740, 540)], w=7, color=GRAY)
    f.line([(890, y0), (890, 540)], w=7, color=GRAY)
    f.box(670, 540, 140, 100, ['⑤ A', '正常负载'], FILL)
    f.box(820, 540, 140, 100, ['⑦ 泄漏', '独立收集'], WHITE, stroke=ACC)
    f.line([(645, y0-BH/2), (645, 190)], w=7, color=GRAY)
    f.line([(645, 190), (545, 190)], w=7, color=GRAY)
    f.box(370, 150, 175, 80, ['⑥ B', '健康负载切换'], FILL2, fs=23)
    f.box(690, 100, 175, 76, ['注入/标定', '工况源'], FILL2, fs=23)
    f.line([(865, 176), (872, 215)], w=2, color=INK, dash=True)
    f.line([(900, y0), (900, 330)], w=7, color=GRAY)
    f.box(865, 215, 120, 115, ['⑧', '采集', 'LoRa'], FILL, lead=32)
    taps_c = [(cx['Q'], 'Q'), (cx['P0'], 'P0'), (cx['P1'], 'P1')]
    ybus = y0 + BH/2 + 52
    for (tx, lab) in taps_c:
        f.line([(tx, y0+BH/2), (tx, ybus)], w=1.4, color=INK, dash=True)
        f.text(tx, y0+BH/2+30, lab, 23, False, 'middle', GRAY)
    f.line([(taps_c[0][0], ybus), (860, ybus)], w=1.4, color=INK, dash=True)
    f.line([(860, ybus), (860, 330)], w=1.4, color=INK, dash=True)
    f.line([(860, 330), (865, 330)], w=1.4, color=INK, dash=True)
    f.text(28, 730, 'A 支路：Q(流量计) → P0 → R → P1 → 正常负载与泄漏分流。', 23, True, 'start')
    f.text(28, 772, 'Q 包含正常与泄漏流量；B 只提供正常负载变化对照（并联，不参与故障注入）。', 23, False, 'start', GRAY)
    f.text(28, 814, '⑧ 节点采集 Q / P0 / P1 三路，经 LoRa 上报；⑦ 泄漏支路设独立收集杯，用于比对注入量。', 23, False, 'start', GRAY)
    f.text(28, 856, '编号：1=Q  2=P0  3=R  4=P1  5=A  6=B  7=泄漏收集  8=采集/LoRa。', 23, False, 'start', GRAY)
    f.save()

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('bench', 'all'):
        bench()
    if which in ('collection', 'all'):
        collection()
