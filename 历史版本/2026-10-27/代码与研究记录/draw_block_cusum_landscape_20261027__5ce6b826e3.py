"""Landscape method diagram with proper vector mathematical typography."""
from pathlib import Path
from io import BytesIO
from html import escape
import json
import re
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'deliverables'/'块CUSUM诊断流程_横版修订_20261027'
OUT.mkdir(parents=True, exist_ok=True)
W,H=2420,1180
matplotlib.rcParams.update({'mathtext.fontset':'stix','svg.fonttype':'path'})
parts=[]
nodes=[]
math_checks=[]
segments=[]

def txt(x,y,value,size=30):
    parts.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei,SimSun,sans-serif" font-size="{size}" text-anchor="middle" dominant-baseline="central">{escape(value)}</text>')

def math(x,y,tex,size=32,maxw=None):
    b=BytesIO()
    math_to_image('$'+tex+'$',b,prop=FontProperties(size=size),format='svg',color='black')
    s=b.getvalue().decode('utf-8')
    s=s[s.index('<svg'):]
    # matplotlib includes RDF metadata with global ids; each equation gets unique ids.
    s=re.sub(r'<metadata>.*?</metadata>','',s,flags=re.S)
    m=re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"',s)
    mw,mh=map(float,m.groups())
    if maxw and mw>maxw:
        raise ValueError(f'Equation too wide: {mw:.1f}>{maxw}: {tex}')
    tag='eq'+str(len(math_checks))
    ids=re.findall(r'\bid="([^"]+)"',s)
    for ident in sorted(set(ids),key=len,reverse=True):
        s=s.replace(f'id="{ident}"',f'id="{tag}-{ident}"').replace(f'#{ident}"',f'#{tag}-{ident}"')
    s=re.sub(r'width="[^"]+"',f'width="{mw}"',s,count=1)
    s=re.sub(r'height="[^"]+"',f'height="{mh}"',s,count=1)
    s=s.replace('<svg ',f'<svg x="{x-mw/2}" y="{y-mh/2}" data-equation="{tag}" ',1)
    parts.append(s)
    math_checks.append(dict(id=tag,tex=tex,x=x-mw/2,y=y-mh/2,w=mw,h=mh))

def box(name,x,y,w,h,r=0):
    nodes.append(dict(name=name,x=x,y=y,w=w,h=h,kind='rect'))
    parts.append(f'<g data-node="{name}" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="white" stroke="#111" stroke-width="1.8"/>')

def end():parts.append('</g>')

def diamond(name,cx,cy,w,h):
    nodes.append(dict(name=name,x=cx-w/2,y=cy-h/2,w=w,h=h,kind='diamond'))
    parts.append(f'<g data-node="{name}" data-kind="diamond" data-x="{cx-w/2}" data-y="{cy-h/2}" data-w="{w}" data-h="{h}"><path d="M{cx-w/2} {cy} L{cx} {cy-h/2} L{cx+w/2} {cy} L{cx} {cy+h/2}Z" fill="white" stroke="#111" stroke-width="1.8"/>')

def line(points,arrow=True):
    segments.extend([dict(a=a,b=b) for a,b in zip(points,points[1:])])
    d='M'+' L'.join(f'{x} {y}' for x,y in points)
    parts.append(f'<path d="{d}" fill="none" stroke="#111" stroke-width="1.7" stroke-linejoin="miter"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>')

# Data/control paths. Long return paths run outside the calculation blocks.
line([(200,95),(200,140)])
line([(200,285),(200,370)],False)
line([(200,370),(200,415)])
line([(760,95),(850,95)])
line([(850,190),(790,190),(790,210),(360,210)])
line([(1300,225),(1300,315),(1485,315),(1485,400)])
line([(360,540),(425,540)])
line([(705,540),(790,540)])
line([(565,630),(565,730)])
line([(430,785),(20,785)],False)
line([(1180,540),(1260,540)])
line([(1710,540),(1790,540)])
line([(2075,660),(2075,710)])
line([(2290,800),(2400,800),(2400,1150),(20,1150)],False)
line([(2075,890),(2075,915),(1100,915)],False)
for x in [1100,1570,2040]:line([(x,915),(x,955)])
for x in [1100,1570,2040]:line([(x,1080),(x,1110)],False)
line([(2040,1110),(740,1110),(740,1017),(690,1017)])
line([(40,1017),(20,1017)],False)
line([(20,1150),(20,370),(200,370)],False)

