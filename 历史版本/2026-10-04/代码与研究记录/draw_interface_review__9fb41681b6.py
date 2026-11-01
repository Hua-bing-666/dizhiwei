"""Three source-linked functional diagrams; no manufacturing schematic claim."""
from pathlib import Path
from html import escape
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures/interface_review'
records=[]
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

def frontend():
    f=Figure('measurement_interfaces',930,'感知节点：双压力与流量采集接口','候选功能原理；压力采用两路4—20mA，流量脉冲转换为3.3V。')
    for y,label,ain in [(180,'P0变送器','AIN0'),(410,'P1变送器','AIN1')]:
        cy=y+46;f.box(30,y,205,92,[label,'两线4—20mA']);f.line([(132,y-32),(132,y)],label='24V to '+label);f.text(132,y-45,'+24V',anchor='middle')
        f.line([(235,cy),(310,cy),(425,cy)],label=label+' current loop and ADC sense tap');f.dot(310,cy)
        f.line([(310,cy),(310,cy+43)]);f.items.append(f'<rect x="300" y="{cy+43}" width="20" height="48" fill="white" stroke="#172b30" stroke-width="2"/>');f.text(285,cy+72,'150Ω',anchor='end');f.line([(310,cy+91),(310,cy+115)]);f.ground(310,cy+115)
        f.box(425,y,230,92,['输入保护与滤波','具体定值待验证'],dash=True);f.line([(655,cy),(740,cy)],label=ain+' protected normal 0.6—3.0V')
    f.items.append('<rect x="740" y="160" width="230" height="430" rx="3" fill="white" stroke="#172b30" stroke-width="2"/>')
    # Input labels must be painted after the housing, rather than hidden by it.
    f.text(750,234,'AIN0');f.text(750,464,'AIN1')
    f.text(855,321,'ADS1115',27,True,'middle');f.text(855,358,'VDD 3.3V',anchor='middle');f.text(855,395,'PGA ±4.096V',anchor='middle')
    f.line([(855,133),(855,160)]);f.text(855,121,'+3.3V / 去耦',anchor='middle')
    for x,value in [(790,'PB7/SDA'),(920,'PB6/SCL')]:f.line([(x,590),(x,615)],label='ADC I2C '+value);f.text(x,642,value,anchor='middle')
    f.line([(855,590),(855,605)]);f.ground(855,605)
    f.text(28,682,'正常量程0.6—3.0V；20mA耗散0.06W；22mA已达3.3V。')
    f.box(30,725,205,104,['SEN0549','5V供电']);f.box(395,715,260,124,['SN74LVC1G17','VCC 3.3V','输入允许至5.5V']);f.box(805,725,165,104,['TIM2_CH1','PA0计数'])
    f.line([(235,777),(395,777)],arrow=True,label='5V pulse to tolerant buffer input');f.text(315,755,'5V脉冲',anchor='middle')
    f.line([(655,777),(805,777)],arrow=True,label='3.3V buffered pulse to PA0');f.text(730,755,'3.3V',anchor='middle')
    f.text(28,881,'台架共地；24V不进ADC。保护、掉电注入、实际引脚与标定尚待验证。')
    f.text(28,915,'候选功能图，非可投板原理图或接线完成证明。',color='#52636a');f.save()

def resources():
    f=Figure('power_and_pin_resources',785,'电源与引脚：一节点的资源分配','电流为设计预留，非实测功耗；主控、ADC与存储使用独立3.3V稳压。')
    f.text(243,144,'节点电源分配',26,True,'middle');f.box(30,190,145,84,['5V入口','候选≥1A'],fill='#eef5f2');f.box(270,190,190,84,['3.3V降压','候选≥1A'],fill='#eaf1f7')
    f.line([(175,232),(270,232)],arrow=True,label='5V to external 3.3V converter');f.dot(230,232)
    f.box(30,360,190,124,['E220','VCC 5V','IO 3.3V'],fill='#eef5f2');f.box(270,360,190,124,['SEN0549','VCC 5V','经缓冲后计数'],fill='#f8f2e8')
    f.line([(102,274),(102,360)],arrow=True,label='5V radio power');f.line([(230,232),(230,330),(365,330),(365,360)],arrow=True,label='5V flow sensor power')
    f.line([(460,232),(487,232),(487,518),(245,518),(245,555)],arrow=True,label='3.3V to MCU ADC and SD');f.text(255,547,'3.3V',color='#3c6284')
    f.box(30,555,430,105,['主控 + ADC + microSD','360mA预留，未测瞬态电流'],fill='#eaf1f7')
    f.text(747,144,'候选引脚表',26,True,'middle');f.items.append('<rect x="530" y="173" width="440" height="482" fill="#fafbfb" stroke="#ccd5d8"/>')
    rows=[('ADC / I²C','PB6 / PB7'),('流量计数','PA0'),('LoRa / UART','PA9 / PA10'),('microSD / SPI','PA4—PA7'),('AUX 输入','PB0'),('M0 / M1','PB10 / PB11'),('SWD 保留','PA13 / PA14'),('调试串口','PA2 / PA3')]
    for i,(label,pin) in enumerate(rows):
        y=208+i*57;f.text(546,y,label);f.text(774,y,pin)
        if i<len(rows)-1:f.line([(542,y+18),(958,y+18)],color='#d5dddf')
    f.text(530,695,'PB1为人工B状态标记，非阀位实测。')
    f.text(28,738,'24V另供两压力回路；接收端5V供电、USB-TTL须为3.3V通信电平。')
    f.text(28,771,'接线前核对板上稳压/上拉，避免USB与外部电源互相回灌。',color='#52636a');f.save()

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
