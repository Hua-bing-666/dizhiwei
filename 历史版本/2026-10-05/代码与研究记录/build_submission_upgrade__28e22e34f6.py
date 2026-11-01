"""Narrow, template-preserving edit of the user's current native-math DOCX."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
from PIL import Image
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'deliverables/11.docx'
OUT=ROOT/'deliverables/大创申报书_系统方案完善稿.docx'
DATA=ROOT/'application/submission_upgrade';DATA.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp/submission_document_review';TMP.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
original=SRC.read_bytes()
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}';R='{'+NS['r']+'}';V='{'+NS['v']+'}'
tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
alltx=lambda p:''.join(p.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))
(TMP/'artifact.md').write_text(f'''Artifact: edit of {SRC}\nSource SHA256: {sha(original)}
Preserve: school cover, A4 page settings, outer 31 rows, blank personal/teacher fields,
approval areas, 27 native math objects, user changes to software-copyright schedule.
Changes: nine revised images plus unchanged platform image; causal sampling evidence;
planned adaptive acquisition and simulated control; blank budget; centered tables/captions.
Quality: review every final rendered page; no clipping, stretched image, overlapping labels,
incorrect arrow direction, false hardware/energy claims. Source file must stay byte-identical.
''',encoding='utf-8')
with ZipFile(SRC) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
root=E.fromstring(parts['word/document.xml']);rels=E.fromstring(parts['word/_rels/document.xml.rels'])
outer=root.find(W+'body/'+W+'tbl');rows=outer.findall(W+'tr')
before_math=[E.tostring(x) for x in root.xpath('.//m:oMath',namespaces=NS)]
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(25,31))}
changes=[]
sample=next(p for p in rows[18].xpath('.//w:p',namespaces=NS) if tx(p).startswith('位置提示采用'))

def run(value,bold=False):
 r=E.Element(W+'r');pr=E.SubElement(r,W+'rPr');f=E.SubElement(pr,W+'rFonts')
 for key in ('ascii','hAnsi','eastAsia'):f.set(W+key,'宋体')
 for key in ('sz','szCs'):E.SubElement(pr,W+key).set(W+'val','21')
 if bold:E.SubElement(pr,W+'b')
 t=E.SubElement(r,W+'t');t.text=value;return r
def new_p(value):
 p=deepcopy(sample)
 for c in list(p):
  if c.tag!=W+'pPr':p.remove(c)
 p.attrib.clear();p.append(run(value))
 return p
def body_replace(row_index,prefix,value):
 found=[p for p in rows[row_index].xpath('.//w:p',namespaces=NS) if tx(p).startswith(prefix)]
 assert len(found)==1,(row_index,prefix,len(found))
 p=found[0];assert not p.xpath('.//m:oMath',namespaces=NS),prefix
 # Headings and manual line breaks remain intact. Replace only body text.
 texts=p.xpath('./w:r/w:t',namespaces=NS)
 if p.xpath('./w:r/w:br',namespaces=NS):
  body=texts[-1];before=body.text;body.text=value
 else:
  before=tx(p)
  for c in list(p):
   if c.tag!=W+'pPr':p.remove(c)
  p.append(run(value))
 changes.append(dict(prefix=prefix,before=before,after=value))
 return p
def insert_after(p,values):
 parent=p.getparent();idx=parent.index(p)+1
 added=[]
 for value in values:
  node=new_p(value);parent.insert(idx,node);idx+=1;added.append(node)
 return added

body_replace(16,'一、项目简介',
 '本项目面向南疆规模化棉田膜下滴灌的支管巡检需求，研究泄漏与局部过流受限的早期识别，研制集压力与流量采集、LoRa无线传输、异常诊断和巡检管理于一体的物联网原型系统。针对供压波动、轮灌切换与渐进故障容易混淆的问题，建立双压力—流量联合特征及运行工况约束下的诊断方法，将异常提示关联到监测支管和测点区段。在此基础上研究事件触发分级采集，设计自动与人工控制请求、模拟执行及执行器接口。通过双支路清水台架、独立参考测量和无线对照试验，评价故障检出、误报、有效提前量与远端告警延迟，形成原型、实验数据及研究报告，为后续棉田分区监测和支管隔离控制提供基础。')
body_replace(18,'总体目标是',
 '总体目标是研制一套能够采集支管状态、识别异常、可靠传输并支持巡检处置的物联网原型系统。系统由双压力—流量感知节点、LoRa接收端和本地Web平台组成，按“参考标定与健康建模—工况约束诊断—分级采集与事件传输—处置记录与复核”组织技术路线。研究任务围绕两个问题展开：联合观测能在何种误差和运行条件下改善故障识别；调整采集与上报节奏时，异常响应和资源开销如何变化。双支路清水台架承担可重复验证，控制联动采用软件模拟与执行接口预留，使感知、诊断和处置逻辑在同一系统中衔接。')
body_replace(18,'图1给出了',
 '图1给出了系统职责和数据交互。节点承担采集调度、初步诊断、事件缓存和模拟控制输出；接收模块以串口桥接方式连接计算机，接收服务完成校验、去重和SQLite事务存储，Web平台保存巡检及指令状态。参考测量和故障操作标签独立于诊断程序，用于检验输出是否正确。数据提交后的接收确认、模拟指令反馈和人工维护归档分别记录，避免将信息到达解释为实际阀门动作或维护完成。')
anchor=next(p for p in rows[18].xpath('.//w:p',namespaces=NS) if tx(p).startswith('实际滴灌管具有'))
added=insert_after(anchor,[
 '在固定周期采集完成标定和诊断基线后，研究由运行变化触发的分级采集策略。节点正常运行时保留周期测量与连续脉冲计数；观测相对健康参照出现持续偏离后，切换至较短读取周期，并延长异常观察时间。稳定恢复且保持时间结束后返回正常监测。触发采用累计偏离与特征变化，兼顾渐进故障，避免仅凭相邻差值判断。变化触发用于调整采集节奏，故障分类仍按数据质量、运行工况和持续确认流程完成。',
 '采集、完整记录和无线发送分别配置。台架以1秒读取建立高频基线，正常监测设置5、10、30、60秒候选，并以更长周期检查迟检边界；异常加密阶段以1秒为初始设置，正常状态上报采用60秒候选。周期根据故障发展时间、误触发和监测开销选择，不预设统一的分钟级读取要求。流量保持10秒计数窗口，保存真实窗口及压力转换时刻；判定按经过时间和实际观测次数确认，不将休眠期间的未测数据填充成连续观测。图5给出分级采集与模拟处置的衔接。',
 '采集策略采用固定高频、固定低频、仅改变上报周期和分级采集四组对照。使用相同健康参照、特征阈值和故障操作，改变故障相对于监测周期的出现时刻，分别评价误触发、漏检、首次正确提示及有效提前量。记录压力转换、计数窗口更新、完整记录和发送次数，将持续监测开销计入比较；实物阶段以相同供电和运行时长测量整机电流或能量。减少记录或发送次数的结论与能耗结论分别给出，依据独立批次确定适用范围。'])

platform=body_replace(18,'联调按照',
 '联调按照有线采集、无线收发、接收服务、Web显示的顺序进行。以同一异常事件贯穿采集、判定、发送、存储、显示和人工复测，核对各环节时刻与内容。系统验收至少完成两类故障的核查及处置复测、一次误报核查、一次8小时连续记录和至少3次重启恢复，并核对自动与人工模拟请求的状态，形成可检查的测量、通信及操作记录。')
insert_after(platform,[
 '控制联动用于验证异常提示与处置流程的衔接，本期以LED或蜂鸣器演示，保留人工操作。普通候选告警提供巡检依据；数据有效、工况明确并满足另行设置的保护条件时，生成包含支管身份、原因和唯一序号的自动请求。人工与自动请求使用同一状态记录，接收确认、演示输出和人工复位分别核验，重复命令不产生重复输出。页面与日志标明模拟模式，未接入真实节点时仅显示请求已生成，不显示已下发或阀门已关闭。',
 '节点预留控制输出、驱动接口与反馈输入，接口方案用于后续接入执行器。真实阀门作为延伸任务，依据管径、工作压力和反馈方式匹配驱动，在A支路入口、上游压力测点之前布置隔离执行器；核验到位反馈、实际止流和对B支路的影响后，再开展保护效果评价。诊断数据采集与控制验证分开组织，不以原有15%水力参照直接设定农业关阀标准，使原诊断路线和独立实验条件保持可比。'])
body_replace(19,'在通信策略方面',
 '在事件策略方面，Lozoya等以土壤水分和过程模型预测下一次采集时刻，比较了非周期采集与周期方案的通信和能量取舍[8]，其研究对象为山核桃灌溉，链路采用IEEE 802.15.4/Zigbee。本项目借鉴分开评价控制效果、消息数量和实测能耗的思路，围绕支管压力与流量异常设计周期监测后的事件触发，不直接沿用土壤水分的分钟级采集周期。采集调度、数据上报和接收确认分别设置对照，分析通信负担下降是否伴随告警等待、误触发或数据缺口。')
body_replace(19,'结合上述研究',
 '结合上述研究，本项目拟形成两方面增量：一是以双压力—流量测量和轮灌状态为依据，研究渐进泄漏与局部受限的可辨识范围，在误报约束下评价有效提前量；二是研究事件触发分级采集与可靠上报的协同，分析减少观测和通信负担时的异常响应代价。控制请求模拟作为系统实现任务，以功能和过程记录体现集成贡献。通过独立标定、正常干扰对照、留出批次及失败实例，形成可复核的方法结论及原型。')
body_replace(20,'（3）',
 '（3）与故障响应对应的事件采集与可靠告警。拟将健康参照偏离、运行变化及持续确认用于采集调度，分别评价触发监测、完整记录和无线发送的开销。以固定周期和仅调整上报等方案为对照，研究记录及通信负担与有效提前量、误触发、漏检之间的取舍；事件持久化、接收确认和队列调度共同约束远端及时性。以同一事件贯穿观测、模拟请求、人工核查和复测，为真实隔离控制与多支管巡检保留接口。')
body_replace(21,'六、项目预期成果',
 '完成1套支管故障诊断物联网原型，包括一个双压力—流量感知节点、一个LoRa接收端、双支路清水台架及本地Web平台。实现数据采集、分级调度、异常候选提示、事件接收存储、巡检复测和控制请求模拟，配套提交连接与结构设计、执行接口方案、程序、操作说明及结题报告。控制演示采用LED或蜂鸣器输出及日志核验，原型以单监测单元完成可演示、可复核的功能验证。')
body_replace(21,'形成标定',
 '形成标定、健康关系、故障操作、正常干扰、采集策略、无线对照和连续恢复等实验数据。按计划完成54次主要故障操作及表2所列对照，保存参考值、配置、缺失和失败记录；建立图表与原始批次的对应关系，形成测量适用范围、故障识别及采集通信取舍的研究报告。数据采集与分析遵循正式验证前固定方法和评价规则的要求。软件成果按实际开发内容整理著作权申请材料。')
body_replace(21,'形成1篇',
 '形成1篇以实测数据为基础的研究论文稿，围绕跨工况故障辨识或事件采集策略开展分析，完成基线、消融及统计评价后投稿。项目按2027年3月至2028年2月完成原型和研究报告，论文按真实进度投稿与修订，录用、发表结果据实际证明登记。')
body_replace(22,'七、项目年度目标',
 '项目周期为2027年3月至2028年2月。2027年完成台架与节点、诊断及采集策略对照、无线与平台联调，形成数据和软件成果；2028年1—2月补验证并结项。阶段交付按表3核验，正式评价前固定方法和数据版本，论文以实测结果组织。')
body_replace(22,'申报阶段重点',
 '申报阶段重点完成研究对象、系统结构和验证方法，以可复现模型、接口设计及现有软件支撑可行性；立项后以台架和真实链路形成工程与研究证据；论文阶段围绕已验证的问题提炼贡献。三个阶段保持任务递进，仿真用于前期分析，实测用于原型验收和主要性能结论。')

# New evidence is host replay/mock only; original results and counterexamples stay unchanged.
last=next(p for p in rows[23].xpath('.//w:p',namespaces=NS) if tx(p).startswith('离线Web已实现'))
insert_after(last,[
 '事件采集已完成基于上述480条合成观测的四策略配对回放，形成1920条策略结果，并检查调度不读取未采样或未来观测。回放采用相同标定区间、10秒因果窗口及至少两次真实观测、经过5秒的确认条件；其确认定义与前述连续5样本基线分别记录。以压力随机噪声0.3kPa、故障相位固定的模型条件为例，高频方案在监测区间读取471次，分级方案在正常、泄漏、受限场景平均读取218.2、393.2、399.8次；两故障各20条回放均在参照前提示。固定60秒读取的泄漏组为0/20有效早期，表明周期选择存在响应代价。',
 '另对5至600秒监测周期改变首次监测相位开展敏感性回放。周期为300秒时，两类故障合计98/240条相位回放满足有效早期条件，600秒为18/240；同一基础噪声轨迹被重复使用，这些记录不作为独立实验数量。正常B支路切换会提高分级方案的采集和发送负担；仅改变上报的方案未减少读取，在当前回放中也比同时加密发送的分级方案更少发送。上述结果用于确定候选设置，尚不能给出最优周期、整机节电或突发故障保证。',
 '控制方面已完成12项主机模拟检查，覆盖正常及证据不足不自动请求、命令去重、内容冲突、支管身份核对、接收与演示输出区分及人工复位。当前程序只验证主机模拟状态，不涉及真实STM32固件、IO输出或阀门动作；节点控制与页面接入将在原型联调中实现。采集回放和控制检查分别保存参数、结果及程序版本，作为实施前的逻辑验证依据。'])

# Add strategy/control requirements to existing work packages and schedule.
substitutions={
 '诊断程序、干扰对照及独立故障数据':'诊断与分级采集程序、独立故障及干扰对照',
 '试次级误报、漏检、模式正确性及有效提前量':'误报、漏检、模式正确性、提前量及实际读取次数',
 '六模块Web、真实接入及维护记录':'六模块Web、真实接入、模拟请求及维护记录',
 '事件全过程可追溯；连续记录、重启和故障复测':'事件与指令状态可追溯；连续记录、重启及复测',
 '诊断程序、独立故障及正常干扰实验':'诊断与分级采集、独立故障及正常干扰对照',
 '无线收发、接收服务、Web及处置复测':'无线收发、Web接入、模拟控制及处置复测',
}
for ri in (18,22):
 for p in rows[ri].xpath('.//w:p',namespaces=NS):
  if tx(p) in substitutions:
   old=tx(p);ts=p.xpath('.//w:t',namespaces=NS);ts[0].text=substitutions[old]
   for t in ts[1:]:t.text=''

# Add planned trials as rows of the existing experimental table, not a separate table.
def content_tables(row):
 return [t for t in row.xpath('.//w:tbl',namespaces=NS)
         if len(t.find(W+'tr').findall(W+'tc'))>=3]
tables=content_tables(rows[18])
assert len(tables)==2
experiments=next(t for t in tables if '层次' in tx(t.find(W+'tr')))
for values in [
 ['采集调度对照','54次故障操作和18次正常对照配套高频参考记录；分块交叉配置复核','4策略、候选周期及相位对照；统计读取/发送与提前量，不新增为独立操作数'],
 ['模拟控制流程','至少12类状态检查；主机检查后开展节点与页面联调','自动/人工、去重、质量与工况约束、模拟反馈及人工复位；真实阀门不列为本期必做'],
]:
 row=deepcopy(experiments.findall(W+'tr')[-1])
 for cell,value in zip(row.findall(W+'tc'),values):
  ps=cell.findall(W+'p');p=ps[0]
  for c in list(p):
   if c.tag!=W+'pPr':p.remove(c)
  p.append(run(value))
  for old in ps[1:]:cell.remove(old)
 experiments.append(row)
# Remove inherited bottom rules from now-intermediate experiment rows.
for row in experiments.findall(W+'tr')[1:-1]:
 for bottom in row.xpath('./w:tc/w:tcPr/w:tcBorders/w:bottom',namespaces=NS):
  bottom.set(W+'val','nil')

# Keep the school budget slot entirely blank, with its original section heading.
cell=rows[24].find(W+'tc');first=cell.find(W+'p');header=deepcopy(first)
for c in list(header):
 if c.tag!=W+'pPr':header.remove(c)
header.append(run('九、项目经费使用计划',True))
# The inherited placeholder used an exact 1 pt line; real heading text was clipped.
header.find(W+'pPr/'+W+'spacing').attrib.update({W+'line':'240',W+'lineRule':'auto'})
for c in list(cell):
 if c.tag!=W+'tcPr':cell.remove(c)
cell.append(header);cell.append(new_p(''))
h=rows[24].find(W+'trPr/'+W+'trHeight');h.set(W+'val','1700');h.set(W+'hRule','atLeast')

# Renumber existing figures once, then insert the strategy image at the acquisition section.
for t in root.xpath('.//w:t',namespaces=NS):
 if t.text:t.text=re.sub(r'图([5-9])(?!\d)',lambda m:'图'+str(int(m[1])+1),t.text)
for t in added[1].xpath('.//w:t',namespaces=NS):
 if t.text:t.text=t.text.replace('图6给出分级采集','图5给出分级采集')
relmap={e.get('Id'):e.get('Target') for e in rels}
figure_map={1:'system_responsibilities',2:'water_layout',3:'collection_overview',4:'measurement_interfaces',
            6:'diagnosis_proposal',7:'durable_event_sequence',9:'noise_outcomes_print',10:'failure_counterexamples'}
fig1=next(p for p in root.xpath('.//w:p',namespaces=NS) if tx(p).startswith('图1 '))
f=deepcopy(fig1);f.attrib.clear()
shape=f.find('.//'+V+'shape');shape.set('id','_x0000_i1305')
rid='rIdUpgradeStrategy'
im=f.find('.//'+V+'imagedata');im.set(R+'id',rid);im.set('{urn:schemas-microsoft-com:office:office}title','event_sampling_strategy')
rel=E.SubElement(rels,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',Id=rid,
                 Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',Target='media/event_sampling_strategy.png')
relmap[rid]='media/event_sampling_strategy.png'
f.xpath('.//w:t',namespaces=NS)[0].text='图5 事件触发分级采集与模拟处置逻辑'
added[1].getparent().insert(added[1].getparent().index(added[1])+1,f)
figure_map[5]='event_sampling_strategy'
replaced=[]
for p in root.xpath('.//w:p',namespaces=NS):
 cap=tx(p);match=re.match(r'^图(\d+)\s',cap)
 if not match:continue
 n=int(match[1]);image=p.find('.//'+V+'imagedata');shape=p.find('.//'+V+'shape')
 assert image is not None,(n,cap)
 if n in figure_map:
  png=ROOT/'application/figures/submission_upgrade'/f'{figure_map[n]}.png'
  part='word/'+relmap[image.get(R+'id')];parts[part]=png.read_bytes()
  with Image.open(png) as img:w,h=img.size
  shape.set('style',f'height:{420*h/w:.3f}pt;width:420pt;')
  shape.set('alt',cap)
  replaced.append(dict(figure=n,part=part,png=png.relative_to(ROOT).as_posix(),sha256=sha(parts[part]),height_pt=420*h/w))
 # Captions and pictures remain in one centered paragraph.
 for sz in p.xpath('.//w:sz',namespaces=NS):sz.set(W+'val','21')
 spacing=p.find(W+'pPr/'+W+'spacing')
 if spacing is not None:
  spacing.attrib.pop(W+'beforeLines',None);spacing.set(W+'before','0')

assert len(replaced)==9
# Each inline figure and its caption form one non-splitting table row.
# WPS can otherwise split a tall paragraph inside an existing layout cell.
for p in list(root.xpath('.//w:p',namespaces=NS)):
 if not re.match(r'^图\d+\s',tx(p)) or p.find('.//'+V+'imagedata') is None:continue
 parent=p.getparent();pos=parent.index(p)
 table=E.Element(W+'tbl');pr=E.SubElement(table,W+'tblPr')
 E.SubElement(pr,W+'tblW').attrib.update({W+'w':'9070',W+'type':'dxa'})
 E.SubElement(pr,W+'jc').set(W+'val','center')
 E.SubElement(pr,W+'tblLayout').set(W+'type','fixed')
 borders=E.SubElement(pr,W+'tblBorders')
 for edge in ('top','left','bottom','right','insideH','insideV'):
  E.SubElement(borders,W+edge).set(W+'val','nil')
 margins=E.SubElement(pr,W+'tblCellMar')
 for edge in ('top','left','bottom','right'):
  E.SubElement(margins,W+edge).attrib.update({W+'w':'0',W+'type':'dxa'})
 grid=E.SubElement(table,W+'tblGrid');E.SubElement(grid,W+'gridCol').set(W+'w','9070')
 tr=E.SubElement(table,W+'tr');trpr=E.SubElement(tr,W+'trPr');E.SubElement(trpr,W+'cantSplit')
 tc=E.SubElement(tr,W+'tc');tcpr=E.SubElement(tc,W+'tcPr')
 E.SubElement(tcpr,W+'tcW').attrib.update({W+'w':'9070',W+'type':'dxa'})
 parent.remove(p);tc.append(p);parent.insert(pos,table)
 # Word requires a paragraph after a trailing nested table.
 if pos==len(parent)-1:
  tail=new_p('');tail.find(W+'pPr/'+W+'spacing').set(W+'after','0');parent.append(tail)
after_math=[E.tostring(x) for x in root.xpath('.//m:oMath',namespaces=NS)]
assert after_math==before_math and len(after_math)==27
for i,b in protected.items():assert E.tostring(rows[i])==b,('protected template row',i)
assert len(outer.findall(W+'tr'))==31
assert len(root.xpath('.//w:p[w:r/w:t[starts-with(text(),"[1]")]]',namespaces=NS))==1
bodytext=alltx(root)
assert '2000元' not in bodytext and '经费估算' not in bodytext
assert '关键边界补实验及软著申请' in bodytext
assert not re.search('老师.{0,5}待确认|职称待确认',bodytext)
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[\d\]',tx(p))]
assert len(refs)==8
for table in tables+content_tables(rows[22]):
 pr=table.find(W+'tblPr');assert pr is not None
 jc=pr.find(W+'jc')
 if jc is None:jc=E.SubElement(pr,W+'jc')
 jc.set(W+'val','center')
 indent=pr.find(W+'tblInd')
 if indent is not None:indent.set(W+'w','0');indent.set(W+'type','dxa')
 for p in table.findall(W+'tr')[0].xpath('.//w:p',namespaces=NS):
  pr=p.find(W+'pPr')
  if pr is None:pr=E.SubElement(p,W+'pPr')
  jc=pr.find(W+'jc')
  if jc is None:jc=E.SubElement(pr,W+'jc')
  jc.set(W+'val','center')
for p in root.xpath('.//w:p',namespaces=NS):
 if re.match(r'^(图|表)\d+\s',tx(p)):
  pr=p.find(W+'pPr');jc=pr.find(W+'jc')
  if jc is None:jc=E.SubElement(pr,W+'jc')
  jc.set(W+'val','center')
  ind=pr.find(W+'ind')
  if ind is not None:pr.remove(ind)
parts['word/document.xml']=E.tostring(root,encoding='utf-8',xml_declaration=True,standalone=True)
parts['word/_rels/document.xml.rels']=E.tostring(rels,encoding='utf-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
 for k,b in parts.items():z.writestr(k,b)
assert SRC.read_bytes()==original
record=dict(source=SRC.relative_to(ROOT).as_posix(),source_sha256=sha(original),output=OUT.relative_to(ROOT).as_posix(),
            output_sha256=sha(OUT.read_bytes()),native_math_count=27,native_math_unchanged=True,
            protected_rows_unchanged=True,personal_fields_blank=True,budget_blank=True,
            references=refs,figure_replacements=replaced,changes=changes,physical_validation=False)
(DATA/'build_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paras=[alltx(p) for row in rows[16:25] for p in row.xpath('.//w:p',namespaces=NS) if alltx(p)]
(DATA/'body.txt').write_text('\n\n'.join(paras)+'\n',encoding='utf-8')
print('Created new application: 27 original math objects; 10 figures, 3 centered body tables, budget blank. Render pending.')
