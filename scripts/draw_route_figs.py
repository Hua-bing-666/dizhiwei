# -*- coding: utf-8 -*-
"""
技术路线配套图（HTML/CSS 排版 + 无头浏览器渲染）—— 3D 立体框 · 黑白打印版

视觉规范（借鉴"分步(1).docx"图集并做黑白化改造）：
  · 3D 立体框：正面白/浅灰 + 右下深灰侧面 + 深描边；
  · 每框两层文字：粗体主词 + 小字关键词注解（"/"分隔）；
  · 灰度体系替代彩色：正面 #f7f7f7、侧面 #c4c4c4、强调纯黑；
  · 已完成阶段用 45° 斜纹填充（黑白打印可辨）；
  · 门控/编号用黑底白字小标签；
  · 底部灰色小字注释行。
"""
import subprocess, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures'
TMP = ROOT / 'tmp/htmlfig'
TMP.mkdir(parents=True, exist_ok=True)
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

# ── 灰度设计令牌 ────────────────────────────────────────────
INK = '#1a1a1a'      # 主文字（近黑）
MUTE = '#565656'     # 次级文字（深灰）
FAINT = '#8a8a8a'    # 注释文字（中灰）
LINE = '#bfbfbf'     # 细线
EDGE_C = '#2b2b2b'   # 立体框描边（深灰）
FACE = '#f7f7f7'     # 立体框正面
FACE2 = '#ededed'    # 次级正面
SIDE = '#c4c4c4'     # 立体框侧面
SIDE2 = '#a6a6a6'    # 深侧面
BLACK = '#1a1a1a'    # 强调标签底色


def S(t):
    """{{TOKEN}} 替换，避开 CSS 百分号与 Python 格式化冲突。"""
    for k, v in dict(ink=INK, mute=MUTE, faint=FAINT, line=LINE,
                     edge=EDGE_C, face=FACE, face2=FACE2,
                     side=SIDE, side2=SIDE2, black=BLACK).items():
        t = t.replace('{{' + k + '}}', v)
    return t


BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: {{w}}px; background: #ffffff; }
body {
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
  color: {{ink}}; font-size: 17px; line-height: 1.5;
  padding: 26px 30px 22px;
}
.note { font-size: 24px; color: {{faint}}; border-left: 5px solid {{edge}};
        padding: 4px 0 4px 13px; margin-top: 10px; background: #fafafa; }
.note b { color: {{ink}}; font-weight: 600; }

/* ── 3D 立体框（右下 extrude） ─────────────────────── */
.b3 { position: relative; margin: 0 13px 13px 0; }
.b3 .e {
  position: absolute; top: 0; right: -11px; width: 11px; height: 100%;
  background: {{side}}; border: 1.5px solid {{edge}};
  transform: skewY(45deg); transform-origin: 0 0; z-index: 1;
}
.b3 .f {
  position: relative; z-index: 2; background: {{face}};
  border: 1.5px solid {{edge}};
}
.b3.solid .f { background: #ffffff; }

/* 黑底白字小标签 */
.tag-k {
  display: inline-block; background: {{black}}; color: #fff;
  font-size: 26px; font-weight: 600; padding: 2px 10px; margin-right: 9px;
  vertical-align: 2px;
}

/* 竖直箭头 */
.varr { width: 2.5px; height: 14px; background: {{edge}}; position: relative; }
.varr::before {
  content: ""; position: absolute; top: -4px; left: -2.5px;
  width: 7.5px; height: 7.5px; background: {{edge}};
}
.varr::after {
  content: ""; position: absolute; bottom: -8px; left: -4.2px;
  border-left: 5.5px solid transparent; border-right: 5.5px solid transparent;
  border-top: 8px solid {{edge}};
}
/* ── 科技感：HUD 内角标 + 编号牌外侧偏移描边 ───────────── */
.b3 .f::before, .b3 .f::after {
  content: ""; position: absolute; width: 14px; height: 14px; z-index: 3;
}
.b3 .f::before { left: 4px; top: 4px; border-left: 2.5px solid {{edge}}; border-top: 2.5px solid {{edge}}; }
.b3 .f::after  { right: 4px; bottom: 4px; border-right: 2.5px solid {{edge}}; border-bottom: 2.5px solid {{edge}}; }
.b3 .f { padding-left: 18px; padding-right: 18px; }
/* 编号牌：黑底白字 + 外侧细线偏移框 */
.tag-k { box-shadow: 3px 3px 0 0 rgba(43,43,43,.28); }
.snum { letter-spacing: -2px; }
"""


def render(name, body, w=1060, scale=3):
    """把 HTML body 渲染为 PNG（自动高度 + 裁白边）。"""
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<style>{S(BASE_CSS).replace('{{w}}', str(w))}
{body.get('css','')}
</style></head><body>{body['html']}</body></html>"""
    hp = TMP / f'{name}.html'
    hp.write_text(html, encoding='utf-8')
    png = TMP / f'{name}.png'
    png.unlink(missing_ok=True)
    prof = TMP / ('p-' + uuid.uuid4().hex[:10])
    subprocess.run(
        [EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
         f'--force-device-scale-factor={scale}', f'--window-size={w},2600',
         f'--user-data-dir={prof}', f'--screenshot={png}', hp.as_uri()],
        capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic() + 20
    while not png.exists() or png.stat().st_size < 2000:
        if time.monotonic() > deadline:
            raise RuntimeError(f'{name}: png 未生成')
        time.sleep(0.2)
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
        dest = OUT / f'{name}.png'
        im.save(dest)
        return dest, im.size
    except ImportError:
        dest = OUT / f'{name}.png'
        dest.write_bytes(png.read_bytes())
        return dest, (0, 0)


# ═══════════════════════════════════════════════════════════
# 图 1  技术路线主线：风险收敛链（大编号 + 3D 立体框）
# ═══════════════════════════════════════════════════════════
STAGES = [
    ('M0', '数字样机（起点）', '2026.10—2027.2', True,
     None,
     [('建模与数值仿真', '三通道合成轨迹 + 注入口径修正'),
      ('判据结构定型', '10 s 不重叠块 CUSUM（k = 0.5）')],
     ('已取得', 'h* = 26；可检边界 泄漏 +2% / 受限 +50%（80 s）')),
    ('M1', '测量链构建', '2027.3—4 · 测得准', False,
     ('R1', '故障信号幅度是否高于测量不确定度'),
     [('单只差压变送器 + 干管参照', '量程/信号比 20—40 倍 → 4—8 倍'),
      ('台架水路按冻结顺序装配', '流量计 → 取压嘴A → 区段R → 取压嘴B → 泄漏球阀')],
     ('G1', '合成不确定度 U ≤ 0.20 kPa')),
    ('M2', '建模与标定', '2027.4—5 · 站得稳', False,
     ('R2', '供压波动与传感器漂移是否会淹没特征'),
     [('比值型双通道特征', 'K 管泄漏、Rh 管受限'),
      ('参照指数可辨识性判定', 'P₁ 跨度 < 20% 固定 n = 0.5')],
     ('G2', 'σ、τ、K 通道漂移速率实测入档')),
    ('M3', '判据与边界验证', '2027.5—6 · 判得出', False,
     ('R3', '轮灌切换等正常扰动会不会被误判成故障'),
     [('门限按实测噪声反推', '健康段扫描至误报率 ≤ 1% 后冻结'),
      ('54—72 次独立注入 + 三类对照', '供压扰动 / 邻支路切换 / 切换期故障')],
     ('G3', '检出率与误报率同时达标，可检边界成表')),
    ('M4', '通信与集成', '2027.7—8 · 传得到', False,
     ('R4', '断电与链路中断时事件是否会丢失'),
     [('只传事件、原始行走 SD 卡', '事件帧 57 B；先落库后 ACK'),
      ('整机 8 小时连续记录', '含重启恢复与中断恢复对照')],
     ('G4', '连续记录无缺段，中断恢复后事件零缺失')),
    ('M5', '验证与固化', '2027.9—2028.2 · 验得实', False,
     ('R5', '结论是否只在自家数据上成立'),
     [('留出批次 + 消融 + 强基线对照', '同门限下比检出侧增益'),
      ('论文、软著与结项材料', '数据集与复现脚本同步公开')],
     ('G5', '留出批次复现既有结论，成果齐套')),
]


def fig_route_chain():
    """两列布局：左列阶段 0—2、右列阶段 3—5，按编号顺序推进。"""
    css = S(""".chain { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }
.coltag {
  font-size: 24px; font-weight: 600; color: {{mute}}; border-bottom: 2px solid {{edge}};
  padding-bottom: 6px; margin-bottom: 12px;
}
.srow { display: grid; grid-template-columns: 84px 1fr; column-gap: 10px; }
.snum { font-size: 52px; font-weight: 800; color: {{ink}}; text-align: right; line-height: 1; padding-top: 6px; }
.sgap { height: 18px; display: flex; align-items: center; }
.sgap .varr { margin-left: 84px; }
.b3 .f { padding: 13px 18px 0; }
.b3 .hd { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.b3 .hd .nm { font-size: 38px; font-weight: 700; line-height: 1.2; }
.b3 .hd .tm { font-size: 24px; color: {{faint}}; flex: none; }
.b3 .risk { font-size: 38px; font-weight: 700; padding: 4px 0 8px; line-height: 1.3; }
.b3 .acts { padding-bottom: 9px; font-size: 24px; color: {{mute}}; line-height: 1.45; }
.act { display: flex; gap: 7px; }
.act .i { font-size: 24px; font-weight: 600; color: {{ink}}; flex: none; }
.b3 .gate { border-top: 1.5px dashed {{edge}}; padding: 8px 0 10px; font-size: 38px; font-weight: 700; line-height: 1.3; }
.done .f { background: repeating-linear-gradient(45deg, #ffffff 0 7px, #efefef 7px 12px); }
.legend { display: flex; gap: 26px; font-size: 22px; color: {{mute}}; align-items: center; flex-wrap: wrap; }
.legend i { display: inline-block; width: 34px; height: 20px; margin-right: 8px; vertical-align: -3px; }
""")

    def stage_html(no, name, tm, done, risk, acts, gate):
        cls = 'b3 done' if done else 'b3'
        h = [f'<div class="srow"><div class="snum">{no}</div>',
             f'<div class="{cls}"><div class="e" data-deco="1"></div><div class="f">',
             f'<div class="hd"><span class="nm">{name}</span><span class="tm">{tm}</span></div>']
        if risk:
            rt, rx = risk
            h.append(f'<div class="risk"><span class="tag-k">{rt}</span>{rx}</div>')
        else:
            h.append('<div class="risk"><span class="tag-k">起点</span>'
                     '在仿真上先回答"可检边界是否存在"</div>')
        h.append('<div class="acts">')
        for k, (t, d) in enumerate(acts):
            h.append(f'<div class="act"><span class="i">{k+1}.</span><span>{t}：{d}</span></div>')
        h.append('</div>')
        gt, gx = gate
        h.append(f'<div class="gate"><span class="tag-k">{gt}</span>{gx}</div>')
        h.append('</div></div></div>')
        return ''.join(h)

    parts = ['<div class="chain">']
    for ci, (col, tag) in enumerate([(STAGES[:3], '阶段 M0—M2'), (STAGES[3:], '阶段 M3—M5')]):
        parts.append('<div>')
        parts.append(f'<div class="coltag">{tag}</div>')
        for i, st in enumerate(col):
            parts.append(stage_html(*st))
            if i < len(col) - 1:
                parts.append('<div class="sgap"><div class="varr"></div></div>')
        parts.append('</div>')
    parts.append('</div>')
    parts.append(
        '<div class="legend" style="margin-top:12px">'
        '<span><i style="background:repeating-linear-gradient(45deg,#cfcfcf 0 5px,#ffffff 5px 10px);'
        f'border:1.5px solid {EDGE_C}"></i>已完成阶段</span>'
        f'<span><i style="border-top:2.5px solid {EDGE_C};height:0;width:34px;background:none"></i>阶段推进</span>'
        '<span><i style="border-top:1.5px dashed '
        f'{EDGE_C};height:0;width:34px;background:none"></i>门控验收点</span>'
        '</div>')
    return dict(html=''.join(parts), css=css)



# ═══════════════════════════════════════════════════════════
# 图 2  关键技术决策：备选 → 选定（3D 卡片 · 黑白）
# ═══════════════════════════════════════════════════════════
DECISIONS = [
    ('D1', '测压方案', '两只表压相减', '单只差压 + 干管参照',
     '量程/信号比 20—40 倍 → 4—8 倍，5% 级信号才留得下信噪比'),
    ('D2', '判据样本', '1 s 逐点判据', '10 s 不重叠块',
     '逐点相邻样本共享 90% 数据，门限被高估约 57 倍（1028 → 18）'),
    ('D3', '参照指数', '每工况拟合 n', '跨度不足时固定 n = 0.5',
     '单工况 P₁ 跨度仅 0.34%，n 不可辨识；跨度 ≥ 20% 才回归'),
    ('D4', '门限来源', '沿用仿真值', '按实测噪声反推冻结',
     '仿真未建模各通道独立传感器噪声，实物门限须重标'),
    ('D5', '受限注入', '更换孔板定量', '针阀连续调节',
     '定量受限需孔径精确到 4.82 mm，加工不可控'),
    ('D6', '区段阻力', '光管段取压', '段内内置 φ5.0 孔板',
     '光管 2.9 L/min 下压降 < 0.1 kPa，产生不了 7—8 kPa 健康态差压'),
    ('D7', '上报内容', '原始波形无线上传', '只传事件、原始行走 SD 卡',
     '事件帧 57 B ≤ 64 B 分包；续航与带宽同时守住'),
    ('D8', '发射功率', '模块标称最大功率', '功率设 ≤ 10 dBm',
     '433 MHz 免执照频段限值 10 mW e.r.p.'),
]


def fig_decision_fork():
    css = S("""
.dgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 18px; }
.dcard .dtop { display: flex; align-items: center; gap: 9px; margin-bottom: 9px; }
.dname { font-size: 31px; font-weight: 700; }
.opts { display: grid; grid-template-columns: 1fr 26px 1fr; align-items: stretch; gap: 4px; }
.opt {
  background: #fff; border: 1.5px dashed {{faint}}; padding: 9px 10px;
  font-size: 20px; color: {{mute}}; text-align: center;
  display: flex; align-items: center; justify-content: center; min-height: 46px;
}
.pick {
  position: relative; background: {{face2}}; border: 1.5px solid {{edge}};
  padding: 8px 11px; min-height: 46px;
  display: flex; flex-direction: column; justify-content: center;
}
.pick .p { font-size: 22px; font-weight: 600; }
.pick .w { font-size: 20px; color: {{mute}}; padding-top: 3px; }
.dfoot { margin-top: 6px; font-size: 17px; color: {{faint}}; }
.legend { margin-top: 14px; font-size: 20px; color: {{mute}}; display: flex; gap: 24px; align-items: center; }
.legend .sw { display: inline-block; width: 30px; height: 18px; margin-right: 7px; vertical-align: -3px; }
""")

    parts = ['<div class="dgrid">']
    for no, name, a, b, why in DECISIONS:
        parts.append('<div class="dcard">')
        parts.append(f'<div class="dtop"><span class="tag-k">{no}</span>'
                     f'<span class="dname">{name}</span></div>')
        parts.append(f'<div class="opts"><div class="opt">{a}</div>'
                     f'<div class="arrow" style="display:flex;align-items:center;'
                     f'justify-content:center;color:{EDGE_C};font-size:26px">→</div>'
                     f'<div class="pick"><div class="p">{b}</div>'
                     f'<div class="w">{why}</div></div></div>')
        parts.append('</div>')
    parts.append('</div>')
    parts.append(
        '<div class="legend">'
        f'<span><i class="sw" style="border:1.5px dashed {FAINT};background:#fff"></i>备选（被否）</span>'
        f'<span><i class="sw" style="border:1.5px solid {EDGE_C};background:{FACE2}"></i>选定与依据</span>'
        '</div>')
    return dict(html=''.join(parts), css=css)


# ═══════════════════════════════════════════════════════════
# 图 3  阶段推进甘特图（灰度条 + 斜纹已完成 + 门控虚线）
# ═══════════════════════════════════════════════════════════
MONTHS = ['26.10', '26.11', '26.12', '27.01', '27.02', '27.03', '27.04', '27.05',
          '27.06', '27.07', '27.08', '27.09', '27.10', '27.11', '27.12', '28.01', '28.02']
BARS = [
    ('M0 数字样机', 0, 5, 'hatch'),
    ('M1 测量链构建', 5, 7, '#3d3d3d'),
    ('M2 建模与标定', 6, 8, '#5a5a5a'),
    ('M3 判据验证', 7, 9, '#6f6f6f'),
    ('M4 通信集成', 9, 11, '#8a8a8a'),
    ('M5 成果固化', 11, 17, '#a8a8a8'),
]
GATES = [(7, 'G1 测量不确定度'), (9, 'G2 可检边界'), (11, 'G3 连续运行'), (17, 'G4 留出复现')]


def fig_gantt():
    n = len(MONTHS)
    css = S("""
.g { position: relative; }
.ghead { display: grid; grid-template-columns: 260px 1fr; margin-bottom: 6px; }
.gmonths { display: grid; grid-template-columns: repeat({{n}}, 1fr); }
.gmonths div { font-size: 18px; color: {{mute}}; text-align: center; }
.grow { display: grid; grid-template-columns: 260px 1fr; align-items: center; margin-bottom: 10px; }
.glabel { font-size: 31px; font-weight: 700; padding-right: 10px; }
.gtrack { position: relative; height: 28px; background: #fafafa; border: 1px solid {{line}}; }
.gbar {
  position: absolute; top: 3.5px; height: 20px;
  font-size: 12.5px; color: #fff; display: flex; align-items: center;
  justify-content: center; white-space: nowrap;
}
.gbar.hatch {
  background: repeating-linear-gradient(45deg, #cfcfcf 0 5px, #ffffff 5px 10px);
  border: 1.5px solid {{edge}}; color: {{ink}};
}
.gateline { position: absolute; top: -4px; bottom: -4px; width: 0; border-left: 3px dashed {{black}}; }
.gatetag { font-size: 20px; color: {{black}}; font-weight: 600; background: #fff; padding: 0 3px; }
.gatewrap { display: grid; grid-template-columns: 260px 1fr; }
.gatelane { position: relative; height: 62px; }
.gatetxt { position: absolute; white-space: nowrap; }
.legend { margin-top: 8px; display: flex; gap: 22px; font-size: 20px; color: {{mute}}; align-items: center; }
.legend .sw { display: inline-block; width: 28px; height: 14px; margin-right: 6px; vertical-align: -2px; }
""")

    parts = ['<div class="g">']
    parts.append('<div class="ghead"><div></div><div class="gmonths">'
                 + ''.join(f'<div data-scale="1">{m}</div>' for m in MONTHS) + '</div></div>')
    for label, s, e, style in BARS:
        left = s / n * 100
        width = (e - s) / n * 100
        if style == 'hatch':
            bar = f'<div class="gbar hatch" style="left:{left:.3f}%;width:{width:.3f}%"></div>'
        else:
            bar = f'<div class="gbar" style="left:{left:.3f}%;width:{width:.3f}%;background:{style}"></div>'
        parts.append(f'<div class="grow"><div class="glabel">{label}</div>'
                     f'<div class="gtrack">{bar}</div></div>')
    lane = []
    for k, (m, txt) in enumerate(GATES):
        left = m / n * 100
        align = 'translateX(-100%)' if m >= n - 1 else 'translateX(-50%)'
        top = 0 if k % 2 == 0 else 30
        lane.append(f'<div class="gatetxt" style="left:{left:.3f}%;top:{top}px;transform:{align}">'
                    f'<span class="gatetag">{txt}</span></div>')
        lane.append(f'<div class="gateline" data-line="1" style="left:{left:.3f}%"></div>')
    parts.append('<div class="gatewrap"><div></div><div class="gatelane" style="height:62px">'
                 + ''.join(lane) + '</div></div>')
    parts.append('</div>')
    parts.append(
        '<div class="legend">'
        f'<span><i class="sw hatch" style="background:repeating-linear-gradient(45deg,#cfcfcf 0 5px,#ffffff 5px 10px);border:1.5px solid {EDGE_C}"></i>已完成</span>'
        f'<span><i class="sw" style="background:#3d3d3d"></i>灰度由深到浅＝阶段先后</span>'
        f'<span><i class="sw" style="border-left:2.5px dashed {BLACK};width:0;height:18px;margin-right:0"></i>&nbsp;虚线＝门控验收点</span>'
        '</div>')
    return dict(html=''.join(parts), css=css.replace('{{n}}', str(n)))


if __name__ == '__main__':
    for fn, maker, w in [('route_risk_chain', fig_route_chain, 1300),
                         ('route_decision_fork', fig_decision_fork, 1060),
                         ('route_gantt', fig_gantt, 1060)]:
        d, size = render(fn, maker(), w=w)
        print(f'{d.name}  {size[0]}x{size[1]}')
