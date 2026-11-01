"""Rewrite Section 8 around the five previously generated main figures.
All figure files are reused byte-for-byte; this task authors the narrative.
"""
from pathlib import Path
import json,hashlib,shutil
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

B=Path(__file__).resolve().parents[1];ROOT=B.parents[1]
SOURCE=ROOT/'tmp/section8_rewrite/八_原件快照.docx'
OLD=ROOT/'output/第八部分_机制与轨迹图组_20261027'
NAMES=['图8-1_泄漏信号与判据演变','图8-2_特征轨迹与诊断歧义',
 '图8-3_候选方法与不确定性','图8-4_故障幅值与检出响应','图8-5_采集次数与响应余量']
for name in NAMES:
 for ext in ['png','pdf','svg']:shutil.copy2(OLD/'figures'/f'{name}.{ext}',B/'figures'/f'{name}.{ext}')

BLOCKS=[
('title','八、已有基础'),
('heading','8.1 系统设计与诊断预研'),
('body','围绕南疆棉田膜下滴灌支管巡检需求，团队已完成文献梳理、双支路水路设计、参数化装配、诊断算法预研和本地巡检软件开发，并开展了故障、正常调节与测量扰动的合成仿真，形成了系统设计、方法对照和软件实现相互支撑的前期研究基础。'),
('body','台架方案采用A、B双支路结构：A支路用于监测和故障注入，B支路通过开关及负载调节形成正常扰动。两处压力测点包围受限区段，结合支路流量提取出流与阻力特征；下游设置泄漏旁路和独立收集称量位置，用于记录泄漏量。已完成包含207个有效实体的参数化装配模型，支持整体、电气和泄漏计量部位查看，为器件布置、接口连接和台架搭建提供依据。'),
('body','水力模型已复现支路切换、渐进泄漏和局部受限的压力—流量变化。图8-1中，泄漏使流量上升、下游压力下降，出流特征K持续增加，阻力特征R未出现持续上升。本例在403秒形成泄漏候选，比达到15%流量偏离的模型参照提前51秒。信号变化与判据响应的对应关系，为测点选择和故障注入试验提供了直观依据。'),
('figure1',''),
('body_page','特征轨迹对照进一步明确了原因判别所需的信息。图8-2中，未知正常负载增加与等效泄漏形成重合轨迹，上游测压漂移也会抬高阻力估计。项目据此将诊断结果作为异常候选，并将操作记录、健康标定和人工复测纳入核查流程，使检测结果能够对应到可检查的支管与测点区段。'),
('figure2',''),
('body','在方法比较中，团队使用相同测量前端、窗口和确认条件，对固定门限、稳健门限及累积组合开展配对评价。冻结参数后，以100个测试种子完成三档噪声下900条轨迹、2700条方法记录。10 kPa噪声下，稳健门限对泄漏和受限均有99/100条有效早期，固定门限分别为14/100和16/100；3470秒正常监测对照中，稳健门限有2/100条出现误报（图8-3）。这些结果为后续台架试验选择比较基线提供了依据。'),
('figure3',''),
('body_page','为确定检出范围，团队完成了5%—30%终值流量偏离的幅值扫描，共3000条故障轨迹及300条健康对照。0.3 kPa噪声下，5%泄漏有2/100条正确提示，10%泄漏为100/100；10 kPa噪声下，5%受限为22/100（图8-4）。这些结果为按故障程度分组、比较检出与响应时间提供了依据。'),
('figure4',''),
('body','采集策略已比较1、2、5秒巡航周期。渐进泄漏场景中，压力读取次数中位数由471次降至330.2次，提前量由52.5秒变为51.5秒；切换期快泄漏较早触发加密，读取次数下降较少（图8-5）。后续将结合响应要求选择采集周期，并测量实际通信与供电开销。'),
('figure5',''),
('heading_page','8.2 节点程序与平台软件'),
('body','团队已完成便携C诊断内核、采集适配与主机回放工具。既有内核在216条合成轨迹、130,896次更新中，与参考程序的九字段输出一致，形成了输入校验、状态管理和逐点核验的程序基础。近期预研进一步开展了10秒不重叠块累积和判据（CUSUM）的门限与持续时间分析，采样程序已加入块边界更新逻辑。后续将结合实际传感器完成目标板移植，并统一节点、接收端与平台的诊断调用。'),
('body','通信部分已形成遥测、事件与应答帧协议，完成编解码、分段接收、重复报文、确认丢失和缓存重发等主机测试。遥测、事件与应答帧长度分别为55、57和24字节；设备会话、事件序号、接收入库与确认状态均有对应记录，便于追踪事件送达及断连恢复过程，为LoRa模块接入提供了协议与程序基础。'),
('body','本地巡检平台已完成Python服务、SQLite存储及Windows桌面封装，提供八页操作界面，支持数据回放、压力与流量趋势查看、三维测点聚焦、事件核查、历史查询和CSV/JSON导出。软件已完成启动、暂停、保存及重启恢复检查，核查、处置与复测记录可关联到同一事件。现有平台能够承载台架试验的数据查看与记录整理，下一步重点完成真实采集数据接入和软硬件联合运行。'),
('heading','8.3 现有条件与实施安排'),
('body','目前已具备水泵、稳压水源、电子秤和实验场地条件，配套的台架模型、接口分析、仿真程序及巡检软件已完成前期准备。硬件方案按单监测节点、单LoRa接收端和本地计算机组织，采用成品开发板及模块化接口，便于分步装配、独立调试和器件更换。'),
('body','实施阶段将于2027年3—4月完成传感器选型与标定、台架装配和节点采集联调，随后依次开展健康工况采集、故障与正常扰动对照、LoRa收发及连续运行试验。试验同步保存参考测量、操作标签、原始采样和事件记录，形成可复核的数据集与测试报告，为方法分析和结题成果整理提供支撑。'),
]
CAPTIONS={
 'figure1':('图8-1 渐进泄漏的信号与判据演变',
 '注：初始K/R模型，压力噪声σ=3 kPa，种子10300，十秒因果均值。灰区为故障推进段，黑点线为确认时刻，灰虚线为15%流量偏离的模型参照。'),
 'figure2':('图8-2 特征轨迹揭示负载歧义与测压漂移',
 '注：初始K/R模型，同一噪声实现下的360—600秒轨迹。泄漏与未知正常负载观测重合；测压漂移终值为上游压力偏置10 kPa。'),
 'figure3':('图8-3 高噪声下候选方法的有效早期与正常误报',
 '注：σ=10 kPa，每组100种子，横线为Wilson 95%区间。有效早期要求无前期误报、首次模式正确且早于15%模型参照；正常误报按每条3470秒监测统计。'),
 'figure4':('图8-4 故障幅值与正确提示比例',
 '注：稳健门限，每点100种子，阴影为Wilson 95%区间。正确提示指600秒内无前期误报且故障后首次模式正确；五档幅值按实际测试点连接。'),
 'figure5':('图8-5 采集次数与响应余量的关系',
 '注：每场景16个配对种子，种子内先平均采集相位。点为中位数，误差线为四分位区间；标注为巡航周期，触发后进入1 Hz加密采集。'),
}
doc=Document(SOURCE)
for child in list(doc._element.body):
 if child.tag!=qn('w:sectPr'):doc._element.body.remove(child)
