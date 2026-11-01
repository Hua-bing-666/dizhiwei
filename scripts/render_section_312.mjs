// Render and inspect only the new section 3.1.2 composition figure.
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
function withPrintDensity(png,printWidthMm){
 const pixelsPerMetre=Math.round(png.readUInt32BE(16)*1000/printWidthMm);
 const payload=Buffer.alloc(13);payload.write('pHYs');payload.writeUInt32BE(pixelsPerMetre,4);payload.writeUInt32BE(pixelsPerMetre,8);payload[12]=1;
 let crc=0xffffffff;for(const byte of payload){crc^=byte;for(let k=0;k<8;k++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}
 const chunk=Buffer.alloc(21);chunk.writeUInt32BE(9,0);payload.copy(chunk,4);chunk.writeUInt32BE((crc^0xffffffff)>>>0,17);
 const chunks=[png.subarray(0,8)];let at=8;
 while(at<png.length){const len=png.readUInt32BE(at),type=png.toString('ascii',at+4,at+8);if(type!=='pHYs')chunks.push(png.subarray(at,at+12+len));if(type==='IHDR')chunks.push(chunk);at+=12+len;}
 return Buffer.concat(chunks);
}
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=process.argv[2]?path.resolve(process.argv[2]):path.join(root,'deliverables/系统组成与研究边界_框图_20261026.svg');
const output=source.replace(/\.svg$/,'.png');
const scratch=path.join(root,'tmp',path.basename(source,'.svg'));
await fs.mkdir(scratch,{recursive:true});
const profile=path.join(scratch,'edge-'+crypto.randomUUID());
const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{windowsHide:true,stdio:'ignore'});
let browser;
try{
 for(let i=0;i<100;i++){
  try{const port=(await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);break;}
  catch{await new Promise(r=>setTimeout(r,100));}
 }
 if(!browser)throw Error('Owned Edge did not start');
 const svgSource=await fs.readFile(source,'utf8');
 const [canvasWidth,canvasHeight]=svgSource.match(/viewBox="0 0 (\d+) (\d+)"/).slice(1).map(Number);
 const context=await browser.newContext({viewport:{width:canvasWidth,height:canvasHeight},deviceScaleFactor:2});
 const page=await context.newPage();await page.goto(pathToFileURL(source).href);
 await page.evaluate(({w,h})=>{const s=document.querySelector('svg');s.style.width=w+'px';s.style.height=h+'px';},{w:canvasWidth,h:canvasHeight});
 await page.evaluate(()=>document.fonts.ready);
 const checked=await page.evaluate(()=>{
  const errors=[],svg=document.querySelector('svg'),v=svg.viewBox.baseVal;
  const printWidthMm=Number(svg.dataset.printWidthMm)||410/72*25.4;
  const printWidthPt=printWidthMm/25.4*72;
 const texts=[...svg.querySelectorAll('text, path[data-source-text]')].map(el=>({el,text:el.dataset.sourceText||el.textContent,box:el.getBBox()}));
  const boxes=[...svg.querySelectorAll('[data-box]')].map(el=>({el,id:el.id,x:+el.dataset.x,y:+el.dataset.y,w:+el.dataset.w,h:+el.dataset.h}));
  const intersects=(a,b)=>Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>.5&&Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>.5;
  for(const t of texts){
   const b=t.box;if(b.x<16||b.y<16||b.x+b.width>v.width-16||b.y+b.height>v.height-16)errors.push('canvas '+t.text);
   const pt=parseFloat(getComputedStyle(t.el).fontSize)*printWidthPt/v.width;if(pt<9.5)errors.push('print font '+t.text);
   for(const box of boxes){
    if(box.el.contains(t.el)){if(b.x<box.x+16||b.x+b.width>box.x+box.w-16||b.y<box.y+16||b.y+b.height>box.y+box.h-16)errors.push('padding '+box.id+': '+t.text);}
    else if(intersects(b,{x:box.x,y:box.y,width:box.w,height:box.h}))errors.push('unrelated box '+t.text+' / '+box.id);
   }
  }
  for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++)if(intersects(texts[i].box,texts[j].box))errors.push('text overlap '+texts[i].text+' / '+texts[j].text);
  for(const link of svg.querySelectorAll('path[data-from]')){
   if(/[CLQSAclqsa]/.test(link.getAttribute('d'))){
    const from=boxes.find(b=>b.id===link.dataset.from),to=boxes.find(b=>b.id===link.dataset.to),length=link.getTotalLength();
    const onEdge=(p,b)=>p.x>=b.x-.3&&p.x<=b.x+b.w+.3&&p.y>=b.y-.3&&p.y<=b.y+b.h+.3&&[Math.abs(p.x-b.x),Math.abs(p.x-b.x-b.w),Math.abs(p.y-b.y),Math.abs(p.y-b.y-b.h)].some(n=>n<.3);
    if(!onEdge(link.getPointAtLength(0),from)||!onEdge(link.getPointAtLength(length),to))errors.push('curve endpoints '+link.dataset.from+' / '+link.dataset.to);
    for(let s=0;s<=length;s+=1.5){
     const p=link.getPointAtLength(s);
     for(const t of texts){const b=t.box;if(p.x>b.x-3&&p.x<b.x+b.width+3&&p.y>b.y-3&&p.y<b.y+b.height+3)errors.push('curve crosses text '+t.text);}
     for(const b of boxes)if(p.x>b.x+.5&&p.x<b.x+b.w-.5&&p.y>b.y+.5&&p.y<b.y+b.h-.5)errors.push('curve crosses box '+b.id);
    }
    continue;
   }
   const pts=[...link.getAttribute('d').matchAll(/([MHV])([\d., ]+)/g)];let at=null;const vertices=[];
   for(const p of pts){const n=p[2].trim().split(/[, ]+/).map(Number);at=p[1]==='M'?{x:n[0],y:n[1]}:p[1]==='H'?{x:n[0],y:at.y}:{x:at.x,y:n[0]};vertices.push({...at});}
   const onEdge=(p,b)=>p.x>=b.x-.1&&p.x<=b.x+b.w+.1&&p.y>=b.y-.1&&p.y<=b.y+b.h+.1&&[Math.abs(p.x-b.x),Math.abs(p.x-b.x-b.w),Math.abs(p.y-b.y),Math.abs(p.y-b.y-b.h)].some(n=>n<.1);
   const from=boxes.find(b=>b.id===link.dataset.from),to=boxes.find(b=>b.id===link.dataset.to);
   if(!onEdge(vertices[0],from)||!onEdge(vertices.at(-1),to))errors.push('connection endpoints '+link.dataset.from+' / '+link.dataset.to);
   for(let i=1;i<vertices.length;i++){
    const a=vertices[i-1],b=vertices[i];
    for(const t of texts){
     const r=t.box,margin=3;
     if(a.x===b.x&&a.x>r.x-margin&&a.x<r.x+r.width+margin&&Math.min(a.y,b.y)<r.y+r.height+margin&&Math.max(a.y,b.y)>r.y-margin)errors.push('line crosses text '+t.text);
     if(a.y===b.y&&a.y>r.y-margin&&a.y<r.y+r.height+margin&&Math.min(a.x,b.x)<r.x+r.width+margin&&Math.max(a.x,b.x)>r.x-margin)errors.push('line crosses text '+t.text);
    }
    for(const box of boxes){
     const x0=box.x+.2,x1=box.x+box.w-.2,y0=box.y+.2,y1=box.y+box.h-.2;
     if(a.x===b.x&&a.x>x0&&a.x<x1&&Math.min(a.y,b.y)<y1&&Math.max(a.y,b.y)>y0)errors.push('line crosses box '+box.id);
     if(a.y===b.y&&a.y>y0&&a.y<y1&&Math.min(a.x,b.x)<x1&&Math.max(a.x,b.x)>x0)errors.push('line crosses box '+box.id);
    }
   }
  }
  return {errors,boxes:boxes.length,texts:texts.length,links:svg.querySelectorAll('path[data-from]').length,print_width_mm:printWidthMm,print_height_mm:printWidthMm*v.height/v.width,min_print_pt:Math.min(...texts.map(t=>parseFloat(getComputedStyle(t.el).fontSize)*printWidthPt/v.width))};
 });
 if(checked.errors.length)throw Error(checked.errors.join('\n'));
 await page.locator('svg').screenshot({path:output});
 const specifiedPrintWidth=Number(svgSource.match(/data-print-width-mm="([\d.]+)"/)?.[1]);
 if(specifiedPrintWidth){
  await fs.writeFile(output,withPrintDensity(await fs.readFile(output),specifiedPrintWidth));
  const preview=path.join(scratch,'a4_preview.html');
  await fs.writeFile(preview,`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>
  *{box-sizing:border-box}html,body{margin:0;background:#fff}.sheet{width:210mm;height:297mm;padding:25mm;font-family:SimSun,serif;font-size:10.5pt;line-height:1.5;color:#111}
  .cell{width:160mm;border:.5pt solid #222;padding:2mm 2mm 3mm}h1{font:700 10.5pt SimSun,serif;margin:0 0 2mm}p{margin:0 0 2mm;text-indent:2em;text-align:justify}figure{margin:2mm 0 0;text-align:center}img{display:block;width:${specifiedPrintWidth}mm;height:auto;margin:0 auto}figcaption{font:10.5pt SimSun,serif;margin-top:2mm;line-height:1.3}
  </style><body><main class="sheet"><section class="cell"><h1>3.3 技术路线</h1><p>本项目围绕支管异常与正常灌溉扰动的区分，开展水力建模、判据构建和采集策略研究，通过独立台架试验评价方法的适用条件。技术路线如图所示。</p><figure><img src="${pathToFileURL(output).href}"><figcaption>项目技术路线图</figcaption></figure></section></main></body></html>`);
  const previewPage=await context.newPage();await previewPage.setViewportSize({width:794,height:1123});await previewPage.goto(pathToFileURL(preview).href);await previewPage.evaluate(()=>document.fonts.ready);await previewPage.locator('img').evaluate(el=>el.decode());
  const fit=await previewPage.evaluate(()=>{const sheet=document.querySelector('.sheet').getBoundingClientRect(),cell=document.querySelector('.cell').getBoundingClientRect(),img=document.querySelector('img').getBoundingClientRect();return{fits:cell.bottom<=sheet.bottom-25/25.4*96+1,image_css_width:img.width,image_css_height:img.height};});
  if(!fit.fits)throw Error('A4 preview does not fit within planned bottom margin');
  await previewPage.screenshot({path:path.join(scratch,'a4_preview.png')});await previewPage.close();
  checked.a4_simulation=fit;
 }
 const receipt={source:path.relative(root,source),output:path.relative(root,output),sha256:crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex'),...checked,classification:'proposed_technical_figure_not_completed_physical_validation',manual_visual_review:'pending'};
 await fs.writeFile(path.join(scratch,'layout_check.json'),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify(receipt));
}finally{if(browser)await browser.close();child.kill();}
