"""Purposeful visual revision; every graphic is a concept or recorded simulation.

Native SVG objects, truthful scenario data, no borrowed prototype photographs.
"""
from pathlib import Path
from html import escape
import json,math,sys
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'projects/drip-research_ppt169_20261002'
deck=json.loads((P/'analysis/deck_content.json').read_text(encoding='utf-8'))
diag=json.loads((ROOT/'simulation/diagnosis_results/summary.json').read_text(encoding='utf-8'))
comm=json.loads((ROOT/'simulation/communication_results/summary.json').read_text(encoding='utf-8'))
G='#164C45';D='#092E2B';S='#EEF3EF';W='#FAF9F5';T='#20332F';M='#556762';L='#C7D2CB'
A='#B4512B';B='#426B91';C='#78DFC5';Y='#F3C77B';F='Microsoft YaHei, Arial'
def txt(x,y,s,size=24,color=T,bold=False,anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="{F}" font-size="{size}" fill="{color}" text-anchor="{anchor}"'+(' font-weight="bold"' if bold else '')+'>'+escape(str(s))+'</text>'
def para(x,y,s,width,size=24,color=T,bold=False,leading=None):
    lines=[];word='';used=0
    for ch in s:
        advance=size*(1.10 if ord(ch)>127 else .62)
        if ch=='\n' or used+advance>width:
            if word:lines.append(word)
            word='';used=0
            if ch=='\n':continue
        word+=ch;used+=advance
    if word:lines.append(word)
    lead=leading or round(size*1.45)
    return f'<text x="{x}" y="{y}" font-family="{F}" font-size="{size}" fill="{color}"'+(' font-weight="bold"' if bold else '')+'>'+escape(lines[0])+''.join(f'<tspan x="{x}" dy="{lead}">{escape(v)}</tspan>' for v in lines[1:])+'</text>'
def box(x,y,w,h,fill=S,stroke='none',r=0):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
def ln(x,y,X,Z,color=L,width=2,dash=None):return f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Z}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def circ(x,y,r,fill=G,stroke='none',sw=2):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def poly(points,fill,stroke='none',sw=1):return '<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def grp(key,x,y,w,h,v):return f'<g id="{key}" data-pptx-bounds="{x} {y} {w} {h}">{v}</g>'
def arrow(x,y,X,Z,color=G,width=2):
    theta=math.atan2(Z-y,X-x);a=11
    return ln(x,y,X,Z,color,width)+poly([(X,Z),(X-a*math.cos(theta-.45),Z-a*math.sin(theta-.45)),(X-a*math.cos(theta+.45),Z-a*math.sin(theta+.45))],color)
def tag(x,y,s,color=G,dark=False,width=None):
    w=width or len(s)*18+26
    return box(x,y,w,31,D if dark else S,r=4)+txt(x+13,y+22,s,18,color)

sources={1:'方案场景示意 · 文献、未标定模型与合成回放 · 暂无实物或田间数据',2:'研究对象：下游等效泄漏、支管等效受限；正常供压及切换为对照',3:'文献：AWM 2022 / HydroNeuro 2026 / Land 2026 / Sensors 2021 / IFAC 2025',4:'拟交付系统 · 1节点 / 1接收端 / 1台架 / 本地Web；扩节点按资源开展',5:'集中等效水力模型，非台架实物；健康压降与差压不确定度须标定',6:'未标定合成模型 · 种子10300 · 各压力点噪声σ0.3kPa · 非实物性能',7:'旧单压力模型回放 · 同检测/ACK · 非射频实测；未与新诊断端到端集成',8:'6场景 × 4噪声 × 20种子 = 480次合成试验；重复种子不是独立实物实验',9:'合成回放界面示意，按当前网站功能重绘；设备接入与日志持久化为拟实施',10:'实验数量与供压为设计网格，实际范围须按仪器/水路条件核定',11:'2000元为启动额度估计，非报价或已获资助；论文费用另核查',12:'研究目标由实验兑现；立项级别、论文发表及推免认定均不保证',13:'旧单点反例及双点模型；原因可辨识性依赖布点、操作信息与测量质量',14:'当前重点：申报；结项及论文按后续真实数据和批准任务书推进',15:'完整链接与原始合成数据见仓库、协议及证据清单'}
darkpages={1,2,4,8,12}
def frame(i):
    dark=i in darkpages;bg=D if dark else W;fg='#FFFFFF' if dark else G;muted='#B7CCC6' if dark else M
    role='cover' if i==1 else 'ending' if i==12 else 'content'
    v=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" data-pptx-page-role="{role}">'
    v+='<defs><linearGradient id="deep-field" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#164C45"/><stop offset="100%" stop-color="#092E2B"/></linearGradient></defs>'
    v+=box(0,0,1280,720,'url(#deep-field)' if dark else bg).replace('<rect ','<rect id="page-background" data-pptx-role="background" ',1)
    v+=box(48,35,8,19,C if dark else G).replace('<rect ','<rect id="header-mark" data-pptx-role="decoration" ',1)+f'<text id="page-kicker" data-pptx-role="header" x="68" y="51" font-family="{F}" font-size="16" fill="{muted}">滴智卫 / 创新训练申报</text>'
    active=0 if i<=3 else 1 if i in (4,5,9) else 2 if i in (6,7,8,13,15) else 3
    for j,s in enumerate(['场景','系统','证据','实施']):
        if j==active:v+=box(865+j*83,27,65,31,'#23554E' if dark else S,r=4).replace('<rect ','<rect id="route-highlight" data-pptx-role="decoration" ',1)
        v+=f'<text id="page-route-{j}" data-pptx-role="header" x="{878+j*83}" y="49" font-family="{F}" font-size="16" fill="{C if dark and j==active else fg if j==active else muted}">'+s+'</text>'
    if i!=1:v+=grp('page-title',48,82,1184,78,txt(48,126,deck[i-1]['title'],42,fg,True))
    v+=f'<text id="source-footer" data-pptx-role="footer" x="48" y="686" font-family="{F}" font-size="16" fill="{muted}">'+escape(sources[i])+'</text>'
    v+=f'<text id="page-number" data-pptx-role="page-number" x="1232" y="686" text-anchor="end" font-family="{F}" font-size="16" fill="{muted}">{i:02}/15</text>'
    return v

