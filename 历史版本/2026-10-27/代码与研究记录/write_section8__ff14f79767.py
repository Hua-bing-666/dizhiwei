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
SCREENSHOT=ROOT/'deliverables/桌面版V1.3验收预览/desktop-monitor-with-data.png'
NAMES.append('图8-6_巡检平台监测界面原始截图')
shutil.copy2(SCREENSHOT,B/'figures'/f'{NAMES[-1]}.png')

BLOCKS=[
('title','八、已有基础'),
('heading','8.1 系统设计与诊断预研'),
('body','围绕南疆棉田膜下滴灌支管巡检需求，团队已完成文献梳理、双支路水路设计、参数化装配、诊断算法预研和本地巡检软件开发，并开展了故障、正常调节与测量扰动的合成仿真，形成了较为完整的设计方案、对照结果与软件工具。'),
('body','台架方案采用A、B双支路结构：A支路用于监测和故障注入，B支路通过开关及负载调节形成正常扰动。两处压力测点包围受限区段，结合支路流量提取出流与阻力特征；下游设置泄漏旁路和独立收集称量位置，用于记录泄漏量。已完成包含207个有效实体的参数化装配模型，支持整体、电气和泄漏计量部位查看，为器件布置、接口连接和台架搭建提供依据。'),
('body','水力模型已复现支路切换、渐进泄漏和局部受限的压力—流量变化。渐进泄漏的信号与判据演变如图8-1所示。该例采用初始K/R模型，压力噪声标准差取3 kPa，三通道观测经十秒因果均值处理。随着泄漏发展，流量上升、下游压力下降，出流特征K持续增加，阻力特征R保持波动。黑色点线标出403秒的候选确认时刻，灰色虚线对应454秒达到15%流量偏离的模型参照，两者相差51秒，为后续故障注入与响应评价提供了依据。'),
('figure1',''),
('body_page','负载变化与测压漂移的特征轨迹如图8-2所示。在相同噪声条件下，未知正常负载增加与等效泄漏的轨迹重合；上游测压偏置增加至10 kPa时，阻力估计随之升高并越过初始R门限。前期分析据此将操作记录、健康标定和人工复测纳入核查流程，使异常提示能够对应到具体支管与测点区段。'),
('figure2',''),
('body','候选方法的对照结果如图8-3所示。采用相同测量前端、窗口和确认条件，以100个随机种子完成三档噪声下900条轨迹、2700条方法记录。有效早期按无前期误报、故障后首次模式正确且早于15%模型参照统计。压力噪声标准差为10 kPa时，稳健门限对两类故障均为99/100条有效早期，固定门限分别为14/100和16/100；每条3470秒的正常监测中，稳健门限有2/100条出现误报。图中横线为Wilson 95%置信区间，结果为台架试验选择比较基线提供了依据。'),
('figure3',''),
('body_page','故障幅值与正确提示比例的关系如图8-4所示。按5%—30%终值流量偏离完成3000条故障轨迹和300条健康对照，以600秒内无前期误报、故障后首次候选正确为评价依据。压力噪声标准差为0.3 kPa时，5%泄漏有2/100条正确提示，10%泄漏为100/100；标准差增至10 kPa时，5%受限为22/100。每个测试档位采用100组噪声实现，阴影为Wilson 95%置信区间，为后续按故障程度组织试验提供了参考。'),
('figure4',''),
('body','采集次数与响应余量的对照如图8-5所示。每个场景开展16组配对回放，比较1、2、5秒巡航周期，图中点与误差线分别表示中位数和四分位区间。渐进泄漏中，1秒至5秒巡航的读取次数中位数由471次降至330.2次，提前量由52.5秒变为51.5秒；切换期快泄漏较早触发1 Hz加密采集，读取次数下降较少。结果为采集周期选择和后续开销测试提供了依据。'),
('figure5',''),
('heading_page','8.2 节点程序与平台软件'),
('body','团队已完成便携C诊断内核、采集适配与主机回放工具。既有内核在216条合成轨迹、130,896次更新中，与参考程序的九字段输出一致。近期进一步开展了10秒不重叠块累积和判据（CUSUM）的门限与持续时间分析，采样程序已加入块边界更新逻辑，为目标板移植和统一诊断调用提供了程序基础。'),
('body','通信部分已形成遥测、事件与应答帧协议，完成编解码、分段接收、重复报文和缓存重发等主机测试。三类帧长度分别为55、57和24字节，设备会话、事件序号及接收确认均有对应记录，便于追踪事件送达和断连恢复过程。'),
('body','本地巡检平台的监测界面如图8-6所示。平台采用Python服务与SQLite存储，已完成Windows桌面封装，支持监测回放、三维测点查看、事件核查、历史查询和数据导出，图示取自现有软件的回放运行。软件已完成启动、暂停、保存与重启恢复检查，核查、处置和复测记录可关联到同一事件，为台架联调和试验数据整理提供了工具。'),
('figure6',''),
('heading','8.3 现有条件与实施安排'),
('body','目前已具备水泵、稳压水源、电子秤和实验场地条件，配套的台架模型、接口分析、仿真程序及巡检软件已完成前期准备。硬件方案按单监测节点、单LoRa接收端和本地计算机组织，采用成品开发板及模块化接口，便于分步装配、独立调试和器件更换。'),
('body','实施阶段将于2027年3—4月完成传感器选型与标定、台架装配和节点采集联调，随后依次开展健康工况采集、故障与正常扰动对照、LoRa收发及连续运行试验。试验同步保存参考测量、操作标签、原始采样和事件记录，形成可复核的数据集与测试报告，为方法分析和结题成果整理提供支撑。'),
]
CONCISE_BODY=[
 '围绕南疆棉田膜下滴灌支管巡检需求，团队已完成文献梳理、双支路台架设计、参数化装配、诊断算法预研和本地巡检软件开发，并开展了泄漏、受限及正常扰动的合成仿真。',
 '台架方案由监测支路A和扰动支路B组成，两处压力测点包围受限区段，结合流量提取诊断特征，下游设置泄漏旁路与独立称量位置。已完成包含207个有效实体的参数化装配模型，明确了水路、电气和计量部件的布置。',
 '渐进泄漏的信号与判据演变如图8-1所示。在压力噪声标准差为3 kPa的初始K/R模型中，泄漏使流量上升、下游压力下降，出流特征K持续增加，阻力特征R保持波动。本例在403秒确认泄漏候选，比达到15%流量偏离的模型参照提前51秒。',
 '负载变化与测压漂移的特征轨迹如图8-2所示。未知正常负载增加与等效泄漏的轨迹重合，上游测压偏置也会抬高阻力估计。项目据此将操作记录、健康标定和人工复测纳入异常核查。',
 '候选方法的对照结果如图8-3所示。采用相同测量前端和确认条件，完成三档噪声下900条轨迹、2700条方法记录。压力噪声标准差为10 kPa时，稳健门限对泄漏和受限均为99/100条有效早期，固定门限分别为14/100和16/100；3470秒正常监测中，稳健门限有2/100条出现误报。有效早期按无前期误报、首次模式正确且早于15%模型参照统计，横线表示95%置信区间。',
 '故障幅值与正确提示比例的关系如图8-4所示。幅值扫描包含3000条故障轨迹和300条健康对照，以600秒内无前期误报且故障后首次候选正确为评价依据。压力噪声标准差为0.3 kPa时，5%泄漏有2/100条正确提示，10%泄漏为100/100，显示出小幅故障与较大故障的检出差异。阴影表示95%置信区间。',
 '采集次数与响应余量的对照如图8-5所示。每个场景以16组配对回放比较1、2、5秒巡航周期，点和误差线分别表示中位数与四分位区间。渐进泄漏中，1秒至5秒巡航的压力读取次数由471次降至330.2次，提前量由52.5秒变为51.5秒；切换期快泄漏较早触发1 Hz加密采集，读取次数下降较少。',
 '已完成便携C诊断内核、采集适配与主机回放工具。既有内核在216条合成轨迹、130,896次更新中，与参考程序的九字段输出一致。近期增加了10秒不重叠块CUSUM的门限与持续时间分析，采样程序已加入块边界更新逻辑。',
 '已形成遥测、事件与应答帧协议，完成编解码、分段接收、重复报文和缓存重发等主机测试。三类帧长度分别为55、57和24字节，设备会话、事件序号及接收确认均有对应记录。',
 '本地巡检平台的监测界面如图8-6所示，图示取自现有软件的回放运行。平台采用Python服务与SQLite存储，已完成Windows桌面封装，支持监测回放、三维测点查看、事件核查、历史查询和数据导出，并完成启动、保存和重启恢复检查。',
 '目前已具备水泵、稳压水源、电子秤和实验场地，配套的台架模型、接口分析、仿真程序及巡检软件已完成前期准备。硬件按单监测节点、单LoRa接收端和本地计算机配置，采用成品开发板及模块化接口。',
 '2027年3—4月将完成传感器标定、台架装配和节点采集联调，随后开展故障对照、LoRa收发及连续运行试验，同步保存参考测量、操作标签、原始采样和事件记录，形成试验数据集与测试报告。',
]
assert len(CONCISE_BODY)==sum(kind.startswith('body') for kind,_ in BLOCKS)
it=iter(CONCISE_BODY)
BLOCKS=[(kind,next(it) if kind.startswith('body') else text) for kind,text in BLOCKS]

