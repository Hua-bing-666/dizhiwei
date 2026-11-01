import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const dir=path.resolve('deliverables/块CUSUM诊断流程_重绘_20261027');
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
try{
  const page=await browser.newPage({viewport:{width:1160,height:1460},deviceScaleFactor:3});
  await page.goto(pathToFileURL(path.join(dir,'块CUSUM诊断流程.svg')).href);
  await page.evaluate(()=>document.fonts.ready);
  const errors=await page.evaluate(()=>{
    const errors=[];
    for(const t of document.querySelectorAll('text')){
      const b=t.getBBox();
      if(b.x<8||b.y<8||b.x+b.width>1152||b.y+b.height>1452)errors.push('canvas: '+t.textContent);
    }
    for(const g of document.querySelectorAll('g[data-node]:not([data-kind])')){
      const {x,y,w,h}=Object.fromEntries(['x','y','w','h'].map(k=>[k,+g.dataset[k]]));
      for(const t of g.querySelectorAll('text')){
        const b=t.getBBox();
        if(b.x<x+10||b.x+b.width>x+w-10||b.y<y+5||b.y+b.height>y+h-5)errors.push('node '+g.dataset.node+': '+t.textContent);
      }
    }
    for(const g of document.querySelectorAll('g[data-kind="diamond"]')){
      const {x,y,w,h}=Object.fromEntries(['x','y','w','h'].map(k=>[k,+g.dataset[k]]));
      for(const t of g.querySelectorAll('text')){
        const b=t.getBBox();
        for(const px of [b.x,b.x+b.width])for(const py of [b.y,b.y+b.height]){
          if(Math.abs(px-x-w/2)/(w/2)+Math.abs(py-y-h/2)/(h/2)>0.96)errors.push('diamond '+g.dataset.node+': '+t.textContent);
        }
      }
    }
    return errors;
  });
  if(errors.length)throw Error(errors.join('\n'));
  await page.locator('svg').screenshot({path:path.join(dir,'块CUSUM诊断流程.png')});
  await page.setViewportSize({width:812,height:1022});
  await page.evaluate(()=>{const s=document.querySelector('svg');s.setAttribute('width','812');s.setAttribute('height','1022');});
  await page.locator('svg').screenshot({path:path.join(dir,'块CUSUM诊断流程_预览.png'),scale:'css'});
  await fs.writeFile(path.join(dir,'版式检查.json'),JSON.stringify({status:'passed',checks:['所有文字位于画布内','矩形节点文字不溢出','菱形判断框文字不碰斜边'],png:{width:3480,height:4380},note:'图件几何检查，不是算法及实物验收'},null,2));
  console.log('Rendered editable SVG and 3480×4380 PNG. Text containment checks passed.');
}finally{await browser.close();}
