"""Remove research/document navigation from the operational product UI."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'scripts/system_portal.template.html'
s=p.read_text(encoding='utf-8')
s,n=re.subn(r'<a href="研究与答辩资料.html" class="resource-link">.*?</a>','',s);assert n==1
s,n=re.subn(r'<a class="button secondary" href="台架三维结构交互模型_收集优化候选版.html">.*?</a>','',s);assert n==1
s,n=re.subn(r'<div class="settings-links">.*?</div>','',s);assert n==1
changes={
'当前使用未标定模型的合成数据，设备尚未接入。查看、处置和复测记录为本地演示，不代表实物维护结果。':'当前为演示数据，设备尚未接入。核查、处置和复测记录仅保存在此浏览器。',
'读数为种子10300的带噪合成观测；K与R̂取10点均值，状态来自已保存计算。播放按 1 秒回放步长推进，可随时暂停。':'选择场景和时刻，查看压力、流量及候选异常。特征采用10秒平滑，播放可随时暂停。当前为合成回放。',
'参考编号</dt><dd>20261004-A06A07-v1 / seed 10300':'参照状态</dt><dd>演示参照 · 未实物标定',
'本页不修改检测阈值以伪造既有结果。真实标定、配置版本和设备接入需在实施期完成。':'当前使用固定的演示参数，仅供查看；设备接入后需依据实际标定配置。',
'20261004-A06A07-v1，未实物标定':'演示参照，未实物标定',
'5 s · 已保存回放的模型设定':'连续5秒 · 演示设定',
'双压力与流量；平方律、单故障；切换门控尚未实现':'P0 / P1 / Q；工况切换后须人工核查',
'数据来源：A06/A07 v1 · 合成观测 / seed 10300':'演示数据 · 设备未接入',
'不显示未经测量的RSSI、丢包率、距离或电池续航。':'无线接入后显示实际链路数据。',
'当前软件回放与未来硬件路径分别显示':'设备连接规划 · 硬件尚未接入',
'合成回放 → 页面共享状态 → 本地事件与维护记录 → JSON / CSV 导出。没有真实节点接入或无线发送。':'可查看演示数据，记录核查与复测，并导出记录。真实节点与无线链路尚未接入。',
'无实际发收、ACK 或功耗记录':'等待节点与接收端连接',
}
for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
assert not re.search(r'href="(?!#)[^"]+',s)
p.write_text(s,encoding='utf-8',newline='\n')
p=ROOT/'scripts/system_portal.js';s=p.read_text(encoding='utf-8')
changes={
'区分计划配置、当前软件功能和待接入的实物链路。':'查看节点配置、采集通道和无线接入状态。',
'按模型时刻查看参考数据，按操作时间追溯维护记录。':'查看压力、流量记录，追溯核查与维护操作。',
'B操作仅由合成场景提供；当前规则未做切换门控':'演示B支路切换，切换后需人工核查',
'负载变化未提供给诊断（反例）':'正常负载未知，不能据此确认泄漏',
'场景操作为模型标签，非实际阀位测量':'演示场景条件 · 阀位尚未接入',
}
for a,b in changes.items():assert a in s,a;s=s.replace(a,b)
p.write_text(s,encoding='utf-8',newline='\n')
# Keep prior QA receipts intact: this revision gets its own browser session and report.
p=ROOT/'scripts/verify_quality_site.mjs'
s=p.read_text(encoding='utf-8').replace("'quality_site_review'","'table_reference_site_review'").replace("'simulation/quality_review'","'simulation/table_reference_review'")
s=s.replace("await check('chart_current_time_marker_and_accessible_description'", "await check('operations_page_has_no_material_or_report_links',`if([...document.querySelectorAll('a[href]')].some(a=>!a.getAttribute('href').startsWith('#')))throw Error('Non-operational link');if(document.body.innerText.includes('申报与答辩资料')||document.body.innerText.includes('验收报告')||document.body.innerText.includes('以伪造'))throw Error('Process copy left in UI');`);\n await check('chart_current_time_marker_and_accessible_description'")
(ROOT/'simulation/table_reference_review').mkdir(parents=True,exist_ok=True)
(ROOT/'scripts/verify_revised_site.mjs').write_text(s,encoding='utf-8',newline='\n')
print('Operational navigation separated; brief truthful UI copy retained; previous reports preserved.')
