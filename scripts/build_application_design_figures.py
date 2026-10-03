"""Design diagrams for application arguments, not verified wiring/schematics."""
from pathlib import Path
import subprocess
from author_visual_redesign import txt,box,ln,arrow,para,G,A,B,M,S
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures';TMP=ROOT/'tmp/visual_redesign'
EDGE=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
def render(name,contents,w,h):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'+box(0,0,w,h,'#FFFFFF')+contents+'</svg>'
    (OUT/(name+'.svg')).write_text(svg,encoding='utf-8',newline='\n')
    p=TMP/(name+'.html');p.write_text(f'<meta charset="utf-8"><style>html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}svg{{width:{w}px;height:{h}px}}</style>'+svg,encoding='utf-8')
    subprocess.run([EDGE,'--headless=new','--disable-gpu','--hide-scrollbars','--no-first-run','--force-device-scale-factor=2','--user-data-dir='+str(TMP/'figure-profile'),f'--window-size={w},{h}','--screenshot='+str(OUT/(name+'.png')),p.as_uri()],capture_output=True,check=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
def component(x,y,w,h,title,detail):
    return box(x,y,w,h,S,'#C7D2CB',5)+txt(x+15,y+32,title,24,G,True)+para(x+15,y+65,detail,w-30,21,M,leading=29)
v=''
for y,title,detail in [(30,'双压力4—20mA','150Ω / ADS1115'),(147,'SEN0549流量','脉冲计数 / 电平转换'),(264,'阀态与配置','状态 / 编号 / 质量')]:
    v+=component(15,y,254,96,title,detail)+arrow(272,y+49,363,y+49,G)
v+=component(369,30,244,330,'STM32F103C8T6','时间与转换记录\n质量检查\n健康参照与特征\n持续判据\n有限模式 / 待检查')
v+=component(694,42,190,112,'E220 LoRa','UART 3.3V\n发收与确认')+arrow(616,91,689,91,G)
v+=component(689,236,195,155,'microSD日志','原始测量\n状态与质量\n时间与配置')+arrow(616,292,684,292,G)
v+=ln(22,427,880,427,B,2,'7,5')+txt(25,416,'稳压供电与接口防护：按实际器件电平、功耗及输入输出核定',21,B)
v+=txt(25,477,'候选连接方案；接口保护、引脚分配、电路与存储尚需实物验证。',21,M)
render('hardware_node',v,900,500)
v=''
steps=[('原始测量与运行状态','P0 / P1 / Q、阀态、时间、质量'),('健康参照与状态关联','同工况参考冻结；切换单独评价'),('可解释特征','K=Q/√P1；R̂=(P0−P1)/Q²'),('持续偏离与模式判断','强基线对照；记录首次可靠提示')]
for j,(title,detail) in enumerate(steps):
    y=16+j*123;v+=component(22,y,518,104,title,detail)
    if j<3:v+=arrow(280,y+107,280,y+120,G)
v+=component(616,16,263,104,'无效数据','停止原因判断')+arrow(543,66,610,66,A)
v+=component(616,139,263,104,'切换与漂移挑战','保留数据与误报记录')+arrow(543,189,610,189,A)
v+=component(616,263,263,104,'信息不足','异常待检查')+arrow(543,313,610,313,A)
v+=component(616,386,263,104,'有限故障模式','等效泄漏 / 等效受限')+arrow(543,436,610,436,G)
v+=txt(24,535,'输出需结合标定、状态和可观测条件；流程为拟实施设计。',22,M)
render('diagnosis_flow',v,900,560)
v=component(18,12,367,85,'感知节点','本地发现 → 缓存与序号')+component(515,12,367,85,'LoRa接收端','存储 → ACK → 网页呈现')
v+=ln(202,103,202,398,G,2)+ln(699,103,699,398,G,2)
for y,title,direction,color in [(148,'事件摘要与会话序号',1,G),(213,'存储后ACK；节点确认移除',-1,B),(278,'ACK超时重试；接收端去重',1,G),(343,'断链恢复补发；溢出留记录',1,A)]:
    v+=txt(450,y-13,title,22,color,False,'middle')
    v+=arrow(205 if direction==1 else 696,y,696 if direction==1 else 205,y,color,2)
v+=txt(25,439,'ACK表示接收存储；管理确认另记录。实际协议参数需无线实测核定。',21,M)
render('protocol_loop',v,900,463)
print('Three application design figures produced; no physical implementation claimed.')
