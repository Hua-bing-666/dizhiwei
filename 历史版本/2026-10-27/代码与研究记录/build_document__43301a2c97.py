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
for p in pp:
    p.paragraph_format.line_spacing=1.25;p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(4)
    p.paragraph_format.widow_control=True
    for r in p.runs:font(r)
replace(pp[0],'八、已有基础');pp[0].paragraph_format.space_before=Pt(4)
font(pp[0].runs[0],12,True);pp[0].paragraph_format.keep_with_next=True
h=OxmlElement('w:p');pp[0]._p.addnext(h)
from docx.text.paragraph import Paragraph
p=Paragraph(h,pp[0]._parent);font(p.add_run('8.1 系统设计与前期论证'),10.5,True)
p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=True

for i,name in [(2,'图8-1_候选判据扩展验证'),(5,'图8-2_负载歧义与漂移反例')]:
    p=pp[i];p.clear();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(3)
    p.paragraph_format.line_spacing=1.;p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.45))
    p._p.xpath('.//wp:docPr')[0].set('descr',name+' 合成仿真图 详见图注及可复现数据')
pp[5].paragraph_format.page_break_before=True
replace(pp[3],'图8-1 冻结参数下三种候选判据的扩展仿真对照')
replace(pp[6],'图8-2 初始 K/R 判据的负载歧义与压力漂移反例')
for i in [3,6]:
    p=pp[i];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    p.paragraph_format.space_after=Pt(3);font(p.runs[0],9,True)
def note_after(p,text):
    el=OxmlElement('w:p');p._p.addnext(el);x=Paragraph(el,p._parent)
    font(x.add_run(text),9);x.paragraph_format.line_spacing=1.15
    x.paragraph_format.space_after=Pt(6);x.paragraph_format.keep_with_next=False
    return x
note_after(pp[3],
    '注：每个场景、每档噪声使用100个新测试种子；三方法共享观测，参数未重新调优。a、b为有效早期比例及Wilson 95%置信区间；c为3470秒正常监测中发生确认误报的试次；d为10 kPa下有效早期试次的提前量中位数及四分位距。有效早期要求无前期误报、首次故障后模式正确且早于15%模型流量偏离参照；该参照未经农艺验证。')
replace(pp[4],
    '原12种子对照的324条方法记录已逐条复现；冻结参数后新增100个留出种子，完成三档噪声下900条合成轨迹、2700条方法记录（图8-1）。10 kPa时，固定门限对泄漏与受限分别为14/100、16/100条有效早期，稳健门限均为99/100，累积组合均为98/100。长时正常对照中，稳健门限在0.3、3、10 kPa下分别有0/100、1/100、2/100条误报，累积组合分别为0/100、7/100、9/100。结果支持优先验证稳健门限，也表明小样本零误报不能外推为无误报。各场景复用同一组噪声种子，不合并为独立实物试验。')
note_after(pp[6],
    '注：两面板均重跑初始K/R模型，压力噪声σ=3 kPa，20个原始种子。实线为种子中位数，色带为逐时刻2.5%—97.5%分位范围，并非均值置信区间；空心点标出未知正常负载轨迹。360秒开始引入变化，至540秒达到终值；漂移为上游测压增加10 kPa，真实水路阻力保持不变。')
replace(pp[7],
    '负载歧义与漂移反例保留初始K/R模型，与图8-1的健康参照候选比较分别评价。在四档噪声、20个原始种子的320条反例及对照轨迹中，同一噪声实现下未知负载增加与等效泄漏的三通道观测差值严格为零；图8-2展示σ=3 kPa时的统计曲线。上游测压漂移也可使阻力残差越过0.6 kPa/(L/min)²固定门限。稳健门限可以抑制随机波动，故障原因仍需结合操作记录、健康标定、跨负载留出评价和独立核查确认。')
for i in [9,15]:
    for r in pp[i].runs:font(r,10.5,True)
    pp[i].paragraph_format.keep_with_next=True;pp[i].paragraph_format.space_before=Pt(8)
pp[9].paragraph_format.page_break_before=True
target=B/'第八部分_彩印仿真修订稿.docx';d.save(target)
# Preserve all unrelated source paragraphs verbatim, including unrerun platform claims.
for i in [1,8,9,10,11,12,13,14,15,16,17,18]:assert pp[i].text==Document(source).paragraphs[i].text
audit=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    source_text_preserved_indices=[1,8,9,10,11,12,13,14,15,16,17,18],unrelated_platform_claims_not_revalidated=True,
    figures=2,inline_figure_width_cm=14.45,body_font_pt=10.5,caption_font_pt=9)
(B/'evidence/document_edit_record.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