def field_scene(x,y,w,h,dark=True):
    """An isometric irrigation plan, not a photorealistic farm or fabricated CAD."""
    # Coordinate projection keeps each depicted branch parallel on one plane.
    def point(u,v):return x+w*(.07+.77*u+.18*v),y+h*(.18+.56*v-.14*u)
    v='';plane=[point(0,0),point(1,0),point(1,1),point(0,1)]
    v+=poly([(X,Z+19) for X,Z in plane],'#103B35')+poly(plane,'#215749','#437966',2)
    for row in [.12,.25,.38,.51,.64,.77,.90]:
        a=point(.03,row);b=point(.96,row);v+=ln(*a,*b,'#4F8165',5)
        for u in [.10,.22,.34,.46,.58,.70,.82,.94]:
            X,Z=point(u,row);v+=circ(X,Z-4,3.4,'#8EAF7A')
    a=point(.04,.08);b=point(.04,.94);v+=ln(*a,*b,C,7)
    for row in [.25,.51,.77]:
        a=point(.04,row);b=point(.96,row);v+=ln(*a,*b,C,3)
    for u,label,col in [(.18,'P0',C),(.43,'P1',C),(.64,'Q',Y)]:
        X,Z=point(u,.51)
        v+=ln(X,Z,X,Z-38,col,2)+circ(X,Z-53,17,D,col)+txt(X,Z-47,label,18,col,False,'middle')
    X,Z=point(.30,.51);v+=box(X-9,Z-7,18,14,Y)
    X,Z=point(.79,.51);v+=ln(X,Z,X+10,Z+47,Y,3)+ln(X+10,Z+47,X+36,Z+47,Y,3)
    # Node and gateway above the field are connected as a design relationship.
    xx=x+w*.61;yy=y+h*.78
    v+=box(xx,yy,123,78,'#E7F2EA',r=6)+box(xx+10,yy+10,70,36,G,r=3)
    v+=circ(xx+99,yy+19,5,C)+ln(xx+20,yy,xx+20,yy-23,C,3)
    v+=txt(xx+13,yy+67,'感知节点',16,G)
    X,Z=point(.43,.51);v+=ln(X,Z+7,xx+16,yy,C,2,'6,5')
    gx=x+w*.83;gy=y+h*.18
    v+=box(gx,gy,83,96,'#CFDED7',r=6)+box(gx+15,gy+20,53,36,G,r=3)
    v+=ln(gx+22,gy,gx+22,gy-31,C,3)+ln(gx+63,gy,gx+63,gy-31,C,3)
    v+=circ(gx+41,gy+73,5,G)+txt(gx+41,gy+127,'LoRa接收',18,'#E7F2EA' if dark else G,False,'middle')
    v+=ln(xx+118,yy+4,gx+35,gy+95,C,2,'7,6')
    return v

def icon_node(x,y,color):
    return box(x,y,54,44,'none',color,5)+box(x+11,y+10,24,22,'none',color)+ln(x+45,y+3,x+45,y-16,color,2)+circ(x+44,y+30,3,color)
def icon_signal(x,y,color):
    return ln(x+25,y+12,x+25,y+43,color,3)+circ(x+25,y+6,5,color)+ln(x+11,y+15,x+5,y+27,color,3)+ln(x+39,y+15,x+45,y+27,color,3)+ln(x+6,y+8,x-4,y+28,color,2)+ln(x+44,y+8,x+54,y+28,color,2)
def icon_diagnosis(x,y,color):
    return ln(x+8,y+20,x+45,y+5,color,2)+ln(x+8,y+20,x+45,y+36,color,2)+circ(x+8,y+20,6,'none',color)+circ(x+45,y+5,6,'none',color)+circ(x+45,y+36,6,'none',color)
