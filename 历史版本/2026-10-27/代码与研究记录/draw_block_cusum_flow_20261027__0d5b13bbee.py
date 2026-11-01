"""Draw the proposed block-CUSUM method as an editable academic flowchart."""
from pathlib import Path
from html import escape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables' / '块CUSUM诊断流程_重绘_20261027'
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1160, 1460
parts = []
nodes = []

def rich(value):
    value = escape(value)
    return re.sub(r'_\{([^}]+)\}|_([A-Za-z]+)', lambda m: f'<tspan baseline-shift="sub" font-size="72%">{m[1] or m[2]}</tspan>', value)

def text(x, y, value, size=26, math=False):
    math = math or any(t in value for t in ['=', '∈', '>'])
    family = 'Cambria, Microsoft YaHei, sans-serif' if math else 'Microsoft YaHei, sans-serif'
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-family="{family}" text-anchor="middle" dominant-baseline="central">{rich(value)}</text>')

def lines(x, y, values, gap=33, size=26):
    for i, value in enumerate(values):
        text(x, y + (i - (len(values)-1)/2)*gap, value, size)

def box(name, x, y, w, h, values, size=26, radius=0, gap=33):
    nodes.append(dict(name=name, x=x, y=y, w=w, h=h, kind='rect'))
    parts.append(f'<g data-node="{name}" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}">')
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="white" stroke="#111" stroke-width="1.65"/>')
    lines(x+w/2, y+h/2, values, gap, size)
    parts.append('</g>')

def diamond(name, cx, cy, w, h, values, size=25):
    nodes.append(dict(name=name, x=cx-w/2, y=cy-h/2, w=w, h=h, kind='diamond'))
    parts.append(f'<g data-node="{name}" data-kind="diamond" data-x="{cx-w/2}" data-y="{cy-h/2}" data-w="{w}" data-h="{h}"><path d="M{cx} {cy-h/2} L{cx+w/2} {cy} L{cx} {cy+h/2} L{cx-w/2} {cy}Z" fill="white" stroke="#111" stroke-width="1.65"/>')
    lines(cx,cy,values,31,size)
    parts.append('</g>')

def path(points, arrow=True):
    d='M'+' L'.join(f'{x} {y}' for x,y in points)
    parts.append(f'<path class="connector" d="{d}" fill="none" stroke="#111" stroke-width="1.55" stroke-linejoin="miter"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>')

def label(x,y,value,size=24):
    # White halo keeps branch labels clean at connector joins.
    parts.append(f'<text x="{x}" y="{y}" font-family="Cambria, Microsoft YaHei, sans-serif" font-size="{size}" text-anchor="middle" dominant-baseline="central" stroke="white" stroke-width="7" paint-order="stroke" fill="#111">{rich(value)}</text>')

# Connectors first: nodes cover only their own entry and exit edges.
path([(600,72),(600,103)])
path([(600,169),(600,202)])
path([(600,284),(600,315)])
path([(600,393),(600,421)])
path([(600,561),(600,594)])
path([(790,491),(900,491)])
path([(1125,491),(1140,491)],False)
path([(600,684),(600,720)])
path([(160,284),(160,315)])
path([(160,465),(160,775),(350,775)])
path([(600,830),(600,865)])
path([(600,967),(600,1000)])
path([(790,1057),(1140,1057)],False)
path([(600,1114),(600,1150)],False)
path([(190,1150),(970,1150)],False)
path([(190,1150),(190,1190)])
path([(580,1150),(580,1190)])
path([(970,1150),(970,1190)])
for x in [190,580,970]:
    path([(x,1278),(x,1312)],False)
path([(190,1312),(970,1312)],False)
path([(600,1312),(600,1340)])
path([(900,1384),(1140,1384),(1140,187),(600,187),(600,202)])

