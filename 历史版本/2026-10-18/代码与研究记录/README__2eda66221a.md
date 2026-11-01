# scripts_历史 — 已归档死亡脚本说明

归档时间：2026-10-18（P4-5 图库整改主体 17 个；P4-6 引用复查追加 7 个，合计 24 个）。
归档判定准则（两条同时满足才归档）：
1. **产出全灭**——脚本输出的图/校验对象均已在 P4-1/P4-2 图库整改中删除，或其输入文件已被删除导致脚本必然报错；
2. **无存活引用**——scripts/、simulation/、application/、docs/、README.md 中无任何存活文件 import、调用或以复现命令形式引用它
   （`.workbuddy/memory/` 历史日志与 `simulation/*/figure_sources.json` 等历史登记记录不计入引用，它们本就是档案）。

**归档不是删除**：所有脚本可用 `git mv` 随时回到 scripts/。但复活前必须先读死亡证据——
带「必崩/必错」判定的脚本原样运行只会产出错误结果。

现行活脚本的复现链以 README「修改与复现」节与各 docs 验收记录为准；
图形三通道校验入口为 `scripts/verify_figure_layout.mjs`、`scripts/verify_html_figs.mjs`、`scripts/verify_quality_visuals.mjs`。

## 归档清单与死亡证据

| 脚本 | 产出 / 校验对象 | 死亡证据 |
|---|---|---|
| draw_protocol_figs.py | application/figures/frame_layout、judging_chain（SVG+PNG） | 两图的 SVG 孪生件已于 P4-1 裁决退役（现行为 draw_impl_figs.py 的 PNG 管道）；输出全删 |
| draw_system_overview_horizontal.py | deliverables/系统总体结构_横版曲线_单色学术版.svg | 落选横版变体，4 文件已于 P4-1 删除；现行图为此脚本的纵版继任者 draw_system_overview_monochrome.py |
| draw_system_overview_html.py | deliverables/系统总体结构_横版曲线.html | 同上，HTML 变体已删 |
| redesign_document_figures.py | application/figures/early_diagnosis.svg/.png | 旧版诊断流程图已删（现行口径以 threshold_separation / detection_boundary 为准）；仅被 build_portal.py 清单 paths 与历史文本提及，无 import/调用 |
| build_application_design_figures.py | application/figures/{architecture,water_layout,hardware,hydraulic_model,acquisition,diagnosis,protocol,experiment}.svg | 申报版设计图全家已删；三个导入方（build_application_visuals / render_bench_plate / render_collection_review）全部死亡，无存活导入 |
| build_application_visuals.py | application/figures/{system_scope,dual_pressure_layout,pressure_frontend,diagnosis_flow,protocol_sequence}.svg | 5 图全删（旧架构图，被「系统总体结构_单色学术版」取代） |
| render_bench_plate.py | application/figures/bench_plate 标注图 | 输入 application/figures/bench_isometric.png 已删，脚本首行 hash 断言必失败 |
| render_collection_review.py | application/figures/collection_review/ 四板图 | 输入 application/models/collection_review/ 目录已不存在，脚本首行读 JSON 必失败；存活的 collection_overview.svg 为冻结交付物（plate_provenance.json 保留其来源记录） |
| prepare_method_application_figures.py | application/figures/method_revision/ | 整目录已删 |
| prepare_submission_upgrade_figures.py | application/figures/submission_upgrade/ | 整目录已删（其输入 equation_revision/ 亦已删） |
| prepare_usability_figures.py | application/figures/usability_revision/ | 整目录已删 |
| prepare_equation_figure_revision.py | application/figures/equation_revision/ | 整目录已删 |
| polish_application_figures.py | application/figures/print_polish/ | 整目录已删，且其输入 submission_upgrade/ 亦已删 |
| draw_event_system_diagrams.py | application/figures/submission_upgrade/ 事件序列图 | 输出目录已删；唯一提及处为 simulation/submission_upgrade/figure_sources.json 历史登记（只登记已删图，属档案） |
| build_compact_water_figure.py | application/figures/compact_layout/water_layout.svg | 输出目录已删（现行水路图为 quality_review/water_layout） |
| verify_compact_water_figure.mjs | 校验 application/figures/compact_layout/ | 校验对象已删；其检查逻辑已由 verify_figure_layout.mjs 全库继承（该文件头注已改述为 Archived 状态） |
| finalize_compact_layout.py | 冻结 compact_layout 发布（断言 application/figures/compact_layout/water_layout.png 哈希） | 断言对象已删，脚本必失败；属紧凑排版集群的收尾脚本，随图形部分一并归档 |
| author_visual_redesign.py | application/figures/svg_output/ 28 页 SVG + field_concept.svg | 输出全家已于 P4-1 删除（PPT 图形源，旧版概念图）；P4-5 漏网，P4-6 引用复查补归；全库无存活引用 |
| sync_application_delivery.py | 一次性迁移：把 README「图形/PDF脚本依赖」段替换为新文案 | 一次性迁移脚本（任务早已执行完毕）；输入 deliverables/大创申报书_模板审阅版.pdf 已不存在，必报错；零调用 |
| build_bench_viewer.py | deliverables/台架三维结构交互模型.html 与 _收集优化候选版.html（OCCT 场景 + three.js 离线查看器） | 两个产物均已删（主版 39de404、候选版 P4-1）；现行三维交付物为 build_bench_workspace.py 构建的 清水试验台架_V1.2.html，技术路线总纲仅引后者；零活调用（仅 build_portal 清单登记与 update_quality_release_content 第 120 行陈旧文本提及） |
| capture_bench_views.mjs | 台架三维结构交互模型*.html 的 Edge 截图（bench_* 五视角 PNG） | 截取对象两个 HTML 均已删，脚本无输入可拍；输出 PNG 亦已于 P4-1 删除；零活调用 |
| verify_quality_model_viewer.mjs | 校验 台架三维结构交互模型_收集优化候选版.html 的字节哈希 | 第 17 行硬编码被删文件、第 33 行 readFile 必崩；仅剩 simulation/quality_review/model_viewer_checks.json 等历史校验记录提及；零活调用 |
| build_print_polish_application.py | deliverables/大创申报书_版式修订稿.docx | 产出 docx 已于 39de404 删除；输入 application/figures/print_polish/ 整目录已于 P4-1 删除；零调用 |
| build_submission_upgrade.py | deliverables/大创申报书_系统方案完善稿.docx | 产出 docx 已于 39de404 删除；关联 submission_upgrade 图目录已于 P4-1 删除；零调用 |

