"""Print diagrams: core labels and legends only; no explanatory footers."""
from pathlib import Path
from lxml import etree as E
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'application/figures/submission_upgrade'
OUT=ROOT/'application/figures/print_polish';OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/'simulation/print_polish';DATA.mkdir(parents=True,exist_ok=True)
S='{http://www.w3.org/2000/svg}'
sha=lambda b:hashlib.sha256(b).hexdigest()
records=[]
def canvas(h):
 r=E.Element(S+'svg',nsmap={None:S[1:-1]},width='1000',height=str(h),viewBox=f'0 0 1000 {h}')
 d=E.SubElement(r,S+'defs');m=E.SubElement(d,S+'marker',id='arrow',markerWidth='8',markerHeight='8',refX='7',refY='4',orient='auto',markerUnits='userSpaceOnUse')
 E.SubElement(m,S+'path',d='M0 0 L7 4 L0 8 Z',fill='#202020')
 E.SubElement(r,S+'rect',width='1000',height=str(h),fill='white');return r
def text(r,x,y,value,bold=False,anchor='middle'):
 e=E.SubElement(r,S+'text',x=str(x),y=str(y),fill='#151515',**{'font-family':'Microsoft YaHei, SimSun, sans-serif','font-size':'24','font-weight':'700' if bold else '400','text-anchor':anchor});e.text=value;return e
def box(r,x,y,w,h,lines,dashed=False):
 g=E.SubElement(r,S+'g',**{'data-box':'true','data-x':str(x),'data-y':str(y),'data-w':str(w),'data-h':str(h)})
 at={'x':str(x),'y':str(y),'width':str(w),'height':str(h),'fill':'white','stroke':'#202020','stroke-width':'2','rx':'2'}
 if dashed:at['stroke-dasharray']='7 5'
 E.SubElement(g,S+'rect',**at)
 gap=30;first=y+(h-(len(lines)-1)*gap)/2+8
 for i,line in enumerate(lines):text(g,x+w/2,first+i*gap,line,i==0)
def line(r,points,arrow=True,dashed=False):
 at={'d':'M '+' L '.join(f'{x} {y}' for x,y in points),'fill':'none','stroke':'#202020','stroke-width':'2'}
 if arrow:at['marker-end']='url(#arrow)'
 if dashed:at['stroke-dasharray']='7 5'
 E.SubElement(r,S+'path',**at)
def save(r,name,removed=None):
 p=OUT/(name+'.svg');p.write_bytes(E.tostring(r,encoding='utf-8'))
 records.append({'name':name,'svg':p.relative_to(ROOT).as_posix(),'source':(SRC/(name+'.svg')).relative_to(ROOT).as_posix(),
                 'source_sha256':sha((SRC/(name+'.svg')).read_bytes()),'removed_labels':removed or [],'physical_validation':False})

# Figure 1: balanced modules, short arrows and a compact evaluation row.
r=canvas(535)
for x,w,lines in [(20,215,['感知与诊断节点','压力与流量','分级采集与诊断','日志与模拟控制']),
 (325,150,['接收模块','E220','USB-TTL','串口桥接']),
 (560,200,['PC接收服务','校验与去重','SQLite存储','事务提交后确认']),
 (825,155,['本地Web','状态与趋势','巡检与复测','指令状态'])]:box(r,x,25,w,150,lines)
for xa,xb,y,label in [(235,325,83,'LoRa'),(475,560,83,'UART'),(760,825,83,'读取'),
 (325,235,140,'ACK'),(560,475,140,'ACK'),(825,760,140,'记录')]:
 line(r,[(xa,y),(xb,y)]);text(r,(xa+xb)/2,y-12,label)
box(r,20,240,215,80,['预留执行器接口','LED / 蜂鸣器'],True)
line(r,[(125,175),(125,240)]);text(r,20,221,'控制请求',anchor='start')
box(r,20,370,300,90,['清水台架与参考测量','故障操作与参考读数'])
box(r,400,370,580,90,['独立实验评价','诊断、送达、控制模拟与复测'])
line(r,[(280,370),(280,205),(220,205),(220,175)]);text(r,292,346,'采集',anchor='start')
line(r,[(320,415),(400,415)]);text(r,360,402,'参照')
line(r,[(200,175),(200,190),(370,190),(370,335),(450,335),(450,370)],dashed=True)
for x in (660,900):line(r,[(x,175),(x,370)],dashed=True)
text(r,20,511,'实线：测量或业务连接；虚线：评价记录或预留接口。',anchor='start')
save(r,'system_responsibilities',['标签独立于检测结果','采集和发送计数；另测整机能量'])

