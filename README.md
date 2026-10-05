# 滴智卫 DiZhiWei

项目题目：**基于 LoRa 的南疆滴灌支管道早期故障诊断物联网原型系统**。

2026年10月5日。当前交付为24页学校模板申报书表格与文献修订稿、13页实施项目书和六模块离线运行网站。申报精选文献为5篇中文、3篇英文。四工作包覆盖测量与建模、故障诊断边界、LoRa可靠告警、集成与独立评价。现有证据为未标定模型、概念几何、候选接口、主机检查和合成回放；没有硬件、射频、功耗或田间实测。

## 最新入口

- [学校模板申报书表格与文献修订稿](deliverables/大创申报书_表格与文献修订稿.docx) / [原生审阅PDF](deliverables/大创申报书_表格与文献修订审阅版.pdf)：24页、9图、4张可编辑表、8篇文献，中文5篇、英文3篇；四表与表题、表头居中，原封面、九节正文及审批区域保留。
- [实施项目书](deliverables/实施项目书.docx) / [原生审阅PDF](deliverables/实施项目书.pdf)：13页、9章、5图、6张可编辑表；四工作包、实验协议、资源、里程碑、返工与归档。为自主执行稿，正式任务书尚待取得并填写。
- [本次表格文献与职责修订验收](docs/表格文献与材料职责修订验收.md) / [修订记录](deliverables/表格文献与职责修订验收记录.json)：本次24页逐页审阅、实际表格中心核对、八篇文献及网站检查。[材料职责与分项标准](docs/材料职责与本轮修订标准.md)明确申报、实施、仿真、模型、网站和PPT分别负责的内容。
- [运行平台](deliverables/index.html)：运行总览、支管监测、异常事件、设备与链路、历史记录、系统设置，共享合成回放与本地人工维护记录。
- [历史研究与答辩资料](deliverables/研究与答辩资料.html)：原研究文献库、历史统计、旧材料和草案PPT；由文件目录单独打开，不进入运行网站导航，也不作为最新申报书入口。
- [收集优化三维候选模型](deliverables/台架三维结构交互模型_收集优化候选版.html)：离线可旋转、查看；STEP/GLB与几何源在application/models/collection_review。暂定尺寸不用于加工下单。
- [执行台账](docs/项目总规划与任务验收台账.md) / [三阶段分项标准](docs/三阶段分项执行与验收标准.md) / [本轮Q01—Q07计划](docs/全量复核与格式优化执行计划.md)。
- [使用说明](deliverables/使用说明.md)。此前[材料包](deliverables/申报材料与证据包.zip)及[哈希清单](deliverables/证据清单.json)保留上一轮25页、17篇文献的历史版本，本次修订直接使用上列最新文件与修订记录，不挪用旧包的验收状态。

## 系统与三阶段约束

拟实施期2027年3月至2028年2月。基础为一个P0/P1/Q双压力流量节点、一个E220接收字节桥、现有PC上的SQLite及本地Web、双支路清水台架。A测量与故障注入，B只作正常共享水源扰动。定位只到监测支管/区段，节流不证明真实滴头堵塞；自动阀控、多节点、太阳能和云端需新资源与验收。

约2000元是借用连续水源及参考仪器条件下的启动估算，不是已获经费或报价。真实团队开发能力、导师、场地、借用和压力传感器规格仍待落实。20秒泄漏取样先要求实测安全液位有效容量≥440mL；长时实验另设排水。电气保护定值与实际器件规格确认后才进入上电。

申报负责论证任务和条件；实施负责真实系统和独立实验；论文从实测提炼一项充分贡献。主线为跨供压、跨负载的辨识边界，通信取舍为备选。省级第一完成人4分加符合条件6分论文可按用户今年截图达10分，但未来年度政策、认可成果及截止须确认，不能保证立项级别、发表或加分。

## 模型与来源

当前诊断版本20261004-A06A07-v1，480个合成试次、960条配对方法结果、288个有界误差组合；20个基础序列复用，不是480次独立实测。高压力噪声劣势、未知健康负载同形、漂移与负载模型失配均保留，见[诊断证据](docs/仿真建模与诊断证据分项验收.md)及[可复现说明](simulation/diagnosis_review/README.md)。

