"""Editable monochrome diagrams, with labels kept separate from document captions."""
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/figures/usability_revision';OUT.mkdir(parents=True,exist_ok=True)

class Diagram:
    def __init__(self,name,height):self.name=name;self.height=height;self.items=[]
    def text(self,x,y,value,size=25,bold=False,anchor='middle'):
        self.items.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{600 if bold else 400}" text-anchor="{anchor}">{escape(value)}</text>')
    def box(self,x,y,w,h,lines,dash=False):
        self.items.append(f'<g data-box="1" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="#222" stroke-width="1.8" '+('stroke-dasharray="7 5"' if dash else '')+'/>')
        for i,line in enumerate(lines):self.text(x+w/2,y+h/2+9+(i-(len(lines)-1)/2)*32,line,25,i==0)
        self.items.append('</g>')
    def path(self,points,arrow=True,dash=False):
        self.items.append('<path d="M'+' L'.join(f'{x},{y}' for x,y in points)+'" fill="none" stroke="#333" stroke-width="1.8" '+('marker-end="url(#arrow)" ' if arrow else '')+('stroke-dasharray="7 5"' if dash else '')+'/>')
    def sensor(self,x,y,label):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="27" fill="white" stroke="#222" stroke-width="1.8"/>');self.text(x,y+9,label,25,True)
    def label(self,x,y,value):
        width=sum(13 if c.isascii() else 25 for c in value)+16
        self.items.append(f'<rect x="{x-width/2}" y="{y-24}" width="{width}" height="32" fill="white"/>');self.text(x,y,value,23)
    def save(self):
        s=f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.height}" viewBox="0 0 1200 {self.height}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L8 4 L0 8Z" fill="#333"/></marker></defs><rect width="1200" height="{self.height}" fill="white"/><g font-family="Microsoft YaHei,SimSun,sans-serif" fill="#111">'+''.join(self.items)+'</g></svg>'
        (OUT/(self.name+'.svg')).write_text(s,encoding='utf-8')

d=Diagram('system',390)
for x,w,lines in [(35,240,['感知诊断节点','压力、流量与事件']),(360,180,['LoRa 接收端','E220 字节桥']),(635,245,['本地接收服务','校验、去重与存储']),(965,200,['巡检平台','监测与维护'])]:d.box(x,45,w,118,lines)
for a,b,label in [(275,360,'LoRa'),(540,635,'UART'),(880,965,'读取')]:d.path([(a,84),(b,84)]);d.label((a+b)/2,73,label)
for a,b,label in [(360,275,'ACK'),(635,540,'ACK'),(965,880,'记录')]:d.path([(a,137),(b,137)]);d.label((a+b)/2,126,label)
d.box(35,215,240,60,['预留 IO 演示接口'],True);d.path([(155,163),(155,215)],True,True)
d.box(35,295,320,60,['台架与独立参考测量'])
d.box(535,280,630,90,['独立实验评价','辨识、采集、传输与处置记录'])
d.path([(355,325),(535,325)]);d.label(440,314,'参考记录')
d.path([(450,163),(450,260),(580,260),(580,280)],True,True)
for x in [758,1065]:d.path([(x,163),(x,280)],True,True)
d.save()

d=Diagram('water',455)
d.box(30,166,165,82,['可调供水','稳压与调节']);d.path([(195,207),(230,207)],False)
d.path([(230,207),(230,100),(430,100)],False)
d.sensor(332,45,'P₀');d.path([(332,72),(332,100)],False);d.box(430,66,130,68,['受限 R']);d.path([(560,100),(757,100)],False)
d.sensor(650,45,'P₁');d.path([(650,72),(650,100)],False);d.sensor(784,100,'Q')
d.path([(811,100),(945,100)]);d.box(945,66,195,68,['A 正常负载'])
d.path([(895,100),(895,215),(945,215)]);d.box(945,181,195,68,['泄漏旁路'])
d.path([(1042,249),(1042,285),(755,285),(755,249)]);d.box(645,181,220,68,['独立收集计时'])
d.path([(230,207),(230,349),(430,349)]);d.box(430,315,190,68,['B 负载切换'])
d.path([(620,349),(945,349)]);d.box(945,315,195,68,['B 正常负载'])
d.path([(1140,100),(1170,100),(1170,410),(325,410)],False)
d.path([(1140,349),(1170,349)],False);d.box(65,380,260,60,['正常出流回水'])
d.save()

