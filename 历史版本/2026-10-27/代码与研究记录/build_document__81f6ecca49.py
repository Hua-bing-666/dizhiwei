from pathlib import Path
import hashlib,json
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

B=Path(__file__).resolve().parents[1];ROOT=B.parents[1]
source=B/'code/source.docx';old=Document(source);texts=[p.text for p in old.paragraphs]
d=Document(source)
body=d._element.body
for child in list(body):
 if child.tag!=qn('w:sectPr'):body.remove(child)
from docx.opc.constants import RELATIONSHIP_TYPE as RT
for relid,rel in list(d.part.rels.items()):
 if rel.reltype==RT.IMAGE:d.part.drop_rel(relid)
def font(r,size=10.5,bold=False):
 r.font.name='Times New Roman';r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=RGBColor(0,0,0)
 r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
def p(text='',size=10.5,bold=False,heading=False,page=False):
 x=d.add_paragraph();font(x.add_run(text),size,bold)
 pr=x._p.get_or_add_pPr();snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0');pr.append(snap)
 f=x.paragraph_format;f.line_spacing=1.2;f.space_before=Pt(0);f.space_after=Pt(4)
 f.widow_control=True;f.keep_together=True;f.keep_with_next=heading;f.page_break_before=page
 return x
def figure(name,caption,note,page=False):
 x=p(page=page);x.clear();x.alignment=WD_ALIGN_PARAGRAPH.CENTER
 x.paragraph_format.keep_with_next=True;x.paragraph_format.line_spacing=1
 x.paragraph_format.space_before=Pt(3);x.paragraph_format.space_after=Pt(2)
 x.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.6))
 x._p.xpath('.//wp:docPr')[0].set('descr',caption+' 准稳态合成仿真 非实物试验')
 x=p(caption,9,True,heading=True);x.alignment=WD_ALIGN_PARAGRAPH.CENTER
 x.paragraph_format.space_after=Pt(3)
 x=p(note,9);x.paragraph_format.line_spacing=1.1;x.paragraph_format.space_after=Pt(5)

p('八、已有基础',12,True,True)
p('8.1 系统设计与前期论证',10.5,True,True)
p(texts[1])
intro=p('前期诊断采用流量压力特征 ')
from lxml import etree
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
def mathrun(text):
 el=etree.Element('{'+M+'}r');etree.SubElement(el,'{'+M+'}t').text=text;return el
def sub(base,index):
 el=etree.Element('{'+M+'}sSub');etree.SubElement(el,'{'+M+'}e').append(mathrun(base));etree.SubElement(el,'{'+M+'}sub').append(mathrun(index));return el
def equation_k():
 el=etree.Element('{'+M+'}oMath');el.append(mathrun('K='));frac=etree.SubElement(el,'{'+M+'}f')
 etree.SubElement(frac,'{'+M+'}num').append(mathrun('Q'));den=etree.SubElement(frac,'{'+M+'}den')
 rad=etree.SubElement(den,'{'+M+'}rad');pr=etree.SubElement(rad,'{'+M+'}radPr');etree.SubElement(pr,'{'+M+'}degHide').set('{'+M+'}val','1')
 etree.SubElement(rad,'{'+M+'}deg');etree.SubElement(rad,'{'+M+'}e').append(sub('P','1'));return el
def equation_r():
 el=etree.Element('{'+M+'}oMath');el.append(mathrun('R='));frac=etree.SubElement(el,'{'+M+'}f');num=etree.SubElement(frac,'{'+M+'}num')
 num.append(sub('P','0'));num.append(mathrun('−'));num.append(sub('P','1'))
 den=etree.SubElement(frac,'{'+M+'}den');sup=etree.SubElement(den,'{'+M+'}sSup')
 etree.SubElement(sup,'{'+M+'}e').append(mathrun('Q'));etree.SubElement(sup,'{'+M+'}sup').append(mathrun('2'));return el
