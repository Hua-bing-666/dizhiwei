// Actual SVG text geometry in an owned headless Edge session.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const scratch=path.join(root,'tmp','presentation_diagram_review');await mkdir(scratch,{recursive:true});
const profile=path.join(scratch,'edge-'+crypto.randomUUID());
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let browser;
for(let i=0;i<100;i++){try{const port=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();break}catch{await delay(250)}}
if(!browser){child.kill();throw Error('Owned browser unavailable')}
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});let id=0;const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}))})}
const {targetId}=await call('Target.createTarget',{url:'about:blank'}),{sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
const send=(method,params)=>call(method,params,sessionId);
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const provenance=JSON.parse(await readFile(path.join(root,'application/figures/presentation_review/figure_provenance.json'),'utf8'));
const report={date:'2026-10-04',classification:'svg_text_layout_checks_not_scientific_or_physical_validation',physical_validation:false,figures:[]};
try{
 await send('Page.enable');await send('Runtime.enable');
 for(const fig of provenance.figures){
  const base=path.join(root,'application/figures/presentation_review',fig.name),svg=await readFile(base+'.svg','utf8');
  const html=path.join(scratch,fig.name+'.html');await writeFile(html,'<!doctype html><meta charset="utf-8"><style>body{margin:0;background:white}svg{display:block;width:1000px;height:auto}</style>'+svg.replace(/<\?xml[^>]*>/,'').replace(/<!DOCTYPE[\s\S]*?\]>\s*/,''));
  await send('Page.navigate',{url:pathToFileURL(html).href});
  for(let i=0;i<50;i++){if(await evaluate('!!document.querySelector("svg text")'))break;await delay(100)}
  await evaluate('document.fonts.ready');
  await send('Emulation.setDeviceMetricsOverride',{width:1000,height:fig.height,deviceScaleFactor:2,mobile:false});
  const result=await evaluate(`(()=>{
   const svg=document.querySelector('svg'),v=svg.viewBox.baseVal,inv=svg.getScreenCTM().inverse();
   const texts=[...svg.querySelectorAll('text')].filter(t=>t.textContent.trim()).map((t,i)=>{
    const box=t.getBBox(),matrix=inv.multiply(t.getScreenCTM());
    const points=[[box.x,box.y],[box.x+box.width,box.y],[box.x,box.y+box.height],[box.x+box.width,box.y+box.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(matrix));
    const xs=points.map(p=>p.x),ys=points.map(p=>p.y),font=parseFloat(getComputedStyle(t).fontSize);
    return {i,text:t.textContent.trim(),x0:Math.min(...xs),x1:Math.max(...xs),y0:Math.min(...ys),y1:Math.max(...ys),fontPx:font};
   });
   const outside=texts.filter(t=>t.x0<v.x-.2||t.y0<v.y-.2||t.x1>v.x+v.width+.2||t.y1>v.y+v.height+.2),overlaps=[];
   for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){
    const a=texts[i],b=texts[j],x=Math.min(a.x1,b.x1)-Math.max(a.x0,b.x0),y=Math.min(a.y1,b.y1)-Math.max(a.y0,b.y0);
    if(x>.3&&y>.3)overlaps.push({a:a.text,b:b.text,xOverlap:x,yOverlap:y});
   }
   const boxErrors=[];for(const g of svg.querySelectorAll('[data-box]')){const x=+g.dataset.x,y=+g.dataset.y,w=+g.dataset.w,h=+g.dataset.h;for(const t of g.querySelectorAll('text')){const b=t.getBBox();if(b.x<x+6||b.y<y+4||b.x+b.width>x+w-6||b.y+b.height>y+h-4)boxErrors.push(t.textContent)}}
   return {boxErrors,viewBox:{width:v.width,height:v.height},textCount:texts.length,minimumTextPx:Math.min(...texts.map(t=>t.fontPx)),outside,overlaps,texts};
  })()`);
  const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await writeFile(base+'.png',Buffer.from(shot.data,'base64'));
  result.name=fig.name;result.sha256={svg:sha(await readFile(base+'.svg')),png:sha(await readFile(base+'.png'))};
  if(result.sha256.svg!==fig.svg_sha256)throw Error('Stale SVG provenance '+fig.name);
  result.minimumTextPtAt425pt=result.minimumTextPx*425/result.viewBox.width;report.figures.push(result);
  console.log(fig.name,JSON.stringify({outside:result.outside,overlaps:result.overlaps,boxErrors:result.boxErrors,minPtAt425:result.minimumTextPtAt425pt}));
 }
 report.status=report.figures.every(f=>!f.outside.length&&!f.overlaps.length&&!f.boxErrors.length&&f.minimumTextPtAt425pt>=9)?'passed':'failed';
 report.source_sha256={script:sha(await readFile(fileURLToPath(import.meta.url))),provenance:sha(await readFile(path.join(root,'application/figures/presentation_review/figure_provenance.json')))};
 await writeFile(path.join(root,'simulation/presentation_review/diagram_layout_checks.json'),JSON.stringify(report,null,2)+'\n');
 if(report.status!=='passed')throw Error('Figure text layout failed; see saved record');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
