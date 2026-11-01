import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright'),root=process.cwd(),out=path.join(root,'application/figures/usability_revision');
const profile=path.join(root,'tmp/usability_submission/diagram-edge-'+Date.now());
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let browser;
try{
 for(let i=0;i<100;i++){try{const port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);break;}catch{await new Promise(r=>setTimeout(r,100));}}
 if(!browser)throw Error('Edge unavailable');
 const context=await browser.newContext({viewport:{width:1200,height:700},deviceScaleFactor:3}),page=await context.newPage(),checks=[];
 for(const name of ['system','water','acquisition','sampling','diagnosis','protocol']){
  await page.goto(pathToFileURL(path.join(out,name+'.svg')).href);await page.evaluate(()=>document.fonts.ready);
  const errors=await page.evaluate(()=>{
   const errors=[],svg=document.querySelector('svg'),v=svg.viewBox.baseVal;
   for(const t of document.querySelectorAll('text')){const b=t.getBBox();if(b.x<12||b.y<8||b.x+b.width>v.width-12||b.y+b.height>v.height-8)errors.push('canvas: '+t.textContent);}
   for(const g of document.querySelectorAll('[data-box]')){const x=+g.dataset.x,y=+g.dataset.y,w=+g.dataset.w,h=+g.dataset.h;for(const t of g.querySelectorAll('text')){const b=t.getBBox();if(b.x<x+8||b.x+b.width>x+w-8||b.y<y+8||b.y+b.height>y+h-8)errors.push('box: '+t.textContent);}}
   return errors;
  });
  if(errors.length)throw Error(name+': '+errors.join('; '));
  await page.locator('svg').screenshot({path:path.join(out,name+'.png')});checks.push({name,result:'passed'});
 }
 await fs.writeFile(path.join(out,'layout_checks.json'),JSON.stringify({checks,classification:'diagram_geometry_not_hardware_validation'},null,2));console.log('Six diagram layouts passed; rendered at 3×.');
}finally{if(browser)await browser.close();child.kill();}
