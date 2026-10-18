"""Native vector diagrams with connection labels placed next to their arrows."""
from pathlib import Path
from lxml import etree as E
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/figures/submission_upgrade'
S='http://www.w3.org/2000/svg'; Q='{'+S+'}'

def canvas(h):
 r=E.Element(Q+'svg',nsmap={None:S},width='1000',height=str(h),viewBox=f'0 0 1000 {h}')
 r.set('data-classification','planned_system_not_physical_validation')
 defs=E.SubElement(r,Q+'defs');m=E.SubElement(defs,Q+'marker',id='arrow',markerWidth='9',markerHeight='9',refX='8',refY='4',orient='auto')
 E.SubElement(m,Q+'path',d='M0 0 L8 4 L0 8 Z',fill='#202020')
 E.SubElement(r,Q+'rect',width='1000',height=str(h),fill='white')
 return r
def text(r,x,y,t,bold=False,anchor='middle'):
 e=E.SubElement(r,Q+'text',x=str(x),y=str(y),fill='#151515',**{'font-family':'Microsoft YaHei, SimSun, sans-serif','font-size':'24','text-anchor':anchor,'font-weight':'700' if bold else '400'})
 e.text=t;return e
def box(r,x,y,w,h,lines,dashed=False):
 g=E.SubElement(r,Q+'g',**{'data-box':'true','data-x':str(x),'data-y':str(y),'data-w':str(w),'data-h':str(h)})
 at=dict(x=str(x),y=str(y),width=str(w),height=str(h),rx='3',fill='white',stroke='#202020',**{'stroke-width':'2'})
 if dashed:at['stroke-dasharray']='8 5'
 E.SubElement(g,Q+'rect',**at)
 gap=32;first=y+(h-(len(lines)-1)*gap)/2+8
 for i,line in enumerate(lines):text(g,x+w/2,first+i*gap,line,i==0)
def arrow(r,points,dashed=False):
 a={'d':'M '+' L '.join(f'{x} {y}' for x,y in points),'fill':'none','stroke':'#202020','stroke-width':'2','marker-end':'url(#arrow)'}
 if dashed:a['stroke-dasharray']='7 5'
 E.SubElement(r,Q+'path',**a)
