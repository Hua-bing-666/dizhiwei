"""Preserve the accepted template; refine prose, captions, figures and superscript citations."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
from PIL import Image
import hashlib, json, re
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'deliverables/大创申报书_系统方案完善稿.docx'
OUT=ROOT/'deliverables/大创申报书_版式修订稿.docx'
DATA=ROOT/'application/print_polish';DATA.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp/print_polish_document';TMP.mkdir(parents=True,exist_ok=True)
original=SRC.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}';V='{'+NS['v']+'}';R='{'+NS['r']+'}'
tx=lambda x:''.join(x.xpath('.//w:t/text()',namespaces=NS))
with ZipFile(SRC) as z:parts={n:z.read(n) for n in z.namelist()}
root=E.fromstring(parts['word/document.xml']);rels=E.fromstring(parts['word/_rels/document.xml.rels'])
relmap={x.get('Id'):'word/'+x.get('Target') for x in rels}
rows=root.find(W+'body/'+W+'tbl').findall(W+'tr')
protected={i:E.tostring(rows[i]) for i in list(range(16))+list(range(25,31))}
math_before=[E.tostring(x) for x in root.xpath('.//m:oMath',namespaces=NS)]
refs_before=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[\d\]',tx(p))]
captions={1:'系统总体结构',2:'双支路台架水路与测点布置',3:'验证台架三维布局设计',4:'压力与流量采集接口',
 5:'事件触发采集与模拟控制流程',6:'支管异常诊断流程',7:'事件接收确认与重传时序',
 8:'支管诊断界面（合成数据回放）',9:'不同压力噪声条件下的有效早期识别结果（仿真）',10:'负载变化与压力漂移的诊断影响（仿真）'}
names={1:'system_responsibilities',2:'water_layout',3:'collection_overview',4:'measurement_interfaces',5:'event_sampling_strategy',6:'diagnosis_proposal',7:'durable_event_sequence',8:'website_diagnosis_panel',9:'noise_outcomes_print',10:'failure_counterexamples'}
figure_records=[]
for p in root.xpath('.//w:p',namespaces=NS):
 match=re.match(r'^图(\d+)\s',tx(p))
 if not match:continue
 n=int(match[1]);texts=p.xpath('.//w:t',namespaces=NS)
 texts[0].text=f'图{n} '+captions[n]
 for extra in texts[1:]:extra.text=''
 image=p.find('.//'+V+'imagedata');shape=p.find('.//'+V+'shape')
 png=ROOT/'application/figures/print_polish'/f'{names[n]}.png'
 parts[relmap[image.get(R+'id')]]=png.read_bytes()
 width,height=Image.open(png).size
 shape.set('style',f'width:420pt;height:{420*height/width:.3f}pt;')
 shape.set('alt',f'图{n} '+captions[n])
 figure_records.append({'figure':n,'name':names[n],'png':png.relative_to(ROOT).as_posix(),'part':relmap[image.get(R+'id')],
                        'sha256':sha(png.read_bytes()),'width_pt':420,'height_pt':420*height/width,'caption':captions[n]})
assert len(figure_records)==10

edits={
 '四、国、内外研究现状和发展动态':'四、国内外研究现状与发展动态',
 '24V压力回路经150Ω精密电阻转换为0.6—3.0V信号，ADS1115采用3.3V供电；':'台架采用共地采集，24V压力回路经150Ω精密电阻转换为0.6—3.0V信号，经保护与滤波接入3.3V供电的ADS1115，两路结果通过I²C送至主控；',
 '考虑两通道误差、负载调整和压力漂移，采用数据质量检查、工况可比性判断及持续确认构成诊断流程':'考虑两通道误差、负载调整和压力漂移，先检查量程、计数窗口及记录完整性，再核对供压、轮灌和负载状态。满足比较条件后检验持续偏离，构成诊断流程',
 '按“参考标定与健康建模—工况约束诊断—分级采集与事件传输—处置记录与复核”组织技术路线。':'技术路线从参考标定和健康建模开始，依次完成工况判别、异常诊断、分级采集和事件传输，最后通过人工核查与复测形成处置记录。',
 '工况约束下的渐进故障诊断':'渐进故障诊断与工况判别',
 '拟拟定的研究目标':'拟定的研究目标',
 '拟达到的研究目标为':'研究目标为',
 '事件可靠交付':'事件可靠传输',
 '健康参照、阈值及评价规则':'健康参照、诊断阈值及评价规则',
 '按计划完成54次主要故障操作':'按计划完成54次主要故障操作',
 '在本地判断可靠记录的基础上评价通信':'完成本地诊断和数据记录后评价通信',
 '正式验证前固定方法和评价规则':'正式验证前确定方法和评价规则',
 '拟冻结':'拟确定',
 '研究增量需要体现在诊断条件与验证方法上':'研究改进应体现在诊断条件与验证方法上',
 '本项目拟形成两方面增量':'本项目拟围绕两方面开展研究',
 '触发监测、完整记录和无线发送的开销':'周期监测、完整记录和无线发送的开销',
 '与故障响应对应的事件采集与可靠告警':'事件触发采集与可靠传输',
 '共同约束远端及时性':'共同影响远端告警的及时性',
 '小幅故障的测量边界':'小幅故障变化的测量边界',
 '微小故障目标':'小幅故障变化的识别目标',
 '模型分析因此将工况信息、参考标定和有条件输出确定为后续方法研究的重点，使实验设计能够检验正常扰动与故障之间的差别。':'模型分析表明，后续研究应完善工况信息与参考标定，并据此约束诊断结果，使实验设计能够检验正常扰动与故障之间的差别。',
 '以单监测单元完成可演示、可复核的功能验证':'以一个监测单元完成可演示、可复核的功能验证',
 '两故障各20条回放':'两类故障各20条回放',
 '两类故障的两种方法均为20/20有效早期':'两类故障的两种方法均有20/20条试次满足有效早期条件',
 '固定流量阈值仍均为20/20':'固定流量阈值方法仍均为20/20',
 '经过5秒的确认条件':'持续至少5秒的确认条件',
 '在当前回放中也比同时加密发送的分级方案更少发送':'在当前回放中的发送次数也少于同时加密发送的分级采集方案',
 '当前程序只验证主机模拟状态':'当前程序仅验证主机端的模拟状态',
 '正常及证据不足不自动请求':'正常运行及证据不足时不生成自动请求',
 '留出批次及失败实例':'留出批次和失败实例',
}
changes=[]
for p in root.xpath('.//w:p',namespaces=NS):
 if re.match(r'^\[\d\]',tx(p)):continue
 for t in p.xpath('./w:r/w:t',namespaces=NS):
  if not t.text:continue
  before=t.text
  for old,new in edits.items():t.text=t.text.replace(old,new)
  if before!=t.text:changes.append({'before':before,'after':t.text})

# Match this subsection heading to the other two headings in the same section.
heading=next(t for t in rows[23].xpath('.//w:r/w:t',namespaces=NS) if t.text=='3 协议与平台软件')
bold=heading.getparent().find(W+'rPr/'+W+'b')
assert bold is not None
bold.set(W+'val','1')

# A one-cell table around this prose introduced two unintended horizontal rules.
# Keep the school form and figure wrappers, but restore this block to normal prose.
prose_table=next(a for a in heading.iterancestors() if a.tag==W+'tbl')
assert len(prose_table.findall(W+'tr'))==1
prose_cells=prose_table.xpath('./w:tr/w:tc',namespaces=NS)
assert len(prose_cells)==1
assert not prose_table.xpath('.//v:imagedata',namespaces=NS)
parent=prose_table.getparent();position=parent.index(prose_table)
section_text=tx(rows[23])
prose_paragraphs=prose_cells[0].findall(W+'p')
assert len(prose_paragraphs)==1 and tx(prose_paragraphs[0]).startswith('3 协议与平台软件')
for paragraph in prose_paragraphs:
 parent.insert(position,paragraph);position+=1
parent.remove(prose_table)
assert tx(rows[23])==section_text

# Keep operational details in prose, rather than as footers inside each diagram.
p=next(p for p in rows[18].xpath('.//w:p',namespaces=NS) if tx(p).startswith('图7展示'))
texts=p.xpath('./w:r/w:t',namespaces=NS);assert len(texts)==1
texts[0].text=texts[0].text.replace('图7展示正常接收与确认丢失后的处理过程。','图7展示正常接收与确认丢失后的处理过程。节点在匹配接收确认后标记事件已送达；达到重试上限后仍保留未确认事件，待链路恢复再核对。')

citations=[];pattern=re.compile(r'(\[[1-8](?:\s*[,，]\s*[1-8])*\])')
for p in root.xpath('.//w:p',namespaces=NS):
 if re.match(r'^\[\d\]',tx(p)):continue # Reference-list numbers remain on the baseline.
 for r in list(p.findall(W+'r')):
  t=r.find(W+'t')
  if t is None or not t.text or not pattern.search(t.text):continue
  assert all(c.tag in (W+'rPr',W+'t') for c in r),tx(p)
  parent=r.getparent();pos=parent.index(r)
  for token in pattern.split(t.text):
   if not token:continue
   new=deepcopy(r);new.find(W+'t').text=token
   if pattern.fullmatch(token):
    pr=new.find(W+'rPr')
    if pr is None:pr=E.Element(W+'rPr');new.insert(0,pr)
    va=pr.find(W+'vertAlign')
    if va is None:va=E.SubElement(pr,W+'vertAlign')
    va.set(W+'val','superscript');citations.append(token)
   parent.insert(pos,new);pos+=1
  parent.remove(r)
assert len(citations)>10
assert refs_before==[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[\d\]',tx(p))]
assert [E.tostring(x) for x in root.xpath('.//m:oMath',namespaces=NS)]==math_before and len(math_before)==27
for i,b in protected.items():assert E.tostring(rows[i])==b
parts['word/document.xml']=E.tostring(root,encoding='utf-8',xml_declaration=True,standalone=True)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
assert SRC.read_bytes()==original
record={'date':'2026-10-06','source':SRC.relative_to(ROOT).as_posix(),'source_sha256':sha(original),
 'output':OUT.relative_to(ROOT).as_posix(),'output_sha256':sha(OUT.read_bytes()),'figures':figure_records,
 'citations':citations,'superscript_citation_count':len(citations),'references':refs_before,'native_math_count':27,
 'language_changes':changes,'format_changes':['Removed the single-cell nested table and its top/bottom rules around subsection3; retained the bold heading and unchanged prose.'],
 'physical_validation':False,'data_changed':False}
(DATA/'build_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(DATA/'body.txt').write_text('\n\n'.join(tx(p) for row in rows[16:25] for p in row.xpath('.//w:p',namespaces=NS) if tx(p))+'\n',encoding='utf-8',newline='\n')
(TMP/'artifact.md').write_text('Source: accepted school-template application. Preserve personal/budget blanks, approval rows, references and27 OMML objects. Refine natural prose/captions, superscript reference citations and ten proportionate print figures. All-page native export and grayscale QA required.\n',encoding='utf-8')
print(f'New print-polished application:10 figures,27 preserved equations,{len(citations)} superscript citations. Render pending.')
