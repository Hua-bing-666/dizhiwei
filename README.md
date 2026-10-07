# 滴智卫 DiZhiWei

项目题目：**基于 LoRa 的南疆滴灌支管道早期故障诊断物联网原型系统**。

当前交付（2026年10月7日）：[学校模板申报书图文精修稿](deliverables/大创申报书_图文精修稿.docx)，18页、10图、3张完整居中数据表、11处原生公式和5中文＋3英文文献；[实施项目书现阶段更新稿](deliverables/实施项目书_现阶段更新稿.docx)，12页、5图、6表。保留信息和经费空位，更新软件基础、研究任务与三阶段执行安排。桌面V1.3删除装饰框图并重排模型标注，引线接在标签边缘。两种EXE各40项检查、界面50项、浏览器72项通过；压缩包512个文件摘要校验通过。参见[本轮验收](docs/图文与桌面体验精修验收.md)。以下版本说明为历史记录。

2026 年 10 月 7 日：桌面版 V1.3 参考用户提供的桌面程序组织方式，统一会话读数、图表与台架测点，增加本地交互图表、可暂停回放、测点聚焦、浅深色偏好及单文件 EXE。默认页面精简说明，协议和配置按需展开；自动回放不连续弹出保存提示。文件夹版和单文件版各通过 40 项实际桌面检查，界面与模型 48 项、浏览器 72 项、后台 34 项检查通过。申报书与诊断算法本轮未修改。入口见 [桌面使用说明](docs/桌面版使用说明.md)、[参考与执行计划](docs/桌面版V1.3参考分析与执行计划.md)和 [V1.3 验收记录](docs/桌面版V1.3验收记录.md)。二进制留在本机交付目录，源码与验收资料进入仓库。

2026年10月6日。当前申报入口为20页学校模板申报表达修订稿。对照用户提供的国家级案例，正文围绕巡检问题、系统目标、研究内容、创新点、实施安排及成果重新表达，减少论文推导与工程调试细节。10幅图片及打印几何保留，3张居中数据表完整同页，保留5中文＋3英文参考文献和必要原生公式。最终页面已逐项查看，信息、预算与审批空位保留。固定1Hz仍为当前软件基线，事件触发采集为后续独立对照任务；现有证据为设计、模型与主机软件。

## 当前运行平台 V1.2

桌面入口：本地 `deliverables/滴智卫_桌面版_V1.2/滴智卫.exe`。整包解压后双击即可自动连接内置后台，无需安装 Python 或 GCC；记录保存在独立的 `data` 目录。桌面版沿用八个运行模块，增加 Windows 保存窗口、重复启动保护和退出清理。[桌面使用说明](docs/桌面版使用说明.md)与[桌面验收记录](docs/桌面版V1.2验收记录.md)列明运行环境与实际检查结果。构建源代码在 `desktop/`，二进制在本机交付目录，不进入源码仓库。

2026年10月7日：网站已接入编译后的 C 诊断结果，提供离线回放与本地 HTTP / SQLite 两种模式。增加健康参照拟合、事件核查、软件控制请求演示、跨工况与采样策略实验工具；三维台架增加防溅板、过线开口及配套安装孔。此阶段仍是主机软件、未标定模型及概念 CAD，真实串口、LoRa 射频、能耗和阀门尚未验证，申报书本轮未修改。

本轮先明确八页职责与共享结构，移出总览中的重复趋势，独立策略实验与试验台架。增加只读历史会话查询、静态模块滚动渐显与减少动态效果支持。台架使用同一207构件几何，增加实际网格包络查看与实验路径。后台复用状态快照和批量核查记录读取。

[本轮结构计划](docs/运行平台结构与交互实施计划.md)、[UI参考](docs/运行平台UI参考与采用说明.md)、[V1.2验收](docs/运行平台V1.2验收记录.md)。

- [运行平台](deliverables/index.html)：八个职责明确的运行模块，合成来源和候选、短窗提示、质量状态分开呈现。
- [清水试验台架 V1.2](deliverables/清水试验台架_V1.2.html)：207个概念构件，实体 STEP 与实际网格一致。
- [软件包](deliverables/滴智卫_运行平台_V1.2.zip)、[使用说明](docs/软件升级包使用说明.md)、[分项计划](docs/软件算法与三维升级执行计划.md)、[验收记录](docs/软件算法与三维升级验收记录.md)。
- 启动：PowerShell 运行 `scripts/启动运行平台.ps1`，通过 `http://127.0.0.1:8765` 打开网页，展开“回放控制”，再连接本地后端。数据库保留在 `tmp/platform_runtime/operations.sqlite`。