def save(r,name):
 p=OUT/(name+'.svg');p.write_bytes(E.tostring(r,encoding='utf-8'))
 return dict(name=name,svg=p.relative_to(ROOT).as_posix(),planned_design=True,
             connection_labels_placed_along_arrows=True,source='scripts/draw_event_system_diagrams.py',
             source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

r=canvas(660)
box(r,20,40,215,185,['感知诊断节点','双压力 / 流量','分级采集 / 诊断','日志 / 模拟控制'])
box(r,325,40,150,185,['接收模块','E220','USB-TTL','串口桥接'])
box(r,560,40,200,185,['PC接收服务','校验 / 去重','SQLite事务','提交后ACK'])
box(r,825,40,155,185,['本地Web','趋势与证据','巡检与复测','指令状态'])
for xa,xb,label in [(235,325,'LoRa'),(475,560,'UART'),(760,825,'读库')]:
 arrow(r,[(xa,110),(xb,110)]);text(r,(xa+xb)/2,98,label)
for xa,xb,label in [(560,475,'ACK'),(325,235,'ACK'),(825,760,'留痕')]:
 arrow(r,[(xa,182),(xb,182)]);text(r,(xa+xb)/2,170,label)
box(r,20,300,215,80,['预留控制执行器','接口 / 演示输出'],True)
arrow(r,[(130,225),(130,300)]);text(r,20,277,'控制请求',anchor='start')
box(r,20,440,300,116,['清水台架与独立参照','操作 / 压力 / 收集','标签独立于检测结果'])
box(r,400,440,580,116,['独立实验评价','检测 / 交付 / 模拟控制 / 复测','采集和发送计数；另测整机能量'])
arrow(r,[(280,440),(280,260),(220,260),(220,225)]);text(r,295,418,'采集',anchor='start')
arrow(r,[(320,498),(400,498)]);text(r,360,483,'参照')
arrow(r,[(200,225),(200,245),(370,245),(370,390),(450,390),(450,440)],True)
for x in (660,900):arrow(r,[(x,225),(x,440)],True)
text(r,20,615,'实线：测量/业务连接；虚线：评价记录或预留接口。',anchor='start')
records=[save(r,'system_responsibilities')]

r=canvas(880)
box(r,225,25,550,80,['标定与健康参照建立','采集、诊断、上报分别配置'])
box(r,60,185,360,130,['周期监测','读取压力与计数窗口','每次真实观测更新特征'])
box(r,580,185,360,130,['加密采集','变化触发后提高读取频率','持续诊断 / 事件上报'])
arrow(r,[(250,105),(250,185)]);text(r,265,156,'进入监测',anchor='start')
arrow(r,[(420,245),(580,245)]);text(r,500,231,'变化触发')
arrow(r,[(760,315),(760,375),(240,375),(240,315)]);text(r,500,359,'稳定且保持时间结束')
E.SubElement(r,Q+'path',d='M500 415 L810 500 L500 585 L190 500 Z',fill='white',stroke='#202020',**{'stroke-width':'2'})
text(r,500,486,'数据有效、工况明确并持续确认')
text(r,500,522,'满足保护条件？')
arrow(r,[(60,250),(25,250),(25,500),(190,500)]);text(r,120,484,'观测')
arrow(r,[(940,250),(975,250),(975,500),(810,500)]);text(r,875,484,'观测')
box(r,60,650,360,110,['保留诊断与巡检记录','证据不足不自动请求','继续采集 / 人工检查'])
box(r,580,650,360,110,['生成模拟请求与唯一序号','演示输出 / 反馈记录','人工复位'])
arrow(r,[(500,585),(500,615),(240,615),(240,650)]);text(r,360,604,'否')
arrow(r,[(500,585),(500,615),(760,615),(760,650)]);text(r,650,604,'是')
arrow(r,[(900,605),(900,650)]);text(r,915,635,'人工',anchor='start')
text(r,20,810,'周期候选经对照试验选择；确认按经过时间与真实观测次数计算。',anchor='start')
text(r,20,850,'模拟反馈不代表阀门关闭；无实物时只记录请求与演示状态。',anchor='start')
records.append(save(r,'event_sampling_strategy'))

# Compact water diagram; identical measurement order and physical connections.
r=canvas(570)
def pipe(points):
 E.SubElement(r,Q+'path',d='M '+' L '.join(f'{x} {y}' for x,y in points),fill='none',stroke='#202020',**{'stroke-width':'2'})
pipe([(185,245),(230,245),(230,145),(990,145),(990,438),(170,438),(170,455)])
pipe([(230,245),(230,385),(990,385)])
pipe([(760,145),(760,260),(820,260)])
pipe([(280,96),(280,145)]);pipe([(550,96),(550,145)])
box(r,20,200,165,90,['可调供水','稳压调节'])
box(r,350,112,150,66,['受限元件R'])
box(r,820,112,160,66,['A负载 Cₙ'])
box(r,820,227,160,66,['泄漏 Cₗ'])
box(r,580,270,220,60,['独立收集计时'])
arrow(r,[(900,293),(900,300),(800,300)])
box(r,350,346,190,78,['B切换阀','正常负载切换'])
box(r,820,352,160,66,['B正常负载'])
box(r,20,455,300,60,['正常回水至水源'])
for x,y,label in [(280,70,'P0'),(550,70,'P1'),(665,145,'Q')]:
 E.SubElement(r,Q+'circle',cx=str(x),cy=str(y),r='26',fill='white',stroke='#202020',**{'stroke-width':'2'})
 text(r,x,y+8,label,True)
text(r,355,490,'Q计入A正常负载与泄漏总量',anchor='start')
text(r,20,548,'P0/P1侧向测压；Q在分流前。泄漏先独立计量，再人工回水。',anchor='start')
records.append(save(r,'water_layout'))
p=ROOT/'simulation/submission_upgrade/figure_sources.json'
d=json.loads(p.read_text(encoding='utf-8'))
names={x['name'] for x in records}
d['figures']=[x for x in d['figures'] if x['name'] not in names]+records
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('System and adaptive strategy vectors created; browser and manual review required.')
