// Inspect native SVG bounds and capture the actual larger-type variants.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'application/figures/method_revision'),scratch=path.join(root,'tmp/method_revision/visuals');await mkdir(scratch,{recursive:true});
const profile=path.join(scratch,'edge-'+crypto.randomUUID()),child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let browser;
for(let i=0;i<100;i++){try{const port=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();break}catch{await delay(100)}}
if(!browser){child.kill();throw Error('Owned browser unavailable')}
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});let id=0;const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}))})}
const {targetId}=await call('Target.createTarget',{url:'about:blank'}),{sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
const send=(method,params)=>call(method,params,sessionId);
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=JSON.parse(await readFile(path.join(root,'application/method_revision/figure_sources.json'),'utf8')),report={date:'2026-10-06',status:'programmatic_bounds_checked_visual_review_pending',physical_validation:false,figures:[]};
try{
 await send('Page.enable');await send('Runtime.enable');
 for(const figure of source.figures){
  let svg=await readFile(path.join(root,figure.svg),'utf8');svg=svg.replace(/<\?xml[^>]*>/,'').replace(/<!DOCTYPE[\s\S]*?\]>\s*/,'');
  const file=path.join(scratch,figure.name+'.html');await writeFile(file,'<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:white}svg{display:block;width:1000px;height:auto}</style>'+svg);
  await send('Page.navigate',{url:pathToFileURL(file).href});for(let i=0;i<60;i++){if(await evaluate('!!document.querySelector("svg text")'))break;await delay(50)}
  await evaluate('document.fonts.ready');await delay(100);
  const checks=await evaluate(`(()=>{const s=document.querySelector('svg'),v=s.viewBox.baseVal;const texts=[...s.querySelectorAll('text')].map(e=>{const b=e.getBBox(),z=e.getCTM(),p=new DOMPoint(b.x,b.y).matrixTransform(z),q=new DOMPoint(b.x+b.width,b.y+b.height).matrixTransform(z),r=s.getBoundingClientRect();return {text:e.textContent,size:parseFloat(getComputedStyle(e).fontSize),x:p.x-r.x,y:p.y-r.y,w:q.x-p.x,h:q.y-p.y}});const r=s.getBoundingClientRect();return {width:v.width,height:v.height,clip:{x:0,y:0,width:r.width,height:r.height},textCount:texts.length,minFontPt:Math.min(...texts.map(t=>t.size))*420/v.width,outside:texts.filter(t=>t.x<-.5||t.y<-.5||t.x+t.w>r.width+.5||t.y+t.h>r.height+.5),texts}})()`);
  if(checks.outside.length||checks.minFontPt<9.5)throw Error(figure.name+' bounds/font check '+JSON.stringify(checks.outside));
  const structural=await evaluate(`(()=>{const boxes=[...document.querySelectorAll('g[data-box]')].map(g=>({x:+g.dataset.x,y:+g.dataset.y,w:+g.dataset.w,h:+g.dataset.h,g}));const conflicts=[],outside=[];for(let i=0;i<boxes.length;i++){const a=boxes[i];for(let j=i+1;j<boxes.length;j++){const b=boxes[j];if(Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>1&&Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>1)conflicts.push([i,j])}for(const e of a.g.querySelectorAll('text')){const z=e.getBBox();if(z.x<a.x+3||z.y<a.y+3||z.x+z.width>a.x+a.w-3||z.y+z.height>a.y+a.h-3)outside.push(e.textContent)}}return {boxCount:boxes.length,boxIntersections:conflicts,textOutsideOwnBox:outside}})()`);
  if(structural.boxIntersections.length||structural.textOutsideOwnBox.length)throw Error(figure.name+' structural check '+JSON.stringify(structural));
  await send('Emulation.setDeviceMetricsOverride',{width:1000,height:Math.ceil(checks.clip.height),deviceScaleFactor:2,mobile:false});await delay(100);
  const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const bytes=Buffer.from(shot.data,'base64');await writeFile(path.join(out,figure.name+'.png'),bytes);
  const {texts,...compact}=checks;report.figures.push({name:figure.name,...compact,...structural,png_sha256:sha(bytes),svg_sha256:sha(await readFile(path.join(root,figure.svg)))});
 }
 await writeFile(path.join(root,'application/method_revision/figure_checks.json'),JSON.stringify(report,null,2)+'\n');console.log(report.figures.length+' figures: major type>=9.5pt at420pt, no out-of-frame text. Manual inspection still required.');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
