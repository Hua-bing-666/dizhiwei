"""Record public manufacturer HTML observations, not checkout prices."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from datetime import datetime,timezone,timedelta
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.active=None;self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.active=[dict(attrs).get('href',''),[]]
    def handle_data(self,data):
        if self.active:self.active[1].append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.active:self.links.append((self.active[0],''.join(self.active[1]).strip()));self.active=None
def main():
    observed_date=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    records=[]
    for url,model in [('https://www.dfrobot.com.cn/goods-3561.html','SEN0549'),('https://www.dfrobot.com.cn/goods-1734.html','DFR0553'),('https://www.ebyte.com/product/1077.html','E220-400T22D')]:
        record={'url':url,'model':model,'date':observed_date,'classification':'manufacturer_public_listing_not_quote'}
        try:
            response=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20);raw=response.read();html=raw.decode('utf-8','replace')
            record.update(http_status=response.status,html_sha256=hashlib.sha256(raw).hexdigest())
            title=re.search(r'<title>(.*?)</title>',html,re.S);record['title']=title.group(1).strip() if title else None
            if model!='E220-400T22D':
                price=re.search(r'id="ECS_SHOPPRICE"[^>]*>\s*￥([\d.]+)',html);assert price,'No listed price'
                record.update(display_price_cny=float(price.group(1)),shipping_tax_checkout_verified=False,stock_verified=False)
            else:
                parser=Links();parser.feed(html)
                record['manual_links']=[{'label':label,'url':urljoin(url,href)} for href,label in parser.links if 'E220-400T22D_UserManual_CN' in label]
                record['supplier_taobao_links']=list(dict.fromkeys(urljoin(url,href) for href,label in parser.links if 'item.taobao.com' in href and any(s in href for s in ['id=622908748357','id=660727383363'])))
                record['display_price_cny']=None;record['stock_verified']=False
        except Exception as exc:record.update(error=type(exc).__name__+': '+str(exc),display_price_cny=None)
        records.append(record)
    result={'date':observed_date,'physical_data':False,'records':records,'limits':'HTML展示价及厂家出口链接；未登录或下单，具体SKU、含税运费、库存、压力传感器报价未确认'}
    (ROOT/'simulation/interface_review/market_observations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    for r in records:print(r['model'],r.get('display_price_cny'),r.get('manual_links',[]),r.get('supplier_taobao_links',[]),r.get('error',''))
if __name__=='__main__':main()
