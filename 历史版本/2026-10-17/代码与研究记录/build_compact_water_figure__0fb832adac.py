"""Rearrange the water schematic for print; preserve all labels and topology."""
from pathlib import Path
from collections import Counter
from lxml import etree as ET
import json,hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/figures/compact_layout'; OUT.mkdir(parents=True,exist_ok=True)
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="510" viewBox="0 0 1000 510"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L7 4 L0 8 Z" fill="black"/></marker></defs><rect width="1000" height="510" fill="white"/><g font-family="Microsoft YaHei, SimSun, sans-serif" fill="black">']
def label(x,y,s,size=25,bold=False,anchor='middle'):
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{s}</text>')
def line(points,color='black',arrow=False):
    d='M'+' L'.join(f'{x} {y}' for x,y in points)
    parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
def box(x,y,w,h,lines,fill='white',stroke='black'):
    parts.append(f'<g data-kind="box" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    for i,s in enumerate(lines): label(x+w/2,y+h/2+(i-(len(lines)-1)/2)*37+8.5,s,25 if i==0 else 24,i==0)
    parts.append('</g>')
def circle(x,y,s):
    parts.append(f'<circle cx="{x}" cy="{y}" r="26" fill="white" stroke="black" stroke-width="2"/>');label(x,y+8,s,24,True)

blue='#42657b'; brown='#a26437'
# Shared source, monitored A path, and a distinct healthy B disturbance path.
line([(175,145),(215,145),(215,130),(875,130)],blue)
line([(215,145),(215,297),(875,297)],blue)
line([(330,130),(330,88)]); line([(600,130),(600,88)])
line([(690,130),(690,202)],brown)
line([(765,228),(790,228)],arrow=True)
line([(975,130),(995,130),(995,400),(285,400)],arrow=True)
line([(975,297),(995,297)])
box(25,105,150,80,['可调供水','工作点待核'],'#eaf2f8')
circle(330,60,'P0');circle(600,60,'P1')
box(390,104,140,52,['区段R'],'#fbf1db')
circle(255,130,'Q')
label(255,96,'流量计',24)
box(815,104,160,52,['A负载 Cₙ'],'#edf4ed')
box(615,202,150,52,['泄漏球阀'],'#faede2')
box(790,202,185,52,['独立收集计时'],'#faede2',brown)
box(350,271,140,52,['B切换阀'])
box(815,271,160,52,['B正常负载'],'#edf4ed')
box(25,373,260,54,['正常回水至水源'])
label(570,352,'B仅模拟正常负载切换',24)
label(305,386,'Q计入A正常负载与泄漏总量',24,anchor='start')
label(24,456,'安装顺序：流量计 → 取压嘴A → 区段R → 取压嘴B → 泄漏球阀，不可调换。',24,anchor='start')
label(24,492,'两个取压嘴都在流量计下游；泄漏先独立计量，再人工回水。',24,anchor='start')
parts.append('</g></svg>')
svg=''.join(parts); dest=OUT/'water_layout.svg';dest.write_text(svg,encoding='utf-8',newline='\n')
ns={'s':'http://www.w3.org/2000/svg'}
expect={'可调供水','工作点待核','P0','P1','Q','流量计','区段R','A负载 Cₙ','泄漏球阀','独立收集计时','B切换阀','B正常负载','正常回水至水源','B仅模拟正常负载切换','Q计入A正常负载与泄漏总量','安装顺序：流量计 → 取压嘴A → 区段R → 取压嘴B → 泄漏球阀，不可调换。','两个取压嘴都在流量计下游；泄漏先独立计量，再人工回水。'}
texts=lambda p:Counter(ET.parse(str(p)).xpath('//s:text/text()',namespaces=ns))
assert texts(dest)==Counter(expect),'A diagram label changed'
# Use the established browser capture/checker with isolated input/output paths.
scratch=ROOT/'tmp/compact_layout_review';scratch.mkdir(parents=True,exist_ok=True)
record={'figures':[{'name':'water_layout','svg':dest.relative_to(ROOT).as_posix()}]}
(scratch/'figure_input.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
js=(ROOT/'scripts/verify_quality_visuals.mjs').read_text(encoding='utf-8')
js=js.replace("out=path.join(root,'application/figures/quality_review')","out=path.join(root,'application/figures/compact_layout')")
js=js.replace("scratch=path.join(root,'tmp/quality_visuals')","scratch=path.join(root,'tmp/compact_water_figure')")
js=js.replace("'simulation/quality_review/figure_sources.json'","'tmp/compact_layout_review/figure_input.json'")
js=js.replace("'simulation/quality_review/figure_checks.json'","'tmp/compact_layout_review/figure_checks.json'")
js=js.replace('textCount:texts.length,minFontPt:', '''textCount:texts.length,
overlappingLabels:texts.flatMap((a,i)=>texts.slice(i+1).filter(b=>Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>.5&&Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>.5).map(b=>[a.text,b.text])),
labelsOutsideOwnBox:[...s.querySelectorAll('[data-kind="box"]')].flatMap(g=>{const b=g.querySelector('rect').getBBox();return [...g.querySelectorAll('text')].filter(e=>{const t=e.getBBox();return t.x<b.x+2||t.y<b.y+2||t.x+t.width>b.x+b.width-2||t.y+t.height>b.y+b.height-2}).map(e=>e.textContent)}),
guideLabelsOverBoxes:[...s.querySelectorAll('text')].filter(e=>!e.closest('[data-kind="box"]')).flatMap(e=>{const t=e.getBBox();return [...s.querySelectorAll('[data-kind="box"] rect')].filter(r=>{const b=r.getBBox();return Math.min(t.x+t.width,b.x+b.width)-Math.max(t.x,b.x)>.5&&Math.min(t.y+t.height,b.y+b.height)-Math.max(t.y,b.y)>.5}).map(()=>e.textContent)}),
minFontPt:''')
js=js.replace('if(checks.outside.length||checks.minFontPt<9.5)', 'if(checks.outside.length||checks.minFontPt<9.5||checks.overlappingLabels.length||checks.labelsOutsideOwnBox.length||checks.guideLabelsOverBoxes.length)')
js=js.replace('JSON.stringify(checks.outside)', 'JSON.stringify(checks)')
(ROOT/'scripts/verify_compact_water_figure.mjs').write_text(js,encoding='utf-8',newline='\n')
print('Water schematic: all original labels retained; A total-flow split and healthy B path unchanged; 470px high, same 1000px width and font sizes.')
