"""滴智卫 · 系统总体结构单色学术图（原生 SVG + PNG，黑白，可直接插入 Word）。

口径：v2.2 冻结契约（2026-10-18）——
- 测压：单只差压变送器 MDM490（0—40 kPa，跨区段 R）+ 干管参照表压（0—200 kPa）
- 主控：GD32F103CBT6，ADC 主路径为内置 12 位（PA0/PA1），SGM58031 仅可选升级
- 流量：SEN0549 脉冲（540 脉冲/L），PB6/TIM4_CH1 连续计数
- 判据：1 s 提交 + 10 s 不重叠块 CUSUM（k=0.5，h*=26，仿真基准）
- 通信：E220-400T22D（≤10 dBm），遥测 55 B / 事件 57 B / ACK 24 B
- 供电：XL6009 升 24 V，PB0 高边开关间歇供电，仅供两线制变送器
- 巡检平台：Web V1.3 八页面（总览/支管监测/异常事件/设备链路/历史记录/设置/策略实验/试验台架）

版式：canvas 宽 1000，全文最小字号 24px。
- 放置宽度 420 pt 时最小字号 10.08 pt，但高度 697 pt≈24.6 cm 已顶满 A4 纵版心；
  文档放置请用 **400 pt**（高 664 pt≈23.4 cm，最小字号 9.6 pt，仍 ≥9.5 pt）。
- 机器校验：scripts/verify_figure_layout.mjs 已登记（strict 单色通道）。
输出：deliverables/系统总体结构_单色学术版.svg / .png（PNG 由 Edge 无头截图 ×2 渲染）。
"""
from pathlib import Path
import subprocess, uuid, time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'

W, H = 1000, 1660
FONT = "Microsoft YaHei, SimSun, sans-serif"
INK = "#1a1a1a"
GRAY = "#555555"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, t, size=24, bold=False, anchor="middle", fill=INK):
    w = "700" if bold else "400"
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{w}" text-anchor="{anchor}" fill="{fill}">{esc(t)}</text>')


def box(x, y, w, h, lines, dashed=False, fs=24, gap=None):
    """带 data-kind="box" 标注的文本框；行距 fs+10（24px 字号下 bbox 高约 31.3px，
    34px 行距才能过 0.5px 重叠阈值）。框高须 ≥ (n-1)*gap+36。"""
    dash = ' stroke-dasharray="8 5"' if dashed else ""
    gap = gap or (fs + 10)
    first = y + h / 2 - ((len(lines) - 1) * gap) / 2 + fs * 0.36
    s = (f'<g data-kind="box"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" '
         f'fill="white" stroke="{INK}" stroke-width="2"{dash}/>')
    for i, ln in enumerate(lines):
        s += text(x + w / 2, first + i * gap, ln, fs, bold=(i == 0))
    s += '</g>'
    return s


def arrow(points, dashed=False, w=2.0):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    d = "M " + " L ".join(f"{px} {py}" for px, py in points)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}"{dash} '
            f'marker-end="url(#ar)"/>')


def plain_line(points, dashed=False, w=1.8):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    d = "M " + " L ".join(f"{px} {py}" for px, py in points)
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}"{dash}/>'


def container(x, y, w, h, label):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="white" '
         f'stroke="{INK}" stroke-width="1.6" stroke-dasharray="10 6"/>')
    s += text(x + 12, y + 32, label, 26, bold=True, anchor="start")
    return s


def waves(cx, cy, direction):
    """三道电波弧线；direction=+1 向下张开, -1 向上张开。"""
    s = ""
    for r in (8, 16, 24):
        dy = r * 0.62 * direction
        s += (f'<path d="M {cx-r} {cy} Q {cx} {cy+dy} {cx+r} {cy}" fill="none" '
              f'stroke="{INK}" stroke-width="1.6"/>')
    return s


S = []
S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}">')
S.append('<defs>'
         '<marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
         f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker>'
         '</defs>')
S.append(f'<rect width="{W}" height="{H}" fill="white"/>')

# ───────────────────────── 标题与图例 ─────────────────────────
S.append(text(28, 48, "滴智卫 · 系统总体结构", 32, bold=True, anchor="start"))
S.append(text(28, 88, "单色学术版 · 申报书用 · 选型与口径 v2.2（2026-10-18）", 24, fill=GRAY, anchor="start"))
S.append(text(28, 124, "图例：实线=数据/业务流，虚线=人工/参照/预留。", 24, fill=GRAY, anchor="start"))

