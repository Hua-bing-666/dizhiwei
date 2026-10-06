import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn,execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec=promisify(execFile),root=process.cwd();
const out=path.join(root,'tmp/desktop_acceptance');
const folder=process.env.DESKTOP_TEST_FOLDER||path.join(out,'独立解压 空格/滴智卫_桌面版_V1.2');
const exe=path.join(folder,'滴智卫.exe');
const python=path.join(root,'tmp/desktop_build_env/Scripts/python.exe');
const native=path.join(root,'scripts/desktop_native_check.py');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const report={date:'2026-10-07',version:'1.2.0',classification:'packaged_EXE_software_checks_not_physical',checks:[],screenshots:[],console_errors:[]};
let app,ws,pending,id=0,url;
const check=(name,condition)=>{if(!condition)throw Error(name);report.checks.push(name);console.log('PASS '+name);};
const helper=(action,...args)=>exec(python,[native,action,String(app.pid),...args],{windowsHide:true,timeout:10000});
function call(method,params={},sessionId){return new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});}
let session;
async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function waitUntil(fn,name,timeout=20000){const start=Date.now();while(Date.now()-start<timeout){try{if(await fn())return;}catch{}await delay(150);}throw Error(name);}
async function launch(port){
 pending=new Map();id=0;
 app=spawn(exe,[],{cwd:out,windowsHide:true,stdio:'ignore',env:{...process.env,PATH:'C:/Windows/System32',PYTHONPATH:'',PYTHONHOME:'',WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port}`}});
 await waitUntil(async()=>{const info=JSON.parse(await fs.readFile(path.join(folder,'data/runtime.json'),'utf8'));if(info.pid!==app.pid)return false;url=info.url;return (await fetch(url+'/api/state')).ok;},'EXE service not ready',30000);
 await waitUntil(async()=>{const targets=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();return targets.some(t=>t.url?.startsWith(url));},'Native WebView2 not ready',30000);
 const browser=await(await fetch(`http://127.0.0.1:${port}/json/version`)).json();
 ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}if(m.sessionId===session&&m.method==='Runtime.exceptionThrown')report.console_errors.push(m.params.exceptionDetails.text);};
 const targets=(await call('Target.getTargets')).targetInfos;
 const target=targets.find(t=>t.type==='page'&&t.url.startsWith(url));
 session=(await call('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
 await call('Runtime.enable',{},session);await call('Page.enable',{},session);
 await waitUntil(()=>evaluate('window.platformReady&&platform.getState().backend'),'Desktop auto-connect');
 await waitUntil(()=>evaluate('!!window.pywebview?.api?.save_export'),'Native export bridge');
 check('desktop_bridge_only_exposes_save_export',await evaluate("JSON.stringify(Object.keys(window.pywebview.api))==='[\"save_export\"]'"));
}
async function screenshot(name){await delay(250);const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},session);await fs.writeFile(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));report.screenshots.push(name+'.png');}
async function close(){
 const currentUrl=url,pid=app.pid;
 await helper('close');
 await waitUntil(()=>app.exitCode!==null,'Desktop did not exit',15000);
 await waitUntil(async()=>{try{await fetch(currentUrl+'/api/state');return false;}catch{return true;}},'Service still listening');
 await waitUntil(async()=>{try{await fs.stat(path.join(folder,'data/runtime.json'));return false;}catch{return true;}},'Runtime receipt still present');
 ws?.close();
 report.checks.push('native_close_stops_EXE_and_loopback_service_'+pid);
}
try{
 await fs.mkdir(out,{recursive:true});
 for(const name of ['desktop-samples.csv','desktop-records.json'])await fs.rm(path.join(out,name),{force:true});
 await launch(19361);
 check('independent_extraction_Chinese_space_path_unrelated_CWD_no_Python_or_GCC_PATH',await evaluate('platform.getState().backend'));
 check('fresh_database_has_no_user_records',await evaluate('platform.samples().length===0&&platform.getState().server.runs.length===0'));
 for(const page of ['overview','monitor','events','devices','history','experiments','bench','settings']){
  await evaluate(`platform.navigate('${page}')`);
  check('native_page_'+page+'_no_overflow',await evaluate(`document.documentElement.scrollWidth<=innerWidth+1&&document.querySelector('nav [data-page="${page}"]').getAttribute('aria-current')==='page'`));
  if(['overview','monitor','bench','settings'].includes(page))await screenshot('desktop-'+page);
 }
 const second=spawn(exe,[],{cwd:out,windowsHide:true,stdio:'ignore'});
 await waitUntil(()=>second.exitCode!==null,'Duplicate instance did not exit');
 check('duplicate_click_does_not_create_second_service',second.exitCode===0&&app.exitCode===null);
 await evaluate("platform.mutate('/api/replay/start',{scene:'leak',sigma:.3})");
 for(let i=0;i<15;i++)await evaluate("platform.mutate('/api/replay/step',{n:30})");
 check('bundled_C_worker_450_samples_and_candidates',await evaluate('platform.samples().length===450&&platform.events().some(e=>e.code>=4)'));
 const frozen=await evaluate('JSON.stringify(platform.current())');
 const event=await evaluate('platform.events().find(e=>e.code>=4).id');
 await evaluate(`platform.openEvent(${JSON.stringify(event)});document.getElementById('event-stage').value='viewed';document.getElementById('event-note').value='桌面版软件核查记录；不代表实物测试';document.getElementById('event-form').requestSubmit();`);
 await waitUntil(()=>evaluate(`platform.events().find(e=>e.id===${JSON.stringify(event)}).notes.length===1`),'Event note not saved');
 check('native_event_note_does_not_rewrite_snapshot',await evaluate('JSON.stringify(platform.current())==='+JSON.stringify(frozen)));
 await evaluate("document.getElementById('event-dialog').close();platform.navigate('monitor')");await screenshot('desktop-monitor-with-data');
 await helper('screen',path.join(out,'desktop-native-window.png'));report.screenshots.push('desktop-native-window.png');
 await evaluate("platform.navigate('bench');document.getElementById('model-load').click()");
 await waitUntil(()=>evaluate("!!document.querySelector('#model-slot iframe')?.contentWindow?.benchReady"),'3D model scripts missing');
 await waitUntil(()=>evaluate("!!document.querySelector('#model-slot iframe').contentDocument.querySelector('canvas')"),'3D canvas missing');
 await evaluate("document.querySelector('#model-slot iframe').scrollIntoView({block:'center'})");
 await screenshot('desktop-bench-model');
 check('embedded_3D_canvas_loaded_without_CAD_or_network',await evaluate("document.querySelector('#model-slot iframe').contentDocument.querySelector('canvas').width>0"));
 await evaluate("platform.mutate('/api/control',{action:'request',id:'desktop-demo'})");
 await evaluate("platform.mutate('/api/control',{action:'receive',id:'desktop-demo'})");
 await evaluate("platform.mutate('/api/control',{action:'execute',id:'desktop-demo'})");
 check('software_control_workflow_keeps_physical_false',await evaluate("platform.getState().server.commands.some(c=>c.command_id==='desktop-demo'&&c.status==='demo_confirmed'&&!c.physical_verified)"));
 await evaluate("platform.navigate('experiments');document.getElementById('calibration-example').click();document.getElementById('calibration-fit').click()");
 await waitUntil(()=>evaluate("document.getElementById('calibration-result').textContent.includes('拟合残差 RMSE')"),'Calibration UI result missing');
 check('native_candidate_reference_fit_not_applied_automatically',await evaluate('JSON.stringify(platform.current())==='+JSON.stringify(frozen)));
 await evaluate("platform.navigate('history');document.getElementById('export-csv').click()");
 await waitUntil(async()=>JSON.parse((await helper('list')).stdout).some(w=>w.cls==='#32770'),'CSV native save dialog missing');
 await helper('save',path.join(out,'desktop-samples.csv'));
 await waitUntil(async()=>!!(await fs.stat(path.join(out,'desktop-samples.csv'))),'CSV download missing');
 const csv=await fs.readFile(path.join(out,'desktop-samples.csv'),'utf8');check('native_save_CSV_450_rows_with_origin_flag',csv.trim().split('\n').length===451&&csv.includes('physical_data')&&csv.includes('sqlite_host_replay'));
 await waitUntil(async()=>!JSON.parse((await helper('list')).stdout).some(w=>w.cls==='#32770'),'CSV dialog still open');
 await evaluate("document.getElementById('export').click()");
 await waitUntil(async()=>JSON.parse((await helper('list')).stdout).some(w=>w.cls==='#32770'),'JSON native save dialog missing');
 await helper('save',path.join(out,'desktop-records.json'));
 await waitUntil(async()=>!!(await fs.stat(path.join(out,'desktop-records.json'))),'JSON download missing');
 const records=JSON.parse(await fs.readFile(path.join(out,'desktop-records.json'),'utf8'));check('native_save_JSON_contains_samples_notes_and_nonphysical_flag',records.samples.length===450&&records.physical_data===false&&records.events.some(e=>e.notes.length===1));
 const before=await(await fetch(url+'/api/export')).json();
 await close();
 await launch(19362);
 const after=await(await fetch(url+'/api/export')).json();
 check('restart_restores_samples_events_and_notes_exactly',JSON.stringify(before.samples)===JSON.stringify(after.samples)&&JSON.stringify(before.events)===JSON.stringify(after.events));
 check('restart_preserves_control_requests',JSON.stringify(before.state.commands)===JSON.stringify(after.state.commands));
 check('restart_history_is_read_only_not_live_measurement',after.state.active===false&&await evaluate('platform.getState().backend&&platform.samples().length===450&&document.getElementById("advance").disabled'));
 await evaluate("platform.mutate('/api/replay/start',{scene:'normal',sigma:3})");await evaluate("platform.mutate('/api/replay/step',{n:10})");
 check('restart_allows_new_distinct_session',await evaluate('platform.getState().server.run.session===2&&platform.samples().length===10'));
 await evaluate("platform.navigate('history');document.getElementById('history-session').value='1';document.getElementById('history-session').dispatchEvent(new Event('change'))");
 await waitUntil(()=>evaluate('platform.getState().historyArchive?.samples.length===450'),'Historical selection failed');
 check('history_selection_keeps_new_session_unchanged',await evaluate('platform.getState().server.run.session===2&&platform.samples().length===10'));
 await screenshot('desktop-restart-history');
 await close();
 check('no_WebView_console_errors',report.console_errors.length===0);
 report.passed=report.checks.length;report.result='passed';
}catch(e){report.result='failed';report.error=String(e.stack||e);if(app?.exitCode===null){try{await helper('close');await delay(2000);}catch{}if(app.exitCode===null)app.kill();}ws?.close();process.exitCode=1;}
await fs.writeFile(path.join(out,'acceptance.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({result:report.result,passed:report.passed,error:report.error,screenshots:report.screenshots}));
