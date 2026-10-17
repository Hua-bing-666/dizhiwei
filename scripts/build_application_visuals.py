"""Focused proposal figures: structure, topology, real geometry, circuit and sequence.

The geometry is a proposed layout, not a manufactured or hydraulic CAD model.
"""
from pathlib import Path
from html import escape
import json, math
import numpy as np
from build_application_design_figures import Drawing, records, OUT

ROOT=Path(__file__).resolve().parents[1]

def architecture():
    d=Drawing('system_scope',590)
    for x,title,lines in [(30,'测量与诊断节点',['P0 / P1 / Q及阀态','质量 / 有限故障提示','日志 / 版本 / 待发事件']), (370,'LoRa接收端',['事件持久化 / 去重','保存成功后匹配ACK','接收时间 / 离线状态']), (710,'本地维护软件',['趋势 / 证据 / 核查','处置 / 同工况复测','归档 / 回放 / 导出'])]:
        d.box(x,35,260,190,title,lines,fill={30:'#eaf2f8',370:'#edf4ed',710:'#eef1f6'}[x],stroke='#344b59')
    d.path([(290,97),(370,97)]);d.text(330,78,'LoRa',23)
    d.path([(370,180),(290,180)]);d.text(330,206,'ACK',23)
    d.path([(630,97),(710,97)]);d.text(670,78,'数据',23)
    d.path([(710,180),(630,180)]);d.text(670,206,'留痕',23)
    d.box(30,345,260,115,'清水台架与独立参照',['操作 / 参考测量','故障程度 / 复测记录'],fill='#faf2e8',stroke='#715842')
    d.box(370,345,600,115,'独立实验评价与可复现资料',['独立标签对照提示、接收及维护结果','另行测量整机能量，保留失败实例'],fill='#f4f5f5',stroke='#43525b')
    d.path([(160,345),(160,225)]);d.text(199,288,'采样',23)
    d.path([(290,402),(370,402)])
    d.path([(260,225),(260,270),(435,270),(435,345)],dashed=True)
    d.path([(500,225),(500,345)],dashed=True)
    d.path([(840,225),(840,345)],dashed=True)
    d.text(520,511,'事件标识关联试次、配置和健康参照；实验标签独立保存。',23)
    d.footer(['实线为测量或业务连接；虚线为评价数据。ACK、已查看和复测归档分开。'])
    d.render()

def water():
    d=Drawing('dual_pressure_layout',650)
    # Pressure sensors are pressure taps, not through-flow instruments.
    d.box(25,122,150,90,'可调供水',['工作点待核'],fill='#eaf2f8',stroke='#42657b')
    d.path([(175,167),(215,167),(215,145),(875,145)],arrow=False,color='#42657b')
    d.path([(215,167),(215,385),(875,385)],arrow=False,color='#42657b')
    for x,label in [(285,'P0'),(555,'P1')]:
        d.path([(x,145),(x,88)],arrow=False);d.sensor(x,60,label)
    d.box(350,118,140,54,'受限阀 R',fill='#fbf1db',stroke='#c9a227')
    d.sensor(660,145,'Q')
    d.box(815,118,160,54,'A负载 Cₙ',fill='#edf4ed',stroke='#6f8a72')
    d.path([(750,145),(750,247),(815,247)],arrow=False,color='#4a4a4a')
    d.box(815,220,160,54,'泄漏阀 Cₗ',fill='#faede2',stroke='#4a4a4a')
    d.path([(895,274),(895,293)],arrow=True)
    d.box(795,293,195,54,'独立收集计时',fill='#faede2',stroke='#4a4a4a')
    d.box(350,358,140,54,'B切换阀')
    d.box(815,358,160,54,'B正常负载',fill='#edf4ed',stroke='#6f8a72')
    # Normal returns have their own path; the leak exits to a measuring vessel.
    d.path([(975,145),(995,145),(995,485),(155,485),(155,525)],arrow=True)
    d.path([(975,385),(995,385)],arrow=False)
    d.box(25,525,260,54,'正常回水至水源')
    d.text(565,447,'B仅模拟正常负载切换',23)
    d.text(305,559,'Q计入A正常负载与泄漏总量',23,anchor='start')
    d.footer(['P0/P1采用侧向测压；Q位于分流前。泄漏先独立计量，再人工回水。'])
    d.render()