box('start',120,40,160,55,r=27.5);txt(200,67,'开始');end()
box('init',40,140,320,145)
txt(200,171,'载入参照、尺度与门限',27)
math(200,217,r'S_{Q,0}=S_{R,0}=0',31,maxw=290)
txt(200,262,'h = 26（仿真基准）',26);end()

box('healthy',460,40,300,110)
txt(610,77,'独立健康数据',30);txt(610,119,'10 s 不重叠分块',28);end()
box('calibration',850,25,900,200)
txt(1300,61,'标定健康预测流量与稳健尺度',30)
math(1300,121,r'\widehat{Q}_m=g\,a\left(\frac{\bar{P}_{1,m}}{P_{\mathrm{ref}}}\right)^n,\quad n=0.5',34,maxw=860)
txt(1300,190,'健康块同时给出阻力中位数及两路残差稳健尺度',26);end()

box('sampling',40,415,320,250)
txt(200,449,'每 1 s 读取压力与计数',27)
math(200,490,r'\Delta P(t),\ P_1(t),\ N(t)',28,maxw=295)
txt(200,532,'构建 10 s 不重叠块',27)
math(200,585,r'Q_m=\frac{60\,\Delta N_m}{\kappa\,T_b}',32,maxw=290)
txt(200,635,'压力取块内算术均值',26);end()

diamond('quality',565,540,280,180)
txt(565,522,'块数据有效且',24);txt(565,558,'参照适用？',24);end()
txt(746,518,'是',27);txt(594,681,'否',27)
box('invalid',430,730,270,110)
txt(565,767,'记录不可用状态',27);txt(565,806,'本块不参与累积',27);end()

box('features',790,420,390,250)
txt(985,455,'计算块级水力特征',29)
math(985,522,r'K_m=\frac{Q_m}{\sqrt{\bar{P}_{1,m}}}',34,maxw=355)
math(985,610,r'R_{\mathrm{h},m}=\frac{\overline{\Delta P}_m}{Q_m^2}',34,maxw=355);end()

box('residuals',1260,400,450,280)
txt(1485,437,'双通道残差标准化',29)
math(1485,509,r'z_{Q,m}=\frac{Q_m/\widehat{Q}_m-1}{s_Q}',34,maxw=415)
math(1485,612,r'z_{R,m}=\frac{R_{\mathrm{h},m}-R_0}{s_R}',34,maxw=415);end()

box('cusum',1790,420,570,240)
txt(2075,460,'双通道单侧 CUSUM 递推',30)
math(2075,527,r'S_{j,m}=\max\left\{0,\ S_{j,m-1}+z_{j,m}-k\right\}',32,maxw=535)
math(2075,580,r'j\in\{Q,R\},\qquad k=0.5',31,maxw=535)
txt(2075,628,'每个数据块仅更新一次',27);end()

diamond('threshold',2075,800,430,180)
txt(2075,776,'任一通道越限？',26)
math(2075,818,r'\max_j\, S_{j,m}>h',30,maxw=270);end()
txt(2334,777,'否',27);txt(2110,909,'是',27)

for name,x,title,condition,detail in [
 ('leak',900,'等效泄漏候选',r'S_{Q,m}>h,\quad S_{R,m}\leq h','核查附加出流'),
 ('restriction',1370,'局部受限候选',r'S_{Q,m}\leq h,\quad S_{R,m}>h','核查测点区段阻力'),
 ('both',1840,'双通道异常候选',r'S_{Q,m}>h,\quad S_{R,m}>h','结合工况综合核查')]:
    box(name,x,955,400,125)
    math(x+200,983,condition,27,maxw=370)
    txt(x+200,1019,title,28);txt(x+200,1054,detail,23);end()

box('event',40,955,650,125)
txt(365,993,'保存事件、测量质量与参照版本',29)
txt(365,1040,'LoRa 上报，人工核查与同工况复测',28);end()
txt(1250,1134,'未越限：继续下一块',26)

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">支管故障块CUSUM诊断流程（横版公式修订）</title>
<desc id="desc">独立健康数据标定参照；在线每秒采集，十秒不重叠分块，经数据检查后从左向右计算水力特征、标准化残差和CUSUM。越限结果分类后保存事件，沿外侧回路继续采集。</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9.5" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10Z" fill="#111"/></marker></defs>
<rect width="{W}" height="{H}" fill="white"/><g fill="#111">{''.join(parts)}</g></svg>'''
(OUT/'块CUSUM诊断流程_横版.svg').write_text(svg,encoding='utf-8')
(OUT/'绘图信息.json').write_text(json.dumps(dict(width=W,height=H,nodes=nodes,equations=math_checks,segments=segments),ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'公式核对与图注.md').write_text(r'''# 公式核对与图注

