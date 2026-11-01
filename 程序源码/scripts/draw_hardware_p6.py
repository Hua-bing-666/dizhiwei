"""P6 可视化整改 · 硬件候选拼版（摒弃旧劣质拼版，重做真实实物图+原理图）。

用户指令：抓取真实实物图/原理图，摒弃之前的，高标准验收。
做法：用 application/figures/vendor_hardware 下已核实厂商真实图（立创/亿佰特/DFRobot/麦克
      官方与商城公开资料），以 base64 嵌入 SVG，Edge 渲染 PNG。每器件 = 真实照片 + 关键指标
      + 国内现价 + 货源；底部单列典型原理/连接图（原理图）。

口径真源：docs/硬件软件匹配度审查_v2.2.md（器件冻结）
输出：application/figures/hardware_candidates.{svg,png}
      application/figures/hardware_feasibility.{svg,png}
"""
import base64, subprocess, sys, time, uuid
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application' / 'figures'
VH = ROOT / 'application' / 'figures' / 'vendor_hardware'
EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'

INK = '#142a30'; GRAY = '#52636a'; WHITE = '#ffffff'; FILL = '#eef5f2'
FILL2 = '#eaf1f7'; ACC = '#b8543f'; LINE = '#9fb3ab'

def b64(p):
    mime = 'image/png' if p.suffix.lower() == '.png' else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode()

def tw(s, fs):
    return sum(fs if ord(c) > 0x2000 and c != '·' else fs * 0.56 for c in s)

def render_png(name, w, h):
    svg = (OUT / (name + '.svg')).read_text(encoding='utf-8')
    html = ('<!doctype html><meta charset="utf-8">'
            '<style>html,body{margin:0;background:white}svg{display:block}</style>' + svg)
    tmp = ROOT / 'tmp' / 'p6_hw'
    tmp.mkdir(parents=True, exist_ok=True)
    hp = tmp / (name + '.html'); hp.write_text(html, encoding='utf-8')
    png = tmp / (name + '.png'); png.unlink(missing_ok=True)
    prof = tmp / ('p-' + uuid.uuid4().hex[:8])
    kw = {'creationflags': subprocess.CREATE_NO_WINDOW} if hasattr(subprocess, 'CREATE_NO_WINDOW') else {}
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                    '--force-device-scale-factor=2', f'--window-size={w},{h}',
                    f'--user-data-dir={prof}', f'--screenshot={png}', hp.as_uri()],
                   capture_output=True, timeout=180, **kw)
    deadline = time.monotonic() + 60
    while not png.exists() or png.stat().st_size < 2000:
        if time.monotonic() > deadline:
            raise RuntimeError(f'{name}: png 未生成')
        time.sleep(0.25)
    dest = OUT / (name + '.png')
    try:
        from PIL import Image
        im = Image.open(png).convert('RGB')
        px = im.load(); W, H = im.size
        def white_row(y): return all(px[x, y] == (255, 255, 255) for x in range(0, W, 7))
        def white_col(x): return all(px[x, y] == (255, 255, 255) for y in range(0, H, 7))
        top = next((y for y in range(H) if not white_row(y)), 0)
        bot = next((y for y in range(H - 1, -1, -1) if not white_row(y)), H)
        left = next((x for x in range(W) if not white_col(x)), 0)
        right = next((x for x in range(W - 1, -1, -1) if not white_col(x)), W)
        pad = 10
        im = im.crop((max(0, left - pad), max(0, top - pad), min(W, right + pad), min(H, bot + pad)))
        im.save(dest)
    except ImportError:
        dest.write_bytes(png.read_bytes())
    print(f'written: {name} ({dest.stat().st_size} bytes)')

