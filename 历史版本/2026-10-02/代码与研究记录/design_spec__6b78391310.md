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
| Core Message / Ask / Action | 争取较高级别创新训练，以四个工作包与实证计划完成支管有限诊断与可靠告警系统研究 |
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
- **Mode Behavior**: 先给研究问题与拟研究差异；用四工作包建立闭环，模型与公平对照说明前期基础，反例明确边界，再用实现/验证/进度支持立项决策。
- **Visual style**: custom
- **Visual Style Behavior**: 深色场景及架构页与浅色证据页交替；场景以滴灌田块概念模型为主体，架构用分层关系，管理用真实合成回放界面，证据页标出首次提示和失效参照。避免全文字横线页，源注缩为一行，保留模拟和设计状态。
- **Theme**: 农业科技场景与清晰研究证据
- **Tone**: 有挑战、可核查、专业且克制

### Color Scheme
| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FAF9F5 | 证据页底色；封面采用Primary深绿场 |
| Secondary background | #EEF3EF | 语义分区 |
| Primary | #164C45 | 研究主线与主曲线 |
| Accent | #B4512B | 待验证挑战与异常 |
| Secondary accent | #426B91 | 对照曲线 |
| Body text | #20332F | 正文 |
| Secondary text | #556762 | 标注与来源 |
| Divider | #C7D2CB | 分隔线 |
| Grid | #E0E7E2 | 坐标辅助线 |
| Dark surface | #092E2B | 场景和架构主体 |
| Signal | #78DFC5 | 深底感知与通信 |
| Warm highlight | #F3C77B | 深底研究重点 |

## IV. Typography System
### Font Plan
| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | 强无衬线、标题字重 | Microsoft YaHei | Arial | none |
| Body | 清晰无衬线、连续论证 | Microsoft YaHei | Arial | none |
- **Title stack**: Microsoft YaHei, Arial
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
| Display | 64 |
| Hero | 72 |
| Diagram label | 20 |

## V. Layout Principles
### Deck-wide Direction
- **Hierarchy direction**: 结论式标题→主要证据/工作对象→条件与来源
- **Composition tendency**: 证据页以大图为主，流程页按依赖展开，概念页用留白强化一句话
- **Cross-page continuity**: 顶部场景/系统/证据/实施导航统一；封面深绿，证据页暖白；来源及故障配色一致；系统、曲线与任务载体随语义改变
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

#### Slide 01 - 南疆滴灌支管早期故障诊断

- **Composition**: 标题与田块/节点/接收端概念模型左右展开

- **Audience move**: 理解南疆滴灌支管早期故障诊断及其条件
- **Relationships**: 感知诊断通信管理为闭环依赖
- **Title**: 南疆滴灌支管早期故障诊断
- **Core message**: 前期：文献、未标定模型、合成回放；无实物数据
- **Content**: 基于 LoRa 的南疆滴灌支管道早期故障诊断；物联网原型系统；2027.03—2028.02｜创新训练申报方案；前期：文献、未标定模型、合成回放；无实物数据

#### Slide 02 - 看见变化，才能判断故障

- **Composition**: 滴灌支管场景与正常/泄漏/受限三个状态映射

- **Audience move**: 理解看见变化，才能判断故障及其条件
- **Relationships**: 正常与两类故障对比
- **Title**: 看见变化，才能判断故障
- **Core message**: 交付：有限诊断、可靠告警、管理确认及回放
- **Content**: 管理需求：哪里异常、为何检查、什么时候发现；主对象：下游等效泄漏、支管等效受限；正常供压及切换、未知状态和漂移作为挑战；交付：有限诊断、可靠告警、管理确认及回放

#### Slide 03 - 研究增量，落在实验里

- **Composition**: 三条已有工作到候选增量的对应关系

- **Audience move**: 理解研究增量，落在实验里及其条件
- **Relationships**: 已有研究与候选增量对照
- **Title**: 研究增量，落在实验里
- **Core message**: 拟增量：测点/工况的作用、早期边界、可靠取舍
- **Content**: 堵塞综述：压力/流量间接检测不一定见最初堵塞；HydroNeuro：阀态建模及嵌入式感知已有研究；LoRa灌溉平台、事件通信已有先例；拟增量：测点/工况的作用、早期边界、可靠取舍

#### Slide 04 - 一个系统，四个工作包

- **Composition**: 感知—诊断—可靠通信—管理分层并列，研究工作归属明确

