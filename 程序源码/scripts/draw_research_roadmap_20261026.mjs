import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const target=path.join(root,'deliverables/技术路线图_研究主线_20261026.svg');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const out=[`<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1730" viewBox="0 0 1800 1730" role="img" aria-labelledby="title desc">
<title id="title">南疆棉田滴灌支管异常识别研究技术路线</title>
<desc id="desc">研究问题是供压与支路切换扰动下识别支管持续异常。路线依次为：水力建模、测量标定与健康参照；参照残差、不重叠块特征与CUSUM判断；固定采样与事件触发策略对照及可靠告警；冻结参照门限策略后，在双支路台架使用独立批次和独立计量开展故障与正常扰动对照，评价可检边界、策略权衡与适用条件。图示拟研究的方法和验证关系，不表示实测性能已完成。</desc>
<defs><marker id="arrow" markerWidth="14" markerHeight="12" refX="13" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L14,6 L0,12 Z" fill="#30363b"/></marker>
<style>
text{font-family:SimSun,"Times New Roman",serif;font-size:42px;fill:#171b1e;text-anchor:middle;dominant-baseline:central}
.heading{font-size:44px;font-weight:700}.question{font-size:44px;font-weight:700}
.label{fill:#eef0f2;stroke:#a6adb3;stroke-width:1.5}.panel{fill:#fff;stroke:#7a838a;stroke-width:1.7}
.link{fill:none;stroke:#30363b;stroke-width:2.3;stroke-linejoin:round;marker-end:url(#arrow)}
.divider{stroke:#bdc3c8;stroke-width:1.5}
</style></defs><rect width="1800" height="1730" fill="#fff"/>`];
function text(x,y,s,cls=''){
 out.push(`<text x="${x}" y="${y}"${cls?` class="${cls}"`:''}>${esc(s)}</text>`);
}
function group(id,x,y,w,h,fn){
 out.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}">`);fn();out.push('</g>');
}
function stage(id,y,h,label,fn){
 group(id+'-label',40,y,260,h,()=>{
  out.push(`<rect class="label" x="40" y="${y}" width="260" height="${h}"/>`);
  text(170,y+h/2,label,'heading');
 });
 group(id,350,y,1410,h,()=>{
  out.push(`<rect class="panel" x="350" y="${y}" width="1410" height="${h}"/>`);fn();
 });
}
function link(from,to,y0,y1,label='',labelX=1330){
 out.push(`<path class="link" data-from="${from}" data-to="${to}" d="M1055,${y0} V${y1}"/>`);
 if(label)text(labelX,(y0+y1)/2,label);
}

stage('question',40,150,'研究问题',()=>{
 text(1055,85,'供压与支路切换扰动下，如何识别支管持续异常？','question');
 text(1055,145,'南疆棉田膜下滴灌 · 支管等效泄漏与区段受限');
});

stage('mechanism',280,200,'机理与观测',()=>{
 text(1055,325,'故障—扰动水力建模 → 测量标定与误差分析 → 健康参照建立','heading');
 text(1055,380,'压力、压差与流量观测；分析供压及负载变化的影响');
 text(1055,430,'界定故障与正常负载变化可能混淆的条件');
});
link('question','mechanism',190,280);

stage('diagnosis',590,200,'特征与判据',()=>{
 text(1055,635,'参照残差 → 不重叠块特征 → CUSUM累积判断','heading');
 text(1055,690,'持续偏离形成异常候选，结合切换工况挂起与复判');
 text(1055,740,'同等误报条件下与单阈值基线比较');
});
link('mechanism','diagnosis',480,590,'健康参照与测量数据');

stage('strategy',900,220,'采集与告警',()=>{
 text(700,950,'固定采样基线','heading');
 text(1055,950,'对照');
 text(1410,950,'事件触发策略','heading');
 text(1055,1010,'比较识别时延、漏检情况及采集通信开销');
 text(1055,1070,'LoRa可靠上报 → 落库确认 → 人工核查与复测');
});
link('diagnosis','strategy',790,900,'固定采样判据作为基线');

stage('validation',1230,260,'对照与评价',()=>{
 text(1055,1275,'双支路对照 · 独立计量 · 留出验证','heading');
 text(700,1330,'等效泄漏、区段受限');
 text(1410,1330,'供压扰动、B支路切换');
 out.push('<line class="divider" x1="1055" y1="1305" x2="1055" y2="1355"/>');
 text(1055,1390,'基线与策略对照：检出、误报、时延、送达与开销');
 text(1055,1445,'冻结参照、门限与策略后，用独立数据批次评价');
});
link('strategy','validation',1120,1230,'冻结参照、门限与策略');

group('outcome',350,1600,1410,90,()=>{
 out.push('<line class="divider" x1="350" y1="1600" x2="1760" y2="1600"/>');
 text(1055,1645,'可检幅度与持续时间 · 采集告警权衡 · 适用条件','heading');
});
link('validation','outcome',1490,1600,'独立对照评价',1250);
out.push('</svg>');
await fs.writeFile(target,out.join('\n'),'utf8');
console.log(target);
