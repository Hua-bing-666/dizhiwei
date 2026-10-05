from pathlib import Path
import json, hashlib, argparse
from html import escape
ROOT=Path(__file__).resolve().parents[1]
PROJ=ROOT/'projects'/'drip-research_ppt169_20261002'; OUT=ROOT/'deliverables'
parser=argparse.ArgumentParser();parser.add_argument('--pages-only',action='store_true',help='Rebuild website pages before publishing documents; leave evidence manifest intact.')
parser.add_argument('--operations-only',action='store_true',help='Rebuild the operations UI without touching documents, research pages or historical receipts.')
args=parser.parse_args()
if args.operations_only:
    system=(ROOT/'scripts/system_portal.template.html').read_text(encoding='utf-8')
    replay=json.loads((ROOT/'simulation/presentation_review/web_replay.json').read_text(encoding='utf-8'))
    system=system.replace('__SYSTEM_CSS__',(ROOT/'scripts/system_portal.css').read_text(encoding='utf-8')).replace('__DIAG_DATA__',json.dumps(replay,ensure_ascii=False).replace('</',r'<\/')).replace('__SYSTEM_JS__',(ROOT/'scripts/system_portal.js').read_text(encoding='utf-8'))
    assert '__SYSTEM_' not in system
    (OUT/'index.html').write_text(system,encoding='utf-8',newline='\n')
    print('Operations UI rebuilt independently; research and document artifacts preserved.')
    raise SystemExit(0)
summary=json.loads((ROOT/'simulation/communication_results/summary.json').read_text(encoding='utf-8'))
diagnosis=json.loads((ROOT/'simulation/diagnosis_results/summary.json').read_text(encoding='utf-8'))
deck=json.loads((PROJ/'analysis/deck_content.json').read_text(encoding='utf-8'))
svgpaths=sorted((PROJ/'svg_output').glob('*.svg'))
svgs=[p.read_text(encoding='utf-8') for p in svgpaths]
def js(data):return json.dumps(data,ensure_ascii=False).replace('</',r'<\/')
template=(ROOT/'scripts/portal.template.html').read_text(encoding='utf-8')
html=template.replace('__COMM_DATA__',js(summary)).replace('__DECK_DATA__',js(deck)).replace('__SLIDE_SVGS__',js(svgs)).replace('__DIAG_DATA__',js(diagnosis))
references=json.loads((ROOT/'application/references.json').read_text(encoding='utf-8'))
literature='<h2>学术文献与正文依据</h2><p>17篇期刊文献：中文11篇（64.7%），英文6篇。来源、支撑点与适用边界均有对应记录。</p><p><a href="../docs/参考文献核验与正文对应.md">文献核验与正文对应</a> · <a href="../application/references.json">完整引文与来源记录</a></p><div class="plainlinks">'
for r in references['references']:
    literature+=f'<a href="{escape(r["url"],quote=True)}">[{r["number"]}] {escape(r["title"])} · {r["year"]} · {r["language"]}</a>'