网页重建入口为 `scripts/build_portal.py --operations-only`，当前会复用 `simulation/platform_upgrade/web_data.json`。新实验依次运行 `simulation/extend_platform_reference.py`、`scripts/build_system_upgrade.py`；软件验收使用 `scripts/verify_platform_upgrade.py` 与 `scripts/verify_platform_browser.mjs`。下文旧版本记录保留作历史来源，不替代当前 V1.2 的验收。

## 最新入口

- [学校模板申报书申报表达修订稿](deliverables/大创申报书_申报表达修订稿.docx)：当前交付，20页、10幅保留图片、3张完整数据表、8篇参考文献。[表达修订与可行性判断](docs/申报表达修订与可行性判断.md)、[精确文件检查](application/proposal_revision/acceptance.json)、[最终页面审阅记录](application/proposal_revision/visual_review.json)。本版不新增硬件或算法成果。
- [学校模板申报书方法与图文完善稿](deliverables/大创申报书_方法与图文完善稿.docx)：上一版历史稿。双时间窗流程区分短窗待复核与主窗候选；算法对照使用黑白纹理，324条冻结记录逐组核对；前期K/R界面与模型反例保留并注明阶段。[本版验收](docs/申报书方法与图文完善验收.md)、[精确文件检查](application/method_revision/acceptance.json)、[最终逐页及灰度图审阅记录](application/method_revision/visual_review.json)。
- [学校模板申报书研究方案收敛稿](deliverables/大创申报书_研究方案收敛稿.docx)：20页、10图、3张完整居中数据表、8篇文献、29个原生公式，全部最终页面已查看。[本版图文验收](docs/研究方案收敛稿_图文验收.md)、[软件收尾报告](deliverables/软件链路收尾验证.md)、[最终方法与三阶段安排](docs/算法与软件最终方案.md)。信息、预算及审批区域保持用户源稿空白。
- [实施项目书](deliverables/实施项目书.docx) / [原生审阅PDF](deliverables/实施项目书.pdf)：13页、9章、5图、6张可编辑表；四工作包、实验协议、资源、里程碑、返工与归档。为自主执行稿，正式任务书尚待取得并填写。
- [本次公式与插图验收](docs/申报书公式与插图修订验收.md) / [当前验收记录](deliverables/申报书公式与插图修订验收记录.json)：27个原生数学对象由WPS识别，重新保存后核对公式含义，20页实际图像和八幅新图复核；四表居中完整、图注同页、原稿保护；三处必要分页留白列明。[前一轮语言与范围验收](docs/申报书语言与研究范围修订验收.md)、[分页检查](docs/申报书分页与图片复核.md)及[表格文献与职责修订](docs/表格文献与材料职责修订验收.md)作为历史依据保留。[材料职责与分项标准](docs/材料职责与本轮修订标准.md)划分各项职责。
- [运行平台](deliverables/index.html)：运行总览、支管监测、异常事件、设备与链路、历史记录、系统设置，共享合成回放与本地人工维护记录。
- [历史研究与答辩资料](deliverables/研究与答辩资料.html)：原研究文献库、历史统计、旧材料和草案PPT；由文件目录单独打开，不进入运行网站导航，也不作为最新申报书入口。
- [收集优化三维候选模型](deliverables/台架三维结构交互模型_收集优化候选版.html)：离线可旋转、查看；STEP/GLB与几何源在application/models/collection_review。暂定尺寸不用于加工下单。
- [执行台账](docs/项目总规划与任务验收台账.md) / [三阶段分项标准](docs/三阶段分项执行与验收标准.md) / [本轮Q01—Q07计划](docs/全量复核与格式优化执行计划.md)。
- [使用说明](deliverables/使用说明.md)。此前[材料包](deliverables/申报材料与证据包.zip)及[哈希清单](deliverables/证据清单.json)保留上一轮25页、17篇文献的历史版本，本次修订直接使用上列最新文件与修订记录，不挪用旧包的验收状态。

## 系统与三阶段约束

