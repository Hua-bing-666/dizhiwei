"""Three source-linked functional diagrams; no manufacturing schematic claim."""
from pathlib import Path
from html import escape
import hashlib,json,subprocess,uuid,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures/interface_review'
EDGE='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
records=[]
def render_png(name,height):
    """SVG → PNG（Edge 无头截图 ×2 缩放 + 裁白边），与 SVG 同目录输出，保证可复现。"""
    svg=(OUT/(name+'.svg')).read_text(encoding='utf-8')
    html='<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:white}svg{display:block}</style>'+svg
    tmp=ROOT/'tmp'/'iface_render';tmp.mkdir(parents=True,exist_ok=True)
    hp=tmp/(name+'.html');hp.write_text(html,encoding='utf-8')
    png=tmp/(name+'.png');png.unlink(missing_ok=True)
    prof=tmp/('p-'+uuid.uuid4().hex[:8])
    kw={'creationflags':subprocess.CREATE_NO_WINDOW} if hasattr(subprocess,'CREATE_NO_WINDOW') else {}
    subprocess.run([EDGE,'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars',
                    '--force-device-scale-factor=2',f'--window-size=1000,{height}',
                    f'--user-data-dir={prof}',f'--screenshot={png}',hp.as_uri()],
                   capture_output=True,timeout=90,**kw)
    deadline=time.monotonic()+25
    while not png.exists() or png.stat().st_size<2000:
        if time.monotonic()>deadline:raise RuntimeError(f'{name}: png 未生成')
        time.sleep(0.2)
    dest=OUT/(name+'.png')
    try:
        from PIL import Image
        import numpy as np
        im=Image.open(png).convert('RGB');a=np.array(im.convert('L'))
        rows=np.where((a<250).any(axis=1))[0];cols=np.where((a<250).any(axis=0))[0]
        pad=16
        im=im.crop((max(0,cols[0]-pad),max(0,rows[0]-pad),min(im.width,cols[-1]+pad),min(im.height,rows[-1]+pad)))
        im.save(dest)
    except ImportError:
        dest.write_bytes(png.read_bytes())
