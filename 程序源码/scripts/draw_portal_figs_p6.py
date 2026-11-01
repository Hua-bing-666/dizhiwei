"""P6 · 答辩页 6 张系统/诊断/时序矢量图（补齐 portal 缺失引用）。

口径真源：docs/硬件软件匹配度审查_v2.2.md + measurement_interfaces.svg（P4 已验收）
  - 差压 MDM490 0—40 kPa（跨区段）→150Ω→PA0(ΔP)；干管参照 0—200 kPa→150Ω→PA1
  - 两路 24 V（XL6009 + PB0 高边）间歇；BAT54S 钳位
  - SEN0549 5V→10k+20k→SN74LVC1G17→PB6/TIM4_CH1
  - 1 s 提交 + 10 s 不重叠块 CUSUM（k=0.5, n=0.5, h*=26）
全部 1000px 画布字符串直构 SVG，Edge 截图→PNG；正文 ≥23px（≥9.5pt@1000→420pt）。
输出：application/figures/{system_scope,dual_pressure_layout,pressure_frontend,
      diagnosis_flow,protocol_sequence,normal}.{svg,png}
"""
import subprocess, sys, time, uuid
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application' / 'figures'
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'

INK = '#142a30'; GRAY = '#52636a'; FILL = '#eef5f2'; FILL2 = '#eaf1f7'
WHITE = '#ffffff'; ACC = '#b8543f'; TEAL = '#1d4a45'; LINE = '#9fb3ab'

def tw(s, fs):
    return sum(fs if ord(c) > 0x2000 and c != '·' else fs * 0.56 for c in s)

def render_png(name, w, h):
    svg = (OUT / (name + '.svg')).read_text(encoding='utf-8')
    html = ('<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;background:white}svg{display:block}</style>' + svg)
    tmp = ROOT / 'tmp' / 'p6_portal'
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
        im = Image.open(png).convert('RGB')
        px = im.load(); W, H = im.size
        def wr(y): return all(px[x, y] == (255, 255, 255) for x in range(0, W, 7))
        def wc(x): return all(px[x, y] == (255, 255, 255) for y in range(0, H, 7))
        top = next((y for y in range(H) if not wr(y)), 0)
        bot = next((y for y in range(H - 1, -1, -1) if not wr(y)), H)
        left = next((x for x in range(W) if not wc(x)), 0)
        right = next((x for x in range(W - 1, -1, -1) if not wc(x)), W)
        pad = 12
        im = im.crop((max(0, left - pad), max(0, top - pad), min(W, right + pad), min(H, bot + pad)))
        im.save(dest)
    except ImportError:
        dest.write_bytes(png.read_bytes())
    print(f'written: {name} (min {FIG_MIN.get(name,0)}px)')

FIG_MIN = {}