拟实施期2027年3月至2028年2月。原型方案为一个P0/P1/Q双压力流量节点、一个E220接收字节桥、现有PC上的SQLite及本地Web、双支路清水台架。A测量与故障注入，B只作正常共享水源扰动。定位只到监测支管/区段，节流不证明真实滴头堵塞。后续先研究跨负载、供压和日期的健康参照更新，再增加节点开展同步支管关联和巡检价值评价。台架流量计不能直接套用大田支管量程，迁移需重新选型标定；自动阀控、多节点、太阳能和云端需新资源与验收。

约2000元是借用连续水源及参考仪器条件下的启动估算，不是已获经费或报价。真实团队开发能力、导师、场地、借用和压力传感器规格仍待落实。20秒泄漏取样先要求实测安全液位有效容量≥440mL；长时实验另设排水。电气保护定值与实际器件规格确认后才进入上电。

申报负责论证任务和条件；实施负责真实系统和独立实验；论文从实测提炼一项充分贡献。主线为跨供压、跨负载的辨识边界，通信取舍为备选。省级第一完成人4分加符合条件6分论文可按用户今年截图达10分，但未来年度政策、认可成果及截止须确认，不能保证立项级别、发表或加分。

## 模型与来源

当前诊断版本20261004-A06A07-v1，480个合成试次、960条配对方法结果、288个有界误差组合；20个基础序列复用，不是480次独立实测。高压力噪声劣势、未知健康负载同形、漂移与负载模型失配均保留，见[诊断证据](docs/仿真建模与诊断证据分项验收.md)及[可复现说明](simulation/diagnosis_review/README.md)。

通信1920条历史回放与12项主机协议检查不等于实际射频或整机能耗。199个有效CAD实体、局部交集与离散姿态不等于全装配或制造验收。新增理想脉冲相位分析20,000组不等于流量计实测，见simulation/quality_review/sampling_checks.json。

[硬件接口及LoRa论证](docs/硬件接口与LoRa通信论证分项验收.md)、[国内硬件与淘宝入口](docs/国内硬件选型与可行性核对.md)、[参考文献核验](docs/参考文献核验与正文对应.md)、[学校来源记录](application/school_templates/provenance.json)。候选配图不是本项目实物，淘宝入口不保证现货或价格。

官方2026立项及验收要求只作为历史参考。任务书下载返回验证码网页，未取得实际官方DOC；自主实施稿未声称套入官方表。2027规定、正式身份、编号、意见及签字待本人、导师和学院办理。外部案例原件与个人信息未纳入仓库，级别来自用户说明。

## 修改与复现

本轮方法与图文修订依次使用scripts/prepare_method_application_figures.py、scripts/render_method_application_figures.mjs、scripts/update_method_application.py、scripts/export_method_application.ps1和scripts/render_quality_documents.py；逐页查看最终页面并逐张查看实际嵌入图片的灰度版本后，保存application/method_revision/visual_review.json，再运行scripts/verify_method_application.py。源稿为上列研究方案收敛稿；修改图文后必须重新渲染、查看并更新对应指纹，不能直接沿用人工记录。本轮不修改冻结算法及其既有结果。

本次软件收尾依次运行scripts/validate_acquisition_pipeline.py A、B，simulation/review_acquisition_pipeline.py完整回放，再运行validate_acquisition_pipeline.py C与plot_acquisition_closeout.py。先检查已冻结指纹，不以重新冻结掩盖来源变化。Word本版使用scripts/update_submission_closeout.py、export_submission_closeout.ps1、render_quality_documents.py及verify_submission_closeout.py；逐页查看记录位于application/software_closeout。用户源111.docx不随仓库上传，因此改稿复现需要本机保留源文件；当前最终DOCX及验收指纹已纳入仓库。下文为历史流程，不能覆盖最新用户稿或挪用历史验收。

当前稿另存于deliverables/大创申报书_公式与插图修订稿.docx，内部PDF为大创申报书_公式与插图审阅版.pdf。复现依次使用scripts/prepare_equation_figure_revision.py、scripts/render_equation_figures.mjs、scripts/revise_native_equations.py、scripts/export_equation_application.ps1、scripts/render_quality_documents.py及scripts/verify_equation_application.py；实际查看页面及新图后记录scripts/finalize_equation_revision.py。当前为20页，9图打印尺寸及正文字号保留，4表完整同页且居中；第8、12、18页保留有理由的页尾留白。记录在simulation/equation_figure_review与application/equation_figure_revision。人工记录仅对当前哈希有效，后续修改不得沿用。

