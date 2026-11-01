import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=process.argv[2]?path.resolve(process.argv[2]):path.join(root,'deliverables/技术路线图_核心与两翼_20261027.svg');
const scratch=process.argv[3]?path.resolve(process.argv[3]):path.join(root,'tmp/word_vector_20261027');
await fs.mkdir(scratch,{recursive:true});
const profile=path.join(scratch,'edge-'+crypto.randomUUID());
const proc=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let browser;
try{
 for(let i=0;i<100;i++){
  try{const port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);break;}
  catch{await new Promise(r=>setTimeout(r,100));}
 }
 if(!browser)throw Error('Headless renderer did not start');
 const page=await browser.newPage({viewport:{width:1800,height:2160}});
 await page.goto(pathToFileURL(source).href);await page.evaluate(()=>document.fonts.ready);
 const data=await page.evaluate(()=>{
  const svg=document.querySelector('svg');let textIndex=0;
  const hex=c=>{if(c==='none')return c;const n=c.match(/[\d.]+/g);return n?'#'+n.slice(0,3).map(x=>(+x).toString(16).padStart(2,'0')).join(''):c;};
  const elements=[...svg.querySelectorAll('rect,path,text,line')].filter(el=>!el.closest('defs')).map((el,index)=>{
   const cs=getComputedStyle(el),b=el.getBBox();
   const value={index,tag:el.tagName,fill:hex(cs.fill),stroke:hex(cs.stroke),strokeWidth:parseFloat(cs.strokeWidth),strokeDash:cs.strokeDasharray,lineJoin:cs.strokeLinejoin,lineCap:cs.strokeLinecap,arrow:cs.markerEnd!=='none',attrs:Object.fromEntries([...el.attributes].map(a=>[a.name,a.value])),bbox:{x:b.x,y:b.y,width:b.width,height:b.height}};
   if(el.tagName==='text')Object.assign(value,{textIndex:textIndex++,text:el.textContent,fontSize:parseFloat(cs.fontSize),fontWeight:parseInt(cs.fontWeight),fontFamily:cs.fontFamily});
   return value;
  });
  return{width:svg.viewBox.baseVal.width,height:svg.viewBox.baseVal.height,printWidthMm:+svg.dataset.printWidthMm,elements};
 });
 await fs.writeFile(path.join(scratch,'vector_elements.json'),JSON.stringify(data,null,2));
 console.log(JSON.stringify({elements:data.elements.length,texts:data.elements.filter(e=>e.tag==='text').length,file:path.join(scratch,'vector_elements.json')}));
}finally{if(browser)await browser.close();proc.kill();}
