# 滴智卫 DiZhiWei

项目题目：**基于 LoRa 的南疆滴灌支管道早期故障诊断物联网原型系统**。

2026年10月5日。当前交付为25页学校模板申报书格式优化稿、13页实施项目书和六模块离线运行网站。四工作包覆盖测量与建模、故障诊断边界、LoRa可靠告警、集成与独立评价。现有证据为未标定模型、概念几何、候选接口、主机检查和合成回放；没有硬件、射频、功耗或田间实测。

## 最新入口

- [学校模板申报书格式优化稿](deliverables/大创申报书_格式优化稿.docx) / [原生审阅PDF](deliverables/大创申报书_格式优化审阅版.pdf)：25页、9图、4张可编辑表、17篇文献，中文11篇、英文6篇；原封面、正文结构及审批区域保留。
- [实施项目书](deliverables/实施项目书.docx) / [原生审阅PDF](deliverables/实施项目书.pdf)：13页、9章、5图、6张可编辑表；四工作包、实验协议、资源、里程碑、返工与归档。为自主执行稿，正式任务书尚待取得并填写。
- [全量复核与格式优化验收报告](docs/全量复核与格式优化验收报告.md) / [验收记录](deliverables/格式优化与实施项目书验收记录.json)：具体通过项、源与图像哈希、人工审阅和未完成项。
- [运行平台](deliverables/index.html)：运行总览、支管监测、异常事件、设备与链路、历史记录、系统设置，共享合成回放与本地人工维护记录。
- [独立研究与答辩资料](deliverables/研究与答辩资料.html)：文献、历史统计、材料和PPT，旧配置身份已提示；与运行页面分开。
- [收集优化三维候选模型](deliverables/台架三维结构交互模型_收集优化候选版.html)：离线可旋转、查看；STEP/GLB与几何源在application/models/collection_review。暂定尺寸不用于加工下单。
- [执行台账](docs/项目总规划与任务验收台账.md) / [三阶段分项标准](docs/三阶段分项执行与验收标准.md) / [本轮Q01—Q07计划](docs/全量复核与格式优化执行计划.md)。
- [材料与证据包](deliverables/申报材料与证据包.zip) / [使用说明](deliverables/使用说明.md) / [证据哈希清单](deliverables/证据清单.json)。解压后保留目录，打开deliverables/index.html。

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

当前文字源是application/正式模板正文.md与application/实施项目书.md；发布时冻结到application/quality_release。运行文档工具使用捆绑Python：C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe，浏览器工具使用同目录Node与本机Edge。PDF采用WPS原生导出和捆绑PDFium逐页渲染；每次正文或图片改变都必须重新检查实际版面。

申报生成：scripts/prepare_quality_payload.py → PowerShell7运行scripts/fill_quality_application.ps1 → scripts/render_quality_documents.py渲染候选PDF → scripts/verify_quality_application.py --render-dir tmp/quality_application/render-final → 人工逐页查看。原模板必须保留，不能直接修改被冻结版式记录。

实施书生成：scripts/build_execution_book.py → PowerShell7运行scripts/export_quality_book.ps1 → scripts/render_quality_documents.py将PDF渲染至tmp/quality_book/render-v4 → scripts/verify_execution_book.py → 人工逐页查看。该校验记录当前已查看的前12页哈希；修改正文后应建立新一轮审阅及记录，不能沿用旧的人工通过状态。

本轮模型只读复核：CAD Python环境tmp/cad_runtime运行scripts/quality_recheck.py --cad。图生成scripts/build_quality_figures.py，浏览器图核查scripts/verify_quality_visuals.mjs；网站重建scripts/build_portal.py，运行scripts/verify_quality_site.mjs与scripts/capture_quality_panel.mjs。三维页面运行scripts/build_bench_viewer.py --collection-review，核查scripts/verify_quality_model_viewer.mjs。新文档未发布时可用build_portal.py --pages-only先重建网站；完整清单在发布后刷新。图或网站截图改变后，需要重新生成和检查含该图的文档。

发布前检查scripts/verify_quality_release.py；刷新入口scripts/update_quality_release_content.py，冻结和发布scripts/finalize_quality_release.py要求已经存在的人工审阅记录与机器检查一致，不能代替新人工审阅。重建网站及证据清单后运行scripts/package_submission.py核对压缩包。旧分项finalize、旧qa及一次性迁移脚本保留作历史复现，不作为本轮发布入口。

## 历史材料

[24页原学校模板稿](deliverables/大创申报书_模板填写稿.docx)及[整合验收](docs/学校模板申报书整合与分项验收.md)是本轮基线，保留原哈希。[6页旧范围草案](deliverables/项目书审阅版.pdf)不替代当前实施书。[15页答辩PPT](deliverables/立项答辩.pptx)及原PDF为历史草案，硬件、预算和最新截图待内容稳定后单独同步；本轮未改PPT。

主站30组页面/视口、24回放、20交互及3实际导出通过所列检查。网站没有接入真实串口、SQLite服务、设备权限或RF；localStorage仅用于当前演示。文件移动、换浏览器或清除站点数据可能丢失记录，演示记录需导出。材料尚未提交或批准。