class Fig:
    def __init__(self, name, w, h):
        self.name, self.w, self.h = name, w, h
        self.items = []; self.minsize = 99
    def text(self, x, y, s, size=24, bold=False, anchor='middle', color=INK):
        self.minsize = min(self.minsize, size)
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-family="Microsoft YaHei,SimSun,sans-serif" font-weight="{700 if bold else 400}" '
            f'text-anchor="{anchor}" fill="{color}">{escape(s)}</text>')
    def text_rot(self, x, y, s, size=23, color=INK):
        self.minsize = min(self.minsize, size)
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" transform="rotate(-90 {x:.1f} {y:.1f})" '
            f'font-size="{size}" font-family="Microsoft YaHei,SimSun,sans-serif" '
            f'text-anchor="middle" fill="{color}">{escape(s)}</text>')
    def box(self, x, y, w, h, lines, fill=WHITE, dash=False, fs=23, lead=32, stroke=INK, padx=10):
        for ln in lines:
            if tw(ln, fs) > w - 2*padx:
                raise SystemExit(f'[{self.name}] 撑破: {ln!r} {tw(ln,fs):.0f}>{w-2*padx} (w={w})')
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="5" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"'
            + (' stroke-dasharray="8 5"' if dash else '') + '/>')
        n = len(lines); start = y + h/2 - (n-1)*lead/2 + fs*0.35
        if start + (n-1)*lead > y + h - 6:
            raise SystemExit(f'[{self.name}] 行溢出: {lines!r}')
        for i, ln in enumerate(lines):
            self.text(x+w/2, start+i*lead, ln, fs, i == 0)
    def line(self, pts, arrow=True, dash=False, w=2.2, color=INK):
        self.items.append('<path d="M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in pts)
            + f'" fill="none" stroke="{color}" stroke-width="{w}"'
            + (' stroke-dasharray="8 5"' if dash else '')
            + (' marker-end="url(#ar)"' if arrow else '') + '/>')
    def path(self, d, color=INK, w=2.6, dash=False):
        self.items.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}"'
            + (' stroke-dasharray="8 5"' if dash else '') + '/>')
    def save(self):
        FIG_MIN[self.name] = self.minsize
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">'
               '<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
               f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker></defs>'
               f'<rect width="{self.w}" height="{self.h}" fill="white"/>'
               '<g font-family="Microsoft YaHei,SimSun,sans-serif">' + ''.join(self.items) + '</g></svg>\n')
        (OUT / (self.name + '.svg')).write_text(svg, encoding='utf-8', newline='\n')
        render_png(self.name, self.w, self.h)

def title(f, main, sub):
    f.text(28, 44, main, 30, True, 'start')
    f.text(28, 78, sub, 23, False, 'start', GRAY)

# ───────────────────────── 1. system_scope ─────────────────────────
def system_scope():
    f = Fig('system_scope', 1000, 620)
    title(f, '系统组成与独立评价', '感知诊断节点 — LoRa — 本地维护软件；试验评价独立于主链路，用独立标签核对')
    # A 感知节点
    f.box(40, 130, 300, 300, ['感知诊断节点', 'GD32F103CBT6 主控', 'MDM490 差压 0—40 kPa', '干管参照 0—200 kPa',
                              'SEN0549 脉冲流量', 'E220-400T22D'], FILL, fs=23, lead=42)
    # B 接收/本地Web
    f.box(420, 170, 230, 220, ['接收端 / 本地 Web', '告警与历史', '人工核查记录', '处置与复测', '证据归档'], FILL2, fs=23, lead=36)
    # C 独立试验评价
    f.box(730, 170, 230, 220, ['独立试验评价', '台架真值与注入量', '独立标签', '离线回放', '不参与在线告警'], WHITE, dash=True, fs=23, lead=36, stroke=ACC)
    f.line([(340, 280), (418, 280)]); f.text(379, 262, 'LoRa', 23, False, 'middle', ACC)
    f.text(379, 312, '433 MHz', 23, False, 'middle', GRAY)
    f.line([(650, 280), (728, 280)], dash=True)
    f.text(689, 262, '独立核对', 23, False, 'middle', ACC)
    f.text(28, 494, '说明：在线链路只做 感知 → 回传 → 告警 → 维护 闭环；', 23, False, 'start', GRAY)
    f.text(28, 532, '试验评价用台架真值独立判定，避免“用自己的模型证明自己”。', 23, False, 'start', GRAY)
    f.text(28, 572, 'LoRa 功率 ≤10 dBm（433 MHz 免执照合规）；节点与终端均本地部署，不依赖云平台。', 23, False, 'start', GRAY)
    f.save()

