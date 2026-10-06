import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const scratch=path.join(root,'tmp','platform-browser-'+crypto.randomUUID()),out=path.join(root,'deliverables','软件升级验收预览');await mkdir(scratch,{recursive:true});await mkdir(out,{recursive:true});
const profile=path.join(scratch,'edge'),downloads=path.join(scratch,'downloads');await mkdir(downloads);
const python=path.join(root,'tmp/cad_runtime/Scripts/python.exe'),port=18765;
const service=spawn(python,[path.join(root,'scripts/run_platform.py'),'--port',String(port),'--db',path.join(scratch,'test.sqlite')],{windowsHide:true,stdio:'pipe'});
let stderr='';service.stderr.on('data',d=>stderr+=d);service.stdout.on('data',()=>{});
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let browser,ws;
const report={date:'2026-10-07',classification:'software_browser_and_CAD_view_checks_not_physical',physical_data:false,checks:[],screenshots:[],console_errors:[]};
try{
 for(let i=0;i<100;i++){try{const dp=(await readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await(await fetch('http://127.0.0.1:'+dp+'/json/version')).json();await fetch(`http://127.0.0.1:${port}/api/state`).then(r=>{if(!r.ok)throw Error('service');});break;}catch{await delay(200);}}
 if(!browser)throw Error('Browser/service not ready '+stderr);
 ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});let id=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}};
 function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});}
 const {targetId}=await call('Target.createTarget',{url:'about:blank'}),{sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
 const send=(method,params)=>call(method,params,sessionId);
 async function evaluate(expression){const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
 ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.sessionId===sessionId&&m.method==='Runtime.exceptionThrown')report.console_errors.push(m.params.exceptionDetails.text);});
 const check=async(name,expression)=>{const ok=await evaluate(expression);if(!ok)throw Error(name);report.checks.push(name);};
 async function ready(url,flag){await send('Page.navigate',{url});for(let i=0;i<100;i++){if(await evaluate(`!!window.${flag}`))return;await delay(100);}throw Error('Not ready '+flag);}
 async function screen(name){await delay(150);const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await writeFile(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));report.screenshots.push(name+'.png');}
 await send('Page.enable');await send('Runtime.enable');await send('Page.setDownloadBehavior',{behavior:'allow',downloadPath:downloads});
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});
 await ready(pathToFileURL(path.join(root,'deliverables/index.html')).href,'platformReady');
 const source=JSON.parse(await readFile(path.join(root,'simulation/platform_upgrade/web_data.json'),'utf8'));
 await check('all_27_offline_traces_match_saved_C_outputs',`(()=>{const data=${JSON.stringify(source.traces)};for(const [k,v] of Object.entries(data)){if(JSON.stringify(PLATFORM_DATA.traces[k].samples)!==JSON.stringify(v.samples))return false;}return Object.keys(data).length===27;})()`);
 for(const width of [375,768,1024,1440]){await send('Emulation.setDeviceMetricsOverride',{width,height:1050,deviceScaleFactor:1,mobile:false});for(const page of ['overview','monitor','events','devices','history','settings']){await check(`page_${page}_${width}_no_root_overflow`,`(()=>{platform.navigate('${page}');return document.documentElement.scrollWidth<=innerWidth+1&&document.querySelector('nav [data-page="${page}"]').getAttribute('aria-current')==='page';})()`);if(width===375||width===1440)await screen(`${page}-${width}`);}}
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});
 await check('missing_reading_null_not_zero_and_chart_break',`(()=>{platform.setReplay({scene:'missing',cursor:362});platform.navigate('monitor');return platform.current().p1===null&&platform.current().status===3&&document.getElementById('page-body').textContent.includes('暂停原因判断')&&document.querySelector('#pressure-chart path').getAttribute('d').includes('M');})()`);
 await check('offline_archive_requires_view',`(()=>{platform.setReplay({scene:'leak',cursor:450});const e=platform.events().find(e=>e.code>=4);platform.openEvent(e.id);document.getElementById('event-stage').value='archived';document.getElementById('event-note').value='test';document.getElementById('event-form').requestSubmit();return document.getElementById('event-message').textContent.includes('先记录');})()`);
 const frozen=await evaluate('JSON.stringify(platform.events().find(e=>e.code>=4).snapshot)');
 await evaluate(`document.getElementById('event-stage').value='viewed';document.getElementById('event-note').value='<img src=x onerror=alert(1)> fixture';document.getElementById('event-form').requestSubmit();`);
 await check('event_note_escaped_snapshot_unchanged',`document.getElementById('event-history').querySelectorAll('img').length===0&&JSON.stringify(platform.events().find(e=>e.code>=4).snapshot)===${JSON.stringify(frozen)}`);
 await screen('event-dialog-desktop');await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
 await check('native_dialog_escape',`!document.getElementById('event-dialog').open`);
 await evaluate('platform.exportCSV();platform.exportWorkspace();');await delay(300);
 const csv=await readFile(path.join(downloads,'drip-samples.csv'),'utf8'),records=JSON.parse(await readFile(path.join(downloads,'drip-records.json'),'utf8'));
 if(!csv.includes('version,source,physical_data')||records.physical_data!==false||records.source!=='compiled_C_offline_replay')throw Error('Export provenance');report.checks.push('exports_preserve_source_units_version_and_nonphysical_flag');
 const http=`http://127.0.0.1:${port}`;
 const denied=await fetch(http+'/api/replay/start',{method:'POST',headers:{'Origin':'https://untrusted.example','Content-Type':'application/json'},body:'{}'});if(denied.status!==403)throw Error('Cross origin write');report.checks.push('cross_origin_write_rejected');
 const traversed=await fetch(http+'/..%2Fprototype%2Fplatform_service.py');if(traversed.status!==404)throw Error('Path traversal');report.checks.push('server_does_not_publish_repository_sources');
 await ready(http,'platformReady');await evaluate('platform.connect()');await evaluate("platform.mutate('/api/replay/start',{scene:'leak',sigma:.3})");
 for(let i=0;i<15;i++)await evaluate("platform.mutate('/api/replay/step',{n:30})");
 await check('HTTP_C_SQLite_UI_snapshot_equal',`(async()=>{const r=await(await fetch('/api/state')).json();return JSON.stringify(r.current)===JSON.stringify(platform.current())&&r.count===450&&r.rf_connected===false;})()`);
 await evaluate("platform.navigate('monitor')");await screen('backend-monitor-desktop');
 await evaluate("platform.navigate('settings');platform.mutate('/api/control',{action:'request',id:'browser-demo'})");await evaluate("platform.mutate('/api/control',{action:'receive',id:'browser-demo'})");await evaluate("platform.mutate('/api/control',{action:'execute',id:'browser-demo'})");
 await check('control_request_receipt_simulation_separate',`platform.getState().server.commands[0].status==='demo_confirmed'&&platform.getState().server.commands[0].physical_verified===false&&document.getElementById('commands').textContent.includes('软件 LED 指示开启')`);
 await screen('backend-control-desktop');
 await check('candidate_calibration_tool_keeps_runtime_reference',`(async()=>{const before=JSON.stringify(platform.getState().server.configuration);document.getElementById('calibration-example').click();document.getElementById('calibration-fit').click();for(let i=0;i<100;i++){await new Promise(r=>setTimeout(r,50));if(document.getElementById('calibration-result').textContent.includes('Q ='))break;}return document.getElementById('calibration-result').textContent.includes('0.5000')&&before===JSON.stringify(platform.getState().server.configuration);})()`);
 await evaluate("document.getElementById('calibration-csv').scrollIntoView({block:'center'});");await screen('backend-calibration-desktop');await evaluate('window.scrollTo(0,0)');
 await evaluate("platform.navigate('monitor');document.querySelectorAll('details').forEach(x=>x.open=true);document.getElementById('research-scene').scrollIntoView({block:'center'});");await screen('research-desktop');
 await evaluate("document.getElementById('research-scene').value='drift';document.getElementById('research-scene').dispatchEvent(new Event('change'));");
 await check('research_failures_and_denominators_retained',`document.getElementById('research-scene').checkVisibility()&&document.getElementById('research-results').textContent.includes('不作早期判据')&&document.getElementById('page-body').textContent.includes('72 个新种子组合')`);
 await ready(http+'/清水试验台架_V1.1.html','benchReady');
 await check('CAD_title_is_objective_without_release_marketing',`document.querySelector('h1').textContent==='双支路清水试验台架'&&!document.body.innerText.includes('升级版')`);
 for(const view of ['iso','top','pressure','leak','electronics']){await evaluate(`bench.view('${view}')`);await check('CAD_'+view+'_labels_within_stage_no_rect_overlap',`(()=>{const svg=document.getElementById('overlay'),rects=[...svg.querySelectorAll('rect')].map(x=>({x:+x.getAttribute('x'),y:+x.getAttribute('y'),w:+x.getAttribute('width'),h:+x.getAttribute('height')})),stage=document.getElementById('stage');return rects.every(a=>a.x>=0&&a.y>=0&&a.x+a.w<=stage.clientWidth&&a.y+a.h<=stage.clientHeight)&&rects.every((a,i)=>rects.slice(i+1).every(b=>!(a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y)));})()`);await screen('model-'+view);}
 await check('CAD_actual_new_geometry_loaded',`bench.getData().meshes.some(m=>m.name==='perforated_splash_guard')&&bench.getState().meshCount===207`);
 await send('Emulation.setDeviceMetricsOverride',{width:375,height:1050,deviceScaleFactor:1,mobile:false});await evaluate("bench.view('iso')");await screen('model-mobile');await check('CAD_mobile_no_root_overflow',`document.documentElement.scrollWidth<=innerWidth+1`);
 if(report.console_errors.length)throw Error('Browser errors '+JSON.stringify(report.console_errors));report.checks.push('no_uncaught_browser_exceptions');
 await writeFile(path.join(root,'simulation/platform_upgrade/browser_acceptance.json'),JSON.stringify(report,null,2)+'\n');console.log(report.checks.length+' browser checks passed; '+report.screenshots.length+' screenshots');
 await call('Browser.close');
} finally {if(ws)ws.close();child.kill();service.kill();}
