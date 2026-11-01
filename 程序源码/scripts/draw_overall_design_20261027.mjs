import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/总体设计_硬件与信息流_20261027.svg');
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="155mm" height="129.1667mm" viewBox="0 0 1800 1500" data-print-width-mm="155" role="img" aria-labelledby="title desc">
<title id="title">系统总体设计</title>
<desc id="desc">方案组成图，依据总体设计正文中的两路表压测量配置绘制，不表示硬件已搭建。双支路清水台架中A支路提供P0、P1及Q观测量，B支路用于负载扰动，独立收集装置用于计量。两路4–20mA压力经电阻取样、输入保护及ADS1115转换，以I²C连接STM32F103C8T6；SEN0549流量脉冲经电平整形后计数。主控进行特征计算、异常判断和事件触发采样，SPI连接microSD日志，UART连接节点E220。两只E220通过LoRa传递事件和确认；接收端经3.3V逻辑USB–TTL转换器连接本地计算机。接收服务进行校验、去重及持久化，写入成功才回复确认，平台供用户查看状态、记录处置和复测。图中连线表示功能连接，不是可直接施工的电气原理图。</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#435a69"/></marker><style>
text{font-family:SimSun,"Times New Roman",serif;font-size:40px;fill:#243847;text-anchor:middle;dominant-baseline:central}
.heading{font-size:44px;font-weight:700;text-anchor:start}.strong{font-size:42px;font-weight:700}
.card{fill:#fff;stroke:#79909c;stroke-width:1.8}.core{fill:#e7f0f5;stroke:#38657d;stroke-width:2.6}
.link{fill:none;stroke:#435a69;stroke-width:2;stroke-linejoin:round;marker-end:url(#arrow)}
.radio{stroke-width:2.6}.ack{stroke-dasharray:9 7;stroke-width:1.8}
.interface{fill:#405b6c}.muted{fill:#536776}
</style></defs><rect width="1800" height="1500" fill="#fff"/>`];
function text(x,y,value,cls=''){svg.push(`<text x="${x}" y="${y}"${cls?` class="${cls}"`:''}>${escape(value)}</text>`);}
function panel(x,y,w,h,label,fill,accent){
 svg.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="${fill}" stroke="${accent}" stroke-width="1.5"/><rect x="${x+32}" y="${y+32}" width="8" height="42" rx="4" fill="${accent}"/>`);
 text(x+58,y+55,label,'heading');
}
function box(id,x,y,w,h,lines,core=false){
 svg.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect class="card${core?' core':''}" x="${x}" y="${y}" width="${w}" height="${h}" rx="10"/>`);
 const spacing=54,top=y+h/2-(lines.length-1)*spacing/2;
 lines.forEach((s,i)=>text(x+w/2,top+i*spacing,s,i===0?'strong':''));svg.push('</g>');
}
function link(from,to,d,kind=''){svg.push(`<path class="link ${kind}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

panel(40,40,1720,270,'双支路清水台架','#faf8f3','#af9b76');
panel(40,400,1080,1060,'感知诊断节点','#f5f8fb','#52768c');
panel(1220,400,540,460,'LoRa 接收端','#f4f8f8','#5d8989');
panel(1220,920,540,540,'本地巡检平台','#f5f8f4','#789477');

// Cards are independent functional units; enclosing panels only denote scope.
box('branch-a',80,145,760,140,['A 支路：受测区段','压力 P0、P1 与流量 Q']);
box('branch-b',900,145,370,140,['B 支路','负载扰动']);
box('collection',1330,145,390,140,['独立收集装置','计量与操作记录']);
box('pressure',80,540,440,140,['压力变送器 P0、P1','两路 4–20 mA']);
box('conditioning',80,760,440,140,['采样电阻与输入保护','电流信号转电压']);
box('adc',80,1020,440,140,['ADS1115 采集模块','双通道电压采集']);
box('flow',700,770,360,140,['SEN0549 流量计','脉冲整形与计数']);
box('mcu',700,950,360,230,['STM32F103C8T6','特征计算与判断','事件触发采样'],true);
box('node-radio',700,540,360,140,['E220-400T22D','节点无线模块']);
box('sd',700,1290,360,140,['microSD 日志','本地记录']);
box('receiver-radio',1260,540,460,140,['E220-400T22D','接收端无线模块']);
box('usb',1260,730,460,90,['3.3 V 逻辑 USB–TTL']);
box('server',1260,1060,460,190,['接收服务与数据库','校验、去重、持久化','写入成功后回复确认']);
box('web',1260,1290,460,140,['状态展示与巡检记录','查看 · 处置 · 复测']);

link('branch-a','pressure','M600,285 V510 H300 V540');
link('branch-a','flow','M780,285 V340 H650 V830 H700');
link('pressure','conditioning','M300,680 V760');
link('conditioning','adc','M300,900 V1020');
link('adc','mcu','M520,1080 H700');text(610,1032,'I²C','interface');
link('flow','mcu','M880,910 V950');
link('mcu','node-radio','M1000,950 V920 H1085 V690 H1000 V680');text(1015,718,'UART','interface');
svg.push('<path d="M994,938 L1000,950 L1006,938 Z" fill="#435a69"/>');
link('mcu','sd','M880,1180 V1290');text(960,1234,'SPI','interface');
link('node-radio','receiver-radio','M1060,585 H1260','radio');text(1160,538,'LoRa','interface');
link('receiver-radio','node-radio','M1260,635 H1060','ack');text(1160,687,'ACK','interface');
link('receiver-radio','usb','M1460,680 V730');
link('usb','receiver-radio','M1540,730 V680','ack');
link('usb','server','M1660,820 V1060');
link('server','usb','M1600,1060 V820','ack');text(1480,893,'USB','interface');
link('server','web','M1490,1250 V1290');

svg.push('</svg>');await fs.writeFile(target,svg.join('\n'));console.log(target);
