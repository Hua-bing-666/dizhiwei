from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
PROJ=ROOT/'projects'/'drip-research_ppt169_20261002'; OUT=ROOT/'deliverables'
summary=json.loads((ROOT/'simulation/communication_results/summary.json').read_text(encoding='utf-8'))
diagnosis=json.loads((ROOT/'simulation/diagnosis_results/summary.json').read_text(encoding='utf-8'))
deck=json.loads((PROJ/'analysis/deck_content.json').read_text(encoding='utf-8'))
svgpaths=sorted((PROJ/'svg_output').glob('*.svg'))
svgs=[p.read_text(encoding='utf-8') for p in svgpaths]
def js(data):return json.dumps(data,ensure_ascii=False).replace('</','<\/')
template=(ROOT/'scripts/portal.template.html').read_text(encoding='utf-8')
html=template.replace('__COMM_DATA__',js(summary)).replace('__DECK_DATA__',js(deck)).replace('__SLIDE_SVGS__',js(svgs)).replace('__DIAG_DATA__',js(diagnosis))
(OUT/'index.html').write_text(html,encoding='utf-8',newline='\n')
paths=['application/项目书正文草案.md','application/PPT逐页内容与讲稿.md','application/申报任务体系与立项竞争力.md','docs/三阶段路线与执行定稿.md','simulation/run_simulation.py','simulation/adversarial_audit.py','simulation/communication_feasibility.py','simulation/COMMUNICATION.md','simulation/communication_results/summary.json','simulation/communication_results/trials.csv']
paths+=['deliverables/'+name for name in ['项目书审阅版.pdf','立项答辩.pptx','立项答辩审阅版.pdf'] if (OUT/name).exists()]
paths+=['simulation/communication_results/protocol_stress.json','scripts/validate_new_evidence.py','scripts/qa_deliverables.py']
paths+=['application/正式模板正文.md','docs/案例对照与老师建议分析.md','docs/项目范围与三阶段执行方案.md','simulation/diagnosis_feasibility.py','simulation/DIAGNOSIS.md','simulation/diagnosis_results/summary.json','simulation/diagnosis_results/trials.csv','deliverables/大创申报书_模板填写稿.docx','deliverables/大创申报书_模板审阅版.pdf']
paths+=['deliverables/index.html','deliverables/交付检查.json','deliverables/使用说明.md','README.md','scripts/fill_application_template.ps1','scripts/validate_diagnosis_evidence.py','scripts/export_ppt_review.ps1','scripts/package_submission.py','附件1：塔里木大学大学生创新训练项目申报书.doc']
paths+=['docs/国内硬件选型与可行性核对.md','docs/国家级案例写法拆解与申报书改写.md','docs/视觉复核与重设计.md','simulation/hardware_design_check.py','simulation/hardware_results/summary.json','simulation/hardware_results/range_grid.csv','application/figures/vendor/provenance.json','scripts/build_application_design_figures.py','scripts/redesign_document_figures.py','scripts/save_supplier_illustrations.py','scripts/capture_application_platform.py']
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/figures').glob('*')) if p.is_file() and p.suffix in ('.png','.svg')]
paths+=['simulation/hardware_results/observability.csv']
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/figures/vendor').glob('*.png'))]
paths+=['docs/本轮申报书验收记录.md']
paths+=['deliverables/申报书验收记录.json']
manifest={'date':'2026-10-03','classification':'uncalibrated_model_and_proposed_work','physical_data':False,'entries':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'bytes':(ROOT/p).stat().st_size} for p in paths]}
(OUT/'证据清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Offline portal written. Slides embedded:',len(svgs),'evidence records:',len(paths))
