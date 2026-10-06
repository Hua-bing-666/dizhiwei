import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const root=process.cwd(),out=path.join(root,'tmp/current_application_review');await fs.mkdir(out,{recursive:true});
const profile=path.join(out,'edge-profile');
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let browser;
try{
 for(let i=0;i<100;i++){try{const port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);break;}catch{await new Promise(r=>setTimeout(r,100));}}
 if(!browser)throw Error('Edge unavailable');
 const context=await browser.newContext({viewport:{width:1100,height:900},deviceScaleFactor:3});const page=await context.newPage();
 await page.goto(pathToFileURL(path.join(root,'deliverables/index.html')).href);await page.waitForFunction(()=>window.platformReady);
 await page.evaluate(()=>{platform.setReplay({scene:'leak',cursor:450});platform.navigate('monitor');});
 await page.evaluate(()=>{
 const owner=document.querySelector('[data-owner="telemetry"]'),readings=owner.firstElementChild,right=owner.querySelector('.two').lastElementChild;
 const box=document.createElement('section');box.id='publication';
 const source=document.createElement('p');source.textContent='离线 C 合成回放 · 支管 A · 渐进等效泄漏 · 450 s';box.append(source,readings,right);document.body.replaceChildren(box);
 const s=document.createElement('style');s.textContent=`body{margin:0!important;display:block!important;background:white!important;font-family:'Microsoft YaHei',sans-serif!important}#publication{width:760px;padding:16px;background:white;color:#111}#publication .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}#publication .card{margin:0 0 12px;padding:16px;border:1px solid #777;border-radius:5px;box-shadow:none;background:white;color:#111}#publication p,#publication .sub,#publication small,#publication .unit,#publication .line-item,#publication .pill{font-size:17px!important;color:#111!important;line-height:1.55}#publication h2{font-size:21px!important;color:#111!important}#publication h3{font-size:24px!important;color:#111!important}#publication .metric{font-size:32px!important;color:#111!important}#publication .line-item{padding:9px 0}#publication .reveal-ready{opacity:1;transform:none}#publication .status-title{color:#111!important}#publication .line-items{margin-top:12px}`;document.head.append(s);
 });
 await page.locator('#publication').screenshot({path:path.join(out,'platform_publication.png')});
 await page.goto(pathToFileURL(path.join(root,'deliverables/清水试验台架_V1.2.html')).href);await page.waitForFunction(()=>window.benchReady);
 await page.evaluate(()=>{document.body.classList.add('capture');const s=document.createElement('style');s.textContent='body.capture header,body.capture .toolbar,body.capture aside,body.capture .inspection-bar,body.capture .hint,body.capture .stage-tag{display:none!important}body.capture .layout{display:block;margin:0!important}body.capture #stage{width:1100px;height:730px!important;min-height:0!important;border:0;border-radius:0;background:white!important}';document.head.append(s);window.dispatchEvent(new Event('resize'));});
 await page.waitForTimeout(250);
 await page.evaluate(()=>{for(const g of document.querySelectorAll('#overlay g')){const t=g.querySelector('text'),r=g.querySelector('rect');if(!t||!r)continue;t.textContent=t.textContent.trim().split(' ')[0];t.setAttribute('font-size','25');r.setAttribute('width','38');r.setAttribute('height','34');}});
 const anchors=await page.evaluate(()=>Object.fromEntries(['P0','R','P1','Q','A','B','leak','node','guard'].map(k=>[k,bench.project(bench.getData().anchors[k])])));await fs.writeFile(path.join(out,'model_anchors.json'),JSON.stringify(anchors));await page.evaluate(()=>bench.setLabels(false));const labels=await page.locator('#overlay text').evaluateAll(es=>es.map(e=>({text:e.textContent,box:{x:e.getBBox().x,y:e.getBBox().y,w:e.getBBox().width,h:e.getBBox().height}})));
 await page.locator('#stage').screenshot({path:path.join(out,'model_publication_raw.png')});
 await fs.writeFile(path.join(out,'capture.json'),JSON.stringify({source:'actual current browser modules; publication styling only; values unchanged',labels,physical_data:false},null,2));console.log('Captured current platform and model');
}finally{if(browser)await browser.close();child.kill();}

