import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright'),root=process.cwd(),out=path.join(root,'tmp/desktop_ui_v13');
await fs.mkdir(out,{recursive:true});const profile=path.join(out,'edge-'+Date.now());
const edge=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let browser;
const report={version:'1.3.0',classification:'UI_and_model_software_checks_not_physical',checks:[],screenshots:[],console_errors:[]};
function check(name,ok){if(!ok)throw Error(name);report.checks.push(name);console.log('PASS '+name);}
try{
 for(let i=0;i<100;i++){try{const port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);break;}catch{await delay(100);}}
 if(!browser)throw Error('Browser unavailable');
 const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1});const page=await context.newPage();
 page.on('pageerror',e=>report.console_errors.push(String(e)));
 await page.goto(pathToFileURL(path.join(root,'deliverables/index.html')).href);await page.waitForFunction(()=>window.platformReady);
 const evaluate=fn=>page.evaluate(fn),screen=async name=>{await delay(180);await page.screenshot({path:path.join(out,name+'.png')});report.screenshots.push(name+'.png');};
 for(const width of [375,1024,1440]){
  await page.setViewportSize({width,height:1000});
  for(const name of ['overview','monitor','events','devices','history','experiments','bench','settings']){
   await page.evaluate(p=>platform.navigate(p),name);
   check('page_'+name+'_'+width+'_fits',await evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   if(width===1440)await screen(name+'-light');
  }
 }
 await page.evaluate(()=>platform.navigate('monitor'));
 check('monitor_default_view_is_operations_not_protocol_report',await evaluate(()=>!document.querySelector('.feature-details').open&&!document.body.innerText.includes('事务保存后 ACK')&&!document.body.innerText.includes('C 核心输出是判定依据')));
 check('chart_units_pressure_and_flow_separate',await evaluate(()=>platform.chartSummary('pressure-chart').series.length===2&&platform.chartSummary('flow-chart').series.length===1));
 check('chart_uses_same_current_C_snapshots',await evaluate(()=>{const s=platform.samples().slice(-181);return platform.chartSummary('pressure-chart').series[0].data.every(([t,v],i)=>t===s[i].t_s&&v===(s[i].status===3?null:s[i].p0));}));
 check('candidate_markers_come_from_current_events',await evaluate(()=>{const markers=platform.chartSummary('pressure-chart').markers;return markers.length>0&&markers.every(m=>platform.events().some(e=>e.code>=4&&e.snapshot.t_s===m.xAxis));}));
 await page.locator('[data-chart-range="0"]').click();
 check('all_range_preserves_original_sample_count',await evaluate(()=>platform.chartSummary('pressure-chart').series[0].data.length===platform.samples().length));
 await page.evaluate(()=>echarts.getInstanceByDom(document.getElementById('pressure-chart')).dispatchAction({type:'showTip',seriesIndex:0,dataIndex:100}));
 await delay(100);check('interactive_tooltip_shows_sample_time',await page.locator('#pressure-chart').innerText().then(t=>t.includes('回放 100 s')));
 await page.evaluate(()=>platform.setReplay({scene:'missing',cursor:362}));
 check('missing_pressure_stays_null_and_disconnects',await evaluate(()=>{const c=platform.chartSummary('pressure-chart');return c.series.every(s=>s.connectNulls===false)&&c.series[1].data.some(([t,v])=>t===362&&v===null)&&platform.current().p1===null;}));
 await page.evaluate(()=>platform.setReplay({scene:'leak',cursor:450}));
 await page.locator('#theme-toggle').click();await screen('monitor-dark');
 check('dark_theme_has_readable_foreground',await evaluate(()=>document.documentElement.dataset.theme==='dark'&&getComputedStyle(document.body).color==='rgb(227, 237, 248)'));
 await page.evaluate(()=>platform.navigate('settings'));check('settings_agree_with_theme',await page.locator('#appearance-theme').inputValue().then(v=>v==='dark'));
 check('technical_settings_available_without_default_clutter',await evaluate(()=>document.querySelector('[data-owner="configuration"] details').open===false&&document.body.innerText.includes('版本与数据')&&!document.body.innerText.includes('C 源文件摘要')));
 await page.locator('#appearance-theme').selectOption('light');
 await page.evaluate(()=>platform.setReplay({cursor:150}));await page.locator('#replay-panel').evaluate(el=>el.open=true);
 await page.locator('#playback-toggle').click();await delay(650);await page.locator('#playback-toggle').click();
 const cursor=await evaluate(()=>platform.current().t_s);await delay(650);
 check('automatic_replay_moves_then_pause_holds_cursor',cursor>150&&await evaluate(()=>!platform.getState().playing)&&await evaluate(()=>platform.current().t_s)===cursor);
 await page.evaluate(()=>platform.setReplay({cursor:899}));await page.locator('#playback-toggle').click();await delay(1200);
 check('replay_end_stops_automatically',await evaluate(()=>!platform.getState().playing&&platform.current().t_s===platform.samples().at(-1).t_s));
 await page.evaluate(()=>platform.setReplay({scene:'leak',cursor:450}));
 await page.evaluate(()=>platform.navigate('bench'));await page.locator('#model-load').click();
 await page.waitForFunction(()=>document.querySelector('#bench-frame')?.dataset.loaded==='true');
 const model=page.frames().find(f=>decodeURI(f.url()).includes('清水试验台架'));
 await model.waitForFunction(()=>window.benchToolsReady&&window.benchReadings?.t_s===450);
 const snapshot=await evaluate(()=>platform.current()),reading=await model.evaluate(()=>window.benchReadings);
 check('model_shares_current_snapshot_and_labels_synthetic',reading.p0===snapshot.p0&&reading.p1===snapshot.p1&&reading.q===snapshot.q&&reading.physical_data===false&&await model.locator('.stage-tag').innerText().then(t=>t.includes('合成回放')));
 check('model_has_207_unchanged_components',await model.evaluate(()=>modelData.meshes.length===207));
 await screen('bench-model');
 for(const name of ['P0_sensor_envelope','P1_sensor_envelope','Q_meter_envelope']){
  await page.locator('[data-bench-point="'+name+'"]').click();await delay(200);
  check('model_focus_'+name,await model.evaluate(n=>benchInspection.getState().part===n,name));
  check('model_focus_labels_fit_'+name,await model.evaluate(()=>{const stage=document.getElementById('stage'),boxes=[...document.querySelectorAll('#overlay rect')].map(r=>({x:+r.getAttribute('x'),y:+r.getAttribute('y'),w:+r.getAttribute('width'),h:+r.getAttribute('height')}));return boxes.every(b=>b.x>=0&&b.y>=0&&b.x+b.w<=stage.clientWidth&&b.y+b.h<=stage.clientHeight)&&boxes.every((a,i)=>boxes.slice(i+1).every(b=>!(a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y)));}));
  const namePNG='model-focus-'+name+'.png';await page.locator('#bench-frame').screenshot({path:path.join(out,namePNG)});report.screenshots.push(namePNG);
 }
 await screen('bench-focus-Q');
 await page.evaluate(()=>platform.setReplay({scene:'missing',cursor:362}));await delay(100);
 check('model_missing_pressure_is_not_previous_value',await model.evaluate(()=>benchReadings.t_s===362&&benchReadings.p0===null&&benchReadings.p1===null));
 check('model_technical_notes_collapsed_but_controls_available',await model.evaluate(()=>!document.querySelector('.model-help').open&&document.getElementById('zoom-in').checkVisibility()));
 await page.evaluate(()=>platform.navigate('monitor'));await page.locator('[data-chart-range="600"]').click();
 await page.reload();await page.waitForFunction(()=>window.platformReady);
 check('web_preferences_restore_range_and_theme',await evaluate(()=>platform.getState().chartRange===600&&platform.getState().theme==='light'));
 check('no_browser_console_exceptions',report.console_errors.length===0);
}catch(e){report.error=String(e.stack||e);report.result='failed';process.exitCode=1;}
finally{await browser?.close();edge.kill();}
if(!report.error){report.result='passed';report.passed=report.checks.length;}
await fs.writeFile(path.join(out,'acceptance.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({result:report.result,passed:report.passed,error:report.error}));
