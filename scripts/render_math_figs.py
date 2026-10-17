# -*- coding: utf-8 -*-
"""CSS 公式渲染器：用 HTML/CSS 排版数学公式（分式、根号覆盖线、上下标），Edge 截图为 PNG。
公式以白底卡片渲染，可嵌入 SVG（<image>）与 docx。"""
from pathlib import Path
import subprocess, time, uuid

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / 'tmp/math_figs'
OUT = ROOT / 'application/figures/math'
TMP.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

BASE_CSS = """
<body style="margin:0;background:white;">
<div class="eq" style="font-family:'Cambria Math','Times New Roman',serif;font-size:34px;color:#1a1a1a;display:inline-block;padding:14px 22px;">
%(body)s
</div>
</body>
"""
STYLE = """<style>
.frac{display:inline-flex;flex-direction:column;align-items:center;vertical-align:middle;margin:0 6px;}
.frac .num{padding:0 8px 3px;}
.frac .den{border-top:1.8px solid #1a1a1a;padding:3px 8px 0;}
.sqrt{display:inline-flex;align-items:flex-start;vertical-align:middle;margin:0 4px;}
.sqrt .rad{font-size:1.25em;line-height:1;transform:translateY(2px);}
.sqrt .inner{border-top:1.8px solid #1a1a1a;padding:4px 6px 0 2px;}
sup,sub{font-size:0.62em;}
.op{margin:0 7px;}
</style>"""

EQS = {
 'eq_hydraulic': 'Q = C·P<sub>1</sub><sup>n</sup><span class="op">，</span>ΔP = R·Q<sup>2</sup>',
 'eq_K': 'K = <span class="frac"><span class="num">Q</span><span class="den"><span class="sqrt"><span class="rad">√</span><span class="inner">P<sub>1</sub></span></span></span></span>',
 'eq_Rh': 'R<sub>h</sub> = <span class="frac"><span class="num">ΔP</span><span class="den">Q<sup>2</sup></span></span>',
 'eq_block': 'x̄<sub>m</sub> = <span class="frac"><span class="num">1</span><span class="den">10</span></span> Σ x(t)',
 'eq_cusum': 'S<sub>m</sub> = max(0, S<sub>m−1</sub> + z<sub>m</sub> − k)，S<sub>m</sub> &gt; h ⇒ 事件',
 'eq_direction': '泄漏 ⇒ K↑（Rh 不变）<span class="op" style="color:#888;">｜</span>受限 ⇒ R<sub>h</sub>↑（K 不变）',
}

def render_eq(name, body):
    html = f'<html><meta charset="utf-8">{STYLE}{BASE_CSS % {"body": body}}</html>'
    fp = TMP/(name+'.html'); fp.write_text(html, encoding='utf-8')
    dest = OUT/(name+'.png'); dest.unlink(missing_ok=True)
    profile = TMP/('edge-'+uuid.uuid4().hex[:12])
    subprocess.run([EDGE,'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars',
                    '--force-device-scale-factor=3','--window-size=1400,140',
                    '--screenshot='+str(dest.resolve()), fp.resolve().as_uri()],
                   capture_output=True, check=True, timeout=40, creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic()+25
    while not dest.exists() or dest.stat().st_size < 500:
        if time.monotonic() > deadline: raise RuntimeError(name)
        time.sleep(.15)
    print(name, dest.stat().st_size)

for n, b in EQS.items():
    render_eq(n, b)
print('all formulas rendered')