## 曾经误归档、已撤回的两个脚本（P4-6 复查翻案，记录在案）

P4-6 初版曾把 `build_portal.py` 与 `verify_staged_evidence.py` 一并归档，全库引用复查发现
**活调用**后当日撤回（`git mv` 回 scripts/）。翻案证据：

- `scripts/build_desktop.py` 第 41 行 subprocess 调用 `build_portal.py --operations-only`（桌面版 V1.3 构建链，现行交付物）；
- `docs/项目实施详细步骤与技术路线总纲.md` 第 404 行把 `python scripts/build_portal.py --operations-only`
  列为「运行平台重建」现行命令；
- `build_portal.py` 第 71 行把 `scripts/verify_staged_evidence.py` 登记进证据清单 paths——
  若该脚本不在 scripts/，默认模式永远修不好。

教训：判死必须查**调用方**（subprocess/文档命令表），不能只看脚本自身的输出文件在不在。

## 补充清查（P4-6 第二轮）：收集优化候选版 / 旧申报稿退役簇

引用复查又牵出一簇「产物已删、零活调用」的退役脚本（build_bench_viewer、capture_bench_views、
verify_quality_model_viewer、build_print_polish_application、build_submission_upgrade），逐个证据见上表，
已并入归档。注意 `scripts/update_quality_release_content.py` 第 120 行的发布流文本仍写着
「三维页面运行 scripts/build_bench_viewer.py --collection-review」——该文本是 2026-10-05 轮次的
历史描述，两个脚本均已归档，**下一轮发布前须同步改写该段**（现行三维页面为
`deliverables/清水试验台架_V1.2.html`，构建链为 `scripts/build_bench_workspace.py`）。

## 发布流水线现状（P4-6 复查结论，供下一轮发布前修复）

质量发布流水线（研究与答辩门户）当前处于**轮次之间**，六条活脚本全部保留在 scripts/：

| 脚本 | 状态 |
|---|---|
| build_portal.py | **活，双模式**：`--operations-only` 自洽可用（web_data.json 与模板资产俱全，桌面版构建链在用）；**默认模式已崩**——第 92 行对清单 paths 逐个 read_bytes，40 条硬编码路径已不存在（docs 移Archive、脚本归档、申报稿改名），运行即 FileNotFoundError |
| verify_staged_evidence.py | 活但休眠：第 5 行硬读 证据清单.json（P2 提交 39de404 已删），当前必崩；无独立调用方，属全量发布链一环 |
| update_quality_release_content.py | 活：产出 deliverables/分项验收进度.json（2026-10-05）在 |
| finalize_quality_release.py | 活：产出 application/quality_release/ 冻结材料与 deliverables/格式优化与实施项目书验收记录.json 在 |
| package_submission.py | 活但被阻塞：需 证据清单.json 才能打包申报材料与证据包.zip |
| verify_quality_release.py | 活但当前必失败：读 证据清单.json 与 申报材料与证据包.zip（均不存在） |

**下一轮发布（预计 P5 申报书装配后）的修复顺序**：
① 逐条核对 build_portal.py 第 47—90 行 paths（现存 102 条 / 缺失 43 条，逐条清单见
`docs/图库整改验收记录_P4_20261018.md` §六），把缺失条目改指现行文件或删除；② 默认模式重跑生成
index.html 与 证据清单.json；③ verify_staged_evidence.py 核对 git 字节；④ package_submission.py 打包；
⑤ verify_quality_release.py 发布前审计。
注意：`--operations-only` 模式不碰清单，运行平台日常重建不受上述破损影响。
另：`update_quality_release_content.py` 第 120 行文本中的 build_bench_viewer.py --collection-review
已随该脚本退役，改写时一并处理（见上「补充清查」节）。

## 未归档的相邻脚本（有意保留在 scripts/）

- 紧凑排版集群的文档级脚本（compact_application_layout.py、export_compact_application.ps1、verify_compact_application.py、
  measure_application_page_gaps.py）：操作对象是 application/compact_layout_revision/ 与 simulation/compact_layout_review/
  （两者均存活），属文档排版集群而非图形集群。

## 历史登记记录留存说明

simulation/submission_upgrade/figure_sources.json、application/figures/collection_review/plate_provenance.json 等记录
虽只登记已删图，但作为「删了什么、由谁生成」的档案保留，供溯源核对；它们不是活链路，任何校验器都不应再把它们当作输入。