intro._p.append(equation_k());font(intro.add_run(' 与等效阻力 '));intro._p.append(equation_r())
font(intro.add_run('。先检查故障演变及原因歧义，再对冻结参数后的候选方法开展随机噪声对照。以下均为尚未经实物标定的准稳态合成仿真。'))
figure('图8-1_泄漏信号与判据演变','图8-1 渐进泄漏的信号与判据演变',
 '注：初始K/R模型，固定使用原批次首个种子10300，压力噪声σ=3 kPa。a为十秒因果均值，180—300秒开启B支路；b、c为相对健康标定的K变化和R残差。灰区为360—540秒故障推进段，水平虚线为实际单侧门限K增加6%、R增加0.6 kPa/(L/min)²。黑点线为403秒确认，灰虚线为454秒达到15%流量偏离的模型参照，提前51秒；该参照非农艺标准。')
p('本例中，泄漏使等效出流能力增大，流量上升、下游压力下降，K持续增加并越限；R残差未形成受限候选。B支路切换则使三通道共同变化，展示了仅凭流量波动判定故障的局限。受限过程的互补示例见补图S1。')

figure('图8-2_特征轨迹与诊断歧义','图8-2 特征轨迹揭示观测歧义',
 '注：初始K/R模型，种子10300、σ=3 kPa，360—600秒逐秒轨迹。泄漏与未知正常负载严格重合；测压漂移终值10 kPa。彩色圆点为终值，黑点为泄漏起点。虚线为K/K₀=1.06、ΔR=0.6；灰区仅表示两个正向门限均未越过。',page=True)
p('四档噪声、20个种子的320条反例及对照轨迹中，泄漏与未知负载的三通道观测逐种子一致。测压漂移又可抬高R而产生受限候选，原因判别仍需操作记录、健康标定、跨负载留出评价与独立核查。')
p('原12种子的324条方法记录已逐条复现。冻结参数后，100个留出种子完成三档噪声下900条轨迹、2700条方法记录。图8-3中稳健门限对两种故障均为99/100条有效早期、正常误报2/100；累积组合分别为98/100、9/100，支持优先验证稳健门限。')
figure('图8-3_候选方法与不确定性','图8-3 高噪声下的候选方法比较',
 '注：每点100种子，横线为Wilson 95%区间。a、b为无前期误报、首次模式正确且早于15%模型参照的比例；c为每条3470秒正常监测中出现误报的比例。不同场景复用同一组噪声种子，不合并为独立实物试验；其余噪声档位保留在随附数据中。')

p('为检查小幅故障，以100个新种子扫描5%—30%的终值流量偏离，完成3000条故障轨迹和300条匹配健康对照。图8-4显示，较大故障中的高检出比例不能外推至任意小故障；例如0.3 kPa下5%泄漏仅2/100条正确提示。',page=True)
figure('图8-4_故障幅值与检出响应','图8-4 故障幅值与正确提示比例',
 '注：稳健门限，每点100种子，阴影为Wilson 95%区间。仅测试5、10、15、20、30%五档，连线用于阅读，不是连续检出概率模型。正确提示要求600秒内无前期误报且故障后首次候选正确，与图8-3的有效早期指标不同。曲线重合处保留实际数值，不作人为错位；噪声助推小幅越限不表示加噪有益。')
p('另以16个配对种子、两种故障情景比较1、2、5秒巡航周期，遍历全部整数相位，得到256次采集回放。图8-5按种子内先平均相位再统计，展示压力读取次数与响应余量；触发后转入1 Hz加密采集，读取次数不等于实际能耗。')
figure('图8-5_采集次数与响应余量','图8-5 采集次数与响应余量的关系',
 '注：σ=3 kPa，点为16个种子的中位数，横纵误差线为四分位区间。标注为巡航周期；每个种子内先平均不同相位。渐进泄漏可减少读取，切换期快泄漏较早触发加密，节省空间较小。本批256次回放均有效早期，不外推至其他工况或实测节能率。提前量经验分布另见补图S2。')

p(texts[8],page=True)
for i in range(9,19):
 x=p(texts[i],bold=i in [9,15],heading=i in [9,15])
 if i in [9,15]:x.paragraph_format.space_before=Pt(7)
target=B/'第八部分_机制与轨迹修订稿.docx';d.save(target)
preserve=[1,8,9,10,11,12,13,14,15,16,17,18]
newtexts=[x.text for x in d.paragraphs]
for i in preserve:assert texts[i] in newtexts
audit=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
 preserved_source_paragraphs=preserve,unrelated_original_platform_claims_not_revalidated=True,figures=5,inline_width_cm=14.6,
 actual_positive_thresholds_only=True)
(B/'evidence/document_edit_record.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
