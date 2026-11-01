"""Update the existing execution book while retaining its section and style system."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
from PIL import Image
import io,re,json,hashlib
R=Path(__file__).resolve().parents[1];S=R/'deliverables/实施项目书.docx';D=R/'deliverables/实施项目书_现阶段更新稿.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}';tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS));sha=lambda b:hashlib.sha256(b).hexdigest();changes=[]
source=S.read_bytes()
with ZipFile(io.BytesIO(source)) as z:parts={n:z.read(n) for n in z.namelist()}
original=parts.copy();root=E.fromstring(parts['word/document.xml']);body=root.find(W+'body')
def find(prefix):
 a=[p for p in body.findall(W+'p') if tx(p).startswith(prefix)];assert len(a)==1,(prefix,len(a));return a[0]
def fill(p,text):
 before=tx(p);runs=p.findall(W+'r');pr=deepcopy(runs[0].find(W+'rPr')) if runs and runs[0].find(W+'rPr') is not None else None
 for c in list(p):
  if c.tag!=W+'pPr':p.remove(c)
 if text:
  r=E.SubElement(p,W+'r')
  if pr is not None:r.append(pr)
  E.SubElement(r,W+'t').text=text
 changes.append({'before':before,'after':tx(p)})
def replace(prefix,text):fill(find(prefix),text)
replace('编制日期：','编制日期：2026年10月7日')
replace('负责人、指导教师','')
replace('本书供负责人','本书用于安排原型研制、独立试验和研究成果整理。项目以南疆规模化棉田膜下滴灌支管巡检为应用对象，完成一个双压力—流量节点、LoRa接收端、双支路清水台架及本地桌面巡检软件，形成可重复验证的系统和实测论文稿。实施周期为2027年3月至2028年2月，任务与申报书保持一致。')
replace('本书为自主编制','本书为实施规划。立项后的正式任务书按学校当批模板填写，批准的研究内容、周期和成果要求作为实施依据。')
replace('输入为同一份冻结本地','通信联调使用同一份本地检测日志、事件身份及E220配置。先实现节点日志和恢复，再以有线方式核验V2帧、CRC16、COBS与提交确认，最后接入LoRa射频。重试次数、事件有效期及队列容量作为配置保存，联调时核验时序和恢复过程。')
replace('围绕低成本双压力','项目研究两类变化：支管接头或管路泄漏，以及两个压力测点之间的局部过流受限。以压力—流量健康关系为参照，在供压调整、轮灌和负载切换对照中评价异常提示；进一步比较事件触发采集与可靠上报的响应和通信开销。系统提示支管及检查区段，具体漏点和原因由现场核查确认。')
replace('基础交付限定','系统包括一个P₀/P₁/Q感知诊断节点、一个E220接收桥、PC本地服务与SQLite数据库、八页巡检软件和双支路清水台架。A支路测量和注入故障，B支路模拟同源健康负载切换。控制采用软件请求与LED或蜂鸣器演示，预留执行接口；多节点和真实阀门作为后续任务。')
replace('在可测且工况可比','在标定确认的范围内，力争使10%和15%故障组首次持续候选正确比例达到90%，正常确认误报不高于1次/小时，并评价达到15%试验参照前的有效提示比例。5%组用于探索小幅变化的识别边界。预实验确定可用范围和参数，正式评价采用未参与调参的独立批次，保留漏检和失败结果。')
replace('当前480个合成试次','现有诊断比较支持优先选择稳健门限与连续确认。合成回放覆盖不同噪声、渐进故障和正常对照，便携C内核与主机参考程序已完成输出核对；未知负载和压力漂移反例说明，门限不能替代工况信息。实物阶段据此安排健康标定、正常切换和跨负载留出试验。')
replace('199个有效实体','当前台架概念模型含207个有效实体，完成新增防溅板交集与局部间隙检查，支持测点、电气和计量布局查看。C回放、Python服务、SQLite和八页平台已贯通，桌面封装支持历史恢复与原生导出。上述为设计和主机软件基础，实物标定、节点运行、射频及田间应用在实施阶段验证。')
replace('节点保存原始采样','节点采集压力与累计计数，保存观测质量、工况和异常事件。LoRa模块桥接无线字节，PC服务校验、去重并写入SQLite，提交成功后回复ACK。桌面平台读取同一会话，追加查看、处置和复测记录。接收确认、人工核查和模拟执行分别保存，避免混淆不同环节的状态。')
replace('拟统一事件身份','事件身份由设备、会话和序号组成，关联健康参照、配置与试次ID。原始测量、判断、发送和接收提交分别记录时间；跨设备比较注明同步方法，未同步时按同设备时钟或区间评价延迟。')
replace('拟每1秒记录','固定1 Hz为主线，节点保存压力与累计脉冲，采用10秒窗计算流量。540 pulse/L的模型脉冲系数对应每脉冲约0.01111 L/min的10秒窗流量步长；实际系数由参考流量标定。压力转换、计数锁存、缺测和时钟偏差随记录保存，在突变与复位检查中核验时间对应关系。')
replace('候选空腔几何容量','泄漏计量按20秒分次取样，容器安全液位以下的实测有效容量不低于440 mL。使用前检查自由出流、飞溅与出口淹没，并按实际最大泄漏量核验容量余量；8小时记录另设排水，避免容器液位改变试验水力条件。')
replace('候选采用STM32','节点采用STM32F103C8T6、两路0—200 kPa两线制4—20 mA压力变送器、ADS1115、SEN0549、microSD和E220模块的设计配置。采购时以量程、精度、输出方式和安装尺寸核对型号，压力测量按±0.25%FS等级提出要求。主控资源按64 KB Flash和20 KB SRAM规划，目标编译与连续日志检查后确认实际占用。')
replace('本图中的75%','分级采集以2秒、5秒巡航间隔作为对照，发生持续偏离后切换至1秒读取，稳定后返回巡航；累计脉冲持续计数。压力读取与无线发送分别配置，正常上报以60秒为候选，异常优先发送。固定高频、固定低频、仅调整上报及分级采集四组在相同故障记录上比较，读取次数和实测电流分别报告。')
replace('输入为通过WP1','输入为已标定的适用范围、原始日志、独立参考、阀态及健康参照。节点采用相对流量残差与区段阻力残差，结合健康波动估计的稳健门限进行判断。十秒主窗同类候选连续五次成立输出持续候选，三秒短窗连续两次正向越限形成关注提示。固定1 Hz先完成实测，再开展分级采集对照。')
replace('交付包括冻结协议','交付健康曲线、门限与程序版本、54次主要故障、18次正常干扰、12次切换期故障及逐试次评价。所有方法使用相同观测和试次，比较固定门限、稳健门限与累积判据组合；再去掉压力测点或工况信息，评价各部分的作用。按日期、供压或负载批次留出，不拆分相邻采样点作为独立验证。')
replace('退出条件是每次操作','验收时核对独立操作与参考测量、窗口有效性、首次正确持续候选和15%参照时刻。误报、漏检、先错后对和迟检均计入。参照适配比较固定曲线、多供压重新标定及少量健康数据修正，以独立批次评价效果和标定工作量；未知负载同形时保留异常待检查。')
replace('输入为真实串口','本地平台已具备八页结构、数据库及桌面封装，实施中接入真实串口和LoRa数据。总览提示待处理工作，监测页显示压力与流量，事件页记录核查，历史页检索与导出；实验页组织策略和标定，台架页查看测点与结构。页面共享同一会话和候选快照，断连时区分历史读数与当前状态。')
replace('交付包括启动说明','交付节点与前后端程序、桌面EXE、连接说明、数据库结构、接口映射及操作记录。完成两类故障处置复测、误报核查、一次8小时台架运行和至少3次重启，检查采样缺失、事件恢复及记录一致性。界面覆盖375、1024、1440宽度，并核验键盘操作、保存取消和实际导出文件。')
replace('退出条件为同一事件','验收以同一事件的采集、判断、传输、保存和人工记录能够对应为准。核查不改原候选快照，只有已处置并取得符合条件的复测记录后才归档。模拟控制检查请求、接收、演示输出及复位，先在主机验证状态，再联调节点IO。')
replace('预算以已有电脑','经费表保留空位，获批后按学校科目与实际报价填写。器件选择首先核对量程、精度、接口及参考测量能力；现有电脑、可调水源和独立参考仪器列入资源落实清单。')
replace('正式任务书经费','采购前核对供水的连续压力—流量工作点、传感器安装尺寸和安全输入范围。报价、借用记录、批准经费及实际支出分别保存，调整任务时同步更新实施安排。')
replace('时间是当前内部计划','实施按2027年3月至2028年2月安排。立项后对照批准任务细化节点；论文投稿和修订结合独立数据进度推进，录用与收录按真实证明登记。')
replace('结项包至少包含','结项包包含原型演示、硬件连接与标定、诊断和无线对照、连续恢复、维护复测、程序、数据和研究报告。提交前按批准任务逐项核对功能、实验和成果，补齐缺项及说明。')
replace('主论文优先研究','主论文优先研究双压力—流量诊断的健康参照适配。围绕供压和负载规律变化，对比固定参照、多供压点标定及健康数据修正，配合正常干扰、独立故障和跨日留出，评价误报、漏检和有效提前量。保留未知负载和漂移失败条件，使结论对应明确的信息与工作范围。')
replace('若测量信息增量不足','事件触发采集可作为另一研究方向：在相同诊断规则和故障条件下，比较固定高频、固定低频、仅调整上报和分级采集，分析观测次数、及时性及正常切换误触发。通信侧再对比事件优先与有限重试。能耗结论以整机电压、电流积分为依据，论文选择一个具有充分独立数据的问题深入展开。')
for prefix in ['3 科研积分','用户提供的当年','按该参考口径','项目成果状态单独']:
 p=find(prefix);body.remove(p)
replace('八 官方任务书','八 正式任务对应')
replace('中文11篇','申报书保留8篇参考文献，其中中文5篇、英文3篇，分别支撑棉田应用对象、水力观测、LoRa系统和事件策略。实施资料按测量、诊断、采集、通信、软件与模型归档，使研究方法、程序和试验记录能够互相核对。')
p=find('模型版本为');changes.append({'before':tx(p),'after':'','reason':'Version details already retained in the accompanying software records.'});body.remove(p)

# Apply six centered, editable table layouts without forcing each table to one page.
tables=body.findall(W+'tbl')
captions=['表1 三阶段目标与交付','表2 独立实验安排','表3 经费使用计划','表4 实施进度与阶段验收','表5 主要问题与处理','表6 正式任务书填写对应']
for i,table in enumerate(tables):
 pr=table.find(W+'tblPr')
 for e in list(pr):
  if e.tag==W+'tblInd':pr.remove(e)
 jc=pr.find(W+'jc')
 if jc is None:jc=E.SubElement(pr,W+'jc')
 jc.set(W+'val','center')
 margins=pr.find(W+'tblCellMar')
 if margins is None:margins=E.SubElement(pr,W+'tblCellMar')
 for side,value in [('left','100'),('right','100'),('top','70'),('bottom','70')]:
  e=margins.find(W+side)
  if e is None:e=E.SubElement(margins,W+side)
  e.set(W+'w',value);e.set(W+'type','dxa')
 for ri,row in enumerate(table.findall(W+'tr')):
  for p in row.xpath('.//w:p',namespaces=NS):
   pp=p.find(W+'pPr')
   if pp is None:pp=E.SubElement(p,W+'pPr')
   kn=pp.find(W+'keepNext')
   if kn is None:kn=E.SubElement(pp,W+'keepNext')
   kn.set(W+'val','1' if ri==0 else '0')
   if ri==0:
    align=pp.find(W+'jc')
    if align is None:align=E.SubElement(pp,W+'jc')
    align.set(W+'val','center')
 caption=E.Element(W+'p');cp=E.SubElement(caption,W+'pPr');E.SubElement(cp,W+'jc').set(W+'val','center');E.SubElement(cp,W+'keepNext').set(W+'val','1');E.SubElement(cp,W+'spacing',attrib={W+'before':'120',W+'after':'70'})
 cr=E.SubElement(caption,W+'r');E.SubElement(cr,W+'t').text=captions[i];body.insert(body.index(table),caption)
 if tx(table).startswith('用途'):
  for p,value in zip(table.find(W+'tr').xpath('.//w:p',namespaces=NS),['用途','金额 元','说明']):fill(p,value)
  rows=table.findall(W+'tr');blank=deepcopy(rows[1])
  for old in rows[1:]:table.remove(old)
  for n in range(4):
   row=deepcopy(blank)
   for p in row.xpath('.//w:p',namespaces=NS):fill(p,'')
   table.append(row)

# Update progress and resource tables; remove fabricated administrative placeholders.
for p in root.xpath('.//w:p',namespaces=NS):
 s=tx(p)
 replacements={'本地六模块Web':'本地八页巡检软件','Web及连续恢复':'桌面平台及连续恢复','独立故障和正常对照、门控、基线与留出协议':'故障与正常对照、分级采集及参照适配','待真实':'','待确认':'','按分工':'按工作任务'}
 for a,b in replacements.items():
  if a in s and not p.xpath('.//w:drawing',namespaces=NS):fill(p,s.replace(a,b));s=tx(p)

rels={e.get('Id'):e.get('Target') for e in E.fromstring(parts['word/_rels/document.xml.rels'])};figures=[]
for number,name,caption in [(1,'system','图1 系统组成与独立评价关系'),(2,'water','图2 双支路台架水路与测点'),(3,'sampling','图3 事件触发分级采集与模拟处置'),(4,'protocol','图4 事件提交确认与重传'),(5,'platform','图5 桌面巡检平台监测页面（合成回放）')]:
 p=find(f'图{number} ');rid=p.xpath('.//a:blip/@r:embed',namespaces=NS)[0];part='word/'+rels[rid];path=R/'application/figures/usability_revision'/(name+'.png');b=path.read_bytes();iw,ih=Image.open(io.BytesIO(b)).size;width=420;height=width*ih/iw
 for e in p.xpath('.//wp:extent|.//a:xfrm/a:ext',namespaces=NS):e.set('cx',str(round(width*12700)));e.set('cy',str(round(height*12700)))
 for t in p.xpath('./w:r/w:t',namespaces=NS):t.text=caption;caption=''
 parts[part]=b;figures.append({'number':number,'source':str(path.relative_to(R)),'print_pt':[width,height]})

# Short narrative paragraphs may flow; keep headings, figures and table rows intact.
styles=E.fromstring(parts['word/styles.xml'])
for st in styles.xpath('//w:style[@w:styleId="Normal"]',namespaces=NS):
 pp=st.find(W+'pPr')
 if pp is not None:
  for tag in ['keepLines','keepNext']:
   e=pp.find(W+tag)
   if e is not None:e.set(W+'val','0')
parts['word/styles.xml']=E.tostring(styles,encoding='UTF-8',xml_declaration=True,standalone=True)
core=E.fromstring(parts['docProps/core.xml'])
for e in core:
 if E.QName(e).localname in ['creator','lastModifiedBy']:e.text=''
parts['docProps/core.xml']=E.tostring(core,encoding='UTF-8',xml_declaration=True,standalone=True)
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(D,'w',ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
record={'source':str(S.relative_to(R)),'source_sha256':sha(source),'output':str(D.relative_to(R)),'output_sha256':sha(D.read_bytes()),'changes':changes,'figures':figures,'tables':len(tables),'changed_parts':[n for n in parts if parts[n]!=original[n]],'visual_review':'pending'}
(R/'application/usability_revision/execution_edit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('Execution book updated:',len(changes),'edits, five figures, six centered tables; budget left blank.')
