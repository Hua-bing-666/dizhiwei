"""Main-agent authored, page-specific SVG compositions; converter owns PPTX export."""
from pathlib import Path
from html import escape
import json, math, sys

ROOT=Path(__file__).resolve().parents[1]; P=ROOT/'projects/drip-research_ppt169_20261002'
deck=json.loads((P/'analysis/deck_content.json').read_text(encoding='utf-8'))
cases=json.loads((ROOT/'simulation/results/scenarios.json').read_text(encoding='utf-8'))
comm=json.loads((ROOT/'simulation/communication_results/summary.json').read_text(encoding='utf-8'))
diagnosis=json.loads((ROOT/'simulation/diagnosis_results/summary.json').read_text(encoding='utf-8'))
G='#164C45'; A='#B4512B'; B='#426B91'; T='#20332F'; M='#556762'; L='#C7D2CB'; BG='#FAF9F5'; S='#EEF3EF'
F='Microsoft YaHei, Arial'; H='SimHei, Arial'

def text(x,y,value,size=24,color=T,bold=False,family=None,anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="{family or F}" font-size="{size}" fill="{color}" text-anchor="{anchor}"'+(' font-weight="bold"' if bold else '')+'>'+escape(str(value))+'</text>'

def paragraph(x,y,value,width,size=24,color=T,leading=None,bold=False):
    # Conservative CJK headroom, including punctuation. One editable frame per paragraph.
    lines=[]; line=''; used=0
    for ch in value:
        advance=size*(1.08 if ord(ch)>127 else .60)
        if ch=='\n' or used+advance>width:
            if line:lines.append(line)
            line='';used=0
            if ch=='\n':continue
        line+=ch;used+=advance
    if line:lines.append(line)
    leading=leading or round(size*1.55)
    return f'<text x="{x}" y="{y}" font-family="{F}" font-size="{size}" fill="{color}"'+(' font-weight="bold"' if bold else '')+'>'+escape(lines[0])+''.join(f'<tspan x="{x}" dy="{leading}">{escape(l)}</tspan>' for l in lines[1:])+'</text>'

def rect(x,y,w,h,fill=S,stroke='none',r=0):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
def line(x1,y1,x2,y2,color=L,width=2,dash=None):return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def group(id,x,y,w,h,contents):return f'<g id="{id}" data-pptx-bounds="{x} {y} {w} {h}">{contents}</g>'
def circle(x,y,r,fill=G,stroke='none'):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'

sources={3:'文献：AWM 2022；HydroNeuro 2026；Land 2026；Sensors 2021；IFAC 2025。完整DOI见备用页。',5:'来源：diagnosis_feasibility.py 的布点假设；平方律及负载未标定。设计示意，非样机。',6:'来源：diagnosis_results/summary.json，种子10300、压力噪声σ0.3kPa；未标定合成数据，非实测。',7:'来源：旧单压力communication_results/summary.json；相同检测/ACK；非射频/功耗，未与新诊断合并。',8:'来源：diagnosis_results/summary.json，6场景×4噪声×20种子；合成重复不是实物识别率。',11:'额度估算，非报价；已有电脑且借参考仪器为前提，任务及数值须提交前由导师核对。',13:'来源：旧单点结构反例及新增双点模型；辨因依赖布点、操作信息、负载与测量质量。',15:'制度按本批核对；已有成果限文献、模型和程序；案例内容不作为本项目性能证明。'}

def frame(i):
    d=deck[i-1]
    role='cover' if i==1 else 'ending' if i==12 else 'content'
    out=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" data-pptx-page-role="{role}">'
    out+=rect(0,0,1280,720,G if i==1 else BG).replace('<rect ','<rect id="page-background" data-pptx-role="background" ',1)
    out+=f'<text id="page-kicker" data-pptx-role="header" x="48" y="44" font-family="{F}" font-size="16" fill="{S if i==1 else G}">'+escape(d['status'])+'</text>'
    active=0 if i<=3 else 1 if i in (4,5,9) else 2 if i in (6,7,8,13,15) else 3
    for j,label in enumerate(['场景','系统','证据','实施']):
        out+=f'<text id="page-route-{j}" data-pptx-role="header" x="{790+j*93}" y="44" font-family="{F}" font-size="16" fill="{S if i==1 else G if j==active else M}"'+(' font-weight="bold"' if j==active else '')+'>'+label+'</text>'
    if i!=1:out+=group('page-title',48,65,1184,95,text(48,121,d['title'],42,G,family=H))
    out+=f'<line id="header-rule" data-pptx-role="decoration" x1="48" y1="148" x2="1232" y2="148" stroke="{L}" stroke-width="1"/>'
    out+=f'<text id="source-footer" data-pptx-role="footer" x="48" y="683" font-family="{F}" font-size="16" fill="{S if i==1 else M}">'+escape(sources.get(i,'研究计划：实物、真实无线和田间证据尚未完成；所有指标及扩展按正式任务书冻结。'))+'</text>'
    out+=f'<text id="page-number" data-pptx-role="page-number" x="1232" y="44" font-family="{F}" font-size="16" text-anchor="end" fill="{S if i==1 else M}">{i:02} / 15</text>'
    return out

def pressure_chart():
    x,y,w,h=48,211,1184,332; px,py,pw,ph=118,222,1066,258
    key='pressure-response';xs=list(range(330,601,5));series=[]
    for c,n in [('leak','渐进等效泄漏'),('restriction','渐进等效受限')]:series.append({'name':n,'x':xs,'y':[diagnosis['traces'][c+'_0.3']['severity'][j]*100 for j in xs]})
    series.append({'name':'演示失效判据15%','x':xs,'y':[15.]*len(xs)})
    meta={'name':key,'x':x,'y':y,'width':w,'height':h,'plot_area':{'x':px,'y':py,'width':pw,'height':ph},'type':'scatter','scatter_style':'line','series':series,'show_legend':False,'axes':{'x':{'minimum':330,'maximum':600,'major_unit':45,'major_gridlines':False},'y':{'minimum':0,'maximum':30,'major_unit':6,'major_gridlines':True}},'style':{'colors':[A,G,B],'font_family':F,'axis_font_size':18,'text_color':M,'axis_color':M,'grid_color':'#E0E7E2'}}
    b=f'<g id="{key}" data-pptx-replace-with="chart" data-pptx-bounds="{x} {y} {w} {h}"><metadata type="application/json">'+escape(json.dumps(meta,ensure_ascii=False))+'</metadata>'
    b+=f'<g id="{key}-chartArea"><!-- chart-plot-area: object={key} | x_min={px} | y_min={py} | x_max={px+pw} | y_max={py+ph} -->'
    for val in [0,6,12,18,24,30]:
        yy=py+ph-val/30*ph;b+=line(px,yy,px+pw,yy,'#E0E7E2',1)+text(px-16,yy+6,val,18,M,anchor='end')
    for val in [330,375,420,465,510,555,600]:b+=text(px+(val-330)/270*pw,py+ph+28,val,18,M,anchor='middle')
    b+=line(px,py,px,py+ph,M,1).replace('<line ','<line id="pressure-axis-y" ',1)+line(px,py+ph,px+pw,py+ph,M,1).replace('<line ','<line id="pressure-axis-x" ',1)
    for sr,color in zip(series,[A,G,B]):
        pts=' '.join(f'{px+(t-330)/270*pw:.3f},{py+ph-v/30*ph:.3f}' for t,v in zip(sr['x'],sr['y']))
        b+=f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>'
    b+='</g></g>'
    return b

def scatter_chart(key,case,x,y,w,h):
    rows=[r for r in comm['summary'] if r['case']==case and r['loss']==.1]
    xmax=100 if case=='normal' else 600;ymax=1.5 if case=='normal' else 2.5
    px=x+62;py=y+35;pw=w-103;ph=h-110;X=lambda v:px+v/xmax*pw;Y=lambda v:py+ph-v/ymax*ph
    names=['周期10s','周期30s','原始事件','滤波限频事件'];cols=[G,B,A,'#83639B'];notes=[]
    for i,(r,n) in enumerate(zip(rows,names)):
        notes.append({'text':n,'width':150,'font_size':18,'color':cols[i]})
    meta={'name':key,'type':'scatter','scatter_style':'marker','x':x,'y':y,'width':w,'height':h,'plot_area':{'x':px,'y':py,'width':pw,'height':ph},'series':[{'name':n,'x':[r['frames_mean']],'y':[r['pressure_mae']]} for r,n in zip(rows,names)],'show_legend':False,'axes':{'x':{'minimum':0,'maximum':xmax,'major_unit':xmax/4,'major_gridlines':False},'y':{'minimum':0,'maximum':ymax,'major_unit':ymax/5,'major_gridlines':True,'number_format':'0.0'}},'notes':notes,'style':{'colors':cols,'font_family':F,'axis_font_size':18,'text_color':M,'axis_color':M,'grid_color':'#E0E7E2'}}
    b=f'<g id="{key}" data-pptx-replace-with="chart" data-pptx-bounds="{x} {y} {w} {h}"><metadata type="application/json">'+escape(json.dumps(meta,ensure_ascii=False))+'</metadata>'
    b+=f'<g id="{key}-chartArea"><!-- chart-plot-area: object={key} | x_min={px} | y_min={py} | x_max={px+pw} | y_max={py+ph} -->'
    for j in range(6):
        val=j*ymax/5;yy=Y(val);b+=line(px,yy,px+pw,yy,'#E0E7E2',1)+text(px-12,yy+6,f'{val:.1f}',18,M,anchor='end')
    for j in range(5):b+=text(X(j*xmax/4),py+ph+28,f'{j*xmax/4:g}',18,M,anchor='middle')
    b+=line(px,py,px,py+ph,M,1).replace('<line ',f'<line id="{key}-axis-y" ',1)+line(px,py+ph,px+pw,py+ph,M,1).replace('<line ',f'<line id="{key}-axis-x" ',1)
    # Point labels attach to their own series; stagger offsets avoid misidentification.
    offsets=[(10,-15),(12,-14),(10,26),(12,-18)] if case=='normal' else [(20,-10),(12,-14),(-105,-14),(12,43)]
    for r,n,c,(dx,dy) in zip(rows,names,cols,offsets):b+=circle(round(X(r['frames_mean']),3),round(Y(r['pressure_mae']),3),6,c)+text(round(X(r['frames_mean'])+dx,3),round(Y(r['pressure_mae'])+dy,3),n,18,c)
    b+='</g></g>';return b

def authored(i):
    d=deck[i-1]; out=frame(i);c=''
    modules='core, structure'
    if i==1:
        # Cover: two-line claim dominates; right-hand diagram grounds the subject.
        c+=paragraph(48,243,'南疆滴灌支管\n早期故障诊断',770,60,'#FFFFFF',leading=84,bold=True)
        c+=paragraph(48,415,d['content'][0]+'\n'+d['content'][1],800,24,S)
        c+=text(48,536,d['content'][2],24,S)
        c+=paragraph(48,593,d['content'][3],790,18,S)
        out+=group('cover-claim',48,170,810,466,c)
        c=line(916,285,1050,285,S,4)+line(1050,285,1050,420,S,4)+line(1050,285,1200,285,S,4)+line(1050,420,1200,420,S,4)
        c+=circle(1110,285,21,G,S)+circle(1110,420,21,G,S)+text(1110,293,'P',24,S,anchor='middle')+text(1110,428,'Q',24,S,anchor='middle')
        c+=text(940,244,'双压力',28,S)+text(1122,502,'诊断 → 告警',24,S,anchor='middle')+line(1110,451,1110,477,S,2,'6,5')
        out+=group('cover-system',894,170,338,466,c)
    elif i==2:
        c=text(48,210,'一组测量，两类来源',30,G)
        c+=rect(48,246,566,171,S)+text(74,290,'正常运行',28,G,bold=True)+paragraph(74,341,'支路开关、供压调整、负载改变',510,24)
        c+=rect(648,246,584,171,'#F4ECE5')+text(674,290,'需要检查的异常',28,A,bold=True)+paragraph(674,341,'可控泄漏、水力受限、切换期短时异常',520,24)
        c+=paragraph(48,488,'诊断：能观察到多小的故障，何时需要输出待检查？',1184,28,G)
        c+=paragraph(48,558,'系统：本地发现的证据能否可靠送达并回放确认？',1184,28,G)
        out+=group('problem-comparison',48,178,1184,452,c)
    elif i==3:
        entries=[('间接检测的边界','滴灌堵塞综述（2022）','限定低成本测点可观测范围，不承诺逐滴头早期诊断'),('阀态建模已有先例','HydroNeuro（2026）','检验连续切换与短时异常，不把状态辅助直接当作创新'),('平台和事件通信已有研究','灌溉平台（2026）；农业通信（2021/2025）','增加强周期对照与相同告警确认，评价取舍而非预设优越')]
        for j,(t,s,b) in enumerate(entries):
            yy=195+j*139;c+=text(48,yy+22,t,28,G)+text(690,yy+22,s,18,M)+line(48,yy+42,1232,yy+42,L,1)+paragraph(48,yy+88,b,1184,24)
        out+=group('research-position',48,175,1184,449,c)
    elif i==4:
        entries=[('01','WP1 测量与建模','P0 / P1 / Q → 参考标定 → 差压误差'),('02','WP2 诊断与边界','渐进故障 → 状态 / 强基线 → 程度与提前量'),('03','WP3 可靠告警','固定采样 → 周期/事件公平对照 → ACK / 整机测量'),('04','WP4 系统与验证','节点 / 管理软件 / 台架 → 独立实测 → 数据与报告')]
        for j,(n,t,b) in enumerate(entries):
            yy=178+j*112;c+=text(48,yy+63,n,60,G)+text(171,yy+34,t,28,G,bold=True)+text(171,yy+78,b,24,T)+line(171,yy+99,1232,yy+99,L,1)
        out+=group('research-packages',48,175,1184,461,c)
    elif i==5:
        modules+=', formula'
        c+=text(52,216,'共同供水 → 双支路 → P0 / P1 / Q',28,G)
        for args in [(80,357,360,357),(360,285,360,493),(360,285,1050,285),(360,493,1050,493)]:c+=line(*args,G,4)
        c+=rect(186,330,100,54,BG,G)+text(205,366,'Rc',28,G)
        c+=rect(458,258,122,54,BG,A)+text(475,294,'节流',24,A)
        c+=circle(403,285,26,BG,B)+text(403,294,'P0',24,B,anchor='middle')+circle(727,285,26,BG,G)+text(727,294,'P1',24,G,anchor='middle')+circle(865,285,26,BG,G)+text(865,294,'Q',24,G,anchor='middle')
        c+=rect(974,250,82,68,S,G)+rect(974,459,82,68,S,G)
        c+=text(65,312,'供压Ps',24,G)+text(668,237,'A下游',24,G)+text(598,452,'B支路切换',24,G)
        c+=line(924,285,924,365,A,2)+line(924,365,1080,365,A,2)+text(1100,372,'泄漏',24,A)
        c+=text(1081,290,'负载',24,T)+text(1081,501,'负载',24,T)
        c+=f'<text x="52" y="575" font-family="{F}" font-size="28" fill="{G}">负载假设：<tspan data-pptx-inline-formula="Q=C\\sqrt{{P_1}}">Q = C√P₁</tspan></text>'
        c+=text(526,575,'压降假设：P0 − P1 = R·Q²',24,G)
        c+=text(52,623,'测点间健康压降与差分不确定度必须先标定；图为集中等效模型。',18,M)
        out+=group('hydraulic-model',48,175,1184,454,c)
    elif i==6:
        modules='core, chart, native-data'
        out+=group('pressure-heading',48,165,1184,44,text(48,199,'渐进泄漏',24,A)+text(285,199,'渐进受限',24,G)+text(548,199,'15%演示判据',24,B)+text(923,199,'纵轴：流量偏离 / %',18,M))
        # Chart frame starts below its separate legend module.
        out+=pressure_chart()
        out+=group('response-implication',48,557,1184,82,text(48,590,'从360s渐进增长；早期需在判据前正确提示，并同时报告前期误报。',24,T)+text(48,627,'横轴：模型时间/s；15%非农学阈值；实际判据、故障程度和两段时间须独立测量。',18,M))
    elif i==7:
        modules='core, chart, native-data'
        out+=group('communication-heading',48,162,1184,54,text(48,197,'相同检测、滤波载荷与告警确认；示例：10%随机丢包＋15s全丢包',24,T))
        out+=group('normal-label',48,218,556,37,text(48,245,'正常轮灌',24,G)+text(210,245,'纵轴MAE/kPa',18,M))
        out+=group('noise-label',660,218,572,37,text(660,245,'较大噪声',24,G)+text(822,245,'纵轴MAE/kPa',18,M))
        out+=scatter_chart('normal-tradeoff','normal',48,258,556,311)
        out+=scatter_chart('noise-tradeoff','noise',660,258,572,311)
        out+=group('communication-implication',48,577,1184,66,text(48,602,'横轴：上行＋ACK帧（含清队列）。少发帧可能增加信息误差；慢周期也有竞争力。',24,G)+text(48,632,'MAE相对本地模拟滤波量，首次接收前另报覆盖；不是实际压力精度或整机节电。',18,M))
    elif i==8:
        c=text(48,260,'12 / 20',60,A,bold=True)+text(383,250,'大噪声下正确提前发现试次',30,G)+text(383,300,'两类均如此；压力噪声σ10kPa，非实物性能。',24,T)
        c+=line(48,336,1232,336,L,1)+text(48,394,'测量漂移',28,A)+text(282,394,'入口压力漂移可被误判为局部受限',24,T)
        c+=text(48,459,'状态未知',28,A)+text(282,459,'正常负载增大可与等效泄漏同形',24,T)
        c+=text(48,524,'理想假设',28,A)+paragraph(282,524,'单故障、同步测量、平方律；不能据此证明田间早期准确率',934,24)
        c+=text(48,622,'保留失败案例与强基线，按实际证据确定研究增量。',28,G)
        out+=group('failure-boundaries',48,175,1184,467,c)
    elif i==9:
        # End-to-end chain: native simple lines have real order; no faux device photograph.
        names=[('原始采集','P0 / P1 / Q'),('本地节点','有限诊断 + 缓存'),('LoRa链路','发送 + ACK'),('管理软件','证据 + 确认')]
        for j,(n,b) in enumerate(names):
            xx=48+j*307;c+=rect(xx,239,263,147,S)+text(xx+20,289,n,28,G,bold=True)+text(xx+20,339,b,24,T)
            if j<3:c+=line(xx+263,312,xx+305,312,G,3)
        c+=paragraph(48,461,'管理功能：设备档案、支管示意、趋势、事件确认、回放、导出。',1184,24)
        c+=paragraph(48,518,'分别显示：故障模式 / 待检查 / 数据无效 / 节点离线。',1184,24)
        c+=paragraph(48,592,'当前网站：设计及合成回放；接收日志与状态持久化拟实现。',1184,28,G)
        out+=group('system-chain',48,175,1184,467,c)
    elif i==10:
        stages=[('01','标定与台架','五类工况、参考量与独立标签'),('02','方法验证','按批次留出、强基线、消融'),('03','无线与整机','帧/字节、两段延迟、能量')]
        for j,(n,t,b) in enumerate(stages):
            yy=191+j*114;c+=circle(77,yy+27,27,G)+text(77,yy+35,n,24,'#FFFFFF',anchor='middle')+text(131,yy+34,t,28,G,bold=True)+text(463,yy+34,b,24,T)
            if j<2:c+=line(77,yy+55,77,yy+83,L,2)
        c+=line(48,539,1232,539,L,1)+text(48,588,'两类型×三供压×三程度×三次操作：拟54次；正常/切换另做。',24,G)+text(48,630,'拟8h连续台架及恢复检查；现场无故障标签只验适应性；提交前核对资源。',18,M)
        out+=group('validation-stages',48,175,1184,467,c)
    elif i==11:
        entries=[('2027.03—04','标定 / 有线采集 / 可观测性'),('2027.05—08','独立台架 / 可靠LoRa / 整机测量'),('2027.09—10','跨条件 / 消融 / 论文成稿与投稿'),('2027.11—2028.02','补实验 / 原型与报告 / 结项')]
        for j,(t,b) in enumerate(entries):
            yy=210+j*80;c+=text(48,yy,t,24,G,bold=True)+text(342,yy,b,24,T)+line(48,yy+23,799,yy+23,L,1)
        out+=group('project-schedule',48,175,751,458,c)
        c=rect(834,175,398,458,S)+text(861,236,'启动额度估算',28,G)+text(861,322,'¥2000',60,G,bold=True)
        c+=paragraph(861,381,'电子无线260；传感500\n水路500；供电外壳250\n记录耗材130；返工360',344,24)
        c+=paragraph(861,559,'需借参考仪器；资助后优先扩展实验，论文费用另核查。',344,18,M)
        out+=group('startup-budget',834,175,398,458,c)
    elif i==12:
        c=text(48,232,'系统交付',30,G,bold=True)+text(48,286,'双压力流量节点 + 接收端 + 台架 + 管理软件',28,T)
        c+=text(48,370,'研究证据',30,G,bold=True)+paragraph(48,423,'标定/标签、强基线/消融、提前量/失败案例、报告与论文稿',1130,28,T)
        c+=rect(48,523,1184,102,G)+text(75,567,'争取国家级：以问题、增量、证据与真实条件支撑。',28,'#FFFFFF')+text(75,604,'已有成果据实陈述；研究目标以实验兑现。',24,'#FFFFFF')
        out+=group('project-deliverables',48,175,1184,467,c)
    elif i==13:
        c=text(48,255,'相同压力 / 流量 ≠ 相同故障原因',42,A,family=H)
        c+=paragraph(48,335,'上游节流与供压下降可映射到相同测点观测。',1184,28,T)
        c+=paragraph(48,418,'新增P0可有条件改善；未知正常负载仍与泄漏同形。',1184,28,G)
        c+=paragraph(48,504,'位置只到监测支管区段；输出模式、待检查或数据无效。',1184,24,T)
        c+=text(48,602,'成立条件：信号可观测、参考可标定、操作可重复。',28,G)
        out+=group('observability-boundary',48,175,1184,467,c)
    elif i==14:
        entries=[('申报','九节模板 + 四工作包 + 证据 + 实验/资源计划'),('结项','系统 + 独立实测 + 方法对照 + 报告/过程'),('论文','一个主问题 + 真实数据 + 强基线 + 可复现贡献')]
        for j,(t,b) in enumerate(entries):
            yy=205+j*117;c+=text(48,yy+29,t,30,G,bold=True)+paragraph(241,yy+29,b,974,24)+line(241,yy+63,1232,yy+63,L,1)
        c+=text(48,614,'论文优先：渐进故障辨识边界；可靠通信为另一候选，不保证发表。',24,A)
        out+=group('three-phase-contract',48,175,1184,467,c)
    else:
        for j,t in enumerate(d['content']):c+=text(48,210+j*59,t,24,T)
        out+=group('reference-register',48,175,1184,467,c)
    print(f'P{i:02} modules: {modules}')
    return out+'</svg>'

start=int(sys.argv[1]) if len(sys.argv)>1 else 1
end=int(sys.argv[2]) if len(sys.argv)>2 else 15
for i in range(start,end+1):
    (P/'svg_output'/f'{i:02}_slide.svg').write_text(authored(i),encoding='utf-8',newline='\n')
print('Authored pages:',start,'through',end)
