# -*- coding: utf-8 -*-
"""
《项目实施方案》配套图（HTML/CSS 排版 + 无头浏览器渲染）—— 3D 立体框 · 黑白打印版

与 draw_route_figs.py / draw_signal_figs.py 共用同一套视觉规范：
灰度体系、右下 extrude 立体框、HUD 内角标、黑底白字标签、底部注释行。
数字口径一律取自已冻结的技术文档，不在本脚本内杜撰。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draw_route_figs import render, S, OUT, EDGE_C, MUTE, FAINT, INK, FACE2, SIDE as SIDE_C

W = 1180          # 绘制宽度：主词 ≥35px、次要 ≥22px（A4 版心 15.4cm 放置后 9.5/6 pt）


# ═══════════════════════════════════════════════════════════
# A. 帧字节结构条带（遥测 55 B / 事件 57 B / ACK 24 B）
# ═══════════════════════════════════════════════════════════
FRAMES = [
    ('遥测帧　55 B', [
        ('公共头', 16, 'head'),
        ('测量快照', 35, 'snap'),
        ('CRC16 / COBS', 4, 'crc'),
    ]),
    ('事件帧　57 B', [
        ('公共头', 16, 'head'),
        ('测量快照', 35, 'snap'),
        ('事件码 + 细节', 2, 'event'),
        ('CRC16 / COBS', 4, 'crc'),
    ]),
    ('ACK　24 B', [
        ('公共头', 16, 'head'),
        ('CRC32 指纹', 4, 'event'),
        ('CRC16 / COBS', 4, 'crc'),
    ]),
]


def fig_frame_layout():
    css = S(""".fl { }
.row { display: grid; grid-template-columns: 250px 1fr; align-items: stretch; column-gap: 16px; margin-bottom: 14px; }
.fname { font-size: 35px; font-weight: 700; display: flex; align-items: center; }
.strip { display: flex; border: 1.5px solid {{edge}}; background: #fff; }
.seg {
  border-left: 1.5px solid {{edge}}; padding: 9px 6px 8px; text-align: center;
  display: flex; flex-direction: column; justify-content: center; min-width: 0;
}
.seg:first-child { border-left: none; }
.seg .n { font-size: 22px; font-weight: 600; line-height: 1.2; }
.seg .b { font-size: 35px; font-weight: 700; padding-top: 2px; }
.seg.head  { background: {{face2}}; }
.seg.snap  { background: #ffffff; }
.seg.event { background: repeating-linear-gradient(45deg, #e9e9e9 0 6px, #ffffff 6px 12px); }
.seg.crc   { background: {{side}}; }
.hdbar {
  border: 1.5px solid {{edge}}; background: #fafafa; padding: 10px 14px;
  font-size: 22px; color: {{mute}}; margin-bottom: 16px;
}
.hdbar b { color: {{ink}}; font-weight: 600; }
.legend { display: flex; gap: 26px; margin-top: 14px; font-size: 22px; color: {{mute}}; flex-wrap: wrap; }
.legend i { display: inline-block; width: 34px; height: 20px; margin-right: 8px; vertical-align: -3px; border: 1.5px solid {{edge}}; }
""")

    parts = ['<div class="fl">']
    parts.append('<div class="hdbar"><b>公共头 16 B：</b>'
                 '版本 1 B / 类型 1 B / 载荷长度 2 B / 设备号 4 B / 会话号 4 B / 消息序号 4 B</div>')
    for name, segs in FRAMES:
        total = sum(s[1] for s in segs)
        parts.append(f'<div class="row"><div class="fname">{name}</div><div class="strip">')
        for seg_name, nb, kind in segs:
            flex = nb / total * 100
            parts.append(f'<div class="seg {kind}" style="flex:0 0 {flex:.3f}%">'
                         f'<div class="n">{seg_name}</div><div class="b">{nb} B</div></div>')
        parts.append('</div></div>')
    parts.append(
        '<div class="legend">'
        f'<span><i style="background:{FACE2}"></i>公共头</span>'
        '<span><i style="background:#ffffff"></i>测量快照</span>'
        '<span><i style="background:repeating-linear-gradient(45deg,#e9e9e9 0 6px,#ffffff 6px 12px)"></i>事件码 / 指纹</span>'
        f'<span><i style="background:{SIDE_C}"></i>CRC16 / COBS</span>'
        '</div>')
    return dict(html=''.join(parts), css=css)


# ═══════════════════════════════════════════════════════════
# B. 10 s 块判据处理链
# ═══════════════════════════════════════════════════════════
CHAIN = [
    ('采样提交', '三通道 1 s 行', '1 Hz 节拍'),
    ('块平均', '块均值序列', '块长 W = 10 s'),
    ('特征构造', 'K 与 Rh', 'n 固定 0.5'),
    ('CUSUM 累积', '累积量 Sₘ', 'k = 0.5'),
    ('门限判决', '候选事件', 'h* = 26（仿真基准）'),
]


def fig_judging_chain():
    css = S(""".jc { display: flex; align-items: stretch; }
.node { flex: 1; display: flex; flex-direction: column; }
.b3 { flex: 1; }
.b3 .f { padding: 13px 10px 12px; text-align: center; }
.b3 .f .t { font-size: 35px; font-weight: 700; }
.b3 .f .s { font-size: 22px; color: {{mute}}; padding-top: 5px; }
.param {
  margin-top: 11px; border: 1.5px dashed {{edge}}; background: #fafafa;
  padding: 7px 6px; font-size: 22px; font-weight: 600; text-align: center;
}
.legend { display: flex; gap: 26px; font-size: 22px; color: {{mute}}; align-items: center; }
.legend i { display: inline-block; width: 34px; height: 20px; margin-right: 8px; vertical-align: -3px; }
.harr { width: 34px; display: flex; align-items: center; justify-content: center;
        font-size: 26px; font-weight: 700; color: {{edge}}; flex: none; }
""")

    parts = ['<div class="jc">']
    for i, (t, sub, param) in enumerate(CHAIN):
        parts.append('<div class="node">')
        parts.append(f'<div class="b3"><div class="e" data-deco="1"></div><div class="f">'
                     f'<div class="t">{t}</div><div class="s">{sub}</div></div></div>')
        parts.append(f'<div class="param">{param}</div>')
        parts.append('</div>')
        if i < len(CHAIN) - 1:
            parts.append('<div class="harr">→</div>')
    parts.append('</div>')
    parts.append(
        '<div class="legend" style="margin-top:18px">'
        f'<span><i style="border-top:2.5px solid {EDGE_C};height:0;width:34px;background:none"></i>处理顺序</span>'
        f'<span><i style="border:1.5px dashed {EDGE_C};background:#fafafa"></i>该环节参数</span>'
        '</div>')
    return dict(html=''.join(parts), css=css)


if __name__ == '__main__':
    for fn, maker in [('frame_layout', fig_frame_layout),
                      ('judging_chain', fig_judging_chain)]:
        d, size = render(fn, maker(), w=W)
        print(f'{d.name}  {size[0]}x{size[1]}')
