// Capture native UI regions without replacing DOM, styling controls or editing pixels.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'application/figures/print_polish'),scratch=path.join(root,'tmp','print_panel_capture');await mkdir(out,{recursive:true});await mkdir(scratch,{recursive:true});
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
const report={date:'2026-10-06',classification:'actual_local_browser_captures_of_synthetic_ui_not_hardware',physical_data:false,dom_replaced:false,css_overridden:false,print_media:true,pixels_postprocessed:false,screenshots:[],research_notice_checks:[]};
async function capture(name,selector,body=false){
 const geometry=await evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)}),b=el.getBoundingClientRect(),clip=${body?'({x:0,y:0,width:1440,height:1800})':'({x:b.x,y:b.y,width:b.width,height:b.height})'};const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),texts=[];let n;while(n=walker.nextNode()){if(!n.textContent.trim())continue;const p=n.parentElement;if(!p||!p.checkVisibility()||getComputedStyle(p).visibility==='hidden')continue;const r=document.createRange();r.selectNodeContents(n);for(const a of r.getClientRects()){if(a.width<.1||a.height<.1||a.x<clip.x-.2||a.y<clip.y-.2||a.right>clip.x+clip.width+.2||a.bottom>clip.y+clip.height+.2)continue;texts.push({text:n.textContent.trim(),fontPx:parseFloat(getComputedStyle(p).fontSize),x:a.x-clip.x,y:a.y-clip.y,width:a.width,height:a.height});}}const overlaps=[];for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++){const a=texts[i],b=texts[j],dx=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x),dy=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);if(dx>.5&&dy>.5)overlaps.push({a:a.text,b:b.text,dx,dy});}return {clip,texts,overlaps,minimumTextPx:Math.min(...texts.map(t=>t.fontPx))}})()`);
 if(!body&&(geometry.clip.x<0||geometry.clip.y<0||geometry.clip.x+geometry.clip.width>1440||geometry.clip.y+geometry.clip.height>1800))throw Error('Native region extends beyond capture viewport');
 const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,clip:{...geometry.clip,scale:1}});
 const bytes=Buffer.from(shot.data,'base64');await writeFile(path.join(out,name+'.png'),bytes);
 report.screenshots.push({name,selector,viewport:{width:1440,height:1800,deviceScaleFactor:2},...geometry,minimumTextPtAt425pt:geometry.minimumTextPx*425/geometry.clip.width,sha256:sha(bytes),state:await evaluate('operations.getState()'),diagnosis:await evaluate('operations.currentStatus()'),displayed:await evaluate("({k:document.getElementById('feature-k').textContent,r:document.getElementById('feature-r').textContent,q:document.getElementById('overview-q').textContent})")});
}
try{
 await send('Page.enable');await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1800,deviceScaleFactor:2,mobile:false});await send('Page.navigate',{url:pathToFileURL(path.join(root,'deliverables','index.html')).href});
 for(let i=0;i<100;i++){if(await evaluate('!!window.operationsReady'))break;await delay(100)}
 await evaluate("operations.setReplay({scenario:'leak',noise:'0.3',quality:'replay',time:450});operations.navigate('overview');document.activeElement.blur();window.scrollTo(0,0);document.fonts.ready");await delay(250);
 await send('Emulation.setEmulatedMedia',{media:'print'});await delay(200);
 await capture('website_diagnosis_panel','.diagnosis-card');
 report.source_sha256={site:sha(await readFile(path.join(root,'deliverables/index.html'))),script:sha(await readFile(fileURLToPath(import.meta.url)))};
 report.math=await evaluate("(()=>{const c=document.querySelector('.diagnosis-card');return {unitCount:c.querySelectorAll('math').length,radicalCount:c.querySelectorAll('msqrt').length,fractionCount:c.querySelectorAll('mfrac').length,exponentCount:c.querySelectorAll('msup').length}})()");
 if(report.math.radicalCount!==1||report.math.fractionCount!==2||report.math.exponentCount!==1)throw Error('Missing native mathematical unit');
 const panel=report.screenshots[0];if(panel.overlaps.length)throw Error('Panel text overlaps: '+JSON.stringify(panel.overlaps));
 await send('Emulation.setEmulatedMedia',{media:'screen'});
 report.responsive_units=[];
 for(const width of [375,768,1024,1440]){
  await send('Emulation.setDeviceMetricsOverride',{width,height:1800,deviceScaleFactor:2,mobile:false});await delay(150);
  const check=await evaluate(`(()=>{const width=${width},units=[...document.querySelectorAll('.feature-unit')].map(el=>{const p=el.getBoundingClientRect(),m=el.querySelector('math').getBoundingClientRect();return {contained:m.x>=p.x-.5&&m.right<=p.right+.5&&m.y>=p.y-.5&&m.bottom<=p.bottom+.5}});return {width,documentWidth:document.documentElement.scrollWidth,units}})()`);
  if(check.documentWidth>width||check.units.length!==2||check.units.some(x=>!x.contained))throw Error('Responsive mathematical unit layout failed: '+JSON.stringify(check));
  report.responsive_units.push(check);
 }
 report.status='captured_requires_visual_review';
 await writeFile(path.join(root,'simulation/print_polish/website_capture_checks.json'),JSON.stringify(report,null,2)+'\n');
 console.log('Captured print layout from native site; units use MathML fractions, radical and exponent.');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
