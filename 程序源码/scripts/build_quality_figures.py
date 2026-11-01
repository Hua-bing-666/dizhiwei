"""Larger print typography from frozen source SVGs; no data or CAD editing."""
from pathlib import Path
import re,json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures/quality_review';OUT.mkdir(exist_ok=True)
SOURCES={
 'system_responsibilities':'application/figures/presentation_review/system_responsibilities.svg',
 'water_layout':'application/figures/presentation_review/water_layout.svg',
 'collection_overview':'application/figures/collection_review/collection_overview.svg',
 'measurement_interfaces':'application/figures/interface_review/measurement_interfaces.svg',
 'diagnosis_proposal':'application/figures/presentation_review/diagnosis_proposal.svg',
 'durable_event_sequence':'application/figures/interface_review/durable_event_sequence.svg',
 'noise_outcomes_print':'application/figures/presentation_review/noise_outcomes_print.svg',
 'failure_counterexamples':'application/figures/diagnosis_review/failure_counterexamples.svg'}
def sha(b):return hashlib.sha256(b).hexdigest()
records=[]
for name,path in SOURCES.items():
    src=ROOT/path;s=src.read_text(encoding='utf-8');root=ET.fromstring(s)
    width=float(root.get('viewBox').split()[2]);minimum=24 if width==1000 else 14
    # Raise only font sizes, preserving every geometry, series and label string.
    s=re.sub(r'font-size="([\d.]+)"',lambda m:f'font-size="{max(minimum,float(m[1])):g}"',s)
    s=re.sub(r'font-size:\s*([\d.]+)px',lambda m:f'font-size: {max(minimum,float(m[1])):g}px',s)
    s=s.replace('候选空腔：30s取样 + 25%余量','候选空腔：实际有效容量需标定')
    out=OUT/(name+'.svg');out.write_text(s,encoding='utf-8',newline='\n')
    records.append({'name':name,'source':path,'source_sha256':sha(src.read_bytes()),'svg':out.relative_to(ROOT).as_posix(),'svg_sha256':sha(out.read_bytes()),'width':width,'major_font_lower_bound_pt_at_420pt':minimum*420/width,'data_modified':False,'geometry_modified':False})
# New chart has an explicit operational question and reproducible numeric source.
import draw_interface_review as drawing
drawing.OUT=OUT
data=ROOT/'simulation/quality_review/sampling_checks.json';sample=json.loads(data.read_text(encoding='utf-8'))
f=drawing.Figure('sampling_window_tradeoff',690,'取样与脉冲窗口：可用容量、分辨率和等待','模型最大泄漏与理想计数分析；非容器标定、真实传感器或固件测试。')
f.text(28,143,'容量需求与候选空腔 / mL',26,True)
labels=['空腔几何','75%有效假设','20s + 25%余量','30s + 25%余量']
values=[sample['geometric_capacity_ml'],sample['geometric_capacity_ml']*.75,sample['sample_20s_required_ml_with_1_25_margin'],sample['sample_30s_required_ml_with_1_25_margin']]
for i,(label,value) in enumerate(zip(labels,values)):
    y=187+i*75;f.text(28,y,label,24)
    f.items.append(f'<rect x="245" y="{y-21}" width="{value/700*145:.2f}" height="29" fill="{["#7d9694","#a9b7b5","#476f62","#a37850"][i]}"/>')
    f.text(475,y,f'{value:.1f}',24,anchor='end')
f.text(535,143,'计数窗口与理想步长 / L·min⁻¹',26,True)
for i,row in enumerate(sample['pulse_windows']):
    y=187+i*75;f.text(535,y,f'{row["window_s"]}秒窗口',24)
    f.text(975,y,f'{row["pulse_step_l_min"]:.5f}',26,True,anchor='end')
    f.text(535,y+31,f'因果窗均值滞后 {row["causal_window_mean_delay_s"]:g} 秒',24,color='#52636a')
f.line([(505,130),(505,484)],color='#c6d0d1')
for y,line in [(536,'拟采用20秒分次取样：先标定有效容积≥440mL，长时实验另设排水。'),(579,'75%只是安全液位敏感性假设；30秒要求未扣安全液位，不能直接承诺。'),(622,'长计数窗口降低理想步长，却增加滞后；高斯回放未实现脉冲计数。'),(665,'20,000组恒定流量/脉冲相位检查不包括漏脉冲、抖动或器件误差。')]:f.text(28,y,line,24,color='#52636a')
f.save()
p=OUT/'sampling_window_tradeoff.svg';records.append({'name':p.stem,'source':data.relative_to(ROOT).as_posix(),'source_sha256':sha(data.read_bytes()),'svg':p.relative_to(ROOT).as_posix(),'svg_sha256':sha(p.read_bytes()),'width':1000,'major_font_lower_bound_pt_at_420pt':24*420/1000,'data_modified':False,'geometry_modified':False})
(ROOT/'simulation/quality_review/figure_sources.json').write_text(json.dumps({'date':'2026-10-05','physical_validation':False,'figures':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('8 source-matched SVG variants with larger print typography; data/geometry preserved.')