图注建议：图3-10 支管故障的块CUSUM诊断流程。

## 视觉复核与修订

原纵版的根号仅使用字符，没有覆盖被开方项的横线；两条水力特征挤在同一行；块序号在计算式与判断式中不统一；预测流量未说明是否包含标定增益；σ易被误读为普通标准差。横版使用STIX数学字体及矢量公式，改为完整分式、根式、上下标，全部块变量用m索引，MAD得到的稳健尺度统一写为s_Q、s_R。

## 与项目参考程序逐项对应

1. 数据块：T_b=10 s，每1 s读取累计脉冲数。图中Q_m以L/min计，κ以脉冲/L计，ΔN_m为本块起止端点之差，故Q_m=60ΔN_m/(κT_b)。κ由独立流量标定确定，名义值540脉冲/L。压力变量加横线，表示先取块内算术均值，再计算比值。脉冲计数需包含本块两个边界端点。
2. 水力特征：K_m=Q_m/√P̄_{1,m}；R_{h,m}=ΔP̄_m/Q_m²。图中分子ΔP̄_m为直接差压观测均值；参考仿真使用P̄₀−P̄₁，两者是同一水力压差的两种输入形式。
3. 健康预测：Q̂_m=g·a·(P̄_{1,m}/P_ref)^n，P_ref=100 kPa，n=0.5。g为标定增益，a为曲线系数；图中Q̂包含二者，避免遗漏lib_block.py中gain的歧义。本文图示不修改既有标定程序。
4. 残差：e_{Q,m}=Q_m/Q̂_m−1；e_{R,m}=R_{h,m}−R₀。z_{Q,m}=e_{Q,m}/s_Q，z_{R,m}=e_{R,m}/s_R。R₀为独立健康块的区段阻力中位数。s_Q、s_R分别由健康残差的1.4826×MAD及尺度下限计算，单位分别与各自残差一致；标准化后z均无量纲。程序尺度下限分别为1e−5和1e−4（后者使用项目阻力计算单位）。残差不额外减健康残差中位数，与resid_blocks/cusum_run一致。
5. 累积：S_{j,m}=max{0,S_{j,m−1}+z_{j,m}−k}，j∈{Q,R}，k=0.5，S_{j,0}=0。每10 s完整有效块仅更新一次。m表示块序号，不表示秒数。
6. 越限：max_j S_{j,m}>h，与参考程序严格大于h的比较一致，不能擅自改成≥。h=26仅为既有合成仿真基准；实物需根据台架实测噪声重标。
7. 无效块：记录不可用，不增加CUSUM；图按cusum_run的mask语义保留上一累积值，不表示清零。工程中的长期中断复位策略应另行定义。图为拟实施方法设计，参考evaluate入口未统一接入全部质量门控，不能据图认定固件集成已完成。
8. 候选分类：仅流量路越限→等效泄漏候选；仅阻力路越限→局部受限候选；两路越限→综合异常候选。这里是提示模式，负载正常变化、漂移和历史累积均可能影响结果，不能把模式当作已确认故障原因。现场原因由操作记录和同工况人工复测确认。
9. K用于水力解释；当前CUSUM流量通道直接使用Q/Q̂−1，而非把未标准化K直接送入CUSUM。n=0.5时，这一路对应相对健康负载特征的偏离。

## 文件与使用

PNG为3倍分辨率；SVG中中文、框和连线保留为矢量，数学公式转为矢量轮廓以保证跨设备显示。公式原始TeX在绘图信息.json与生成脚本中，修改时可重新生成。

本图宽高比约2.05:1，适合横向页面。按宽25 cm放置，主要中文字号约8—9 pt；如放在普通纵向A4正文内，应单独横向放置或适当放大，避免过度缩小。

依据：simulation/project_review/lib_block.py中的blocks、calib、resid_blocks、cusum_run，以及docs/技术路线_分块版_申报书用.md第3—4部分。未运行或改写历史实验。
''',encoding='utf-8')
print(OUT)
