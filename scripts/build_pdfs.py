"""Typeset scope plan; export the delivered PPTX through native WPS/Office.

deck_pdf() is an optional SVG authoring preview, not the delivered PPTX review.
"""
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
 'body':ParagraphStyle('body',fontName='CJK',fontSize=10.5,leading=17.5,textColor=ink,spaceAfter=8,wordWrap='CJK',allowWidows=0,allowOrphans=0),
 'h1':ParagraphStyle('h1',fontName='CJK',fontSize=18,leading=27,textColor=colors.black,spaceAfter=16,wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='CJK',fontSize=14,leading=21,textColor=colors.black,spaceBefore=16,spaceAfter=9,keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='CJK',fontSize=11.5,leading=19,textColor=colors.black,spaceBefore=10,spaceAfter=6,keepWithNext=True,wordWrap='CJK'),
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
    canvas.setFont('CJK',9);canvas.setFillColor(muted);canvas.drawString(42,815,'南疆滴灌支管诊断系统 · 项目范围与执行 / 2026.10.04')
    canvas.drawString(42,25,'模型为前期基础；实物与性能为拟开展工作。申报正文见另附学校模板填写稿。')
    canvas.drawRightString(553,25,str(doc.page));canvas.restoreState()

def proposal():
    path=OUT/'项目书审阅版.pdf'
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=42,leftMargin=42,topMargin=55,bottomMargin=47,title='南疆滴灌支管诊断系统项目范围与执行方案',author='项目团队（待正式填写）')
    lines=(ROOT/'docs/项目范围与三阶段执行方案.md').read_text(encoding='utf-8').splitlines();story=[];i=0
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
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eef3ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,g),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#c7d2cb')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([table,Spacer(1,10)]);continue
        kind='body';value=l
        if l.startswith('# '):kind='h1';value=l[2:]
        elif l.startswith('## '):kind='h2';value=l[3:]
        elif l.startswith('### '):kind='h3';value=l[4:]
        elif l.startswith('#### '):kind='h3';value=l[5:]
        elif l.startswith('- '):value='• '+l[2:]
        para=Paragraph(markup(value).replace('\n','<br/>'),styles[kind])
        story.append(para);i+=1
        figures=[('申报名称采用','system_scope.png','系统设计：感知、有限诊断、可靠告警与管理确认；尚无在线实物。'),('必做配置为','dual_pressure_layout.png','布点与台架设计：P0/P1/Q包围目标区段；量程与差压误差仍须参考标定。'),('第2周完成','early_diagnosis.png','未标定合成模型480试次；15%仅为演示失效参照。非实物识别率。')]
        for trigger,name,caption in figures:
            if l.startswith(trigger):
                img=Image(str(ROOT/'application/figures'/name));img.drawHeight=511*img.imageHeight/img.imageWidth;img.drawWidth=511
                story.append(KeepTogether([img,Paragraph(caption,styles['caption'])]))
    story.append(Paragraph('附件：前期通信取舍图',styles['h2']))
    img=Image(str(ROOT/'application/figures/communication_tradeoff.png'));img.drawWidth=511;img.drawHeight=511*1044/2160
    story.append(img);story.append(Paragraph('图为未标定的合成回放；四策略同检测、同滤波载荷、同告警确认。每点为20个种子均值，发送帧包含确认和尾段清队列；误差相对本地模拟滤波量。',styles['caption']))
    story.append(Paragraph('复现与材料索引',styles['h2']))
    story.append(Paragraph('本地打开deliverables/index.html查看双点诊断、管理交互设计、历史模型反例、通信对照和PPT。学校申报正文见大创申报书_模板填写稿.docx；程序与JSON/CSV保存在simulation，案例与执行文件在docs。网站不连接真实传感器。',styles['body']))
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
    proposal()
    latest=max((P/'exports').glob('*.pptx'),key=lambda p:p.stat().st_mtime)
    shutil.copy2(latest,DEL/'立项答辩.pptx')
    print('Copied editable PPTX:',latest.name)
    shell=shutil.which('pwsh') or shutil.which('powershell')
    if not shell:raise RuntimeError('PowerShell required for native PPTX review export.')
    subprocess.run([shell,'-NoProfile','-File',str(ROOT/'scripts/export_ppt_review.ps1'),
                    '-InputPptx',str(DEL/'立项答辩.pptx'),
                    '-OutputPdf',str(DEL/'立项答辩审阅版.pdf')],check=True,timeout=90)