通信1920条历史回放与12项主机协议检查不等于实际射频或整机能耗。199个有效CAD实体、局部交集与离散姿态不等于全装配或制造验收。新增理想脉冲相位分析20,000组不等于流量计实测，见simulation/quality_review/sampling_checks.json。

[硬件接口及LoRa论证](docs/硬件接口与LoRa通信论证分项验收.md)、[国内硬件与淘宝入口](docs/国内硬件选型与可行性核对.md)、[参考文献核验](docs/参考文献核验与正文对应.md)、[学校来源记录](application/school_templates/provenance.json)。候选配图不是本项目实物，淘宝入口不保证现货或价格。

官方2026立项及验收要求只作为历史参考。任务书下载返回验证码网页，未取得实际官方DOC；自主实施稿未声称套入官方表。2027规定、正式身份、编号、意见及签字待本人、导师和学院办理。外部案例原件与个人信息未纳入仓库，级别来自用户说明。

## 修改与复现

当前文字源是application/正式模板正文.md与application/实施项目书.md。本次申报快照在application/table_reference_revision，application/quality_release保留上一轮版本。运行文档工具使用捆绑Python：C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe，浏览器工具使用同目录Node与本机Edge。PDF采用WPS原生导出和捆绑PDFium逐页渲染；每次正文或图片改变都必须重新检查实际版面。

本次申报基于用户当前DOCX另存修订文件，原文件保持原字节；编辑脚本为scripts/revise_application_tables_references.py，导出为scripts/export_revised_application.ps1，检查为scripts/verify_revised_application.py。渲染使用scripts/render_quality_documents.py，24页人工查看记录在simulation/table_reference_review/visual_review.json。scripts/finalize_table_reference_revision.py只允许已记录的相同图像通过，不能替代新的人工审阅。上一轮prepare_quality_payload、fill_quality_application和verify_quality_application依赖17篇历史正文，不用于当前修订稿。

实施书生成：scripts/build_execution_book.py → PowerShell7运行scripts/export_quality_book.ps1 → scripts/render_quality_documents.py将PDF渲染至tmp/quality_book/render-v4 → scripts/verify_execution_book.py → 人工逐页查看。该校验记录当前已查看的前12页哈希；修改正文后应建立新一轮审阅及记录，不能沿用旧的人工通过状态。

本次网站独立重建使用scripts/build_portal.py --operations-only，检查使用scripts/verify_revised_site.mjs，不修改文档、独立研究页或历史记录。模型原数据及实体本次未改。后续模型只读核对可用CAD环境tmp/cad_runtime运行scripts/quality_recheck.py --cad；图生成和浏览器图检查使用scripts/build_quality_figures.py与scripts/verify_quality_visuals.mjs。三维页面使用scripts/build_bench_viewer.py --collection-review与scripts/verify_quality_model_viewer.mjs。图像改变后须重新检查包含该图的文档，不沿用旧人工通过状态。

当前修订的机器检查、人工记录和文件哈希各自保存于simulation/table_reference_review及deliverables/表格文献与职责修订验收记录.json。verify_quality_release、update_quality_release_content、finalize_quality_release和旧材料包针对上一轮25页/17篇文件，不作为本次入口，也不能覆盖本次正文。一次性迁移脚本保留作来源说明。

## 历史材料

[上一轮25页申报PDF](deliverables/大创申报书_格式优化审阅版.pdf)及[全量验收](docs/全量复核与格式优化验收报告.md)保留为历史记录。[24页原学校模板稿](deliverables/大创申报书_模板填写稿.docx)及[整合验收](docs/学校模板申报书整合与分项验收.md)为更早基线。[6页旧范围草案](deliverables/项目书审阅版.pdf)不替代当前实施书。[15页答辩PPT](deliverables/立项答辩.pptx)及原PDF为历史草案，硬件、预算和最新截图待内容稳定后单独同步；本次未改PPT。

主站30组页面/视口、24回放、21项交互及3项实际导出通过本次检查。运行界面只保留业务功能，不链接申报、项目书、模型或验收报告。网站没有接入真实串口、SQLite服务、设备权限或RF；localStorage仅用于当前演示。文件移动、换浏览器或清除站点数据可能丢失记录，演示记录需导出。材料尚未提交或批准。