for relid,rel in list(doc.part.rels.items()):
 if rel.reltype==RT.IMAGE:doc.part.drop_rel(relid)
def font(run,size=11,bold=False):
 run.font.name='Times New Roman';run.font.size=Pt(size);run.font.bold=bold;run.font.color.rgb=RGBColor(0,0,0)
 run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
def para(text='',size=11,bold=False,keep=False,page=False):
 p=doc.add_paragraph();font(p.add_run(text),size,bold)
 pr=p._p.get_or_add_pPr();snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0');pr.append(snap)
 pf=p.paragraph_format;pf.line_spacing=1.2;pf.space_before=Pt(0);pf.space_after=Pt(5)
 pf.keep_together=True;pf.keep_with_next=keep;pf.widow_control=True;pf.page_break_before=page
 return p
md=[]
for kind,text in BLOCKS:
 if kind.startswith('figure'):
  number=int(kind[-1]);name=NAMES[number-1];caption,note=CAPTIONS[kind]
  p=para(keep=True);p.clear();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  p.paragraph_format.line_spacing=1;p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(2)
  p.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.6))
  p._p.xpath('.//wp:docPr')[0].set('descr',caption)
  p=para(caption,9,True,True);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(2)
  p=para(note,9);p.paragraph_format.line_spacing=1.1;p.paragraph_format.space_after=Pt(5)
  md.extend([f'![{caption}](figures/{name}.png)',f'**{caption}**',note])
 else:
  heading=kind in ['title','heading','heading_page']
  p=para(text,12 if kind=='title' else 11,heading,heading or kind=='body_page',kind in ['body_page','heading_page'])
  if kind.startswith('heading'):p.paragraph_format.space_before=Pt(5)
  md.append(('# ' if kind=='title' else '## ' if kind.startswith('heading') else '')+text)
target=B/'第八部分_已有基础_现状整合重写稿.docx';doc.save(target)
(B/'第八部分_已有基础_正文.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
plain=[]
for kind,text in BLOCKS:
 if kind.startswith('figure'):
  caption,note=CAPTIONS[kind];plain.extend([f'〔此处插入{caption}〕',note])
 else:plain.append(text)
(B/'第八部分_已有基础_可复制正文.txt').write_text('\n\n'.join(plain)+'\n',encoding='utf-8-sig')
audit=dict(input_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
 body_characters=sum(len(t) for k,t in BLOCKS if k.startswith('body')),sections=3,figure_count=5,figure_files_unchanged=True,
 original_attachment_figures_discarded=True,legacy_integer_equivalence_distinguished_from_current_block_research=True,
 figures=[dict(name=name,sha256=hashlib.sha256((B/'figures'/f'{name}.png').read_bytes()).hexdigest()) for name in NAMES])
assert all(hashlib.sha256((B/'figures'/f'{n}.png').read_bytes()).digest()==hashlib.sha256((OLD/'figures'/f'{n}.png').read_bytes()).digest() for n in NAMES)
(ROOT/'tmp/section8_rewrite/build_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(target);print('Body characters',audit['body_characters'])
