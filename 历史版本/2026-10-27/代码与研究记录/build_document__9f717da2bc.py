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
    p.paragraph_format.keep_together=True
    for r in p.runs:font(r)
replace(pp[0],'八、已有基础');pp[0].paragraph_format.space_before=Pt(4)
font(pp[0].runs[0],12,True);pp[0].paragraph_format.keep_with_next=True
h=OxmlElement('w:p');pp[0]._p.addnext(h)
from docx.text.paragraph import Paragraph
p=Paragraph(h,pp[0]._parent);font(p.add_run('8.1 系统设计与前期论证'),10.5,True)
unsnap(p)
p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=True

for i,name in [(2,'图8-2_高噪声试次结局'),(5,'图8-4_终值特征与观测歧义')]:
    p=pp[i];p.clear();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(3)
    p.paragraph_format.line_spacing=1.;p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(B/'figures'/f'{name}.png'),width=Cm(14.45))
    p._p.xpath('.//wp:docPr')[0].set('descr',name+' 合成仿真图 详见图注及可复现数据')
pp[5].paragraph_format.page_break_before=False
replace(pp[3],'图8-2 高噪声下候选判据的试次结局')
replace(pp[6],'图8-4 终值特征分布与故障原因歧义')
for i in [3,6]:
    p=pp[i];p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    p.paragraph_format.space_after=Pt(3);font(p.runs[0],9,True)
def note_after(p,text):
    el=OxmlElement('w:p');p._p.addnext(el);x=Paragraph(el,p._parent)
    unsnap(x)
    font(x.add_run(text),9);x.paragraph_format.line_spacing=1.15
    x.paragraph_format.space_after=Pt(6);x.paragraph_format.keep_with_next=False
    x.paragraph_format.keep_together=True
    return x
note_after(pp[3],
    '注：σ=10 kPa，每组100种子。a、b为故障试次结局，c为3470秒正常监测误报比例。有效早期须无前期误报、首次模式正确且早于15%模型参照；该参照非农艺标准。完整分组及Wilson 95%区间随数据附。')
replace(pp[4],
    '原12种子对照的324条方法记录已逐条复现；冻结参数后新增100个留出种子，完成三档噪声下900条合成轨迹、2700条方法记录（图8-2）。10 kPa时，固定门限对泄漏与受限分别为14/100、16/100条有效早期，稳健门限均为99/100，累积组合均为98/100。长时正常对照中，稳健门限在0.3、3、10 kPa下分别有0/100、1/100、2/100条误报，累积组合分别为0/100、7/100、9/100。结果支持优先验证稳健门限，也表明小样本零误报不能外推为无误报。各场景复用同一组噪声种子，不合并为独立实物试验。')
note_after(pp[6],
    '注：初始K/R模型，σ=3 kPa，每种场景20个原始种子，绘制600秒终值。灰点为正常，蓝点为泄漏，青色空心环为未知正常负载，紫三角为上游测压漂移；泄漏与负载逐种子重合。虚线为6%和0.6 kPa/(L/min)²初始门限。漂移终值为10 kPa，真实水路阻力未变。')
replace(pp[7],
    '负载歧义与漂移反例保留初始K/R模型，与图8-2的健康参照候选比较分别评价。四档噪声、20个原始种子的320条反例及对照轨迹显示，同一噪声实现下未知负载增加与等效泄漏的三通道观测差值严格为零。图8-4将σ=3 kPa的终值投影到特征平面：泄漏与负载重合，测压漂移则可能落入受限候选。稳健门限能抑制随机波动，故障原因仍需操作记录、健康标定、跨负载留出评价和独立核查。')
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
add_figure(pp[1],'图8-1_压力流量响应轨迹','图8-1 渐进故障的压力流量响应轨迹',
    '注：σ=3 kPa，泄漏与受限各100个新种子。横轴为十秒计数流量，纵轴为十秒因果压力均值；细线为成对观测轨迹，粗线为逐时中位轨迹。黑菱形为360秒健康状态中位点，圆点为600秒终值，箭头指示时间方向。故障从360秒开始，540秒参数达到终值；准稳态模型尚未标定为实物动态响应。')
amplitude_intro=after(pp[4],
    '为检查小幅故障的可检范围，另以100个新种子扫描5%—30%的终值流量偏离，完成3000条故障轨迹，并设置300条匹配健康对照（图8-3）。0.3 kPa噪声下，5%泄漏仅2/100条正确提示，10%泄漏为100/100；10 kPa下5%受限为22/100。这说明图8-2的较大故障结果不能外推为任意小故障均可检出。该批按600秒内首次模式正确且无前期误报评价，与15%参照前的有效早期指标分别统计。')
add_figure(amplitude_intro,'图8-3_离散检出边界','图8-3 稳健门限的离散检出边界',
    '注：每格100个种子，色条为正确提示比例；仅标非100%的格子，未标数值的深蓝格均为100%。行、列为实际测试的噪声和幅值档位，不作连续插值。幅值为600秒时相对健康流量的偏离。正确提示要求无前期误报且故障后首次候选模式正确，不等同于有效早期。完整分组及Wilson 95%区间随数据附。')
for i in [9,15]:
    for r in pp[i].runs:font(r,10.5,True)
    pp[i].paragraph_format.keep_with_next=True;pp[i].paragraph_format.space_before=Pt(8)
pp[9].paragraph_format.page_break_before=True
pp[8].paragraph_format.keep_together=True
target=B/'第八部分_期刊主图重构稿.docx';d.save(target)
# Preserve all unrelated source paragraphs verbatim, including unrerun platform claims.
for i in [1,8,9,10,11,12,13,14,15,16,17,18]:assert pp[i].text==Document(source).paragraphs[i].text
audit=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    source_text_preserved_indices=[1,8,9,10,11,12,13,14,15,16,17,18],unrelated_platform_claims_not_revalidated=True,
    figures=4,inline_figure_width_cm=14.45,body_font_pt=10.5,caption_font_pt=9)
(B/'evidence/document_edit_record.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
