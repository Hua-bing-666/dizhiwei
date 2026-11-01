"""Revise the supplied section using native, structured Word equations."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
from hashlib import sha256
import json, math, re
from docx import Document
from docx.shared import Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp/formula_review_20261027'
SOURCE=Path('C:/Users/Lenovo/Desktop/3.docx')
OUTPUT=ROOT/'deliverables/3_测量平台与软件设计_公式规范精简稿.docx'
QA=TMP/'concise_review'
QA.mkdir(parents=True,exist_ok=True)
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
source_hash=sha256(SOURCE.read_bytes()).hexdigest()

# Each variable, descriptive subscript, fraction, power, radical and accent is a
# real OMML element. No Unicode lookalike subscripts or formula screenshots.
def e(name,*children,**attrs):
    node=OxmlElement('m:'+name)
    for key,value in attrs.items(): node.set(qn('m:'+key),str(value))
    for child in children:
        if child is not None: node.append(child)
    return node
def items(value): return value if isinstance(value,(list,tuple)) else [value]
def wrap(name,value): return e(name,*[deepcopy(x) for x in items(value)])
def r(value,roman=False):
    rp=e('rPr',e('sty',val='p' if roman else 'i'))
    wp=OxmlElement('w:rPr'); fonts=OxmlElement('w:rFonts')
    for key in ('ascii','hAnsi','cs'): fonts.set(qn('w:'+key),'Times New Roman')
    fonts.set(qn('w:eastAsia'),'宋体');wp.append(fonts)
    size=OxmlElement('w:sz');size.set(qn('w:val'),'21');wp.append(size)
    t=e('t');t.text=str(value)
    if str(value).strip()!=str(value): t.set(qn('xml:space'),'preserve')
    return e('r',rp,wp,t)
def op(value): return r(value,True)
def sub(base,index): return e('sSub',wrap('e',base),wrap('sub',index))
def sup(base,index): return e('sSup',wrap('e',base),wrap('sup',index))
def frac(numerator,denominator): return e('f',e('fPr',e('type',val='bar')),wrap('num',numerator),wrap('den',denominator))
def accent(base,char): return e('acc',e('accPr',e('chr',val=char)),wrap('e',base))
def bar(base): return accent(base,'\u0305')
def hat(base): return accent(base,'\u0302')
def sqrt(base): return e('rad',e('radPr',e('degHide',val='1')),e('deg'),wrap('e',base))
def pm(point,block=True): return sub(bar(r('P')) if block else r('P'),[op(str(point))]+([op(','),r('m')] if block else []))
def qm(): return sub(r('Q'),r('m'))
def rh(index='m'): return sub(r('R'),[op('h,'),r('m') if index=='m' else op(index)])
def qhat(): return sub(hat(r('Q')),r('m'))
def z(channel='j',previous=False): return sub(r('z'),[r('j') if channel=='j' else op(channel),op(','),r('m')]+([op('−1')] if previous else []))
def ss(previous=False,initial=False):
    return sub(r('S'),[r('j'),op(','),op('0') if initial else r('m')]+([op('−1')] if previous else []))
def sc(channel): return sub(r('s'),op(channel))
def math_inline(p,content):
    om=e('oMath',*[deepcopy(x) for x in items(content)]);p._p.append(om);return om

doc=Document(SOURCE)
body=doc._element.body
for child in list(body):
    if child.tag!=qn('w:sectPr'): body.remove(child)
section=doc.sections[0]
usable=section.page_width-section.left_margin-section.right_margin
image_width=Mm(146)
for style_name in ('Normal','Heading 1','Heading 2','Heading 3','Heading 4','Caption'):
    if style_name not in doc.styles: continue
    style=doc.styles[style_name];style.font.name='Times New Roman';style.font.color.rgb=__import__('docx').shared.RGBColor(0,0,0)
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
    style.font.size=Pt(10.5)
normal=doc.styles['Normal'].paragraph_format
normal.line_spacing=1.2;normal.space_before=Pt(0);normal.space_after=Pt(3)
normal.widow_control=True
snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0')
doc.styles['Normal'].element.get_or_add_pPr().append(snap)

def font(run,bold=False):
    run.font.name='Times New Roman';run.font.size=Pt(10.5);run.font.bold=bold
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
    return run

INLINE={
 'unitq':lambda:[op('L·'),sup(op('min'),op('−1'))],
 'unitk':lambda:[op('L·'),sup(op('min'),op('−1')),op('·'),sup(op('kPa'),op('−1/2'))],
 'unitr':lambda:[op('kPa·'),sup(op('min'),op('2')),op('·'),sup(op('L'),op('−2'))],
 'unitpulse':lambda:sup(op('L'),op('−1')),
 'P0':lambda:pm(0,False),'P1':lambda:pm(1,False),
 'Pbar0':lambda:pm(0),'Pbar1':lambda:pm(1),
 'Qm':qm,'Qhat':qhat,'K':lambda:r('K'),
 'Km':lambda:sub(r('K'),r('m')),'Rh':lambda:sub(r('R'),op('h')),'Rhm':rh,'Rh0':lambda:rh('0'),
 'Tb':lambda:sub(r('T'),op('b')),'dNm':lambda:[op('Δ'),sub(r('N'),r('m'))],
 'kappa':lambda:r('κ'),'a':lambda:r('a'),'n':lambda:r('n'),
 'Pref':lambda:sub(r('P'),op('ref')),'sQ':lambda:sc('Q'),'sR':lambda:sc('R'),
 'zQm':lambda:z('Q'),'zRm':lambda:z('R'),'j':lambda:r('j'),'m':lambda:r('m'),
 'k':lambda:r('k'),'h':lambda:r('h'),'Sj0':lambda:ss(initial=True),
 'Sjm':ss,'zjm':z,
 'SQm':lambda:sub(r('S'),[op('Q,'),r('m')]),'SRm':lambda:sub(r('S'),[op('R,'),r('m')]),
 'pFA':lambda:sub(r('p'),op('FA')),'NFA':lambda:sub(r('N'),op('FA')),'NH':lambda:sub(r('N'),op('H')),
 'taud':lambda:sub(r('τ'),op('d')),'ta':lambda:sub(r('t'),op('a')),'tinj':lambda:sub(r('t'),op('inj')),
}
def prose(value,indent=True):
    if value.startswith('式中，'): value='式中：'+value[3:]
    for old,new in (('L·min⁻¹·kPa⁻¹ᐟ²','{{unitk}}'),('kPa·min²·L⁻²','{{unitr}}'),('L·min⁻¹','{{unitq}}'),('L⁻¹','{{unitpulse}}')): value=value.replace(old,new)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent=Pt(21) if indent else Pt(0)
    for part in re.split(r'(\{\{[A-Za-z0-9]+\}\})',value):
        if part.startswith('{{'): math_inline(p,INLINE[part[2:-2]]())
        elif part: font(p.add_run(part))
    return p
def heading(value,level=False):
    p=doc.add_paragraph();p.paragraph_format.first_line_indent=Pt(0)
    p.paragraph_format.space_before=Pt(6 if level else 4);p.paragraph_format.space_after=Pt(3)
    p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
    font(p.add_run(value),True)
    return p
def equation(content,number):
    # Separate the number from the display-math paragraph: ordinary text in the
    # same paragraph forces Word to shrink fractions to inline style.
    table=doc.add_table(rows=1,cols=3);table.autofit=False;table.alignment=WD_TABLE_ALIGNMENT.CENTER
    widths=[Mm(17),int(usable-Mm(34)),Mm(17)]
    pr=table._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        line=OxmlElement('w:'+side);line.set(qn('w:val'),'nil');borders.append(line)
    pr.append(borders)
    margins=OxmlElement('w:tblCellMar')
    for side in ('top','left','bottom','right'):
        margin=OxmlElement('w:'+side);margin.set(qn('w:w'),'0');margin.set(qn('w:type'),'dxa');margins.append(margin)
    pr.append(margins)
    row=table.rows[0];row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    for column,cell,width in zip(table.columns,row.cells,widths):
        column.width=width;cell.width=width;cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p=cell.paragraphs[0];pf=p.paragraph_format
        pf.first_line_indent=Pt(0);pf.space_before=Pt(3);pf.space_after=Pt(3);pf.line_spacing=1
        pf.keep_together=True;pf.keep_with_next=True
    p=row.cells[1].paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p._p.append(e('oMathPara',e('oMathParaPr',e('jc',val='center')),e('oMath',*[deepcopy(x) for x in items(content)],op('，'))))
    p=row.cells[2].paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    font(p.add_run('（3-'+str(number)+'）'))
    return table
def figure(file,caption):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1
    p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
    p.add_run().add_picture(str(file),width=image_width)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_after=Pt(3)
    font(p.add_run(caption));p.paragraph_format.keep_together=True

heading('3.3.3 测量平台与水力表征',True)
prose('面向南疆棉田轮灌中的支管巡检需求，项目利用清水台架研究受限、泄漏与供压变化的压力流量响应，通过故障注入和正常扰动对照，为节点判断及现场复测提供依据。')
heading('（1）双支路台架与测点布置')
prose('台架采用共用水源的 A、B 双支路。A 支路为被测支路，水流依次经过上游取压口 {{P0}}、可调受限元件、下游取压口 {{P1}} 与流量计，随后分为正常出流和泄漏旁路；B 支路通过负载切换模拟邻支路启闭。两取压口布置在同一高度，监测区段内不设置分流点，流量计位于泄漏分流点之前，使测得的总流量与区段压降对应。')
prose('台架采用 PVC-U 管路，框架尺寸为 900 mm × 520 mm，水路与采集电路之间设置防溅隔离。泄漏水由独立容器收集，收集量、持续时间和阀门操作记录用于结果核对。三维布局与测点布置分别见图3-8、图3-9。')
figure(TMP/'image1.png','图3-8 双支路验证台架三维布局')
figure(TMP/'image2.png','图3-9 双支路清水台架水路与测点布置')
heading('（2）流量换算与水力特征')
prose('固定采集基线每 1 s 读取压力并汇总脉冲计数，按连续 10 s 构成一个不重叠数据块。以 {{m}} 表示数据块序号，{{Qm}} 表示块内平均流量；两路压力取同一时间段的均值，分别记为 {{Pbar0}} 和 {{Pbar1}}。流量由实际计数区间换算：')
equation([qm(),op('='),frac([op('60Δ'),sub(r('N'),r('m'))],[r('κ'),sub(r('T'),op('b'))])],1)
prose('式中，{{dNm}} 为第 {{m}} 块的新增脉冲数；{{kappa}} 为脉冲系数，SEN0549 标称为 540 L⁻¹；{{Tb}} 为计数时长，单位为 s；{{Qm}} 的单位为 L·min⁻¹；60 为秒至分钟的换算系数。脉冲系数通过独立计量复核。')
prose('当测点间的压损以局部节流为主时，压降与通过该区段的流量平方近似成正比。采用区段等效阻力消除流量变化对压降的直接影响，使同一受限元件在不同供压下便于比较：')
equation([rh(),op('='),frac([pm(0),op('−'),pm(1)],sup(qm(),op('2')))],2)
prose('式中，{{Rhm}} 为区段等效阻力，单位为 kPa·min²·L⁻²；两路压力均使用 kPa。该特征用于局部节流主导的台架短区段，受限时通常增大。下游出流变化由压力参照残差表征，流量计及管件损失通过健康数据校正。比值计算采用满足压力、流量和量程条件的有效数据块。')

heading('3.3.4 软件模块设计',True)
prose('节点计算压力流量特征并形成异常候选，接收服务完成数据校验与持久化，巡检平台记录查看、处置和复测过程。事件通过支管编号、测点区段与原始测量记录关联。')
heading('（1）健康参照与块级异常判断')
prose('节点用独立健康数据建立压力与流量的参照关系，补偿正常供压变化。健康预测流量为：')
equation([qhat(),op('='),r('a'),sup([op('('),frac(pm(1),sub(r('P'),op('ref'))),op(')')],r('n'))],3)
prose('式中，{{Qhat}} 为健康预测流量，单位为 L·min⁻¹；{{Pref}} 为参考压力，取 100 kPa；{{a}} 为该参考压力下的流量系数，单位与流量相同；{{n}} 为无量纲压力指数。孔口型台架取 {{n}} = 0.5，{{a}} 由健康数据标定，并通过多压力工况检验。')
prose('流量通道检测超出健康预测的出流变化，阻力通道检测区段阻力的增量，两路残差分别标准化：')
equation([z('Q'),op('='),frac([qm(),op('−'),qhat()],[sc('Q'),qhat()]),op('，　'),z('R'),op('='),frac([rh(),op('−'),rh('0')],sc('R'))],4)
prose('式中，{{Rh0}} 为健康区段阻力的中位数；{{sQ}} 为无量纲的相对流量残差尺度；{{sR}} 为阻力残差尺度，单位与 {{Rh}} 相同；{{zQm}}、{{zRm}} 均为无量纲残差。两种尺度由独立健康数据计算并设置正下限。')
prose('为识别持续的小幅偏离，两个通道采用单侧累积和（CUSUM）判据，每个完整有效数据块更新一次：')
equation([ss(),op('='),op('max'),op('{0, '),ss(previous=True),op('+'),z(),op('−'),r('k'),op('}，　'),r('j'),op('∈{Q,R}')],5)
prose('式中，{{Sjm}} 为第 {{m}} 块的累积统计量；{{zjm}} 为对应通道的标准化残差；{{j}} 为通道标记，Q、R 分别表示流量与阻力通道；{{k}} 为无量纲参考漂移量。初值 {{Sj0}} = 0，累积值超过无量纲门限 {{h}} 时形成异常候选。仿真取 {{k}} = 0.5、{{h}} = 26，台架阶段按误报目标标定。')
prose('判据按 10 s 不重叠数据块更新，程序同步检查量程、时间对齐和数据完整性。供压或邻支路切换时挂起判断，工况稳定且取得完整有效块后复判；无效块记录为不可用状态。处理流程见图3-10。')
figure(TMP/'算法流程_正文配套.png','图3-10 块级异常判断与工况复判流程')
prose('流量、阻力通道分别形成附加出流和区段受限候选，双通道越限按复合异常处理。结合阀门操作及同工况复测核查候选原因。')
heading('（2）事件触发采集策略')
prose('常规阶段降低压力读取频率，检测到压力或流量持续变化后切换为 1 s 连续采集，形成完整的 10 s 数据块后启动复核。流量脉冲保持连续计数，稀疏阶段保留实际时间戳与可用状态。监测间隔、触发门限和保持时长通过与固定 1 s 采集对照确定，评价采集次数、漏检和识别时延。')
heading('（3）接收服务与巡检平台')
prose('接收服务完成 COBS 分帧解码和帧校验，按设备、会话与序号识别事件。新事件提交数据库后回复接收确认（ACK）；相同事件的重传复用原记录并再次确认，内容冲突则记录拒绝原因。节点确认超时后重发原事件。接收与重传关系见图3-11。')
figure(TMP/'image4.png','图3-11 事件接收确认与重传去重')
prose('巡检平台按总览、支管监测、异常事件、设备与链路、历史记录、实验记录、试验台架和系统设置八个页面分工。原始事件与人工核查、处置和复测记录关联保存，断连或数据过期时显示不可用状态。控制演示记录请求、软件接收、模拟输出和人工复位四类状态。')
heading('（4）试验与评价')
prose('试验设置供压变化、B 支路切换、A 支路受限和泄漏旁路等工况，健康标定、门限选择和独立验证采用不同批次数据。根据独立操作记录计算健康试次误报率及已检出异常的识别时延：')
equation([sub(r('p'),op('FA')),op('='),frac(sub(r('N'),op('FA')),sub(r('N'),op('H'))),op('，　'),sub(r('τ'),op('d')),op('='),sub(r('t'),op('a')),op('−'),sub(r('t'),op('inj'))],6)
prose('式中，{{pFA}} 为健康试次误报率；{{NH}} 为健康验证试次数且大于零；{{NFA}} 为出现过异常候选的健康试次数；{{taud}} 为识别时延，单位为 s；{{ta}} 为异常注入后首次对应候选的形成时刻；{{tinj}} 为异常注入时刻。各策略采用相同观察时长与工况集合，漏检、判断不可用和识别时延分别统计。通信侧记录唯一落库比例、确认往返时延及重传次数。')

# Clear theme/default paragraph borders without adding a new visual template.
for p in doc.paragraphs:
    pp=p._p.pPr
    if pp is not None:
        for border in list(pp.findall(qn('w:pBdr'))): pp.remove(border)
settings=doc.settings.element
mathpr=settings.find(qn('m:mathPr'))
if mathpr is None: mathpr=e('mathPr');settings.append(mathpr)
mathfont=mathpr.find(qn('m:mathFont'))
if mathfont is None: mathpr.append(e('mathFont',val='Cambria Math'))
else: mathfont.set(qn('m:val'),'Cambria Math')
doc.save(OUTPUT)

# Mathematical checks cover units/conversion, healthy invariance, diagnostic
# directions and a known ambiguity; these are calculations, not physical data.
checks=[]
assert math.isclose(60*270/(540*10),3.0);checks.append('270 pulses / 10 s at 540 per L gives 3 L/min')
for p1 in (40.,80.,120.):
    q=.28*math.sqrt(p1);p0=p1+.8*q*q
    assert math.isclose(q/math.sqrt(p1),.28)
    assert math.isclose((p0-p1)/q**2,.8)
    assert math.isclose(2.8*(p1/100.)**.5,q)
checks.append('healthy K and Rh invariant across three model pressures; normalized reference matches')
p1=100.; q_leak=.37*math.sqrt(p1); p0_leak=p1+.8*q_leak*q_leak
assert q_leak/(2.8*(p1/100.)**.5)-1>0
assert math.isclose((p0_leak-p1)/q_leak**2-.8,0,abs_tol=1e-12)
checks.append('additional outflow increases flow residual while segment resistance stays fixed')
q=.28*math.sqrt(p1);p0=p1+8*q*q
assert math.isclose(q/2.8-1,0,abs_tol=1e-12) and (p0-p1)/q**2-.8>0
checks.append('segment restriction increases resistance residual at fixed downstream pressure')
normal_load_only=.37*math.sqrt(p1)
normal_load_p0=p1+.8*normal_load_only**2
assert all(math.isclose(v,w) for v,w in zip((p0_leak,p1,q_leak),(normal_load_p0,p1,normal_load_only)))
checks.append('same downstream aggregate load yields the same observable triple; no unique leakage claim')
s=0.;cross=None
for m in range(1,54):
    s=max(0.,s+1.-.5)
    if s>26 and cross is None: cross=m
assert cross==53;checks.append('strict S > 26 crossing occurs at block 53 for z=1, k=0.5')
assert max(0.,0.-1.-.5)==0;checks.append('negative increments do not create a positive CUSUM score')

with ZipFile(OUTPUT) as z:
    from lxml import etree
    xml=etree.fromstring(z.read('word/document.xml'))
    text=''.join(xml.xpath('//w:t/text()|//m:t/text()',namespaces=NS))
    assert '【' not in text and '待确认' not in text and 'Cn' not in text
    assert len(xml.xpath('//m:f',namespaces=NS))==6
    assert len(xml.xpath('//m:sSub',namespaces=NS))>30
    assert len(xml.xpath('//m:rad',namespaces=NS))==0
    equation_numbers=re.findall(r'（3-\d+）',text)
    assert equation_numbers==[f'（3-{n}）' for n in range(1,7)]
    counts={name:len(xml.xpath('//m:'+name,namespaces=NS)) for name in ('oMath','f','sSub','sSup','rad','acc')}
assert sha256(SOURCE.read_bytes()).hexdigest()==source_hash
receipt={'source':str(SOURCE),'source_sha256':source_hash,'output':str(OUTPUT),'display_equation_groups':6,'native_math_elements':counts,'mathematical_checks':checks,'evidence_type':'analytical checks and existing code correspondence; no physical experiment claimed','render_review':'pending','source_unchanged':True,'image_count':len(doc.inline_shapes),'available_width_mm':usable/36000,'image_width_mm':146}
(QA/'revision_checks.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