def screen(x,y,w,h,dark=False):
    """Draw UI from the actual diagnostic trace, expressly a synthetic replay."""
    q=diag['traces']['leak_0.3'];time=450
    v=box(x,y,w,h,'#FFFFFF',L,9)+box(x,y,w,38,'#F0F4F1')
    v+=circ(x+17,y+19,4,'#DBA897')+circ(x+31,y+19,4,Y)+circ(x+45,y+19,4,C)
    v+=txt(x+65,y+25,'滴智卫 / 双点诊断回放',16,G)
    v+=box(x,y+38,127,h-38,G)+txt(x+15,y+74,'设计演示',20,'#FFFFFF',True)
    for j,label in enumerate(['研究目标','双点诊断','历史反例','通信对照','执行路线']):
        if j==1:v+=box(x+9,y+105+j*40,108,30,'#2C6259',r=4)
        v+=txt(x+18,y+125+j*40,label,16,'#EEF3EF')
    xx=x+146;yy=y+64
    v+=txt(xx,yy,'下游等效泄漏 · 合成回放',24,G,True)
    v+=tag(xx,yy+13,'σ0.3kPa / 450s',G,width=187)+tag(xx+198,yy+13,'未接入设备',A,width=136)
    # Use the exact stored underlying hydraulic values; they are not live sensor data.
    for j,(label,value,unit) in enumerate([('P0',q['p0'][time],'kPa'),('P1',q['p1'][time],'kPa'),('Q',q['q'][time],'L/min')]):
        bx=xx+j*137;v+=box(bx,yy+58,125,76,S,r=4)+txt(bx+10,yy+81,label,18,M)+txt(bx+10,yy+112,f'{value:.2f}',24,G,True)+txt(bx+117,yy+81,unit,16,M,False,'end')
    px=xx+32;py=yy+161;pw=w-219;ph=115
    for a in [0,15,30]:v+=ln(px,py+ph-a/30*ph,px+pw,py+ph-a/30*ph,'#DEE7E0',1)+txt(px-9,py+ph-a/30*ph+5,a,16,M,False,'end')
    pts=' '.join(f'{px+j/600*pw:.2f},{py+ph-q["severity"][j]*100/30*ph:.2f}' for j in range(0,601,5))
    v+=f'<polyline points="{pts}" fill="none" stroke="{A}" stroke-width="3"/>'
    v+=ln(px,py+ph/2,px+pw,py+ph/2,B,1,'5,5')+txt(px,py-10,'相对健康流量偏离 / %',16,M)
    v+=txt(px+pw,py+ph/2-9,'15%演示判据',16,B,False,'end')
    cursor=px+time/600*pw
    v+=ln(cursor,py,cursor,py+ph,M,1,'3,4')+txt(cursor,py+ph+26,f'{time}s',16,M,False,'middle')
    v+=txt(px,py+ph+26,'0s',16,M)+txt(px+pw,py+ph+26,'600s',16,M,False,'end')
    v+=box(xx,yy+313,w-173,68,'#F6ECE6',r=4)+txt(xx+12,yy+338,'候选输出：等效泄漏模式',24,A,True)
    v+=txt(xx+12,yy+363,'查看证据 → 管理确认（当前为页面演示）',16,M)
    return v

def severity_chart():
    key='pressure-response';x=48;y=215;w=784;h=333;px=99;py=253;pw=707;ph=234
    xs=list(range(330,601,5));series=[]
    for kind,label in [('leak','渐进等效泄漏'),('restriction','渐进等效受限')]:series.append({'name':label,'x':xs,'y':[diag['traces'][kind+'_0.3']['severity'][j]*100 for j in xs]})
    series.append({'name':'演示失效判据15%','x':xs,'y':[15.]*len(xs)})
    meta={'name':key,'x':x,'y':y,'width':w,'height':h,'plot_area':{'x':px,'y':py,'width':pw,'height':ph},'type':'scatter','scatter_style':'line','series':series,'show_legend':False,'axes':{'x':{'minimum':330,'maximum':600,'major_unit':45,'major_gridlines':False},'y':{'minimum':0,'maximum':30,'major_unit':6,'major_gridlines':True}},'style':{'colors':[A,G,B],'font_family':F,'axis_font_size':18,'text_color':M,'axis_color':M,'grid_color':'#E0E7E2'}}
    v=f'<g id="{key}" data-pptx-replace-with="chart" data-pptx-bounds="{x} {y} {w} {h}"><metadata type="application/json">'+escape(json.dumps(meta,ensure_ascii=False))+'</metadata>'
    v+=f'<g id="{key}-chartArea"><!-- chart-plot-area: object={key} | x_min={px} | y_min={py} | x_max={px+pw} | y_max={py+ph} -->'
    for val in [0,6,12,18,24,30]:
        yy=py+ph-val/30*ph;v+=ln(px,yy,px+pw,yy,'#E0E7E2',1)+txt(px-15,yy+6,val,18,M,False,'end')
    for val in [330,375,420,465,510,555,600]:v+=txt(px+(val-330)/270*pw,py+ph+27,val,18,M,False,'middle')
    v+=ln(px,py,px,py+ph,M,1).replace('<line ','<line id="pressure-axis-y" ',1)+ln(px,py+ph,px+pw,py+ph,M,1).replace('<line ','<line id="pressure-axis-x" ',1)
    for sr,col in zip(series,[A,G,B]):
        pts=' '.join(f'{px+(t-330)/270*pw:.3f},{py+ph-vv/30*ph:.3f}' for t,vv in zip(sr['x'],sr['y']))
        v+=f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>'
    v+='</g></g>'
    # Outside the native chart object: these are trace-specific evaluation annotations.
    annotations=''
    for kind,col,label,offset,label_y in [('leak',A,'泄漏',85,py+58),('restriction',G,'受限',-65,py+145)]:
        tr=diag['traces'][kind+'_0.3'];ts=tr['detected_s'];tc=tr['critical_s'];X=lambda t:px+(t-330)/270*pw
        yy=py+ph-tr['severity_at_detection']*100/30*ph
        annotations+=circ(X(ts),yy,6,W,col,3)+ln(X(ts),yy,X(ts)+offset,label_y+10,col,1.5)+txt(X(ts)+offset,label_y,f'{label}提示 {ts}s',18,col,False,'middle')
        annotations+=ln(X(tc),py+ph/2-10,X(tc),py+ph/2+10,col,3)
    annotations+=txt(99,231,'流量偏离 / %',18,M)+txt(807,541,'模型时间 / s',18,M,False,'end')
    return grp('early-plot',48,215,784,333,v+'<g id="early-evaluation">'+annotations+'</g>')

