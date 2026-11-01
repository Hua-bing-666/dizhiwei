# -*- coding: utf-8 -*-
"""申报书两张升级版示意图（v2，最小字号 23px，A4 420pt 放置 ≥9.5pt 达标）：
A. tech_roadmap_staircase  技术路线阶梯递进图（六层逐级上升 + 实验数据回补框）
B. diagnosis_closed_loop   诊断业务闭环图（主链四节点 + 参照更新回环）"""
from pathlib import Path
import subprocess, time, uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures'
TMP = ROOT / 'tmp/upgrade_figs'
TMP.mkdir(parents=True, exist_ok=True)
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

FONT = 'Microsoft YaHei, SimSun, sans-serif'
INK = '#3c3c3a'      # 主文字（真灰）
MUTE = '#7a7a78'     # 次文字（真灰，差2，判灰排除出palette）
STROKE = '#5f5e5a'   # 统一框线（真灰）
BLUE6 = '#185FA5'    # 序号圆（彩色1）
AMBER4 = '#BA7517'   # 回环（彩色2，与彩色1灰度差大）
BLUE50 = '#E6F1FB'; TEAL50 = '#E1F5EE'; AMBER50 = '#FAEEDA'

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
        '<path d="M2 1 L8 4.5 L2 8" fill="none" stroke="#5f5e5a" stroke-width="1.6" stroke-linecap="round"/></marker>'
        '<marker id="aram" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto-start-reverse">'
        '<path d="M2 1 L8 4.5 L2 8" fill="none" stroke="#BA7517" stroke-width="1.6" stroke-linecap="round"/></marker></defs>')

# ════ 图 A：技术路线阶梯递进（v2） ════
W, H = 1000, 640
p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}<rect width="{W}" height="{H}" fill="white"/>',
     f'<g font-family="{FONT}" fill="{INK}">']

layers = [
    ('1', '场景锚定', '2026.10-2027.2', '监测对象=支管；两类故障等效注入', BLUE50),
    ('2', '测量链构建', '2027.3-4', 'U≤0.20 kPa 实测；水路装配', TEAL50),
    ('3', '建模与标定', '2027.4-5', '健康参照；固定 n=0.5；残差尺度', BLUE50),
    ('4', '判据与验证', '2027.5-6', '54-72 次注入；门限重标冻结', TEAL50),
    ('5', '通信与集成', '2027.7-8', 'LoRa 闭环；先落库后 ACK', BLUE50),
    ('6', '成果固化', '2027.9-2028.2', '留出验证；论文、软著、结项', AMBER50),
]
sw, sh, dy, dx = 660, 64, 92, 26
x0, y0 = 40, 545
for i, (num, name, period, output, fill) in enumerate(layers):
    x = x0 + i*dx; y = y0 - i*dy
    p.append(f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" rx="12" fill="{fill}" stroke="{STROKE}" stroke-width="1"/>')
    cx, cy = x+30, y+sh/2
    p.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="{BLUE6}"/>')
    p.append(f'<text x="{cx}" y="{cy+1}" font-size="23" font-weight="700" fill="white" text-anchor="middle" dominant-baseline="central">{num}</text>')
    p.append(f'<text x="{x+58}" y="{y+25}" font-size="24" font-weight="700">{name}</text>')
    p.append(f'<text x="{x+58}" y="{y+56}" font-size="23" fill="{MUTE}">{period}</text>')
    p.append(f'<text x="{x+250}" y="{cy}" font-size="23" dominant-baseline="central">{output}</text>')
    if i < 5:
        nx, ny = x0+(i+1)*dx, y0-(i+1)*dy
        p.append(f'<path d="M {x+130} {y-3} L {nx+170} {ny+sh+3}" fill="none" stroke="{STROKE}" stroke-width="1.8" marker-end="url(#ar)"/>')

# 回补弧：判据与验证层 → 弧线 → 测量链构建层
p.append(f'<path d="M 836 250 C 985 300, 985 420, 736 492" fill="none" stroke="{AMBER4}" stroke-width="2.4" stroke-dasharray="10 7" marker-end="url(#aram)"/>')
p.append(f'<text x="898" y="352" font-size="23" font-weight="700" fill="{AMBER4}" text-anchor="middle">实验数据回补</text>')
p.append(f'<text x="898" y="382" font-size="23" fill="{AMBER4}" text-anchor="middle">σ、τ、漂移、n</text>')
p.append('</g></svg>')
render('tech_roadmap_staircase', ''.join(p), W, H)

# ════ 图 B：诊断业务闭环（v2） ════
W2, H2 = 1000, 452
q = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}">{DEFS}<rect width="{W2}" height="{H2}" fill="white"/>',
     f'<g font-family="{FONT}" fill="{INK}">']

nodes = [
    (35,  '感知采样', '三通道 1 s 采集', BLUE50),
    (275, '块判据',   '10 s 块 CUSUM', TEAL50),
    (515, '事件落库', '先落库后 ACK', BLUE50),
    (755, '人工处置', '查看/处置/复测', TEAL50),
]
nw, nh = 210, 96
for i, (x, title, sub, fill) in enumerate(nodes):
    q.append(f'<rect x="{x}" y="110" width="{nw}" height="{nh}" rx="12" fill="{fill}" stroke="{STROKE}" stroke-width="1"/>')
    q.append(f'<text x="{x+nw/2}" y="146" font-size="24" font-weight="700" text-anchor="middle">{title}</text>')
    q.append(f'<text x="{x+nw/2}" y="182" font-size="23" fill="{MUTE}" text-anchor="middle">{sub}</text>')
    if i < 3:
        q.append(f'<path d="M {x+nw+4} 158 L {x+nw+26} 158" fill="none" stroke="{STROKE}" stroke-width="1.8" marker-end="url(#ar)"/>')

# 误报来源注
q.append(f'<text x="290" y="248" font-size="23" fill="{MUTE}">误报来源：供压扰动 / 邻支路切换 / 切换期故障</text>')

# 回环：处置 → 健康参照更新 → 感知
q.append(f'<path d="M 860 214 C 880 336, 700 400, 528 400" fill="none" stroke="{AMBER4}" stroke-width="2.4" stroke-dasharray="9 6"/>')
q.append(f'<rect x="300" y="352" width="228" height="76" rx="12" fill="{AMBER50}" stroke="{AMBER4}" stroke-width="1.6"/>')
q.append(f'<text x="414" y="384" font-size="24" font-weight="700" text-anchor="middle" fill="#63490b">健康参照更新</text>')
q.append(f'<text x="414" y="414" font-size="23" text-anchor="middle" fill="{MUTE}">按供压档分档</text>')
q.append(f'<path d="M 298 392 C 170 386, 90 306, 100 218" fill="none" stroke="{AMBER4}" stroke-width="2.4" stroke-dasharray="9 6" marker-end="url(#aram)"/>')
q.append('</g></svg>')
render('diagnosis_closed_loop', ''.join(q), W2, H2)
