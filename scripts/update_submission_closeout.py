"""Local edits of user-approved 111.docx; preserve template, math and graphics."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,re
from lxml import etree as E
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'deliverables/111.docx';OUT=ROOT/'deliverables/大创申报书_研究方案收敛稿.docx'
DATA=ROOT/'application/software_closeout';DATA.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp/software_closeout';TMP.mkdir(parents=True,exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml'}
W='{'+NS['w']+'}';M='{'+NS['m']+'}'
tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
sha=lambda data:hashlib.sha256(data).hexdigest()
original=SRC.read_bytes()
accept=json.loads((ROOT/'simulation/acquisition_pipeline_review/final_acceptance.json').read_text(encoding='utf-8'))
assert accept['passed'];summary=accept['summary'];assert summary['runs']==216 and summary['updates']==130896
with ZipFile(SRC) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
root=E.fromstring(parts['word/document.xml']);rows=root.find(W+'body/'+W+'tbl').findall(W+'tr');assert len(rows)==31
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(25,31))}
old_math=[E.tostring(m) for m in root.xpath('.//m:oMath',namespaces=NS)];assert len(old_math)==27
old_refs=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))];assert len(old_refs)==8
changes=[]
sample=next(p for p in rows[18].xpath('.//w:p',namespaces=NS) if tx(p).startswith('总体目标是'))
def run(value):
    r=E.Element(W+'r');pr=E.SubElement(r,W+'rPr');font=E.SubElement(pr,W+'rFonts')
    for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:font.set(W+k,v)
    for key in ['sz','szCs']:E.SubElement(pr,W+key).set(W+'val','21')
    t=E.SubElement(r,W+'t');t.text=value;return r
def paragraph(value):
    p=deepcopy(sample)
    for c in list(p):
        if c.tag!=W+'pPr':p.remove(c)
    p.attrib.clear();p.append(run(value));return p
def find(ri,prefix):
    matches=[p for p in rows[ri].xpath('.//w:p',namespaces=NS) if tx(p).startswith(prefix)]
    assert len(matches)==1,(ri,prefix,len(matches));return matches[0]
def replace(ri,prefix,value):
    p=find(ri,prefix);assert not p.xpath('.//m:oMath|.//v:imagedata',namespaces=NS),prefix
    before=tx(p)
    breaks=p.xpath('./w:r[w:br]',namespaces=NS)
    if breaks:
        last=breaks[-1];idx=p.index(last)
        # Existing title/heading and its line breaks remain; only following body changes.
        assert len(last)==1 or len(last.xpath('./w:t',namespaces=NS))==0
        for child in list(p)[idx+1:]:p.remove(child)
        p.append(run(value))
    else:
        for child in list(p):
            if child.tag!=W+'pPr':p.remove(child)
        p.append(run(value))
    changes.append(dict(prefix=prefix,before=before,after=tx(p)));return p
def add_after(p,new):
    p.getparent().insert(p.getparent().index(p)+1,new)
replace(16,'一、项目简介',
 '本项目面向南疆规模化棉田膜下滴灌的支管巡检，研制集双压力—流量感知、异常诊断、LoRa传输和巡检管理于一体的物联网原型系统。围绕泄漏、局部过流受限与正常供压变化容易混淆的问题，研究健康参照约束下的联合诊断，形成支管及测点区段的异常提示。以固定频率采集建立测量基线，设置短窗关注与主窗确认，并研究事件触发分级采集的响应与开销取舍；采用事件优先缓存、接收确认和有界恢复传输，保持测量质量及事件身份的一致性。通过双支路清水台架、独立参考测量和无线对照评价误报、漏检、有效提前量及远端延迟，完成原型、实验数据、研究报告和控制请求演示，为多支管协同监测及后续隔离控制提供基础。')
replace(18,'总体目标是',
 '总体目标是研制能够采集支管状态、形成异常线索、可靠接收事件并支持巡检复核的物联网原型系统。系统由双压力—流量感知节点、LoRa接收端和本地Web平台组成，依次完成参考标定、健康建模、质量检查、异常诊断、无线接收及处置复测。研究围绕联合观测的可辨识边界和采集通信策略的响应代价展开：先建立固定1Hz测量基线，再比较分级采集及事件优先传输。双支路清水台架承担可重复验证；控制采用软件模拟和执行接口预留，使感知、诊断与处置在同一系统中衔接。')
replace(18,'初版采集以',
 '基线采用1Hz采集和连续脉冲计数，十秒主窗由十一处有效累计端点形成，三秒短窗用于提示需要加密观察的变化。SEN0549按540脉冲/L计算，十秒计数窗口的单脉冲分辨率为0.01111L/min；窗口长度与确认条件共同影响提示时间。每帧保存两路压力转换时刻及计数锁存时刻，迟到、缺测或复位分别记录，窗口仅使用真实有效端点。压力、流量分别采用不少于五个工作点标定，每点至少三次独立读取，并增加升降压、共同压力和容积或称量计时对照，随批次保存参考值及标定残差。')
replace(18,'在固定周期采集完成',
 '事件触发采集在固定频率基线通过后开展。正常阶段连续计数并按候选周期读取压力，累计偏离或持续变化触发较短周期；恢复稳定并满足保持时间后返回原周期。触发用于调度采集，不直接认定故障。针对低频观测可能错过短时变化的问题，分别记录未观测区间、触发时刻和实际读取次数，分析渐进故障与短时异常的响应差异，确定策略适用范围。')
replace(18,'采集、完整记录和无线发送',
 '采集、完整原始记录与无线发送分别设置。固定1秒读取为当前基线，2秒、5秒为首轮间隔对照，并以更长周期分析迟检边界；正常状态上报采用60秒候选。分级采集使用实际时间窗和真实观测次数判断，不以保持值补齐未测数据。周期根据故障发展时间和误触发约束选择，不能仅按消息数量决定。图5为拟研究的分级采集与模拟处置流程；其采集调度将独立于固定1Hz诊断基线验收。')
anchor=find(18,'4 渐进故障诊断')
extra=paragraph('平方根负载特征作为水力解释及方法对照，实际判据采用经独立健康检查的经验压力—流量关系。健康预测流量与相对偏离分别定义为：')
def mr(value):
    r=E.Element(M+'r');rp=E.SubElement(r,W+'rPr');f=E.SubElement(rp,W+'rFonts');f.set(W+'ascii','Cambria Math');f.set(W+'hAnsi','Cambria Math');E.SubElement(rp,W+'sz').set(W+'val','21');E.SubElement(r,M+'t').text=value;return r
def group(tag,*nodes):
    e=E.Element(M+tag)
    for n in nodes:e.append(n)
    return e
def sub(base,index):return group('sSub',group('e',mr(base)),group('sub',mr(index)))
def frac(n,d):return group('f',group('num',n),group('den',d))
qref=sub('Q','ref');pstar=sub('P','*');p1=sub('P','1')
eq=group('oMath',deepcopy(qref),mr('='),mr('g'),mr('a'),group('sSup',group('e',mr('('),frac(p1,pstar),mr(')')),group('sup',mr('n'))))
extra.append(eq);extra.append(run('，'))
extra.append(group('oMath',mr('e'),mr('='),frac(mr('Q'),deepcopy(qref)),mr('−'),mr('1')))
extra.append(run('。其中参考压力为100kPa，指数及曲线系数由参考标定确定，局部增益由监测开始前的已核验健康区段确定。主诊断以十秒观测计算相对流量偏离和阻力变化，门限结合健康残差的稳健尺度与预设下限，在验证前固定；连续五次满足条件后输出候选模式。三秒短窗连续两次越限仅形成待复核提示，不替代主诊断确认，也不直接触发控制。'))
add_after(anchor,extra)
replace(18,'算法输出包括',
 '输出分别记录测量是否可用、短窗是否关注和主窗候选模式，并附配置、健康参照版本及建议核查区段。数值参照缺失或独立健康许可不足时不启用故障判断；缺测、越量程和时序异常清除受影响的窗口，恢复后重新积累。正常下游负载增加可能与泄漏产生相同观测，量程内压力漂移也可能造成受限候选，因此候选模式须结合阀态、负载和人工复测解释。工况检查的收益通过正常切换、切换期间故障和未知负载对照检验，不将暂缓判断等同于没有故障。')
replace(18,'图7展示',
 '图7展示正常接收及确认丢失后的同身份重传。当前主机协议的遥测、事件和确认帧分别为55、57和24B，采用CRC校验与COBS定界。业务缓存限定16槽，普通遥测保留最新一条；事件优先接纳，已接纳事件不因新遥测而被替换。每条业务消息初始发送至多八次，恢复阶段至多四次，保留期限为300秒；超过期限或事件占满缓存时分别记录过期与拒绝。实施阶段完成节点日志及真实串口联调，并独立核验掉电恢复；模块缓冲状态不能代替远端接收确认。')
replace(18,'通信试验比较',
 '通信试验比较快周期、慢周期、事件与周期状态、事件优先有界恢复四种方案，统一本地诊断轨迹、事件定义、载荷和接收确认规则。普通遥测的替代与事件的保存分别评价，不通过删减故障事件降低开销。统计远端告警延迟P50/P95、期限内送达比例、未送达数量、重传、容量拒绝和源端过期，并保留FIFO等待61秒的历史反例。无线发送次数、字节数及占用表示通信开销；整机能量用独立电流测量评价，长中断和确认全丢条件下报告真实缺口。')
# Existing native R symbol stays in this revised paragraph.
p=find(23,'当前合成基线实现');ts=p.xpath('.//w:t',namespaces=NS);assert len(p.xpath('.//m:oMath',namespaces=NS))==1
before=tx(p);ts[0].text='针对早期固定门限在高噪声下的误报，已建立健康经验参照、稳健门限和质量门控，并保留区段阻力'
for t in ts[1:]:t.text=''
ts[-1].text='的联合判断。固定1Hz、十秒主窗和五次确认作为当前基线，三秒短窗仅输出待复核。便携C整数内核与独立有理数参考在216条合成轨迹、130,896次更新中输出一致；另构造的压力舍入、预测表插值及工作域边界样例存在差异，已保存为验证边界，不据此宣称任意输入等价或实物识别准确率。采集引脚、电平及20,000组理想计数枚举为接口准备，脉冲抖动与实物时序在台架测定。'
changes.append(dict(prefix='当前合成基线实现',before=before,after=tx(p)))
replace(23,'3 协议与平台软件',
 '已完成采集适配、C诊断和协议快照的主机联调，对迟到、缺测、越量程、重复及重叠转换、计数复位和序号中断开展定向检查。216条既有合成轨迹逐更新映射到快照和事件，与冻结的九字段诊断结果一致；80组端到端回放覆盖正常链路、随机丢失、60秒中断和确认全丢，20组正常链路收到全部生成事件。回放保留丢失、拒绝和过期记录，不把重复消息写为新采集；这些结果验证软件语义，STM32目标编译、真实无线和节点掉电持久化仍在实施阶段分别验收。')
replace(23,'事件采集已完成',
 '分级采集已完成四策略合成回放，检查调度不使用未来或未采样观测。既有模型中，固定60秒读取的泄漏组为0/20有效早期；更长周期的相位分析也出现明显迟检。该结果支持保留1Hz工程基线，并将分级采集作为独立研究任务：围绕2秒、5秒等候选间隔检验覆盖与触发，再根据真实故障发展时间扩展。读取和发送减少量与实测能耗分别评价，不能把回放次数写成独立物理实验。')
replace(23,'另对5至600秒',
 '前期模型还显示正常B支路切换会增加触发开销，短时变化可能在主窗确认前恢复，量程内漂移和未知健康负载仍可造成模式歧义。因此，正式实验同时保存正常干扰、短时异常和跨负载失败实例，采用相同误报约束、独立操作标签及留出批次评价改进。当前软件具备保存质量与候选模式的条件，故障原因、最优采集周期和整机节电须由实测进一步核验。')
# Distinguish initial model evidence from the subsequent noise-aware implementation.
p=find(23,'诊断模型版本为');t=p.xpath('.//w:t',namespaces=NS)[0];t.text=t.text.replace('诊断模型版本为','初始诊断模型版本为')
# Explicitly show this as the proposed adaptive route, not current validated low-frequency firmware.
p=find(18,'图5 ');p.xpath('.//w:t',namespaces=NS)[0].text='图5 拟研究的事件触发采集与模拟控制流程'
# No redundant new figure; all ten accepted graphics retain their original bytes/ratios.
assert {i:E.tostring(rows[i]) for i in protected}==protected
new_math=[E.tostring(m) for m in root.xpath('.//m:oMath',namespaces=NS)]
kept=[x for x in new_math if x in old_math];assert kept==old_math and len(new_math)==29
assert old_refs==[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,value in parts.items():z.writestr(name,value)
assert SRC.read_bytes()==original
with ZipFile(SRC) as a,ZipFile(OUT) as b:
    altered=[name for name in a.namelist() if a.read(name)!=b.read(name)]
assert altered==['word/document.xml']
record=dict(source=SRC.relative_to(ROOT).as_posix(),source_sha256=sha(original),output=OUT.relative_to(ROOT).as_posix(),
            output_sha256=sha(OUT.read_bytes()),changed_parts=altered,protected_rows=list(protected),
            preserved_native_math=27,added_native_math=2,total_native_math=29,references_Chinese=5,references_English=3,
            original_images_preserved=True,software_acceptance_sha256=sha((ROOT/'simulation/acquisition_pipeline_review/final_acceptance.json').read_bytes()),
            visual_review_status='pending',changes=changes)
(DATA/'edit_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(TMP/'artifact.md').write_text('School application edit using latest user-approved 111.docx. Preserve all cover/personal/approval/budget fields, 31-row structure, eight references and ten images. Update only method and software evidence. Native math retained, two formulas added. Render and visually review every final page; no claim of physical hardware verification.\n',encoding='utf-8')
print('Saved separate application: 31 rows, 29 native equations, 8 references, all original images unchanged.')