def scatter(key,case,x,y,w,h):
    rows=[r for r in comm['summary'] if r['case']==case and r['loss']==.1]
    xmax=100 if case=='normal' else 600;ymax=1.5 if case=='normal' else 2.5
    px=x+57;py=y+26;pw=w-86;ph=h-66
    X=lambda a:px+a/xmax*pw;Yv=lambda a:py+ph-a/ymax*ph
    names=['周期10s','周期30s','原始事件','滤波限频事件'];cols=[G,B,A,'#83639B']
    meta={'name':key,'type':'scatter','scatter_style':'marker','x':x,'y':y,'width':w,'height':h,'plot_area':{'x':px,'y':py,'width':pw,'height':ph},'series':[{'name':n,'x':[r['frames_mean']],'y':[r['pressure_mae']]} for r,n in zip(rows,names)],'show_legend':False,'axes':{'x':{'minimum':0,'maximum':xmax,'major_unit':xmax/4,'major_gridlines':False},'y':{'minimum':0,'maximum':ymax,'major_unit':ymax/5,'major_gridlines':True,'number_format':'0.0'}},'notes':[{'text':n,'width':150,'font_size':18,'color':c} for n,c in zip(names,cols)],'style':{'colors':cols,'font_family':F,'axis_font_size':18,'text_color':M,'axis_color':M,'grid_color':'#E0E7E2'}}
    v=f'<g id="{key}" data-pptx-replace-with="chart" data-pptx-bounds="{x} {y} {w} {h}"><metadata type="application/json">'+escape(json.dumps(meta,ensure_ascii=False))+'</metadata>'
    v+=f'<g id="{key}-chartArea"><!-- chart-plot-area: object={key} | x_min={px} | y_min={py} | x_max={px+pw} | y_max={py+ph} -->'
    for j in range(6):
        val=j*ymax/5;yy=Yv(val);v+=ln(px,yy,px+pw,yy,'#E0E7E2',1)+txt(px-12,yy+6,f'{val:.1f}',18,M,False,'end')
    for j in range(5):v+=txt(X(j*xmax/4),py+ph+26,f'{j*xmax/4:g}',18,M,False,'middle')
    v+=ln(px,py,px,py+ph,M,1).replace('<line ',f'<line id="{key}-axis-y" ',1)+ln(px,py+ph,px+pw,py+ph,M,1).replace('<line ',f'<line id="{key}-axis-x" ',1)
    offsets=[(10,-15),(12,-14),(10,27),(12,-18)] if case=='normal' else [(20,-7),(12,-14),(-107,-17),(12,43)]
    for r,n,col,(dx,dy) in zip(rows,names,cols,offsets):v+=circ(round(X(r['frames_mean']),3),round(Yv(r['pressure_mae']),3),6,col)+txt(round(X(r['frames_mean'])+dx,3),round(Yv(r['pressure_mae'])+dy,3),n,18,col)
    return v+'</g></g>'

