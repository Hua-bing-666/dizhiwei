// Check-only layout verifier: no PNG is written, no source hash is touched.
// Checks, for every figure: text outside the canvas, type below 9.5 pt at 420 pt
// width, label/label overlap, labels escaping their own box, and guide labels
// sitting on top of a box. Originally mirrored the checks in
// verify_compact_water_figure.mjs (archived 2026-10-18 to archive/scripts_历史/
// together with its now-deleted subject); those checks are now inherited here
// for the whole figure library.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const scratch=path.join(root,'tmp','figure_layout');await mkdir(scratch,{recursive:true});
const reportPath=path.join(scratch,'layout_report.json');

const profile=path.join(scratch,'edge-'+crypto.randomUUID());
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  ['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],
  {windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let browser;
for(let i=0;i<100;i++){
  try{
    const port=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];
    browser=await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();break;
  }catch{await delay(100)}
}
if(!browser){child.kill();throw Error('Owned browser unavailable')}
const ws=new WebSocket(browser.webSocketDebuggerUrl);
await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
let id=0;const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}))})}
const {targetId}=await call('Target.createTarget',{url:'about:blank'});
const {sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
const send=(method,params)=>call(method,params,sessionId);
async function evaluate(expression){
  const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}

const checks=`(()=>{
  const s=document.querySelector('svg'),v=s.viewBox.baseVal;
  const texts=[...s.querySelectorAll('text')].map(e=>{
    const b=e.getBBox(),z=e.getCTM();
    const p=new DOMPoint(b.x,b.y).matrixTransform(z),q=new DOMPoint(b.x+b.width,b.y+b.height).matrixTransform(z);
    const r=s.getBoundingClientRect();
    return {el:e,text:(e.textContent||'').trim(),size:parseFloat(getComputedStyle(e).fontSize),
            x:p.x-r.x,y:p.y-r.y,w:q.x-p.x,h:q.y-p.y};
  }).filter(t=>t.text);
  const r=s.getBoundingClientRect();
  const overlap=(a,b)=>Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>.5&&Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>.5;
  const boxes=[...s.querySelectorAll('[data-kind="box"]')].map(g=>{const b=g.querySelector('rect').getBBox();return b});

  /* ---------- 配色 / 对比度 / 灰度可分辨性 ---------- */
  const parseColor=c=>{
    if(!c)return null;
    c=String(c).trim();
    if(c==='none'||c==='transparent'||c==='currentColor'||c==='')return null;
    let m;
    if((m=c.match(/^#([0-9a-f]{3})$/i))){
      const h=m[1];return [parseInt(h[0]+h[0],16),parseInt(h[1]+h[1],16),parseInt(h[2]+h[2],16)];
    }
    if((m=c.match(/^#([0-9a-f]{6})$/i))){
      return [parseInt(m[1].slice(0,2),16),parseInt(m[1].slice(2,4),16),parseInt(m[1].slice(4,6),16)];
    }
    if((m=c.match(/^rgba?\(([^)]+)\)$/i))){
      const p=m[1].split(',').map(x=>parseFloat(x));
      if(p.length>3&&p[3]===0)return null;
      return [p[0],p[1],p[2]];
    }
    const named={black:[0,0,0],white:[255,255,255],red:[255,0,0],green:[0,128,0],blue:[0,0,255]};
    return named[c.toLowerCase()]||null;
  };
  const isGray=c=>c&&Math.abs(c[0]-c[1])<=6&&Math.abs(c[1]-c[2])<=6;
  const lum=c=>{const f=x=>{x/=255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)};
    return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])};
  const contrast=(a,b)=>{const l1=lum(a),l2=lum(b);return (Math.max(l1,l2)+.05)/(Math.min(l1,l2)+.05)};
  const hex=c=>'#'+c.map(x=>Math.round(x).toString(16).padStart(2,'0')).join('');
  // 文本背景：取"包围该文本的最小带填充形状"；找不到按白底。
  // 注意不能直接用 <g> 上的 fill——那是给文本继承的文字色，不是底色。
  const toRoot=el=>{const m=el.getCTM();const p=new DOMPoint(0,0).matrixTransform(m);return p};
  const textBackground=el=>{
    const box=el.closest?el.closest('[data-kind="box"]'):null;
    const scopes=box?[box]:[];
    let node=el.parentNode;
    while(node&&node!==s){scopes.push(node);node=node.parentNode;}
    const tb=el.getBBox();
    const tp=new DOMPoint(tb.x,tb.y).matrixTransform(el.getCTM());
    const tq=new DOMPoint(tb.x+tb.width,tb.y+tb.height).matrixTransform(el.getCTM());
    const tx0=Math.min(tp.x,tq.x),ty0=Math.min(tp.y,tq.y),tx1=Math.max(tp.x,tq.x),ty1=Math.max(tp.y,tq.y);
    let best=null,bestArea=Infinity;
    for(const scope of scopes){
      const shapes=scope.querySelectorAll?[...scope.querySelectorAll('rect,circle,polygon,path')].filter(sh=>!sh.closest('defs')):[];
      for(const sh of shapes){
        const f=parseColor(sh.getAttribute('fill'))||parseColor(getComputedStyle(sh).fill);
        if(!f)continue;
        const b=sh.getBBox();
        const p=new DOMPoint(b.x,b.y).matrixTransform(sh.getCTM());
        const q=new DOMPoint(b.x+b.width,b.y+b.height).matrixTransform(sh.getCTM());
        const bx0=Math.min(p.x,q.x),by0=Math.min(p.y,q.y),bx1=Math.max(p.x,q.x),by1=Math.max(p.y,q.y);
        if(bx0-1<=tx0&&by0-1<=ty0&&bx1+1>=tx1&&by1+1>=ty1){
          const area=(bx1-bx0)*(by1-by0);
          if(area<bestArea){bestArea=area;best=f;}
        }
      }
    }
    return best||[255,255,255];
  };
  const contrastIssues=[];
  for(const t of texts){
    const fill=parseColor(getComputedStyle(t.el).fill)||[0,0,0];
    const bg=textBackground(t.el);
    const cs=getComputedStyle(t.el);
    const large=t.size>=18||(t.size>=14&&(cs.fontWeight==='700'||cs.fontWeight==='bold'));
    const need=large?3:4.5;
    const ratio=contrast(fill,bg);
    if(ratio<need)contrastIssues.push([t.text.slice(0,24),hex(fill),hex(bg),Number(ratio.toFixed(2)),need]);
  }
  // 装饰用彩色：只统计形状（rect/circle/path/polygon/line）的填色与描边，
  // 排除"近黑的文字墨色"与"近白的纸面底纹"——它们是墨和纸，不是配色。
  const palette=new Map();
  for(const el of s.querySelectorAll('rect,circle,path,polygon,line')){
    if(el.closest('defs'))continue;
    for(const attr of ['fill','stroke']){
      const c=parseColor(el.getAttribute(attr))||parseColor(getComputedStyle(el)[attr]);
      if(!c||isGray(c))continue;
      const l=lum(c);
      if(l<.04||l>.85)continue;
      palette.set(hex(c),c);
    }
  }
  const colors=[...palette.keys()];
  // 灰度可分辨性：黑白打印时任意两种彩色转灰度后亮度差 >= 0.05
  const grayCollisions=[];
  for(let i=0;i<colors.length;i++)for(let j=i+1;j<colors.length;j++){
    if(Math.abs(lum(palette.get(colors[i]))-lum(palette.get(colors[j])))<.05)
      grayCollisions.push([colors[i],colors[j]]);
  }

  return {
    width:v.width,height:v.height,
    clipWidth:r.width,clipHeight:r.height,
    textCount:texts.length,
    minFontPt:Math.min(...texts.map(t=>t.size))*420/v.width,
    outside:texts.filter(t=>t.x<-.5||t.y<-.5||t.x+t.w>r.width+.5||t.y+t.h>r.height+.5).map(t=>t.text),
    overlappingLabels:texts.flatMap((a,i)=>texts.slice(i+1).filter(b=>overlap(a,b)).map(b=>[a.text,b.text])),
    labelsOutsideOwnBox:[...s.querySelectorAll('[data-kind="box"]')].flatMap(g=>{
      const b=g.querySelector('rect').getBBox();
      return [...g.querySelectorAll('text')].filter(e=>{const t=e.getBBox();
        return t.x<b.x+2||t.y<b.y+2||t.x+t.width>b.x+b.width-2||t.y+t.height>b.y+b.height-2}).map(e=>e.textContent);
    }),
    guideLabelsOverBoxes:[...s.querySelectorAll('text')].filter(e=>!e.closest('[data-kind="box"]')).flatMap(e=>{
      const t=e.getBBox();
      return boxes.filter(b=>Math.min(t.x+t.width,b.x+b.width)-Math.max(t.x,b.x)>.5&&Math.min(t.y+t.height,b.y+b.height)-Math.max(t.y,b.y)>.5).map(()=>e.textContent);
    }),
    palette:colors,
    contrastIssues,
    grayCollisions
  };
})()`;

const sources=JSON.parse(await readFile(path.join(root,'simulation/quality_review/figure_sources.json'),'utf8'));
const extra=[];
for(const name of ['roadmap','threshold_separation','detection_boundary']){
  extra.push({name,svg:'simulation/project_review/figures/'+name+'.svg',strict:true});
}
extra.push({name:'技术路线图_单色学术版',svg:'deliverables/技术路线图_单色学术版.svg',strict:true});
extra.push({name:'tech_roadmap_staircase',svg:'application/figures/tech_roadmap_staircase.svg',strict:true});
extra.push({name:'diagnosis_closed_loop',svg:'application/figures/diagnosis_closed_loop.svg',strict:true});
extra.push({name:'system_responsibilities',svg:'application/figures/quality_review/system_responsibilities.svg',strict:true});
extra.push({name:'measurement_interfaces',svg:'application/figures/quality_review/measurement_interfaces.svg',strict:true});
extra.push({name:'water_layout',svg:'application/figures/quality_review/water_layout.svg',strict:true});
extra.push({name:'durable_event_sequence',svg:'application/figures/quality_review/durable_event_sequence.svg',strict:true});
extra.push({name:'network_topology',svg:'application/figures/network_topology.svg',strict:true});
extra.push({name:'power_and_pin_resources',svg:'application/figures/interface_review/power_and_pin_resources.svg',strict:true});
extra.push({name:'系统总体结构_单色学术版',svg:'deliverables/系统总体结构_单色学术版.svg',strict:true});
const figures=[...sources.figures,...extra];
const report={date:new Date().toISOString().slice(0,10),mode:'check_only_no_png_written',figures:[]};
let bad=0;
try{
  await send('Page.enable');await send('Runtime.enable');
  for(const figure of figures){
    let svg=await readFile(path.join(root,figure.svg),'utf8');
    svg=svg.replace(/<\?xml[^>]*>/,'').replace(/<!DOCTYPE[\s\S]*?\]>\s*/,'');
    const file=path.join(scratch,figure.name+'.html');
    await writeFile(file,'<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:white}svg{display:block;width:1000px;height:auto}</style>'+svg);
    await send('Page.navigate',{url:pathToFileURL(file).href});
    for(let i=0;i<60;i++){if(await evaluate('!!document.querySelector("svg text")'))break;await delay(50)}
    await evaluate('document.fonts.ready');await delay(120);
    const checksResult=await evaluate(checks);
    const problems=[];
    if(checksResult.outside.length)problems.push('outside:'+JSON.stringify(checksResult.outside));
    if(checksResult.minFontPt<9.5)problems.push('minFontPt '+checksResult.minFontPt.toFixed(2));
    if(checksResult.overlappingLabels.length)problems.push('overlappingLabels '+JSON.stringify(checksResult.overlappingLabels));
    if(checksResult.labelsOutsideOwnBox.length)problems.push('labelsOutsideOwnBox '+JSON.stringify(checksResult.labelsOutsideOwnBox));
    if(checksResult.guideLabelsOverBoxes.length)problems.push('guideLabelsOverBoxes '+JSON.stringify(checksResult.guideLabelsOverBoxes));
    if(checksResult.palette.length>(figure.strict?4:6))
      problems.push('palette '+(figure.strict?'>4':'')+' '+checksResult.palette.length+' 色: '+JSON.stringify(checksResult.palette));
    if(checksResult.contrastIssues.length)problems.push('contrast '+JSON.stringify(checksResult.contrastIssues));
    if(checksResult.grayCollisions.length)problems.push('grayCollision '+JSON.stringify(checksResult.grayCollisions));
    const entry={name:figure.name,svg:figure.svg,textCount:checksResult.textCount,
                 minFontPt:Number(checksResult.minFontPt.toFixed(2)),
                 palette:checksResult.palette,problems};
    report.figures.push(entry);
    if(problems.length){bad++;console.log('  ✗ '+figure.name+' -> '+problems.join(' | '))}
    else console.log('  ✓ '+figure.name+' ('+checksResult.textCount+' texts, min '+entry.minFontPt+'pt, '+checksResult.palette.length+' 彩色)');
  }
}finally{
  await call('Browser.close').catch(()=>{});ws.close();child.kill();
}
report.figuresChecked=figures.length;report.figuresWithProblems=bad;
await writeFile(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(bad? bad+' / '+figures.length+' 张图存在问题（版式或配色），详见 '+path.relative(root,reportPath)
              : figures.length+' 张图全部通过：无越界、无重叠、无压框、字号达标、配色合规。');
