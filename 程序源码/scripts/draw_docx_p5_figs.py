"""P5 申报书内嵌图整改：重建 图3-2（GD32F103CBT6 最小系统）与 图3-8（双支路台架三维布局）。

口径唯一真源：docs/硬件软件匹配度审查_v2.2.md + docs/数值口径统一清单.md（N11/N12/N07）。
画法沿用项目既有约定：1000 px 画布字符串直构 SVG，Edge 无头截图 → PNG（×2 + 裁白边）。
生成期自带两道自检：① 文字估宽不得超过父容器内宽（防「撑破盒子」）；
                    ② 编号徽标不得压元件顶面、不得互相重叠（防「徽标打架」）。
用法：python scripts/draw_docx_p5_figs.py [gd32|bench|all]
"""
from pathlib import Path
from html import escape
import hashlib, json, subprocess, sys, time, uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables'
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'

INK = '#142a30'
GRAY = '#52636a'
FILL = '#eef5f2'      # 唯一浅填充（浅绿灰）
FILL2 = '#eaf1f7'     # 极浅蓝（仅用于次区块；总数仍 ≤4）
WHITE = '#ffffff'

records = []


def tw(s, fs):
    """估算字符串渲染宽度：CJK 记 1.0 em，其余（含 ·/μ/Ω 按窄字符）记 0.56 em。"""
    return sum(fs if ord(c) > 0x2000 and c != '·' else fs * 0.56 for c in s)


def render_png(name, w, h):
    svg = (OUT / (name + '.svg')).read_text(encoding='utf-8')
    html = ('<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;background:white}svg{display:block}</style>' + svg)
    tmp = ROOT / 'tmp' / 'p5_render'
    tmp.mkdir(parents=True, exist_ok=True)
    hp = tmp / (name + '.html')
    hp.write_text(html, encoding='utf-8')
    png = tmp / (name + '.png')
    png.unlink(missing_ok=True)
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
        im = im.crop((max(0, cols[0] - pad), max(0, rows[0] - pad),
                      min(im.width, cols[-1] + pad), min(im.height, rows[-1] + pad)))
        im.save(dest)
    except ImportError:
        dest.write_bytes(png.read_bytes())


class Fig:
    def __init__(self, name, w, h):
        self.name = name
        self.w = w
        self.h = h
        self.items = []
        self.minsize = 99

    def text(self, x, y, s, size=24, bold=False, anchor='middle', color=INK):
        self.minsize = min(self.minsize, size)
        self.items.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-family="Microsoft YaHei, SimSun, sans-serif" '
            f'font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{escape(s)}</text>')

    def box(self, x, y, w, h, lines, fill=WHITE, dash=False, fs=23, lead=30):
        self.items.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" '
            f'fill="{fill}" stroke="{INK}" stroke-width="2"'
            + (' stroke-dasharray="7 5"' if dash else '') + '/>')
        n = len(lines)
        start = y + h / 2 - (n - 1) * lead / 2 + fs * 0.35
        for i, ln in enumerate(lines):
            self.text(x + w / 2, start + i * lead, ln, fs, i == 0)

    def boxl(self, x, y, w, h, lines, fill=WHITE, dash=False, fs=23, lead=30, padx=12):
        """左对齐多行盒（首行加粗）；生成期校验每行估宽不超内宽。"""
        self.items.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" '
            f'fill="{fill}" stroke="{INK}" stroke-width="2"'
            + (' stroke-dasharray="7 5"' if dash else '') + '/>')
        n = len(lines)
        start = y + h / 2 - (n - 1) * lead / 2 + fs * 0.35
        for i, ln in enumerate(lines):
            if tw(ln, fs) > w - 2 * padx:
                raise SystemExit(f'[{self.name}] 文字撑破盒子：{ln!r} 估宽 {tw(ln, fs):.0f}px '
                                 f'> 容器 {w - 2 * padx:.0f}px')
            if start + i * lead > y + h - 6:
                raise SystemExit(f'[{self.name}] 行溢出盒底：{ln!r}')
            self.text(x + padx, start + i * lead, ln, fs, i == 0, 'start')

    def line(self, pts, arrow=False, dash=False, w=2.0, color=INK):
        self.items.append(
            '<path d="M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in pts) +
            f'" fill="none" stroke="{color}" stroke-width="{w}"'
            + (' stroke-dasharray="7 5"' if dash else '')
            + (' marker-end="url(#ar)"' if arrow else '') + '/>')

    def dot(self, x, y, r=4):
        self.items.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{INK}"/>')

    def badge(self, x, y, n, r=16):
        self.items.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{WHITE}" stroke="{INK}" stroke-width="2"/>')
        self.text(x, y + 7, str(n), 23, True, 'middle')

    def fit_text(self, x, y, s, fs=23, anchor='start', color=INK, limit=None):
        """单行文本 + 越界自检。limit 缺省为画布内宽。"""
        if limit is None:
            limit = (self.w - 2 * 12) if anchor == 'start' else (2 * (x if anchor == 'middle' else 0))
        if tw(s, fs) > limit:
            raise SystemExit(f'[{self.name}] 单行超宽：{s!r} 估宽 {tw(s, fs):.0f}px > {limit:.0f}px')
        self.text(x, y, s, fs, False, anchor, color)

    def save(self):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">'
               '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
               f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker></defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="white"/>'
               '<g font-family="Microsoft YaHei, SimSun, sans-serif">' + ''.join(self.items) + '</g></svg>\n')
        (OUT / (self.name + '.svg')).write_text(svg, encoding='utf-8', newline='\n')
        render_png(self.name, self.w, self.h)
        records.append({'name': self.name, 'width': self.w, 'height': self.h,
                        'min_text_px': self.minsize,
                        'min_text_pt_at_1000': round(self.minsize * 420 / self.w, 2),
                        'svg_sha256': hashlib.sha256(svg.encode()).hexdigest()})
        print(f'written: {self.name} ({self.w}x{self.h}, min {self.minsize}px)')