d=Diagram('acquisition',510)
for y,l in [(85,'P₀ 压力变送器'),(225,'P₁ 压力变送器')]:
 d.box(35,y,270,88,[l,'4—20 mA']);d.path([(305,y+44),(375,y+44)],False)
 d.box(375,y,275,88,['电流采样与保护','调理、滤波']);d.path([(650,y+44),(760,y+44)]);d.label(703,y+31,'AIN'+('0' if y==85 else '1'))
d.box(760,75,185,250,['ADS1115','3.3 V']);d.path([(945,200),(1025,200)]);d.label(985,187,'I²C')
d.box(1025,120,145,150,['STM32','主控'])
d.box(35,377,270,100,['脉冲流量计','5 V']);d.path([(305,427),(375,427)])
d.box(375,377,275,100,['3.3 V 电平转换','SN74LVC1G17']);d.path([(650,427),(1098,427),(1098,270)])
d.label(855,415,'硬件累计计数')
d.text(170,62,'24 V 供电',23);d.text(170,202,'24 V 供电',23)
d.save()

d=Diagram('sampling',645)
d.box(225,30,750,74,['独立标定与健康参照']);d.path([(600,104),(600,126),(292,126),(292,145)])
d.box(95,145,395,102,['巡航采集','压力读取与累计计数']);d.box(710,145,395,102,['加密采集','1 秒读取、优先上报'])
# The first transition starts at the entry state, not at the middle of a cycle.
d.path([(490,183),(710,183)]);d.label(600,172,'观测持续偏离')
d.path([(907,247),(907,286),(292,286),(292,247)]);d.label(600,277,'恢复稳定且保持时间结束')
d.path([(292,247),(292,323),(600,323),(600,350)])
d.path([(907,247),(1130,247),(1130,323),(600,323)],False)
d.box(280,350,640,90,['处置条件核验','观测有效、工况明确、异常持续'])
d.path([(600,440),(600,482),(292,482),(292,510)]);d.label(445,474,'未满足')
d.path([(600,482),(907,482),(907,510)]);d.label(755,474,'满足并人工确认')
d.box(95,510,395,90,['保存记录与继续观测','异常交由人工核查'])
d.box(710,510,395,90,['模拟控制请求','LED / 蜂鸣器、反馈与复位'])
d.save()

d=Diagram('diagnosis',665)
d.box(200,30,800,78,['压力读取与累计计数']);d.path([(600,108),(600,148)])
d.box(200,148,800,88,['测量质量与健康参照检查','无效观测不补作正常数据']);d.path([(600,236),(600,268)],False)
d.path([(600,268),(292,268),(292,306)]);d.path([(600,268),(908,268),(908,306)])
d.box(75,306,435,96,['3 秒短窗','独立参照与关注门限']);d.box(690,306,435,96,['10 秒主窗','流量残差与区段阻力残差'])
d.path([(292,402),(292,437)]);d.path([(908,402),(908,437)])
d.box(75,437,435,100,['连续 2 次正向越限','关注提示'])
d.box(690,437,435,100,['同类候选连续 5 次成立','泄漏、受限或异常待检查'])
d.path([(292,537),(292,565),(600,565)],False);d.path([(908,537),(908,565),(600,565)],False)
d.path([(600,565),(600,590)]);d.box(200,590,800,60,['保存事件、观测质量与参照版本'])
d.save()

d=Diagram('protocol',610)
for x,lines in [(70,['节点与无线模块']),(470,['接收端与 PC 服务']),(870,['SQLite 数据库'])]:d.box(x,25,260,64,lines)
for x in [200,600,1000]:d.path([(x,89),(x,582)],False,True)
for a,b,y,label,dash in [(200,600,151,'EVENT：设备 / 会话 / 序号',False),(600,1000,209,'校验、写入与去重',False),(1000,600,267,'事务提交成功',False),(600,200,325,'ACK：事件身份与摘要',False),(200,600,413,'同一事件重发',True),(600,1000,471,'核对已保存记录与摘要',True),(1000,600,529,'一致且已经提交',True),(600,200,582,'再次回复 ACK',True)]:
 d.path([(a,y),(b,y)],True,dash);d.label((a+b)/2,y-12,label)
d.save()
print('Prepared six editable figures; no internal titles or decorative footnotes.')