# ───────────────────────── ① 双支路清水台架 ─────────────────────────
S.append(container(20, 138, 960, 470, "双支路清水台架（实验室验证平台）"))
S.append(text(40, 204, "A 支路（被测支管）", 24, anchor="start", fill=GRAY))
S.append(box(40, 216, 150, 76, ["供水首部", "压力可调"]))
S.append(box(220, 216, 140, 76, ["流量计 Q", "SEN0549"]))
S.append(box(390, 216, 150, 76, ["区段 R", "孔板+针阀"]))
S.append(arrow([(190, 254), (220, 254)]))
S.append(arrow([(360, 254), (390, 254)]))
# 分流：正常负载 / 泄漏旁路 → 独立收集与计量
S.append(box(570, 204, 150, 76, ["正常负载", "滴头模拟"]))
S.append(box(570, 296, 150, 76, ["泄漏旁路", "可调球阀"]))
S.append(box(760, 250, 190, 76, ["独立收集与计量", "参考流量"]))
S.append(arrow([(540, 254), (560, 254), (560, 242), (570, 242)]))
S.append(arrow([(540, 254), (560, 254), (560, 334), (570, 334)]))
S.append(arrow([(720, 242), (748, 242), (748, 288), (760, 288)]))
S.append(arrow([(720, 334), (748, 334), (748, 288), (760, 288)]))
# 传感行：干管参照 + 差压变送器（虚线=取压/参照）
S.append(box(40, 384, 220, 76, ["干管参照表压", "0—200 kPa"]))
S.append(box(300, 384, 300, 76, ["差压变送器 MDM490", "0—40 kPa · 跨区段 R"]))
S.append(arrow([(115, 292), (115, 322), (150, 322), (150, 382)], dashed=True, w=1.5))
S.append(arrow([(430, 292), (430, 382)], dashed=True, w=1.5))
S.append(arrow([(500, 292), (500, 382)], dashed=True, w=1.5))
S.append(text(438, 322, "A", 24, anchor="start", fill=GRAY))
S.append(text(492, 322, "B", 24, anchor="end", fill=GRAY))
# B 支路：模拟邻支路轮灌扰动
S.append(text(40, 498, "B 支路（模拟邻支路轮灌扰动）", 24, anchor="start", fill=GRAY))
S.append(box(40, 510, 150, 76, ["B 支路", "供水"]))
S.append(box(220, 510, 170, 76, ["开关阀", "模拟轮灌切换"]))
S.append(box(420, 510, 200, 76, ["末端可调堵塞", "背压抬升"]))
S.append(arrow([(190, 548), (220, 548)]))
S.append(arrow([(390, 548), (420, 548)]))
S.append(text(650, 556, "扰动以干管参照识别", 24, anchor="start", fill=GRAY))

# ───────────────────────── ② 感知诊断节点 ─────────────────────────
S.append(container(20, 628, 960, 340, "感知诊断节点（现场侧）"))
S.append(box(290, 673, 360, 216,
             ["GD32F103CBT6 主控",
              "1 s 提交 · 10 s 不重叠块",
              "K=Q/√P₁ · Rh=ΔP/Q²",
              "块 CUSUM k=0.5 · h*=26",
              "microSD 日志 · SPI1",
              "脉冲 PB6/TIM4_CH1"]))
S.append(box(30, 738, 200, 112, ["SGM58031", "可选升级", "16 位 I²C"], dashed=True))
S.append(plain_line([(230, 794), (290, 794)], dashed=True))
S.append(text(260, 786, "I²C1", 24, fill=GRAY))
S.append(box(720, 673, 220, 112, ["E220-400T22D", "LoRa ≤10 dBm", "USART1 PA9/10"]))
S.append(arrow([(650, 729), (720, 729)]))
# 24 V 高边开关供电注记
S.append(text(40, 919, "24 V 经 XL6009 升压、PB0 高边开关间歇供电，仅两线制变送器使用", 24, anchor="start", fill=GRAY))

# ───────────────────────── ③ LoRa 无线链路 ─────────────────────────
S.append(container(20, 988, 960, 160, "LoRa 无线链路"))
S.append(text(40, 1056, "LoRa 433 MHz · 发射 ≤10 dBm", 24, anchor="start"))
S.append(text(40, 1092, "遥测 55 B · 事件 57 B · ACK 24 B", 24, anchor="start", fill=GRAY))
S.append(text(40, 1128, "未确认 → 有界重传", 24, anchor="start", fill=GRAY))
S.append(waves(860, 1056, -1))

