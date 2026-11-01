import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'deliverables/技术路线图_研究展开_20261027.svg');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2270" viewBox="0 0 1800 2270" data-print-width-mm="150" role="img" aria-labelledby="title desc">
<title id="title">南疆棉田滴灌支管异常识别技术路线</title>
<desc id="desc">拟开展的研究路线。故障及正常扰动水力建模形成压力流量和阻力特征并开展敏感性分析。独立健康工况测量经时序对齐、连续计数、标定及误差分析形成健康参照和残差尺度。二者输入归一化残差和不重叠块特征，采用块级CUSUM及切换复判。诊断判据支撑异常候选的可靠告警研究，也作为固定采样与事件触发采样对照的统一判据。事件身份关联观测快照，LoRa采用有限重发、去重和持久化后确认，配合人工复测。两条研究线在参数冻结前汇合，随后开展双支路留出批次验证和基线比较，研究检出、误报、时延、送达、开销和可检边界。图示研究计划，不表示实测结果已经取得。</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#252525"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:41px;fill:#151515;text-anchor:middle;dominant-baseline:central}
.title{font-size:44px;font-weight:700}.heading{font-size:42px;font-weight:700}.core-title{font-size:46px;font-weight:700}
.box{fill:#fff;stroke:#353535;stroke-width:1.7}.input{stroke:#505050;stroke-width:1.5}
.core{fill:#eeeeee;stroke:#202020;stroke-width:2.6}.result{fill:#f6f6f6;stroke:#353535;stroke-width:1.9}
.link{fill:none;stroke:#303030;stroke-width:1.7;stroke-linejoin:round;marker-end:url(#arrow)}.main{stroke-width:2.1}
.rule{stroke:#aaaaaa;stroke-width:1.1}
</style></defs><rect width="1800" height="2270" fill="#fff"/>`];

function text(x,y,s,cls=''){svg.push(`<text x="${x}" y="${y}"${cls?` class="${cls}"`:''}>${esc(s)}</text>`);}
function box(id,x,y,w,h,lines,kind='method'){
 const special=kind==='input'?' input':kind==='core'?' core':kind==='result'?' result':'';
 svg.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect class="box${special}" x="${x}" y="${y}" width="${w}" height="${h}"${kind==='input'?' rx="14"':''}/>`);
 const ys=lines.length===1?[y+h/2]:[y+45,y+100];
 lines.forEach((s,i)=>text(x+w/2,ys[i],s,lines.length>1&&i===0?(kind==='core'?'core-title':'heading'):kind==='result'?'heading':''));
 svg.push('</g>');
}
function link(from,to,d,main=false){svg.push(`<path class="link${main?' main':''}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

text(490,50,'故障与正常扰动建模','title');
text(1370,50,'同步测量与健康标定','title');
svg.push('<path class="rule" d="M60,85 H920 M1020,85 H1720"/>');

box('leak',60,120,250,90,['等效泄漏'],'input');
box('restriction',365,120,250,90,['区段受限'],'input');
box('disturbance',670,120,250,90,['供压/切换'],'input');
box('model',170,280,640,110,['故障与扰动水力建模']);
link('leak','model','M185,210 V245 H350 V280');
link('restriction','model','M490,210 V280');
link('disturbance','model','M795,210 V245 H630 V280');

box('pressure-flow',60,450,400,90,['压力—流量特征']);
box('resistance',520,450,400,90,['区段阻力特征']);
link('model','pressure-flow','M490,390 V420 H260 V450');
link('model','resistance','M490,390 V420 H720 V450');
box('sensitivity',170,620,640,90,['特征敏感性与扰动分析']);
link('pressure-flow','sensitivity','M260,540 V580 H350 V620');
link('resistance','sensitivity','M720,540 V580 H630 V620');

box('pressure',1020,120,300,90,['压力/压差'],'input');
box('flow',1420,120,300,90,['流量脉冲'],'input');
box('alignment',1040,280,660,110,['时序对齐与连续计数']);
link('pressure','alignment','M1170,210 V245 H1250 V280');
link('flow','alignment','M1570,210 V245 H1490 V280');
box('calibration',1040,450,660,110,['标定与测量误差分析']);
link('alignment','calibration','M1370,390 V450');
box('reference',1040,620,660,90,['独立健康参照及残差尺度']);
link('calibration','reference','M1370,560 V620');

box('blocks',470,780,860,110,['归一化残差与不重叠块特征']);
link('sensitivity','blocks','M490,710 V745 H730 V780',true);
link('reference','blocks','M1370,710 V745 H1070 V780');
box('cusum',470,950,860,140,['块级 CUSUM 累积判断','切换工况挂起与复判'],'core');
link('blocks','cusum','M900,890 V950',true);

box('candidate',90,1150,700,140,['持续异常候选','观测记录与事件关联']);
box('sampling',1010,1150,700,140,['采集策略研究','保持统一诊断判据']);
link('cusum','candidate','M900,1090 V1120 H440 V1150',true);
link('cusum','sampling','M900,1090 V1120 H1360 V1150');

box('delivery',90,1350,700,90,['LoRa重发、去重与提交后确认']);
link('candidate','delivery','M440,1290 V1350',true);
box('fixed',1010,1350,310,90,['固定采样'],'input');
box('triggered',1400,1350,310,90,['事件触发采样'],'input');
link('sampling','fixed','M1360,1290 V1320 H1165 V1350');
link('sampling','triggered','M1360,1290 V1320 H1555 V1350');

box('recheck',90,1500,700,140,['可核查告警链','人工核查与同工况复测']);
link('delivery','recheck','M440,1440 V1500',true);
box('sampling-config',1010,1500,700,140,['策略设计与参数选择','时延、漏检与采集通信开销']);
link('fixed','sampling-config','M1165,1440 V1470 H1230 V1500');
link('triggered','sampling-config','M1555,1440 V1470 H1490 V1500');

box('freeze',500,1720,800,100,['调参试验与各方法参数冻结'],'input');
link('recheck','freeze','M440,1640 V1680 H750 V1720',true);
link('sampling-config','freeze','M1360,1640 V1680 H1050 V1720');

box('validation',500,1900,800,110,['留出批次独立验证']);
link('freeze','validation','M900,1820 V1900',true);
box('bench',60,1900,340,110,['双支路对照试验']);
box('records',1400,1885,340,140,['独立计量','与操作记录']);
link('bench','validation','M400,1955 H500');
link('records','validation','M1400,1955 H1300');

box('comparison',500,2090,800,140,['基线与策略对照评价','检出、误报、时延、送达与开销']);
link('validation','comparison','M900,2010 V2090',true);
box('baselines',60,2090,340,140,['单阈值基线','固定采样基线']);
link('baselines','comparison','M400,2160 H500');
box('outcome',1400,2090,340,140,['可检边界','与适用条件'],'result');
link('comparison','outcome','M1300,2160 H1400',true);

svg.push('</svg>');
await fs.writeFile(output,svg.join('\n'),'utf8');
console.log(output);