# ───────────────────────── 图3-2 GD32F103CBT6 最小系统 ─────────────────────────
def gd32():
    f = Fig('图3-2_GD32F103CBT6最小系统原理图', 1000, 704)

    # 中央主控（312 宽，内宽 284）
    mx, mw = 344, 312
    f.items.append(f'<rect x="{mx}" y="80" width="{mw}" height="480" rx="4" '
                   f'fill="{WHITE}" stroke="{INK}" stroke-width="2.6"/>')
    f.text(mx + mw / 2, 112, 'GD32F103CBT6', 28, True)
    f.text(mx + mw / 2, 146, 'LQFP48 · Cortex-M3', 23)
    f.text(mx + mw / 2, 178, '128 KB Flash', 23)
    f.text(mx + mw / 2, 208, '20 KB SRAM', 23)
    f.line([(mx + 14, 224), (mx + mw - 14, 224)], w=1.4, color=GRAY)
    rows = [('差压 ΔP', 'PA0'), ('干管参照', 'PA1'), ('流量 Q', 'PB6/TIM4_CH1'),
            ('LoRa', 'PA9/PA10'), ('microSD', 'PA4—PA7'), ('ADC/RTC', 'PB8/PB9'),
            ('SWD', 'PA13/PA14'), ('调试串口', 'PA2/PA3')]
    y = 252
    for k, v in rows:
        if tw(k, 23) + tw(v, 23) + 28 > mw - 28:
            raise SystemExit(f'[图3-2] 引脚行超宽：{k} / {v}')
        f.text(mx + 14, y, k, 23, False, 'start')
        f.text(mx + mw - 14, y, v, 23, False, 'end')
        y += 33
    f.text(mx + mw / 2, 528, '内置 12 位 ADC 主路径', 23, False, 'middle', GRAY)

    # 左列（310 宽，内宽 286）：电源 / 复位 / 启动
    f.boxl(14, 86, 310, 150, ['电源与去耦（3.3 V）', 'VDD / VDDA / VBAT', '去耦 100 nF×n + 4.7 µF'], FILL)
    f.line([(324, 161), (344, 161)], arrow=True)

    f.boxl(14, 290, 310, 120, ['复位电路', 'NRST + 10 kΩ 上拉', '100 nF 滤波 + 按键'], WHITE)
    f.line([(324, 350), (344, 350)], arrow=True)

    f.boxl(14, 450, 310, 110, ['启动方式', 'BOOT0 10 kΩ 下拉', 'BOOT1 接地'], WHITE)
    f.line([(324, 505), (344, 505)], arrow=True)

    # 右列（310 宽）：时钟 / 片内资源 / 供电边界
    f.boxl(676, 86, 310, 164, ['时钟', '8 MHz HSE 晶振', '2×22 pF 负载电容',
                               '32.768 kHz LSE 可选'], FILL)
    f.line([(676, 168), (656, 168)], arrow=True)

    f.boxl(676, 270, 310, 186, ['片内资源', 'ADC×2（16× 过采样）', 'TIM4 脉冲计数', 'USART1 · SPI1',
                                'I2C1（PB8/PB9 重映射）'], FILL2)
    f.line([(656, 363), (676, 363)], arrow=True)

    f.boxl(676, 466, 310, 94, ['供电边界', '3.3 V 单电源', '24 V 仅供两线制变送器'], WHITE, lead=30)
    f.line([(656, 513), (672, 513)], arrow=False)

    # 底注
    f.fit_text(14, 602, '注：内置 12 位 ADC 为主路径；SGM58031（16 位 I²C）为可选升级模块，非必装。')
    f.text(14, 640, '本图为最小系统功能框图，非可投板 EDA 原理图；取值按官方推荐，实物待台架验证。',
           23, False, 'start', GRAY)
    f.save()


