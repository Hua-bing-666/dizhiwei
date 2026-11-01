import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/技术路线图_核心与两翼_20261027.svg');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2160" viewBox="0 0 1800 2160" data-print-width-mm="155" role="img" aria-labelledby="title desc">
<title id="title">南疆滴灌支管异常识别与采集策略研究技术路线</title>
<desc id="desc">拟开展的研究技术路线。两侧水力机理和同步测量研究为中间的归一化残差及不重叠块特征提供依据。块级CUSUM位于主轴，向左形成候选事件、可靠LoRa传输和人工核查研究，向右开展固定采样及事件触发采样的同判据比较。主轴同时开展同误报水平的判据及基线参数标定。两翼研究与判据参数在冻结阶段汇合，继而进行双支路留出批次验证和基线比较，评价可检幅度、持续时间及适用条件。仅健康标定数据用于健康参照；故障操作真值用于独立评价。图示研究计划，不表示实物性能已取得。</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#252525"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:40px;fill:#111;text-anchor:middle;dominant-baseline:central}
.heading{font-size:42px;font-weight:700}.core-title{font-size:44px;font-weight:700}
.box{fill:#fff;stroke:#3c3c3c;stroke-width:1.6}.input{stroke:#555;stroke-width:1.4}
.feature{fill:#fafafa;stroke:#303030;stroke-width:2}.core{fill:#e8e8e8;stroke:#202020;stroke-width:2.8}
.focus{fill:#f3f3f3;stroke:#303030;stroke-width:2.2}.result{fill:#f7f7f7;stroke:#353535;stroke-width:1.9}
.link{fill:none;stroke:#303030;stroke-width:1.6;stroke-linejoin:round;marker-end:url(#arrow)}.main{stroke-width:2.2}
.rule{stroke:#aaa;stroke-width:1.1}
</style></defs><rect width="1800" height="2160" fill="#fff"/>`];

function text(x,y,s,cls=''){svg.push(`<text x="${x}" y="${y}"${cls?` class="${cls}"`:''}>${esc(s)}</text>`);}
function box(id,x,y,w,h,lines,kind='method'){
 const style=['input','feature','core','focus','result'].includes(kind)?' '+kind:'';
 svg.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect class="box${style}" x="${x}" y="${y}" width="${w}" height="${h}"${kind==='input'?' rx="12"':''}/>`);
 const ys=lines.length===1?[y+h/2]:[y+45,y+100];
 lines.forEach((s,i)=>text(x+w/2,ys[i],s,lines.length>1&&i===0?(kind==='core'?'core-title':'heading'):kind==='result'?'heading':''));
 svg.push('</g>');
}
function link(from,to,d,main=false){svg.push(`<path class="link${main?' main':''}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

text(310,50,'故障与正常扰动建模','heading');
text(1490,50,'同步测量与健康标定','heading');
svg.push('<path class="rule" d="M30,85 H590 M1210,85 H1770"/>');

box('faults',30,120,300,90,['等效泄漏/受限'],'input');
box('disturbance',370,120,220,90,['供压/切换'],'input');
box('model',30,290,560,100,['故障与扰动水力建模']);
link('faults','model','M180,210 V250 H210 V290');
link('disturbance','model','M480,210 V250 H410 V290');
box('pressure-flow',30,460,260,140,['压力—流量','耦合特征']);
box('resistance',330,460,260,140,['区段阻力','变化特征']);
link('model','pressure-flow','M310,390 V425 H160 V460');
link('model','resistance','M310,390 V425 H460 V460');
box('sensitivity',30,670,560,90,['特征敏感性与扰动分析']);
link('pressure-flow','sensitivity','M160,600 V635 H210 V670');
link('resistance','sensitivity','M460,600 V635 H410 V670');

box('pressure',1210,120,260,90,['压力/压差'],'input');
box('flow',1510,120,260,90,['流量脉冲'],'input');
box('alignment',1210,290,560,100,['时序对齐与连续计数']);
link('pressure','alignment','M1340,210 V250 H1390 V290');
link('flow','alignment','M1640,210 V250 H1590 V290');
box('calibration',1210,460,560,110,['标定与测量误差分析']);
link('alignment','calibration','M1490,390 V460');
box('reference',1210,670,560,90,['独立健康参照与残差尺度']);
link('calibration','reference','M1490,570 V670');

box('blocks',680,645,440,140,['归一化参照残差','不重叠块特征'],'feature');
link('sensitivity','blocks','M590,715 H680',true);
link('reference','blocks','M1210,715 H1120');
box('cusum',680,920,440,150,['块级CUSUM判据','切换工况挂起与复判'],'core');
link('blocks','cusum','M900,785 V920',true);

box('candidate',30,925,560,140,['持续异常候选','观测记录与事件关联']);
box('sampling',1210,925,560,140,['事件触发采样研究','固定采样对照与统一判据'],'focus');
link('cusum','candidate','M680,995 H590');
link('cusum','sampling','M1120,995 H1210',true);

box('delivery',30,1140,560,140,['LoRa可靠传输','重发、去重与提交后确认']);
link('candidate','delivery','M310,1065 V1140');
box('recheck',30,1370,560,140,['可核查告警链','人工核查与同工况复测']);
link('delivery','recheck','M310,1280 V1370');

box('fixed',1210,1165,260,90,['固定采样'],'input');
box('triggered',1510,1165,260,90,['事件触发'],'input');
link('sampling','fixed','M1490,1065 V1115 H1340 V1165');
link('sampling','triggered','M1490,1065 V1115 H1640 V1165');
box('sampling-config',1210,1370,560,140,['策略设计与参数选择','时延、漏检与采集通信开销']);
link('fixed','sampling-config','M1340,1255 V1310 H1390 V1370');
link('triggered','sampling-config','M1640,1255 V1310 H1590 V1370');

box('fair-calibration',680,1190,440,140,['按统一误报目标标定','判据与基线参数']);
link('cusum','fair-calibration','M900,1070 V1190',true);
box('freeze',650,1560,500,140,['联合调参与参数冻结','参照、判据及采样策略'],'feature');
link('fair-calibration','freeze','M900,1330 V1560',true);
link('recheck','freeze','M310,1510 V1535 H730 V1560');
link('sampling-config','freeze','M1490,1510 V1535 H1070 V1560');

box('validation',600,1780,600,110,['留出批次独立验证']);
link('freeze','validation','M900,1700 V1780',true);
box('bench',30,1765,450,140,['双支路对照试验','A支路注入/B支路切换']);
box('records',1320,1765,450,140,['独立计量','与操作记录']);
link('bench','validation','M480,1835 H600');
link('records','validation','M1320,1835 H1200');

box('comparison',600,1980,600,140,['基线与策略对照评价','检出、误报、时延、送达与开销']);
link('validation','comparison','M900,1890 V1980',true);
box('baselines',30,1980,450,140,['单阈值基线','固定采样基线']);
link('baselines','comparison','M480,2050 H600');
box('outcome',1320,1980,450,140,['可检边界与适用条件','幅度—持续时间'],'result');
link('comparison','outcome','M1200,2050 H1320',true);

svg.push('</svg>');
await fs.writeFile(target,svg.join('\n'),'utf8');
console.log(target);
