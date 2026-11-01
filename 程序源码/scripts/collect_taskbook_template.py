"""Collect school taskbook references; preserve raw files and request provenance."""
from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,re,concurrent.futures
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/school_templates';OUT.mkdir(exist_ok=True)
RAW=ROOT/'tmp/school_template_sources';RAW.mkdir(exist_ok=True,parents=True)
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=22) as r:return r.read(),r.headers.get('Content-Type',''),r.geturl()
def fetch_notice(item):
    year,url=item
    try:
        b,ct,final=get(url);s=b.decode('utf-8');(RAW/f'notice_{year}.html').write_bytes(b)
        attachments=[]
        for href,title in re.findall(r'<a[^>]+href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>',s,re.S):
            title=re.sub('<[^>]+>','',title).strip()
            if '任务书' in title:attachments.append({'title':title,'url':urllib.parse.urljoin(url,href)})
        return {'year':year,'url':url,'status':'fetched','content_type':ct,'attachments':attachments,'sha256':hashlib.sha256(b).hexdigest()}
    except Exception as e:return {'year':year,'url':url,'status':'failed','error':str(e)}
def main():
    notices=[(2026,'https://jwc.taru.edu.cn/info/1052/4416.htm'),(2025,'https://jwc.taru.edu.cn/info/1052/3886.htm')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:reports=list(pool.map(fetch_notice,notices))
    for report in reports:
        for a in report.get('attachments',[]):
            try:
                data,ct,final=get(a['url']);a.update(content_type=ct,final_url=final,sha256=hashlib.sha256(data).hexdigest())
                if data.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
                    path=OUT/f"塔里木大学大创任务书原模板_{report['year']}.doc";path.write_bytes(data);a.update(status='downloaded_doc',path=path.relative_to(ROOT).as_posix())
                else:
                    a['status']='not_document';a['response_bytes']=len(data)
                    (RAW/f"attachment_response_{report['year']}.html").write_bytes(data)
            except Exception as e:a.update(status='failed',error=str(e))
    result={'retrieval_date':'2026-10-05','official_sources_only':True,'use':'Historical school template; 2027 batch and awarded project identities remain pending','notices':reports}
    (OUT/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