box('start',525,24,150,48,['开始'],radius=24)
box('init',350,103,500,66,['载入标定参数，累积量置零'])
box('sample',350,202,500,82,['每 1 s 读取压力与累计脉冲数','ΔP、P₁、N'],gap=31)
box('block',350,315,500,78,['构建 10 s 不重叠数据块','块内均值；计数增量换算流量 Q'],gap=33)
diamond('valid',600,491,380,140,['块数据有效且','健康参照适用？'],size=24)
box('invalid',900,448,225,86,['记录不可用状态','本块不参与累积'],size=23,gap=31)
box('features',350,594,500,90,['计算块级水力特征','K = Q / √P₁    Rₕ = ΔP / Q²'],gap=35)
box('independent_data',35,202,250,82,['独立健康数据','按 10 s 分块'],size=25,gap=31)
box('calibration',35,315,250,150,['标定健康参照','Q_ref(P₁)、R₀','稳健尺度 σ_Q、σ_R','h = 26（仿真基准）'],size=24,gap=32)
box('residual',350,720,500,110,['计算并标准化双通道残差','z_Q = (Q / Q_ref − 1) / σ_Q','z_R = (Rₕ − R₀) / σ_R'],size=24,gap=29)
box('cusum',350,865,500,102,['双通道单侧 CUSUM 递推','S_{j,m} = max(0, S_{j,m−1} + z_{j,m} − 0.5)','j ∈ {Q, R}；每个数据块更新一次'],size=24,gap=30)
diamond('threshold',600,1057,380,114,['S_Q > h 或 S_R > h？'],size=27)
box('leak',35,1190,310,88,['等效泄漏候选','核查附加出流'],size=25,gap=33)
box('restriction',425,1190,310,88,['局部受限候选','核查测点区段阻力'],size=25,gap=33)
box('both',815,1190,310,88,['双通道异常候选','结合工况综合核查'],size=25,gap=33)
box('event',300,1340,600,88,['保存事件、测量质量与参照版本','LoRa 上报，人工核查与同工况复测'],size=26,gap=35)
label(634,575,'是')
label(839,475,'否')
label(955,1041,'否，继续监测',23)
label(629,1133,'是')
label(190,1172,'S_Q > h，S_R ≤ h',24)
label(580,1172,'S_Q ≤ h，S_R > h',24)
label(970,1172,'S_Q > h，S_R > h',24)

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">支管故障块CUSUM诊断流程</title>
<desc id="desc">独立健康标定支路向在线监测提供参照和尺度。每秒采集，十秒不重叠块，数据检查，双残差标准化，双通道单侧CUSUM递推与候选分类；无效、未越限及事件记录后均返回采集。</desc>
<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8.5" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L9 4.5 L0 9Z" fill="#111"/></marker></defs>
<rect width="{W}" height="{H}" fill="white"/>
<g fill="#111">{''.join(parts)}</g></svg>'''
(OUT/'块CUSUM诊断流程.svg').write_text(svg,encoding='utf-8')
(OUT/'绘图信息.json').write_text(json.dumps(dict(width=W,height=H,nodes=nodes,sources=[
    'docs/技术路线_分块版_申报书用.md §3.2、§4.2',
    'simulation/project_review/lib_block.py blocks/calib/resid_blocks/cusum_run',
],scope='诊断方法设计图；不表示固件与平台已完成集成'),ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'图注与正文替换建议.md').write_text('''# 图注与对应正文

建议图注：图3-10 支管故障的块CUSUM诊断流程。

节点每1 s读取区段差压ΔP、下游参照压力P₁和累计脉冲数，构建10 s不重叠数据块，并由计数增量换算流量。对有效块计算区段阻力Rₕ=ΔP/Q²及相对健康预测流量的偏离；经独立健康数据标定的稳健尺度标准化后，分别更新流量与阻力通道的单侧CUSUM，参考值k=0.5。仅流量通道越限时形成等效泄漏候选，仅阻力通道越限时形成局部受限候选，两路均越限时列为综合异常。无效块标记不可用且不参与累积；未越限时继续观测。事件保存测量质量和参照版本，经LoRa上报，并结合操作记录、人工核查与同工况复测解释原因。

图中h=26为项目既有合成仿真基准；实物门限须按台架实测噪声重新标定。图为拟实施诊断方法，不能据此认定目标固件及平台已完成集成。健康数据与监测数据分开，不能使用待判故障段重新拟合健康参照。当前单工况方案默认固定压力指数n=0.5。

与截图正文的区别：本图每10 s更新一次CUSUM，不沿用3 s短窗、连续2次提示与连续5次确认。替换图3-10时，原图上方对应诊断段落也应改为本方案。

交付文件：PNG为3倍分辨率白底图；SVG内的文字、框和连线可继续编辑。图内不嵌图号，可直接放入Word并单独添加题注。
''',encoding='utf-8')
print(OUT)