- **Audience move**: 理解一个系统，四个工作包及其条件
- **Relationships**: 四工作包按依据诊断传输系统递进
- **Title**: 一个系统，四个工作包
- **Core message**: WP4 系统与验证｜节点、管理软件、台架与证据归档
- **Content**: WP1 测量与建模｜P0/P1/Q、参考标定与差压误差；WP2 诊断与边界｜渐进故障、状态、强基线与提前量；WP3 可靠告警｜周期/事件公平对照、ACK与整机测量；WP4 系统与验证｜节点、管理软件、台架与证据归档

#### Slide 05 - 测点包围目标区段

- **Composition**: 上侧测点水路，下侧测点角色与两个特征；原生公式

- **Audience move**: 理解测点包围目标区段及其条件
- **Relationships**: P0在受限前P1在受限后Q包含全部下游流量
- **Title**: 测点包围目标区段
- **Core message**: 未知负载及传感器漂移仍可能混淆；需标定
- **Content**: P0在入口；P1在受限下游；Q含下游负载与泄漏；K=Q/√P1；R估计=(P0-P1)/Q²；共同供压变化与局部受限有望分开；未知负载及传感器漂移仍可能混淆；需标定
- **Mathematical content**: Q=C\sqrt{P_1}

#### Slide 06 - 早期，必须早于失效判据

- **Composition**: 主图标出首次提示/失效，右栏给示例提前量；两类型区分

- **Audience move**: 理解早期，必须早于失效判据及其条件
- **Relationships**: 两渐进故障曲线与失效参照对照
- **Title**: 早期，必须早于失效判据
- **Core message**: 需分别测故障→本地提示→远端接收
- **Content**: 渐进故障从360s起、180s增长；图为合成流量偏离；15%偏离为演示失效判据，非农学或行业标准；早期：正确提示在判据前，且没有前期误报；需分别测故障→本地提示→远端接收
- **Visualization**: pressure-response承载两类渐进故障相对健康流量偏离，横轴330—600秒，纵轴0—30%；数据来自diagnosis_results/summary.json的低噪声真值。15%是演示失效判据，非农业标准。
- **Native-ready**: pressure-response=yes
- **Data class**: scenario

#### Slide 07 - 少发帧，也要保住证据

- **Composition**: 两个匹配坐标图，底部共享解释；语义图例和单位完整

- **Audience move**: 理解少发帧，也要保住证据及其条件
- **Relationships**: 四通信策略在正常和噪声场景对照
- **Title**: 少发帧，也要保住证据
- **Core message**: 新诊断与通信尚未合并成经验证的端到端系统
- **Content**: 1920次旧单压力模型通信回放；非射频实测；同检测、载荷、缓存和ACK；慢周期作强基线；比较发送、信息误差和告警及时性；新诊断与通信尚未合并成经验证的端到端系统
- **Visualization**: normal-tradeoff和noise-tradeoff为旧单压力通信四策略帧数与MAE；噪声/正常并列，10%假定丢包。
- **Native-ready**: normal-tradeoff=yes; noise-tradeoff=yes
- **Data class**: scenario

#### Slide 08 - 测点增加，边界仍然存在

- **Composition**: 12/20重点与两条失效证据、成立条件并排

- **Audience move**: 理解测点增加，边界仍然存在及其条件
- **Relationships**: 噪声漂移及负载挑战界定方法边界
- **Title**: 测点增加，边界仍然存在
- **Core message**: 单故障、理想同步、平方律；不是实物识别率
- **Content**: 双压力模型480试次：6场景×4噪声×20种子；σ10kPa：两类正确提前发现各12/20；压力漂移与未知正常负载可导致误报；单故障、理想同步、平方律；不是实物识别率

#### Slide 09 - 把诊断结果交给使用者

- **Composition**: 合成回放界面为主体，右栏设备/趋势/事件/回放功能

- **Audience move**: 理解把诊断结果交给使用者及其条件
- **Relationships**: 感知诊断通信管理确认依次链接
- **Title**: 把诊断结果交给使用者
- **Core message**: 当前网页为设计与合成回放，未接在线设备
- **Content**: 采集质量→本地有限诊断→可靠LoRa→管理确认；设备档案、支管示意、趋势、事件、回放、导出；异常待检查、数据无效、节点离线分别显示；当前网页为设计与合成回放，未接在线设备

