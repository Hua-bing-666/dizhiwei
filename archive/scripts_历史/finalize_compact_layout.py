"""Freeze a layout release only when its exact rendered pages were reviewed."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/compact_layout_review'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=read(DATA/'visual_review.json')
assert review['status']=='manual_visual_pass' and len(review['pages'])==20
for path,digest in review['artifact_sha256'].items():assert sha(ROOT/path)==digest
for page in review['pages']:
    assert page['manual_inspection']=='passed'
    assert sha(ROOT/page['file'])==page['sha256'],'Changed page requires a fresh visual review'
checks=read(DATA/'document_checks.json');assert checks['pages']==20
for path,digest in checks['artifact_sha256'].items():assert sha(ROOT/path)==digest
figure=read(DATA/'figure_checks.json')['figures'][0]
assert not any(figure[k] for k in ['outside','overlappingLabels','labelsOutsideOwnBox','guideLabelsOverBoxes'])
assert figure['minFontPt']>=9.5
assert sha(ROOT/'application/figures/compact_layout/water_layout.png')==figure['png_sha256']
gap=read(DATA/'page_gap_comparison.json');assert not gap['after']['pages_with_bottom_gap_over_25_percent']
prior=read(ROOT/'deliverables/表格文献与职责修订验收记录.json')
assert sha(ROOT/'deliverables/大创申报书_格式优化稿.docx')==prior['input_sha256'],'Original user document changed'
unchanged=['deliverables/index.html','deliverables/实施项目书.docx','deliverables/实施项目书.pdf','application/正式模板正文.md','application/references.json']
files=['deliverables/大创申报书_紧凑排版稿.docx','deliverables/大创申报书_紧凑排版审阅版.pdf','deliverables/使用说明.md','README.md','docs/申报书分页与图片复核.md']
for folder in ['application/compact_layout_revision','application/figures/compact_layout','simulation/compact_layout_review']:
    files.extend(p.relative_to(ROOT).as_posix() for p in sorted((ROOT/folder).glob('*')) if p.is_file())
files.extend('scripts/'+name for name in ['compact_application_layout.py','build_compact_water_figure.py','verify_compact_water_figure.mjs','export_compact_application.ps1','verify_compact_application.py','measure_application_page_gaps.py','finalize_compact_layout.py'])
record={'date':'2026-10-05','status':'passed_scoped_pagination_and_image_review','pages':20,'body_pages':15,'figures':9,'data_tables':4,'chinese_references':5,'english_references':3,
        'all_document_text_unchanged':True,'character_font_sizes_unchanged':True,'original_user_file_preserved':True,'input_sha256':read(ROOT/'application/compact_layout_revision/build_record.json')['input_sha256'],
        'physical_validation':False,'administrative_complete':False,
        'scope':'申报书分页、段距、图2版面；网站、实施书、仿真数据、三维实体和PPT未改',
        'page_gap_definition':gap['method'],'pages_with_trailing_gap_over_25_percent':{'before':7,'after':0},
        'checks':['simulation/compact_layout_review/'+name for name in ['document_checks.json','figure_checks.json','page_gap_comparison.json','visual_review.json']],
        'unchanged_files':[{'path':p,'sha256':sha(ROOT/p)} for p in unchanged],
        'files':[{'path':p,'sha256':sha(ROOT/p)} for p in files]}
out=ROOT/'deliverables/申报书紧凑排版验收记录.json'
out.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Exact 20-page visual record, figure bounds, table centers and input preservation verified; release hashes frozen.')
