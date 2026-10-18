"""Four print-readable plates sourced from the staged, hash-matched OCCT scene."""
from pathlib import Path
import base64,hashlib,io,json
from PIL import Image,ImageChops
import build_application_design_figures as design
from build_application_design_figures import Drawing
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'application/figures/collection_review'
design.OUT=OUT
VIEWS=json.loads((ROOT/'application/models/collection_review/bench_views.json').read_text(encoding='utf-8'))
AUDIT=json.loads((ROOT/'application/models/collection_review/collection_feasibility.json').read_text(encoding='utf-8'))
META=json.loads((ROOT/'application/models/collection_review/bench_layout.json').read_text(encoding='utf-8'))
assert META['base_envelope']==[900,520] and META['pipe_centre_height']==140
assert META['collection_design']['inner_radius_mm']==60 and META['collection_design']['inner_height_mm']==60
assert abs(AUDIT['geometry_checks']['outlet_to_lip_vertical_gap_mm']-20)<1e-4
assert abs(AUDIT['geometry_checks']['support_foot_to_tray_min_distance_mm']-15)<1e-4
assert hashlib.sha256((ROOT/'application/models/collection_review/bench_scene.json').read_bytes()).hexdigest()==VIEWS['sceneSha256']

def place(d,name,x,y,width,crop=False):
    raw=OUT/(name+'.png');assert hashlib.sha256(raw.read_bytes()).hexdigest()==VIEWS['imageSha256'][raw.name]
    im=Image.open(raw).convert('RGB');left=top=0
    if crop:
        mask=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L').point(lambda v:255 if v>13 else 0)
        a,b,c,e=mask.getbbox();left=max(0,a-24);top=max(0,b-24);im=im.crop((left,top,min(im.width,c+24),min(im.height,e+24)))
    buf=io.BytesIO();im.save(buf,format='PNG');height=width*im.height/im.width
    d.items.append(f'<image x="{x}" y="{y}" width="{width}" height="{height}" href="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')
    return lambda point:(x+(point[0]*2-left)*width/im.width,y+(point[1]*2-top)*width/im.width),height

NAMES=['P0区段入口压力','R等效受限元件','P1受限下游压力','Q测量A总流量','A正常等效负载','B健康负载切换','泄漏独立收集','采集与LoRa节点']
KEYS=['P0','R','P1','Q','A','B','leak','node']
def badge(d,x,y,n,dx,dy):
    cx,cy=x+dx,y+dy;length=(dx*dx+dy*dy)**.5
    d.path([(x,y),(cx-dx/length*17,cy-dy/length*17)],arrow=False,color='#405d66')
    d.items.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="white" stroke="#405d66" stroke-width="1.8"/>')
    d.text(cx,cy+8,str(n),23,True)