# Figure 5: acquisition and protection remain separate decisions.
r=canvas(680)
box(r,225,20,550,75,['标定与健康参照','采集和上报分别配置'])
box(r,60,160,360,112,['周期监测','读取压力与流量计数','根据本次观测更新特征'])
box(r,580,160,360,112,['加密采集','缩短读取周期','持续诊断与事件上报'])
line(r,[(240,95),(240,160)]);text(r,255,133,'开始监测',anchor='start')
line(r,[(420,216),(580,216)]);text(r,500,203,'变化触发')
line(r,[(760,272),(760,325),(240,325),(240,272)]);text(r,500,311,'恢复稳定且保持时间结束')
E.SubElement(r,S+'path',d='M500 365 L805 440 L500 515 L195 440 Z',fill='white',stroke='#202020',**{'stroke-width':'2'})
text(r,500,426,'数据有效、工况明确且异常持续')
text(r,500,462,'满足保护条件？')
line(r,[(60,216),(25,216),(25,440),(195,440)]);text(r,110,425,'观测')
line(r,[(940,216),(975,216),(975,440),(805,440)]);text(r,890,425,'观测')
box(r,60,575,360,90,['保存记录并继续采集','异常时人工核查'])
box(r,580,575,360,90,['生成模拟控制请求','序号、演示输出与复位'])
line(r,[(500,515),(500,545),(240,545),(240,575)]);text(r,360,534,'否')
line(r,[(500,515),(500,545),(760,545),(760,575)]);text(r,650,534,'是')
line(r,[(900,533),(900,575)]);text(r,917,559,'人工',anchor='start')
save(r,'event_sampling_strategy',['周期候选经对照试验选择；确认按经过时间与真实观测次数计算。','模拟反馈不代表阀门关闭；无实物时只记录请求与演示状态。'])

# Figure 6: smaller diamonds, consistent text hierarchy and equal branch margins.
r=canvas(685)
box(r,80,20,510,80,['保存P₀、P₁、Q及时间','核对配置、健康参照与操作状态'])
line(r,[(335,100),(335,135)])
E.SubElement(r,S+'path',d='M335 135 L565 200 L335 265 L105 200 Z',fill='white',stroke='#202020',**{'stroke-width':'2'})
text(r,335,208,'数据有效且工况可比？')
box(r,700,163,260,74,['暂缓诊断','保留数据与原因'])
line(r,[(565,200),(700,200)]);text(r,632,188,'否')
line(r,[(335,265),(335,300)]);text(r,365,289,'是')
box(r,80,300,510,95,['计算负载特征与区段阻力','按标定结果检验持续偏离'])
line(r,[(335,395),(335,430)])
E.SubElement(r,S+'path',d='M335 430 L565 495 L335 560 L105 495 Z',fill='white',stroke='#202020',**{'stroke-width':'2'})
text(r,335,503,'异常是否持续满足判据？')
box(r,700,458,260,74,['继续监测','保留观测记录'])
line(r,[(565,495),(700,495)]);text(r,632,483,'否')
line(r,[(335,560),(335,605)]);text(r,365,588,'是')
box(r,80,605,510,60,['输出候选模式与异常事件'])
save(r,'diagnosis_proposal')

# Figure 7: two aligned sequence sections instead of a long explanatory footer.
r=canvas(635)
for x,w,lines in [(25,240,['节点日志与模块']),(380,240,['接收端与PC服务']),(740,235,['SQLite数据库'])]:box(r,x,20,w,56,lines)
for x in (145,500,857):line(r,[(x,76),(x,615)],arrow=False,dashed=True)
text(r,25,113,'正常接收',True,anchor='start')
for xa,xb,y,label in [(145,500,155,'EVENT：设备、批次、序号'),(500,857,220,'校验并写入或去重'),
 (857,500,280,'事务提交成功'),(500,145,340,'ACK：事件身份与摘要')]:
 line(r,[(xa,y),(xb,y)]);text(r,(xa+xb)/2,y-14,label)
