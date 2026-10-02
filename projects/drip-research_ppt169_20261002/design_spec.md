<!-- ppt-master-schema: design-spec/v1 -->
# 滴灌异常监测申报 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 滴灌异常监测申报 |
| Canvas Format | PPT 16:9 1280×720 |
| Page Count | 15 |
| Primary Language | zh-CN |
| Target Audience | 大创立项评委与指导教师 |
| Communication Intent | 先建立具体问题与研究增量，再以模型证据和任务闭环支持评审 |
| Desired Audience Outcome | 认可研究问题的训练价值，并能审查实现条件和验证路线 |
| Core Message / Ask / Action | 争取较高级别创新训练，以三个工作包与实证计划完成监测和可靠通信研究 |
| Delivery Context | 现场答辩，暂按6—8分钟准备，正式时长待通知 |
| Artifact Afterlife | 可编辑PPTX与独立审阅PDF |
| Reading Mode | balanced |
| Content Strategy | 保留事实与边界，按问题—研究—证据—实施组织 |
| Design Style | 自定义研究论证方向 |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — workflow default |
| Custom Animations | disabled — final Stage-2 proactive policy |
| Narration Audio | disabled — workflow default |
| Created Date | 2026-10-02 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 48 px |
| Content Area | 48 48 1184 624 |

## III. Visual Theme

### Theme Style
- **Mode**: custom
- **Mode Behavior**: 先给研究问题与拟研究差异；用三工作包建立闭环，模型与公平对照说明前期基础，反例明确边界，再用实现/验证/进度支持立项决策。
- **Visual style**: custom
- **Visual Style Behavior**: 稳定的页眉、细分隔线与来源脚注建立研究材料的秩序。证据页让坐标与数据占主导，系统页以连接和包含表达真实依赖，结尾保留显著留白；平面颜色表示状态而非装饰。
- **Theme**: 深绿结构线与暖白证据版面
- **Tone**: 有挑战、可核查、专业且克制

### Color Scheme
| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FAF9F5 | 页面底色 |
| Secondary background | #EEF3EF | 语义分区 |
| Primary | #164C45 | 研究主线与主曲线 |
| Accent | #B4512B | 待验证挑战与异常 |
| Secondary accent | #426B91 | 对照曲线 |
| Body text | #20332F | 正文 |
| Secondary text | #556762 | 标注与来源 |
| Divider | #C7D2CB | 分隔线 |
| Grid | #E0E7E2 | 坐标辅助线 |

## IV. Typography System
### Font Plan
| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | 强无衬线、标题字重 | SimHei | Arial | none |
| Body | 清晰无衬线、连续论证 | Microsoft YaHei | Arial | none |
- **Title stack**: SimHei, Arial
- **Body stack**: Microsoft YaHei, Arial
### Font Size Hierarchy
| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 24 |
| Title | 42 |
| Subtitle | 30 |
| Lead | 28 |
| Annotation | 18 |
| Footnote | 16 |
| Display | 60 |

## V. Layout Principles
### Deck-wide Direction
- **Hierarchy direction**: 结论式标题→主要证据/工作对象→条件与来源
- **Composition tendency**: 证据页以大图为主，流程页按依赖展开，概念页用留白强化一句话
- **Cross-page continuity**: 页眉、来源和压力/异常配色一致；系统、曲线与任务载体随语义改变
- **Spacing posture**: variable by page rhythm
- **Spacing anchors**: page margin 48, block gap 28, column gutter 36, corner radius 6, body leading 38

## VI. Icon Usage Specification
- **Primary bundled library**: none
| Icon Path | Suitable Scenarios |
| --- | --- |

## VIII. Image Resource List
| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## IX. Content Outline

#### Slide 01 - 让轮灌监测看得清、报得可靠

- **Audience move**: 未审查本页问题→理解让轮灌监测看得清、报得可靠及其限定
- **Relationships**: 研究目标包含三个工作包与周期
- **Title**: 让轮灌监测看得清、报得可靠
- **Core message**: 前期基础：文献、模型与合成回放；尚无实物数据
- **Content**: 面向棉田轮灌工况的滴灌支管异常监测；与事件触发 LoRa 通信方法研究；2027.03—2028.02｜争取较高级别立项；前期基础：文献、模型与合成回放；尚无实物数据

#### Slide 02 - 正常操作与异常可能同时改变测量

- **Audience move**: 未审查本页问题→理解正常操作与异常可能同时改变测量及其限定
- **Relationships**: 正常与异常对比；检测与通信为先后依赖
- **Title**: 正常操作与异常可能同时改变测量
- **Core message**: 研究问题2：有限通信下，短时告警能否可靠保留？
- **Content**: 正常：支路开关、供压调整、负载改变；异常：可控泄漏、水力受限、切换期短时异常；研究问题1：显著异常能否在正常扰动中被看见？；研究问题2：有限通信下，短时告警能否可靠保留？

#### Slide 03 - 研究增量落在动态工况与可靠告警

