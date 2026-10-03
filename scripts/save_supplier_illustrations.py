"""Retain attributed manufacturer illustrations for a candidate-selection figure."""
from pathlib import Path
from io import BytesIO
import requests,json,hashlib
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures/vendor';OUT.mkdir(exist_ok=True)
items=[
 ('mcu','STM32F103C8T6 最小系统板','LCDWIKI / 候选开发板','https://www.lcdwiki.com/zh/STM32F103C8T6_Minimum_System_Development_Board','https://www.lcdwiki.com/images/thumb/7/72/开发板STM32F103C8T6-40.jpg/400px-开发板STM32F103C8T6-40.jpg'),
 ('pressure','MPM489 系列配图','拟订K200表压规格 / 待询价','https://www.microsensor.cn/products-193','https://www.microsensor.cn/uploads/20251216/b81c68c6f0bf513ae31e06a1a919981e.webp'),
 ('flow','SEN0549 G1/4 流量','DFRobot / 合成试验需匹配量程','https://www.dfrobot.com.cn/goods-3561.html','https://ws.dfrobot.com.cn/FtE4Gxx_cSyORQvAHN3GkdMlgngz?imageView2/1/w/486/h/486')]
font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',29);small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',23)
canvas=Image.new('RGB',(1800,690),'white');draw=ImageDraw.Draw(canvas);record=[]
for i,(key,title,detail,page,url) in enumerate(items):
    response=requests.get(url,timeout=30);response.raise_for_status()
    path=OUT/(key+'.png');source=Image.open(BytesIO(response.content)).convert('RGBA')
    background=Image.new('RGBA',source.size,'white');background.alpha_composite(source);background.convert('RGB').save(path)
    placed=ImageOps.contain(background.convert('RGB'),(520,420))
    canvas.paste(placed,(i*600+40+(520-placed.width)//2,35+(420-placed.height)//2))
    draw.text((i*600+40,475),title,font=font,fill='#164c45');draw.text((i*600+40,525),detail,font=small,fill='#556762')
    record.append({'key':key,'page_url':page,'image_url':url,'local':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'classification':'supplier_product_illustration_not_project_prototype'})
draw.text((40,613),'国内供应商配图用于选型说明；非本项目实物，未采购，配置以询价与标定后冻结。',font=small,fill='#556762')
canvas.save(ROOT/'application/figures/hardware_candidates.png')
(OUT/'provenance.json').write_text(json.dumps({'checked_date':'2026-10-03','entries':record},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Three supplier illustrations saved with URLs and source-state labels.')
