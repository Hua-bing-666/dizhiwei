import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const proposalMode=process.argv.includes('--proposal');
const target=path.join(root,proposalMode?'deliverables/技术路线图_申报书插图_20261027.svg':'deliverables/技术路线图_方法与验证_20261027.svg');
const canvasHeight=proposalMode?1990:2320;
const yAnchors=[[0,0],[40,40],[140,140],[220,190],[320,290],[400,340],[540,480],[620,530],[730,640],[810,690],[920,800],[1000,850],[1110,960],[1190,1010],[1300,1120],[1380,1170],[1520,1310],[1600,1360],[1710,1470],[1790,1520],[1900,1630],[1980,1680],[2090,1790],[2170,1840],[2280,1950],[2320,1990]];
function Y(value){
 if(!proposalMode)return value;
 for(let i=1;i<yAnchors.length;i++){
  const [a,b]=yAnchors[i-1],[c,d]=yAnchors[i];
  if(value<=c)return b+(value-a)*(d-b)/(c-a);
 }
 throw Error('Y coordinate out of planned canvas');
}
const technicalEdits=new Map([
 ['提取水力响应特征','构造归一化水力特征'],
 ['CUSUM累积判断与切换复判','块级CUSUM判断与切换复判'],
 ['固定采样与事件触发对照','固定与事件触发采样对照']
]);
const emphasized=new Set(['physical-model','features','diagnosis','sampling']);
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="${canvasHeight}" viewBox="0 0 1800 ${canvasHeight}"${proposalMode?' data-print-width-mm="150"':''} role="img" aria-labelledby="title desc">
<title id="title">南疆棉田滴灌支管异常识别研究技术路线</title>
<desc id="desc">拟开展的方法研究与验证路线。故障和正常扰动的水力建模提供响应特征，独立健康工况的测量标定提供健康参照，二者支撑参照残差、不重叠块特征及CUSUM判断。采用统一判据研究固定采样与事件触发的时延、漏检和开销，同时研究候选事件与测量快照绑定，形成可靠上报、落库确认及人工复测。调参并冻结参数后，采用独立计量与操作记录开展台架留出验证，并与单阈值和固定采样基线对照，评价检出误报、时延、送达恢复及可检边界与策略权衡。本图为研究路线，不表示实测性能已经完成。</desc>
<defs><marker id="arrow" markerWidth="11" markerHeight="9" refX="10" refY="4.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,4.5 L0,9 Z" fill="#222"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:42px;fill:#111;text-anchor:middle;dominant-baseline:central}
.technical{font-weight:700}
.box{fill:#fff;stroke:#222;stroke-width:${proposalMode?2:1.8}}
.link{fill:none;stroke:#222;stroke-width:${proposalMode?1.9:1.7};stroke-linejoin:round;marker-end:url(#arrow)}
</style></defs><rect width="1800" height="${canvasHeight}" fill="#fff"/>`];
function box(id,x,y,w,h,lines){
 svg.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${Y(y)}" data-w="${w}" data-h="${h}"><rect class="box" x="${x}" y="${Y(y)}" width="${w}" height="${h}"/>`);
 const ys=lines.length===1?[y+h/2]:[y+45,y+100];
 lines.forEach((line,i)=>svg.push(`<text x="${x+w/2}" y="${Y(ys[i])}"${proposalMode&&emphasized.has(id)&&i===0?' class="technical"':''}>${esc(proposalMode?(technicalEdits.get(line)||line):line)}</text>`));
 svg.push('</g>');
}
function link(from,to,d){
 if(proposalMode)d=d.replace(/M([\d.]+),([\d.]+)/g,(_,x,y)=>`M${x},${Y(+y)}`).replace(/V([\d.]+)/g,(_,y)=>`V${Y(+y)}`);
 svg.push(`<path class="link" data-from="${from}" data-to="${to}" d="${d}"/>`);
}

box('goal',480,40,840,100,['南疆棉田支管异常识别与可靠预警']);

box('fault-input',60,220,440,100,['等效泄漏与区段受限']);
box('normal-input',680,220,440,100,['供压变化与支路切换']);
box('healthy-input',1300,220,440,100,['独立健康工况采集']);
link('goal','fault-input','M900,140 V180 H280 V220');
link('goal','normal-input','M900,140 V220');
link('goal','healthy-input','M900,140 V180 H1520 V220');

box('physical-model',340,400,500,140,['故障与扰动水力建模','提取水力响应特征']);
box('healthy-reference',1300,400,440,140,['测量标定与误差分析','健康数据建立参照']);
link('fault-input','physical-model','M280,320 V360 H490 V400');
link('normal-input','physical-model','M900,320 V360 H690 V400');
link('healthy-input','healthy-reference','M1520,320 V400');

box('features',580,620,640,110,['参照残差与不重叠块特征']);
link('physical-model','features','M590,540 V580 H760 V620');
link('healthy-reference','features','M1520,540 V580 H1040 V620');

box('diagnosis',570,810,660,110,['CUSUM累积判断与切换复判']);
link('features','diagnosis','M900,730 V810');

box('candidate',160,1000,520,110,['异常候选生成']);
box('sampling',1120,1000,520,110,['固定采样与事件触发对照']);
link('diagnosis','candidate','M900,920 V960 H420 V1000');
link('diagnosis','sampling','M900,920 V960 H1380 V1000');

box('snapshot',160,1190,520,110,['候选事件与测量快照绑定']);
box('sampling-analysis',1120,1190,520,110,['时延、漏检与开销分析']);
link('candidate','snapshot','M420,1110 V1190');
link('sampling','sampling-analysis','M1380,1110 V1190');

box('reliable-warning',540,1380,720,140,['LoRa可靠上报与落库确认','人工核查与同工况复测']);
link('snapshot','reliable-warning','M420,1300 V1340 H760 V1380');
link('sampling-analysis','reliable-warning','M1380,1300 V1340 H1040 V1380');

box('parameter-freeze',570,1600,660,110,['调参试验与参数冻结']);
link('reliable-warning','parameter-freeze','M900,1520 V1600');

box('bench-validation',570,1790,660,110,['独立批次验证']);
box('bench-conditions',40,1790,420,110,['双支路台架对照']);
box('truth-records',1340,1790,420,110,['独立计量与操作记录']);
link('parameter-freeze','bench-validation','M900,1710 V1790');
link('bench-conditions','bench-validation','M460,1845 H570');
link('truth-records','bench-validation','M1340,1845 H1230');

box('comparison',570,1980,660,110,['基线与策略对照评价']);
box('threshold-baseline',40,1980,420,110,['单阈值基线']);
box('sampling-baseline',1340,1980,420,110,['固定采样基线']);
link('bench-validation','comparison','M900,1900 V1980');
link('threshold-baseline','comparison','M460,2035 H570');
link('sampling-baseline','comparison','M1340,2035 H1230');

box('diagnostic-evidence',60,2170,440,110,['检出、误报与时延']);
box('communication-evidence',680,2170,440,110,['事件送达与恢复']);
box('applicability',1300,2170,440,110,['可检边界与适用条件']);
link('comparison','diagnostic-evidence','M900,2090 V2130 H280 V2170');
link('comparison','communication-evidence','M900,2090 V2170');
link('comparison','applicability','M900,2090 V2130 H1520 V2170');

svg.push('</svg>');
await fs.writeFile(target,svg.join('\n'),'utf8');
console.log(target);
