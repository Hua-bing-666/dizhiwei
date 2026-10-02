"""Plain-text payload for native Windows template editing; no DOCX authoring."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'tmp/reference_review';OUT.mkdir(parents=True,exist_ok=True)
text=(ROOT/'application/正式模板正文.md').read_text(encoding='utf-8')
parts=re.split(r'^## ',text,flags=re.M)[1:]
sections=['\r'.join(line for line in re.sub(r'^### ', '',part,flags=re.M).splitlines() if line.strip()) for part in parts]
assert len(sections)==9
payload={'title':text.splitlines()[0][2:],'sections':sections,'figures':[
 {'path':'application/figures/system_scope.png','caption':'图1 支管巡检系统信息闭环设计 尚未连接实物'},
 {'path':'application/figures/dual_pressure_layout.png','caption':'图2 双压力流量布点与台架设计 非实物照片'},
 {'path':'application/figures/early_diagnosis.png','caption':'图3 渐进故障与早期判据的合成模型检验 参数未标定 非实物性能'}]}
(OUT/'application_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print('Nine template sections prepared; abstract',len(parts[0].split('\n\n')[1]),'characters.')