# ───────────────────────── 图3-1 系统总体结构（四部分） ─────────────────────────
def fig31():
    """按正文「感知诊断节点 / LoRa 接收端 / 本地巡检平台 / 双支路清水台架四部分组成」重绘。
    图内不设大标题（避免与图题重复或互相矛盾），四部分以 ①②③④ 直接对应正文。"""
    f = Fig('图3-1_系统总体结构', 1000, 650)

    y0, hh = 40, 250
    boxes = [
        (25, 290, ['① 感知诊断节点', '差压 P1 / 干管参照 P0', '脉冲流量 Q',
                   '本地特征 + 分块判据', 'microSD 事件日志', 'GD32F103CBT6', '内置 12 位 ADC'], FILL),
        (405, 200, ['② LoRa 接收端', 'E220-400T22D', '3.3 V 逻辑', 'USB-TTL 转换', '接入计算机'], WHITE),
        (695, 280, ['③ 本地巡检平台', '接收服务：校验 / 去重', '写库并回复确认（ACK）',
                    'Web：趋势 / 证据', '处置 / 人工复测'], FILL2),
    ]
    for x, w, lines, fill in boxes:
        f.boxl(x, y0, w, hh, lines, fill, lead=32)

    # 主链路箭头（标签走英文缩写，宽度可容于 90px 间隙）
    ay = y0 + 120
    f.line([(315, ay), (405, ay)], arrow=True)
    f.text(360, ay - 14, 'LoRa', 23, False, 'middle', GRAY)
    f.line([(605, ay), (695, ay)], arrow=True)
    f.text(650, ay - 14, 'UART', 23, False, 'middle', GRAY)

    # 确认回传（虚线）：③ 底部 → ① 底部；文字白底切断虚线，方向靠箭头表达
    f.line([(835, y0 + hh), (835, 326), (200, 326), (200, y0 + hh)], dash=True, arrow=True, w=1.8)
    _s = '事件确认与重传（ACK）'
    _w = tw(_s, 23)
    f.items.append(f'<rect x="{500 - _w / 2 - 8:.1f}" y="296" width="{_w + 16:.1f}" '
                   f'height="32" fill="{WHITE}"/>')
    f.text(500, 320, _s, 23, False, 'middle', GRAY)

    # ④ 双支路清水台架（向节点提供标定与注入工况）
    f.boxl(25, 370, 950, 170, [
        '④ 双支路清水台架（向 ① 提供健康标定与故障注入工况）',
        'A 支路：Q → P0 → 受限 R → P1，末端分正常出流与泄漏旁路',
        'B 支路：切换阀 + 可调负载，模拟另一支管轮灌',
        '泄漏旁路经独立容器计量，用于误报与检出对照'], FILL, lead=34)

    # 台架 → 节点
    f.line([(120, 370), (120, y0 + hh)], arrow=True)

    # 底注
    f.fit_text(25, 578, '注：①②③④ 与正文「四部分组成」一一对应；接收端不参与诊断决策。')
    f.text(25, 616, '实线为测量与业务数据流，虚线为事件确认回传；台架为验证条件，不属田间部署范围。',
           23, False, 'start', GRAY)
    f.save()