def authored(i):
    out=frame(i);v='';dark=i in darkpages;fg='#FFFFFF' if dark else T;muted='#B7CCC6' if dark else M
    print(f'P{i:02} modules: core, structure'+(', chart, native-data' if i in (6,7) else ', formula' if i==5 else ', constructed-field' if i in (1,2) else ''))
    if i==1:
        v+=tag(48,118,'南疆滴灌 / 研究原型',C,True,239)
        v+=txt(48,236,'滴智卫',72,'#FFFFFF',True)
        v+=para(48,317,'南疆滴灌支管\n早期故障诊断',520,42,'#FFFFFF',True,61)
        v+=para(48,434,'基于 LoRa 的物联网原型系统',496,24,C)
        v+=ln(48,470,508,470,'#40736A',1)
        v+=txt(48,517,'2027.03—2028.02',28,Y,True)
        v+=txt(48,558,'测量建模 / 有限诊断 / 可靠告警 / 管理确认',20,'#D8EAE2')
        v+=para(48,606,'已有基础：文献、未标定模型与合成回放\n实物、台架及田间实验尚未开展',490,18,'#B7CCC6')
        out+=grp('cover-message',48,110,510,540,v)
        out+=grp('cover-field',566,184,665,447,field_scene(566,184,640,438)+txt(873,617,'方案概念模型 · 非现场照片',18,C,False,'middle'))
    elif i==2:
        v+=field_scene(48,238,697,371)
        v+=tag(48,173,'管理需求：哪里 / 为什么 / 何时',C,True,376)
        v+=txt(48,635,'定位到监测支管或区段，保留可检查的证据。',24,'#FFFFFF')
        out+=grp('field-problem',48,163,700,481,v);v=''
        entries=[('01','正常变化','供压调整 / 支路切换',C),('02','等效泄漏','下游负载或旁路增加',Y),('03','等效受限','监测区段水力阻力增加',Y)]
        for j,(n,title,body,col) in enumerate(entries):
            yy=183+j*137;v+=ln(793,yy+6,793,yy+91,col,4)+txt(813,yy+23,n,20,col)+txt(858,yy+28,title,28,'#FFFFFF',True)+txt(813,yy+71,body,20,'#D8EAE2')
        v+=para(793,611,'漂移、未知操作与切换期短时异常\n检验误报及原因混淆',431,18,'#B7CCC6')
        out+=grp('normal-fault-states',786,170,446,485,v)
    elif i==3:
        entries=[('间接检测','堵塞综述 / AWM 2022','压力/流量未必反映最初堵塞','检验低成本测点的早期边界'),('状态建模','HydroNeuro / Sensors 2026','阀态建模与嵌入式感知已有先例','比较单/双点及工况信息作用'),('可靠通信','Land 2026 / Sensors / IFAC','灌溉物联网与事件通信已有研究','同检测与确认下评价可靠取舍')]
        v+=txt(48,194,'已有工作',20,M)+txt(737,194,'拟研究增量（须独立实验验证）',20,G,True)
        for j,(title,cite,known,new) in enumerate(entries):
            yy=217+j*126;v+=box(48,yy,657,105,S,r=6)+txt(70,yy+34,title,28,G,True)+txt(70,yy+78,cite,16,M)+para(321,yy+42,known,361,20,T)
            v+=arrow(708,yy+51,733,yy+51,G)+txt(751,yy+39,new,24,G,True)+txt(751,yy+78,['真实程度标签 / 提前量 / 误报','强基线 / 漂移挑战 / 消融','真实链路 / 两段延迟 / 整机能量'][j],20,M)
        v+=box(48,617,1184,33,G,r=4)+txt(67,641,'使用LoRa、增加压力点、建立平台均不自动构成创新。',20,'#FFFFFF')
        out+=grp('prior-work-increment',48,174,1184,481,v)
    elif i==4:
        entries=[('WP1','测量与建模','P0 / P1 / Q','参考标定','误差与程度',C),('WP2','诊断与边界','渐进故障','强基线 / 状态','误报与提前量',Y),('WP3','可靠告警','周期 / 事件','缓存 / ACK','真实延迟与能量',C),('WP4','系统与验证','节点 / 软件','台架 / 独立批次','数据与报告',Y)]
        for j,(wp,title,a,b,c,col) in enumerate(entries):
            xx=48+j*307;v+=box(xx,199,263,355,'#164C45',r=8)+box(xx,199,263,5,col)
            v+=txt(xx+21,243,wp,24,col,True)+txt(xx+21,295,title,30,'#FFFFFF',True)
            v+=(icon_node(xx+24,330,col) if j in (0,3) else icon_diagnosis(xx+25,333,col) if j==1 else icon_signal(xx+25,333,col))
            v+=txt(xx+21,425,a,24,'#FFFFFF')+txt(xx+21,474,b,20,'#D8EAE2')+txt(xx+21,514,c,20,'#D8EAE2')
            if j<3:v+=arrow(xx+268,380,xx+301,380,'#78DFC5',2)
        v+=txt(48,607,'闭环：采集 → 有限诊断 → 可靠送达 → 管理确认与回放',28,C,True)
        v+=txt(48,642,'两条研究线：可辨识与早期边界；同诊断下的通信取舍。',20,'#D8EAE2')
        out+=grp('layered-system',48,180,1184,477,v)
    elif i==5:
        v+=box(48,180,1184,270,'#FFFFFF',L,8)
        # Pipe strokes sit behind symbol surfaces and labels.
        for a in [(86,294,304,294),(304,253,304,388),(304,253,1150,253),(304,388,1150,388)]:v+=ln(*a,G,6)
        v+=box(87,265,128,58,S,G,6)+txt(151,300,'共同供水',20,G,False,'middle')
        v+=box(474,231,91,44,'#F6ECE6',A,5)+txt(519,259,'受限元件',18,A,False,'middle')
        for xx,label in [(393,'P0'),(676,'P1'),(838,'Q')]:v+=circ(xx,253,25,W,G,3)+txt(xx,260,label,20,G,True,'middle')
        v+=txt(393,208,'区段入口',18,M,False,'middle')+txt(676,208,'受限下游',18,M,False,'middle')+txt(838,208,'支管总流量',18,M,False,'middle')
        v+=ln(941,253,941,321,A,3)+ln(941,321,1103,321,A,3)+txt(1114,329,'泄漏',18,A)
        v+=box(1065,232,97,42,S,r=4)+txt(1113,260,'A负载',18,G,False,'middle')
        v+=box(543,367,109,42,S,G,4)+txt(597,396,'切换阀',18,G,False,'middle')
        v+=box(1065,367,97,42,S,r=4)+txt(1113,396,'B负载',18,G,False,'middle')
        v+=txt(86,433,'P0/P1包围目标受限区段；Q包含负载与泄漏旁路总流量。',20,G)
        out+=grp('measurement-layout',48,175,1184,281,v);v=''
        for j,(label,body) in enumerate([('负载特征 K','Q / √P1'),('阻力特征 R估计','(P0 − P1) / Q²')]):
            xx=48+j*414;v+=box(xx,480,391,115,S,r=6)+txt(xx+20,513,label,20,G,True)+txt(xx+20,559,body,28,G)
        v+=box(876,480,356,115,'#F6ECE6',r=6)+txt(896,513,'诊断成立条件',20,A,True)+para(896,549,'已知操作 / 参考标定\n未知负载与漂移仍可能混淆',315,20,T)
        v+=f'<text x="48" y="639" font-family="{F}" font-size="24" fill="{G}">负载假设：<tspan data-pptx-inline-formula="Q=C\\sqrt{{P_1}}">Q = C√P₁</tspan></text>'
        v+=txt(498,639,'压降假设：P0 − P1 = R·Q²',24,G)
        out+=grp('diagnostic-features',48,475,1184,180,v)
    elif i==6:
        v+=tag(48,170,'合成模型 / 单次记录示例',G,width=277)
        v+=ln(382,187,408,187,A,4)+txt(419,193,'泄漏',20,A)+ln(511,187,537,187,G,4)+txt(548,193,'受限',20,G)+ln(645,187,671,187,B,3)+txt(682,193,'15%判据',20,B)
        out+=grp('early-legend',48,164,784,43,v)+severity_chart();v=''
        for j,(kind,label,col) in enumerate([('leak','等效泄漏',A),('restriction','等效受限',G)]):
            tr=diag['traces'][kind+'_0.3'];yy=190+j*189
            v+=box(870,yy,362,171,'#F6ECE6' if j==0 else S,r=8)+txt(894,yy+34,label,24,col,True)+txt(894,yy+109,tr['lead_s'],64,col,True)+txt(1021,yy+103,'s 提前量',24,col)
            v+=txt(894,yy+145,f"提示 {tr['detected_s']}s → 判据 {tr['critical_s']}s",20,M)
        v+=para(870,602,'示例值，非实物性能\n20种子中位数另报；判据须实测冻结',352,18,M)
        out+=grp('early-lead-intervals',865,185,367,468,v)
        out+=grp('early-definition',48,580,784,74,para(48,603,'正确提示发生在失效判据前，且没有前期误报。\n15%仅演示；故障→本地提示→远端接收分别评价。',770,20,T))
    elif i==7:
        v=txt(48,184,'匹配对照：同检测、滤波载荷与告警确认；10%随机丢包 + 15s全丢包',20,M)
        v+=box(48,213,572,325,'#FFFFFF',L,8)+box(660,213,572,325,'#FFFFFF',L,8)
        v+=txt(68,246,'正常轮灌',24,G,True)+txt(327,246,'误差 / kPa',18,M)+txt(680,246,'较大噪声',24,G,True)+txt(947,246,'误差 / kPa',18,M)
        out+=grp('tradeoff-panels',48,162,1184,381,v+scatter('normal-tradeoff','normal',59,257,550,269)+scatter('noise-tradeoff','noise',671,257,550,269))
        v=box(48,562,1184,88,S,r=6)+txt(70,594,'少发帧可能增加误差；慢周期也有竞争力。',28,G,True)
        v+=txt(70,628,'横轴：上行+ACK帧（含尾段）；MAE相对模拟滤波量，首次接收前另报覆盖。',20,M)
        out+=grp('communication-result',48,553,1184,104,v)
    elif i==8:
        v+=txt(48,258,'12/20',72,Y,True)+txt(48,302,'大噪声下正确提前发现',28,'#FFFFFF',True)
        v+=para(48,350,'两类故障均如此\n压力点噪声σ10kPa\n20个模拟种子，非实物识别率',406,24,'#D8EAE2')
        v+=ln(48,466,451,466,'#46766B',1)+para(48,511,'保留失败记录，\n据实确定方法的增量。',406,30,C,True)
        out+=grp('noise-boundary',48,175,420,472,v);v=''
        for j,(title,body) in enumerate([('压力漂移','入口压力漂移可误判为局部受限。'),('未知负载','正常负载增大可与等效泄漏同形。'),('模型假设','单故障、同步及平方律不能证明田间泛化。')]):
            yy=181+j*145;v+=box(513,yy,719,125,'#164C45',r=8)+txt(540,yy+37,title,24,C,True)+para(540,yy+83,body,652,24,'#FFFFFF')
        v+=txt(513,639,'需落实参考标定、状态标签与独立批次实测。',24,Y)
        out+=grp('failure-mechanisms',508,175,724,479,v)
    elif i==9:
        v+=screen(48,183,763,447)
        out+=grp('management-replay-ui',48,180,763,453,v);v=''
        entries=[('设备与支管','档案、测点示意、质量标志'),('趋势与证据','本地量、判据、故障候选输出'),('事件与确认','待检查 / 数据无效 / 节点离线'),('回放与导出','日志留存、操作标签、批次导出')]
        for j,(title,body) in enumerate(entries):
            yy=192+j*107;v+=txt(849,yy+26,f'0{j+1}',20,G,True)+txt(896,yy+28,title,28,G,True)+para(849,yy+71,body,373,20,T)
            if j<3:v+=ln(849,yy+91,1232,yy+91,L,1)
        out+=grp('management-functions',842,182,390,466,v)
    elif i==10:
        v=txt(48,192,'主要故障实验网格（计划）',28,G,True)+txt(48,239,'2类型 × 3供压 × 3程度 × 3独立操作',24,T)
        v+=txt(48,326,'≥54',72,G,True)+txt(248,321,'次独立操作',24,G)
        v+=para(48,385,'正常 / 切换对照另做\n按天或批次留出验证\n不以相邻采样点充当独立样本',401,24,T)
        out+=grp('experiment-total',48,162,419,392,v);v=''
        v+=txt(513,197,'暂拟程度 / 相对健康流量偏离',20,M)
        for j,s in enumerate(['5%','10%','15%']):v+=txt(700+j*174,237,s,24,G,True,'middle')
        for j,ps in enumerate(['80kPa','120kPa','160kPa']):
            yy=261+j*94;v+=txt(517,yy+40,ps,20,G)
            for k in range(3):
                xx=629+k*174;v+=box(xx,yy,154,76,S,r=5)+txt(xx+77,yy+31,'两类故障',18,M,False,'middle')+txt(xx+77,yy+59,'各 ≥3次',20,G,True,'middle')
        out+=grp('planned-factor-grid',506,179,726,379,v)
        v=box(48,566,1184,86,G,r=6)+txt(69,600,'标定/台架 → 强基线/消融 → 无线/整机',24,'#FFFFFF',True)
        v+=txt(69,633,'拟8h连续记录及恢复检查；现场无故障标签时，只验证正常运行适应性。',20,'#D8EAE2')
        out+=grp('validation-gates',48,562,1184,95,v)
    elif i==11:
        v=ln(81,228,1185,228,G,4)
        stages=[('2027.03—04','标定与有线','测量误差/可观测性'),('2027.05—08','台架与LoRa','独立批次/整机测量'),('2027.09—10','验证与论文','冻结方法/成稿投稿'),('2027.11—2028.02','结项与归档','补实验/系统/报告')]
        for j,(time,title,body) in enumerate(stages):
            xx=48+j*307;v+=circ(xx+34,228,13,G)+txt(xx,193,time,28,G,True)+txt(xx,284,title,24,G,True)+txt(xx,323,body,20,M)
        out+=grp('time-gates',48,169,1184,171,v);v=''
        v+=box(48,388,339,263,D,r=8)+txt(72,429,'启动额度估计',24,C,True)+txt(72,523,'¥2000',64,'#FFFFFF',True)
        v+=para(72,570,'已有电脑 / 借参考仪器\n资助后优先标定与独立实验',294,20,'#D8EAE2')
        budgets=[('电子/LoRa',260),('传感/调理',500),('水路',500),('供电/外壳',250),('耗材',130),('调研/返工',360)]
        for j,(s,n) in enumerate(budgets):
            col=j%3;row=j//3;xx=423+col*274;yy=394+row*126
            v+=txt(xx,yy+27,s,20,M)+txt(xx,yy+77,f'{n}元',30,G,True)+ln(xx,yy+94,xx+240,yy+94,L,1)
        out+=grp('budget-allocation',48,380,1184,278,v)
    elif i==12:
        v+=txt(48,225,'一个可验证的原型',42,'#FFFFFF',True)
        v+=txt(48,286,'节点 + 接收端 + 台架 + 管理软件',28,C)
        v+=field_scene(44,335,560,279)
        v+=txt(48,653,'部署概念，非实物；基础验收为双支路台架。',18,'#B7CCC6')
        out+=grp('prototype-delivery',48,177,567,484,v);v=''
        v+=ln(650,193,650,613,'#4A776F',2)+txt(688,226,'一组可复现的证据',42,'#FFFFFF',True)
        for j,(title,body) in enumerate([('测量依据','标定、原始日志、程度与独立标签'),('方法验证','强基线、消融、提前量与失败案例'),('研究产出','研究/结题报告、过程记录、论文稿')]):
            yy=285+j*108;v+=txt(688,yy,title,24,Y,True)+txt(688,yy+40,body,20,'#D8EAE2')
        v+=box(688,610,544,40,'#23554E',r=4)+txt(706,638,'争取国家级，以真实问题、增量与条件支撑。',20,C)
        out+=grp('evidence-delivery',645,178,587,478,v)
    elif i==13:
        v+=box(48,204,333,95,S,r=6)+txt(72,246,'原因A：供压下降',24,G,True)+txt(72,278,'旧单点模型',18,M)
        v+=box(48,362,333,95,'#F6ECE6',r=6)+txt(72,404,'原因B：上游节流',24,A,True)+txt(72,436,'可映射到同一测点观测',18,M)
        v+=arrow(390,253,499,330,G,3)+arrow(390,410,499,330,A,3)
        v+=box(515,262,246,137,G,r=6)+txt(638,312,'相同 P / Q',30,'#FFFFFF',True,'middle')+txt(638,362,'不等于相同原因',20,'#FFFFFF',False,'middle')
        v+=arrow(769,330,825,330,G,3)+para(850,289,'增加P0\n有条件改善该歧义',361,28,G,True)
        v+=box(48,505,1184,147,S,r=6)+txt(71,544,'双点仍有歧义：未知正常负载与等效泄漏可以同形。',28,G,True)
        v+=txt(71,588,'输出有限模式 / 待检查 / 数据无效；位置到监测支管或区段。',24,T)
        v+=txt(71,625,'成立条件：信号可观测，参考可标定，操作可重复。',20,M)
        out+=grp('cause-observation-ambiguity',48,180,1184,478,v)
    elif i==14:
        for j,(title,subtitle,items,col) in enumerate([('申报','当前一个月','九节模板 / 四工作包\n模型与反例\n实验资源计划',G),('结项','2027.03—2028.02','实物系统 / 独立实测\n方法对照\n报告和过程记录',B),('论文','由真实证据提炼','一个主问题 / 强基线\n独立数据与消融\n可复现的研究贡献',A)]):
            xx=48+j*407;v+=box(xx,195,370,327,S,r=8)+box(xx,195,370,6,col)+txt(xx+24,251,title,42,col,True)
            v+=txt(xx+24,302,subtitle,20,M)+para(xx+24,369,items,326,24,T)
            if j<2:v+=arrow(xx+375,356,xx+400,356,G,2)
        v+=box(48,564,1184,86,G,r=6)+txt(70,597,'论文优先：渐进故障辨识边界；可靠通信为备选。',24,'#FFFFFF',True)
        v+=txt(70,632,'发表、收录与未来加分需要另行确认；立项材料不承诺已经取得成果。',20,'#D8EAE2')
        out+=grp('completion-standards',48,180,1184,478,v)
    else:
        refs=[('滴灌堵塞综述 / AWM 2022','10.1016/j.agwat.2022.107873'),('HydroNeuro / Sensors 2026','10.3390/s26103010'),('可控灌溉平台 / Land 2026','10.3390/land15030464'),('农业事件通信 / Sensors 2021','10.3390/s21165541'),('长期事件通信 / IFAC 2025','10.1016/j.ifacol.2025.11.761')]
        v+=txt(48,193,'研究文献',28,G,True)
        for j,(s,doi) in enumerate(refs):
            yy=238+j*75;v+=txt(48,yy,s,20,T)+txt(48,yy+30,doi,18,M)
        out+=grp('literature-register',48,170,634,459,v);v=''
        v+=box(742,183,490,465,S,r=8)+txt(766,225,'制度与复现文件',28,G,True)
        v+=para(766,272,'塔大实施细则\njwc.taru.edu.cn/info/1035/3872.htm',437,18,T)
        for j,(s,path) in enumerate([('新增诊断','diagnosis_feasibility.py / DIAGNOSIS.md'),('公平通信','communication_feasibility.py'),('原始证据','summary.json / trials.csv / 证据清单')]):
            yy=366+j*86;v+=txt(766,yy,s,20,G,True)+txt(766,yy+33,path,18,M)
        out+=grp('policy-reproduction',738,178,494,478,v)
    return out+'</svg>'

if __name__=='__main__':
    start=int(sys.argv[1]) if len(sys.argv)>1 else 1
    end=int(sys.argv[2]) if len(sys.argv)>2 else 15
    for i in range(start,end+1):(P/'svg_output'/f'{i:02}_slide.svg').write_text(authored(i),encoding='utf-8',newline='\n')
    # The same native concept asset serves the site; never a fake device photograph.
    if start==1:
        field='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 530">'+box(0,0,800,530,D)+field_scene(10,65,755,395)+txt(35,38,'滴灌支管监测：场景概念示意',24,'#FFFFFF',True)+txt(35,510,'P0/P1/Q → 感知节点 → LoRa接收；非田间或实物照片',18,'#B7CCC6')+'</svg>'
        (ROOT/'application/figures/field_concept.svg').write_text(field,encoding='utf-8',newline='\n')
    print('Visual revision authored:',start,'through',end)