E.SubElement(r,S+'rect',x='20',y='367',width='960',height='40',fill='white')
text(r,25,394,'确认丢失后重传',True,anchor='start')
for xa,xb,y,label in [(145,500,440,'同一事件重发'),(500,857,500,'核对原记录与摘要'),
 (857,500,554,'原记录一致且已提交'),(500,145,608,'再次回复ACK')]:
 line(r,[(xa,y),(xb,y)],dashed=True);text(r,(xa+xb)/2,y-14,label)
save(r,'durable_event_sequence',['ACK表示接收端保存；人工已查看、处置与同工况复测分别记录。','有限重试后保留未确认事件；链路恢复后继续核对。'])

removals={
 'water_layout':['Q计入A正常负载与泄漏总量','P0/P1侧向测压；Q在分流前。泄漏先独立计量，再人工回水。'],
 'collection_overview':['A支路：P0 → R → P1 → Q → 正常负载与泄漏分流。','Q包含正常与泄漏流量；B只提供正常负载变化对照。'],
 'measurement_interfaces':['正常量程0.6—3.0V；20mA耗散0.06W；22mA已达3.3V。','台架共地；压力回路与主控信号接口分级调理。'],
 'noise_outcomes_print':['每组20个合成试次；误差线为模型内Wilson 95%区间。'],
 'failure_counterexamples':[]}
for name,removed in removals.items():
 r=E.fromstring((SRC/(name+'.svg')).read_bytes());seen=[]
 for t in list(r.iter(S+'text')):
  if t.text in removed:seen.append(t.text);t.getparent().remove(t)
 assert sorted(seen)==sorted(removed),(name,seen)
 if name=='collection_overview':
  r.set('viewBox','0 65 1000 745');r.set('height','745')
  labels={'1  P0区段入口压力':'1  P₀ 上游压力测点','2  R等效受限元件':'2  R 等效受限元件','3  P1受限下游压力':'3  P₁ 下游压力测点','4  Q测量A总流量':'4  Q 支路A总流量','5  A正常等效负载':'5  A 正常等效负载','6  B健康负载切换':'6  B 正常负载切换','7  泄漏独立收集':'7  泄漏独立收集容器','8  采集与LoRa节点':'8  采集与LoRa节点'}
  for t in r.iter(S+'text'):
   if t.text in labels:t.text=labels[t.text]
 elif name=='water_layout':
  # Keep the right-hand return line away from the figure edge.
  r.set('width','1090');r.set('height','584');r.set('viewBox','-20 -25 1090 584')
  background=r.find(S+'rect');background.set('x','-20');background.set('y','-25');background.set('width','1090');background.set('height','584')
  for p in r.iter(S+'path'):
   if p.get('d'):p.set('d',p.get('d').replace('990','1020'))
  for t in r.iter(S+'text'):
   t.set('font-size','26')
   if t.text=='P0':t.text='P₀'
   if t.text=='P1':t.text='P₁'
 elif name=='measurement_interfaces':
  # Close the removed notes' vertical gap by moving the flow row up 25 px.
  for node in r.xpath('.//*[local-name()="g" and @data-box]'):
   if float(node.get('data-y'))>700:
    node.set('transform','translate(0 -25)')
  # Paths/labels of that row move with it; other circuit geometry is unchanged.
  for parent in r.iter(S+'g'):
   for node in list(parent):
    if node.tag==S+'text' and float(node.get('y','0'))>700:node.set('transform','translate(0 -25)') if parent.get('data-box') is None else None
    if node.tag==S+'path' and '777' in node.get('d',''):node.set('transform','translate(0 -25)')
  for t in r.iter(S+'text'):
   if t.text=='模数转换':t.text='ADS1115'
   if t.text=='量程匹配与滤波':t.text='模拟输入调理'
   if t.text=='两线4—20mA':t.text='两线制 4–20 mA'
  r.set('height','750');r.set('viewBox','0 85 1000 750')
 elif name=='noise_outcomes_print':r.set('height','480');r.set('viewBox','0 0 612 480')
 save(r,name,removed)
(DATA/'figure_sources.json').write_text(json.dumps({'date':'2026-10-06','physical_validation':False,'figures':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Nine print variants created; model/plot data unchanged. Rendering and inspection required.')