# ───────────────────────── 图3-8 双支路台架三维布局 ─────────────────────────
def bench():
    f = Fig('图3-8_双支路台架三维布局', 1000, 700)
    s = 48.0
    cx, cy = 260, 150
    CA, SA = 0.866, 0.5

    def P(x, y, z=0.0):
        return (cx + (x - y) * CA * s, cy + (x + y) * SA * s - z * s)

    def poly(ps, fl, sw=1.6):
        f.items.append('<path d="M ' + ' L '.join(f'{p[0]:.1f} {p[1]:.1f}' for p in ps) +
                       f' Z" fill="{fl}" stroke="{INK}" stroke-width="{sw}"/>')

    # 底板（含厚度）
    A, B, C, D = P(0, 0), P(9, 0), P(9, 4), P(0, 4)
    th = 10
    for e1, e2 in [(D, C), (C, B)]:
        f.items.append('<path d="M ' + ' L '.join(
            f'{p[0]:.1f} {p[1]:.1f}' for p in [e1, e2, (e2[0], e2[1] + th), (e1[0], e1[1] + th)]) +
            f' Z" fill="#dfe5e3" stroke="{INK}" stroke-width="1.6"/>')
    poly([A, B, C, D], '#f4f6f5', 2)
    for px, py in [(0.35, 0.35), (8.65, 0.35), (8.65, 3.65), (0.35, 3.65)]:
        q = P(px, py)
        f.items.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="3" fill="{INK}"/>')

    # 管路：A 支路（y=2，含全部测点）；B 支路（y=0.7，模拟轮灌）
    for yy, wd in [(2.0, 6), (0.7, 4.5)]:
        ps = [P(0.4, yy), P(8.5, yy)]
        f.items.append('<path d="M ' + ' L '.join(f'{p[0]:.1f} {p[1]:.1f}' for p in ps) +
                       f'" fill="none" stroke="{INK}" stroke-width="{wd}" stroke-linecap="round"/>')

    # 三通：Q 之后分 A / B 两支（Q 计量两支总流量）
    f.line([P(1.95, 2.0), P(1.95, 0.7)], w=4.5)

    obstacles = []

    def cube(x, y, w, d, h, fill):
        t = [P(x, y, h), P(x + w, y, h), P(x + w, y + d, h), P(x, y + d, h)]
        b = [P(x, y, 0), P(x + w, y, 0), P(x + w, y + d, 0), P(x, y + d, 0)]
        poly([t[3], t[2], b[2], b[3]], '#e9edeb')   # +y 侧面
        poly([t[1], t[2], b[2], b[1]], WHITE)       # +x 正面
        poly(t, fill)                               # 顶面
        allp = t + b
        xs = [p[0] for p in allp]
        ys = [p[1] for p in allp]
        obstacles.append((min(xs), min(ys), max(xs), max(ys)))
        return (min(xs), min(ys), max(xs), max(ys))

    # 组件：严格按 流量计Q → 取压嘴A(P0) → 区段R → 取压嘴B(P1) → 泄漏旁路 → A 负载
    tops = {}
    tops[1] = cube(0.95, 1.70, 0.90, 0.60, 0.85, FILL)     # 流量计 Q
    tops[2] = cube(2.25, 1.87, 0.22, 0.26, 1.30, FILL2)    # P0 取压嘴
    tops[3] = cube(3.20, 1.62, 1.00, 0.76, 0.90, FILL)     # 区段 R（φ5.0 孔板 + 针阀）
    tops[4] = cube(4.55, 1.87, 0.22, 0.26, 1.30, FILL2)    # P1 取压嘴
    tops[5] = cube(6.10, 1.60, 0.95, 0.80, 0.95, WHITE)    # A 正常负载
    tops[6] = cube(5.15, 2.62, 0.40, 0.42, 0.80, FILL)     # 泄漏球阀
    tops[7] = cube(6.60, 0.42, 0.55, 0.56, 0.80, WHITE)    # B 切换阀（模拟轮灌）
    tops[8] = cube(7.80, 0.40, 0.90, 0.60, 0.90, WHITE)    # B 正常负载

    # 泄漏支路（P1 之后引出，走向独立计量）
    f.line([P(5.35, 2.0), P(5.35, 3.05)], w=4.5)
    f.line([P(5.35, 3.05), P(5.35, 3.55)], w=4.5)
    q = P(5.35, 3.72)
    f.items.append(f'<ellipse cx="{q[0]:.1f}" cy="{q[1]:.1f}" rx="18" ry="8" '
                   f'fill="{FILL2}" stroke="{INK}" stroke-width="1.6"/>')

    # 采集与 LoRa 节点盒（板外右上）+ 两路取压信号（虚线）
    f.boxl(700, 96, 272, 116, ['采集与 LoRa 节点盒', 'MCU + 变送器 + 电池'], FILL, lead=32)
    obstacles.append((700, 96, 972, 212))
    tops[9] = (700, 96, 972, 212)
    for tgt in (tops[2], tops[4]):
        f.line([(700, 176), ((tgt[0] + tgt[2]) / 2, (tgt[1] + tgt[3]) / 2 - 4)],
               dash=True, w=1.4, color=GRAY)

    # 防溅板（泄漏区虚线框）
    dp = [P(4.85, 2.45), P(6.05, 2.45), P(6.05, 3.95), P(4.85, 3.95)]
    f.items.append('<path d="M ' + ' L '.join(f'{p[0]:.1f} {p[1]:.1f}' for p in dp) +
                   f' Z" fill="none" stroke="{GRAY}" stroke-width="1.6" stroke-dasharray="6 4"/>')

    # 编号徽标：先按等轴测方向强制抬到元件正上方/正下方（指认唯一），冲突时再自动找位
    r = 16
    placed = []
    forced = {1: (1.30, 1.55, 1.45), 2: (2.36, 1.20, 1.85), 3: (3.70, 1.50, 1.45),
              4: (4.66, 1.20, 1.85), 5: (6.55, 1.20, 1.50), 6: (5.35, 3.10, 1.55),
              7: (6.90, 0.10, 1.35), 8: (8.25, 0.05, 1.35)}
    for k in sorted(tops):
        x1, y1, x2, y2 = tops[k]
        bx, by = (x1 + x2) / 2, (y1 + y2) / 2
        cands = ([P(*forced[k])] if k in forced else []) + [
            (bx, y1 - r - 8), (bx, y1 - r - 36), (x1 - r - 8, by), (x2 + r + 8, by),
            (bx, y2 + r + 10), (x1 - r - 34, y1 - r - 16), (x2 + r + 34, y1 - r - 16)]
        pick = None
        for x, y in cands:
            if not (14 + r < x < f.w - 14 - r and 14 + r < y < 468 - r):
                continue
            if any((px - x) ** 2 + (py - y) ** 2 < (2 * r + 8) ** 2 for px, py in placed):
                continue
            if any(x + r > o[0] and x - r < o[2] and y + r > o[1] and y - r < o[3] for o in obstacles):
                continue
            pick = (x, y)
            break
        if pick is None:
            raise SystemExit(f'[图3-8] 编号 {k} 无可用徽标位置')
        placed.append(pick)
        px, py = pick
        # 短引线：徽标边缘 → 元件包围盒最近点，保证指认唯一
        nx = min(max(px, x1), x2)
        ny = min(max(py, y1), y2)
        dx, dy = nx - px, ny - py
        d = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        f.line([(px + dx / d * (r + 2), py + dy / d * (r + 2)), (nx, ny)], w=1.2, color=GRAY)
        f.badge(px, py, k)

    # 图例（三列三行）
    leg = [('1', '流量计 Q（SEN0549）'), ('2', '取压嘴 A（P0）'), ('3', '区段 R 孔板+针阀'),
           ('4', '取压嘴 B（P1）'), ('5', 'A 正常负载'), ('6', '泄漏球阀+独立计量'),
           ('7', 'B 切换阀（模拟轮灌）'), ('8', 'B 正常负载'), ('9', '采集与 LoRa 节点盒')]
    lx = [40, 372, 692]
    for i, (n, t) in enumerate(leg):
        col = i % 3
        row = i // 3
        x = lx[col]
        y = 500 + row * 36
        if tw(t, 23) + 26 > 300:
            raise SystemExit(f'[图3-8] 图例超宽：{t!r} {tw(t, 23):.0f}px')
        f.items.append(f'<circle cx="{x}" cy="{y-7}" r="13" fill="{WHITE}" stroke="{INK}" stroke-width="1.6"/>')
        f.text(x, y, n, 23, True, 'middle')
        f.text(x + 22, y, t, 23, False, 'start')

    # 底注
    f.fit_text(40, 640, '等轴测布局示意，尺寸为相对关系；实际 De25 管路、φ5.0 孔板与针阀按台架确定。')
    f.text(40, 676, 'Q 位于最上游，两取压嘴均在其下游；泄漏先独立计量，再人工回水。',
           23, False, 'start', GRAY)
    f.save()


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('gd32', 'all'):
        gd32()
    if which in ('fig31', 'all'):
        fig31()
    if which in ('bench', 'all'):
        bench()
    (ROOT / 'tmp' / 'p5_fig_records.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
