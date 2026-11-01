# 当前台架参数的建模与诊断证据包

2026年10月4日，A06—A07候选。所有数据来自未标定模型，无实物、田间、射频或功耗数据。正式论证、图注和限制见[分项报告](../../docs/仿真建模与诊断证据分项验收.md)。原`diagnosis_results`为历史参数结果，保留并不覆盖；网站当前也仍使用历史回放。

## 文件与数据口径

| 文件 | 内容 |
|---|---|
| `protocol.json` | 参数、采样、规则、早期资格和挑战；改动后重算所有受影响数据 |
| `raw_trials.npz` | 480个场景/噪声试次的原始P0/P1/Q、6场景真值、同工况健康Q和程度 |
| `method_results.csv` | 每个试次的两条规则，共960行；失败、首次正确、独立参照和有效提前量 |
| `summary.json` | 48组统计、24个种子10300示例、界限/挑战汇总与源文件哈希 |
| `error_intervals.csv` | 288个静态工况的目标特征界限、阈值与健康误触发余量 |
| `timing_challenges.csv` | 8个正常切换/供压阶跃及P1延迟挑战 |
| `model_mismatch_challenges.csv` | 8个正常负载假设与供压工况×两条规则，共16行 |
| `legacy_audit.json` | 旧480行复现与三个历史源文件哈希；不是物理验证 |
| `source_checks.json` | 四个官方规格/论文入口和本轮实际核对范围 |
| `validation.json` | 不导入生成器的独立算术和回放检查及输入哈希 |
| `figure_layout_checks.json` | Edge实际SVG文字位置、越界/重叠与图片哈希 |

NPZ键：`observed`为(480,601,3)，通道依次P0[kPa]、P1[kPa]、Q_A[L/min]；`truth_by_kind`为(6,601,3)，`healthy_q_by_kind`与`severity_by_kind`为(6,601)。`kind_index`、`pressure_sigma`、`seeds`与`trial_ids`逐试次对齐，`t`为0—600s。场景顺序以协议`random_trials.kinds`为准。

读取示例：

```python
import numpy as np
with np.load('simulation/diagnosis_review/raw_trials.npz', allow_pickle=False) as data:
    index = np.flatnonzero(data['trial_ids'] == 'leak|0.3|10300')[0]
    t = data['t']
    p0, p1, q = data['observed'][index].T
```

CSV空字段表示没有相应时刻/结果，不是零。`early_valid`为严格有效早期资格；`valid_lead_s`只在其为True时有值。`first_correct_s`是故障后首次正确模式确认，存在该值不等于无前期误报。`critical_s`为真值总流量偏离15%的独立演示参照，与在线阈值分开。`severity_at_first_correct`是比例，绘图转为百分数。R及R阈值/余量单位为kPa/(L/min)²；K单位为(L/min)/√kPa。

`false_onsets`计持续非正常模式的确认起点，包含返回正常后的重触发和模式变化后的持续新确认；不是实际无线发报数。故障试次`false_exposure_seconds`为故障前230s，无故障对照为470s；不能直接混合两者分母。`invalid_samples`为监测区间无效的采样点数，相邻点不当独立操作。

失败分类按固定优先级互斥：`valid_early`、`prior_false_alarm`、`wrong_first_pattern`、`no_correct_detection`、`reference_not_reached`、`late_detection`；对照为`no_fault_control`。先错后对和已有误报不能因最终出现正确模式而改成成功。

20个基础随机序列在6场景×4压力σ以及两规则之间复用；每组20种子，方法比较为配对。480记录不是480独立随机物理实验，各σ也不是独立噪声样本集。Wilson区间仅针对每组20种子在该假定生成器内的有效早期比例。

界限表中的`intervals_disjoint`、`fault_feature_guarantees_fixed_threshold`和`joint_stationary_threshold_guarantee`分别表示目标特征区间分离、故障侧必触发、触发且健康侧不误触发。只针对一个目标特征的静态箱式界限，不保证联合分类和动态滤波；`full_physical_error_budget`为False。追加残差档位是敏感性假设，没有取得标定保证。

## 复现与修改

在仓库根目录依次运行：

```powershell
python simulation/review_diagnosis.py
python scripts/validate_diagnosis_review.py
python scripts/plot_diagnosis_review.py
node scripts/verify_diagnosis_figures.mjs
python scripts/finalize_diagnosis_review.py
```

依赖NumPy、Matplotlib与本机Microsoft YaHei；布局检查使用本机Edge和支持WebSocket的Node。绘图源/PNG/SVG位于`application/figures/diagnosis_review`。首次执行验收汇总前须有全部前项检查，任何哈希不符则失败。正式产物重新打包还须运行`build_portal.py`与`package_submission.py`，其清单只记录交付一致性。

不得运行`finalize_collection_review.py`重置进度；它是先前A05工作包的汇总器。新汇总保留A05并更新A06/A07，不覆盖旧模型/网页/申报稿。全部进度见[分项进度](../../deliverables/分项验收进度.json)。
