"""Update the accepted school form with evidence verified on 2026-10-07."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
from PIL import Image
import json,re,hashlib,io
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'application/current_revision';TMP=ROOT/'tmp/current_application_review'
SOURCE=ROOT/'deliverables/大创申报书_申报表达修订稿.docx';OUT=ROOT/'deliverables/大创申报书_现阶段更新稿.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}';M='{'+NS['m']+'}';tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS));sha=lambda b:hashlib.sha256(b).hexdigest()
source=SOURCE.read_bytes()
with ZipFile(io.BytesIO(source)) as z:parts={n:z.read(n) for n in z.namelist()}
original=parts.copy();root=E.fromstring(parts['word/document.xml']);rows=root.find(W+'body/'+W+'tbl').findall(W+'tr')
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(24,31))}
refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))];changes=[]
def find(i,prefix):
 ps=[p for p in rows[i].xpath('.//w:p',namespaces=NS) if tx(p).startswith(prefix)];assert len(ps)==1,(i,prefix,len(ps));return ps[0]
def run(t):
 r=E.Element(W+'r');pr=E.SubElement(r,W+'rPr');f=E.SubElement(pr,W+'rFonts')
 for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:f.set(W+k,v)
 for k in ['sz','szCs']:E.SubElement(pr,W+k).set(W+'val','21')
 E.SubElement(r,W+'t').text=t;return r
def fill(p,chunks,heading=False):
 before=tx(p);br=p.xpath('./w:r[w:br]',namespaces=NS);stop=p.index(br[-1]) if heading and br else -1
 for i,c in enumerate(list(p)):
  if i>stop and c.tag!=W+'pPr':p.remove(c)
 for c in chunks:p.append(run(c) if isinstance(c,str) else deepcopy(c))
 changes.append({'before':before,'after':tx(p)})
def replace(i,prefix,text,heading=False):fill(find(i,prefix),[text],heading)
replace(18,'台架结构围绕','台架结构围绕测点安装、故障切换和重复计量设计。图3呈现当前参数化三维布局：A支路测量顺序与水路方案一致，B支路承担共源健康负载切换，采集盒位于前侧，泄漏收集装置与电气区域分开布置。设计增加带过线开口的防溅板，并检查盒盖开启、管路避让和容器取放空间。模型用于布局与装配准备，采购后按实际器件核定尺寸，实物阶段再完成排气、密封、固定及计量稳定性验证。')
replace(18,'泄漏量采用','泄漏量采用独立收集与计时测量。台架按20秒分次取样设计，收集容器有效容量要求不低于440mL，并保留自由出流空间；使用前以实测核定有效容量，检查溢流、出口淹没及重复取样误差。长时运行另设排水并独立验证。该参考测量不依赖诊断输出，用于确定故障程度以及比较提示时刻。')
replace(18,'在固定采集基线稳定后','在固定1Hz采集稳定后，研究事件触发分级采集。正常阶段按候选周期读取压力，持续记录累计脉冲；观测到持续偏离时切换至1秒读取，恢复稳定后返回原周期。触发判断只使用已取得的压力与计数，不以保持旧读数代替新测量。现阶段已完成独立策略仿真，后续结合真实计数、压力时序和窗口重建实现节点调度，比较渐进故障、短时变化及正常负载切换时的响应。')
replace(18,'采集与无线发送分开配置','压力读取与无线发送分别配置。固定1秒读取作为主线，2秒、5秒巡航间隔作为研究对照；正常上报以60秒为候选，异常事件优先发送。稀疏读取的仿真已显示漏检与迟发代价，因此不直接把更长周期设为默认配置。图5给出拟实现的分级采集及模拟处置关系，正式对照同时改变异常出现相位，依据提示及时性、误触发和通信开销选择参数。')
# Native editable mathematics, matching the current C residual channel.
def mr(t):
 r=E.Element(M+'r');rp=E.SubElement(r,M+'rPr');E.SubElement(rp,M+'sty').set(M+'val','p' if t in ['=','−','1','(',')'] else 'i')
 wp=E.SubElement(r,W+'rPr');E.SubElement(wp,W+'rFonts').set(W+'ascii','Cambria Math');E.SubElement(wp,W+'sz').set(W+'val','21');E.SubElement(r,M+'t').text=t;return r
def sub(a,b):
 n=E.Element(M+'sSub');E.SubElement(n,M+'sSubPr');E.SubElement(n,M+'e').append(mr(a));E.SubElement(n,M+'sub').append(mr(b));return n
math=E.Element(M+'oMath');math.extend([sub('e','Q'),mr('=')]);fraction=E.SubElement(math,M+'f');E.SubElement(fraction,M+'fPr');E.SubElement(fraction,M+'num').append(mr('Q'));den=E.SubElement(fraction,M+'den');den.extend([sub('Q','h'),mr('('),sub('P','1'),mr(')')]);math.extend([mr('−'),mr('1')])
p=find(18,'4 支管异常');old_math=p.xpath('.//m:oMath',namespaces=NS)
fill(p,['诊断以健康状态为参照，采用相对流量残差',math,'与区段阻力估计',old_math[1],'进行联合判断。健康曲线Qₕ(P₁)给出相同下游压力下的正常流量，阻力估计与健康区段阻力作差后反映局部受限。流量持续正向偏离而区段阻力基本稳定时形成等效泄漏候选，阻力持续增加时形成受限候选；两类特征冲突时提示异常待检查。图6为固定1Hz基线的处理流程。'],True)
replace(18,'诊断前先开展独立标定','诊断前在不同供压点开展独立健康标定，建立压力—流量经验曲线和区段阻力参照。平台已提供健康记录导入与候选曲线拟合，用于检查数据范围和拟合偏差；生成的候选参数须经独立健康核验与未参与拟合的批次验证，才能用于节点判断。正式故障试验固定参照版本，并记录正常阀门切换与负载状态。通过跨供压、跨负载对照，评价固定参照和重新标定的适用范围。')
replace(18,'节点设置短窗提示','节点设置短窗关注与主窗候选两种结果。三秒短窗连续两次正向越限时提示复核；十秒主窗同一候选连续五次成立后输出持续候选。二者分别记录，短窗关注不直接触发控制，持续候选也需结合工况与人工核查确定实际原因。短窗须具有独立标定依据，窗口未完整建立或观测无效时标明不可用，不以旧数据填补正常状态。')
p=find(18,'6 巡检平台');platform_math=p.xpath('.//m:oMath',namespaces=NS);assert len(platform_math)==2
fill(p,['本地Web平台按功能划分为运行总览、支管监测、异常事件、设备链路、历史记录、策略实验、试验台架和系统设置八个页面。总览集中提示当前工作，监测页面展示',platform_math[0],'、',platform_math[1],'、Q及窗口特征，事件页面组织查看、处置和复测；设备页面核对连接状态，历史页面按会话检索与导出。策略实验用于采样对照和参照标定，台架页面用于结构检查与模拟控制，设置页面维护配置身份。图8为当前监测页面局部，各页面围绕同一支管和事件协作。'],True)
replace(18,'平台将','平台将“已查看、处置、复测”作为独立维护步骤，保留原始候选快照并追加核查记录。现阶段已实现Python本地服务与SQLite数据库接入，核查记录、模拟命令和历史会话能够在服务重启后保留。图8数据来自C程序合成回放，不代表现场监测；实施阶段将把串口和LoRa接收数据接入同一记录流程，核对采集时刻、测量质量及传输状态。断连时显示最近有效记录及连接状态，避免将历史数据误作当前正常。')
replace(18,'控制联动作为','控制联动服务于异常核查后的处置演示，本期采用软件模拟与LED或蜂鸣器输出。平台已实现人工发起请求、软件接收、模拟执行和人工复位的状态记录；实施中再联调节点IO，核验重复命令不重复执行，并研究有效观测、明确工况和人工确认下的请求条件。接收确认、演示输出与真实执行反馈分别呈现。实际阀门不列为本期必做任务，以免改变原诊断试验的水力条件。')
replace(18,'六模块Web','八页面Web、真实接入、模拟请求及维护记录')
replace(18,'后续首先拓展','后续首先研究不同供压和负载条件下的健康参照适配。现有跨工况合成测试表明，供压变化与负载规律变化对判断的影响并不相同，固定参照不能直接覆盖任意负载。拟比较固定参照、多供压点重新标定和少量健康数据修正，按日期与工况设置独立验证批次，考察误报、漏检及标定工作量。这一方向由本期台架和平台标定工具承接，为轮灌条件变化下的应用提供依据。')
replace(20,'（2）','（2）围绕健康参照开展渐进异常辨识与工况适配。以双压力和流量建立正常运行关系，结合稳健门限、双时间窗和连续确认提示渐进变化。通过固定参照与重新标定对照，分析不同负载和供压下的判断变化，将工况记录与复测纳入验证，减少把正常调节直接判为故障的情况。研究重点在于可复核的早期提示及参照适用范围，并由独立故障操作检验。')
replace(21,'六、项目预期成果','预期研制1套支管故障诊断物联网原型，包括双压力—流量感知节点、LoRa接收端、双支路清水台架及本地巡检平台。实现稳定采集、分级采集对照、异常提示、可靠接收、核查复测和控制请求模拟，形成完整巡检流程。提交结构与接口设计、节点及前后端程序、配置、使用说明和结题报告；平台采用本地部署，并研究便携桌面封装，便于台架操作与成果演示。以一个监测单元完成可演示、可复测的原型验证。',True)
replace(22,'诊断与分级采集、','诊断与分级采集、独立故障及正常干扰、参照适配对照')
replace(22,'无线收发、Web接入','真实无线与串口接入、本地平台、IO演示及处置复测')
replace(23,'八、已有基础','前期已完成文献梳理、双支路水路方案、参数化装配、采集接口分析及本地巡检平台，形成模型、程序、配置和图源。三维模型与水路保持一致的测点顺序，新增防溅板及过线开口后，已检查新增板与原构件的实体交集，并完成局部间隙、容器取放和分次计量容量分析。当前模型含207个有效实体，能够按整体、测点、电气和泄漏计量局部查看，为采购装配提供设计基础。现有成果为设计、仿真与主机软件验证，实物制造、真实无线和田间应用尚待实施。',True)
replace(23,'离线Web已实现','本地巡检平台已形成八个功能页面，接入C算法回放、Python服务和SQLite存储，提供27组压力带噪合成轨迹，覆盖正常运行、供压切换、泄漏、受限、漂移、短时异常及采集质量问题。候选快照与核查记录分开保存，支持历史会话检索、CSV/JSON导出和服务重启后读取。已核查重复报文、校验错误、身份冲突及模拟命令的处理，接收确认对应已提交的数据。现有成果说明本地主机流程已贯通，实际串口与射频接入在实施阶段验证。')
replace(23,'分级采集已完成','分级采集新增432组仿真组合，覆盖3个测试种子、3档压力噪声、6类场景及1秒、2秒、5秒读取间隔的全部相位。渐进泄漏和受限在固定1秒组分别为9/9有效早期，2秒巡航组分别为17/18，5秒组分别为39/45和42/45；正常场景平均压力读取次数依次为601.0、411.6和273.6。结果显示减少读取会带来响应代价，支持保留1Hz主线并对2秒、5秒策略继续验证。上述为共享模型下的仿真组合，不能作为独立实物试次，也不据此计算节电率。')
replace(23,'前期模型还显示','新增72组未见工况C程序测试，改变供压、负载指数、噪声及随机种子。参照负载规律匹配时，正常对照8组无候选误报，两类故障各8组满足该模型的有效早期判据；负载规律失配时出现正常误报，说明只改变门限不足以保证跨工况应用。另保留短时变化漏检、压力漂移以及正常切换增加触发次数等记录。平台已提供多供压健康曲线拟合工具，拟合结果仅形成候选参照，不自动批准或覆盖运行配置，后续通过独立实测确定适配效果。')
replace(23,'控制功能已完成','控制功能在既有12项主机状态检查基础上，已接入网页操作和数据库记录，区分请求、软件接收、模拟输出及人工复位，检查重复命令和重启后的历史状态。页面明确标识模拟模式，当前未接入节点IO或实际阀门。相关程序与操作记录为LED或蜂鸣器联调提供基础，不将软件执行状态写成实际关阀效果。')
# Replace two media parts while retaining original VML inline placement and captions.
rels={e.get('Id'):e.get('Target') for e in E.fromstring(parts['word/_rels/document.xml.rels'])};figures=[]
for number,asset,caption,width in [(3,'model_publication.png','图3 双支路验证台架三维布局（概念模型）',425),(8,'platform_publication.png','图8 巡检平台监测页面局部（C程序合成回放）',425)]:
 p=find(18,f'图{number} ');old=tx(p);textnodes=p.xpath('./w:r/w:t',namespaces=NS);assert textnodes;textnodes[0].text=caption
 for t in textnodes[1:]:t.text=''
 shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0];rid=shape.xpath('.//v:imagedata/@r:id',namespaces=NS)[0];part='word/'+rels[rid]
 image_path=DATA/asset;b=image_path.read_bytes();iw,ih=Image.open(io.BytesIO(b)).size;height=width*ih/iw
 style=shape.get('style');style=re.sub(r'width:[\d.]+pt',f'width:{width:.3f}pt',style);style=re.sub(r'height:[\d.]+pt',f'height:{height:.3f}pt',style);shape.set('style',style);parts[part]=b
 figures.append({'number':number,'caption':caption,'part':part,'source':str(image_path.relative_to(ROOT)),'size_px':[iw,ih],'print_pt':[width,height],'sha256':sha(b)})
# Make room for the complete four-line figure-9 interpretation; preserve aspect.
p=find(23,'图9 ');shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0]
style=shape.get('style');dims={k:float(v) for k,v in re.findall(r'(width|height):([\d.]+)pt',style)}
height=dims['height']*400/dims['width'];style=re.sub(r'width:[\d.]+pt','width:400pt',style);shape.set('style',re.sub(r'height:[\d.]+pt',f'height:{height:.3f}pt',style))
# Keep short, meaningful paragraphs together instead of a single opening line at page foot.
for ri,prefix in [(18,'节点设置短窗关注'),(18,'控制联动服务于'),(20,'（2）'),(23,'本地巡检平台已形成')]:
 p=find(ri,prefix);pr=p.find(W+'pPr');keep=pr.find(W+'keepLines')
 if keep is None:keep=E.SubElement(pr,W+'keepLines')
 keep.set(W+'val','1')
 # WPS ignores paragraph keepLines across an outer form row. A borderless,
 # unsplittable single-cell row keeps this short paragraph intact in Word/WPS.
 parent=p.getparent();position=parent.index(p);parent.remove(p)
 table=E.Element(W+'tbl');tp=E.SubElement(table,W+'tblPr')
 E.SubElement(tp,W+'tblW',attrib={W+'w':'9060',W+'type':'dxa'});E.SubElement(tp,W+'jc').set(W+'val','center')
 borders=E.SubElement(tp,W+'tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:E.SubElement(borders,W+side).set(W+'val','nil')
 margins=E.SubElement(tp,W+'tblCellMar')
 for side in ['top','left','bottom','right']:E.SubElement(margins,W+side,attrib={W+'w':'0',W+'type':'dxa'})
 grid=E.SubElement(table,W+'tblGrid');E.SubElement(grid,W+'gridCol').set(W+'w','9060')
 tr=E.SubElement(table,W+'tr');E.SubElement(E.SubElement(tr,W+'trPr'),W+'cantSplit')
 tc=E.SubElement(tr,W+'tc');E.SubElement(E.SubElement(tc,W+'tcPr'),W+'tcW',attrib={W+'w':'9060',W+'type':'dxa'});tc.append(p);parent.insert(position,table)
 if parent[-1].tag==W+'tbl':
  blank=E.SubElement(parent,W+'p');bp=E.SubElement(blank,W+'pPr');E.SubElement(bp,W+'spacing',attrib={W+'before':'0',W+'after':'0',W+'line':'1',W+'lineRule':'exact'})
assert protected=={i:E.tostring(rows[i]) for i in protected};assert refs==[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
assert len(root.xpath('.//m:oMath',namespaces=NS))==11
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
record={'date':'2026-10-07','source':str(SOURCE.relative_to(ROOT)),'source_sha256':sha(source),'output':str(OUT.relative_to(ROOT)),'output_sha256':sha(OUT.read_bytes()),'changed_parts':[n for n in parts if parts[n]!=original[n]],'protected_rows':list(protected),'native_math':11,'references':{'Chinese':5,'English':3},'paragraph_changes':changes,'updated_figures':figures,'evidence_files':['simulation/platform_upgrade/web_data.json','simulation/platform_upgrade/scheduling_trials.json','simulation/platform_upgrade/cross_operating_summary.json','simulation/platform_upgrade/service_acceptance.json','simulation/platform_upgrade/browser_acceptance.json','application/models/system_upgrade/bench_scene.json'],'visual_review_status':'pending'}
(DATA/'edit_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(TMP/'source.docx').write_bytes(source)
(TMP/'artifact.md').write_text('Retained authority: deliverables/大创申报书_申报表达修订稿.docx, SHA256 '+sha(source)+'\nA4 school table form; preserve personal/team/budget/signature rows 0-15 and 24-30, styles, 8 references (5 Chinese, 3 English), superscript citations; 11 native equations. Edit proposal prose by unique row/prefix locators. Replace only actual-render figures 3 and 8 at natural aspect ratio; retain other 8 figures and page geometry. Body宋体10.5pt, Latin Times New Roman; centered data tables and captions. Render and inspect every page. Simulation and host software are not physical performance evidence.\n',encoding='utf-8')
print(f'Wrote {OUT.name}: {len(changes)} paragraph updates; 2 current actual-render figures; 11 native equations; protected form and references unchanged.')
