"""Compose editable labels over the actual, hash-matched OCCT WebGL render."""
from pathlib import Path
import base64,json,hashlib,io
from PIL import Image,ImageChops
from build_application_design_figures import Drawing,ROOT,records


def render_plate():
    record=json.loads((ROOT/'application/models/bench_views.json').read_text(encoding='utf-8'))
    raw=ROOT/'application/figures/bench_isometric.png'
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==record['imageSha256'][raw.name]
    assert hashlib.sha256((ROOT/'application/models/bench_scene.json').read_bytes()).hexdigest()==record['sceneSha256']
    im=Image.open(raw).convert('RGB')
    # Tighten only blank exterior, with enough margin for structural outlines.
    diff=ImageChops.difference(im,Image.new('RGB',im.size,'white')).convert('L')
    mask=diff.point(lambda x:255 if x>13 else 0)
    left,top,right,bottom=mask.getbbox()
    left=max(0,left-24);top=max(0,top-24);right=min(im.width,right+24);bottom=min(im.height,bottom+24)
    crop=im.crop((left,top,right,bottom));buffer=io.BytesIO();crop.save(buffer,format='PNG')
    image_width=920; image_height=image_width*crop.height/crop.width
    start_x,start_y=40,90
    legend_y=start_y+image_height+37
    height=int(legend_y+145)
    d=Drawing('bench_model',height)
    d.text(25,34,'双支路清水台架 参数化装配布局',27,True,anchor='start')
    d.items.append(f'<image x="{start_x}" y="{start_y}" width="{image_width}" height="{image_height:.2f}" href="data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"/>')
    for i,name in enumerate(['P0','R','P1','Q','A','B','leak','node']):
        x,y,_=record['projectedAnchors']['iso'][name]
        px=start_x+(x*2-left)*image_width/crop.width
        py=start_y+(y*2-top)*image_width/crop.width
        dx,dy={0:(-17,-29),1:(-8,-31),2:(-10,-29),3:(-5,-30),4:(26,-27),5:(-23,-27),6:(-50,20),7:(-65,22)}[i]
        cx,cy=px+dx,py+dy
        length=(dx*dx+dy*dy)**.5
        d.path([(px,py),(cx-dx/length*17,cy-dy/length*17)],arrow=False,color='#47606c')
        d.items.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="17" fill="white" stroke="#47606c" stroke-width="1.7"/>')
        d.text(cx,cy+8,str(i+1),23,True)
    names=['P0侧向取压','受限元件','P1侧向取压','Q测量A总流量','A等效正常负载','B健康负载切换','独立泄漏计量','采集与LoRa节点']
    for i,label in enumerate(names):
        x=25+(i%4)*245;y=legend_y+(i//4)*35
        d.text(x,y,f'{i+1}  {label}',23,anchor='start')
    d.text(25,legend_y+77,'底板900×520mm，管中心高140mm；器件包络、接头及安装尺寸暂定。',23,anchor='start')
    d.text(25,legend_y+110,'依据同一实体模型渲染；尚未制造、标定或完成装配验证。',23,anchor='start')
    d.render()
    provenance=ROOT/'application/figures/design_provenance.json'
    if provenance.exists():
        current=json.loads(provenance.read_text(encoding='utf-8'))
        current['figures']=[records[-1] if f['name']=='bench_model' else f for f in current['figures']]
        provenance.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    output=ROOT/'application/figures/bench_plate_provenance.json'
    output.write_text(json.dumps({'source_scene_sha256':record['sceneSha256'],'source_render_sha256':record['imageSha256'][raw.name],
                                 'source_render':raw.relative_to(ROOT).as_posix(),'model':'application/models/bench_layout.step',
                                 'figure_height':height,'minimum_text_pt_at_425pt_width':9.78,
                                 'classification':'actual_render_of_unmanufactured_concept_model'},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    return height


if __name__=='__main__':render_plate()
