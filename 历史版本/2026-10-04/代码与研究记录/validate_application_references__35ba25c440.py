"""Check reference preservation, source metadata and complete native PDF entries."""
from pathlib import Path
import json, re, hashlib
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'application/references.json').read_text(encoding='utf-8'))
refs=data['references']
source=(ROOT/'application/正式模板正文.md').read_text(encoding='utf-8')
review=source.split('## 四、')[1].split('参考文献')[0]
assert len(refs)==17 and len({r['doi'] for r in refs})==17
assert {int(x) for x in re.findall(r'\[(\d+)\]',review)}==set(range(1,18))
assert sum(r['language']=='中文' for r in refs)==11
retained={'10.1016/j.agwat.2022.107873','10.3390/s26103010','10.3390/land15030464','10.3390/s21165541','10.1016/j.ifacol.2025.11.761','10.3390/agronomy15040760'}
assert {r['doi'] for r in refs if r['language']=='英文'}==retained
metadata=json.loads((ROOT/'docs/中文文献来源核验.json').read_text(encoding='utf-8'))
checks=0
for r in refs[:11]:
    record=next(m for m in metadata if m['url']==r['url'])
    if record['status']=='failed':
        assert r['number']==7 and '浏览工具' in r['verification']
        continue
    pairs=record['metadata']
    assert r['title'] in [v for k,v in pairs if k in ('citation_title','dc.title')]
    assert any(r['doi'] in v for k,v in pairs if k in ('citation_doi','dc.identifier'))
    lookup=dict(pairs)
    for key,expected in [('citation_volume',r['volume']),('citation_issue',r['issue']),('citation_year',str(r['year']))]:
        if key in lookup:assert lookup[key]==expected,(r['number'],key)
    if 'citation_firstpage' in lookup:
        assert lookup['citation_firstpage']+'-'+lookup['citation_lastpage']==r['pages']
    if 'citation_authors' in lookup:
        assert r['authors'].split(',')[0] in lookup['citation_authors']
    checks+=1
pdf=pymupdf.open(ROOT/'deliverables/大创申报书_模板审阅版.pdf')
pages=[''.join(p.get_text().split()) for p in pdf]
entry_pages=[]
for r in refs:
    matching=[i+1 for i,t in enumerate(pages) if f"[{r['number']}]" in t and r['doi'] in t and ''.join(r['title'].split()) in t]
    assert len(matching)==1,('missing, split or duplicate PDF citation',r['number'],matching)
    entry_pages.append({'number':r['number'],'page':matching[0]})
template=ROOT/'附件1：塔里木大学大学生创新训练项目申报书.doc'
assert hashlib.sha256(template.read_bytes()).hexdigest()=='91a6fe38b74c804482859fc3a5e5369bac2c781069984a5a7b3baf131bf7d48d'
print('17 body citations; 11 Chinese + 6 retained English; 10 journal-metadata checks + 1 documented browser verification; all PDF entries complete on one page; school template unchanged.')
print(json.dumps(entry_pages,ensure_ascii=False))
