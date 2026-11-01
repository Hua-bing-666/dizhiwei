import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/技术路线图_申报书用_20261027.svg');
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2110" viewBox="0 0 1800 2110" data-print-width-mm="150" role="img" aria-labelledby="title desc">
<title id="title">滴灌支管异常识别研究技术路线</title>
<desc id="desc">拟开展的研究方法与验证路线。等效泄漏、区段受限及正常扰动输入水力模型；独立健康工况用于测量标定和健康参照。两类依据共同支持不重叠块特征和CUSUM判据。统一判据支持事件触发采样对照，研究响应时延、漏检及开销，异常候选关联观测记录并形成LoRa可靠上报与人工复测。调参及参数冻结后进行双支路独立验证，独立计量与正常扰动记录为评价依据，单阈值和固定采样作为基线。输出可检边界、适用条件及告警代价。图示研究计划，不表示实测性能已经取得。</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#222"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:41px;fill:#111;text-anchor:middle;dominant-baseline:central}
.method{font-size:44px;font-weight:700}
.box{fill:#fff;stroke:#222;stroke-width:1.7}
.primary{stroke-width:2.3}
.link{fill:none;stroke:#222;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;marker-end:url(#arrow)}
.mainlink{stroke-width:2.2}
</style></defs><rect width="1800" height="2110" fill="#fff"/>`];

function box(id,x,y,w,h,lines,primary=false){
 svg.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect class="box${primary?' primary':''}" x="${x}" y="${y}" width="${w}" height="${h}"/>`);
 const ys=lines.length===1?[y+h/2]:[y+45,y+100];
 lines.forEach((line,i)=>svg.push(`<text x="${x+w/2}" y="${ys[i]}"${primary&&i===0?' class="method"':''}>${escape(line)}</text>`));
 svg.push('</g>');
}
function link(from,to,d,main=false){svg.push(`<path class="link${main?' mainlink':''}" data-from="${from}" data-to="${to}" d="${d}"/>`);}

box('leak',50,50,260,90,['等效泄漏']);
box('restriction',390,90,260,90,['区段受限']);
box('normal',50,270,300,100,['正常工况扰动']);
box('physical',440,250,600,140,['水力建模与归一化特征','压力—流量关系与区段阻力'],true);
box('healthy',1225,50,400,100,['独立健康工况测量']);
box('calibration',1150,270,550,140,['测量标定与误差分析','建立健康水力参照']);
link('leak','physical','M180,140 C180,205 540,175 540,250');
link('restriction','physical','M520,180 V215 H850 V250');
link('normal','physical','M350,320 H440');
link('healthy','calibration','M1425,150 V270');

box('features',500,500,670,110,['参照残差与不重叠块特征'],true);
link('physical','features','M740,390 C740,450 680,440 680,500',true);
link('calibration','features','M1425,410 C1425,470 990,440 990,500');

box('diagnosis',340,720,690,110,['块级CUSUM与切换复判'],true);
link('features','diagnosis','M835,610 C835,670 685,650 685,720',true);
box('sampling',1180,650,550,110,['固定与事件触发采样对照'],true);
link('diagnosis','sampling','M1030,775 C1110,775 1100,705 1180,705');
svg.push('<text x="1120" y="825">同一判据</text>');

box('sampling-analysis',1270,870,460,100,['时延、漏检与开销']);
link('sampling','sampling-analysis','M1455,760 C1455,820 1500,810 1500,870');
box('event-evidence',180,950,590,110,['异常候选及观测关联']);
link('diagnosis','event-evidence','M685,830 C685,900 475,890 475,950',true);

box('warning',800,1110,830,140,['LoRa可靠上报与落库确认','人工核查及同工况复测']);
link('event-evidence','warning','M770,1005 C890,1005 1030,1020 1030,1110',true);
link('sampling-analysis','warning','M1500,970 C1500,1035 1460,1035 1460,1110');

box('freeze',490,1340,700,110,['调参试验与参数冻结']);
link('warning','freeze','M1100,1250 C1100,1300 840,1280 840,1340',true);
box('validation',500,1530,680,110,['双支路台架独立验证']);
link('freeze','validation','M840,1450 V1530',true);

box('records',70,1515,340,140,['独立计量','与操作记录']);
link('records','validation','M410,1585 H500');
box('controls',1330,1400,400,140,['故障与正常扰动','供压及B支路切换']);
link('controls','validation','M1330,1470 C1240,1470 1280,1585 1180,1585');

box('comparison',700,1740,790,110,['基线与采样策略对照评价']);
link('validation','comparison','M840,1640 C840,1690 1095,1680 1095,1740',true);
box('baselines',90,1725,430,140,['单阈值基线','固定采样基线']);
link('baselines','comparison','M520,1795 H700');

box('boundaries',750,1930,970,140,['可检边界与适用条件','检出、误报、时延、送达与开销'],true);
link('comparison','boundaries','M1095,1850 C1095,1895 1235,1885 1235,1930',true);

svg.push('</svg>');
await fs.writeFile(target,svg.join('\n'),'utf8');
console.log(target);
