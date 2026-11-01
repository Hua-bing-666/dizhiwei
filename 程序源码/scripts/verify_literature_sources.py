"""Store public journal metadata for the application bibliography; no full-text copying."""
from pathlib import Path
import concurrent.futures, json
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
URLS = [
    'https://www.aeeisp.com/nygcxb/article/doi/10.11975/j.issn.1002-6819.2019.03.015',
    'https://www.aeeisp.com/nygcxb/article/doi/10.11975/j.issn.1002-6819.202307109',
    'https://www.aeeisp.com/nygcxb/article/doi/10.11975/j.issn.1002-6819.202212095',
    'https://www.aeeisp.com/nygcxb/article/doi/10.11975/j.issn.1002-6819.202208008',
    'https://www.aeeisp.com/zgnjhxb/article/doi/10.13733/j.jcam.issn.2095-5553.2023.09.023',
    'https://www.aeeisp.com/nygcxb/article/doi/10.11975/j.issn.1002-6819.202401146',
    'https://xuebao.scau.edu.cn/zr/html/2021/4/20210414.htm',
    'https://yqcy.pipechina.com.cn/cn/article/id/20150717',
    'https://www.aas.net.cn/cn/article/doi/10.16383/j.aas.2018.c180383',
    'https://journal.cricaas.com.cn/zgmh/CN/10.11963/cc20220080',
    'https://www.syxb-cps.com.cn/CN/10.7623/syxb201602013',
]

def fetch(url):
    try:
        r = requests.get(url, timeout=35)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        meta = [(m.get('name', m.get('property', '')), m.get('content', '')) for m in soup.find_all('meta')]
        selected = [(k,v) for k,v in meta if k.lower().startswith(('citation_', 'dc.')) and not any(w in k.lower() for w in ['description','abstract','keywords','subject','rights'])]
        text = soup.get_text(' ', strip=True)
        path = ROOT/'tmp/literature_sources'
        path.mkdir(parents=True, exist_ok=True)
        slug = url.rsplit('/',1)[1].replace(':','_')
        (path/(slug+'.txt')).write_text(text, encoding='utf-8')
        return {'url':url, 'retrieved':'2026-10-03', 'metadata':selected, 'status':'journal_page_retrieved'}
    except Exception as exc:
        return {'url':url, 'status':'failed', 'error':str(exc)}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records = list(pool.map(fetch, URLS))
    out = ROOT/'docs/中文文献来源核验.json'
    out.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    for record in records:
        print(json.dumps(record, ensure_ascii=False))