# ───────── 器件数据（口径 v2.2 冻结 + 2026-10 现价复核） ─────────
PHOTO = {
 'GD32': VH/'GD32F103CBT6'/'GD32F103CBT6_实物_LQFP48_立创商城.jpg',
 'MDM':  VH/'MDM490'/'MDM490_差压变送器实物_麦克官方资料.png',
 'SEN':  VH/'SEN0549'/'SEN0549_流量计实物_DFRobot官网.jpg',
 'E220': VH/'E220-400T22D'/'E220-400T22D_实物_亿佰特官网.jpg',
 'SGM':  VH/'SGM58031'/'SGM58031_实物_MSOP10_立创商城.jpg',
 'XL4015': VH/'XL4015'/'XL4015_实物_TO263-5L_立创商城.jpg',
 'MP2359': VH/'MP2359'/'MP2359_实物_TSOT23-6_立创商城.jpg',
 'XL6009': VH/'XL6009'/'XL6009_引脚图_TO263-5L.png',
}
SCH = {
 'GD32': VH/'GD32F103CBT6'/'GD32F103CBT6_典型外围电路_官方推荐.png',
 'MDM':  VH/'MDM490'/'MDM490_电气连接定义_官方.png',
 'E220': VH/'E220-400T22D'/'E220-400T22D_与MCU连接示意.png',
 'SEN':  VH/'SEN0549'/'SEN0549_接口电路_5V转3.3V分压.png',
}

CARDS = [
 ('GD32', 'GD32F103CBT6', '主控 MCU（首选）',
  ['ARM Cortex-M3 · 108 MHz · 128 KB Flash', 'LQFP-48 · 双 12-bit ADC · 37 I/O',
   '国产兆易创新 · 立创现货充足', '备选：CKS32F103CBT6 Pin 兼容'],
  '≈ ¥5.3', '立创商城（1+, 2026）'),
 ('MDM', 'MDM490 差压变送器', '双压力 P0 / P1 感知',
  ['量程 0—40 kPa（订货号 K040）', '精度 ±0.5 %FS → U ≤ 0.20 kPa',
   '两线 4—20 mA · G1/4 · 国产麦克', '标准最小档 0A=0~35 kPa 同平台'],
  '¥100—700', '麦克传感（按量程/输出）'),
 ('SEN', 'SEN0549 电磁流量计', '流量 Q 感知（最上游）',
  ['G1/4 · 3.5—24 V · NPN 脉冲', '540 脉冲/L · ±1%（0.3—5 L/min）',
   '电磁式 · 抗干扰 · 长寿命', '本链路最贵单项'],
  '≈ ¥240', 'DFRobot（≈ $34.75）'),
 ('E220', 'E220-400T22D', 'LoRa 无线回传',
  ['LLCC68(SX1262) · 22 dBm · 5 km', '410—493 MHz · UART 接口',
   '功率设 ≤10 dBm 合规', '国产亿佰特 · 嘉立创现货'],
  '≈ ¥27.5', '嘉立创（10+ ¥26.8）'),
 ('SGM', 'SGM58031（可选）', '16-bit ADC 备份通道',
  ['ΣΔ 16-bit · I²C · MSOP-10', '内置基准 · 4 单端/2 差分',
   'MCU 内置 12-bit 已可主用', '此件为精度冗余，可选'],
  '¥18—26', '立创/世强'),
 ('XL4015', 'XL4015', '电源 · 降压 5 V/5 A',
  ['8—36 V → 5 V · 连续负载', '为 MCU/传感器供电',
   '国产 · 廉价 · 易购', '立创/淘宝现货'],
  '¥2—4', '立创/淘宝'),
 ('MP2359', 'MP2359', '电源 · 降压 3.3 V',
  ['5 V → 3.3 V · TSOT23-6', '为 MCU 核与逻辑供电', '国产 MPS · 小封装', '立创/淘宝现货'],
  '¥1—3', '立创/淘宝'),
 ('XL6009', 'XL6009', '电源 · 升压 24 V（高边）',
  ['升压供两线制变送器', '必须高边开关（控 EN）', '仅变送器用电，独立回路', '立创/淘宝现货'],
  '¥2—4', '立创/淘宝'),
]