CAPTIONS={
 'figure1':('图8-1 渐进泄漏的信号与判据演变',''),
 'figure2':('图8-2 负载变化与测压漂移的特征轨迹',''),
 'figure3':('图8-3 高噪声下候选方法的有效早期与正常误报',''),
 'figure4':('图8-4 故障幅值与正确提示比例',''),
 'figure5':('图8-5 采集次数与响应余量的关系',''),
 'figure6':('图8-6 本地巡检平台的压力与流量监测界面',''),
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
  if number==6:
   # Native Word picture crop of a verified existing screenshot. Original pixels
   # remain embedded unchanged; no redrawing, retouching or value replacement.
   picture=p.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.6),height=Cm(14.6*842/1432))
   fill=picture._inline.graphic.graphicData.pic.blipFill
   crop=OxmlElement('a:srcRect')
   for key,val in {'l':round(375/2561*100000),'t':round(518/1535*100000),'r':round((2561-375-1432)/2561*100000),'b':round((1535-518-842)/1535*100000)}.items():crop.set(key,str(val))
   fill.insert(1,crop)
  else:p.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.6))
  p._p.xpath('.//wp:docPr')[0].set('descr',caption)
  p=para(caption,9,True);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(6)
  md.extend([f'![{caption}](figures/{name}.png)',f'**{caption}**'])
 else:
  heading=kind in ['title','heading','heading_page']
  p=para(text,12 if kind=='title' else 11,heading,heading or kind=='body_page',kind in ['body_page','heading_page'])
  if kind.startswith('heading'):p.paragraph_format.space_before=Pt(5)
  md.append(('# ' if kind=='title' else '## ' if kind.startswith('heading') else '')+text)