# ───────────────────────── ④ 接收端与本地巡检平台 ─────────────────────────
S.append(container(20, 1168, 960, 355, "接收端与本地巡检平台"))
S.append(box(40, 1218, 240, 90, ["E220 接收模块", "USB-TTL 串口桥"]))
S.append(box(380, 1218, 360, 148,
             ["PC 接收服务", "CRC 校验 · 去重", "SQLite 事务写入", "提交后回复 ACK"]))
S.append(arrow([(280, 1263), (380, 1263)]))
S.append(box(300, 1388, 420, 116,
             ["本地巡检平台（八页面）", "总览 · 监测 · 事件 · 设备 · 历史", "设置 · 策略实验 · 试验台架"]))
S.append(box(755, 1388, 210, 116,
             ["巡检闭环（人工）", "核查→处置→复测", "结果回写平台"], dashed=True))
S.append(arrow([(560, 1366), (560, 1386)]))
S.append(arrow([(720, 1442), (755, 1442)], dashed=True))
S.append(arrow([(755, 1458), (720, 1458)], dashed=True))

# 事件上行（节点 → 接收端）与 ACK 下行（接收端 → 节点）
S.append(arrow([(830, 785), (830, 1158), (160, 1158), (160, 1216)], w=2.4))
S.append(arrow([(740, 1293), (890, 1293), (890, 785)], dashed=True, w=2.0))

# ───────────────────────── 脚注 ─────────────────────────
S.append(text(28, 1565,
              "主流程：采集 → 本地诊断 → 事件上报 → 平台入库 → 核查处置 → 复测归档。",
              24, anchor="start", fill=GRAY))
S.append(text(28, 1599,
              "ΔP 0—40 kPa · 干管参照 0—200 kPa · Q 540 脉冲/L · K=Q/√P₁ · Rh=ΔP/Q²。",
              24, anchor="start", fill=GRAY))
S.append(text(28, 1633,
              "实物门限由台架实测重标；h*=26 为仿真基准；候选设计，非投板证明。",
              24, anchor="start", fill=GRAY))

S.append("</svg>")
svg = "\n".join(S)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "系统总体结构_单色学术版.svg").write_text(svg, encoding="utf-8", newline="\n")


def render_png():
    """SVG → PNG（Edge 无头截图 ×2 缩放 + 裁白边）。"""
    html = ('<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;background:white}svg{display:block}</style>' + svg)
    tmp = ROOT / 'tmp' / 'overview_render'
    tmp.mkdir(parents=True, exist_ok=True)
    hp = tmp / 'overview.html'
    hp.write_text(html, encoding='utf-8')
    png = tmp / 'overview.png'
    png.unlink(missing_ok=True)
    prof = tmp / ('p-' + uuid.uuid4().hex[:8])
    kw = {'creationflags': subprocess.CREATE_NO_WINDOW} if hasattr(subprocess, 'CREATE_NO_WINDOW') else {}
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                    '--force-device-scale-factor=2', f'--window-size={W},{H}',
                    f'--user-data-dir={prof}', f'--screenshot={png}', hp.as_uri()],
                   capture_output=True, timeout=120, **kw)
    deadline = time.monotonic() + 30
    while not png.exists() or png.stat().st_size < 2000:
        if time.monotonic() > deadline:
            raise RuntimeError('png 未生成')
        time.sleep(0.2)
    dest = OUT / '系统总体结构_单色学术版.png'
    try:
        from PIL import Image
        import numpy as np
        im = Image.open(png).convert('RGB')
        a = np.array(im.convert('L'))
        rows = np.where((a < 250).any(axis=1))[0]
        cols = np.where((a < 250).any(axis=0))[0]
        pad = 16
        im = im.crop((max(0, cols[0] - pad), max(0, rows[0] - pad),
                      min(im.width, cols[-1] + pad), min(im.height, rows[-1] + pad)))
        im.save(dest)
    except ImportError:
        dest.write_bytes(png.read_bytes())
    print(f'written: {OUT / "系统总体结构_单色学术版.svg"} 与 .png（1000×{H}，最小字号 24px；'
          f'文档放置宽度 400 pt ⇒ 最小字号 9.6 pt，高 23.4 cm）')


render_png()