def build_candidates():
    W, H = 1440, 1980
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    s.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    s.append(f'<rect x="0" y="0" width="{W}" height="116" fill="{FILL}"/>')
    s.append(f'<text x="28" y="56" font-size="40" font-weight="700" fill="{INK}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">国内候选硬件与量程核对</text>')
    s.append(f'<text x="28" y="92" font-size="23" fill="{GRAY}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">均为国内可购现货；价格来自立创/世强/DFRobot/麦克公开报价（2026-10），随市场浮动 · 非项目样机</text>')
    CW, CH = 700, 300
    gx = [24, 740]; gy = [140, 460, 780, 1100]
    for i, (key, name, role, specs, price, src) in enumerate(CARDS):
        col, row = i % 2, i // 2
        x, y = gx[col], gy[row]
        s.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="6" fill="{WHITE}" '
                 f'stroke="{LINE}" stroke-width="2"/>')
        # 照片
        s.append(f'<rect x="{x+18}" y="{y+18}" width="262" height="262" fill="{FILL2}" stroke="{LINE}" stroke-width="1"/>')
        s.append(f'<image x="{x+24}" y="{y+24}" width="250" height="250" '
                 f'preserveAspectRatio="xMidYMid meet" href="{b64(PHOTO[key])}"/>')
        # 文字块
        tx = x + 300
        s.append(f'<text x="{tx}" y="{y+50}" font-size="29" font-weight="700" fill="{INK}" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(name)}</text>')
        s.append(f'<text x="{tx}" y="{y+82}" font-size="22" fill="{ACC}" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(role)}</text>')
        for j, ln in enumerate(specs):
            s.append(f'<text x="{tx}" y="{y+118+j*27}" font-size="19" fill="{GRAY}" '
                     f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(ln)}</text>')
        s.append(f'<text x="{tx}" y="{y+258}" font-size="26" font-weight="700" fill="{INK}" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(price)}</text>')
        s.append(f'<text x="{x+CW-18}" y="{y+258}" font-size="18" fill="{GRAY}" text-anchor="end" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(src)}</text>')
    # 原理图条
    sty = 1480
    s.append(f'<text x="28" y="{sty}" font-size="30" font-weight="700" fill="{INK}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">典型应用 / 连接原理（原理图）</text>')
    s.append(f'<text x="28" y="{sty+30}" font-size="20" fill="{GRAY}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">实物图之上补充官方典型电路，便于评审核对接线与选型的工程可行性</text>')
    sx = [24, 380, 736, 1092]; sw, sh = 324, 300
    scy = sty + 50
    sc_cap = [('GD32', 'GD32 最小系统（官方推荐）'), ('MDM', 'MDM490 电气连接定义'),
              ('E220', 'E220-400T22D 与 MCU 连接'), ('SEN', 'SEN0549 接口（5V→3.3V 分压）')]
    for k, (key, cap) in enumerate(sc_cap):
        x = sx[k]
        s.append(f'<rect x="{x}" y="{scy}" width="{sw}" height="{sh}" fill="{WHITE}" stroke="{LINE}" stroke-width="2"/>')
        s.append(f'<image x="{x+10}" y="{scy+10}" width="{sw-20}" height="{sh-44}" '
                 f'preserveAspectRatio="xMidYMid meet" href="{b64(SCH[key])}"/>')
        s.append(f'<text x="{x+sw/2}" y="{scy+sh-12}" font-size="17" fill="{GRAY}" text-anchor="middle" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(cap)}</text>')
    fy = scy + sh + 40
    s.append(f'<text x="28" y="{fy}" font-size="19" fill="{GRAY}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">核心传感链（MCU＋变送器＋流量计＋LoRa）≈ ¥370；加电源 ≈ ¥380；ADC 可选 +¥20。整机 BOM v2.2 估算 2409—5018 元（含 PCB/天线/结构等）。</text>')
    s.append('</svg>\n')
    (OUT / 'hardware_candidates.svg').write_text(''.join(s), encoding='utf-8', newline='\n')
    render_png('hardware_candidates', W, H)
    print('hardware_candidates done')

