import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/技术路线图_流程版_20261026.svg');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const parts=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2410" viewBox="0 0 1800 2410" role="img" aria-labelledby="title desc">
<title id="title">滴灌支管道早期故障诊断原型系统技术路线图</title>
<desc id="desc">拟开展的研制与验证流程。总体方案后并行开展硬件、台架模型与软件研制，分支分别测试和修订，通过后集成联调。系统先开展调参试验并冻结参数，再用独立批次进行台架对照验证和性能评价。不满足研究要求时定位修订并重新联调，修订后使用新批次独立验证。图示项目实施安排，不代表硬件、无线或实测性能已经完成。虚线表示系统修订后的重新联调路径。</desc>
<defs><marker id="arrow" markerWidth="13" markerHeight="11" refX="12" refY="5.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L13,5.5 L0,11 Z" fill="#222"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:42px;fill:#111;text-anchor:middle;dominant-baseline:central}
.heading{font-size:44px;font-weight:700}.stage{font-size:46px;font-weight:700}
.box{fill:#fff;stroke:#222;stroke-width:2}.main{stroke-width:2.6}
.link{fill:none;stroke:#222;stroke-width:2.1;stroke-linejoin:round;marker-end:url(#arrow)}
.feedback{stroke-dasharray:12 9}
</style></defs><rect width="1800" height="2410" fill="#fff"/>`];

function text(x,y,value,cls=''){
 parts.push(`<text x="${x}" y="${y}"${cls?` class="${cls}"`:''}>${esc(value)}</text>`);
}
function box(id,x,y,w,h,lines,{heading=true,main=false,kind='rect'}={}){
 parts.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}">`);
 if(kind==='diamond')parts.push(`<path class="box${main?' main':''}" d="M${x+w/2},${y} L${x+w},${y+h/2} L${x+w/2},${y+h} L${x},${y+h/2} Z"/>`);
 else if(kind!=='heading')parts.push(`<rect class="box${main?' main':''}" x="${x}" y="${y}" width="${w}" height="${h}"/>`);
 const ys=lines.length===1?[y+h/2]:lines.length===2?[y+45,y+100]:[y+45,y+100,y+150];
 lines.forEach((line,i)=>text(x+w/2,ys[i],line,heading&&i===0?(main?'stage':'heading'):''));
 parts.push('</g>');
}
function link(from,to,d,feedback=false){parts.push(`<path class="link${feedback?' feedback':''}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

box('overall',300,40,1200,140,['总体方案设计','南疆棉田支管巡检：明确测点、故障定义与系统接口'],{main:true});

const branches=[
 {id:'hardware',x:40,title:'硬件研制',steps:[
  ['传感与接口设计','压力/压差与流量'],
  ['节点与接收端制作','存储与接口预留'],
  ['采集标定与测试','时序、计数与误差']
 ]},
 {id:'model',x:610,title:'台架与水力模型',steps:[
  ['台架与测点设计','注入点与切换负载'],
  ['水力建模与仿真','健康参照与特征'],
  ['模型标定与校验','独立计量与误差']
 ]},
 {id:'software',x:1180,title:'软件研制',steps:[
  ['块级CUSUM判断','固定/触发采样策略'],
  ['通信与平台开发','存储、核查与复测'],
  ['主机回放测试','接口与异常处理']
 ]}
];

for(const b of branches){
 const c=b.x+200;
 box(b.id+'-head',b.x,235,400,80,[b.title],{kind:'heading'});
 link('overall',b.id+'-head',`M900,180 V210 H${c} V235`);
 b.steps.forEach((lines,i)=>{
  const y=350+i*190;
  box(b.id+'-'+(i+1),b.x,y,400,140,lines);
  const prev=i===0?b.id+'-head':b.id+'-'+i;
  const fromY=i===0?315:350+(i-1)*190+140;
  link(prev,b.id+'-'+(i+1),`M${c},${fromY} V${y}`);
 });
 box(b.id+'-gate',c-170,930,340,150,['满足要求'],{heading:false,kind:'diamond'});
 link(b.id+'-3',b.id+'-gate',`M${c},870 V930`);
 box(b.id+'-fix',b.x+430,950,120,110,['修订'],{heading:false});
 link(b.id+'-gate',b.id+'-fix',`M${c+170},1005 H${b.x+430}`);
 text(c+200,970,'否');
 link(b.id+'-fix',b.id+'-1',`M${b.x+490},950 V420 H${b.x+400}`);
 text(c+30,1110,'是');
}

box('integration',300,1190,1200,140,['系统集成与逐级联调','板上采集—本地判断—LoRa传输—平台展示与核查'],{main:true});
link('hardware-gate','integration','M240,1080 V1140 H700 V1190');
link('model-gate','integration','M810,1080 V1190');
link('software-gate','integration','M1380,1080 V1140 H1100 V1190');

box('tuning',300,1390,1200,140,['调参试验与参数冻结','同工况比较固定采样与事件触发策略，确定参照与门限'],{main:true});
link('integration','tuning','M900,1330 V1390');
box('validation',180,1590,1440,190,[
 '独立台架对照验证',
 'A支路等效泄漏与受限；健康、供压扰动及B支路切换作对照',
 '独立操作记录与参考计量 · 使用未参与调参的数据批次'
],{main:true});
link('tuning','validation','M900,1530 V1590');
box('evaluation',300,1840,1200,140,[
 '性能评价与适用边界分析',
 '检出、误报与时延 / 送达与恢复 / 采集及通信开销'
],{main:true});
link('validation','evaluation','M900,1780 V1840');
box('final-gate',680,2040,440,160,['满足研究要求？'],{heading:false,kind:'diamond'});
link('evaluation','final-gate','M900,1980 V2040');
box('system-fix',1390,2050,340,140,['问题定位与修订','修订后另批验证'],{heading:false});
link('final-gate','system-fix','M1120,2120 H1390');
text(1255,2085,'否');
link('system-fix','integration','M1730,2120 H1770 V1260 H1500',true);
text(1635,1215,'重新联调');
box('outputs',300,2260,1200,110,['形成原型系统、实验数据与研究结论'],{main:false});
link('final-gate','outputs','M900,2200 V2260');
text(940,2230,'是');
parts.push('</svg>');
await fs.writeFile(target,parts.join('\n'),'utf8');
console.log(target);