# ───────────────────────── 2. dual_pressure_layout ─────────────────────────
def dual_pressure_layout():
    f = Fig('dual_pressure_layout', 1000, 720)
    title(f, '台架测点与独立收集', '水路口径 Q 最上游；差压跨区段 R 两端取压；泄漏支路独立收集杯')
    y0 = 300; BW, BH = 140, 96
    f.line([(90, y0), (880, y0)], w=7, color=GRAY)
    cx = {'Q': 160, 'P0': 320, 'R': 480, 'P1': 640}
    f.box(cx['Q']-BW/2, y0-BH/2, BW, BH, ['① Q', '流量计'], FILL2)
    f.box(cx['P0']-BW/2, y0-BH/2, BW, BH, ['② P0', '取压嘴A'], FILL)
    f.box(cx['R']-BW/2, y0-BH/2, BW, BH, ['③ R', '孔板+针阀'], FILL)
    f.box(cx['P1']-BW/2, y0-BH/2, BW, BH, ['④ P1', '取压嘴B'], FILL)
    # 差压变送器跨接 P0-P1
    f.box(355, 122, 250, 108, ['差压变送器 MDM490', '0—40 kPa', 'ΔP = P1 − P0'], WHITE, stroke=ACC, fs=23)
    f.line([(cx['P0'], y0-BH/2), (cx['P0'], 176), (353, 176)], w=2.4, dash=True, color=ACC)
    f.line([(cx['P1'], y0-BH/2), (cx['P1'], 176), (607, 176)], w=2.4, dash=True, color=ACC)
    f.text(cx['P0'], 210, 'P0 干管参照', 23, False, 'middle', ACC)
    f.text(cx['P1'], 210, 'P1 支管', 23, False, 'middle', ACC)
    # 下游：正常负载 + 泄漏独立收集
    f.line([(710, y0), (710, 470)], w=7, color=GRAY)
    f.line([(710, 470), (830, 470)], w=7, color=GRAY)
    f.box(640, 470, 140, 96, ['⑤ A', '正常负载'], FILL)
    f.box(820, 470, 140, 96, ['⑥ 泄漏', '独立收集'], WHITE, stroke=ACC)
    f.text(28, 620, '图注：Q → P0 → ③R → P1 → ⑤A 正常负载 / ⑥泄漏独立收集（水路 Q 最上游）。', 23, False, 'start', GRAY)
    f.text(28, 660, '差压表跨接 R 两端直接测 ΔP=P1−P0（量程/信号比由两表相减的 20—40 倍降到 4—8 倍）。', 23, False, 'start', GRAY)
    f.save()

# ───────────────────────── 3. pressure_frontend ─────────────────────────
def pressure_frontend():
    f = Fig('pressure_frontend', 1000, 760)
    title(f, '双压力采集电气原理', '24 V 高边间歇供两线制变送器；150 Ω 取样 + BAT54S 钳位进 ADC；流量脉冲整形后计数')
    # 电源
    f.box(30, 158, 150, 74, ['电池', '12—16.8 V'], FILL2)
    f.box(210, 150, 160, 90, ['XL6009 升压', '24 V·高边'], FILL)
    f.line([(180, 195), (208, 195)]); f.text(206, 176, 'PB0', 23, False, 'end', ACC)
    # 两线制变送器
    f.box(410, 116, 170, 80, ['MDM490 差压', '0—40 kPa'], FILL)
    f.box(410, 236, 170, 80, ['干管参照表压', '0—200 kPa'], FILL)
    f.line([(370, 186), (392, 186), (392, 156), (408, 156)])
    f.line([(370, 200), (392, 200), (392, 276), (408, 276)])
    # 取样+钳位
    f.box(610, 116, 150, 72, ['150 Ω 取样', 'BAT54S钳位'], WHITE)
    f.box(610, 236, 150, 72, ['150 Ω 取样', 'BAT54S钳位'], WHITE)
    f.line([(580, 156), (608, 156)]); f.line([(580, 276), (608, 276)])
    # MCU
    f.box(792, 116, 198, 210, ['GD32F103CBT6', '内置 12 位 ADC', 'PA0 ← ΔP', 'PA1 ← 参照'], FILL2, fs=23, lead=44)
    f.line([(760, 156), (790, 156)])
    f.line([(760, 276), (790, 276)])
    # 流量链
    f.box(30, 470, 160, 80, ['SEN0549', '5 V 供电'], FILL)
    f.box(230, 470, 190, 80, ['10k+20k 分压', 'SN74LVC1G17'], FILL)
    f.box(460, 470, 150, 80, ['PB6 计数', 'TIM4_CH1'], FILL2)
    f.line([(190, 510), (228, 510)]); f.text(210, 452, '5 V', 23, False, 'middle', GRAY)
    f.line([(420, 510), (458, 510)]); f.text(440, 452, '3.3 V', 23, False, 'middle', GRAY)
    f.line([(610, 510), (900, 510), (900, 326)], w=2.2)
    f.text(760, 500, '→ 内部计数', 23, False, 'middle', GRAY)
    # 说明
    f.text(28, 640, '采样窗内上电、读完即断电（T_set 待台架实测）；', 23, False, 'start', GRAY)
    f.text(28, 676, '故障电流由钳位管旁路，3.3 V 轨常态负载须 >15 mA。', 23, False, 'start', GRAY)
    f.text(28, 712, '候选功能图，非可投板原理图或接线完成证明。', 23, False, 'start', GRAY)
    f.save()

