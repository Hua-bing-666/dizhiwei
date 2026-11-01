# -*- coding: utf-8 -*-
"""协议与判据两张"小而具体"图（最小字号 23px）：
A. frame_layout      事件/遥测/ACK 帧字节结构条带（真实字段：16B 头 + 35B 快照 + CRC/COBS）
B. judging_chain     10 s 块判据处理链（1s 行 → 块平均 → 特征 → CUSUM → 判决）"""
from pathlib import Path
import subprocess, time, uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures'
TMP = ROOT / 'tmp/upgrade_figs'
TMP.mkdir(parents=True, exist_ok=True)
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

FONT = 'Microsoft YaHei, SimSun, sans-serif'
INK = '#3c3c3a'; MUTE = '#7a7a78'; STROKE = '#5f5e5a'
BLUE6 = '#185FA5'; AMBER4 = '#BA7517'
BLUE50 = '#E6F1FB'; TEAL50 = '#E1F5EE'; AMBER50 = '#FAEEDA'; GRAY50 = '#F1EFE8'

def render(name, svg, w, h):
    fp = OUT/(name+'.svg'); fp.write_text(svg, encoding='utf-8', newline='\n')
    html = TMP/(name+'.html')
    html.write_text(f'<html><meta charset="utf-8"><style>html,body{{margin:0;width:{w}px}}svg{{display:block}}</style>'+svg+'</html>', encoding='utf-8')
    dest = OUT/(name+'.png'); dest.unlink(missing_ok=True)
    profile = TMP/('edge-'+uuid.uuid4().hex[:12])
    subprocess.run([EDGE,'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars',
                    '--force-device-scale-factor=2', f'--window-size={w},{h}',
                    '--screenshot='+str(dest.resolve()), html.resolve().as_uri()],
                   capture_output=True, check=True, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic()+30
    while not dest.exists() or dest.stat().st_size < 1000:
        if time.monotonic() > deadline: raise RuntimeError('png not produced: '+name)
        time.sleep(.2)
    print(name, 'rendered', dest.stat().st_size)

DEFS = ('<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto-start-reverse">'
        '<path d="M2 1 L8 4.5 L2 8" fill="none" stroke="#5f5e5a" stroke-width="1.6" stroke-linecap="round"/></marker></defs>')

# ════ A. 帧结构条带 ════
W, H = 1000, 500
p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}<rect width="{W}" height="{H}" fill="white"/>',
     f'<g font-family="{FONT}" fill="{INK}">']

# 条带区：x 220..960（740px 表示整帧）；字节→px 比例按各帧自身总长等比
rows = [
    ('遥测帧 55 B', 190, [('公共头', 16, BLUE50), ('测量快照', 35, TEAL50), ('CRC16/COBS', 4, GRAY50)]),
    ('事件帧 57 B', 285, [('公共头', 16, BLUE50), ('测量快照', 35, TEAL50), ('事件+细节', 2, AMBER50), ('CRC16/COBS', 4, GRAY50)]),
    ('ACK 24 B',   380, [('公共头', 16, BLUE50), ('CRC32 指纹', 4, AMBER50), ('CRC16/COBS', 4, GRAY50)]),
]
X0, XW = 230, 730
for label, y, segs in rows:
    total = sum(sg[1] for sg in segs)
    p.append(f'<text x="40" y="{y+36}" font-size="24" font-weight="700">{label}</text>')
    x = X0
    for name, nb, fill in segs:
        w = XW * nb / total
        p.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="64" rx="6" fill="{fill}" stroke="{STROKE}" stroke-width="1"/>')
        p.append(f'<text x="{x+w/2:.1f}" y="{y+36}" font-size="23" font-weight="700" text-anchor="middle" dominant-baseline="central">{nb} B</text>')
        x += w
p.append(f'<text x="40" y="120" font-size="24" font-weight="700">公共头 16 B：版本 1 / 类型 1 / 载荷长度 2 / 设备号 4 / 会话号 4 / 消息序号 4</text>')
p.append(f'<text x="230" y="470" font-size="23" font-weight="700">图例：</text>')
p.append(f'<rect x="310" y="448" width="30" height="26" rx="4" fill="{BLUE50}" stroke="{STROKE}" stroke-width="1"/>')
p.append(f'<text x="348" y="470" font-size="23">公共头</text>')
p.append(f'<rect x="440" y="448" width="30" height="26" rx="4" fill="{TEAL50}" stroke="{STROKE}" stroke-width="1"/>')
p.append(f'<text x="478" y="470" font-size="23">测量快照</text>')
p.append(f'<rect x="590" y="448" width="30" height="26" rx="4" fill="{AMBER50}" stroke="{STROKE}" stroke-width="1"/>')
p.append(f'<text x="628" y="470" font-size="23">事件码 / 指纹</text>')
p.append(f'<rect x="800" y="448" width="30" height="26" rx="4" fill="{GRAY50}" stroke="{STROKE}" stroke-width="1"/>')
p.append(f'<text x="838" y="470" font-size="23">CRC16/COBS</text>')
p.append('</g></svg>')
render('frame_layout', ''.join(p), W, H)

# ════ B. 10 s 块判据处理链 ════
W2, H2 = 1000, 300
q = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}">{DEFS}<rect width="{W2}" height="{H2}" fill="white"/>',
     f'<g font-family="{FONT}" fill="{INK}">']
chain = [
    ('采样提交', '三通道 1 s 行', BLUE50, '1 Hz 节拍'),
    ('块平均',   '块均值序列',   TEAL50, '块长 W=10 s'),
    ('特征构造', 'K 与 Rh',      BLUE50, 'n=0.5'),
    ('CUSUM 累积', '累积量 Sₘ',  TEAL50, 'k=0.5'),
    ('门限判决', '候选事件',     AMBER50, 'h*=26（仿真）'),
]
nw, gap = 166, 20
x0 = 40 + (1000 - 80 - 5*nw - 4*gap)//2
for i, (t, sub, fill, param) in enumerate(chain):
    x = x0 + i*(nw+gap)
    q.append(f'<rect x="{x}" y="80" width="{nw}" height="100" rx="12" fill="{fill}" stroke="{STROKE}" stroke-width="1"/>')
    q.append(f'<text x="{x+nw/2}" y="118" font-size="24" font-weight="700" text-anchor="middle">{t}</text>')
    q.append(f'<text x="{x+nw/2}" y="154" font-size="23" fill="{MUTE}" text-anchor="middle">{sub}</text>')
    q.append(f'<text x="{x+nw/2}" y="222" font-size="23" text-anchor="middle" fill="{AMBER4 if i==4 else MUTE}">{param}</text>')
    if i < 4:
        q.append(f'<path d="M {x+nw+2} 130 L {x+nw+gap-2} 130" fill="none" stroke="{STROKE}" stroke-width="1.8" marker-end="url(#ar)"/>')
q.append('</g></svg>')
render('judging_chain', ''.join(q), W2, H2)
