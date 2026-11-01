"""Read manufacturer pages to identify product illustration assets."""
import requests,re,json
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'tmp/hardware_research';out.mkdir(parents=True,exist_ok=True)
sources=[('lora','https://www.ebyte.com/product/1077.html'),('pressure','https://www.microsensor.cn/products-193'),('flow','https://www.dfrobot.com.cn/goods-3561.html'),('mcu','https://www.lcdwiki.com/zh/STM32F103C8T6_Minimum_System_Development_Board')]
records=[]
for name,url in sources:
    try:
        response=requests.get(url,timeout=30);response.raise_for_status();response.encoding=response.apparent_encoding
        html=response.text;(out/(name+'.html')).write_text(html,encoding='utf-8')
        candidates=[urljoin(url,u) for u in re.findall(r'<img[^>]+(?:src|data-src)=[\"\']([^\"\']+)',html,flags=re.I)]
        candidates=list(dict.fromkeys(candidates))
        records.append({'name':name,'url':url,'status':response.status_code,'images':candidates})
        print(name,':',candidates[:20])
    except Exception as e:print(name,type(e).__name__,str(e)[:120])
(out/'asset_candidates.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