# ───────────────────────── 4. diagnosis_flow ─────────────────────────
def diagnosis_flow():
    f = Fig('diagnosis_flow', 1000, 800)
    title(f, '核心诊断流程', '1 s 提交 + 10 s 不重叠块 CUSUM（k=0.5, n=0.5, h*=26）；越限告警并留证据')
    cx = 470; bw = 380; bh = 64; gap = 22
    steps = [('1 s 采样 Q / P0 / P1', FILL2), ('10 s 不重叠块取算术平均', FILL),
             ('CUSUM 累积（k=0.5, n=0.5）', FILL), ('S > h* = 26 ?', WHITE),
             ('告警 + 本地记录（证据帧）', FILL), ('LoRa 上报 + 人工核查', FILL2),
             ('处置', FILL), ('同工况复测 → 证据归档', FILL2)]
    y = 120
    ys = []
    for i, (lab, fill) in enumerate(steps):
        dash = (i == 3)
        stroke = ACC if i in (3, 4) else INK
        f.box(cx - bw/2, y, bw, bh, [lab], fill, dash=dash, stroke=stroke)
        ys.append(y)
        if i < len(steps) - 1:
            f.line([(cx, y + bh), (cx, y + bh + gap)])
        y += bh + gap
    # “否”回路：判定下方折向左回到采样
    yj = ys[3]
    f.line([(cx - bw/2, yj + bh/2), (150, yj + bh/2), (150, ys[0] + bh/2), (cx - bw/2, ys[0] + bh/2)],
           dash=True, color=GRAY)
    f.text(250, yj + bh/2 - 12, '否：继续下一块', 23, False, 'middle', GRAY)
    f.text(cx + 18, yj - 6, '是', 23, True, 'start', ACC)
    f.save()

# ───────────────────────── 5. protocol_sequence ─────────────────────────
def protocol_sequence():
    f = Fig('protocol_sequence', 1000, 660)
    title(f, '确认与重试时序', '节点上报 → 网关 ACK → 超时重发 → 去重；断电重启后按序补发，帧长 55/57/24 B')
    xa, xb = 220, 760            # 两条生命线
    ytop, ybot = 140, 560
    f.box(xa-90, 100, 180, 56, ['节点'], FILL2)
    f.box(xb-90, 100, 180, 56, ['网关 / 接收端'], FILL)
    f.line([(xa, 156), (xa, ybot)], arrow=False, w=2, color=GRAY)
    f.line([(xb, 156), (xb, ybot)], arrow=False, w=2, color=GRAY)
    f.line([(xa, 200), (xb, 200)]); f.text((xa+xb)/2, 188, '上报帧 EVT（55 B）', 23, False, 'middle', INK)
    f.line([(xb, 260), (xa, 260)]); f.text((xa+xb)/2, 248, 'ACK（24 B）', 23, False, 'middle', TEAL)
    f.line([(xa, 330), (xb, 330)], dash=True, color=ACC); f.text((xa+xb)/2, 318, '超时未收 ACK → 重发', 23, False, 'middle', ACC)
    f.line([(xb, 390), (xa, 390)]); f.text((xa+xb)/2, 378, 'ACK（去重后）', 23, False, 'middle', TEAL)
    f.line([(xa, 470), (xb, 470)]); f.text((xa+xb)/2, 458, '断电重启 → 按序补发', 23, False, 'middle', GRAY)
    f.text(28, 596, '重试上限与退避固定；同一事件 ID 幂等去重，避免重复告警。', 23, False, 'start', GRAY)
    f.text(28, 636, '去重窗口与补发条数由固件常量约束。', 23, False, 'start', GRAY)
    f.save()

