// Check the current concept viewer without rewriting its frozen CAD or captures.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),scratch=path.join(root,'tmp/quality_model_viewer');await mkdir(scratch,{recursive:true});
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--user-data-dir='+path.join(scratch,'edge-'+crypto.randomUUID()),'about:blank'],{windowsHide:true,stdio:'ignore'});
const profile=child.spawnargs.find(x=>x.startsWith('--user-data-dir=')).slice('--user-data-dir='.length),delay=ms=>new Promise(r=>setTimeout(r,ms));
let browser;for(let i=0;i<100;i++){try{const port=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();break}catch{await delay(250)}}
if(!browser){child.kill();throw Error('Owned browser unavailable')}
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});let id=0;const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}))})}
const {targetId}=await call('Target.createTarget',{url:'about:blank'}),{sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});const send=(method,params)=>call(method,params,sessionId);
async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),name='deliverables/台架三维结构交互模型_收集优化候选版.html';
const report={date:'2026-10-05',classification:'actual_offline_webgl_concept_viewer_not_manufacturing_validation',physical_validation:false,views:[],controls:[],console_errors:[],external_requests:[],screenshots:[]};
ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.sessionId!==sessionId)return;if(m.method==='Runtime.exceptionThrown')report.console_errors.push(m.params.exceptionDetails.text);if(m.method==='Network.requestWillBeSent'&&/^https?:/.test(m.params.request.url))report.external_requests.push(m.params.request.url)});
async function screen(label){const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}),bytes=Buffer.from(shot.data,'base64'),p='tmp/quality_model_viewer/'+label+'.png';await writeFile(path.join(root,p),bytes);report.screenshots.push({path:p,sha256:sha(bytes)})}
try{
 await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1120,deviceScaleFactor:1,mobile:false});await send('Page.navigate',{url:pathToFileURL(path.join(root,name)).href});
 let ready=false;for(let i=0;i<120;i++){if(await evaluate('!!window.benchReady')){ready=true;break}const error=await evaluate('window.benchError||null');if(error)throw Error(error);await delay(100)}if(!ready)throw Error('Concept model did not load');
 for(const width of [375,768,1024,1440]){
  await send('Emulation.setDeviceMetricsOverride',{width,height:1120,deviceScaleFactor:1,mobile:false});
  for(const view of ['iso','top','front','pressure','leak']){
   await evaluate(`bench.view('${view}')`);await delay(150);
   const result=await evaluate(`(()=>{if(bench.getState().current!=='${view}')throw Error('View state');if(document.documentElement.scrollWidth>innerWidth+1)throw Error('Root overflow');const s=document.getElementById('overlay'),w=s.viewBox.baseVal.width,h=s.viewBox.baseVal.height;const labels=[...s.querySelectorAll('text')].map(e=>{const b=e.getBBox();return{text:e.textContent,x:b.x,y:b.y,width:b.width,height:b.height}}),outside=labels.filter(b=>b.x<0||b.y<0||b.x+b.width>w||b.y+b.height>h),overlap=[];for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j];if(Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>.5&&Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>.5)overlap.push([a.text,b.text]);}const sb=s.getBoundingClientRect(),tb=document.querySelector('.stage-tag').getBoundingClientRect(),tag={x:tb.x-sb.x,y:tb.y-sb.y,width:tb.width,height:tb.height};for(const a of labels)if(Math.min(a.x+a.width,tag.x+tag.width)-Math.max(a.x,tag.x)>.5&&Math.min(a.y+a.height,tag.y+tag.height)-Math.max(a.y,tag.y)>.5)overlap.push([a.text,'stage-tag']);return{width:innerWidth,view:'${view}',state:bench.getState(),label_count:labels.length,outside,overlap}})()`);report.views.push(result);if([375,1440].includes(width))await screen('viewer-'+width+'-'+view);
  }
 }
 await evaluate(`(()=>{document.getElementById('cables').click();if(!bench.getState().showCables)throw Error('Cable control');document.getElementById('cables').click();document.getElementById('lid').click();if(!bench.getState().lidOpen)throw Error('Lid');document.getElementById('lid').click();document.getElementById('labels').click();if(bench.getState().showLabels)throw Error('Labels');document.getElementById('labels').click();for(const id of ['zoom-in','zoom-out','rotate-left','rotate-right'])document.getElementById(id).click();const c=document.getElementById('canvas');c.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowLeft'}));c.dispatchEvent(new KeyboardEvent('keydown',{key:'+'}));document.getElementById('reset').click();if(bench.getState().current!=='iso')throw Error('Reset');})()`);report.controls=['five_view_state_changes','cable_visibility','lid_open_close','label_visibility','zoom_rotate_buttons','keyboard_actions','reset'];
 report.status=report.views.some(v=>v.outside.length||v.overlap.length)||report.console_errors.length||report.external_requests.length?'needs_visual_layout_repair':'passed_programmatic_viewer_checks_manual_review_pending';
 report.source_sha256={[name]:sha(await readFile(path.join(root,name))),'scripts/verify_quality_model_viewer.mjs':sha(await readFile(fileURLToPath(import.meta.url)))};
 await writeFile(path.join(root,'simulation/quality_review/model_viewer_checks.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,views:report.views.length,issues:report.views.filter(v=>v.outside.length||v.overlap.length).map(v=>({width:v.width,view:v.view,outside:v.outside,overlap:v.overlap}))}));
 if(report.status==='needs_visual_layout_repair')throw Error('Concept viewer label/console check needs repair');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
