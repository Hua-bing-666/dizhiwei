// Inspect selected SVG geometry and actual 425pt review-page image placement.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),scratch=path.join(root,'tmp','presentation_assets'),out=path.join(root,'application/figures/presentation_review/proofs');await mkdir(scratch,{recursive:true});await mkdir(out,{recursive:true});
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
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),selection=JSON.parse(await readFile(path.join(root,'simulation/presentation_review/figure_selection.json'),'utf8'));
const report={date:'2026-10-04',classification:'selected_figures_and_425pt_browser_proofs_not_word_pdf_acceptance',physical_data:false,figures:[],proofs:[],console_errors:[]};
ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.sessionId===sessionId&&m.method==='Runtime.exceptionThrown')report.console_errors.push(m.params.exceptionDetails.text)});
async function navigate(url,condition){await send('Page.navigate',{url});for(let i=0;i<100;i++){if(await evaluate(condition))return;await delay(100)}throw Error('Page readiness timeout')}
try{
 await send('Page.enable');await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1000,height:1600,deviceScaleFactor:2,mobile:false});
 for(const fig of selection.main_figures){
  if(sha(await readFile(path.join(root,fig.png)))!==fig.sha256.png)throw Error('Stale selected PNG');
  if(!fig.svg)continue;
  const bytes=await readFile(path.join(root,fig.svg));if(sha(bytes)!==fig.sha256.svg)throw Error('Stale selected SVG');
  const html=path.join(scratch,fig.id+'.html');await writeFile(html,'<!doctype html><meta charset="utf-8"><style>body{margin:0}svg{display:block;width:1000px;height:auto}</style>'+bytes.toString('utf8'));
  await navigate(pathToFileURL(html).href,'!!document.querySelector("svg text")');await evaluate('document.fonts.ready');
  const result=await evaluate(`(()=>{const svg=document.querySelector('svg'),v=svg.viewBox.baseVal,inv=svg.getScreenCTM().inverse(),texts=[...svg.querySelectorAll('text')].filter(t=>t.textContent.trim()).map(t=>{const b=t.getBBox(),m=inv.multiply(t.getScreenCTM()),p=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));return {text:t.textContent.trim(),x0:Math.min(...p.map(a=>a.x)),x1:Math.max(...p.map(a=>a.x)),y0:Math.min(...p.map(a=>a.y)),y1:Math.max(...p.map(a=>a.y)),font:parseFloat(getComputedStyle(t).fontSize)*Math.hypot(m.a,m.b)}}),outside=texts.filter(t=>t.x0<-.2||t.y0<-.2||t.x1>v.width+.2||t.y1>v.height+.2),overlaps=[];for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){const a=texts[i],b=texts[j],dx=Math.min(a.x1,b.x1)-Math.max(a.x0,b.x0),dy=Math.min(a.y1,b.y1)-Math.max(a.y0,b.y0);if(dx>.3&&dy>.3)overlaps.push({a:a.text,b:b.text,dx,dy});}return {width:v.width,height:v.height,texts,minimum_font_pt_at_425pt:Math.min(...texts.map(t=>t.font))*425/v.width,outside,overlaps}})()`);
  result.id=fig.id;report.figures.push(result);if(result.outside.length||result.overlaps.length||result.minimum_font_pt_at_425pt<9)throw Error(JSON.stringify({figure:fig.id,...result}));
 }
 const capture=JSON.parse(await readFile(path.join(root,'simulation/presentation_review/capture_checks.json'),'utf8')),panel=capture.screenshots.find(r=>r.name==='website_diagnosis_panel');report.figures.push({id:'F09',minimum_font_pt_at_425pt:panel.minimumTextPtAt425pt,outside:[],overlaps:panel.overlaps,source:'native DOM capture checks'});
 await send('Emulation.setDeviceMetricsOverride',{width:900,height:1800,deviceScaleFactor:2,mobile:false});
 await navigate(pathToFileURL(path.join(root,'deliverables/申报图文取舍与呈现审阅.html')).href,'[...document.images].every(i=>i.complete&&i.naturalWidth>0)');await evaluate('document.fonts.ready');
 for(const fig of selection.main_figures){
  const placement=await evaluate(`(()=>{const a=document.getElementById('${fig.id}');a.scrollIntoView({block:'start'});const i=a.querySelector('img'),b=i.getBoundingClientRect(),c=a.getBoundingClientRect(),caption=a.querySelector('.caption').getBoundingClientRect(),notes=a.querySelector('dl').getBoundingClientRect();return {image_width_pt:b.width*3/4,image_height_pt:b.height*3/4,caption_font_pt:parseFloat(getComputedStyle(a.querySelector('.caption')).fontSize)*3/4,caption_after_image:caption.y>=b.bottom-.5,notes_after_caption:notes.y>=caption.bottom-.5,clip:{x:c.x,y:c.y+scrollY,width:c.width,height:c.height}}})()`);
  if(Math.abs(placement.image_width_pt-425)>.1||!placement.caption_after_image||!placement.notes_after_caption)throw Error('Proof placement '+fig.id);
  const rendered=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{...placement.clip,scale:1}}),bytes=Buffer.from(rendered.data,'base64');const file=fig.id+'_425pt.png';await writeFile(path.join(out,file),bytes);report.proofs.push({id:fig.id,mode:'color',file:'application/figures/presentation_review/proofs/'+file,sha256:sha(bytes),...placement});
 }
 await evaluate("document.getElementById('gray').click();if(document.getElementById('gray').getAttribute('aria-pressed')!=='true')throw Error('Gray toggle')");
 for(const id of ['F02','F06','F07']){
  const clip=await evaluate(`(()=>{const a=document.getElementById('${id}');a.scrollIntoView({block:'start'});const b=a.getBoundingClientRect();return {x:b.x,y:b.y+scrollY,width:b.width,height:b.height}})()`);
  const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{...clip,scale:1}}),bytes=Buffer.from(result.data,'base64'),file=id+'_gray_425pt.png';await writeFile(path.join(out,file),bytes);report.proofs.push({id,mode:'gray_css_review_only',file:'application/figures/presentation_review/proofs/'+file,sha256:sha(bytes)});
 }
 if(report.console_errors.length)throw Error('Review-page JS exception');report.status='passed';report.source_sha256={script:sha(await readFile(fileURLToPath(import.meta.url))),selection:sha(await readFile(path.join(root,'simulation/presentation_review/figure_selection.json'))),review_html:sha(await readFile(path.join(root,'deliverables/申报图文取舍与呈现审阅.html'))),capture_checks:sha(await readFile(path.join(root,'simulation/presentation_review/capture_checks.json')))};
 await writeFile(path.join(root,'simulation/presentation_review/asset_checks.json'),JSON.stringify(report,null,2)+'\n');console.log('9 selected figures passed; 9 color425pt and3 grayscale proofs captured. Word pagination remains pending.');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