literature+='</div>'
html=html.replace('__LITERATURE_LINKS__',literature)
html=html.replace('<main id="workspace">', '<main id="workspace"><div style="display:flex;flex-wrap:wrap;gap:8px 22px;padding:12px 0;border-bottom:1px solid #dde5e9;font-size:13px"><a href="index.html" style="min-height:44px;display:inline-flex;align-items:center">← 返回运行平台</a><a href="../docs/项目总规划与任务验收台账.md" style="min-height:44px;display:inline-flex;align-items:center">整体规划与当前任务 ↗</a></div>',1)
html=html.replace('<main id="workspace">','<main id="workspace"><div class="note" id="historical-config-note" style="margin-top:16px">本页统计与答辩草案保留历史配置；当前运行主站使用20261004-A06A07-v1。最新材料为<a href="大创申报书_格式优化审阅版.pdf">25页学校申报书</a>、<a href="实施项目书.pdf">13页实施项目书</a>及<a href="../docs/全量复核与格式优化验收报告.md">本轮验收报告</a>；后者为自主执行稿，正式任务书待套学校原表，PPT待同步。模型与接口的原始依据见<a href="../docs/仿真建模与诊断证据分项验收.md">仿真验收</a>及<a href="../docs/硬件接口与LoRa通信论证分项验收.md">接口验收</a>。</div>',1)
(OUT/'研究与答辩资料.html').write_text(html,encoding='utf-8',newline='\n')
system=(ROOT/'scripts/system_portal.template.html').read_text(encoding='utf-8')
operations_replay=json.loads((ROOT/'simulation/presentation_review/web_replay.json').read_text(encoding='utf-8'))
system=system.replace('__SYSTEM_CSS__',(ROOT/'scripts/system_portal.css').read_text(encoding='utf-8')).replace('__DIAG_DATA__',js(operations_replay)).replace('__SYSTEM_JS__',(ROOT/'scripts/system_portal.js').read_text(encoding='utf-8'))
assert '__SYSTEM_' not in system
(OUT/'index.html').write_text(system,encoding='utf-8',newline='\n')
if args.pages_only:
    print('Offline operation and research pages rebuilt; evidence manifest left intact.')
    raise SystemExit(0)
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
paths+=['docs/申报书黑白流程与模型验收.md','scripts/prepare_application_payload.py','application/figures/design_provenance.json']
paths+=['application/references.json','docs/参考文献核验与正文对应.md','docs/中文文献来源核验.json','scripts/verify_literature_sources.py','scripts/integrate_application_references.py']
paths+=['scripts/validate_application_references.py','scripts/finalize_application_review.py']
paths+=['scripts/build_application_visuals.py','docs/论文图示借鉴与本轮结构调整.md','application/models/bench_layout.obj','application/models/bench_layout.json']
paths+=['deliverables/台架三维结构交互模型.html','docs/三维结构模型优化说明.md','scripts/build_bench_cad.py','scripts/build_bench_viewer.py','scripts/bench_viewer.template.html','scripts/capture_bench_views.mjs','scripts/render_bench_plate.py','scripts/validate_bench_model.py','application/figures/bench_plate_provenance.json']
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/models').rglob('*')) if p.is_file()]
paths+=['docs/系统定位与后续研究路线.md','docs/UI重设计与来源记录.md','deliverables/界面验收记录.json','scripts/portal.template.html','scripts/verify_research_ui.mjs','scripts/refine_system_ui.py']
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'design-system').rglob('*.md'))]
paths+=['deliverables/研究与答辩资料.html','scripts/system_portal.template.html','scripts/system_portal.css','scripts/system_portal.js','docs/项目总规划与任务验收台账.md','docs/网站功能与验收说明.md']
paths+=[p for p in ['scripts/verify_operations_ui.mjs','deliverables/研究资料界面验收记录.json'] if (ROOT/p).exists()]
paths+=['docs/本轮网站与总体规划验收报告.md']
paths+=['scripts/finalize_operations_review.py']
paths+=['docs/三阶段分项执行与验收标准.md','docs/三维台架建模论证与本轮验收.md','deliverables/台架三维结构交互模型_收集优化候选版.html','deliverables/分项验收进度.json','deliverables/三维分项验收记录.json','scripts/audit_bench_collection.py','scripts/render_collection_review.py','scripts/finalize_collection_review.py']
paths+=['scripts/verify_staged_evidence.py']
paths+=['docs/仿真建模与诊断证据分项验收.md','simulation/review_diagnosis.py','scripts/validate_diagnosis_review.py','scripts/plot_diagnosis_review.py','scripts/verify_diagnosis_figures.mjs','scripts/finalize_diagnosis_review.py','deliverables/仿真分项验收记录.json']
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'simulation/diagnosis_review').glob('*')) if p.is_file()]
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/figures/diagnosis_review').glob('*')) if p.is_file()]
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/figures/collection_review').glob('*')) if p.is_file()]
paths+=['docs/硬件接口与LoRa通信论证分项验收.md','scripts/check_hardware_interfaces.py','scripts/check_interface_protocol.py','scripts/collect_interface_sources.py','scripts/draw_interface_review.py','scripts/verify_interface_figures.mjs','scripts/finalize_interface_review.py','deliverables/接口与通信分项验收记录.json']
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'simulation/interface_review').glob('*')) if p.is_file()]
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/figures/interface_review').glob('*')) if p.is_file()]
paths+=['docs/网站佐证与申报图表分项验收.md','deliverables/网站与图文分项验收记录.json','deliverables/申报图文取舍与呈现审阅.html','deliverables/网站预览.png']
paths+=['scripts/'+name for name in ['prepare_presentation_review.py','draw_presentation_review.py','plot_presentation_statistics.py','build_presentation_review.py','verify_presentation_site.mjs','verify_presentation_diagrams.mjs','capture_presentation_evidence.mjs','verify_presentation_assets.mjs','finalize_presentation_review.py']]
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'simulation/presentation_review').glob('*')) if p.is_file()]
paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'application/figures/presentation_review').rglob('*')) if p.is_file()]
paths+=['docs/学校模板申报书整合与分项验收.md','deliverables/申报书整合分项验收记录.json','scripts/capture_application_panel.mjs','scripts/verify_application_integration.py','scripts/finalize_application_integration.py']
for directory in ['application/application_integration','application/figures/application_integration','simulation/application_integration']:
    paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/directory).rglob('*')) if p.is_file()]
paths+=['application/实施项目书.md','docs/全量复核与格式优化执行计划.md','docs/全量复核与格式优化验收报告.md','deliverables/大创申报书_格式优化稿.docx','deliverables/大创申报书_格式优化审阅版.pdf','deliverables/实施项目书.docx','deliverables/实施项目书.pdf','deliverables/格式优化与实施项目书验收记录.json']
paths+=['scripts/'+name for name in ['prepare_quality_review.py','prepare_quality_payload.py','prepare_quality_document_check.py','fill_quality_application.ps1','build_quality_figures.py','verify_quality_visuals.mjs','verify_quality_site.mjs','capture_quality_panel.mjs','quality_recheck.py','render_quality_documents.py','verify_quality_application.py','build_execution_book.py','export_quality_book.ps1','verify_execution_book.py','collect_taskbook_template.py','update_quality_release_content.py','finalize_quality_release.py','verify_quality_release.py']]
paths+=['.gitattributes','scripts/build_portal.py','scripts/verify_quality_model_viewer.mjs']
for directory in ['application/quality_release','application/figures/quality_review','application/school_templates','simulation/quality_review']:
    paths+=[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/directory).rglob('*')) if p.is_file()]
paths=list(dict.fromkeys(paths))
manifest={'date':'2026-10-05','classification':'uncalibrated_model_and_proposed_work','physical_data':False,'entries':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'bytes':(ROOT/p).stat().st_size} for p in paths]}
(OUT/'证据清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Offline portal written. Slides embedded:',len(svgs),'evidence records:',len(paths))
