"""Revise the approved school form without changing user data or template parts."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib,json,re
from lxml import etree as E
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'deliverables/大创申报书_研究方案收敛稿.docx'
OUT=ROOT/'deliverables/大创申报书_方法与图文完善稿.docx'
DATA=ROOT/'application/method_revision';TMP=ROOT/'tmp/method_revision'
DATA.mkdir(exist_ok=True);TMP.mkdir(exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W,M=('{' + NS[k]+'}' for k in ['w','m'])
tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
sha=lambda data:hashlib.sha256(data).hexdigest()
original=SRC.read_bytes()
with ZipFile(SRC) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
root=E.fromstring(parts['word/document.xml']);rows=root.find(W+'body/'+W+'tbl').findall(W+'tr');assert len(rows)==31
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(24,31))}
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
sample=next(p for p in rows[18].xpath('.//w:p',namespaces=NS) if tx(p).startswith('总体目标是'))
changes=[]
def run(value):
    r=E.Element(W+'r');pr=E.SubElement(r,W+'rPr');f=E.SubElement(pr,W+'rFonts')
    for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:f.set(W+k,v)
    for key in ['sz','szCs']:E.SubElement(pr,W+key).set(W+'val','21')
    E.SubElement(r,W+'t').text=value;return r
def find(ri,prefix):
    pp=[p for p in rows[ri].xpath('.//w:p',namespaces=NS) if tx(p).startswith(prefix)]
    assert len(pp)==1,(ri,prefix,len(pp));return pp[0]
def fill(p,chunks,heading=False):
    before=tx(p);breaks=p.xpath('./w:r[w:br]',namespaces=NS)
    stop=p.index(breaks[-1]) if heading and breaks else -1
    for i,c in enumerate(list(p)):
        if i>stop and c.tag!=W+'pPr':p.remove(c)
    for c in chunks:p.append(run(c) if isinstance(c,str) else deepcopy(c))
    changes.append(dict(before=before,after=tx(p)))
def replace(ri,prefix,value):
    p=find(ri,prefix);assert not p.xpath('.//v:imagedata|.//m:oMath',namespaces=NS)
    fill(p,[value],heading=True);return p
def paragraph(chunks):
    p=deepcopy(sample);p.attrib.clear();fill(p,chunks);return p
def after(p,new):p.getparent().insert(p.getparent().index(p)+1,new)
def mr(value,plain=False):
    r=E.Element(M+'r')
    if plain:
        mp=E.SubElement(r,M+'rPr');E.SubElement(mp,M+'sty').set(M+'val','p')
    pr=E.SubElement(r,W+'rPr');f=E.SubElement(pr,W+'rFonts');f.set(W+'ascii','Cambria Math');f.set(W+'hAnsi','Cambria Math')
    E.SubElement(pr,W+'sz').set(W+'val','21');E.SubElement(r,M+'t').text=value;return r
def group(tag,*nodes):
    e=E.Element(M+tag)
    for n in nodes:e.append(n)
    return e
def sub(a,b):return group('sSub',group('e',mr(a)),group('sub',mr(b)))
def frac(a,b):return group('f',group('num',a),group('den',b))
def hat():
    a=E.Element(M+'acc');pr=E.SubElement(a,M+'accPr');E.SubElement(pr,M+'chr').set(M+'val','\u0302');a.append(group('e',mr('R')));return a

p=find(18,'4 渐进故障诊断');maths=p.xpath('.//m:oMath',namespaces=NS);assert len(maths)==4
fill(p,['在非压力补偿的等效负载下，采用',maths[0],'分析下游负载，用',maths[1],
        '表征测点区段阻力。K增加而',maths[2],'基本稳定提示附加出流；',maths[3],
        '持续增加提示区段受限。考虑实际健康负载不必服从平方根关系，本项目进一步引入经验健康参照和噪声尺度，用压力—流量残差形成主诊断，并设置独立短窗提示。图6给出固定1Hz基线的处理关系。'],heading=True)
p=find(18,'平方根负载特征');eqs=p.xpath('.//m:oMath',namespaces=NS);assert len(eqs)==2
# Keep editable pressure-reference expression, and name the flow residual consistently.
new_eq=group('oMath',sub('e','Q'),mr('='),frac(mr('Q'),sub('Q','ref')),mr('−'),mr('1'))
fill(p,['健康参照采用经验幂函数，预测流量与相对偏离定义为：',eqs[0],'，',new_eq,
 '。参考压力为100kPa，a、n由独立健康标定拟合，g由监测前已核验健康区段的实测与预测流量比值中位数确定。分别以窗口内压力均值和该时间窗的累计计数流量代入计算，避免将瞬时压力与另一个时段的流量直接比较。健康参照、参数和适用工作域随配置保存，在故障评价期间保持固定；正常操作状态用于试次解释和候选复核。'])
residual=group('oMath',sub('e','R'),mr('='),hat(),mr('−'),sub('R','0'))
threshold=group('oMath',sub('T','j'),mr('='),mr('max',True),mr('('),sub('τ','j'),mr(','),mr('6'),sub('s','j'),mr(')'),mr(','),mr('j'),mr('∈'),mr('{Q,R}'))
scale=paragraph(['阻力残差定义为',residual,'，其中R₀为同一健康区段阻力估计的中位数。两类残差采用中位数绝对偏差MAD衡量波动，取1.4826倍MAD并设置尺度下限，以',threshold,
 '确定正向越限门限。当前软件流量相对偏离的门限下限为0.06、尺度下限为0.003；阻力残差的两项下限分别为0.6、0.03，单位均为kPa/(L/min)²。系数6是已固定的工程候选值，实测以独立健康训练和误报约束复核，不将其解释为六倍标准差的概率保证。'])
after(p,scale)
decision=paragraph(['十秒主窗使用十一处连续有效计数端点和十次压力观测。仅流量相对偏离越限时形成等效泄漏候选，仅阻力残差越限时形成局部受限候选，两者均越限时输出异常待检查；同一候选连续五次成立后确认。未越限仅表示当前没有足够故障证据，窗口无效则单独输出不可用状态。三秒短窗采用四处端点和三次压力观测，共用健康参照但独立计算残差尺度；连续两次观测至少一路正向越限，仅形成待复核提示。主窗未积累完整时，短窗可独立提示，不能代替主窗分类或作为自动控制条件。'])
after(scale,decision)
replace(18,'输出分别记录',
 '输出分别保存测量质量、短窗提示及主窗候选模式，并附配置和健康参照版本。健康参照未获独立核验时停用故障判断；缺测、计数复位、越量程及转换时序异常重建受影响的窗口，连续确认在数据中断或候选改变后重新计数。五次1Hz更新的首末间隔为4秒，完整响应还包含时间窗滞后，不能将确认次数直接写成固定告警延迟。正常负载增加可与泄漏产生相同观测，量程内压力漂移也可能形成受限候选，需结合操作记录和人工复测核查原因。')
# Embedded image and caption share one paragraph; replace the image later.
p=find(18,'图6 ');p.xpath('.//w:t',namespaces=NS)[0].text='图6 固定1Hz基线的双时间窗诊断流程'
p=find(18,'诊断对照包括');maths=p.xpath('.//m:oMath',namespaces=NS);assert len(maths)==2
fill(p,['诊断对照设置固定流量阈值、健康参照固定门限、健康参照稳健门限三组，使用同一测量前端、时间窗、确认条件及训练与验证划分。补充稳健门限与有界累积判据结合的候选方法，检验是否获得稳定增益；通过保留或去除区段阻力',maths[0],'（对应上游压力',maths[1],
 '观测）及已知操作信息的组合进行消融，区分附加测点与工况约束的贡献。各方法仅在健康训练批次和预实验中选取参数，并按相同正常误报约束评价留出试次；短窗单独统计提示延迟和无故障提示次数。统计以独立操作及批次为单位，完整报告负载未知、压力漂移和模型失配条件下的失败。'])
implementation=paragraph(['节点实现采用便携C诊断内核，健康曲线在计算机端完成拟合并生成查找表，节点通过整数定标与线性插值计算预测值，减少在线浮点幂运算。采集适配层保存实际转换、计数锁存及有效性信息，再将诊断状态映射为通信快照；无效或重复观测不补成新样本。实施时逐项校核定标、插值、边界舍入和资源占用，完成STM32目标编译及真实时序联调。算法选择以可解释性、误报约束和部署代价为依据，不以增加算法数量代替实验验证。'])
after(find(18,'研究目标为'),implementation)
p=find(18,'6 巡检平台与系统联调');maths=p.xpath('.//m:oMath',namespaces=NS);assert len(maths)==2
fill(p,['本地Web平台围绕现场维护组织总览、支管监测、异常事件、设备链路、历史记录和设置六个模块。总览呈现当前有效状态，支管页面显示',maths[0],'、',maths[1],
 '、Q及健康参照偏离，分别呈现测量质量、短窗提示和主窗候选；事件页面关联支管编号、测点区段和核查记录。设备页面观察通信、掉线及恢复，历史页面支持按时间和事件检索与导出。断连或数据无效时显示最近有效时刻，避免旧数据被误读为当前正常。'],heading=True)
p=find(18,'图8 ');p.xpath('.//w:t',namespaces=NS)[0].text='图8 前期巡检界面（K/R合成数据回放）'
replace(18,'平台将',
 '平台将“已查看、处置、复测”作为独立维护步骤。核查人员记录实际发现和处理方式，在同类工况下复测压力与流量，据此确认是否恢复。接收确认与人工维护归档在数据库中分别记录。图8为前期K/R合成回放界面，用于验证信息组织和操作流程；实施阶段接入稳定后的诊断结果、质量状态及短窗提示，由Python串口服务写入SQLite，再与真实采集数据联调。')
replace(20,'五、项目的特色',
 '（1）健康参照约束下的支管联合诊断。针对供压变化与渐进故障混淆的问题，将双压力—流量观测转换为相对流量偏离和区段阻力变化，以独立健康标定、稳健尺度门限及持续确认形成可解释的异常线索。短窗用于及时关注，主窗用于候选确认，分别评价时效与误报。输出关联支管编号及测点区段，通过同信息基线和测点消融检验联合观测的实际增量，对负载未知等歧义保留人工核查依据。')

# Replace the obsolete principal evidence plot, retain the old failure example explicitly as such.
fill(find(23,'初始诊断模型版本为'),[
 '图9比较健康参照固定门限、稳健门限及稳健门限与有界累积组合。三组使用相同压力—累计脉冲前端、十秒主窗及五次确认，负载指数设为0.5，两路压力噪声假设独立，流量噪声为0.02L/min。按0.3、3、10kPa压力噪声，在泄漏、受限及长时正常场景使用全部12个固定测试种子；参数仅依据健康训练确定。随机序列跨场景复用，结果反映该合成模型的候选差异，不作为独立实物重复。'])
p=find(23,'图9 ');p.xpath('.//w:t',namespaces=NS)[0].text='图9 候选判据的有效早期与正常误报对照（合成回放）'
p=find(23,'在=0.3');fill(p,[
 '三组在0.3、3kPa时，两类故障均为12/12条有效早期；10kPa时固定门限两组均为1/12，稳健门限及累积组合均为12/12。长时正常对照中，稳健门限三档均无确认误报；固定门限在10kPa有12/12条误报，累积组合在3kPa为1/12。该对照支持优先部署稳健门限；其他场景的失败按完整数据保留，不据此认定实测准确率或普适优势。'])
p=find(23,'以种子10300');fill(p,[
 '初始K/R模型曾在高噪声下出现明显故障前误报，促使后续研究引入健康残差尺度。另完成288个静态有界误差组合分析，将特征区间分离与在线触发分别检查；采集回放同时检验真实观测窗是否完整，不以插值或保持值补齐缺测。不同阶段模型分别保存参数和结果，现阶段已有成果提供方案选择及失败分析依据，主要性能结论将由台架独立操作验证。'])
p=find(23,'2 诊断边界');maths=p.xpath('.//m:oMath',namespaces=NS);assert len(maths)==1
fill(p,['针对水力观测歧义，已构造未知正常负载、压力漂移和负载指数失配反例。图10保留初始K/R模型的两类失败：未知正常负载增加与等效泄漏可生成相同观测，上游压力',maths[0],
 '偏移可能产生受限候选。更新门限有助于抑制随机波动，无法凭现有三通道观测消除负载同形或确定故障原因。因此，项目将已知操作记录、独立健康标定和维护复测纳入实验，并开展跨负载留出评价，明确可辨识范围。'],heading=True)
p=find(23,'图10 ');p.xpath('.//w:t',namespaces=NS)[0].text='图10 初始K/R判据的负载歧义与压力漂移反例（仿真）'
# Add deployment detail to existing evidence without overstating MCU validation.
p=find(23,'针对早期固定门限');ts=p.xpath('.//w:t',namespaces=NS)
ts[-1].text=ts[-1].text.replace('便携C整数内核','已建立压力整数定标、健康曲线查表和边界舍入检查。便携C整数内核')
replace(23,'3 协议与平台软件',
 '已完成采集适配、C诊断与快照联调，覆盖迟到、缺测、越量程、重复及重叠转换、计数复位和序号中断。216条合成轨迹与冻结的九字段输出一致；80组回放覆盖正常、随机丢失、60秒中断及确认全丢，20组正常链路收到全部生成事件。丢失、拒绝与过期分别记录，重传不作新采集。上述为主机软件验证；STM32目标编译、真实无线与节点掉电持久化在实施阶段验收。')

# Application-oriented prose: problem, planned system tasks, implementation and evidence.
# Retain native formulas and the precise software semantics; avoid a paper-style argument.
p=find(17,'项目涉及传感信号')
fill(p,['项目将传感测量、嵌入式采集、无线通信与巡检管理结合起来，形成从支管状态感知到异常核查的完整研制任务。前期已完成台架概念设计、集中参数模型和离线平台，具备开展测点布置、方法选择与软件联调的基础。实施过程中拟依次完成独立标定、节点开发和台架试验，建立观测数据与故障操作记录的对应关系，研制能够提供核查依据的原型系统，为南疆棉田支管巡检提供可复用的技术方案。'])
p=find(18,'4 渐进故障诊断')
ms=p.xpath('.//m:oMath',namespaces=NS)
fill(p,['诊断方法以压力与流量的联合变化为依据。在非压力补偿的等效负载下，采用',ms[0],'描述下游负载，用',ms[1],
 '估计测点区段阻力。K增加而',ms[2],'基本稳定时重点检查附加出流，',ms[3],
 '持续增加时重点检查区段受限。在此基础上，针对正常供压调整与实际负载变化，建立经验健康参照并引入稳健门限，形成可解释的故障候选。图6展示节点从测量检查、双时间窗判断到事件记录的处理流程。'],heading=True)
p=find(18,'健康参照采用经验')
ms=p.xpath('.//m:oMath',namespaces=NS)
fill(p,['健康参照采用经验幂函数，流量与相对偏离为：',ms[0],'，',ms[1],
 '。参考压力取100kPa，a、n由独立标定拟合，g由监测前已核验健康区段的实测与预测流量比值中位数确定。按同一时间窗计算压力均值与累计计数流量，使两类观测对应同一运行过程。健康参照、参数和工作范围随节点配置保存，在正式故障试验中保持固定；操作记录用于解释正常调节及复核异常候选。'])
p=find(18,'阻力残差定义为');ms=p.xpath('.//m:oMath',namespaces=NS)
fill(p,['在健康参照基础上，计算阻力残差',ms[0],
 '，R₀为同一健康区段阻力估计的中位数。采用中位数绝对偏差MAD描述正常波动，取1.4826倍MAD并设置尺度下限，按',ms[1],
 '确定正向判断门限。当前软件中，流量相对偏离的门限和尺度下限分别为0.06、0.003，阻力残差的对应下限分别为0.6、0.03kPa/(L/min)²。系数6及上述数值用于前期软件方案验证，实施阶段根据独立健康标定和正常误报约束复核后确定。该方法以健康波动为判断依据，兼顾小幅变化识别与稳定运行。'])
p=find(18,'十秒主窗使用')
fill(p,['节点采用主窗确认与短窗提示相结合的处理方式。十秒主窗包含十一处连续有效计数端点和十次压力观测：仅流量相对偏离越限时形成等效泄漏候选，仅阻力残差越限时形成局部受限候选，两者同时越限时列为异常待检查；同一候选连续五次成立后确认。三秒短窗包含四处计数端点和三次压力观测，共用健康参照、独立计算残差尺度，连续两次观测至少一路正向越限时形成待复核提示。短窗可先于主窗给出关注线索，主窗负责候选分类与确认，两类结果分别保存，控制请求另按保护条件生成。未越限表示证据不足，窗口不可用单独记录。'])
p=find(18,'输出分别保存')
fill(p,['为使异常记录能够支持后续核查，输出同时保存测量质量、短窗提示、主窗候选及参照版本。健康参照经独立核验后启用故障判断；出现缺测、计数复位、越量程或转换时序异常时重建受影响的窗口，中断或候选改变后重新累计确认次数。五次1Hz更新首末相隔4秒，实际响应还受窗口长度影响，试验中以完整时间记录评价。对正常负载增加与泄漏观测相似、压力漂移影响候选判断等情况，结合操作记录和人工复测核查原因，明确系统能够可靠提示的故障范围。'])
p=find(18,'研究目标为')
fill(p,['本项目以可靠提示和可核查记录作为原型研制目标。在标定确认的工作范围内，力争使10%和15%故障组首次持续候选正确比例达到90%，正常运行确认误报不高于1次/小时，并评估到达15%参照前的有效早期比例；5%程度用于探索小幅变化的识别边界。正式试验采用固定的健康参照、诊断门限和评价规则，分别统计检出、漏检、首次正确提示及误报。通过这些指标评价系统何时能够提供有效巡检线索，并将结论与独立参考测量对应。'])
p=find(18,'节点实现采用便携')
fill(p,['节点软件拟采用便携C诊断内核，将健康曲线拟合与在线判断分开：计算机端生成查找表，节点通过整数定标与线性插值计算预测流量，减少在线运算负担。采集适配层记录实际转换时刻、计数锁存与有效性，将诊断结果连同原采集信息映射为通信快照。开发中重点完成定标与插值核对、异常观测处理、资源占用检查及STM32目标编译，再开展传感器与真实时序联调。由此形成可复用的采集、诊断和事件输出程序，为后续增加监测节点提供基础。'])
p=find(18,'图7展示正常接收')
fill(p,['图7展示正常接收及确认丢失后的处理过程。前期主机协议已设置遥测、事件和确认三类消息，采用CRC校验和COBS定界，分别为55、57和24字节。缓存优先保留已接纳的异常事件，普通遥测保留最新状态；结合有限次数重发和300秒保留期，在链路中断后恢复发送，并分别记录过期及容量拒绝。实施阶段将完成节点日志、接收服务和真实串口的联调，核对采集、发送、存储与确认时刻，使远端事件能够追溯到同一次原始观测。'])
p=find(18,'7 实验安排与研究拓展')
fill(p,['项目按照测量建模、诊断验证、可靠告警和平台集成四个工作包推进，交付内容及验收要求见表1。首先完成台架与节点的独立标定，建立健康状态参照；随后开展故障及正常调节对照，确定诊断方法与适用范围；在本地判断和原始记录稳定后，验证无线接收与事件恢复，最后完成巡检平台和模拟控制联调。各工作包保留程序、配置及原始记录，以实验批次对应图表与结论，保证研究任务能够逐项检查。'],heading=True)
p=find(21,'六、项目预期成果')
fill(p,['预期研制1套支管故障诊断物联网原型，包括双压力—流量感知节点、LoRa接收端、双支路清水台架及本地Web平台。实现数据采集、分级调度、异常提示、可靠接收、巡检复测和控制请求模拟，形成从现场观测到维护记录的完整流程。配套提交接口与结构设计、程序、使用说明及结题报告，采用LED或蜂鸣器演示控制输出并核验日志，以一个监测单元完成可演示、可复测的功能验证。'],heading=True)
# A successful application describes planned tasks; evidence remains in the foundation section.
for ri,old,new in [
 (18,'3 感知节点与水力模型','3 感知节点设计与测量依据'),
 (18,'4 渐进故障诊断与工况判别','4 渐进故障诊断方法与验证目标'),
 (23,'1 水路设计与模型分析','1 系统设计与前期论证'),
 (23,'2 诊断边界与方法准备','2 诊断方法与可行性分析')]:
    candidates=[p for p in rows[ri].xpath('.//w:p',namespaces=NS) if old in tx(p)]
    assert len(candidates)==1,(ri,old,len(candidates))
    p=candidates[0]
    t=next(t for t in p.xpath('.//w:t',namespaces=NS) if old in t.text)
    t.text=t.text.replace(old,new,1)

rel={e.get('Id'):e.get('Target') for e in E.fromstring(parts['word/_rels/document.xml.rels'])}
replaced=[]
for caption,name in [('图6 ','dual_window_diagnosis'),('图9 ','candidate_comparison')]:
    p=next(p for p in root.xpath('.//w:p',namespaces=NS) if tx(p).startswith(caption))
    shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0]
    id=shape.xpath('.//v:imagedata/@r:id',namespaces=NS)[0];part='word/'+rel[id]
    image=ROOT/'application/figures/method_revision'/f'{name}.png';iw,ih=Image.open(image).size
    shape.set('style',re.sub(r'height:[^;]+;',f'height:{420*ih/iw:.3f}pt;',shape.get('style')))
    parts[part]=image.read_bytes();replaced.append(dict(caption=tx(p),part=part,source=image.relative_to(ROOT).as_posix(),width_pt=420,height_pt=420*ih/iw))

# Normalize caption alignment and prevent separated caption lines; all original table styles stay.
for p in root.xpath('.//w:p',namespaces=NS):
    if re.match(r'^(图\d+|表\d+)\s',tx(p)):
        pr=p.find(W+'pPr');assert pr is not None
        jc=pr.find(W+'jc')
        if jc is None:jc=E.SubElement(pr,W+'jc')
        jc.set(W+'val','center')
        if pr.find(W+'keepLines') is None:E.SubElement(pr,W+'keepLines')
# Use a real heading paragraph; keepNext joins it to the first body lines in a table.
p=find(23,'3 协议与平台软件');br=p.xpath('./w:r[w:br]',namespaces=NS)[-1];idx=p.index(br)
heading=deepcopy(p)
for c in list(heading)[idx:]:heading.remove(c)
pr=heading.find(W+'pPr');kn=pr.find(W+'keepNext')
if kn is None:kn=E.SubElement(pr,W+'keepNext')
kn.set(W+'val','1')
for c in list(p)[1:idx+1]:p.remove(c)
p.getparent().insert(p.getparent().index(p),heading)
assert protected=={i:E.tostring(rows[i]) for i in protected}
assert refs==[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
assert len(root.xpath('.//m:oMath',namespaces=NS))==26
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,value in parts.items():z.writestr(name,value)
assert SRC.read_bytes()==original
with ZipFile(SRC) as a,ZipFile(OUT) as b:altered=[n for n in a.namelist() if a.read(n)!=b.read(n)]
assert set(altered)=={'word/document.xml',*(r['part'] for r in replaced)}
record=dict(source=SRC.relative_to(ROOT).as_posix(),source_sha256=sha(original),output=OUT.relative_to(ROOT).as_posix(),
 output_sha256=sha(OUT.read_bytes()),changed_parts=altered,protected_rows=list(protected),native_math=26,
 references={'Chinese':5,'English':3},figure_changes=replaced,paragraph_changes=changes,visual_review_status='pending')
(DATA/'edit_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(TMP/'artifact.md').write_text('School A4 application; retained approved source is the design authority. Blank personal, budget and approval rows unchanged. Ten figures, three centered data tables, eight references. Methods and candid evidence upgraded. Two code-native figures updated. Native editable mathematics. Render every final page and inspect before delivery. No physical, radio, energy or valve validation claimed.\n',encoding='utf-8',newline='\n')
print('Saved method/figure revision: 31 template rows, 26 native equations, 8 references, two updated figures.')
