// Capture native UI regions without replacing DOM, styling controls or editing pixels.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'application/figures/quality_review'),scratch=path.join(root,'tmp','quality_panel_capture');await mkdir(out,{recursive:true});await mkdir(scratch,{recursive:true});
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
const report={date:'2026-10-05',classification:'actual_local_browser_captures_of_synthetic_ui_not_hardware',physical_data:false,dom_replaced:false,css_overridden:false,pixels_postprocessed:false,screenshots:[],research_notice_checks:[]};
async function capture(name,selector,body=false){
 const geometry=await evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)}),b=el.getBoundingClientRect(),clip=${body?'({x:0,y:0,width:1440,height:1120})':'({x:b.x,y:b.y,width:b.width,height:b.height})'};const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),texts=[];let n;while(n=walker.nextNode()){if(!n.textContent.trim())continue;const p=n.parentElement;if(!p||!p.checkVisibility()||getComputedStyle(p).visibility==='hidden')continue;const r=document.createRange();r.selectNodeContents(n);for(const a of r.getClientRects()){if(a.width<.1||a.height<.1||a.x<clip.x-.2||a.y<clip.y-.2||a.right>clip.x+clip.width+.2||a.bottom>clip.y+clip.height+.2)continue;texts.push({text:n.textContent.trim(),fontPx:parseFloat(getComputedStyle(p).fontSize),x:a.x-clip.x,y:a.y-clip.y,width:a.width,height:a.height});}}const overlaps=[];for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){const a=texts[i],b=texts[j],dx=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x),dy=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);if(dx>.5&&dy>.5)overlaps.push({a:a.text,b:b.text,dx,dy});}return {clip,texts,overlaps,minimumTextPx:Math.min(...texts.map(t=>t.fontPx))}})()`);
 if(geometry.clip.y+geometry.clip.height>1120&&!body)throw Error('Native region extends beyond capture viewport');
 const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,clip:{...geometry.clip,scale:1}});
 const bytes=Buffer.from(shot.data,'base64');await writeFile(path.join(out,name+'.png'),bytes);
 report.screenshots.push({name,selector,viewport:{width:1440,height:1120,deviceScaleFactor:2},...geometry,minimumTextPtAt425pt:geometry.minimumTextPx*425/geometry.clip.width,sha256:sha(bytes),state:await evaluate('operations.getState()'),diagnosis:await evaluate('operations.currentStatus()'),displayed:await evaluate("({k:document.getElementById('feature-k').textContent,r:document.getElementById('feature-r').textContent,q:document.getElementById('overview-q').textContent})")});
}
try{
 await send('Page.enable');await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1120,deviceScaleFactor:2,mobile:false});await send('Page.navigate',{url:pathToFileURL(path.join(root,'deliverables','index.html')).href});
 for(let i=0;i<100;i++){if(await evaluate('!!window.operationsReady'))break;await delay(100)}
 await evaluate("operations.setReplay({scenario:'leak',noise:'0.3',quality:'replay',time:450});operations.navigate('overview');document.activeElement.blur();window.scrollTo(0,0);document.fonts.ready");await delay(250);
 await capture('website_diagnosis_panel','.diagnosis-card');await capture('website_overview_desktop','body',true);
 await evaluate("operations.createEvent();document.getElementById('event-viewed').click();document.getElementById('event-note').value='仅为流程演示：核对供压、阀态和传感器；未开展实物检修。';document.getElementById('event-result').value='pending';document.getElementById('event-form').requestSubmit();document.getElementById('event-dialog').close();operations.navigate('events');window.scrollTo(0,0)");await delay(250);
 await capture('website_events_desktop','body',true);
 await send('Page.navigate',{url:pathToFileURL(path.join(root,'deliverables','研究与答辩资料.html')).href});
 for(let i=0;i<100;i++){if(await evaluate('!!document.getElementById("historical-config-note")'))break;await delay(100)}
 for(const width of [375,768,1024,1440]){
  await send('Emulation.setDeviceMetricsOverride',{width,height:1120,deviceScaleFactor:1,mobile:false});
  const result=await evaluate("(()=>{const n=document.getElementById('historical-config-note');if(!n.textContent.includes('历史配置')||!n.textContent.includes('20261004-A06A07-v1'))throw Error('Historical notice');if(document.documentElement.scrollWidth>innerWidth+1)throw Error('Research notice overflow');return {width:innerWidth,notice_present:true,root_overflow:false}})()");report.research_notice_checks.push(result);
 }
 report.status='captured';report.source_sha256={script:sha(await readFile(fileURLToPath(import.meta.url))),site:sha(await readFile(path.join(root,'deliverables/index.html'))),research:sha(await readFile(path.join(root,'deliverables/研究与答辩资料.html'))),replay:sha(await readFile(path.join(root,'simulation/presentation_review/web_replay.json')))};
 await writeFile(path.join(root,'simulation/quality_review/website_capture_checks.json'),JSON.stringify(report,null,2)+'\n');
 const panel=report.screenshots[0];if(panel.minimumTextPtAt425pt<9||panel.overlaps.length)throw Error('Word panel fails text readability/overlap check');
 console.log('3 native captures; main panel min '+panel.minimumTextPtAt425pt.toFixed(2)+'pt at425pt; no panel text overlaps; research historical notice checked at4 widths.');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
