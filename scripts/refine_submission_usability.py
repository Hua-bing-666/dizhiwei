"""Revise a copy of the user's accepted school form; preserve personal fields and math."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
from PIL import Image
import re,json,hashlib,io
R=Path(__file__).resolve().parents[1];T=R/'tmp/usability_submission';T.mkdir(exist_ok=True)
F=R/'application/figures/usability_revision';OUT=R/'application/usability_revision';OUT.mkdir(exist_ok=True)
S=R/'deliverables/大创申报书_现阶段更新稿.docx';D=R/'deliverables/大创申报书_图文精修稿.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}';tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS));sha=lambda b:hashlib.sha256(b).hexdigest()
source=S.read_bytes()
with ZipFile(io.BytesIO(source)) as z:parts={n:z.read(n) for n in z.namelist()}
original=parts.copy();root=E.fromstring(parts['word/document.xml']);rows=root.find(W+'body/'+W+'tbl').findall(W+'tr')
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(24,31))};changes=[]
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
def find(i,prefix):
 ps=[p for p in rows[i].xpath('.//w:p',namespaces=NS) if tx(p).startswith(prefix)]
 if not ps:ps=[p for p in rows[i].xpath('.//w:p',namespaces=NS) if prefix in tx(p)]
 assert len(ps)==1,(i,prefix,len(ps));return ps[0]
def run(text):
 r=E.Element(W+'r');pr=E.SubElement(r,W+'rPr');fonts=E.SubElement(pr,W+'rFonts')
 for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:fonts.set(W+k,v)
 for k in ['sz','szCs']:E.SubElement(pr,W+k).set(W+'val','21')
 E.SubElement(r,W+'t').text=text;return r
def fill(p,chunks,heading=False):
 before=tx(p)
 old_math=p.xpath('.//m:oMath',namespaces=NS)
 if old_math and all(isinstance(c,str) for c in chunks):
  # Preserve simple native pressure symbols instead of replacing them with text.
  for native in old_math:
   symbol=''.join(native.xpath('.//m:t/text()',namespaces=NS));key={'P0':'P₀','P1':'P₁'}.get(symbol)
   assert key,(before,symbol)
   if symbol=='P0' and key not in ''.join(chunks):chunks=[c.replace('上游压力','上游压力P₀',1) for c in chunks]
   replaced=False;new=[]
   for c in chunks:
    if not replaced and isinstance(c,str) and key in c:
     left,right=c.split(key,1);new.extend([left,deepcopy(native),right]);replaced=True
    else:new.append(c)
   assert replaced,(before,key);chunks=new
 br=p.xpath('./w:r[w:br]',namespaces=NS);stop=p.index(br[-1]) if heading and br else -1
 for i,c in enumerate(list(p)):
  if i>stop and c.tag!=W+'pPr':p.remove(c)
 for c in chunks:
  if not isinstance(c,str):p.append(deepcopy(c));continue
  for token in re.split(r'(\[\d+(?:[,，]\d+)*\])',c):
   if not token:continue
   r=run(token)
   if re.fullmatch(r'\[\d+(?:[,，]\d+)*\]',token):E.SubElement(r.find(W+'rPr'),W+'vertAlign').set(W+'val','superscript')
   p.append(r)
 changes.append({'before':before,'after':tx(p)})
def replace(i,prefix,text,heading=False):fill(find(i,prefix),[text],heading)

replace(16,'一、项目简介','本项目面向南疆规模化棉田膜下滴灌支管巡检，研制集双压力—流量感知、早期异常诊断、LoRa通信和巡检管理于一体的物联网原型系统。针对管网分散、异常难以及时发现和人工排查范围大的问题，以健康运行关系为参照，研究渐进泄漏与局部过流受限的识别方法，结合事件触发分级采集提高异常阶段的观测及时性。平台关联支管编号、变化趋势与核查复测记录，为维护人员提供排查线索。项目以单节点双支路清水台架完成原型和对照试验，形成感知节点、接收端、桌面巡检软件及实验数据，进一步研究供压和轮灌负载变化下的参照适配，为多支管分区监测积累方法与实现基础。',True)
replace(17,'本项目围绕','项目选择支管接头或管路泄漏、局部过流受限作为研究对象。单独观察流量，难以分清正常轮灌调节与故障变化；在监测区段布置两个压力点，并记录分流前的总流量，可以为判断提供更多依据。平台将异常支管、变化趋势和建议检查部位联系起来，维护人员据此查看接头、管段及下游配水单元，再通过复测确认处理效果。项目希望把分散的测量信息转化为有针对性的巡检线索。')
replace(17,'项目将','研制工作涵盖传感测量、嵌入式采集、无线通信与巡检软件，能够将通信工程所学用于农业现场问题。前期已建立水路模型、参数化台架和诊断软件，完成本地数据库接入及桌面封装。接下来的工作以独立标定和真实采集为起点，逐步完成节点、无线和台架联调，在有记录、有对照的试验中检验系统效果。')
replace(18,'本项目的应用对象','本项目服务于南疆规模化棉田膜下滴灌管网，重点观察轮灌支管及下游配水单元的水力变化。支管向辅管或毛管配水，毛管通常为带灌水器的滴灌带，二者属于不同管网层级[4]。研究围绕接头或管路泄漏、两压力测点之间的局部过流受限展开，将供压调整、正常轮灌切换及负载变化列为对照。监测结果提示支管和检查区段，具体故障部位由现场核查确定。',True)
replace(18,'本项目拟研制','系统由感知诊断节点、LoRa接收端和本地巡检平台组成。节点获取压力、流量并记录异常，接收端连接计算机，平台呈现趋势和维护过程。本期建设一个监测节点与A、B双支路清水台架，先验证固定1 Hz采集，再比较事件触发策略。控制环节保留软件请求与LED或蜂鸣器演示接口，用于串联异常提示、人工处置和复测流程。')
replace(18,'位置提示采用','位置提示采用“支管编号—测点区段—建议检查部位”。两压力点包围区段的压力损失用于辅助判断局部受限；下游等效泄漏则结合流量、阀门状态提示核查接头、旁路及配水单元。设备与支管标识贯穿采集、事件和维护记录，为后续增加监测节点保留统一的数据组织方式。')
replace(18,'图1给出了','图1说明系统各环节的协作关系。节点负责测量和判断，接收服务负责校验、去重与存储，平台负责展示和核查记录。参考测量与故障操作另行保存，用于检验提示时刻和候选类别，避免用算法输出反过来定义故障。')
replace(18,'为在相同供水条件下','台架采用共用水源的A、B双支路，以便区分故障与正常调节。A支路依次设置上游取压点P₀、受限元件R、下游取压点P₁和流量计Q，随后分为正常出流和泄漏旁路；B支路模拟其他灌溉单元的负载切换。流量计位于分流前，测得A支路正常与泄漏出流的总量；两个压力点包围R，为局部压力损失的判断提供依据。',True)
replace(18,'泄漏试验通过','泄漏试验逐步开启旁路，受限试验调节R改变局部阻力。故障程度由独立收集计时、参考压力与流量及操作记录共同核验，先考察渐进变化，再加入供压和B负载切换。清水台架使用非压力补偿等效负载验证水力响应，压力补偿式灌水器和分布式滴头堵塞作为后续适用性研究。')
replace(18,'台架结构围绕','图3为台架概念装配。测点顺序与图2一致，采集盒和电气接口布置在前侧，防溅板分隔水路与电气区域；独立收集装置保留取放和排水空间。采购后按实际器件核定安装尺寸，装配阶段检查排气、密封与固定，避免结构问题影响重复测量。')
replace(18,'泄漏量采用','独立计量按20秒分次取样设计，收集容器有效容量要求不低于440 mL。使用前核定容量和计时误差，检查出口淹没、溢流与重复取样；长时运行另设排水。参考计量与节点诊断相互独立，用来确定变化程度及提示提前量。')
replace(18,'台架采用水力等效','A负载代表监测单元的综合正常出流，B支路代表共用水源下其他单元的调节。分别改变附加出流和测点区段阻力，检验联合观测能否区分泄漏、受限与正常扰动。迁移至棉田时，按实际管径、流量和安装条件选择传感器，重新测定健康关系，并核验支管提示对巡检的帮助。')
replace(18,'该流量范围服务于','台架的0.3—5 L/min流量范围服务于缩小规模的原理验证。棉田支管流量随管径和轮灌单元变化，需要另行选型标定。采集程序和事件标识与量程参数分开配置，使更换测量器件后的数据仍能进入相同的巡检流程。')
replace(18,'图4给出了','图4给出采集接口。压力电流经采样、保护与滤波进入ADS1115，流量脉冲经3.3 V电平转换进入主控硬件计数端。节点记录转换和计数时刻，并检查缺测、计数复位及异常输入。开发先完成有线采集，再接入日志和无线，逐步核对各环节的稳定性。')
replace(18,'在固定1Hz采集稳定后','事件触发分级采集在固定1 Hz基线基础上开展。巡航阶段按选定周期读取压力，累计脉冲持续计数；已取得的观测连续偏离健康范围时，切换至1秒读取，稳定一段时间后返回巡航周期。研究将比较渐进故障、短时变化和正常负载切换的响应，重点解决减少读取后提示等待增加的问题。')
replace(18,'压力读取与无线发送','压力读取和无线发送分别调度。2秒、5秒巡航间隔列为采集对照，正常状态以60秒周期上报作为候选配置，异常事件优先发送。周期选择通过漏检、误触发、提示提前量和通信开销共同评价。图5给出分级采集与模拟处置的关系；固定1 Hz主线保留，用于检验策略改变带来的收益与代价。')
replace(18,'采集策略设置','试验设置固定高频、固定低频、仅改变上报周期和分级采集四组方案。在相同健康参照和故障条件下改变异常出现相位，记录读取与发送次数，并比较提示及时性、漏检和误触发。整机电流在相同供电和运行时长下测量，采集次数与能耗分别报告。')
p=find(18,'诊断以健康状态');math=p.xpath('.//m:oMath',namespaces=NS);assert len(math)==2
fill(p,['诊断采用相对流量残差',math[0],'和区段阻力估计',math[1],'联合判断。健康曲线给出相同下游压力下的正常流量，区段阻力与健康值比较，分别反映附加出流与局部受限。流量持续正向偏离且区段阻力基本稳定时形成等效泄漏候选；阻力持续增加时形成受限候选。特征冲突则提示异常待检查，保留测量依据供巡检核查。'],True)
replace(18,'诊断前在不同供压点','健康标定覆盖不同供压点和已知负载状态，建立压力—流量经验曲线及区段阻力参照。平台支持健康记录导入与候选曲线拟合，参照经未参与拟合的健康批次核验后使用。故障试验固定参照版本，记录阀门和负载变化；随后对比固定参照与重新标定，研究跨供压、跨负载的适用范围。')
replace(18,'为减少正常波动','为抑制正常波动，使用健康数据估计残差波动范围，设置稳健门限并结合连续确认。前期软件比较支持优先采用这一方案，实际门限由独立标定和正常运行试验确定。正式评价前固定参数，在同一批故障与正常对照上统计检出、误报和漏检。')
replace(18,'节点设置短窗关注','短窗与主窗承担不同任务：三秒短窗连续两次正向越限形成关注提示，十秒主窗同类候选连续五次成立后形成持续候选。两个窗口分别建立参照并记录有效性，缺测或计数复位时重建受影响窗口。关注提示用于及时查看，故障原因仍由工况和复测核验。')
replace(18,'异常记录同时保存','异常记录关联采集时刻、观测质量、候选类别和参照版本。遇到未知负载、压力漂移或正常切换与故障相似的情况，保留异常待检查，由操作记录和复测补充判断依据。试验将这些情况纳入对照，明确哪些变化能够可靠提示，哪些需要额外信息。')
replace(18,'本期试验以独立参考','故障试验按相对健康流量偏离5%、10%和15%设置三级变化，以15%作为统一比较参照。独立记录操作开始、首次正确持续候选和达到参照的时刻，判断系统能否在变化扩大前提示。5%组用于探索小幅变化的识别边界，15%参照仅用于本项目试验比较。')
replace(18,'项目力争在标定确认','项目力争在标定确认的工作范围内，使10%和15%故障组首次持续候选正确比例达到90%，正常运行确认误报不高于1次/小时，并评价达到15%参照前的有效提示比例。各组同时报告独立操作次数、漏检和失败情况，以完整结果说明效果及适用条件。')
replace(18,'节点软件开发','节点程序将现有便携C内核移植至STM32，以预先生成的健康曲线表计算窗口特征，结合实际压力读数和累计计数形成事件。开发依次完成目标编译、有线采集、诊断联调和无线接入，检查运行时间、资源占用及异常观测处理，形成可复用的程序与连接说明。')
replace(18,'面向棉田支管分散','LoRa通信采用周期状态与异常事件相结合的方式。正常状态用于远程查看，异常优先保存和发送；接收端校验后写入数据库并回复确认，重复事件按身份去重。链路中断后恢复待确认事件，使巡检记录能够保留异常发生时的线索。',True)
replace(18,'图7展示','图7展示事件确认与重发过程。接收确认在数据库提交后生成，同一事件重发时核对身份和摘要，避免重复写入或覆盖记录。节点采用有限重试，保留超期、未送达和容量不足情况。真实串口与LoRa联调将核验原始采集、发送、接收和保存记录的对应关系。')
replace(18,'无线通信拟比较','无线对照比较不同上报周期、事件触发和异常优先发送，在稳定、遮挡和短时中断三类链路条件下重放相同诊断记录。记录到达时间、成功接收比例、重传次数和恢复后的缺失，分析及时性与通信负担之间的取舍。')
p=find(18,'本地Web平台按');math=p.xpath('.//m:oMath',namespaces=NS);assert len(math)==2
fill(p,['巡检软件采用本地服务与桌面窗口，八个页面分别承担总览、监测、核查、设备、历史、实验、台架和设置职责。监测页同步展示',math[0],'、',math[1],'与Q，曲线和台架测点读取同一会话；事件页组织查看、处置及复测，历史页检索并导出记录。实验页用于采集对照和健康参照拟合，台架页提供结构与测点查看。图8为当前桌面监测页面。'],True)
replace(18,'平台将','平台保留原始候选快照，人工核查另行追加。Python服务与SQLite负责本机存储，桌面程序支持回放、暂停、曲线范围选择、三维聚焦和原生文件导出，关闭后重新打开可恢复历史记录。实施阶段把串口和LoRa数据接入这一流程，断连时区分历史读数与当前状态。')
replace(18,'控制联动服务于','处置联动采用软件模拟与LED或蜂鸣器演示，区分人工请求、接收、演示输出和复位。主机程序已记录这些状态，后续联调节点IO，核验重复命令与无效观测时的处理。真实阀门另行研究，本期保持水路试验条件稳定，重点完成诊断、核查和复测之间的衔接。')
replace(18,'后续首先研究','后续研究首先围绕健康参照适配展开。现有合成测试表明，供压变化与负载规律变化的影响不同，固定参照对未知负载可能产生误报。项目比较固定参照、多供压点重新标定和少量健康数据修正，按日期及工况划分独立验证批次，评价判断效果和标定工作量，为轮灌条件变化下的应用提供依据。')
replace(18,'在单节点路线','单节点验证完成后，可增加支管监测节点，利用共用水源下不同支管的同步变化区分共同扰动与局部异常。维护记录还可用于比较有无提示时的排查时间，检验系统的实际巡检价值。多节点布点和更细的区段判断在后续资源、现场条件具备时开展。')
replace(19,'结合上述研究','结合已有研究，本项目把改进重点放在两方面：利用双压力—流量与工况记录提高渐进异常提示的可复核性，研究正常调节与故障之间的辨识边界；在此基础上比较事件触发分级采集和可靠上报，分析减少观测与通信时的响应代价。控制请求演示和桌面平台承担系统集成任务，研究结论由独立标定、正常干扰对照与留出批次支持。')
replace(21,'预期研制','预期研制1套支管故障诊断物联网原型，包括双压力—流量感知节点、LoRa接收端、双支路清水台架和桌面巡检软件。完成稳定采集、异常提示、可靠接收、核查复测与模拟控制流程，提交结构和接口设计、节点及前后端程序、使用说明与结题报告，形成可演示、可重复验证的系统。',True)
replace(23,'前期已完成','前期已完成文献梳理、双支路水路设计、参数化装配、采集接口分析和本地巡检软件。台架模型含207个有效实体，测点顺序与水路一致，支持整体、电气和泄漏计量局部查看；已检查防溅板交集、局部间隙与容器取放。现有成果为设计、仿真和主机软件，实物节点、无线射频及田间应用在实施阶段验证。',True)
replace(23,'为选择后续节点','图9比较固定门限、稳健门限及稳健门限与累积判据组合。三组使用相同测量前端、窗口和确认条件，对泄漏、局部受限及长时正常轨迹进行合成回放，覆盖三档压力噪声和12个测试种子。该对照用于选择节点方法，全部试次及失败结果按原记录保留。')
replace(23,'三组在0.3','在0.3、3 kPa噪声下，两类故障均为12/12条有效早期；10 kPa时固定门限降为1/12，稳健门限和累积组合保持12/12。长时正常对照中，稳健门限三档均无确认误报，固定门限与累积组合分别出现误报。结果支持优先部署稳健门限，并在实物阶段检验其实际效果。')
replace(23,'初期模型在高噪声','初期高噪声误报促使方案引入健康波动估计与连续确认。随后完成静态有界误差分析和缺测窗口检查，为标定范围、门限选择及台架试验提供依据。')
replace(23,'针对水力观测歧义','前期还构造了未知正常负载、压力漂移及负载规律失配反例。图10显示，未知负载增加可与等效泄漏产生相同观测，上游压力偏移也可能形成受限候选。稳健门限能够抑制随机波动，却不能替代工况信息和独立核查。因此，试验纳入操作记录、健康标定与跨负载留出评价。',True)
replace(23,'前期已建立健康参照','诊断程序已完成健康参照、稳健门限和测量质量检查。便携C整数内核与主机参考程序在216条合成轨迹、130,896次更新中的九字段输出一致，边界舍入与插值差异另有记录。当前固定1 Hz基线采用十秒主窗、五次确认，三秒短窗形成关注提示，为STM32移植提供程序基础。')
replace(23,'已完成采集适配','采集适配与通信状态已在主机联调，覆盖缺测、越量程、计数复位、重复报文和确认丢失。80组通信回放包括正常链路、随机丢失及受控中断，正常组收到全部生成事件；其他组保留丢失、拒绝和过期记录。节点日志与真实射频恢复将在后续联调中验证。')
replace(23,'本地巡检平台已形成','巡检平台已接入C回放、Python服务和SQLite，提供27组合成轨迹及独立核查记录。桌面封装支持八页操作、可暂停回放、压力与流量曲线、三维测点聚焦、CSV/JSON保存和重启后恢复。两种EXE在当前电脑完成启动、操作、保存与恢复检查，当前界面使用合成数据，图8展示实际运行页面。')
replace(23,'分级采集新增','分级采集仿真共432组，改变种子、噪声、场景及读取相位。固定1秒组的渐进泄漏与受限均为9/9有效早期，2秒巡航组为17/18，5秒组分别为39/45和42/45。读取次数随周期延长减少，响应代价也随之出现；项目据此保留1 Hz主线，并继续研究2秒、5秒策略。')
replace(23,'新增72组未见','72组未见工况C测试显示，参照负载规律匹配时效果较稳定，失配时出现正常误报。这说明调整门限不足以解决跨工况问题。平台已提供多供压健康曲线拟合，候选参照经独立健康数据核验后启用，后续用实测批次比较固定参照与重新标定。')
replace(23,'控制功能在既有','控制请求已接入页面和数据库，能够区分请求、软件接收、模拟输出及人工复位，并保留重复命令和重启后的状态。节点IO仍待联调，现有程序为LED或蜂鸣器演示提供基础。')

rels={e.get('Id'):e.get('Target') for e in E.fromstring(parts['word/_rels/document.xml.rels'])};figures=[]
for num,name in [(1,'system'),(2,'water'),(3,'model'),(4,'acquisition'),(5,'sampling'),(6,'diagnosis'),(7,'protocol'),(8,'platform')]:
 p=find(18,f'图{num} ');shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0];rid=shape.xpath('.//v:imagedata/@r:id',namespaces=NS)[0];part='word/'+rels[rid]
 path=F/(name+'.png');b=path.read_bytes();iw,ih=Image.open(io.BytesIO(b)).size;width=425;height=width*ih/iw
 style=re.sub(r'width:[\d.]+pt',f'width:{width}pt',shape.get('style'));shape.set('style',re.sub(r'height:[\d.]+pt',f'height:{height:.3f}pt',style));parts[part]=b
 if num==8:
  nodes=p.xpath('./w:r/w:t',namespaces=NS);nodes[0].text='图8 桌面巡检平台监测页面（合成回放）'
  for n in nodes[1:]:n.text=''
 figures.append({'number':num,'source':str(path.relative_to(R)),'part':part,'print_pt':[width,height],'sha256':sha(b)})
# Remove layout-only one-cell wrappers inside the editable narrative rows.
# The school's outer form and all multi-column data tables remain untouched.
unwrapped=0
for ri in range(16,24):
 for table in list(rows[ri].xpath('.//w:tbl',namespaces=NS)):
  trs=table.findall(W+'tr')
  if len(trs)!=1 or len(trs[0].findall(W+'tc'))!=1:continue
  cell=trs[0].find(W+'tc');parent=table.getparent();pos=parent.index(table)
  for c in list(cell):
   if c.tag==W+'tcPr':continue
   cell.remove(c);parent.insert(pos,c);pos+=1
  parent.remove(table);unwrapped+=1
# A standalone subheading must stay with the paragraph it introduces.
for ri in range(16,24):
 for p in rows[ri].xpath('.//w:p',namespaces=NS):
  if not re.fullmatch(r'\d+\s+[^。；：\n]{2,24}',tx(p)):continue
  pr=p.find(W+'pPr')
  if pr is None:pr=E.Element(W+'pPr');p.insert(0,pr)
  keep=pr.find(W+'keepNext')
  if keep is None:keep=E.SubElement(pr,W+'keepNext')
  keep.set(W+'val','1')
# Connect the model limitation to the comparison instead of repeating a heading
# and a second explanation of how the same threshold choice was made.
redundant=find(23,'初期高噪声误报');redundant.getparent().remove(redundant)
p=find(23,'2 诊断方法与可行性分析')
for child in list(p):
 if child.tag==W+'pPr':continue
 p.remove(child)
 if child.xpath('.//w:br',namespaces=NS):break
p=find(23,'3 协议与平台软件');heading=p.xpath('./w:r/w:t',namespaces=NS)[0]
heading.text=heading.text.replace('3 协议与平台软件','2 协议与平台软件',1)
assert protected=={i:E.tostring(rows[i]) for i in protected}
assert refs==[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
assert len(root.xpath('.//m:oMath',namespaces=NS))==11
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(D,'w',ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
record={'source':str(S.relative_to(R)),'source_sha256':sha(source),'output':str(D.relative_to(R)),'output_sha256':sha(D.read_bytes()),'protected_rows':list(protected),'native_math':11,'references':{'Chinese':5,'English':3},'paragraph_changes':changes,'updated_figures':figures,'unwrapped_layout_tables':unwrapped,'changed_parts':[n for n in parts if parts[n]!=original[n]],'visual_review':'pending'}
(OUT/'submission_edit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(T/'artifact.md').write_text('Design authority: '+str(S)+'\nSHA256 '+sha(source)+'\nPreserve A4 school form, blank personal and budget fields, citations and 11 native equations. Edit connected proposal prose and eight images; no new measured performance claims. Output is a separate file. Native WPS export plus PDFium used because packaged render_docx lacks soffice.exe. Inspect every final page.\n',encoding='utf-8')
print('Proposal revised:',len(changes),'paragraphs, eight figures; source retained.')
