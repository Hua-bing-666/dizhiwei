from pathlib import Path
import json,hashlib,sys
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

B=Path(__file__).resolve().parents[1];ROOT=B.parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'tmp/section8_colour/source.docx'
d=Document(source);pp=list(d.paragraphs)
def font(run,size=10.5,bold=False):
    run.font.name='Times New Roman';run.font.size=Pt(size);run.font.bold=bold;run.font.color.rgb=RGBColor(0,0,0)
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
def replace(p,text):
    p.clear();font(p.add_run(text));return p
def unsnap(p):
    pr=p._p.get_or_add_pPr();el=pr.find(qn('w:snapToGrid'))
    if el is None:el=OxmlElement('w:snapToGrid');pr.append(el)
    el.set(qn('w:val'),'0')
for p in pp:
    unsnap(p)
    p.paragraph_format.line_spacing=1.25;p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(4)
    p.paragraph_format.widow_control=True
    for r in p.runs:font(r)
replace(pp[0],'八、已有基础');pp[0].paragraph_format.space_before=Pt(4)
font(pp[0].runs[0],12,True);pp[0].paragraph_format.keep_with_next=True
h=OxmlElement('w:p');pp[0]._p.addnext(h)
from docx.text.paragraph import Paragraph
p=Paragraph(h,pp[0]._parent);font(p.add_run('8.1 系统设计与前期论证'),10.5,True)
unsnap(p)
p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=True

for i,name in [(2,'图8-2_候选判据对照'),(5,'图8-4_观测歧义与测压漂移')]:
    p=pp[i];p.clear();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(3)
    p.paragraph_format.line_spacing=1.;p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.45))
    p._p.xpath('.//wp:docPr')[0].set('descr',name+' 合成仿真图 详见图注及可复现数据')
pp[5].paragraph_format.page_break_before=False
replace(pp[3],'图8-2 候选判据的早期检出与正常误报')
replace(pp[6],'图8-4 负载歧义与测压漂移反例')
for i in [3,6]:
    p=pp[i];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    p.paragraph_format.space_after=Pt(3);font(p.runs[0],9,True)
def note_after(p,text):
    el=OxmlElement('w:p');p._p.addnext(el);x=Paragraph(el,p._parent)
    unsnap(x)
    font(x.add_run(text),9);x.paragraph_format.line_spacing=1.15
    x.paragraph_format.space_after=Pt(6);x.paragraph_format.keep_with_next=False
    return x
note_after(pp[3],
    '注：合成回放，每组100个新种子。a、b为有效早期比例，c为3470秒正常监测的误报试次比例；误差线为Wilson 95%置信区间。横轴为对数刻度，同档符号略错位；累积组合为稳健门限与有界累积联合。有效早期须无前期误报、首次模式正确且早于15%模型流量偏离参照；该参照未经农艺验证。')
replace(pp[4],
    '原12种子对照的324条方法记录已逐条复现；冻结参数后新增100个留出种子，完成三档噪声下900条合成轨迹、2700条方法记录（图8-2）。10 kPa时，固定门限对泄漏与受限分别为14/100、16/100条有效早期，稳健门限均为99/100，累积组合均为98/100。长时正常对照中，稳健门限在0.3、3、10 kPa下分别有0/100、1/100、2/100条误报，累积组合分别为0/100、7/100、9/100。结果支持优先验证稳健门限，也表明小样本零误报不能外推为无误报。各场景复用同一组噪声种子，不合并为独立实物试验。')
note_after(pp[6],
    '注：初始K/R模型，σ=3 kPa，20个原始种子。实线为中位数，色带为逐时刻2.5%—97.5%分位范围，并非均值置信区间；a中空心点代表未知正常负载，与泄漏曲线重合。虚线分别为6%和0.6 kPa/(L/min)²门限。360秒开始变化，540秒达到终值；上游测压增加10 kPa，真实阻力不变。')
replace(pp[7],
    '负载歧义与漂移反例保留初始K/R模型，与图8-2的健康参照候选比较分别评价。在四档噪声、20个原始种子的320条反例及对照轨迹中，同一噪声实现下未知负载增加与等效泄漏的三通道观测差值严格为零；图8-4展示σ=3 kPa时的统计曲线。上游测压漂移也可使阻力残差越过0.6 kPa/(L/min)²固定门限。稳健门限可以抑制随机波动，故障原因仍需结合操作记录、健康标定、跨负载留出评价和独立核查确认。')
def after(anchor,text='',size=10.5,bold=False):
    el=OxmlElement('w:p');anchor._p.addnext(el);p=Paragraph(el,anchor._parent);unsnap(p)
    font(p.add_run(text),size,bold);p.paragraph_format.line_spacing=1.25
    p.paragraph_format.space_after=Pt(4);p.paragraph_format.widow_control=True
    return p
def add_figure(anchor,filename,caption,note):
    p=after(anchor);p.clear();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing=1;p.paragraph_format.space_before=Pt(5)
    p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(B/'figures'/f'{filename}.png'),width=Cm(14.45))
    p._p.xpath('.//wp:docPr')[0].set('descr',caption+' 合成仿真 详见图注')
    cap=after(p,caption,9,True);cap.alignment=WD_ALIGN_PARAGRAPH.CENTER;cap.paragraph_format.keep_with_next=True
    return note_after(cap,note)
add_figure(pp[1],'图8-1_水力观测响应','图8-1 渐进故障的压力与流量观测响应',
    '注：正常、泄漏和受限各100个新种子，压力噪声σ=3 kPa。a为下游压力十秒因果均值，b为十秒累计脉冲流量；曲线为中位数，色带为逐时2.5%—97.5%分位范围。故障从360秒开始，540秒达到终值。曲线来自合成水力模型，尚未标定为实物动态响应。')
amplitude_intro=after(pp[4],
    '为检查小幅故障的可检范围，另以100个新种子扫描5%—30%的终值流量偏离，完成3000条故障轨迹，并设置300条匹配健康对照（图8-3）。0.3 kPa噪声下，5%泄漏仅2/100条正确提示，10%泄漏为100/100；10 kPa下5%受限为22/100。这说明图8-2的较大故障结果不能外推为任意小故障均可检出。该批按600秒内首次模式正确且无前期误报评价，与15%参照前的有效早期指标分别统计。')
add_figure(amplitude_intro,'图8-3_幅值检出边界','图8-3 稳健门限的故障幅值检出边界',
    '注：每个幅值、每档噪声100个种子；保持健康参照与门限规则不变。幅值由600秒时相对健康流量的偏离定义，色带为Wilson 95%置信区间。正确提示要求无前期误报且故障后首次候选模式正确；本图不等同于有效早期比例。各幅值及场景复用配对噪声种子。')
for i in [9,15]:
    for r in pp[i].runs:font(r,10.5,True)
    pp[i].paragraph_format.keep_with_next=True;pp[i].paragraph_format.space_before=Pt(8)
pp[9].paragraph_format.page_break_before=False
pp[8].paragraph_format.keep_together=True
target=B/'第八部分_扩展仿真图文稿.docx';d.save(target)
# Preserve all unrelated source paragraphs verbatim, including unrerun platform claims.
for i in [1,8,9,10,11,12,13,14,15,16,17,18]:assert pp[i].text==Document(source).paragraphs[i].text
audit=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    source_text_preserved_indices=[1,8,9,10,11,12,13,14,15,16,17,18],unrelated_platform_claims_not_revalidated=True,
    figures=4,inline_figure_width_cm=14.45,body_font_pt=10.5,caption_font_pt=9)
(B/'evidence/document_edit_record.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