- **Audience move**: 未审查本页问题→理解研究增量落在动态工况与可靠告警及其限定
- **Relationships**: 已有研究与本项目拟研究问题对照
- **Title**: 研究增量落在动态工况与可靠告警
- **Core message**: 本项目：连续切换、强基线、事件保留与通信取舍
- **Content**: 2022｜滴灌堵塞综述：间接监测有局限；2026｜HydroNeuro：阀态建模与嵌入式异常感知；2026｜灌溉模拟平台：压力/流量、可控阀门与LoRa；2021/2025｜事件通信：已有节省发送的研究；本项目：连续切换、强基线、事件保留与通信取舍

#### Slide 04 - 三个工作包组成完整研究闭环

- **Audience move**: 未审查本页问题→理解三个工作包组成完整研究闭环及其限定
- **Relationships**: 三个工作包相互依赖，建模/通信进入验证
- **Title**: 三个工作包组成完整研究闭环
- **Core message**: 台架、固件、回放网站、数据包、报告与演示
- **Content**: WP1｜水力建模与异常感知；测点可观测性、参数校核、正常边界、强基线；WP2｜告警约束下的可靠事件通信；滤波/限频/心跳、缓存/ACK/去重、公平对照；WP3｜系统集成与分层实验验证；台架、固件、回放网站、数据包、报告与演示

#### Slide 05 - 先把测点与假设放进同一个模型

- **Audience move**: 未审查本页问题→理解先把测点与假设放进同一个模型及其限定
- **Relationships**: 共同供水分为A/B支路，A测点与节流位置有序
- **Title**: 先把测点与假设放进同一个模型
- **Core message**: 不是水锤/CFD模型；现场参数仍需实测校核
- **Content**: 共同供压与阻力→A/B双支路；测量A支路；压力测点位于A支路上游节流之后；支路负载采用平方根压力关系；动态用一阶响应；共同阻力为零时，B切换不必影响A；不是水锤/CFD模型；现场参数仍需实测校核
- **Mathematical content**: Q=C\sqrt{P}

#### Slide 06 - 模型展示混淆，也为实验提供工况

- **Audience move**: 未审查本页问题→理解模型展示混淆，也为实验提供工况及其限定
- **Relationships**: 同参数下正常与重叠异常压力曲线对照
- **Title**: 模型展示混淆，也为实验提供工况
- **Core message**: 下一步不是报告识别率，而是标定并建立操作标签
- **Content**: 同一组未标定参数下：正常切换 vs 切换期等效泄漏；B支路开启：180—299秒；重叠异常：190—279秒；图为模拟压力；有线小试将检验幅度与测点；下一步不是报告识别率，而是标定并建立操作标签
- **Visualization**: pressure-response 为模拟时间0—600秒下两条压力序列，横轴秒、纵轴kPa，0—140范围
- **Native-ready**: pressure-response=yes
- **Data class**: scenario

#### Slide 07 - 通信优势必须同时接受误差约束

- **Audience move**: 未审查本页问题→理解通信优势必须同时接受误差约束及其限定
- **Relationships**: 相同规则下四策略对照，正常与噪声场景并列
- **Title**: 通信优势必须同时接受误差约束
- **Core message**: 远端误差相对本地模拟滤波量；帧数不等于能耗
- **Content**: 同检测器、同滤波载荷、同事件保留与ACK规则；示例：随机丢包10%＋异常起点15秒链路阻断；较慢周期有竞争力；原始事件在噪声下频繁发送；远端误差相对本地模拟滤波量；帧数不等于能耗
- **Visualization**: normal-tradeoff、noise-tradeoff 为正常/噪声场景四策略的发送帧数与远端压力MAE散点，读 simulation/communication_results/summary.json；假定丢包10%
- **Native-ready**: normal-tradeoff=yes; noise-tradeoff=yes
- **Data class**: scenario

#### Slide 08 - 反例决定边界，而不是被隐藏

- **Audience move**: 未审查本页问题→理解反例决定边界，而不是被隐藏及其限定
- **Relationships**: 失败工况归属于感知与传输边界
- **Title**: 反例决定边界，而不是被隐藏
- **Core message**: 结论：缩小诊断承诺，保留强基线与失败案例
- **Content**: 弱等效泄漏：候选检测0/20命中；正常切换但无阀态：每试次平均1次误报；较大噪声：每试次平均2.7次误报；30%随机丢包＋15秒阻断：短时告警仍可能超时；结论：缩小诊断承诺，保留强基线与失败案例

#### Slide 09 - 由原始采集走向可追踪的系统

- **Audience move**: 未审查本页问题→理解由原始采集走向可追踪的系统及其限定
- **Relationships**: 采集到检测、缓存、发送、接收与回放为有序链接
- **Title**: 由原始采集走向可追踪的系统
- **Core message**: 先有线记录，再无线，再现场适应性
- **Content**: 压力/流量→微控制器→本地检测与事件缓存；LoRa发送→接收/ACK→日志与回放网站；数据字段：启动会话、序号、时间、测量、事件ID；恢复机制：超时、去重、掉电恢复、缓存溢出记录；先有线记录，再无线，再现场适应性

