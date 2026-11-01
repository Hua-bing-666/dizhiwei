import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'tmp/formula_review_20261027/算法流程_正文配套.svg');
const s=[`<svg xmlns="http://www.w3.org/2000/svg" width="146mm" height="53.5333mm" viewBox="0 0 1800 660" data-print-width-mm="146"><title>块级异常判断流程</title><desc>公式放在正文中解释，图中只展示处理顺序。质量无效时不作有效判断，工况门控后须复判。</desc><defs><marker id="a" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="#222"/></marker><style>text{font-family:SimSun,serif;font-size:42px;text-anchor:middle;dominant-baseline:central;fill:#111}.link{fill:none;stroke:#222;stroke-width:1.8;marker-end:url(#a)}.strong{font-weight:bold}</style></defs><rect width="1800" height="660" fill="#fff"/>`];
function t(x,y,v,c=''){s.push(`<text x="${x}" y="${y}" class="${c}">${v}</text>`);}
function b(id,x,y,w,h,lines,fill='#fff'){s.push(`<g id="${id}" data-box="${id}" data-x="${x}" data-y="${y}" data-w="${w}" data-h="${h}"><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="#222" stroke-width="1.8"/>`);lines.forEach((v,i)=>t(x+w/2,y+h/2+(i-(lines.length-1)/2)*55,v,i===0?'strong':''));s.push('</g>');}
function l(a,b,d){s.push(`<path class="link" data-from="${a}" data-to="${b}" d="${d}"/>`);}
b('quality',40,260,340,140,['数据有效性检查','量程与时序检查']);
b('block',500,260,340,140,['10 s 数据块','各块分别判断']);
b('residual',960,260,340,140,['参照残差标准化','流量与区段阻力']);
b('cusum',1420,260,340,140,['块级 CUSUM','每块更新一次'],'#f2f2f2');
b('calibration',960,40,340,140,['独立健康标定','参照与波动尺度']);
b('invalid',40,500,340,140,['记录不可用状态','本块不参与判断']);
b('gate',500,500,800,140,['工况切换后挂起与复判','缺测时不输出正常结论']);
b('candidate',1420,500,340,140,['异常候选与记录','上报与人工复测']);
l('quality','block','M380,330 H500');t(440,278,'有效');
l('block','residual','M840,330 H960');
l('residual','cusum','M1300,330 H1420');
l('calibration','residual','M1130,180 V260');
l('quality','invalid','M210,400 V500');t(292,449,'无效');
l('gate','quality','M500,570 H420 V370 H380');
l('cusum','candidate','M1590,400 V500');t(1672,449,'越限');
s.push('</svg>');await fs.writeFile(out,s.join('\n'));console.log(out);
