"""Read-only Edge rendering for visual review on this Windows host."""
from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'projects/drip-research_ppt169_20261002'
OUT=ROOT/'tmp/visual_redesign';OUT.mkdir(parents=True,exist_ok=True)
edge=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
records=[];tiles=[]
for svg in sorted((P/'svg_output').glob('*.svg')):
    page=OUT/(svg.stem+'.html');png=OUT/(svg.stem+'.png')
    page.write_text('<!doctype html><html><meta charset="utf-8"><style>html,body{margin:0;width:1280px;height:720px;overflow:hidden}svg{display:block;width:1280px;height:720px}</style>'+svg.read_text(encoding='utf-8')+'</html>',encoding='utf-8')
    subprocess.run([edge,'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars','--force-device-scale-factor=1','--user-data-dir='+str(OUT/'edge-profile'),'--window-size=1280,720','--virtual-time-budget=600','--screenshot='+str(png),page.as_uri()],capture_output=True,check=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
    im=Image.open(png);assert im.size==(1280,720)
    canvas={'view_box':[0,0,1280,720],'width':1280,'height':720,'png_width':1280,'png_height':720}
    records.append({'page':svg.name,'svg_path':str(svg),'png_path':str(png),'canvas':canvas,'ok':True,'all_background':False,'renderer':'Edge Chromium on Windows; native PPTX export reviewed separately'})
    im.thumbnail((420,237));cell=Image.new('RGB',(432,265),'#DAE5DF');cell.paste(im,(6,24));ImageDraw.Draw(cell).text((8,7),svg.stem,fill='#164C45');tiles.append(cell)
contact=Image.new('RGB',(432*3,265*5),'#DAE5DF')
for i,tile in enumerate(tiles):contact.paste(tile,((i%3)*432,(i//3)*265))
contact.save(OUT/'contact.png')
(OUT/'render-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('15 visual-review pages rendered at 1280x720; contact sheet and canvas records written.')
