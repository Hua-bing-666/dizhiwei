import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const require=createRequire('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json');
const {chromium}=require('playwright');
const dir=path.resolve('deliverables/块CUSUM诊断流程_横版大字清晰版_20261027');
const meta=JSON.parse(await fs.readFile(path.join(dir,'绘图信息.json'),'utf8'));
const {width,height}=meta;
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
try{
 const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:4});
 await page.goto(pathToFileURL(path.join(dir,'块CUSUM诊断流程_大字清晰版.svg')).href);
 await page.evaluate(()=>document.fonts.ready);
 const errors=await page.evaluate(()=>{
   const errors=[];
   for(const g of document.querySelectorAll('g[data-node]')){
     const x=+g.dataset.x,y=+g.dataset.y,w=+g.dataset.w,h=+g.dataset.h;
     const bbs=[...g.querySelectorAll('text')].map(t=>({name:t.textContent,...Object.fromEntries(['x','y','width','height'].map(k=>[k,t.getBBox()[k]]))}));
     for(const eq of g.querySelectorAll('svg[data-equation]'))bbs.push({name:eq.dataset.equation,x:+eq.getAttribute('x'),y:+eq.getAttribute('y'),width:+eq.getAttribute('width'),height:+eq.getAttribute('height')});
     for(const b of bbs){
       if(g.dataset.kind==='diamond'){
         for(const px of [b.x,b.x+b.width])for(const py of [b.y,b.y+b.height])if(Math.abs(px-x-w/2)/(w/2)+Math.abs(py-y-h/2)/(h/2)>.98)errors.push('diamond '+g.dataset.node+': '+b.name);
       }else if(b.x<x+10||b.x+b.width>x+w-10||b.y<y+5||b.y+b.height>y+h-5)errors.push('box '+g.dataset.node+': '+b.name);
     }
     for(let i=0;i<bbs.length;i++)for(let j=i+1;j<bbs.length;j++){
       const a=bbs[i],b=bbs[j];if(Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>1&&Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>1)errors.push('overlap '+g.dataset.node+': '+a.name+' / '+b.name);
     }
   }
   return errors;
 });
 if(errors.length)throw Error(errors.join('\n'));
 await page.locator('svg').first().screenshot({path:path.join(dir,'块CUSUM诊断流程_9760高清.png')});
 await page.screenshot({path:path.join(dir,'公式局部_高清.png'),clip:{x:800,y:440,width:1600,height:360}});
 await fs.writeFile(path.join(dir,'清晰度与版式检查.json'),JSON.stringify({status:'passed',png:{width:width*4,height:height*4},textSizes:'中文28–38；主要公式40–52',checks:['矩形和菱形内文字与公式不溢出','同节点文字与公式不重叠','公式由源矢量重新渲染'],note:'保留仿真门限h=26及原有公式含义'},null,2));
 console.log(`Rendered ${width*4}×${height*4} PNG from vector; containment and overlap checks passed.`);
}finally{await browser.close();}
