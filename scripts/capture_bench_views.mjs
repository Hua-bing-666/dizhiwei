// Capture real offline WebGL renders through CDP, awaiting actual scene readiness.
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
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
const uri=pathToFileURL(path.join(root,'deliverables','台架三维结构交互模型.html')).href;
const {targetId}=await call('Target.createTarget',{url:'about:blank'});
const {sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
const send=(method,params)=>call(method,params,sessionId);
const evaluate=async expression=>{const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value};
const views=[['iso','bench_isometric',1000,460],['top','bench_top',1000,540],['front','bench_front',1000,440],['pressure','bench_pressure_detail',620,500],['leak','bench_leak_detail',620,500]];
const poses={};
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
  const png=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  await writeFile(path.join(root,'application','figures',name+'.png'),Buffer.from(png.data,'base64'));
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
 const checksRecord={views:5,controls:'passed',desktopOverflow:false,narrowOverflow:false,meshCount:checks.meshCount,source:'actual offline WebGL scene; not physical validation'};
 await writeFile(path.join(scratch,'projected_anchors.json'),JSON.stringify(poses,null,2));
 await writeFile(path.join(scratch,'viewer_checks.json'),JSON.stringify(checksRecord,null,2));
 const hashes={};for(const [,name] of views)hashes[name+'.png']=crypto.createHash('sha256').update(await readFile(path.join(root,'application','figures',name+'.png'))).digest('hex');
 const sceneHash=crypto.createHash('sha256').update(await readFile(path.join(root,'application','models','bench_scene.json'))).digest('hex');
 await writeFile(path.join(root,'application','models','bench_views.json'),JSON.stringify({projectedAnchors:poses,viewports:views,sceneSha256:sceneHash,imageSha256:hashes,interactiveChecks:checksRecord},null,2));
 console.log('Actual WebGL views captured; 5 views, control actions and desktop/narrow width checks passed.');
}finally{await call('Browser.close').catch(()=>{});ws.close();child.kill()}