def circuit():
    d=Drawing('pressure_frontend',600)
    for y,label,rname in [(80,'P0变送器','R0'),(275,'P1变送器','R1')]:
        d.box(30,y,225,85,label,['4—20mA 两线制'])
        d.path([(142,y-25),(142,y)],arrow=False);d.text(142,y-33,'+24V',23)
        tap=y+42
        d.path([(255,tap),(390,tap),(470,tap)],arrow=False)
        d.items.append(f'<circle cx="390" cy="{tap}" r="4" fill="black"/>')
        d.path([(390,tap),(390,tap+35)],arrow=False)
        d.items.append(f'<rect x="380" y="{tap+35}" width="20" height="45" fill="white" stroke="black" stroke-width="2"/>')
        d.text(370,tap+57,rname+' 150Ω',23,anchor='end')
        ground=tap+100
        d.path([(390,tap+80),(390,ground)],arrow=False)
        for dy,w in [(0,36),(7,24),(14,12)]:d.path([(390-w/2,ground+dy),(390+w/2,ground+dy)],arrow=False)
        d.box(470,y,180,85,'限流及保护',['元件值待验证'],dashed=True)
        d.path([(650,tap),(690,tap)],arrow=False)
    d.box(690,80,280,320,'ADS1115',[]) # Labels placed at real pin positions below.
    # Remove the auto-centred title; preserve bounding group for the labels.
    d.items[-2]=''
    d.text(708,130,'AIN0',23,anchor='start');d.text(708,325,'AIN1',23,anchor='start')
    d.text(830,211,'ADS1115',27,True)
    d.text(830,247,'VDD = 3.3V',23)
    d.text(830,282,'PGA ±4.096V',23)
    d.path([(830,45),(830,80)],arrow=False);d.text(830,35,'+3.3V / 0.1μF去耦',23)
    for x,label in [(760,'SDA'),(900,'SCL')]:
        d.path([(x,400),(x,435)],arrow=False);d.text(x,464,label,23)
    d.path([(830,400),(830,419)],arrow=False)
    for dy,w in [(0,36),(7,24),(14,12)]:d.path([(830-w/2,419+dy),(830+w/2,419+dy)],arrow=False)
    d.text(830,499,'至主控 I²C；上拉至3.3V',23)
    d.text(25,515,'V = I×150Ω = 0.6—3.0V；20mA时电阻耗散0.06W。',23,anchor='start')
    d.footer(['台架共地采集原理；两通道分时转换。输入保护、故障电流与地线布局须实测。', 'PGA量程不是引脚耐压；本图未完成PCB、器件保护定值或标定。'])
    d.render()

def diagnosis():
    d=Drawing('diagnosis_flow',650)
    d.box(30,30,570,85,'测量质量与运行状态检查',['对齐P0/P1/Q；采用冻结的同工况参照'])
    d.path([(315,115),(315,145)])
    d.diamond(315,193,570,96,['有效、状态明确且可计算？'])
    d.path([(600,193),(680,193)])
    d.text(638,174,'否',23)
    d.box(680,150,290,85,'无效或暂缓判断',['保留原始值及原因'])
    d.path([(315,241),(315,274)]);d.text(349,263,'是',23)
    d.box(30,274,570,114,'计算与持续偏离检验',['K = Q/√P1；R̂ = (P0−P1)/Q²','结合误差区间与冻结阈值'])
    d.path([(315,388),(315,420)])
    d.diamond(315,470,570,100,['偏离持续，且模式证据充分？'])
    d.path([(600,470),(680,470)]);d.text(638,450,'否',23)
    d.box(680,425,290,90,'继续记录或待检查',['区分未异常与原因不明'])
    d.path([(315,520),(315,548)]);d.text(349,541,'是',23)
    d.box(30,548,570,85,'有限故障模式与事件摘要',['等效泄漏 / 等效受限；保存首次提示时间'])
    # No false merge from a healthy record into a fault-event box.
    d.render()

def sequence():
    d=Drawing('protocol_sequence',580)
    lanes=[(130,'感知节点'),(500,'LoRa接收端'),(870,'本地数据库')]
    for x,title in lanes:
        d.box(x-110,20,220,54,title)
        d.path([(x,74),(x,530)],arrow=False,dashed=True)
    arrows=[(130,500,140,'① 事件：设备 / 会话 / 序号'),(500,870,210,'② 新事件持久化 / 重复去重'),(870,500,280,'③ 写入成功或已存在'),(500,130,350,'④ 匹配ACK，节点再移除队列项')]
    for a,b,y,label in arrows:
        d.path([(a,y),(b,y)]);d.text((a+b)/2,y-16,label,23)
    d.path([(130,425),(500,425)],dashed=True)
    d.text(315,409,'ACK丢失：超时后重发同一事件',23)
    d.path([(500,492),(130,492)],dashed=True)
    d.text(315,476,'已存重复事件仍回复ACK',23)
    d.footer(['拟实施交互；失败保留待确认状态。ACK表示已存储，人工处理确认另记。'])
    d.render()

def bench_model():
    # The concept assembly is built and captured by build_bench_cad.py and
    # capture_bench_views.mjs. Hash checks prevent using stale render geometry.
    from render_bench_plate import render_plate
    render_plate()


def main():
    records.clear()
    for f in [architecture,water,bench_model,circuit,diagnosis,sequence]:f()
    (OUT/'design_provenance.json').write_text(json.dumps({'classification':'proposed_design_not_physical_validation','browser_box_text_bounds':'passed','figures':records,'formal_flowcharts':1,'spatial_geometry_source':'application/models/bench_layout.obj'},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print('Six complementary design figures; one decision flowchart; actual OBJ layout geometry.')

if __name__=='__main__':main()