#### Slide 10 - 用独立实验兑现研究目标

- **Composition**: 54次独立操作的实验矩阵，三个验证层级及8h条件

- **Audience move**: 理解用独立实验兑现研究目标及其条件
- **Relationships**: 标定先于故障网格方法先于无线评价
- **Title**: 用独立实验兑现研究目标
- **Core message**: 真实LoRa、整机能量；拟8h连续台架与恢复检查
- **Content**: 参考标定：差压误差小于目标变化才进入方法试验；2类型×3供压×3程度×3独立操作：拟54次；正常与切换另做；按日/批次留出，强基线与消融；真实LoRa、整机能量；拟8h连续台架与恢复检查

#### Slide 11 - 一年推进，按条件过关

- **Composition**: 时间门槛横向推进，下侧预算分类与借用条件

- **Audience move**: 理解一年推进，按条件过关及其条件
- **Relationships**: 时间顺序与预算对应实现条件
- **Title**: 一年推进，按条件过关
- **Core message**: 2000元暂估；已有电脑并借参考仪器为前提
- **Content**: 2027.03—04 标定与有线；05—06主要水力实验；07—08可靠LoRa/Web；09—10独立验证与论文稿；11—2028.02补实验、系统、报告及结项；2000元暂估；已有电脑并借参考仪器为前提

#### Slide 12 - 交付原型，也交付证据

- **Composition**: 一个原型与一组可复现证据作为两类成果

- **Audience move**: 理解交付原型，也交付证据及其条件
- **Relationships**: 系统和研究证据共同构成成果
- **Title**: 交付原型，也交付证据
- **Core message**: 争取较高级别；级别及论文结果不作保证
- **Content**: 1个双压力流量节点＋1接收端＋双支路台架＋Web；标定、标签、对照、提前量、失败案例及复现程序；调研/结题/过程报告＋技术说明＋论文稿；争取较高级别；级别及论文结果不作保证

#### Slide 13 - 相同观测，可能有不同原因

- **Composition**: 两个原因汇入同一观测，条件决定输出

- **Audience move**: 理解相同观测，可能有不同原因及其条件
- **Relationships**: 单点双点歧义对照
- **Title**: 相同观测，可能有不同原因
- **Core message**: 输出范围：有限模式 / 待检查 / 数据无效
- **Content**: 旧单点：上游受限与供压下降可有相同P/Q；新增P0有条件改善该歧义，不能定位单滴头；双点仍分不清未知正常负载与等效泄漏；输出范围：有限模式 / 待检查 / 数据无效

#### Slide 14 - 申报、结项、论文分层完成

- **Composition**: 三个阶段各自列出材料/系统/论文完成要求

- **Audience move**: 理解申报、结项、论文分层完成及其条件
- **Relationships**: 三个阶段递进且完成标准不同
- **Title**: 申报、结项、论文分层完成
- **Core message**: 优先渐进诊断边界；可靠通信作为候选备选
- **Content**: 申报：九节模板、四工作包、证据和资源计划；结项：实物系统、独立实测、对照、报告及过程；论文：从项目选一个真实可复现的主贡献；优先渐进诊断边界；可靠通信作为候选备选

#### Slide 15 - 来源与可复现记录

- **Composition**: 文献DOI与程序/协议按来源分组

- **Audience move**: 理解来源与可复现记录及其条件
- **Relationships**: 来源分别支撑制度研究与合成证据
- **Title**: 来源与可复现记录
- **Core message**: 案例级别由用户提供；性能声明未全部独立核实
- **Content**: 塔大实施细则：jwc.taru.edu.cn/info/1035/3872.htm；堵塞综述：10.1016/j.agwat.2022.107873；HydroNeuro：10.3390/s26103010；灌溉平台：10.3390/land15030464；事件通信：10.3390/s21165541；IFAC 2025；新增：diagnosis_feasibility.py / DIAGNOSIS.md；案例级别由用户提供；性能声明未全部独立核实

## X. Speaker Notes Requirements
- **Generation**: enabled
- **Filename**: match each SVG filename under notes/
- **Content**: 以最终SVG可见证据组织论证，保留模拟/计划状态与关键限定，不声称已做实物实验
- **Total duration**: 正文约6—8分钟；备用页按追问使用
- **Notes style**: 自然、准确的中文科研申报表达
- **Presentation purpose**: 支持评委判断研究问题、任务体系与可实施性
