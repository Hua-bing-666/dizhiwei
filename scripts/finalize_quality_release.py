"""Publish inspected native files only; never manufacture a visual pass record."""
from pathlib import Path
import hashlib,json,shutil

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/quality_review'
FROZEN=ROOT/'application/quality_release'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p: json.loads(Path(p).read_text(encoding='utf-8'))

def check_map(mapping):
    for name,digest in mapping.items():
        assert sha(ROOT/name)==digest, ('Source changed after check',name)

def main():
    application=read(DATA/'document_checks.json')
    book=read(DATA/'execution_book_checks.json')
    site=read(DATA/'site_checks.json')
    capture=read(DATA/'website_capture_checks.json')
    figures=read(DATA/'figure_checks.json')
    viewer=read(DATA/'model_viewer_checks.json')
    manual=read(DATA/'manual_visual_review.json')
    assert application['status'].startswith('passed_programmatic') and application['native_pdf_pages']==25
    assert book['status'].startswith('passed_programmatic') and book['native_pdf_pages']==13
    assert site['status']=='passed' and len(site['workflow_checks'])==20
    assert manual['status']=='passed_individual_visual_inspection'
    assert manual['reviewer']=='root_agent_manual_image_inspection'
    for item in manual['documents']:
        assert item['page_count']==len(item['pages'])
        assert sha(ROOT/item['pdf_path'])==item['pdf_sha256']
        assert sha(ROOT/item['docx_path'])==item['docx_sha256']
        for page in item['pages']:
            assert sha(ROOT/page['path'])==page['sha256'], ('Unreviewed page change',page['path'])
    for item in manual['figures']+manual['site_screenshots']+manual['model_viewer_screenshots']:
        assert sha(ROOT/item['path'])==item['sha256'], ('Unreviewed image change',item['path'])
    check_map(application['source_sha256'])
    check_map(book['source_sha256'])
    assert site['source_sha256']==sha(ROOT/'deliverables/index.html')
    assert viewer['status']=='passed_programmatic_viewer_checks_manual_review_pending' and len(viewer['views'])==20
    check_map(viewer['source_sha256'])
    assert manual['model_viewer_source_sha256']==sha(ROOT/'deliverables/台架三维结构交互模型_收集优化候选版.html')
    assert capture['source_sha256']['site']==sha(ROOT/'deliverables/index.html')
    assert capture['source_sha256']['research']==sha(ROOT/'deliverables/研究与答辩资料.html')
    assert capture['source_sha256']['script']==sha(ROOT/'scripts/capture_quality_panel.mjs')
    assert not capture['dom_replaced'] and not capture['css_overridden'] and not capture['pixels_postprocessed']
    for figure in figures['figures']:
        assert not figure['outside'] and figure['minFontPt']>=9.5
        for ext in ['png','svg']:
            assert sha(ROOT/f'application/figures/quality_review/{figure["name"]}.{ext}')==figure[ext+'_sha256']
    mappings={
        'tmp/quality_application/candidate/大创申报书_模板填写稿.docx':'deliverables/大创申报书_格式优化稿.docx',
        'tmp/quality_application/candidate/大创申报书_模板审阅版.pdf':'deliverables/大创申报书_格式优化审阅版.pdf',
        'tmp/quality_book/实施项目书.docx':'deliverables/实施项目书.docx',
        'tmp/quality_book/实施项目书.pdf':'deliverables/实施项目书.pdf',
        'tmp/quality_application/application_payload.json':'application/quality_release/application_payload.json',
        'tmp/quality_application/candidate/native_layout.json':'application/quality_release/application_native_layout.json',
        'tmp/quality_book/native_layout.json':'application/quality_release/book_native_layout.json',
        'tmp/quality_book/layout_contract.json':'application/quality_release/book_layout_contract.json',
        'application/正式模板正文.md':'application/quality_release/申报书正文冻结稿.md',
        'application/实施项目书.md':'application/quality_release/实施项目书正文冻结稿.md',
    }
    FROZEN.mkdir(parents=True,exist_ok=True)
    copies=[]
    for origin,destination in mappings.items():
        original,target=ROOT/origin,ROOT/destination
        assert target.resolve().is_relative_to(ROOT.resolve())
        shutil.copyfile(original,target)
        assert sha(target)==sha(original)
        copies.append({'origin':origin,'path':destination,'sha256':sha(target),'bytes':target.stat().st_size})
    (FROZEN/'README.md').write_text('''# 本轮冻结材料\n\n2026年10月5日。25页学校申报书与13页实施项目书的正文、填充参数、插入尺寸和原生分页记录。\n\n正文冻结副本保留原引用路径，查看图片请按application主目录解析；副本不作为独立网站。对应最终DOCX/PDF在deliverables，完整哈希和原始工作路径映射在deliverables/格式优化与实施项目书验收记录.json。程序与人工验收在simulation/quality_review；逐页PNG属于内部检查记录，不作为成果或实测。学校正式任务书未取得，book布局合同是自主执行稿版式，不能作为学校原模板。\n\n修改正文、图片或版面后须重新导出、渲染、逐页检查并建立新的人工审阅记录。finalize脚本只核对已有记录，不自动产生人工通过状态。\n''',encoding='utf-8',newline='\n')
    names=['recheck_cad','sampling_checks','figure_sources','figure_checks','site_checks','model_viewer_checks','model_viewer_before_fix','website_capture_checks','document_checks','execution_book_checks','manual_visual_review']
    record={
        'date':'2026-10-05','status':'passed_internal_material_and_scoped_software_review',
        'physical_validation':False,'administrative_complete':False,'official_taskbook_template_obtained':False,
        'baseline_commit':'d8b22f0cbb0c1d795e57b087864ffbd5fa4609f4',
        'documents':{'application_pages':25,'execution_book_pages':13,'total_individually_reviewed_pages':38},
        'artifacts_and_frozen_inputs':copies,
        'receipts':[{'path':f'simulation/quality_review/{name}.json','sha256':sha(DATA/(name+'.json'))} for name in names],
        'acceptance_scope':{'Q01_Q06':'passed_in_listed_internal_scope','Q07':'see_separate_release_checks_and_package_verification','machine_checks_do_not_replace_manual_review':True},
        'unresolved':['2027 batch rules and official taskbook','real identities and signatures','approved targets and budget','reference instruments, continuous water source, field permission and team development capability','pressure sensor quotations and exact order specifications','hardware, calibration, firmware, RF, energy and field experiments','PPT synchronization after stable document approval'],
        'historical_evidence_modified':False,
    }
    (ROOT/'deliverables/格式优化与实施项目书验收记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Published 25-page application and 13-page execution book; inspected-source copies and scoped receipts frozen.')

if __name__=='__main__':
    main()
