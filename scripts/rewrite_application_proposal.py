"""Application prose revision; retain the school form and all ten approved pictures."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
import subprocess,io,json,hashlib,re
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'application/proposal_revision';TMP=ROOT/'tmp/proposal_review'
DATA.mkdir(exist_ok=True);TMP.mkdir(exist_ok=True)
SOURCE='deliverables/大创申报书_方法与图文完善稿.docx'
source=subprocess.check_output(['git','show','f989ea2:'+SOURCE],cwd=ROOT)
(TMP/'source.docx').write_bytes(source)
OUT=ROOT/'deliverables/大创申报书_申报表达修订稿.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}';tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
sha=lambda b:hashlib.sha256(b).hexdigest()
with ZipFile(io.BytesIO(source)) as z:parts={n:z.read(n) for n in z.namelist()}
root=E.fromstring(parts['word/document.xml']);rows=root.find(W+'body/'+W+'tbl').findall(W+'tr')
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(24,31))};changes=[]
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
def find(i,prefix):
    ps=[p for p in rows[i].xpath('.//w:p',namespaces=NS) if tx(p).startswith(prefix)]
    assert len(ps)==1,(i,prefix,len(ps));return ps[0]
def run(t):
    r=E.Element(W+'r');pr=E.SubElement(r,W+'rPr');f=E.SubElement(pr,W+'rFonts')
    for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:f.set(W+k,v)
    for k in ['sz','szCs']:E.SubElement(pr,W+k).set(W+'val','21')
    E.SubElement(r,W+'t').text=t;return r
def fill(p,chunks,heading=False):
    before=tx(p);br=p.xpath('./w:r[w:br]',namespaces=NS)
    stop=p.index(br[-1]) if heading and br else -1
    for i,c in enumerate(list(p)):
        if i>stop and c.tag!=W+'pPr':p.remove(c)
    for c in chunks:p.append(run(c) if isinstance(c,str) else deepcopy(c))
    changes.append({'before':before,'after':tx(p)})
def replace(i,prefix,text,heading=False):fill(find(i,prefix),[text],heading)

replace(17,'本项目选择泄漏','本项目围绕支管接头或管路泄漏、局部过流受限两类问题，利用压力和流量变化为巡检提供线索。单独观察流量变化容易将正常调节与故障混淆，因此拟在支管区段布置两个压力测点和一个流量测点，同时记录轮灌状态与维护操作。系统将异常支管、变化趋势和检查建议集中呈现，帮助人员有针对性地查看接头、管段及下游配水单元，并通过复测确认处理效果。研究的重点是形成有测量依据、能够用于巡检的完整原型。')
replace(18,'总体目标是','本项目拟研制由感知节点、LoRa接收端和本地巡检平台组成的物联网原型系统。节点采集支管压力与流量并形成异常提示，接收端将事件传输至计算机，平台呈现运行趋势、支管状态和巡检记录。项目以单节点双支路清水台架完成原理与功能验证，先建立固定1Hz采集基线，再开展事件触发分级采集对照。控制部分采用软件模拟和LED或蜂鸣器演示，预留后续执行接口，形成从感知、判断到人工核查与复测的系统流程。')
p=find(18,'4 渐进故障诊断');ms=p.xpath('.//m:oMath',namespaces=NS)
fill(p,['诊断采用负载特征',ms[0],'和阻力估计',ms[1],
 '。前者反映下游负载变化，后者反映测点区段阻力。流量相对增大而区段阻力基本稳定时，重点检查附加出流；区段阻力持续增大时，重点检查局部受限。结合正常运行记录建立健康参照，使节点能够给出等效泄漏、局部受限或异常待检查三类候选，图6为处理流程。'],True)
replace(18,'健康参照采用','诊断前先开展独立标定，记录正常供压及负载下的压力—流量关系，将其作为健康参照。节点把同一时间窗的实际观测与该参照比较，判断当前变化是否超出正常范围。参照参数随配置保存，正式故障试验期间保持固定，操作记录用于说明正常阀门切换及负载变化。通过这一安排，使判断依据能够由参考测量和运行记录复核。')
replace(18,'在健康参照基础上','为减少正常波动引起的误报，拟采用基于健康数据波动幅度的稳健门限，结合连续确认形成异常候选。前期已对固定门限、稳健门限及累积判据进行软件比较，实施中优先验证稳健门限方案，并根据独立标定和正常运行试验确定参数。门限及确认条件在正式验证前固定，后续同时检查检出效果、误报和适用范围。')
replace(18,'节点采用主窗','节点设置短窗提示与主窗确认两种处理方式。三秒短窗用于及时提示需要关注的变化，十秒主窗用于判断故障候选；短窗连续两次出现正向越限时提示复核，主窗同一候选连续五次成立后确认。两类结果分别记录，短窗提示不直接触发控制。窗口未积累完整或观测无效时单独标明状态，避免把没有有效数据理解为运行正常。')
replace(18,'为使异常记录','异常记录同时保存原采集时刻、测量质量、候选类别及参照版本。健康参照经独立核验后启用判断，出现缺测、计数复位、越量程或采集时序异常时重新建立受影响的窗口。对正常负载变化与泄漏相似等情况，保留异常待检查并交由人工核查，复测结果再写入平台。项目通过真实采集、独立操作和复测记录评价判断效果，明确系统能够可靠提示的范围。')
replace(18,'“早期”以','本期试验以独立参考测量确定故障程度，设置相对健康流量偏离5%、10%和15%的三级变化，将15%作为试验比较参照。记录故障操作开始、首次正确确认及达到该参照的时刻，评价系统能否在变化进一步扩大前给出有效提示。5%用于探索小幅变化的识别能力，该试验参照不等同于棉花减产或农业通用失效标准。')
replace(18,'本项目以可靠','项目力争在标定确认的工作范围内，使10%和15%故障组首次持续候选正确比例达到90%，正常运行确认误报不高于1次/小时，并评价达到15%试验参照前的有效提示比例。上述为拟验证的研究目标，正式试验分别保存检出、漏检、误报和复测记录，形成能够说明系统效果及适用条件的结果。')
replace(18,'节点软件拟采用','节点软件开发以完成稳定采集和可复核判断为目标。拟将已开展主机验证的便携C程序移植至STM32，采用预先生成的健康曲线表进行在线计算，结合实际压力读数和流量计数形成事件记录。开发顺序为目标编译、有线采集、诊断联调和无线接入，逐项检查异常观测处理、程序运行时间及资源占用，形成可复用的节点程序和操作说明。')
replace(18,'图7展示正常','图7展示事件接收及确认丢失后的处理过程。通信采用数据校验、接收确认和有限次数重发，优先保留已接纳的异常事件，普通遥测保留最新状态。接收服务在数据成功存储后回复确认，同一事件重发时核对身份并去重；链路中断后恢复发送，分别记录超期或容量不足的事件。实施中将完成真实串口、节点日志和接收服务联调，确保平台上的异常能够追溯到原始采集记录。')
p=find(18,'诊断对照设置')
fill(p,['诊断试验比较固定流量阈值、健康参照固定门限和健康参照稳健门限三种方案，使用相同观测数据、时间窗和确认条件。通过分别使用单点信息、双压力信息及操作记录，分析附加测点与运行状态记录的作用；累积判据作为候选方案补充比较。参数在健康标定和预实验中确定，正式验证采用留出批次，分别统计故障提示和正常误报，并保留负载变化、压力漂移及模型失配条件下的失败记录。'])
p=find(20,'五、项目的特色')
fill(p,['（1）面向南疆棉田支管巡检的联合判断。将两个压力测点与流量观测结合，以正常运行数据建立参照，减少单一流量报警难以区分正常调节和故障的问题。节点给出异常候选及变化依据，平台关联支管编号、测点区段和建议检查部位，形成感知、提示、核查和复测相衔接的系统功能。对现有观测难以区分的情况保留人工核查，并通过测点对照验证联合观测的实际作用。'],True)
replace(20,'（3）','（3）将事件触发采集与可靠告警结合。正常阶段按设定周期观测，出现持续变化后加密采集，并结合异常优先发送、接收确认和恢复重传保存事件。项目分别比较读取次数、发送次数和提示及时性，实物阶段再测量整机电流，评价策略的收益与代价。通过同一事件贯穿节点、接收平台及人工复测，使采集优化与巡检功能在同一系统中得到验证。')
replace(22,'申报阶段重点','项目按方案论证、原型研制和研究成果三个阶段推进。申报阶段以系统设计、可复现模型及软件验证说明任务可行性；实施阶段完成台架、节点、无线与平台联调，并开展独立试验；成果阶段整理原始记录、研究报告和论文初稿。各阶段围绕同一巡检问题展开，仿真用于前期准备，原型性能以实测结果验收。')
replace(23,'图9比较','为选择后续节点诊断方案，前期对健康参照固定门限、稳健门限及稳健门限与累积判据组合进行了合成回放，结果见图9。三组使用相同测量前端、时间窗和确认条件，在泄漏、局部受限及长时正常场景比较提示与误报，覆盖0.3、3和10kPa压力噪声及全部12个测试种子。模型与随机序列的设置保持一致，用于比较候选方案，不作为独立实物试验。')
replace(23,'初始K/R模型曾','初期模型在高噪声条件下出现故障前误报，促使方案引入健康数据波动幅度和连续确认。另已完成288个静态有界误差组合分析，并核对缺测时的窗口处理。上述工作为测点选择、门限设计和台架试验提供前期依据；正式性能结论由独立标定及故障操作验证。')
p=find(23,'针对早期固定门限');fill(p,['前期已建立健康参照、稳健门限和测量质量检查，完成便携C整数内核与主机参考程序的比较。在216条合成轨迹、130,896次更新中，九字段输出保持一致，边界舍入及插值差异另有记录。固定1Hz、十秒主窗和五次确认作为当前软件基线，三秒短窗仅形成待复核提示。这些工作证明软件逻辑具备移植准备，STM32运行、实际传感器时序及物理诊断效果在实施阶段验证。'])
replace(23,'分级采集已完成','分级采集已完成四种策略的合成回放，检查调度仅使用已经取得的观测。既有模型中，固定60秒读取的泄漏组未获得有效早期提示（0/20），更长周期还存在明显漏检。这一结果说明采集周期必须结合故障变化速度选择。后续保留固定1Hz基线，从2秒、5秒候选间隔开展对照，分别评价读取与发送次数、提示及时性及实测电流。')

# Follow the supplied national-level example's problem -> system -> value exposition.
replace(16,'一、项目简介','本项目面向南疆规模化棉田膜下滴灌支管巡检，针对管网分散、异常不易及时发现和人工排查范围大的问题，拟研制集压力与流量感知、支管异常诊断、LoRa无线传输和巡检管理于一体的物联网原型系统。项目围绕泄漏与局部过流受限，通过双压力—流量联合观测建立健康状态参照，研究渐进异常提示和事件触发采集方法，使正常运行与异常变化采用不同的采集和上报方式。平台集中呈现支管状态、变化趋势及建议检查区段，关联人工核查与复测记录。项目以双支路清水台架完成原型与对照验证，交付感知节点、无线接收端、巡检平台、实验数据和研究报告，为棉田支管分区监测提供可复用方案，并为后续跨工况应用和多支管联动研究奠定基础。',True)
replace(18,'图1给出了','图1给出了系统组成及协作关系。感知节点负责测量、异常判断及事件记录，LoRa接收端连接计算机，接收服务完成数据校验与存储，巡检平台组织状态展示和维护记录。各环节围绕同一支管及异常事件衔接，使人员能够从页面查看变化依据，并记录核查、处置及复测结果。参考测量与故障操作独立记录，用于检验原型提示是否正确。')
replace(18,'台架按测量','台架结构围绕测量和重复试验需求设计。图3以参数化三维模型呈现管路、取压点、采集盒和泄漏收集装置，兼顾传感器安装、管段拆装及收集容器取放。设计中将电气采集与出水路径隔离，按照器件要求确定安装长度与直管段，并检查维护空间。模型为装配提供依据，实物阶段再核验漏水、排气、固定和计量稳定性，形成便于更换工况和重复操作的验证平台。')
replace(18,'独立收集采用','泄漏量采用独立收集与计时测量，按模型最大泄漏量和取样时长核定容器需求，预留容量余量和自由出流空间，连续试验另设排水。容器在使用前测定有效容量，取样时避免溢流和出水口淹没，并检查计时、称量及重复取样误差。由此建立不依赖诊断结果的参考测量，为故障程度和提示时间评价提供依据。')
replace(18,'图4给出','图4给出了压力与脉冲流量采集接口。两路压力信号经调理、保护和滤波后转换为数字观测，流量信号经电平转换接入主控计数端，节点统一记录测量时刻。电源和逻辑接口按实际器件要求核对，重点检查异常输入、断电和采集、存储、发送同时运行时的稳定性。先完成有线采集，再接入无线模块，使各环节能够逐项验证。')
replace(18,'基线采用','节点首先建立固定1Hz采集基线，采用累计脉冲和时间窗计算流量，保存压力转换与计数锁存时刻，为渐进异常判断提供连续观测。压力和流量分别采用不少于五个工作点、每点至少三次独立读取开展标定，并设置升降压、共同压力及容积或称量计时对照。缺测、迟到及计数复位分别记录，使判断依据能够与参考测量核对，并明确实际可用量程和误差。')
replace(18,'事件触发采集在','在固定采集基线稳定后，开展事件触发分级采集研究。正常阶段采用候选周期观测压力并连续计数，出现持续变化时缩短读取周期，恢复稳定后返回原周期。其目标是在保持异常响应的同时减少不必要的采集与上报。对渐进故障和短时变化分别比较，记录读取次数、首次提示时间及漏检情况，依据实验确定周期和适用条件。')
replace(18,'采集、完整原始','采集与无线发送分开配置，保留固定1秒读取方案作为基线，首先比较2秒、5秒候选采集间隔，并考察更长间隔的响应边界；正常状态上报以60秒作为候选。图5为事件触发采集与模拟处置流程，判断只使用真实取得的观测。策略选择兼顾异常响应、误触发和通信开销，逐步确定适合台架工况的参数，再研究田间迁移条件。')
replace(18,'采集策略采用','采集策略设置固定高频、固定低频、仅改变上报周期和分级采集四组对照。在相同健康参照与故障条件下，改变异常出现时刻，比较提示及时性、漏检和误触发；同时记录读取、存储及发送次数。实物阶段按相同供电和运行时长测量整机电流，评价策略收益与代价，使采集次数减少和实际能耗变化分别获得依据。')
replace(18,'5 LoRa事件传输','面向棉田支管分散布置的需求，设计周期状态与异常事件相结合的LoRa传输方式。正常状态支持远程查看，异常事件优先保存和发送；接收端校验后存入数据库并回复确认，重复事件核对身份后去重。节点在短时中断后恢复待确认事件，使平台能够保留完整巡检线索，降低通信中断对异常追踪的影响。',True)
replace(18,'联调按照','系统联调依次完成有线采集、无线收发、平台显示及巡检记录，使用同一异常操作贯穿采集、判断、传输、展示和复测。验收包括两类故障的核查与复测、误报核查、一次8小时连续记录和至少3次重启恢复，并检查模拟控制与人工操作的状态。形成原型、使用说明和对应记录，验证系统能否为支管巡检提供可理解、可追溯的信息。')
replace(18,'后续研究首先','后续首先拓展不同负载、供压和运行日期下的适应能力。利用原型积累健康状态数据，比较固定参照、少量数据重新标定及经验修正方式，研究轮灌条件变化时如何保持可靠提示。按不同工况开展独立验证，分析误报、漏检及标定工作量，逐步形成可迁移的测量和参照更新方法。')
replace(18,'在增加节点','在单节点路线验证后，进一步拓展多支管分区监测。利用同一水源下不同支管的同步变化，研究共同供压扰动与局部异常的区分，改进支管范围提示。结合维护记录比较有无系统提示时的排查时间和误导情况，评价实际巡检价值。本期完成单节点台架和事件流程，后续布点按新增资源及现场条件推进。')
replace(20,'（2）','（2）面向渐进异常的稳健提示。结合健康状态参照、波动门限和连续确认，研究小幅泄漏及局部受限逐渐发展时的压力—流量变化，减少正常波动产生的误报。通过独立参考测量比较提示时刻和候选正确性，同时保留正常调节与测量误差对照，使早期提示能力具有明确的验证依据和适用范围。')
# Keep the main form focused on student innovation tasks rather than a protocol report.
replace(18,'通信试验比较','无线通信拟比较不同上报周期、事件触发和异常优先发送方式，考察链路稳定、遮挡和短时中断时的告警效果。使用相同诊断记录开展对照，记录告警到达时间、成功接收比例及恢复后的事件缺失，分析可靠传输与通信开销的关系。发送次数和整机电流分别测量，使通信方案选择具有可检查的依据。')
replace(18,'控制联动用于','控制联动作为巡检流程的演示功能，本期采用LED或蜂鸣器表示执行输出，并保留人工操作。异常候选先供人员核查，满足有效观测和明确工况等保护条件时再生成模拟请求。系统关联支管身份、请求原因及处理状态，区分接收确认、演示输出和人工复位，重复命令只执行一次。页面标明模拟模式，未接入节点时仅显示请求已生成，保证演示状态与实际实现一致。')
replace(18,'节点预留控制','节点预留控制驱动和反馈接口，为后续接入执行器提供条件。真实阀门作为延伸任务，结合管径、工作压力及反馈方式选型，置于A支路入口并检查实际止流和对其他支路的影响。阀控验证与原诊断试验分开开展，保护条件通过独立试验确定；本期先完成异常提示、人工核查及模拟输出衔接，避免执行动作影响原有测量和诊断验证。')
replace(18,'无线测试覆盖','无线测试设置稳定、遮挡和短时中断三类场景，改变测试顺序并保存位置与配置，比较本地提示和平台收到事件的时刻。平台连续运行时核对节点日志、数据库和维护记录，检查掉线恢复、事件去重及页面状态，验证从采集到巡检记录的完整功能。')
replace(21,'形成标定','整理形成标定、故障、正常调节、采集策略和通信对照等原始数据，按表2完成主要故障操作及相关验证。配套提交标定曲线、测试记录和结果分析，说明原型的测量范围、故障提示效果及采集通信方案的取舍，形成能够复核的研究报告。软件成果按实际开发内容整理著作权申请材料。')
replace(21,'形成1篇','形成1篇以实测数据为基础的研究论文稿，围绕跨工况故障辨识或事件采集策略，完成对照试验、结果分析和投稿。项目在规定周期内完成原型及结题报告，论文投稿与修订按实际研究进度推进，录用、发表结果依据真实证明登记。')
replace(23,'已完成采集适配','已完成采集适配、诊断与通信状态的主机软件联调，检查缺测、越量程、计数复位等异常情况下的处理。80组通信回放涵盖正常、随机丢失、60秒中断及接收确认全丢，其中20组正常链路收到全部生成事件；丢失、拒绝及过期记录分别保存。这些结果为后续节点移植和无线联调提供程序基础，尚不代表真实射频链路或节点掉电恢复性能。')
replace(23,'控制方面已完成','控制功能已完成12项主机模拟检查，包括自动请求条件、命令去重、支管身份核对、演示输出及人工复位。现有结果说明模拟处理流程已建立，节点IO输出和页面接入在原型联调中完成。相关程序、参数及检查记录已保存，可作为控制接口开发与系统演示的基础。')
for oldtitle,newtitle in [('3 感知节点设计与测量依据','3 感知节点与分级采集'),('4 渐进故障诊断方法与验证目标','4 支管异常诊断与巡检提示'),('5 LoRa事件传输与可靠接收','5 LoRa无线通信与事件管理'),('7 实验安排与研究拓展','7 实施步骤与验证安排')]:
    for p in rows[18].xpath('.//w:p',namespaces=NS):
        for t in p.xpath('.//w:t',namespaces=NS):
            if t.text==oldtitle:t.text=newtitle
for ri in [21,22]:
    for t in rows[ri].xpath('.//w:t',namespaces=NS):
        if t.text:t.text=t.text.replace('基线与消融','基线与测点对照').replace('留出批次、基线与消融','独立批次与方法对照')

p=find(18,'水力分析采用');ms=p.xpath('.//m:oMath',namespaces=NS)
fill(p,['台架采用',ms[0],'和',ms[1],
 '描述水力变化，R表示区段阻力，Cₙ、Cₗ分别为正常负载和附加泄漏系数，压力、流量分别按kPa、L/min表示。模型用于比较测点布置与诊断特征，并分析两支路在共同水源下的影响。现有分析中，A支路流量约1.85—4.34L/min，最大总供水量约7.95L/min，据此确定台架水源及量程要求，实物阶段通过标定核对。'])
# Put planned diagnostic targets and development tasks before the flowchart.
anchor=find(18,'图6 ')
parent=rows[18].find(W+'tc')
while anchor.getparent() is not parent:
    anchor=anchor.getparent()
for prefix in ['项目力争在','节点软件开发以']:
    p=find(18,prefix);p.getparent().remove(p);parent.insert(parent.index(anchor),p)
p=find(18,'实际滴灌管具有')
p.find(W+'pPr/'+W+'keepLines').set(W+'val','1')

# This inner one-cell table holds prose, not a figure: allow normal pagination.
p=find(18,'4 支管异常')
tr=p.getparent().getparent()
assert tr.tag==W+'tr' and not tr.xpath('.//w:pict',namespaces=NS)
flag=tr.find(W+'trPr/'+W+'cantSplit')
if flag is not None:flag.getparent().remove(flag)
# Keep each innovation paragraph together, avoiding an isolated opening line.
p=find(20,'（2）')
pr=p.find(W+'pPr');flag=pr.find(W+'keepLines')
if flag is None:flag=E.SubElement(pr,W+'keepLines')
flag.set(W+'val','1')

assert protected=={i:E.tostring(rows[i]) for i in protected}
assert refs==[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for n,b in parts.items():z.writestr(n,b)
count=len(root.xpath('.//m:oMath',namespaces=NS))
record={'source_commit':'f989ea2','source':SOURCE,'source_sha256':sha(source),'output':OUT.relative_to(ROOT).as_posix(),
 'output_sha256':sha(OUT.read_bytes()),'protected_rows':list(protected),'changed_parts':['word/document.xml'],
 'native_math':count,'figures_unchanged':10,'references':{'Chinese':5,'English':3},'paragraph_changes':changes,
 'technical_detail_authority':'docs/算法与软件最终方案.md and source commit f989ea2; no algorithms or accepted results changed',
 'visual_review_status':'pending'}
(DATA/'edit_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(TMP/'artifact.md').write_text('School A4 grant application. Use application prose, preserve all template and pictures, blank information and budget. Native mathematics retained where necessary. Algorithms unchanged; details remain in technical source. Final render and per-page review required.\n',encoding='utf-8',newline='\n')
print(f'Saved application prose revision; {len(changes)} paragraphs, {count} native math objects; all ten pictures unchanged.')
