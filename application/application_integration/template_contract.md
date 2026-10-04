学校模板执行约束
Reference: 原学校DOC的只读转换参考；转换文件留在本地tmp/reference_review/template.docx，不作为附件重复交付。
SHA256: e0ab74dc46e7baacc4b04c4b42f152b1c482d47f8d1a2e2356cf7b96307e7ded
8页原生参考PDF，全部页面已查看。原DOC哈希91a6fe38b74c804482859fc3a5e5369bac2c781069984a5a7b3baf131bf7d48d不变。
A4纵向两节：封面及须知左/右1.25英寸，上/下1英寸；正文左/右/上/下约0.98英寸。两节与页脚规则保持。保留封面徽标、31行主表、签字及审批区。
主表第17—25行为九节编辑槽；COM全文Cells第63—71格。标题与起止时间分别Cells2/6，负责人13—17，科研情况19，导师简介60及支持62。名单、签字、意见未知，保留待填写并记行政未完成。
正文宋体10.5pt、单倍，Times New Roman西文；黑色标题，间隔不堆装饰，5pt段后。正文行可跨页。八张图410pt，网站局部图380pt，主要图字至少9pt，图注9pt；四表425pt、9.5pt，自适应行高，表头重复，浅灰表头与可见浅灰网格。表格列宽由payload冻结。
图片逐张原生InlineShape，与图注同段软换行；模板九节顺序不变。表格用无可见边框的分页容器保持记录与表题；这是排版容器，不是装饰面板。保留17文献原编号，用不可分行维护完整引文。
源内容application/正式模板正文.md，八图来自既有图源选择，第七图使用application/figures/application_integration/website_diagnosis_panel.png重新原生截取；具体图源和尺寸由payload.json冻结。本轮新增研究目标仅为拟定，实物未验证。
学校模板是视觉权威，不替换通用设计。字体、页脚、封面、审批文字以及模板媒体保持；正文扩展允许增加分页。所有新PDF页面均须检查，并绑定最终文件哈希。
包清单template-package.json；section/style证据template-style.json；图及表槽application_payload.json。
打包渲染器已尝试，日志证实本机无LibreOffice；使用WPS原生导出加bundled Poppler渲染，不安装替代办公软件。