此前语言与范围稿使用scripts/rewrite_application_language.py、scripts/export_language_application.ps1、scripts/verify_language_application.py及scripts/finalize_language_scope_revision.py，记录在simulation/language_scope_review与application/language_scope_revision，保留为本次原始输入及历史依据。

前一轮紧凑排版稿及其PDF作为历史版本保留，原验收见docs/申报书分页与图片复核.md。其正文未改的20页排版检查不能用于证明当前重写稿的页尾留白或内容状态。此前生成脚本与simulation/compact_layout_review、application/compact_layout_revision供历史复现。

当前申报文字源是application/正式模板正文.md，本次快照在application/equation_figure_revision，新图在application/figures/equation_revision。实施项目书源为application/实施项目书.md，尚未随前一轮研究范围细化重写。application/language_scope_revision、application/table_reference_revision与application/quality_release保留历史版本。运行文档工具使用捆绑Python：C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe，浏览器工具使用同目录Node与本机Edge。PDF采用WPS原生导出和捆绑PDFium逐页渲染；每次正文或图片改变都必须重新检查实际版面。

此前24页表格与文献修订使用scripts/revise_application_tables_references.py、scripts/export_revised_application.ps1和scripts/verify_revised_application.py。渲染使用scripts/render_quality_documents.py，24页人工查看记录在simulation/table_reference_review/visual_review.json。scripts/finalize_table_reference_revision.py只允许已记录的相同图像通过，不能替代新的人工审阅。prepare_quality_payload、fill_quality_application和verify_quality_application依赖17篇历史正文，不用于当前修订稿。

实施书生成：scripts/build_execution_book.py → PowerShell7运行scripts/export_quality_book.ps1 → scripts/render_quality_documents.py将PDF渲染至tmp/quality_book/render-v4 → scripts/verify_execution_book.py → 人工逐页查看。该校验记录当前已查看的前12页哈希；修改正文后应建立新一轮审阅及记录，不能沿用旧的人工通过状态。

本次网站独立重建使用scripts/build_portal.py --operations-only，检查使用scripts/verify_revised_site.mjs，不修改文档、独立研究页或历史记录。模型原数据及实体本次未改。后续模型只读核对可用CAD环境tmp/cad_runtime运行scripts/quality_recheck.py --cad；图生成和浏览器图检查使用scripts/build_quality_figures.py与scripts/verify_quality_visuals.mjs。三维页面使用scripts/build_bench_viewer.py --collection-review与scripts/verify_quality_model_viewer.mjs。图像改变后须重新检查包含该图的文档，不沿用旧人工通过状态。

当前修订的机器检查、人工记录和文件哈希保存于simulation/equation_figure_review及deliverables/申报书公式与插图修订验收记录.json。simulation/language_scope_review及对应记录为前一版；simulation/table_reference_review及deliverables/表格文献与职责修订验收记录.json对应此前24页稿。verify_quality_release、update_quality_release_content、finalize_quality_release和旧材料包针对上一轮25页/17篇文件，不作为本次入口，也不能覆盖本次正文。一次性迁移脚本保留作来源说明。

## 历史材料

[上一轮25页申报PDF](deliverables/大创申报书_格式优化审阅版.pdf)及[全量验收](docs/全量复核与格式优化验收报告.md)保留为历史记录。[24页原学校模板稿](deliverables/大创申报书_模板填写稿.docx)及[整合验收](docs/学校模板申报书整合与分项验收.md)为更早基线。[6页旧范围草案](deliverables/项目书审阅版.pdf)不替代当前实施书。[15页答辩PPT](deliverables/立项答辩.pptx)及原PDF为历史草案，硬件、预算和最新截图待内容稳定后单独同步；本次未改PPT。

主站30组页面/视口、24回放、21项交互及3项实际导出通过本次检查。运行界面只保留业务功能，不链接申报、项目书、模型或验收报告。网站没有接入真实串口、SQLite服务、设备权限或RF；localStorage仅用于当前演示。文件移动、换浏览器或清除站点数据可能丢失记录，演示记录需导出。材料尚未提交或批准。
