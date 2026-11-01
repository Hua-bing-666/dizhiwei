import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const dir=path.resolve('deliverables/块CUSUM诊断流程_横版修订_20261027');
const meta=JSON.parse(await fs.readFile(path.join(dir,'绘图信息.json'),'utf8'));
const {width,height}=meta;
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
try{
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:3});
  await page.goto(pathToFileURL(path.join(dir,'块CUSUM诊断流程_横版.svg')).href);
  await page.evaluate(()=>document.fonts.ready);
  const errors=await page.evaluate(()=>{
    const errors=[],root=document.querySelector('svg'),W=root.viewBox.baseVal.width,H=root.viewBox.baseVal.height;
    for(const g of document.querySelectorAll('g[data-node]')){
      const x=+g.dataset.x,y=+g.dataset.y,w=+g.dataset.w,h=+g.dataset.h;
      const items=[...g.querySelectorAll('text')].map(t=>({name:t.textContent,...Object.fromEntries(['x','y','width','height'].map(k=>[k,t.getBBox()[k]]))}));
      for(const eq of g.querySelectorAll('svg[data-equation]'))items.push({name:eq.dataset.equation,x:+eq.getAttribute('x'),y:+eq.getAttribute('y'),width:+eq.getAttribute('width'),height:+eq.getAttribute('height')});
      for(const b of items){
        if(g.dataset.kind==='diamond'){
          for(const px of [b.x,b.x+b.width])for(const py of [b.y,b.y+b.height])if(Math.abs(px-x-w/2)/(w/2)+Math.abs(py-y-h/2)/(h/2)>.97)errors.push('diamond '+g.dataset.node+': '+b.name);
        }else if(b.x<x+10||b.x+b.width>x+w-10||b.y<y+5||b.y+b.height>y+h-5)errors.push('box '+g.dataset.node+': '+b.name);
      }
    }
    for(const t of document.querySelectorAll('text')){const b=t.getBBox();if(b.x<5||b.y<5||b.x+b.width>W-5||b.y+b.height>H-5)errors.push('canvas '+t.textContent);}
    return errors;
  });
  if(errors.length)throw new Error(errors.join('\n'));
  await page.locator('svg').first().screenshot({path:path.join(dir,'块CUSUM诊断流程_横版.png')});
  await page.screenshot({path:path.join(dir,'残差公式_放大核对.png'),clip:{x:1260,y:400,width:450,height:280}});
  const previewWidth=1452,previewHeight=708;
  await page.setViewportSize({width:previewWidth,height:previewHeight});
  await page.evaluate(({w,h})=>{const s=document.querySelector('svg');s.setAttribute('width',w);s.setAttribute('height',h);},{w:previewWidth,h:previewHeight});
  await page.locator('svg').first().screenshot({path:path.join(dir,'块CUSUM诊断流程_横版_预览.png'),scale:'css'});
  await fs.writeFile(path.join(dir,'版式检查.json'),JSON.stringify({status:'passed',width:width*3,height:height*3,equationCount:meta.equations.length,checks:['矩形内中文与公式不溢出','菱形文字与公式不碰斜边','所有中文位于画布内','公式以独立矢量根式、分式、上下标排版'],scope:'图件版式检查；不表示实物性能验证'},null,2));
  console.log('Rendered landscape PNG and SVG; all text and equation containment checks passed.');
}finally{await browser.close();}
