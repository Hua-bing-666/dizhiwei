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
    d=Drawing('system_scope',470)
    for x,title,lines in [(30,'测量与诊断节点',['P0 / P1 / Q与阀态','原始日志 / 有限提示']), (370,'LoRa接收端',['持久化 / ACK / 去重','SQLite事件记录']), (710,'本地管理软件',['趋势 / 质量 / 事件','人工核查 / 处理记录'])]:
        d.box(x,65,260,145,title,lines,fill={30:'#eaf2f8',370:'#edf4ed',710:'#f2edf7'}[x],stroke='#344b59')
    d.path([(290,137),(370,137)]);d.text(330,114,'LoRa',23)
    d.path([(370,180),(290,180)]);d.text(330,202,'ACK',23)
    d.path([(710,165),(630,165)]);d.text(670,192,'确认',23)
    d.path([(630,110),(710,110)]);d.text(670,87,'数据',23)
    d.box(30,290,260,90,'清水台架与参考仪器',['操作 / 参考表 / 收集量'],fill='#faf2e8',stroke='#715842')
    d.box(370,290,600,90,'独立实验评价与可复现资料',['独立标签对照本地提示、远端接收与整机测量'],fill='#f4f5f5',stroke='#43525b')
    d.path([(160,290),(160,210)])
    d.text(200,259,'采样',23)
    d.path([(290,335),(370,335)])
    d.path([(260,210),(260,245),(435,245),(435,290)],dashed=True)
    d.path([(500,210),(500,290)],dashed=True)
    d.path([(840,210),(840,290)],dashed=True)
    d.footer(['实线为测量或业务连接；虚线为评价数据。管理确认不等于自动阀控。'])
    d.render()