target=B/'第八部分_正文融图与平台补图稿.docx';doc.save(target)
(B/'第八部分_已有基础_正文.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
plain=[]
for kind,text in BLOCKS:
 if kind.startswith('figure'):
  caption,note=CAPTIONS[kind];plain.append(f'〔此处插入{caption}〕')
 else:plain.append(text)
(B/'第八部分_已有基础_可复制正文.txt').write_text('\n\n'.join(plain)+'\n',encoding='utf-8-sig')
audit=dict(input_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
 body_characters=sum(len(t) for k,t in BLOCKS if k.startswith('body')),sections=3,figure_count=6,figure_files_unchanged=True,
 original_attachment_figures_discarded=True,legacy_integer_equivalence_distinguished_from_current_block_research=True,
 figures=[dict(name=name,sha256=hashlib.sha256((B/'figures'/f'{name}.png').read_bytes()).hexdigest()) for name in NAMES])
audit['screenshot_source']=str(SCREENSHOT.relative_to(ROOT));audit['screenshot_original_sha256']=hashlib.sha256(SCREENSHOT.read_bytes()).hexdigest()
audit['screenshot_native_word_crop_xywh']=[375,518,1432,842];audit['standalone_notes_removed']=True
assert all(hashlib.sha256((B/'figures'/f'{n}.png').read_bytes()).digest()==hashlib.sha256((OLD/'figures'/f'{n}.png').read_bytes()).digest() for n in NAMES[:5])
assert hashlib.sha256((B/'figures'/f'{NAMES[-1]}.png').read_bytes()).digest()==hashlib.sha256(SCREENSHOT.read_bytes()).digest()
(ROOT/'tmp/section8_integrated/build_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(target);print('Body characters',audit['body_characters'])
