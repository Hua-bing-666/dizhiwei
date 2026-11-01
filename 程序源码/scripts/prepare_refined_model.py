"""Annotate actual projected CAD anchors, then add a compact nine-item legend."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json
R=Path(__file__).resolve().parents[1];T=R/'tmp/usability_submission'
im=Image.open(T/'model_raw.png').convert('RGB');im=ImageOps.grayscale(im).convert('RGB')
scale=im.width/1200;bottom=135
out=Image.new('RGB',(im.width,im.height+round(bottom*scale)),'white');out.paste(im,(0,0));d=ImageDraw.Draw(out)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',round(25*scale));small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',round(23*scale))
keys=['P0','R','P1','Q','A','B','leak','node','guard'];labels=['P0 上游取压','受限元件 R','P1 下游取压','A 支路流量 Q','A 正常负载','B 负载切换','独立泄漏计量','采集与 LoRa','防溅板']
anchors=json.loads((T/'model_anchors.json').read_text());offsets=[(-25,-48),(0,-48),(0,-48),(0,-48),(30,-30),(-25,-35),(35,30),(-20,35),(-45,10)];records=[]
for i,k in enumerate(keys):
 x,y,z=anchors[k];dx,dy=offsets[i];radius=18*scale
 choices=[]
 for oy in [0,40,-40,80,-80]:
  for ox in [0,40,-40,80,-80]:
   cx=max(28,min(1172,x+dx+ox))*scale;cy=max(28,min(622,y+dy+oy))*scale
   if all((cx-old['cx'])**2+(cy-old['cy'])**2>(radius*2+8*scale)**2 for old in records):choices.append((cx,cy))
 assert choices,('no clear label position',k);cx,cy=choices[0]
 d.line([(x*scale,y*scale),(cx,cy)],fill='#666',width=round(1.3*scale));d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill='white',outline='#555',width=round(1.2*scale))
 d.text((cx,cy),str(i+1),font=font,fill='black',anchor='mm');records.append({'key':k,'number':i+1,'anchor':anchors[k],'cx':cx,'cy':cy})
for i,label in enumerate(labels):d.text(((35+i%3*390)*scale,im.height+(22+i//3*34)*scale),f'{i+1}  {label}',font=small,fill='#111')
out.save(R/'application/figures/usability_revision/model.png')
(T/'model_annotation_checks.json').write_text(json.dumps({'labels':records,'classification':'actual_207_component_mesh_projection_not_physical'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Actual model with nine projected, nonoverlapping print labels.')
