"""Large-type landscape flowchart; source equations stay in vector form."""
from pathlib import Path
from io import BytesIO
from html import escape
import json,re
import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables'/'块CUSUM诊断流程_横版大字清晰版_20261027'
OUT.mkdir(parents=True,exist_ok=True)
W,H=2440,1400
matplotlib.rcParams.update({'mathtext.fontset':'stix','svg.fonttype':'path'})
parts=[];nodes=[];equations=[]

def txt(x,y,value,size=34):
    parts.append(f'<text x="{x}" y="{y}" font-family="SimHei,Microsoft YaHei,sans-serif" font-size="{size}" text-anchor="middle" dominant-baseline="central" text-rendering="geometricPrecision">{escape(value)}</text>')

def math(x,y,tex,size=50,maxw=None):
    b=BytesIO();math_to_image('$'+tex+'$',b,prop=FontProperties(size=size),format='svg',color='black')
    s=b.getvalue().decode('utf-8');s=s[s.index('<svg'):]
    s=re.sub(r'<metadata>.*?</metadata>','',s,flags=re.S)
    mw,mh=map(float,re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"',s).groups())
    if maxw and mw>maxw:raise ValueError(f'Equation too wide: {mw}>{maxw}: {tex}')
    tag='eq'+str(len(equations))
    for ident in sorted(set(re.findall(r'\bid="([^"]+)"',s)),key=len,reverse=True):
        s=s.replace(f'id="{ident}"',f'id="{tag}-{ident}"').replace(f'#{ident}"',f'#{tag}-{ident}"')
    s=re.sub(r'width="[^"]+"',f'width="{mw}"',s,count=1)
    s=re.sub(r'height="[^"]+"',f'height="{mh}"',s,count=1)
    parts.append(s.replace('<svg ',f'<svg x="{x-mw/2}" y="{y-mh/2}" data-equation="{tag}" ',1))
    equations.append(dict(id=tag,tex=tex,x=x-mw/2,y=y-mh/2,w=mw,h=mh))

def box(name,x,y,w,h,r=0):
    nodes.append(dict(name=name,x=x,y=y,w=w,h=h,kind='rect'))
    parts.append(f'<g data-node="{name}" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="white" stroke="#000" stroke-width="2.2"/>')
def end():parts.append('</g>')
def diamond(name,cx,cy,w,h):
    nodes.append(dict(name=name,x=cx-w/2,y=cy-h/2,w=w,h=h,kind='diamond'))
    parts.append(f'<g data-node="{name}" data-kind="diamond" data-x="{cx-w/2}" data-y="{cy-h/2}" data-w="{w}" data-h="{h}"><path d="M{cx-w/2} {cy} L{cx} {cy-h/2} L{cx+w/2} {cy} L{cx} {cy+h/2}Z" fill="white" stroke="#000" stroke-width="2.2"/>')
def line(points,arrow=True):
    d='M'+' L'.join(f'{x} {y}' for x,y in points)
    parts.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="2.1" stroke-linejoin="miter"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>')

line([(210,110),(210,150)])
line([(210,325),(210,390)],False);line([(210,390),(210,470)])
line([(780,110),(850,110)])
line([(850,210),(800,210),(800,245),(380,245)])
line([(1335,260),(1335,350),(1510,350),(1510,450)])
line([(380,620),(450,620)]);line([(730,620),(810,620)])
line([(590,730),(590,870)])
line([(450,940),(20,940)],False)
line([(1200,620),(1280,620)]);line([(1740,620),(1820,620)])
line([(2105,780),(2105,830)])
line([(2320,940),(2420,940),(2420,1370),(20,1370)],False)
line([(2105,1050),(2105,1090),(1110,1090)],False)
for x in [1110,1580,2050]:line([(x,1090),(x,1130)])
for x in [1110,1580,2050]:line([(x,1295),(x,1320)],False)
line([(2050,1320),(740,1320),(740,1210),(690,1210)])
line([(40,1210),(20,1210)],False)
line([(20,1370),(20,390),(210,390)],False)

box('start',130,40,160,70,r=35);txt(210,75,'开始',38);end()
box('init',40,150,340,175)
txt(210,188,'载入标定参数',36)
math(210,241,r'S_{Q,0}=S_{R,0}=0',42,maxw=310)
txt(210,296,'h = 26（仿真基准）',30);end()

box('healthy',460,40,320,140)
txt(620,84,'独立健康数据',36);txt(620,139,'10 s 不重叠分块',32);end()
box('calibration',850,25,970,235)
txt(1335,65,'标定健康预测流量与稳健尺度',36)
math(1335,143,r'\widehat{Q}_m=g\,a\left(\frac{\bar{P}_{1,m}}{P_{\mathrm{ref}}}\right)^n,\quad n=0.5',50,maxw=920)
txt(1335,222,'健康块给出阻力中位数与两路残差稳健尺度',32);end()

box('sampling',40,470,340,310)
txt(210,510,'1 s 读取压力与计数',34)
math(210,558,r'\Delta P(t),\ P_1(t),\ N(t)',38,maxw=310)
txt(210,608,'10 s 不重叠分块',34)
math(210,676,r'Q_m=\frac{60\,\Delta N_m}{\kappa\,T_b}',48,maxw=310)
txt(210,744,'压力取块内均值',32);end()

diamond('quality',590,620,280,220)
txt(590,598,'数据有效且',28);txt(590,642,'参照适用？',28);end()
txt(770,593,'是',34);txt(627,798,'否',34)
box('invalid',450,870,280,140)
txt(590,912,'记录不可用状态',32);txt(590,968,'本块不参与累积',32);end()

box('features',810,450,390,340)
txt(1005,492,'块级水力特征',36)
math(1005,588,r'K_m=\frac{Q_m}{\sqrt{\bar{P}_{1,m}}}',52,maxw=350)
math(1005,718,r'R_{\mathrm{h},m}=\frac{\overline{\Delta P}_m}{Q_m^2}',52,maxw=350);end()

box('residuals',1280,450,460,340)
txt(1510,492,'双通道残差标准化',36)
math(1510,590,r'z_{Q,m}=\frac{Q_m/\widehat{Q}_m-1}{s_Q}',52,maxw=420)
math(1510,718,r'z_{R,m}=\frac{R_{\mathrm{h},m}-R_0}{s_R}',52,maxw=420);end()

box('cusum',1820,470,570,310)
txt(2105,515,'双通道 CUSUM 递推',36)
math(2105,586,r'S_{j,m}=\max\left\{0,\ S_{j,m-1}+z_{j,m}-k\right\}',40,maxw=535)
math(2105,655,r'j\in\{Q,R\},\qquad k=0.5',44,maxw=535)
txt(2105,741,'每个数据块更新一次',34);end()

diamond('threshold',2105,940,430,220)
txt(2105,903,'累积值越限？',30)
math(2105,957,r'\max_j\,S_{j,m}>h',42,maxw=260);end()
txt(2368,908,'否',34);txt(2146,1080,'是',34)

for name,x,title,condition,detail in [
 ('leak',910,'等效泄漏候选',r'S_{Q,m}>h,\quad S_{R,m}\leq h','核查附加出流'),
 ('restriction',1380,'局部受限候选',r'S_{Q,m}\leq h,\quad S_{R,m}>h','核查测点区段阻力'),
 ('both',1850,'双通道异常候选',r'S_{Q,m}>h,\quad S_{R,m}>h','结合工况综合核查')]:
    box(name,x,1130,400,165)
    math(x+200,1165,condition,37,maxw=365)
    txt(x+200,1214,title,34);txt(x+200,1260,detail,30);end()

box('event',40,1130,650,165)
txt(365,1181,'保存事件、测量质量与参照版本',34)
txt(365,1246,'LoRa 上报，人工核查与同工况复测',32);end()
txt(1280,1350,'未越限：继续下一块',30)

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title"><title id="title">支管故障块CUSUM诊断流程——横版大字清晰版</title><defs><marker id="arrow" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L12 6 L0 12Z" fill="#000"/></marker></defs><rect width="{W}" height="{H}" fill="white"/><g fill="#000">{''.join(parts)}</g></svg>'''
(OUT/'块CUSUM诊断流程_大字清晰版.svg').write_text(svg,encoding='utf-8')
(OUT/'绘图信息.json').write_text(json.dumps(dict(width=W,height=H,nodes=nodes,equations=equations),ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT)