# ───────────────────────── 6. normal（合成模型响应） ─────────────────────────
def normal():
    f = Fig('normal', 1000, 700)
    title(f, '合成模型响应曲线', '相对同工况健康流量的偏离（%）；合成示意，参数未标定，非实测')
    x0, y0, x1, y1 = 115, 120, 930, 500
    vmax, vmin = 6.0, -6.0
    tmax = 600.0
    def px(t): return x0 + (t / tmax) * (x1 - x0)
    def py(v): return y0 + (vmax - v) / (vmax - vmin) * (y1 - y0)
    # 轴
    f.line([(x0, y1), (x1, y1)], arrow=False, w=2.2, color=INK)
    f.line([(x0, y0), (x0, y1)], arrow=False, w=2.2, color=INK)
    # 网格 + y 刻度
    for v in (-6, -3, 0, 3, 6):
        yy = py(v)
        f.line([(x0, yy), (x1, yy)], arrow=False, w=1, color=LINE)
        f.text(x0 - 14, yy + 8, f'{v:+d}' if v != 0 else '0', 23, False, 'end', GRAY)
    for t in (0, 120, 240, 360, 480, 600):
        xx = px(t)
        f.line([(xx, y0), (xx, y1)], arrow=False, w=1, color=LINE)
        f.text(xx, y1 + 34, str(t), 23, False, 'middle', GRAY)
    f.text((x0 + x1)/2, y1 + 74, '时间 t / s', 23, False, 'middle', GRAY)
    f.text_rot(x0 - 78, (y0 + y1)/2, '偏离 / %', 23, GRAY)
    # 曲线
    def curve(fn):
        pts = []
        for i in range(0, 121):
            t = tmax * i / 120
            pts.append((px(t), py(fn(t))))
        return 'M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in pts)
    import math
    normal_fn = lambda t: 0.15 * math.sin(t / 45.0)
    leak_fn = lambda t: 0.0 if t < 100 else min(5.0, (t - 100) / 300.0 * 5.0)
    rest_fn = lambda t: 0.0 if t < 100 else -min(4.0, (t - 100) / 260.0 * 4.0)
    over_fn = lambda t: (0.0 if t < 120 else 2.0 + 1.6 * math.sin((t - 120) / 60.0))
    f.path(curve(normal_fn), color=GRAY, w=2.6)
    f.path(curve(leak_fn), color=ACC, w=2.8)
    f.path(curve(rest_fn), color=TEAL, w=2.8)
    f.path(curve(over_fn), color=INK, w=2.4, dash=True)
    # 图例（横向置于图下方空白，避免压曲线）
    items = [('正常轮灌', GRAY, False), ('等效泄漏', ACC, False), ('上游节流/受限', TEAL, False), ('切换期（示意）', INK, True)]
    xs = [115, 330, 560, 780]; ly = 632
    for (lab, col, dash), lx in zip(items, xs):
        f.line([(lx, ly), (lx + 40, ly)], arrow=False, w=2.6, color=col, dash=dash)
        f.text(lx + 50, ly + 8, lab, 23, False, 'start', INK)
    f.save()

if __name__ == '__main__':
    for fn in (system_scope, dual_pressure_layout, pressure_frontend, diagnosis_flow, protocol_sequence, normal):
        try:
            fn()
        except SystemExit as e:
            print('ERROR', e)
