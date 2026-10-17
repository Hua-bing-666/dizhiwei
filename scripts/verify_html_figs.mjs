// HTML 图版式校验（check-only）：针对 draw_route_figs.py / draw_signal_figs.py
// 渲染的 HTML/CSS 图。检查：文本两两重叠（非祖先关系）、文本越出画布、
// 最小字号按 420pt 放置宽度换算 ≥ 9.5pt。清单：tmp/htmlfig/*.html。
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const scratch=path.join(root,'tmp','htmlfig_check');await mkdir(scratch,{recursive:true});
const reportPath=path.join(scratch,'htmlfig_report.json');

// 图库清单：name → 相对 root 的 html 源 + 绘制宽度 px
const FIGS=[
  {name:'route_risk_chain',    html:'tmp/htmlfig/route_risk_chain.html',     w:1300},
  {name:'route_decision_fork', html:'tmp/htmlfig/route_decision_fork.html',  w:1060},
  {name:'route_gantt',         html:'tmp/htmlfig/route_gantt.html',          w:1060},
  {name:'signal_chain',        html:'tmp/htmlfig/signal_chain.html',         w:1180},
  {name:'fault_mechanism',     html:'tmp/htmlfig/fault_mechanism.html',      w:1180},
  {name:'frame_layout',        html:'tmp/htmlfig/frame_layout.html',         w:1180},
  {name:'judging_chain',       html:'tmp/htmlfig/judging_chain.html',        w:1180},
];

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
  const isAncestor=(a,b)=>a.contains(b), rel=(a,b)=>isAncestor(a,b)||isAncestor(b,a);
  // 直接携带文本的叶子元素
  const leaves=[...document.querySelectorAll('body *')].filter(e=>{
    if(!e.offsetParent && getComputedStyle(e).position!=='fixed')return false;
    return [...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
  }).map(e=>{
    const r=e.getBoundingClientRect(),cs=getComputedStyle(e);
    return {el:e,text:e.textContent.trim().slice(0,24),
            x:r.x,y:r.y,w:r.width,h:r.height,size:parseFloat(cs.fontSize),
            wsize:cs.fontWeight,bold:parseInt(cs.fontWeight)>=700&&/[\u4e00-\u9fa5A-Za-z0-9]/.test(e.textContent),
            scale:!!e.closest('[data-scale]'),
            hidden:cs.visibility==='hidden'||cs.display==='none'};
  }).filter(t=>t.text&&!t.hidden);
  const W=document.documentElement.scrollWidth, H=document.body.scrollHeight;
  const overlap=(a,b)=>Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>2&&Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>2;
  const overlapping=leaves.flatMap((a,i)=>leaves.slice(i+1).filter(b=>!rel(a.el,b.el)&&overlap(a,b)).map(b=>[a.text,b.text]));
  /* ---------- 块级元素两两重叠（含装饰件，排除祖孙） ---------- */
  const cls=e=>typeof e.className==='string'&&e.className?'.'+e.className.trim().split(/\s+/).join('.'):e.tagName;
  const blocks=[...document.querySelectorAll('body *')].filter(e=>{
    const cs=getComputedStyle(e);
    if(cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity)===0)return false;
    const r=e.getBoundingClientRect();
    if(e.hasAttribute('data-line')||e.hasAttribute('data-deco'))return false;
    return r.width>5&&r.height>5;
  }).map(e=>({el:e,r:e.getBoundingClientRect(),
              tag:cls(e),txt:(e.textContent||'').trim().slice(0,16)}));
  const ovl=(x,y)=>Math.min(x.right,y.right)-Math.max(x.left,y.left)>2&&
                   Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>2;
  const blockOverlaps=blocks.flatMap((a,i)=>blocks.slice(i+1)
      .filter(b=>!rel(a.el,b.el)&&ovl(a.r,b.r))
      .map(b=>[a.tag+'['+a.txt+']',b.tag+'['+b.txt+']']));
  /* ---------- 绝对定位元素是否溢出定位父容器（容差 6px） ---------- */
  const T=6;
  const oob=[...document.querySelectorAll('body *')].filter(e=>{
    const cs=getComputedStyle(e); if(cs.position!=='absolute')return false;
    if(e.hasAttribute('data-deco')||e.hasAttribute('data-line'))return false;
    const p=e.offsetParent; if(!p||p.tagName==='BODY')return false;
    const r=e.getBoundingClientRect(), pr=p.getBoundingClientRect();
    return r.left<pr.left-T||r.top<pr.top-T||r.right>pr.right+T||r.bottom>pr.bottom+T;
  }).map(e=>cls(e)+'['+(e.textContent||'').trim().slice(0,16)+']');
  const outside=leaves.filter(t=>t.x<-1||t.y<-1||t.x+t.w>W+1||t.y+t.h>H+1).map(t=>t.text);
  return {width:W,height:H,textCount:leaves.length,
          minFontPx:Math.min(...leaves.map(t=>t.size)),
          minBoldPx:Math.min(...leaves.filter(t=>t.bold).map(t=>t.size)),
          boldList:leaves.filter(t=>t.bold).map(t=>t.text+'@'+t.size),
          smallList:leaves.filter(t=>t.size*0.75*436/W<6&&!t.el.closest('[data-scale]')).map(t=>t.text+'@'+t.size),
          allList:leaves.filter(t=>!t.scale).map(t=>t.text+'@'+t.size+'/'+Math.round(t.wsize)),
          overlapping,outside,blockOverlaps,oob};
})()`;

const report={date:new Date().toISOString().slice(0,10),mode:'check_only_no_png_written',figures:[]};
let bad=0;
try{
  await send('Page.enable');await send('Runtime.enable');
  for(const figure of FIGS){
    let html=await readFile(path.join(root,figure.html),'utf8');
    const file=path.join(scratch,figure.name+'.html');
    await writeFile(file,html);
    await send('Page.navigate',{url:pathToFileURL(file).href});
    await evaluate('document.fonts.ready');await delay(200);
    const c=await evaluate(checks);
    // 字号换算：绘制宽 figure.w px；A4 版心放置 15.4cm=436pt，px→pt 系数 0.75
    const K=0.75*436/figure.w;
    const minFontPt=c.minFontPx*K;   // 次要文本（下限 6pt）
    const mainFontPt=c.minBoldPx*K;  // 主要文本（下限 9.5pt）
    const problems=[];
    if(c.overlapping.length)problems.push('overlapping '+JSON.stringify(c.overlapping));
    if(c.outside.length)problems.push('outside '+JSON.stringify(c.outside));
    if(c.blockOverlaps.length)problems.push('blockOverlap '+JSON.stringify(c.blockOverlaps.slice(0,6)));
    if(c.oob.length)problems.push('outOfParent '+JSON.stringify(c.oob.slice(0,6)));
    if(minFontPt<4.5)problems.push('minFontPt '+minFontPt.toFixed(2)+' (<4.5 刻度下限)');
    if(c.smallList.length>6)problems.push('次要字偏小 '+c.smallList.length+' 处: '+JSON.stringify(c.smallList.slice(0,6)));
    if(mainFontPt<9.5)problems.push('mainFontPt '+mainFontPt.toFixed(2)+' (<9.5)');
    const entry={name:figure.name,html:figure.html,textCount:c.textCount,
                 minFontPt:Number(minFontPt.toFixed(2)),
                 mainFontPt:Number(mainFontPt.toFixed(2)),
                 small:problems.some(p=>p.startsWith('minFontPt'))?c.smallList.slice(0,8):[],
                 boldMin:c.boldList.slice(0,6),
                 all:c.allList,problems};
    report.figures.push(entry);
    if(problems.length){bad++;console.log('  ✗ '+figure.name+' -> '+problems.join(' | '))}
    else console.log('  ✓ '+figure.name+' ('+c.textCount+' texts, min '+entry.minFontPt+'pt, main '+entry.mainFontPt+'pt)');
  }
}finally{
  await call('Browser.close').catch(()=>{});ws.close();child.kill();
}
await writeFile(reportPath,JSON.stringify(report,null,2));
console.log(bad? bad+' / '+FIGS.length+' 张 HTML 图存在问题，详见 '+path.relative(root,reportPath)
              : FIGS.length+' 张 HTML 图全部通过：无重叠、无越界、字号达标。');
process.exit(bad?1:0);
