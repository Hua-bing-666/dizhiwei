# -*- coding: utf-8 -*-
"""
信号链全景（signal_chain）+ 故障机理对照（fault_mechanism）
—— 3D 立体框 · 黑白打印版，HTML/CSS 渲染（复用 draw_route_figs 基建）

视觉规范与 draw_route_figs.py 相同：
灰度体系、右下 extrude 立体框、黑底白字标签、底部灰色注释行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draw_route_figs import render, S, OUT, EDGE_C, MUTE, FAINT, INK, FACE2

MATH_URI = (OUT / 'math').as_uri()


# ═══════════════════════════════════════════════════════════
# A. 信号链全景：物理层 → 输入层 → 处理层 → 输出层
# ═══════════════════════════════════════════════════════════
def fig_signal_chain():
    css = S("""
.sc { }
.lay { display: grid; grid-template-columns: 104px 1fr; column-gap: 16px; align-items: stretch; }
.ltag {
  display: flex; align-items: center; justify-content: center;
  border: 1.5px solid {{edge}}; background: {{face2}}; font-size: 35px;
  font-weight: 700; writing-mode: horizontal-tb; padding: 6px 4px; height: 100%;
}
.nodes { position: relative; }
.nrow { display: flex; align-items: stretch; }
.b3 { flex: 1; }
.b3 .f { padding: 12px 18px 10px; text-align: center; }
.b3 .f .t { font-size: 35px; font-weight: 700; }
.b3 .f .s { font-size: 22px; color: {{mute}}; padding-top: 4px; line-height: 1.45; }
.b3 .f .gk { font-size: 22px; font-weight: 600; padding-top: 4px; }
.b3 .f .gk::before { content: "守门 "; font-weight: 400; color: {{faint}}; font-size: 18px; }
.harr { width: 30px; display: flex; align-items: center; justify-content: center;
        color: {{edge}}; font-size: 26px; font-weight: 700; flex: none; }
