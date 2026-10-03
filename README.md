# 滴智卫 · DiZhiWei

申报题目：**基于 LoRa 的南疆滴灌支管道早期故障诊断物联网原型系统**。

2026年10月4日版本。根据老师建议、学校模板及两份案例，更新为四个工作包，完成学校模板填写稿、独立项目范围文件、答辩材料和离线交互网站。当前基础是文献、未标定模型与合成回放；尚无硬件、真实无线、功耗或田间实验。题目、工作数量和材料不能保证立项级别。

## 最新材料

- [先打开：研究与申报网站](deliverables/index.html)，下载完整仓库后用浏览器打开，保留目录结构。
- [学校模板填写稿 Word](deliverables/大创申报书_模板填写稿.docx) / [原生审阅 PDF](deliverables/大创申报书_模板审阅版.pdf)：22页，原封面、九节正文、9幅图、4张可编辑数据表、17条完整参考文献及审批栏；图文按系统、测量、诊断、通信和验证展开；包括三维布局、电气原理、统计图与网站局部截图，仅保留1张核心诊断流程。
- [项目范围与执行 PDF](deliverables/项目书审阅版.pdf) / [可编辑三阶段方案](docs/项目范围与三阶段执行方案.md)：5页，明确申报、结项、论文的不同标准。
- [可编辑答辩 PPTX](deliverables/立项答辩.pptx) / [原生审阅 PDF](deliverables/立项答辩审阅版.pdf)：视觉修订草案，12页主讲、3页备用，附15页讲稿；最新硬件及预算尚待同步，后续再完成。
- [国内硬件选型与淘宝入口](docs/国内硬件选型与可行性核对.md) / [国家级案例写法拆解](docs/国家级案例写法拆解与申报书改写.md)。
- [案例对照与老师建议分析](docs/案例对照与老师建议分析.md) / [申报九节正文源稿](application/正式模板正文.md)。
- [打包材料与源文件](deliverables/申报材料与证据包.zip) / [使用说明](deliverables/使用说明.md)。
- [交付检查及范围](deliverables/交付检查.json) / [证据哈希清单](deliverables/证据清单.json)。

- [参考文献核验与正文对应](docs/参考文献核验与正文对应.md)：17篇期刊论文，中文11篇（64.7%）、英文6篇；原英文全部保留，正文逐项引用。

[本轮图示取舍与论文依据](docs/论文图示借鉴与本轮结构调整.md) · [三维布置OBJ](application/models/bench_layout.obj) · [本轮验收记录](docs/本轮申报书验收记录.md)

## 当前范围

实施期2027年3月至2028年2月。必做配置为一个P0/P1/Q双压力流量节点、一个LoRa接收端、一套可重复双支路清水台架及本地Web管理软件。约2000元以借用参考仪器及可调连续水源为前提，两压力传感器待询价，是启动额度估计，未获得报价或资助；团队、导师支持、场地与仪器仍待落实。

四个工作包分别为测量与建模、渐进故障诊断与边界、LoRa可靠告警、系统集成与分层验证。主要研究下游等效泄漏与支管等效受限，评价供压、切换、漂移及未知负载下的误报、漏检和早期提前量。位置只到所监测支管/区段；节流不证明真实滴头堵塞。自动阀控、多节点、太阳能和云端按资源扩展。

论文优先提炼测点与工况信息对渐进故障辨识的作用，可靠通信为备选。需要独立实测、强基线和消融；增加测点或采用LoRa本身不构成创新。参考今年截图，省级第一完成人4分加符合条件的6分论文可达10分；未来规则、认定和成果时间需学院核实，不能保证取得分数。

## 模型与可复现证据

- [双压力诊断协议](simulation/DIAGNOSIS.md)：6场景×4噪声×20种子，共480次合成试验。压力漂移会误报，未知正常负载与等效泄漏可具有相同观测。15%健康流量偏离只是演示失效参照。
- [公平通信回放协议](simulation/COMMUNICATION.md)：8场景×3丢包条件×20种子×4策略，共1920次回放；四策略同检测、滤波载荷与告警确认，发送帧不等于整机能量。
- [历史单压力模型审查](docs/对抗性检验报告.md)：反例与960条方法结果，属于旧配置基础。

诊断与通信模型尚未合并成经验证的端到端系统。重复种子主要改变假定噪声与通道，不代表独立物理实验。历史方向文件已标记，当前设备、任务、预算以最新范围文件为准。

## 修改与复现

申报文字源为 `application/正式模板正文.md`，学校原模板为根目录DOC。先运行 `python scripts/prepare_application_payload.py`，再在PowerShell 7运行 `./scripts/fill_application_template.ps1`，使用本机WPS原生填写和导出。真实行政资料、意见与签字需要本人及导师补齐。

诊断复跑：`python simulation/diagnosis_feasibility.py`；验证：`python scripts/validate_diagnosis_evidence.py`。通信复跑：`python simulation/communication_feasibility.py`；协议及图表验证：`python scripts/validate_new_evidence.py`。参考文献检查：`python scripts/validate_application_references.py`。网站重建：`python scripts/build_portal.py`；交付检查：`python scripts/qa_deliverables.py`。

诊断数据复跑后，应再运行 `scripts/redesign_document_figures.py` 恢复申报版图形；设计图运行 `scripts/build_application_visuals.py`，硬件核对运行 `simulation/hardware_design_check.py`。PPT新图形源为 `scripts/author_visual_redesign.py`。`rewrite_application_argument.py`、`redesign_visual_plan.py`及`redesign_portal_surface.py`是一次性迁移脚本，不重复覆盖当前材料。

图形/PDF脚本依赖NumPy、Matplotlib、ReportLab、PyMuPDF、Pillow；浏览器检查使用Edge，原生审阅导出使用本机WPS。PPT可编辑源码保存在 `projects/drip-research_ppt169_20261002`，生产工作流依赖本机ppt-master技能。`prepare_materials.py`和两个`revise_*.py`是历史/一次性迁移脚本，不要重复运行来覆盖当前内容。

外部案例原件和个人信息未纳入仓库；案例立项级别来自用户说明。材料尚未提交或批准。
