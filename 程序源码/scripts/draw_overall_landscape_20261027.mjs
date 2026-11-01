import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/总体设计_横版_20261027.svg');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="155mm" height="94.7222mm" viewBox="0 0 1800 1100" data-print-width-mm="155" role="img" aria-labelledby="title desc">
<title id="title">系统总体设计</title>
<desc id="desc">总体设计横版配图。双支路清水台架的A支路提供P0、P1和Q观测量，B支路用于负载扰动，独立收集装置用于计量。两路4–20mA压力经电阻取样及输入保护，进入ADS1115，再通过I²C接入STM32F103C8T6。SEN0549流量脉冲经电平整形后计数；主控负责特征计算、异常判断及事件触发采样，SPI连接microSD日志，UART双向连接节点E220。LoRa接收端由另一只E220及3.3V逻辑USB–TTL组成，连接本地计算机。接收服务校验、去重并成功持久化后回复应用层确认，平台提供状态、事件、处置及复测记录。虚线为接收确认返回。功能连接示意，不是接线原理图，也不表示已完成实物验证。</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#435a69"/></marker><style>
text{font-family:SimSun,"Times New Roman",serif;font-size:40px;fill:#243847;text-anchor:middle;dominant-baseline:central}
.heading{font-size:44px;font-weight:700;text-anchor:start}.strong{font-size:42px;font-weight:700}
.card{fill:#fff;stroke:#79909c;stroke-width:1.8}.core{fill:#e7f0f5;stroke:#38657d;stroke-width:2.6}
.link{fill:none;stroke:#435a69;stroke-width:2;stroke-linejoin:round;marker-end:url(#arrow)}
.radio{stroke-width:2.6}.ack{stroke-dasharray:9 7;stroke-width:1.8}.interface{fill:#405b6c}
</style></defs><rect width="1800" height="1100" fill="#fff"/>`];
function text(x,y,s,cls=''){svg.push(`<text x="${x}" y="${y}"${cls?` class="${cls}"`:''}>${esc(s)}</text>`);}
function panel(x,y,w,h,label,fill,accent){
 svg.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="18" fill="${fill}" stroke="${accent}" stroke-width="1.5"/><rect x="${x+32}" y="${y+32}" width="8" height="42" rx="4" fill="${accent}"/>`);
 text(x+58,y+55,label,'heading');
}
function box(id,x,y,w,h,lines,core=false){
 svg.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect class="card${core?' core':''}" x="${x}" y="${y}" width="${w}" height="${h}" rx="10"/>`);
 const top=y+h/2-(lines.length-1)*27;lines.forEach((s,i)=>text(x+w/2,top+i*54,s,i===0?'strong':''));svg.push('</g>');
}
function link(from,to,d,kind=''){svg.push(`<path class="link ${kind}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

panel(40,40,1720,270,'双支路清水台架','#faf8f3','#af9b76');
panel(40,340,1080,720,'感知诊断节点','#f5f8fb','#52768c');
panel(1160,340,600,340,'LoRa 接收端','#f4f8f8','#5d8989');
panel(1160,710,600,350,'本地巡检平台','#f5f8f4','#789477');
box('branch-a',80,140,760,140,['A 支路：受测区段','压力 P0、P1 与流量 Q']);
box('branch-b',900,140,370,140,['B 支路','负载扰动']);
box('collection',1330,140,390,140,['独立收集装置','计量与操作记录']);
box('pressure',80,480,300,190,['压力 P0、P1','两路 4–20 mA','取样及保护']);
box('adc',430,480,320,140,['ADS1115','双通道电压采集']);
box('mcu',430,760,320,230,['STM32F103C8T6','特征计算与判断','事件触发采样'],true);
box('flow',80,780,300,230,['SEN0549','流量脉冲','整形与计数']);
box('node-radio',790,480,300,140,['E220-400T22D','节点无线模块']);
box('sd',790,820,300,140,['microSD 日志','本地记录']);
box('receiver-radio',1200,480,300,140,['E220-400T22D','无线接收']);
box('usb',1540,480,200,140,['USB-TTL','3.3 V']);
box('server',1200,830,240,190,['接收服务','校验与去重','写库后确认']);
box('web',1480,830,240,190,['巡检界面','状态与事件','处置与复测']);

link('branch-a','pressure','M580,280 V455 H230 V480');
link('branch-a','flow','M180,280 V325 H60 V895 H80');
link('pressure','adc','M380,550 H430');
link('adc','mcu','M590,620 V760');text(665,690,'I²C','interface');
link('flow','mcu','M380,890 H430');
link('mcu','node-radio','M750,820 H770 V550 H790');text(865,702,'UART','interface');
svg.push('<path d="M762,814 L750,820 L762,826 Z" fill="#435a69"/>');
link('mcu','sd','M750,910 H790');text(865,1006,'SPI','interface');
link('node-radio','receiver-radio','M1090,525 H1200','radio');text(1140,465,'LoRa','interface');
link('receiver-radio','node-radio','M1200,575 H1090','ack');text(1140,653,'ACK','interface');
link('receiver-radio','usb','M1500,520 H1540');
link('usb','receiver-radio','M1540,580 H1500','ack');
link('usb','server','M1630,620 V690 H1135 V930 H1200');
link('server','usb','M1200,875 H1145 V700 H1670 V620','ack');text(1510,653,'USB','interface');
link('server','web','M1440,925 H1480');

svg.push('</svg>');await fs.writeFile(target,svg.join('\n'));console.log(target);