def legend(d,y):
    for i,name in enumerate(NAMES):d.text(28+(i%2)*490,y+(i//2)*34,f'{i+1}  {name}',23,anchor='start')
def intro(d,title,subtitle):
    d.text(28,38,title,28,True,anchor='start');d.text(28,74,subtitle,23,anchor='start')
def overview():
    d=Drawing('collection_overview',840)
    intro(d,'清水台架：测量、注入与独立计量','候选结构用于预实验和重复验证；设备包络暂定，尚未制造。')
    project,h=place(d,'bench_isometric',40,107,920,True)
    offsets=[(-17,-28),(-8,-31),(-10,-29),(-5,-30),(26,-27),(-23,-27),(-50,20),(-65,22)]
    for i,key in enumerate(KEYS):badge(d,*project(VIEWS['projectedAnchors']['iso'][key]),i+1,*offsets[i])
    ly=107+h+37;legend(d,ly)
    d.text(28,ly+148,'A支路：P0 → R → P1 → Q → 正常负载与泄漏分流。',23,anchor='start')
    d.text(28,ly+181,'Q包含正常与泄漏流量；B只提供正常负载变化对照。',23,anchor='start')
    d.height=int(ly+220)
    d.render()
def top():
    d=Drawing('collection_installation',890)
    intro(d,'俯视安装：尺寸边界与取出空间','底板900×520mm，管中心高140mm；尺寸为概念设计值。')
    project,h=place(d,'bench_top',50,106,850)
    offsets=[(-8,-32),(-8,-32),(-8,-32),(-8,-32),(25,-32),(-8,33),(-35,-12),(68,0)]
    for i,key in enumerate(KEYS):badge(d,*project(VIEWS['projectedAnchors']['top']['leak_rim' if key=='leak' else key]),i+1,*offsets[i])
    a=project(VIEWS['projectedAnchors']['top']['base_left']);b=project(VIEWS['projectedAnchors']['top']['base_right']);c=project(VIEWS['projectedAnchors']['top']['base_back'])
    d.path([(a[0],a[1]+6),(a[0],590)],False);d.path([(b[0],b[1]+6),(b[0],590)],False);d.path([(a[0],583),(b[0],583)],False)
    d.label((a[0]+b[0])/2,580,'900 mm')
    d.path([(b[0]+6,b[1]),(934,b[1])],False);d.path([(c[0]+6,c[1]),(934,c[1])],False);d.path([(924,c[1]),(924,b[1])],False)
    d.label(925,(c[1]+b[1])/2,'520 mm')
    legend(d,628)
    d.text(28,778,'杯外径126mm；托盘内宽140mm；支架脚与托盘间距15mm。',23,anchor='start')
    d.text(28,812,'拟先上抬8mm再向前滑出225mm；20个位置无实体重叠。',23,anchor='start')
    d.text(28,846,'取出路径仅做离散几何检查，手部空间及防溅仍需实物复核。',23,anchor='start')
    d.render()
def interfaces():
    d=Drawing('collection_interfaces',650)
    intro(d,'取压接口：模型能够说明什么','P0与P1采用相同接口思路；下图为P0局部，非厂家尺寸图。')
    place(d,'bench_pressure_detail',28,110,470)
    d.text(535,145,'侧向取压与参考测量',25,True,anchor='start')
    for i,line in enumerate(['压力传感器设置在取压三通上。','P0/P1夹住等效受限区段。','参照表接口与排气需实装核定。']):d.text(535,188+i*36,line,23,anchor='start')
    d.text(535,338,'装配前必须核对',25,True,anchor='start')
    for i,line in enumerate(['螺纹制式、内径与插接长度；','量程、取压方向与排气位置；','支架孔位、线缆防水与应力；','真实接头与仪表的安装高度。']):d.text(535,381+i*36,line,23,anchor='start')
    d.text(28,576,'实体通道中心点检查通过，不代表整段水路压损、密封或承压合格。',23,anchor='start')
    d.text(28,612,'采购尺寸与标定结果确定后，才能冻结装配图和最终加工孔位。',23,anchor='start')
    d.render()
def metering():
    d=Drawing('collection_metering',910)
    intro(d,'泄漏计量：容量、自由出流与实验时长','短时收集与长时运行分开设计；当前杯体只服务短时取样。')
    place(d,'bench_leak_detail',28,115,490)
    d.text(545,140,'竖向关系示意（非比例剖面）',23,True,anchor='start')
    d.items.append('<rect x="655" y="175" width="40" height="48" fill="#bb8954" stroke="black" stroke-width="2"/><path d="M 578 273 L 578 341 L 779 341 L 779 273" fill="none" stroke="black" stroke-width="3"/>')
    d.text(593,202,'出口',23,anchor='start');d.text(583,320,'杯体',23,anchor='start')
    d.path([(695,223),(853,223)],False,True,color='#654c32');d.path([(779,273),(853,273)],False,True,color='#654c32')
    d.path([(845,223),(845,273)],False,color='#654c32');d.text(865,255,'20 mm',23,anchor='start')
    d.text(725,207,'112 mm',23,anchor='start');d.text(865,302,'92 mm',23,anchor='start')
    d.text(545,392,'容量与计量待核项',25,True,anchor='start')
    for i,line in enumerate(['内腔半径60mm、高60mm；','先标定有效容积，再计时30秒；','Q泄漏 = 实收水量 ÷ 收集时长。','防溅、称重、计时与同步待实测。']):d.text(545,432+i*36,line,23,anchor='start')
    cal=AUDIT['design_calculation'];scale=520/700
    for i,(label,value,color) in enumerate([('原内腔',cal['baseline_geometric_capacity_ml'],'#b98b70'),('30秒所需',cal['required_with_margin_ml'],'#71818a'),('候选内腔',cal['candidate_geometric_capacity_ml'],'#557d77')]):
        y=590+i*55;d.text(28,y+24,label,23,anchor='start');d.items.append(f'<rect x="190" y="{y}" width="{value*scale}" height="30" fill="{color}"/>');d.text(750,y+24,f'{value:.1f} mL',23,anchor='start')
    d.text(28,785,'设计最大泄漏1.055L/min；所需容量含25%余量，尚未实测或标定。',23,anchor='start')
    d.text(28,821,'同工况10分钟需约13.19L（含余量）；本杯不能承担长时收集。',23,anchor='start')
    d.text(28,857,'长时试验需独立自由排水或回收路径，未落实前不得宣称连续可用。',23,anchor='start')
    d.render()
if __name__=='__main__':
    overview();top();interfaces();metering()
    proof={'classification':'actual_OCCT_render_and_uncalibrated_design_calculation','scene_sha256':VIEWS['sceneSha256'],'source_render_sha256':VIEWS['imageSha256'],'figures':design.records,'manufacturing_validated':False}
    (OUT/'plate_provenance.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