.ev { background: #fff; border: 1.5px dashed {{faint}}; }
.ev .t { color: {{ink}}; }
.vconn { display: grid; grid-template-columns: 90px 1fr; }
.vconn .pad { }
.vconn .ar { height: 30px; display: flex; align-items: center; justify-content: center; }
.vconn .ar .varr { margin: 0; }
.lgap { height: 8px; }
.legend { display: flex; gap: 26px; margin-top: 16px; font-size: 22px; color: {{mute}}; align-items: center; }
.legend .sw { display: inline-block; width: 34px; height: 0; vertical-align: 3px; }
.eqimg { display: block; margin: 4px auto 0; }
""")

    def node(title, sub, gate=None, ev=False):
        g = f'<div class="gk">{gate}</div>' if gate else ''
        cls = 'b3 ev' if ev else 'b3'
        return (f'<div class="{cls}"><div class="e" data-deco="1"></div><div class="f">'
                f'<div class="t">{title}</div><div class="s">{sub}</div>{g}</div></div>')

    def harr():
        return '<div class="harr">→</div>'

    parts = ['<div class="sc">']

    # 物理层：故障源 + 水力响应
    parts.append('<div class="lay"><div class="ltag">物理层</div><div class="nodes"><div class="nrow">')
    parts.append(node('等效泄漏', '旁路跑水 · 总流量增大', ev=True))
    parts.append(harr())
    parts.append(node('等效受限', '孔板收缩 · 区段阻力增大', ev=True))
    parts.append(harr())
    parts.append(node('水力响应', 'K = Q/√P₁ 管泄漏　Rh = ΔP/Q² 管受限'))
    parts.append('</div></div></div>')

    parts.append('<div class="vconn"><div class="pad"></div><div class="ar"><div class="varr"></div></div></div>')

    # 输入层
    parts.append('<div class="lay"><div class="ltag">输入层</div><div class="nodes"><div class="nrow">')
    parts.append(node('差压 ΔP', '单只差压变送器<br>35—40 kPa · ±0.5%FS', 'U ≤ 0.20 kPa'))
    parts.append(harr())
    parts.append(node('干管参照 P₁', '干管取压 · 健康参照指数', '跨度 ≥ 20% 才拟合 n'))
    parts.append(harr())
    parts.append(node('脉冲流量 Q', 'SEN0549 · 540 脉冲/L<br>PB6/TIM4_CH1 计数', '1 s 提交'))
    parts.append(harr())
    parts.append(node('原始行走', '1 s 逐条写 SD 卡 CSV<br>断网不丢数'))
    parts.append('</div></div></div>')

    parts.append('<div class="vconn"><div class="pad"></div><div class="ar"><div class="varr"></div></div></div>')

    # 处理层
    parts.append('<div class="lay"><div class="ltag">处理层</div><div class="nodes"><div class="nrow">')
    parts.append(node('特征计算', '比值型双通道<br>K 管泄漏 · Rh 管受限'))
    parts.append(harr())
    parts.append(node('10 s 不重叠块', '块内算术平均<br>每块累积一次'))
    parts.append(harr())
    parts.append(node('块 CUSUM', 'k = 0.5 · n 固定 0.5', 'h* = 26（仿真基准）'))
    parts.append(harr())
    parts.append(node('判定', 'Sₘ > h ⇒ 事件<br>复位 Sₘ ← max(0, …)'))
    parts.append('</div></div></div>')

    parts.append('<div class="vconn"><div class="pad"></div><div class="ar"><div class="varr"></div></div></div>')

    # 输出层
    parts.append('<div class="lay"><div class="ltag">输出层</div><div class="nodes"><div class="nrow">')
    parts.append(node('事件帧上报', '57 B · COBS + CRC16<br>先落库后 ACK', '重发预算零缺失'))
    parts.append(harr())
    parts.append(node('LoRa 发送', 'E220-400T22D', '≤ 10 dBm（合规）'))
    parts.append(harr())
    parts.append(node('处置闭环', '查看 / 处置 / 复测<br>处置结果回写健康参照'))
    parts.append('</div></div></div>')

    parts.append(
        '<div class="legend">'
        f'<span><i class="sw" style="border-top:2.5px solid {EDGE_C}"></i>数据流（实线箭头）</span>'
        f'<span><i class="sw" style="border-top:1.5px dashed {FAINT};height:0"></i>虚线框＝外部事件（故障源）</span>'
        '<span>"守门"＝该环节的量化验收指标</span></div>')
    return dict(html=''.join(parts), css=css)


# ═══════════════════════════════════════════════════════════
# B. 故障机理对照：(a) 等效泄漏 vs (b) 等效受限
# ═══════════════════════════════════════════════════════════
def fig_fault_mechanism():
    css = S("""
.fm { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
.panel { position: relative; border: 1.5px solid {{edge}}; background: {{face}}; padding: 16px 20px 14px; }
.panel::before, .panel::after { content: ""; position: absolute; width: 16px; height: 16px; }
.panel::before { left: 4px; top: 4px; border-left: 2.5px solid {{edge}}; border-top: 2.5px solid {{edge}}; }
.panel::after  { right: 4px; bottom: 4px; border-right: 2.5px solid {{edge}}; border-bottom: 2.5px solid {{edge}}; }
.ptitle { font-size: 35px; font-weight: 700; text-align: center; padding-bottom: 12px; }
.pzone { position: relative; height: 168px; background: #fff; border: 1px solid {{line}}; }
.plabel { position: absolute; top: 36px; font-size: 22px; color: {{mute}}; }
.plabel.l { left: 14px; }
.plabel.r { right: 14px; }
.pipe { position: absolute; top: 72px; left: 48px; right: 48px; height: 4px; background: {{edge}}; }
.pipe::after {
  content: ""; position: absolute; right: -11px; top: -5.5px;
  border-top: 7.5px solid transparent; border-bottom: 7.5px solid transparent;
  border-left: 11px solid {{edge}};
}
.pt {
  position: absolute; top: 58px; width: 32px; height: 32px; border-radius: 50%;
  background: #fff; border: 2px solid {{edge}}; font-size: 22px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
}
.ptag { position: absolute; top: 18px; font-size: 22px; color: {{mute}}; transform: translateX(-50%); }
.branch { position: absolute; left: calc(50% - 1.5px); top: 76px; width: 3px; height: 52px; background: {{edge}}; }
.branch::after {
  content: ""; position: absolute; bottom: -9px; left: -5.2px;
  border-left: 6.7px solid transparent; border-right: 6.7px solid transparent;
  border-top: 9px solid {{edge}};
}
.valve {
  position: absolute; top: 126px; left: 50%; transform: translateX(-50%);
  background: {{face2}}; border: 1.5px solid {{edge}}; font-size: 22px; font-weight: 600;
  padding: 3px 14px; white-space: nowrap;
}
.valve-l { position: absolute; top: 134px; left: calc(50% + 86px); font-size: 18px; color: {{mute}}; }
.restrict {
  position: absolute; top: 54px; left: 50%; transform: translateX(-50%);
  width: 26px; height: 40px; background: #fff; border: 2px solid {{edge}};
}
.rtag2 {
  position: absolute; top: 100px; left: 50%; transform: translateX(-50%);
  background: {{face2}}; border: 1.5px solid {{edge}}; font-size: 22px; font-weight: 600;
  padding: 3px 14px; white-space: nowrap;
}
.resp { padding-top: 14px; font-size: 22px; }
.resp b { font-weight: 600; }
.eqrow { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.up { font-size: 35px; font-weight: 700; }
.dashednote { margin-top: 18px; border: 1.5px dashed {{faint}}; background: #fff;
  padding: 12px 16px; font-size: 22px; color: {{mute}}; }
.dashednote b { color: {{ink}}; font-weight: 600; }
""")

    leak_panel = f"""
<div class="panel">
  <div class="ptitle">(a) 等效泄漏 —— 旁路放水</div>
  <div class="pzone">
    <span class="plabel l">来水</span><span class="plabel r">下游负载</span>
    <div class="pipe" data-line="1"></div>
    <div class="pt" style="left:26%">Q</div><div class="ptag" style="left:calc(26% + 16px)">测流量</div>
    <div class="pt" style="left:66%">ΔP</div><div class="ptag" style="left:calc(66% + 16px)">测压降</div>
    <div class="branch" data-line="1"></div>
    <div class="valve">泄漏阀</div>
    <div class="valve-l">旁路跑水</div>
  </div>
  <div class="resp"><b>响应</b>　Q ↑（含泄漏量）　ΔP ≈ 不变</div>
  <div class="eqrow">
    <img class="eqimg" style="margin:0" src="{MATH_URI}/eq_K.png" style2="" width="118" alt="K = Q/√P₁">
    <span class="up">↑</span><span style="font-size:22px;color:{MUTE}">Rh = ΔP/Q² ≈ 不变</span>
  </div>
</div>"""

    restr_panel = f"""
<div class="panel">
  <div class="ptitle">(b) 等效受限 —— 孔板收缩</div>
  <div class="pzone">
    <span class="plabel l">来水</span><span class="plabel r">下游负载</span>
    <div class="pipe" data-line="1"></div>
    <div class="pt" style="left:26%">Q</div><div class="ptag" style="left:calc(26% + 16px)">测流量</div>
    <div class="pt" style="left:66%">ΔP</div><div class="ptag" style="left:calc(66% + 16px)">测压降</div>
    <div class="restrict"></div>
    <div class="rtag2">孔板 + 针阀</div>
  </div>
  <div class="resp"><b>响应</b>　Q ≈ 不变　ΔP ↑</div>
  <div class="eqrow">
    <img class="eqimg" style="margin:0" src="{MATH_URI}/eq_Rh.png" width="100" alt="Rh = ΔP/Q²">
    <span class="up">↑</span><span style="font-size:22px;color:{MUTE}">K = Q/√P₁ ≈ 不变</span>
  </div>
</div>"""

    html = (leak_panel + restr_panel +
            f'<div class="legend" style="margin-top:20px">'
            f'<span><i style="border-top:3px solid {EDGE_C};height:0;width:34px;background:none"></i>管段与流向</span>'
            f'<span><i style="width:20px;height:20px;border:2px solid {EDGE_C};border-radius:50%;background:#fff"></i>测点</span>'
            f'<span><i style="background:{FACE2};border:1.5px solid {EDGE_C};width:34px"></i>泄漏阀 / 孔板</span>'
            '</div>')
    return dict(html=f'<div class="fm">{html}</div>', css=css)


if __name__ == '__main__':
    for fn, maker in [('signal_chain', fig_signal_chain),
                      ('fault_mechanism', fig_fault_mechanism)]:
        d, size = render(fn, maker(), w=1180)
        print(f'{d.name}  {size[0]}x{size[1]}')
