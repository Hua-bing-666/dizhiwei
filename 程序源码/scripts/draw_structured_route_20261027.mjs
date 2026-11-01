import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/技术路线图_分层结构_20261027.svg');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const out=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2090" viewBox="0 0 1800 2090" data-print-width-mm="150" role="img" aria-labelledby="title desc">
<title id="title">滴灌支管异常识别技术路线</title>
<desc id="desc">拟开展的研究路线，按建模与测量依据、判据与采样方法、独立验证与边界评价组织。水力模型和独立健康标定共同支撑参照残差、不重叠块特征与CUSUM判据。固定采样与事件触发策略在同一判据下对照，输出采样及上报配置；候选事件经LoRa上报、落库确认及人工复测形成核查链。参数冻结后，以双支路台架、独立计量与操作记录开展独立验证，再与单阈值和固定采样基线比较。虚线外框为研究环节分区，不表示新增系统设备。图示研究计划，不表示实测结论已完成。</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#222"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:41px;fill:#111;text-anchor:middle;dominant-baseline:central}
.key{font-size:44px;font-weight:700}.section-title{font-size:44px;font-weight:700;text-anchor:start}
.box{fill:#fff;stroke:#222;stroke-width:1.7}.primary{stroke-width:2.2}
.section{fill:none;stroke:#858585;stroke-width:1.3;stroke-dasharray:9 7}
.link{fill:none;stroke:#222;stroke-width:1.8;stroke-linejoin:round;marker-end:url(#arrow)}
.main{stroke-width:2.2}
</style></defs><rect width="1800" height="2090" fill="#fff"/>`];

function section(y,h,label,labelWidth){
 out.push(`<rect class="section" x="40" y="${y}" width="1720" height="${h}"/>`);
 out.push(`<rect x="80" y="${y-28}" width="${labelWidth}" height="58" fill="#fff"/>`);
 out.push(`<text class="section-title" x="100" y="${y}">${esc(label)}</text>`);
}
function box(id,x,y,w,h,lines,primary=false){
 out.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect class="box${primary?' primary':''}" x="${x}" y="${y}" width="${w}" height="${h}"/>`);
 const ys=lines.length===1?[y+h/2]:[y+45,y+100];
 lines.forEach((line,i)=>out.push(`<text x="${x+w/2}" y="${ys[i]}"${primary&&i===0?' class="key"':''}>${esc(line)}</text>`));
 out.push('</g>');
}
function link(from,to,d,main=false){out.push(`<path class="link${main?' main':''}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

section(40,450,'建模与测量依据',360);
section(590,710,'判据与采样方法',360);
section(1400,650,'试验验证与边界评价',410);

box('faults',90,130,340,100,['泄漏与区段受限']);
box('disturbances',500,130,380,100,['供压与支路切换']);
box('model',220,300,600,140,['水力建模与归一化特征','压力—流量关系及区段阻力'],true);
link('faults','model','M260,230 V265 H400 V300');
link('disturbances','model','M690,230 V265 H640 V300');

box('healthy-data',1160,130,480,100,['独立健康工况测量']);
box('calibration',1100,300,600,140,['测量标定与误差分析','建立健康水力参照']);
link('healthy-data','calibration','M1400,230 V300');

box('features',190,690,660,110,['参照残差与不重叠块特征'],true);
link('model','features','M520,440 V690',true);
link('calibration','features','M1400,440 V560 H720 V690');
box('diagnosis',190,890,660,110,['块级CUSUM与切换复判'],true);
link('features','diagnosis','M520,800 V890',true);

box('fixed-sampling',1155,690,420,100,['固定采样基线']);
box('adaptive-sampling',1040,890,650,110,['事件触发采样对照'],true);
link('fixed-sampling','adaptive-sampling','M1365,790 V890');
link('diagnosis','adaptive-sampling','M850,945 H1040');
out.push('<text x="945" y="910">统一判据</text>');

box('warning',190,1090,660,140,['异常候选与可核查告警','LoRa上报、确认与人工复测']);
link('diagnosis','warning','M520,1000 V1090',true);
box('sampling-config',1040,1100,650,110,['采样与上报参数配置']);
link('adaptive-sampling','sampling-config','M1365,1000 V1100');

box('freeze',560,1500,680,110,['调参试验与参数冻结']);
link('warning','freeze','M520,1230 V1350 H760 V1500',true);
link('sampling-config','freeze','M1365,1210 V1350 H1040 V1500');

box('validation',560,1690,680,110,['独立批次台架验证']);
link('freeze','validation','M900,1610 V1690',true);
box('bench',90,1690,370,110,['双支路台架对照']);
box('measurement-records',1330,1675,370,140,['独立计量','与操作记录']);
link('bench','validation','M460,1745 H560');
link('measurement-records','validation','M1330,1745 H1240');

box('comparison',560,1870,680,110,['基线与策略对照评价']);
link('validation','comparison','M900,1800 V1870',true);
box('baselines',90,1855,370,140,['单阈值基线','固定采样基线']);
link('baselines','comparison','M460,1925 H560');
box('boundaries',1290,1855,440,140,['可检边界与适用条件','检出/误报/时延/开销'],true);
link('comparison','boundaries','M1240,1925 H1290',true);

out.push('</svg>');
await fs.writeFile(target,out.join('\n'),'utf8');
console.log(target);