def build_feasibility():
    W, H = 1440, 1000
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    s.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    s.append(f'<text x="28" y="52" font-size="38" font-weight="700" fill="{INK}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">硬件量程与不确定度核对（24 组未标定设计计算）</text>')
    s.append(f'<text x="28" y="88" font-size="21" fill="{GRAY}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">口径唯一真源 v2.2：0—40 kPa 档 / ±0.5%FS（K040）· 设计工况 U ≤ 0.20 kPa（较 +2% 边界余量 10×）</text>')
    # 表头（列宽合计 1400，字号 18，右列留足）
    cols = [('传感器 / 通道', 28, 400), ('量程', 440, 170), ('设计工况跨度', 624, 250),
            ('不确定度 U', 888, 260), ('是否满足', 1162, 260)]
    ty = 150
    s.append(f'<rect x="20" y="{ty-34}" width="{W-40}" height="44" fill="{FILL}"/>')
    for name, x, w in cols:
        s.append(f'<text x="{x+12}" y="{ty-4}" font-size="21" font-weight="700" fill="{INK}" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(name)}</text>')
    rows = [
     ('差压 ΔP = P1−P0', '0—40 kPa', '≈ 2—8 kPa', '≤ 0.20 kPa', '满足（±0.5%FS）'),
     ('P1 取压嘴B', '0—40 kPa', '≈ 20—35 kPa', '≤ 0.20 kPa', '满足'),
     ('P0 取压嘴A（干管参照）', '0—40 kPa', '≈ 20—35 kPa', '≤ 0.20 kPa', '满足'),
     ('Q 流量计', '0.3—5 L/min', '≈ 0.5—3 L/min', '±1% ≈ 0.03 L/min', '满足（540 脉冲/L）'),
     ('K = Q/√P1 通道', '派生量', '跨度 ≥20% 拟合 n', '增益漂移 ≤0.10%', '满足（n 默认 0.5）'),
    ]
    ry = ty + 14
    for r in rows:
        s.append(f'<rect x="20" y="{ry}" width="{W-40}" height="56" fill="{WHITE}" stroke="{LINE}" stroke-width="1"/>')
        for (name, x, w), val in zip(cols, r):
            size = 19
            if tw(val, size) > w - 16:
                raise SystemExit(f'[hardware_feasibility] 单元格超宽: {val!r} 估宽 {tw(val,size):.0f} > {w-16}')
            s.append(f'<text x="{x+12}" y="{ry+34}" font-size="{size}" fill="{INK if name!="是否满足" else GRAY}" '
                     f'font-family="Microsoft YaHei,SimSun,sans-serif">{escape(val)}</text>')
        ry += 56
    # 24 组范围核对结论
    cy = ry + 36
    s.append(f'<text x="28" y="{cy}" font-size="28" font-weight="700" fill="{INK}" '
             f'font-family="Microsoft YaHei,SimSun,sans-serif">台架范围核对结论（24 组：多供压 × 多流量组合）</text>')
    concl = [
     '等效泄漏：+2% 边界需 80 s 注入窗（40/40 检出）；+5% 需 20 s；+10% 需 10 s。',
     '等效受限：+50% 才 40/40（80 s）；+30% 仅 32/40 ⇒ 申报口径取 +50%（80 s）或 +30% 需 ≥5 min。',
     '时间常数 τ：≤5 s 无影响；τ=120 s 门限需 14.5× ⇒ 台架必测 τ，τ≤10 s 才可直接用 10 s 块判据。',
     '慢漂移：K 通道容限 ≈1%/h（自适应基线可翻倍）；为全项目最紧约束，须台架静置 ≥8 h 实测。',
     '原理性边界：下游负载自身变化与等效泄漏在 (P0,P1,Q) 下严格不可区分 ⇒ 仅输出“异常·建议核查”。',
    ]
    for j, ln in enumerate(concl):
        s.append(f'<text x="28" y="{cy+44+j*36}" font-size="20" fill="{GRAY}" '
                 f'font-family="Microsoft YaHei,SimSun,sans-serif">• {escape(ln)}</text>')
    s.append('</svg>\n')
    (OUT / 'hardware_feasibility.svg').write_text(''.join(s), encoding='utf-8', newline='\n')
    render_png('hardware_feasibility', W, H)
    print('hardware_feasibility done')

if __name__ == '__main__':
    build_candidates()
    build_feasibility()