def water():
    d=Drawing('dual_pressure_layout',650)
    # Pressure sensors are pressure taps, not through-flow instruments.
    d.box(25,122,150,90,'可调供水',['工作点待核'],fill='#eaf2f8',stroke='#42657b')
    d.path([(175,167),(215,167),(215,145),(875,145)],arrow=False,color='#42657b')
    d.path([(215,167),(215,385),(875,385)],arrow=False,color='#42657b')
    for x,label in [(285,'P0'),(555,'P1')]:
        d.path([(x,145),(x,88)],arrow=False);d.sensor(x,60,label)
    d.box(350,118,140,54,'受限阀 R',fill='#fbf1db',stroke='#826521')
    d.sensor(660,145,'Q')
    d.box(815,118,160,54,'A负载 Cₙ',fill='#edf4ed',stroke='#526b54')
    d.path([(750,145),(750,247),(815,247)],arrow=False,color='#a26437')
    d.box(815,220,160,54,'泄漏阀 Cₗ',fill='#faede2',stroke='#a26437')
    d.path([(895,274),(895,293)],arrow=True)
    d.box(795,293,195,54,'独立收集计时',fill='#faede2',stroke='#a26437')
    d.box(350,358,140,54,'B切换阀')
    d.box(815,358,160,54,'B正常负载',fill='#edf4ed',stroke='#526b54')
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
    """Export the actual geometry used by the orthographic SVG to OBJ."""
    vertices=[];faces=[];objects=[]
    def add(name,vs,fs,color):
        offset=len(vertices);vertices.extend(vs)
        objfaces=[tuple(offset+i for i in f) for f in fs];faces.extend(objfaces)
        objects.append((name,np.asarray(vs),fs,color))
    def cuboid(name,origin,size,color):
        x,y,z=origin;a,b,c=size
        vs=[(x+i*a,y+j*b,z+k*c) for k in (0,1) for j in (0,1) for i in (0,1)]
        fs=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
        add(name,vs,fs,color)
    def cylinder(name,p0,p1,r,color,n=16):
        p0,p1=np.array(p0,dtype=float),np.array(p1,dtype=float)
        axis=(p1-p0)/np.linalg.norm(p1-p0)
        helper=np.array([0.,0.,1.]) if abs(axis[2])<.8 else np.array([1.,0.,0.])
        u=np.cross(axis,helper);u/=np.linalg.norm(u);v=np.cross(axis,u)
        vs=[tuple(p+r*(math.cos(t)*u+math.sin(t)*v)) for p in (p0,p1) for t in np.arange(n)*2*math.pi/n]
        fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        add(name,vs,fs,color)
    def pipe(name,points,color='#567e92'):
        for k,(a,b) in enumerate(zip(points,points[1:])):cylinder(name+str(k),a,b,7,color)
    cuboid('base',(0,0,-16),(900,520,16),'#dce2e3')
    pipe('supply',[(90,350,60),(150,350,60),(150,125,60),(850,125,60)])
    pipe('B',[(150,250,60),(150,330,60),(850,330,60)])
    pipe('return',[(850,125,60),(850,410,60),(90,410,60),(90,390,45)])
    pipe('leak',[(695,125,60),(695,235,60),(780,235,60),(780,235,35)],'#ac7755')
    cuboid('water_source',(40,350,0),(100,110,95),'#b7cbd5')
    for name,x,y in [('P0',230,125),('P1',485,125)]:
        cylinder(name+'_tap',(x,y,60),(x,y,82),9,'#738b95')
        cylinder(name,(x,y,82),(x,y,134),16,'#9aa5ad')
    for name,x,y in [('restriction',365,125),('B_valve',365,330),('leak_valve',730,235)]:
        cuboid(name,(x-18,y-14,49),(36,28,22),'#7e9891')
        cylinder(name+'_stem',(x,y,70),(x,y,93),5,'#667572')
        cuboid(name+'_handle',(x-25,y-7,91),(50,14,8),'#44574f')
    cylinder('Q',(580,125,60),(635,125,60),17,'#546c7c')
    for name,y in [('A_load',125),('B_load',330)]:cylinder(name,(780,y,60),(810,y,60),14,'#7d9198')
    cylinder('collection',(780,235,0),(780,235,45),28,'#d8b592')
    cuboid('dry_node',(435,445,0),(185,65,50),'#657d73')
    output=ROOT/'application/models';output.mkdir(parents=True,exist_ok=True)
    lines=['# Proposed bench layout; units mm; primitive envelopes only.']
    lines += [f'v {x:.4f} {y:.4f} {z:.4f}' for x,y,z in vertices]
    lines += ['f '+' '.join(str(i+1) for i in f) for f in faces]
    (output/'bench_layout.obj').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    projected=[]
    def project(p):
        x,y,z=p
        return np.array([220+.72*x-.36*y,85+.20*x+.38*y-.75*z])
    for name,vs,fs,color in objects:
        for face in fs:
            points=vs[list(face)]
            depth=np.mean(points@np.cross([.72,-.36,0],[.20,.38,-.75]))
            projected.append((name=='base',depth,[project(p) for p in points],color))
    d=Drawing('bench_model',660)
    d.text(25,35,'双支路清水台架 三维布置概念',27,True,anchor='start')
    # Base is behind every mounted object; a centroid painter otherwise covers
    # rear pipes with a large top face despite their positive height.
    for is_base,depth,points,color in sorted(projected,key=lambda f:(not f[0],f[1])):
        coords=' '.join(f'{x:.2f},{y:.2f}' for x,y in points)
        d.items.append(f'<polygon points="{coords}" fill="{color}" stroke="#52605c" stroke-width="0.6"/>')
    labels=[('P0',(230,125,134),(305,72)),('受限阀',(365,125,95),(450,88)),('P1',(485,125,134),(565,88)),('Q',(610,125,80),(695,105)),('A正常负载',(795,125,70),(910,158)),('泄漏计量杯',(780,235,45),(918,285)),('B切换阀',(365,330,95),(320,322)),('B正常负载',(795,330,70),(885,398)),('借用供水接口',(85,405,95),(130,317)),('干区感知节点',(530,477,50),(540,495))]
    for text,p,(tx,ty) in labels:
        xy=project(p);end_y=ty+8 if ty<xy[1] else ty-29
        d.path([tuple(xy),(tx,end_y)],arrow=False)
        d.text(tx,ty,text,23)
    d.text(25,555,'底板包络暂设900×520mm；管径、器件外形与接头均为占位参数。',23,anchor='start')
    d.footer(['用于检查布置、检修空间、干湿分区与独立收集路径；不是样机照片或制造图。', '保存OBJ几何源；实际尺寸、耐压、装配与保护须按采购器件重新核定。'])
    d.render()
    (output/'bench_layout.json').write_text(json.dumps({'classification':'parametric_layout_concept_not_manufacturing_model','units':'mm','base_envelope':[900,520],'vertices':len(vertices),'faces':len(faces),'components':[name for name,_,_,_ in objects],'electrical_enclosure_position':'dry_front_zone','leak_collection':'separate_vessel_not_connected_to_normal_return','hydraulic_geometry_calibrated':False},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

def main():
    records.clear()
    for f in [architecture,water,bench_model,circuit,diagnosis,sequence]:f()
    (OUT/'design_provenance.json').write_text(json.dumps({'classification':'proposed_design_not_physical_validation','browser_box_text_bounds':'passed','figures':records,'formal_flowcharts':1,'spatial_geometry_source':'application/models/bench_layout.obj'},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print('Six complementary design figures; one decision flowchart; actual OBJ layout geometry.')

if __name__=='__main__':main()