class Figure:
    def __init__(self,name,height,title,subtitle):
        self.name=name;self.height=height;self.items=[];self.connections=[];self.text(28,48,title,30,True);self.text(28,88,subtitle,23,color='#52636a')
    def text(self,x,y,value,size=23,bold=False,anchor='start',color='#142a30'):
        self.items.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}" fill="{color}">{escape(value)}</text>')
    def line(self,points,arrow=False,dash=False,color='#172b30',label=None):
        self.items.append('<path d="M '+' L '.join(f'{x} {y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="2"'+(' stroke-dasharray="7 5"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
        if label:self.connections.append({'meaning':label,'points':points})
    def box(self,x,y,w,h,lines,fill='white',dash=False):
        self.items.append(f'<g data-box="true" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" stroke="#26383d" stroke-width="2"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')
        start=y+(h-(len(lines)-1)*32)/2+8
        for i,line in enumerate(lines):self.text(x+w/2,start+i*32,line,24 if i==0 else 23,i==0,'middle')
        self.items.append('</g>')
    def dot(self,x,y):self.items.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#172b30"/>')
    def ground(self,x,y):
        for dy,w in [(0,32),(7,22),(14,12)]:self.line([(x-w/2,y+dy),(x+w/2,y+dy)])
    def save(self):
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{self.height}" viewBox="0 0 1000 {self.height}" data-classification="candidate_functional_design_not_physical_test"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#172b30"/></marker></defs><rect width="1000" height="{self.height}" fill="white"/><g font-family="Microsoft YaHei, SimSun, sans-serif">'+''.join(self.items)+'</g></svg>\n'
        (OUT/(self.name+'.svg')).write_text(svg,encoding='utf-8',newline='\n')
        records.append({'name':self.name,'width':1000,'height':self.height,'classification':'candidate_functional_design_not_build_released','connections':self.connections,'svg_sha256':hashlib.sha256(svg.encode()).hexdigest(),'minimum_text_px':23,'minimum_text_pt_at_425pt_width':23*425/1000})
        render_png(self.name,self.height)

def frontend():
    f=Figure('measurement_interfaces',950,'感知节点：差压/参照/流量采集接口','单只差压变送器测区段压降 + 干管参照表压；ADC 主路径为 MCU 内置 12 位。')
    # 供电通栏：24 V 只供两线制变送器，高边开关间歇供电（v2.2 契约 H3/H10）
    f.box(30,115,940,96,['24 V 升压 XL6009：电池 12—16.8 V → 24 V','EN 受 PB0 控制（高边开关）；采样窗内上电、读完即断电','断电期间 ADC 停止采样'],fill='#eef5f2')
    # 差压支路（区段 R 两端取压）
    f.box(30,225,230,124,['差压变送器 MDM490','+24 V 间歇供电','0—40 kPa · 跨区段R'])
    f.line([(260,287),(300,287),(425,287)],label='differential current loop and ADC sense tap');f.dot(300,287)
    f.line([(300,287),(300,330)]);f.items.append(f'<rect x="290" y="330" width="20" height="48" fill="white" stroke="#172b30" stroke-width="2"/>');f.text(315,359,'150Ω',anchor='start');f.line([(300,378),(300,402)]);f.ground(300,402)
    f.box(425,225,230,124,['输入保护与滤波','BAT54S 钳位 + TVS','具体定值待验证'],dash=True);f.line([(655,287),(740,287)],label='AIN0 protected normal 0.6—3.0V')
    # 干管参照支路
    f.box(30,425,230,124,['干管参照表压','+24 V 间歇供电','0—200 kPa'])
    f.line([(260,447),(300,447),(425,447)],label='reference current loop and ADC sense tap');f.dot(300,447)
    f.line([(300,447),(300,490)]);f.items.append(f'<rect x="290" y="490" width="20" height="48" fill="white" stroke="#172b30" stroke-width="2"/>');f.text(315,519,'150Ω',anchor='start');f.line([(300,538),(300,562)]);f.ground(300,562)
    f.box(425,425,230,124,['输入保护与滤波','BAT54S 钳位 + TVS','具体定值待验证'],dash=True);f.line([(655,447),(740,447)],label='AIN1 protected normal 0.6—3.0V')
    # 采集主路径：GD32 内置 12 位 ADC（PA0/PA1）；SGM58031 为可选升级，与 DS3231 共用 I²C1 重映射总线
    f.items.append('<rect x="740" y="225" width="230" height="275" rx="3" fill="white" stroke="#172b30" stroke-width="2"/>')
    f.text(750,249,'AIN0');f.text(750,449,'AIN1')
    f.text(855,300,'GD32F103CBT6',27,True,'middle');f.text(855,332,'内置 12 位 ADC · 主路径',anchor='middle');f.text(855,364,'PA0←AIN0（ΔP）',anchor='middle');f.text(855,396,'PA1←AIN1（干管参照）',anchor='middle')
    f.line([(855,211),(855,225)],label='+3.3V to MCU');f.text(865,238,'+3.3V',anchor='start')
    # I²C1 重映射总线：PB8/PB9 横总线，下挂 SGM58031（可选）与 DS3231
    f.line([(790,500),(790,560)],label='I2C1 remap PB8 SDA');f.line([(880,500),(880,560)],label='I2C1 remap PB9 SCL')
    f.line([(430,560),(880,560)]);f.text(775,540,'PB8/SDA',anchor='end');f.text(895,540,'PB9/SCL',anchor='start')
    f.box(430,585,240,105,['SGM58031 · 可选升级','16 位 I²C · 非必装','VDDA 噪声大时加装'],dash=True)
    f.line([(490,560),(490,585)],dash=True);f.line([(610,560),(610,585)],dash=True)
    f.box(740,600,180,64,['DS3231 RTC','I²C 总线上挂载'])
    f.line([(790,560),(790,600)]);f.line([(880,560),(880,600)])
    # 脉冲链路：5 V 脉冲 → 分压 + 施密特整形 → PB6/TIM4_CH1
    f.box(30,700,205,104,['SEN0549','5V供电']);f.box(395,690,260,124,['SN74LVC1G17','VCC 3.3V','10k+20k 分压输入']);f.box(805,700,165,104,['TIM4_CH1','PB6 计数'])
    f.line([(235,752),(395,752)],arrow=True,label='5V pulse to divider input');f.text(315,730,'5V脉冲',anchor='middle')
    f.line([(655,752),(805,752)],arrow=True,label='3.3V shaped pulse to PB6');f.text(730,730,'3.3V',anchor='middle')
    f.text(28,850,'量程 0.6—3.0V；20mA耗散0.06W；30mA故障电流由钳位管旁路。')
    f.text(28,884,'16× 过采样；台架共地；24V不进ADC；保护、掉电注入、实际引脚与标定尚待验证。')
    f.text(28,918,'候选功能图，非可投板原理图或接线完成证明。',color='#52636a');f.save()

def resources():
    f=Figure('power_and_pin_resources',785,'电源与引脚：一节点的资源分配','电流为设计预留，非实测功耗；主控、ADC与存储使用独立3.3V稳压。')
    f.text(243,144,'节点电源分配',26,True,'middle');f.box(30,190,145,84,['5V入口','候选≥1A'],fill='#eef5f2');f.box(270,190,190,84,['3.3V降压','候选≥1A'],fill='#eaf1f7')
    f.line([(175,232),(270,232)],arrow=True,label='5V to external 3.3V converter');f.dot(230,232)
    f.box(30,360,190,124,['E220','VCC 5V','IO 3.3V'],fill='#eef5f2');f.box(270,360,190,124,['SEN0549','VCC 5V','经缓冲后计数'],fill='#f8f2e8')
    f.line([(102,274),(102,360)],arrow=True,label='5V radio power');f.line([(230,232),(230,330),(365,330),(365,360)],arrow=True,label='5V flow sensor power')
    f.line([(460,232),(487,232),(487,518),(245,518),(245,555)],arrow=True,label='3.3V to MCU ADC and SD');f.text(255,547,'3.3V',color='#3c6284')
    f.box(30,555,430,105,['主控（内置 ADC）+ microSD','360mA预留，未测瞬态电流'],fill='#eaf1f7')
    f.text(747,144,'候选引脚表',26,True,'middle');f.items.append('<rect x="530" y="173" width="440" height="482" fill="#fafbfb" stroke="#ccd5d8"/>')
    rows=[('内置 ADC（主路径）','PA0 / PA1'),('I²C1 总线','PB8 / PB9'),('流量计数','PB6 / TIM4_CH1'),('LoRa / UART','PA9 / PA10'),('microSD / SPI','PA4—PA7'),('24V 高边开关','PB0'),('SWD 保留','PA13 / PA14'),('调试串口','PA2 / PA3')]
    for i,(label,pin) in enumerate(rows):
        y=208+i*57;f.text(546,y,label);f.text(774,y,pin)
        if i<len(rows)-1:f.line([(542,y+18),(958,y+18)],color='#d5dddf')
    f.text(28,700,'PB8/PB9 总线挂 DS3231 与可选 SGM58031；')
    f.text(28,733,'PB1 为人工 B 状态标记，非阀位实测；24 V 仅供两线制变送器。')
    f.text(28,766,'USB-TTL 须为 3.3 V 电平；接线前核对稳压/上拉，避免电源回灌。',color='#52636a');f.save()

def sequence():
    f=Figure('durable_event_sequence',930,'事件可靠交付：持久化确认与重复去重','主机参考协议已执行字节/事务检查；图示为拟接入真实LoRa的职责关系。')
    for x,title in [(135,'节点日志/模块'),(510,'接收端/PC服务'),(865,'SQLite文件')]:
        f.box(x-110,125,220,58,[title]);f.line([(x,183),(x,845)],dash=True,color='#95a2a7')
    f.text(153,223,'本地事件先持久入队',23)
    arrows=[(135,510,275,'① EVENT + 三元身份'),(510,865,355,'② 校验、写入或去重'),(865,510,430,'③ COMMIT已成功'),(510,135,505,'④ ACK：事件身份+指纹')]
    for a,b,y,label in arrows:f.line([(a,y),(b,y)],arrow=True,label=label);f.text((a+b)/2,y-18,label,anchor='middle')
    f.text(153,540,'节点匹配后标记已送达',23)
    f.line([(28,562),(972,562)],color='#d5dddf');f.text(28,592,'以下为另一条路径：上面的ACK未到达节点',23,True)
    f.line([(135,649),(510,649)],arrow=True,dash=True,label='ACK lost then resend exact event');f.text(323,631,'ACK丢失→同一事件重发',anchor='middle')
    f.line([(510,721),(865,721)],arrow=True,dash=True,label='check exact existing committed body');f.text(687,703,'核对已存原记录与摘要',anchor='middle')
    f.line([(865,774),(510,774)],arrow=True,dash=True,label='commit duplicate lookup transaction');f.text(687,756,'原记录一致且事务完成',anchor='middle')
    f.line([(510,832),(135,832)],arrow=True,dash=True,label='same ACK for exact duplicate');f.text(323,814,'重复已存→再次回复ACK',anchor='middle')
    f.text(28,880,'ACK表示接收端保存；人工已查看、处置与同工况复测分别记录。')
    f.text(28,915,'8次/300秒候选上限；超限保留未确认记录，不承诺必然送达。',color='#52636a');f.save()

if __name__=='__main__':
    frontend();resources();sequence()
    sources=[Path(__file__),ROOT/'simulation/interface_review/interface_spec.json',ROOT/'simulation/interface_review/hardware_checks.json',ROOT/'simulation/interface_review/protocol_checks.json']
    result={'classification':'candidate_functional_diagrams','physical_data':False,'figures':records,'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (OUT/'figure_provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');print('Three functional SVG diagrams written; actual browser rendering/validation required.')
