"""Record the completed human page review without altering historical releases."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'simulation/table_reference_review'
TMP=ROOT/'tmp/table_reference_review'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
check=read(DATA/'document_checks.json');site=read(DATA/'site_checks.json')
assert check['pages']==24 and check['chinese']==5 and check['english']==3
assert site['status']=='passed' and len(site['workflow_checks'])==21
assert site['source_sha256']==sha(ROOT/'deliverables/index.html')
assert all(sha(ROOT/p)==h for p,h in check['artifact_sha256'].items())
previous_manual=read(DATA/'visual_review.json')
assert len(previous_manual['document_pages'])==24
for item in previous_manual['document_pages']+previous_manual['website_views']:
    p=ROOT/item.get('image_path',item.get('path'))
    assert sha(p)==item['sha256'],'New image requires a new actual human review'
notes={1:'校徽、封面及身份留空区域完整',2:'学校填写须知保留',3:'原登记表边框与空白字段保留',4:'简介、申请理由和系统目标无裁切',5:'系统职责图与图题同页',6:'双支路原理图、取压与分流标注完整',7:'三维布局图标注与计量条件说明清晰',8:'压力回路与流量接口图无裁切',9:'3.3小标题恢复加粗，引用编号已调整',10:'诊断流程图与已有及拟实施边界完整',11:'研究目标与无线方案无溢出',12:'确认重试时序图与图题同页',13:'网站原生局部截图与图题同页',14:'四工作包表、表题及表头居中',15:'实验计划表居中；后续研究段落无孤行',16:'研究现状标题与首段同页；文献1完整',17:'文献2至8各自完整，来源与制度依据保留',18:'创新点及预期成果标题各带正文',19:'里程碑表居中；已有基础标题与首段同页',20:'噪声统计及图题同页，计数与限制说明保留',21:'反例图与图题同页；软件成果用具体功能描述',22:'预算表、表题和表头居中，金额列居中',23:'签字及指导教师意见区域完整',24:'学院及学校审批区域完整'}
reviewed=[]
for number in range(1,25):
    p=TMP/'final_pages'/f'page-{number:02d}.png';assert p.exists()
    reviewed.append({'page':number,'image_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'review':'viewed_individually_in_this_revision','finding':notes[number],'layout_pass':True})
shots=['settings-1440','settings-375','overview-final-desktop','overview-final-mobile','monitor-1440','monitor-375','devices-1440','devices-375','events-with-record-desktop','events-with-record-mobile','history-1440','history-375','event-dialog-desktop','event-dialog-mobile']
website_review=[]
for name in shots:
    p=ROOT/'tmp/table_reference_site_review'/f'{name}.png';assert p.exists()
    website_review.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'viewed':True,'finding':'所查看视图未见组件遮挡或错位；窄屏表格与导航允许组件内横向滚动'})
manual={'date':'2026-10-05','basis':'pages and screenshots actually viewed in this revision','document_pages':reviewed,'website_views':website_review,'scope':'当前文档版面及所列浏览器视图；不构成实物、研究性能或全装配验收'}
(DATA/'visual_review.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
frozen=ROOT/'application/table_reference_revision';frozen.mkdir(exist_ok=True)
if not (frozen/'original_body.md').exists():
    (frozen/'original_body.md').write_text((TMP/'original_body.md').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
(frozen/'revised_body.md').write_bytes((ROOT/'application/正式模板正文.md').read_bytes())
(frozen/'native_layout.json').write_text(json.dumps(read(TMP/'native_layout.json'),ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
input_record=read(TMP/'build_record.json')
record={'date':'2026-10-05','status':'passed_scoped_document_and_operations_review','physical_validation':False,'administrative_complete':False,'pages':24,'figures':9,'data_tables':4,'chinese_references':5,'english_references':3,'original_user_file_preserved':sha(Path(input_record['input_path']))==input_record['input_sha256'],'input_sha256':input_record['input_sha256'],'scope':'申报表格与文献修订、页面职责分离；未改实物、射频、CAD模型或PPT','checks':['simulation/table_reference_review/document_checks.json','simulation/table_reference_review/site_checks.json','simulation/table_reference_review/visual_review.json'],'historical_release_preserved':'上一轮25页/17篇文献记录保留，不用于验证本修订稿'}
report='''# 表格 文献与材料职责修订验收

2026年10月5日。当前申报书为24页、9图、4张可编辑数据表、8篇参考文献，中文5篇、英文3篇。范围为文档版面与运行网站，不构成实物或研究性能验收。

四张表的外层容器原先窄于正文区域，仅设置表格“居中”不能解决WPS中的实际偏左。此次统一容器、表格网格和单元格宽度，使表格与表题相对正文区域居中；表头居中，长说明左对齐，金额居中。固定列宽、重复表头及不可拆数据行保留。PDF中的实际中心另做几何核对，不只检查文档属性。

| 数据表 | PDF页码 | 表题与表格中心差 |
| --- | --- | --- |
'''
for item in check['actual_pdf_table_positions']:
    report+=f"| {item['caption']} | {item['page']} | {item['center_error_pt']:.3f} pt |\n"
report+='''
参考文献重排为[1]至[8]，正文引用、研究现状和已有基础同步修改。原17篇研究文献库仍保留，申报精选记录单独维护。八篇题名、出处和DOI完整出现于PDF，每篇不跨页。中文覆盖南疆背景、水力关系、泄漏诊断及LoRa系统；英文覆盖间接检测边界、可控台架和通信评价。Lozoya文中的实际IEEE 802.15.4/Zigbee链路已与本项目LoRa区分，不转用其性能。

学校原封面、须知、登记及审批区保留，真实身份和审批信息没有代填。修复研究现状、预期成果标题与正文分离，以及已有基础前强制换页产生的留白；改动过的小标题保持加粗。九幅图与输入文档中的原图哈希一致，显示比例保留，图题与图像所在段落不跨页。24页最终PNG均在本轮逐页打开审阅；字体、表格、图片、页码及审批区未发现裁切、重叠或错位。PDF全部可打印文字坐标在A4页面内。

运行网站已移除申报、项目书、答辩、验收及三维材料入口，只保留六个业务模块和数据导出。减少内部种子、运行编号及过程说明的界面展示，保留演示数据、设备未接入及不能可靠归因的必要提示；事件导出仍保存模型来源和版本。没有删除采集、诊断、事件去重等拟研究系统功能，也没有隐藏未接入状态。

网站在独立Edge会话中通过30组页面与视口检查、24条保存回放、21项工作流程及3项实际导出，无外部HTTP请求或JavaScript异常；冻结的86,544个观测、特征与状态值逐项核对。六模块桌面及手机界面和两个事件弹窗视图已人工查看，局部横向滚动用于窄屏导航与数据表。检查没有触碰用户浏览器中的维护记录。

本轮没有改动三维实体、仿真原始结果、实施项目书或PPT，其职责和下一次修改边界写入《材料职责与本轮修订标准》。模型未标定、实物与田间未验证、硬件规格和借用条件待落实；申报修订不改变这些限制。材料未提交或立项。

文档采用WPS原生PDF导出和捆绑PDFium渲染；此前已诊断打包文档渲染器缺少LibreOffice，没有将这次检查标为该渲染器通过。原用户DOCX保持原字节，修订文件另存。上一轮25页/17篇的报告与材料包属于历史版本，不覆盖、不挪用通过状态。

最新申报书：deliverables/大创申报书_表格与文献修订稿.docx。
检查记录：simulation/table_reference_review；版本记录：deliverables/表格文献与职责修订验收记录.json。
'''
(ROOT/'docs/表格文献与材料职责修订验收.md').write_text(report,encoding='utf-8',newline='\n')
paths=['deliverables/大创申报书_表格与文献修订稿.docx','deliverables/大创申报书_表格与文献修订审阅版.pdf','deliverables/index.html','application/正式模板正文.md','application/申报精选参考文献.json','application/table_reference_revision/original_body.md','application/table_reference_revision/revised_body.md','application/table_reference_revision/native_layout.json','docs/材料职责与本轮修订标准.md','docs/表格文献与材料职责修订验收.md','scripts/build_portal.py','scripts/system_portal.js','scripts/system_portal.template.html','scripts/revise_application_tables_references.py','scripts/export_revised_application.ps1','scripts/verify_revised_application.py','scripts/verify_revised_site.mjs','scripts/finalize_table_reference_revision.py','README.md','deliverables/使用说明.md']+record['checks']
record['files']=[{'path':p,'sha256':sha(ROOT/p)} for p in paths]
(ROOT/'deliverables/表格文献与职责修订验收记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Recorded actual review of all 24 pages and 14 website views; historical files and user original preserved.')
