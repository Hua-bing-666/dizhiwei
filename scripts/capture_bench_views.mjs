// Capture real offline WebGL renders through CDP, awaiting actual scene readiness.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const review=process.argv.includes('--collection-review');
const models=path.join(root,'application','models',...(review?['collection_review']:[]));
const figures=path.join(root,'application','figures',...(review?['collection_review']:[]));await mkdir(figures,{recursive:true});
const scratch=path.join(root,'tmp','bench_cdp');await mkdir(scratch,{recursive:true});
const profile=path.join(scratch,'edge-'+crypto.randomUUID());
const edge='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const child=spawn(edge,['--headless=new','--no-first-run','--no-default-browser-check','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let browser;
for(let i=0;i<100;i++){try{const port=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await (await fetch('http://127.0.0.1:'+port+'/json/version')).json();break}catch{await delay(250)}}
if(!browser)throw Error('Fresh Edge debugging session unavailable');
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
let id=0;const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const {resolve,reject}=pending.get(m.id);pending.delete(m.id);m.error?reject(Error(JSON.stringify(m.error))):resolve(m.result)}};
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}))})}
const uri=pathToFileURL(path.join(root,'deliverables',review?'台架三维结构交互模型_收集优化候选版.html':'台架三维结构交互模型.html')).href;
const {targetId}=await call('Target.createTarget',{url:'about:blank'});
const {sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
const send=(method,params)=>call(method,params,sessionId);
const evaluate=async expression=>{const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value};
const views=[['iso','bench_isometric',1000,460],['top','bench_top',1000,540],['front','bench_front',1000,440],['pressure','bench_pressure_detail',620,500],['leak','bench_leak_detail',620,500]];
const poses={},visibilityChecks=[];
try{
 await send('Page.enable');await send('Runtime.enable');
 await send('Emulation.setDeviceMetricsOverride',{width:1000,height:460,deviceScaleFactor:2,mobile:false});
 await send('Page.navigate',{url:uri+'?capture=1'});
 let ready=false;for(let i=0;i<180;i++){if(await evaluate('!!window.benchReady')){ready=true;break}const error=await evaluate('window.benchError||null');if(error)throw Error(error);await delay(250)}
 if(!ready)throw Error('WebGL scene did not become ready');
 for(const [view,name,width,height] of views){
  await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:2,mobile:false});
  await evaluate(`bench.view(${JSON.stringify(view)})`);await delay(150);
  poses[view]=await evaluate('Object.fromEntries(Object.entries(bench.getData().anchors).map(([k,p])=>[k,bench.project(p)]))');
  if(review){const layout=JSON.parse(await readFile(path.join(models,'bench_layout.json'),'utf8'));const bounds=name=>layout.parts.find(p=>p.name===name).evidence.bounds;const cup=bounds('open_measuring_vessel'),outlet=bounds('leak_free_outlet'),foot=bounds('support_6_foot'),tray=bounds('removable_catch_tray');const extras={outlet_bottom:[685,305,outlet.min[2]],vessel_lip:[685,305,cup.max[2]],foot_edge:[foot.max[0],250,30],tray_edge:[tray.min[0],250,30],base_left:[0,0,26],base_right:[900,0,26],base_front:[900,0,26],base_back:[900,520,26]};poses[view]={...poses[view],...await evaluate(`Object.fromEntries(Object.entries(${JSON.stringify(extras)}).map(([k,p])=>[k,bench.project(p)]))`)};}
  if(review && ['iso','top'].includes(view)){
   const visible=await evaluate(`(()=>{const targets={P0:'P0_connector',R:'restriction_pivot',P1:'P1_connector',Q:'Q_pulse_cap',A:'A_equivalent_load_pivot',B:'B_switch_pivot',leak:'open_measuring_vessel',node:'electronics_lid'},results=[];const ray=new THREE.Raycaster();for(const[key,targetPart]of Object.entries(targets)){const anchor=key==='leak'&&${JSON.stringify(view)}==='top'?'leak_rim':key;const[x,y]=bench.project(modelData.anchors[anchor]);const samples=[];for(const[dx,dy]of [[0,0],[.5,0],[-.5,0],[0,.5],[0,-.5]]){ray.setFromCamera(new THREE.Vector2((x+dx)/${width}*2-1,1-(y+dy)/${height}*2),camera);samples.push(ray.intersectObjects(meshes.filter(m=>m.visible),false)[0]?.object.name||null)}results.push({label:key,anchor,targetPart,firstHits:samples,targetVisibleWithinHalfPixel:samples.includes(targetPart)})}return results})()`);
   if(visible.some(c=>!c.targetVisibleWithinHalfPixel))throw Error(view+' annotation occlusion: '+JSON.stringify(visible));visibilityChecks.push({view,checks:visible});
  }
  const png=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  await writeFile(path.join(figures,name+'.png'),Buffer.from(png.data,'base64'));
 }
 // Check actual interactive controls and default/narrow layouts, not a mock.
 await send('Page.navigate',{url:uri});
 for(let i=0;i<180;i++){if(await evaluate('!!window.benchReady'))break;await delay(250)}
 await send('Emulation.setDeviceMetricsOverride',{width:1320,height:960,deviceScaleFactor:1,mobile:false});
 const checks=await evaluate(`(()=>{for(const b of document.querySelectorAll('[data-view]')){b.click();if(bench.getState().current!==b.dataset.view)throw Error('view switch failed')};document.getElementById('cables').click();if(!bench.getState().showCables)throw Error('cable control failed');document.getElementById('cables').click();document.getElementById('lid').click();if(!bench.getState().lidOpen)throw Error('lid control failed');document.getElementById('lid').click();document.getElementById('labels').click();if(bench.getState().showLabels)throw Error('label control failed');document.getElementById('labels').click();document.getElementById('reset').click();return {...bench.getState(),rootOverflow:document.documentElement.scrollWidth>innerWidth+1}})()`);
 if(checks.rootOverflow)throw Error('Desktop model viewer overflow');
 await delay(100);let screen=await send('Page.captureScreenshot',{format:'png'});await writeFile(path.join(scratch,'viewer-desktop.png'),Buffer.from(screen.data,'base64'));
 await send('Emulation.setDeviceMetricsOverride',{width:520,height:1100,deviceScaleFactor:1,mobile:false});await delay(100);await evaluate('bench.update()');
 if(await evaluate('document.documentElement.scrollWidth>innerWidth+1'))throw Error('Narrow model viewer overflow');
 screen=await send('Page.captureScreenshot',{format:'png'});await writeFile(path.join(scratch,'viewer-mobile.png'),Buffer.from(screen.data,'base64'));
 const checksRecord={views:5,controls:'passed',desktopOverflow:false,narrowOverflow:false,meshCount:checks.meshCount,source:'actual offline WebGL scene; not physical validation',viewerSha256:crypto.createHash('sha256').update(await readFile(fileURLToPath(uri))).digest('hex')};
 await writeFile(path.join(scratch,'projected_anchors.json'),JSON.stringify(poses,null,2));
 await writeFile(path.join(scratch,'viewer_checks.json'),JSON.stringify(checksRecord,null,2));
 const hashes={};for(const [,name] of views)hashes[name+'.png']=crypto.createHash('sha256').update(await readFile(path.join(figures,name+'.png'))).digest('hex');
 const sceneHash=crypto.createHash('sha256').update(await readFile(path.join(models,'bench_scene.json'))).digest('hex');
 await writeFile(path.join(models,'bench_views.json'),JSON.stringify({projectedAnchors:poses,viewports:views,sceneSha256:sceneHash,imageSha256:hashes,interactiveChecks:checksRecord,...(review?{annotationVisibilityChecks:visibilityChecks}:{})},null,2));
 if(review && process.argv.includes('--verify-plates')){
  const plates=[];
  for(const name of ['collection_overview','collection_installation','collection_interfaces','collection_metering']){
   await send('Page.navigate',{url:pathToFileURL(path.join(root,'tmp/application_diagrams',name+'.html')).href});
   for(let i=0;i<40;i++){if(await evaluate('!!document.querySelector("svg text")'))break;await delay(50)}
   const layout=await evaluate(`(()=>{const s=document.querySelector('svg'),w=s.viewBox.baseVal.width,h=s.viewBox.baseVal.height;const t=[...s.querySelectorAll('text')].map(e=>{const b=e.getBBox();return{text:e.textContent,x:b.x,y:b.y,w:b.width,h:b.height,size:+e.getAttribute('font-size')}});const outside=t.filter(b=>b.x<0||b.y<0||b.x+b.w>w||b.y+b.h>h);const overlaps=[];for(let i=0;i<t.length;i++)for(let j=i+1;j<t.length;j++){const a=t[i],b=t[j];if(Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>1&&Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>1)overlaps.push([a.text,b.text])}return{width:w,height:h,texts:t.length,minimumFontPx:Math.min(...t.map(b=>b.size)),outside,overlaps}})()`);
   if(layout.outside.length||layout.overlaps.length||layout.minimumFontPx<23)throw Error(name+' plate layout failed: '+JSON.stringify(layout));
   const files={};for(const ext of ['svg','png'])files[ext]=crypto.createHash('sha256').update(await readFile(path.join(figures,name+'.'+ext))).digest('hex');
   plates.push({name,...layout,sha256:files});
  }
  await writeFile(path.join(models,'plate_layout_checks.json'),JSON.stringify({classification:'browser_text_bounds_and_text_overlap_checks; visual inspection recorded separately',plates},null,2));
 }
 console.log('Actual WebGL views captured; 5 views, control actions and desktop/narrow width checks passed.');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
