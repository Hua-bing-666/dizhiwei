"""Refresh the acceptance record after the visually reviewed literature revision."""
from pathlib import Path
import hashlib, json
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
pdf=ROOT/'deliverables/大创申报书_模板审阅版.pdf'
count=pymupdf.open(pdf).page_count
assert count==24
for filename in ['README.md','deliverables/使用说明.md','docs/本轮申报书验收记录.md','docs/申报书黑白流程与模型验收.md']:
    path=ROOT/filename
    text=path.read_text(encoding='utf-8').replace('23页','24页').replace('研究正文18页','研究正文19页')
    text=text.replace('2026年10月3日','2026年10月4日')
    path.write_text(text,encoding='utf-8',newline='\n')
path=ROOT/'README.md'
text=path.read_text(encoding='utf-8')
line='- [参考文献核验与正文对应](docs/参考文献核验与正文对应.md)：17篇期刊论文，中文11篇（64.7%）、英文6篇；原英文全部保留，正文逐项引用。\n'
if line not in text:text=text.replace('## 当前范围',line+'\n## 当前范围')
text=text.replace('4张可编辑表及审批栏','4张可编辑数据表、17条完整参考文献及审批栏')
text=text.replace('网站重建：','参考文献检查：`python scripts/validate_application_references.py`。网站重建：')
path.write_text(text,encoding='utf-8',newline='\n')

path=ROOT/'deliverables/使用说明.md'
text=path.read_text(encoding='utf-8')
extra='参考文献共17篇，中文11篇占64.7%，原有6篇英文全部保留；每篇均在研究现状正文引用。来源、核验范围及不能推出的结论见 `../docs/参考文献核验与正文对应.md`，完整数据见 `../application/references.json`。\n\n'
if extra not in text:text=text.replace('已有证据包括',extra+'已有证据包括')
path.write_text(text,encoding='utf-8',newline='\n')

path=ROOT/'docs/本轮申报书验收记录.md'
text=path.read_text(encoding='utf-8')
extra='文献增补为11篇中文及保留的6篇英文，共17篇，中文占64.7%。核对题名、作者、期刊、年份、卷期、页码或文章号及DOI；中文条目10篇可与期刊元数据自动比对，1篇由浏览工具核对原期刊页面。核验范围逐项记录，未声称全部论文均已逐页阅读全文。正文第四节逐项引用并解释方案取舍，学校制度与产品目录不计入学术论文数量。17条完整参考文献在原生PDF第18—19页，无单条跨页；用无边框原生行保持每条完整，仍可编辑。章节标题页底孤立已经修复。\n\n'
if extra not in text:text=text.replace('## 技术与真实性',extra+'## 技术与真实性')
path.write_text(text,encoding='utf-8',newline='\n')

path=ROOT/'docs/申报书黑白流程与模型验收.md'
text=path.read_text(encoding='utf-8')
extra='补充文献后重新核对第17—24页，第1—16页的渲染图像与先前逐页复核版字节一致。17条参考文献均在正文引用，题名与DOI在同一页完整出现。中文11篇占64.7%，原6篇英文保留；原始入口及解释边界见《参考文献核验与正文对应》。\n\n'
if extra not in text:text=text.replace('封面、行政栏',extra+'封面、行政栏')
path.write_text(text,encoding='utf-8',newline='\n')

path=ROOT/'deliverables/申报书验收记录.json'
record=json.loads(path.read_text(encoding='utf-8'))
record['date']='2026-10-04'
record['visual_review']['application_native_wps_pdf_pages']=count
record['visual_review']['application_reviewed_pages']=list(range(1,count+1))
record['visual_review']['unchanged_previously_reviewed_raster_pages']=list(range(1,17))
record['native_pdf_sha256']=hashlib.sha256(pdf.read_bytes()).hexdigest()
record['references']={'total':17,'chinese':11,'english_retained':6,'chinese_percent':64.7,'all_cited_in_body':True,'all_native_pdf_entries_complete_on_one_page':True,'bibliography_pdf_pages':[18,19],'journal_metadata_comparisons':10,'journal_browser_verifications':1,'all_full_text_read':False}
path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Updated acceptance record: 24 pages, 17 references, material review complete; physical and submission conditions remain pending.')
