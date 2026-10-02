"""Typeset proposal and browser-render the slide SVGs as a readable PDF."""
from pathlib import Path
from html import escape
import re, shutil, subprocess, json
import pymupdf
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
DEL=ROOT/'deliverables';TMP=ROOT/'tmp/qa';TMP.mkdir(parents=True,exist_ok=True)
P=ROOT/'projects/drip-research_ppt169_20261002'
pdfmetrics.registerFont(TTFont('CJK',r'C:\Windows\Fonts\simhei.ttf'))
pdfmetrics.registerFontFamily('CJK',normal='CJK',bold='CJK',italic='CJK',boldItalic='CJK')
g=colors.HexColor('#164c45');ink=colors.HexColor('#20332f');muted=colors.HexColor('#556762')
styles={
 'body':ParagraphStyle('body',fontName='CJK',fontSize=10.5,leading=17.5,textColor=ink,spaceAfter=8,wordWrap='CJK'),
 'h1':ParagraphStyle('h1',fontName='CJK',fontSize=20,leading=29,textColor=g,spaceAfter=16,wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='CJK',fontSize=14,leading=21,textColor=g,spaceBefore=16,spaceAfter=9,keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='CJK',fontSize=11.5,leading=19,textColor=g,spaceBefore=10,spaceAfter=6,keepWithNext=True,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='CJK',fontSize=9,leading=14,textColor=ink,wordWrap='CJK'),
 'caption':ParagraphStyle('caption',fontName='CJK',fontSize=9,leading=14,textColor=muted,spaceAfter=12,wordWrap='CJK')}

def markup(value):
    value=re.sub(r'`([^`]+)`',r'\1',value)
    # Local links remain readable labels in PDF; DOI/HTTP references remain clickable.
    value=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:m[1],value)
    value=escape(value)
    value=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',value)
    value=re.sub(r'(https?://[^\s<]+)',r'<link href="\1" color="#164c45">\1</link>',value)
    return value

def page_frame(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(g);canvas.setLineWidth(.7);canvas.line(42,801,553,801)
    canvas.setFont('CJK',9);canvas.setFillColor(muted);canvas.drawString(42,815,'创新训练申报正文 · 审阅版 / 2026.10.02')
    canvas.drawString(42,25,'模型分析为前期基础；实物与性能验证为拟开展工作。正式模板与行政字段另补。')
    canvas.drawRightString(553,25,str(doc.page));canvas.restoreState()

def proposal():
    path=OUT/'项目书审阅版.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=42,leftMargin=42,topMargin=55,bottomMargin=47,title='滴灌支管异常监测与可靠事件通信：创新训练申报正文',author='项目团队（待正式填写）')
    lines=(ROOT/'application/项目书正文草案.md').read_text(encoding='utf-8').splitlines();story=[];i=0
    review=pymupdf.open(OUT/'立项答辩审阅版.pdf')
    model_fig=TMP/'proposal-model.png';response_fig=TMP/'proposal-response.png'
    for page_idx,region,dest in [(4,(48,175,1232,590),model_fig),(5,(48,165,1232,550),response_fig)]:
        clip=pymupdf.Rect(*(value*.75 for value in region))
        review[page_idx].get_pixmap(matrix=pymupdf.Matrix(2,2),clip=clip).save(dest)
    review.close()
    while i<len(lines):
        l=lines[i].strip()
        if not l:i+=1;continue
        if l.startswith('|'):
            block=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',v or ' ') for v in row):block.append(row)
                i+=1
            n=len(block[0]);width=511.28/n
            data=[[Paragraph(markup(c),styles['cell']) for c in row] for row in block]
            table=Table(data,colWidths=[width]*n,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eef3ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,g),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#c7d2cb')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            story.extend([table,Spacer(1,10)]);continue
        kind='body';value=l
        if l.startswith('# '):kind='h1';value='创新训练项目申报书正文\n模型证据与实施路线版'
        elif l.startswith('## '):kind='h2';value=l[3:]
        elif l.startswith('### '):kind='h3';value=l[4:]
        elif l.startswith('#### '):kind='h3';value=l[5:]
        elif l.startswith('- '):value='• '+l[2:]
        para=Paragraph(markup(value).replace('\n','<br/>'),styles[kind])
        story.append(KeepTogether([para]) if re.match(r'^\[\d+\]',l) else para);i+=1
        if l.startswith('技术路线：'):
            img=Image(str(model_fig));img.drawWidth=511;img.drawHeight=511*415/1184
            story.extend([img,Paragraph('图1　双支路等效水路与测点。未标定模型示意，压力测点位于A支路额外节流之后；不是设备照片或已搭建台架。',styles['caption'])])
        if l.startswith('**新完成的对抗检验：'):
            img=Image(str(response_fig));img.drawWidth=511;img.drawHeight=511*385/1184
            story.extend([img,Paragraph('图2　同参数下正常切换与切换期间等效泄漏的模拟压力。来源scenarios.json，种子20261002，绘图5秒抽取；未标定、非实测。用于工况设计，不支持田间准确率结论。',styles['caption'])])
    story.append(PageBreak());story.append(Paragraph('附件：前期通信取舍图',styles['h2']))
    img=Image(str(ROOT/'application/figures/communication_tradeoff.png'));img.drawWidth=511;img.drawHeight=511*1044/2160
    story.append(img);story.append(Paragraph('图为未标定的合成回放；四策略同检测、同滤波载荷、同告警确认。每点为20个种子均值，发送帧包含确认和尾段清队列；误差相对本地模拟滤波量。',styles['caption']))
    story.append(Paragraph('复现与材料索引',styles['h2']))
    story.append(Paragraph('本地打开 deliverables/index.html 查看参数化水路、反例、通信对照和PPT。程序与JSON/CSV保存在simulation目录；三阶段路线和立项任务体系分别保存在docs和application目录。网站不连接真实传感器。',styles['body']))
    doc.build(story,onFirstPage=page_frame,onLaterPages=page_frame)
    shutil.copy2(path,DEL/path.name);print('Proposal PDF:',path)

def deck_pdf():
    slides=[]
    for s in sorted((P/'svg_output').glob('*.svg')):
        slides.append('<div class="slide">'+s.read_text(encoding='utf-8')+'</div>')
    html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>@page{size:1280px 720px;margin:0}html,body{margin:0;padding:0;width:1280px}*{box-sizing:border-box;print-color-adjust:exact;-webkit-print-color-adjust:exact}.slide{width:1280px;height:720px;break-after:page}.slide:last-child{break-after:auto}svg{display:block;width:1280px;height:720px}</style><body>'+''.join(slides)+'</body></html>'
    page=TMP/'deck-print.html';page.write_text(html,encoding='utf-8',newline='\n')
    edge=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe';target=OUT/'立项答辩审阅版.pdf'
    args=[edge,'--headless=new','--disable-gpu','--no-first-run','--no-pdf-header-footer','--user-data-dir='+str(TMP/'edge-pdf-profile'),'--print-to-pdf='+str(target),'--virtual-time-budget=3000',page.as_uri()]
    result=subprocess.run(args,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
    if result.returncode!=0 or not target.exists():raise RuntimeError(result.stderr.decode('utf-8',errors='replace')[-1000:])
    shutil.copy2(target,DEL/target.name);print('Deck review PDF:',target)

if __name__=='__main__':
    deck_pdf();proposal()
    latest=max((P/'exports').glob('*.pptx'),key=lambda p:p.stat().st_mtime)
    shutil.copy2(latest,DEL/'立项答辩.pptx')
    print('Copied editable PPTX:',latest.name)