#### Slide 10 - 分层验证把方法、硬件与场景分开

- **Audience move**: 未审查本页问题→理解分层验证把方法、硬件与场景分开及其限定
- **Relationships**: 标定先于独立批次，方法冻结先于真实通信评价
- **Title**: 分层验证把方法、硬件与场景分开
- **Core message**: 核心条件拟≥3次独立重复；连续台架记录拟≥8h
- **Content**: 第1层｜标定与台架：五类工况、独立操作标签；第2层｜独立批次：误报/漏检、强基线与参数消融；第3层｜真实无线：帧/字节、两段延迟、整机能量；现场有许可才采集；无故障标签只验证正常运行；核心条件拟≥3次独立重复；连续台架记录拟≥8h

#### Slide 11 - 一年有阶段门槛，2000元先启动

- **Audience move**: 未审查本页问题→理解一年有阶段门槛，2000元先启动及其限定
- **Relationships**: 实施月份按时间顺序；启动预算依赖借用仪器
- **Title**: 一年有阶段门槛，2000元先启动
- **Core message**: 启动2000元；需借参考仪器，论文费用另行核查
- **Content**: 2027.03—04｜标定、有线采集、可观测性；2027.05—08｜独立台架、可靠LoRa、整机测量；2027.09—10｜跨条件验证、论文成稿与投稿；2027.11—2028.02｜补实验、原型/报告/结项；启动2000元；需借参考仪器，论文费用另行核查

#### Slide 12 - 用系统成果结项，用研究证据支撑论文

- **Audience move**: 未审查本页问题→理解用系统成果结项，用研究证据支撑论文及其限定
- **Relationships**: 系统/数据/方法/报告共同构成预期成果
- **Title**: 用系统成果结项，用研究证据支撑论文
- **Core message**: 已有成果据实陈述；研究目标以实验兑现
- **Content**: 1节点＋1接收端＋1套双支路台架；标定与标签数据＋检测/通信对照＋复现程序；回放软件＋调研/研究报告＋过程记录＋论文稿；争取国家级：靠问题、增量、证据与实施条件；已有成果据实陈述；研究目标以实验兑现

#### Slide 13 - 备用｜单测点不等于故障原因诊断

- **Audience move**: 未审查本页问题→理解备用｜单测点不等于故障原因诊断及其限定
- **Relationships**: 两个不同故障原因可映射到相同观测
- **Title**: 备用｜单测点不等于故障原因诊断
- **Core message**: 可行性成立的条件：信号可观测、可标定、可重复
- **Content**: 上游节流和供压下降可产生相同测点压力/流量；一个测点可以提示异常，却未必判定原因；共同阻力为零时，相邻支路切换可不影响测点；模型必须校核：供压、管路阻力、负载与测点；可行性成立的条件：信号可观测、可标定、可重复

#### Slide 14 - 备用｜三个阶段有不同完成标准

- **Audience move**: 未审查本页问题→理解备用｜三个阶段有不同完成标准及其限定
- **Relationships**: 申报、大创与论文按阶段递进且标准不同
- **Title**: 备用｜三个阶段有不同完成标准
- **Core message**: 若无方法增量，调整为测量/部署边界研究
- **Content**: 申报阶段｜模型论证、研究任务、实验设计与资源计划；大创结项｜系统、独立实测、方法对照、报告与过程；论文阶段｜一个主问题、真实数据、强基线、可复现贡献；主问题优先：可靠告警约束下的通信取舍；若无方法增量，调整为测量/部署边界研究

#### Slide 15 - 备用｜来源与证据索引

- **Audience move**: 未审查本页问题→理解备用｜来源与证据索引及其限定
- **Relationships**: 制度、文献与程序分别支持流程、依据和模型证据
- **Title**: 备用｜来源与证据索引
- **Core message**: 本地证据：程序、JSON/CSV、审查报告与交互网站
- **Content**: 塔大实施细则：jwc.taru.edu.cn/info/1035/3872.htm；2026申报通知：jwc.taru.edu.cn/info/1052/4329.htm；堵塞综述｜10.1016/j.agwat.2022.107873；HydroNeuro｜10.3390/s26103010；灌溉模拟平台｜10.3390/land15030464；事件通信｜10.3390/s21165541；10.1016/j.ifacol.2025.11.761；本地证据：程序、JSON/CSV、审查报告与交互网站

## X. Speaker Notes Requirements
- **Generation**: enabled
- **Filename**: match each SVG filename under notes/
- **Content**: 以最终SVG可见证据组织论证，保留模拟/计划状态与关键限定，不声称已做实物实验
- **Total duration**: 正文约6—8分钟；备用页按追问使用
- **Notes style**: 自然、准确的中文科研申报表达
- **Presentation purpose**: 支持评委判断研究问题、任务体系与可实施性
