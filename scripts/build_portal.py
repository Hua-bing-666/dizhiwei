from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
PROJ=ROOT/'projects'/'drip-research_ppt169_20261002'; OUT=ROOT/'deliverables'
summary=json.loads((ROOT/'simulation/communication_results/summary.json').read_text(encoding='utf-8'))
deck=json.loads((PROJ/'analysis/deck_content.json').read_text(encoding='utf-8'))
svgpaths=sorted((PROJ/'svg_output').glob('*.svg'))
svgs=[p.read_text(encoding='utf-8') for p in svgpaths]
def js(data):return json.dumps(data,ensure_ascii=False).replace('</','<\/')
template=(ROOT/'scripts/portal.template.html').read_text(encoding='utf-8')
html=template.replace('__COMM_DATA__',js(summary)).replace('__DECK_DATA__',js(deck)).replace('__SLIDE_SVGS__',js(svgs))
(OUT/'index.html').write_text(html,encoding='utf-8',newline='\n')
paths=['application/项目书正文草案.md','application/PPT逐页内容与讲稿.md','application/申报任务体系与立项竞争力.md','docs/三阶段路线与执行定稿.md','simulation/run_simulation.py','simulation/adversarial_audit.py','simulation/communication_feasibility.py','simulation/COMMUNICATION.md','simulation/communication_results/summary.json','simulation/communication_results/trials.csv']
paths+=['deliverables/'+name for name in ['项目书审阅版.pdf','立项答辩.pptx','立项答辩审阅版.pdf'] if (OUT/name).exists()]
paths+=['simulation/communication_results/protocol_stress.json','scripts/validate_new_evidence.py','scripts/qa_deliverables.py']
manifest={'date':'2026-10-02','classification':'uncalibrated_model_and_proposed_work','physical_data':False,'entries':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),'bytes':(ROOT/p).stat().st_size} for p in paths]}
(OUT/'证据清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Offline portal written. Slides embedded:',len(svgs),'evidence records:',len(paths))
