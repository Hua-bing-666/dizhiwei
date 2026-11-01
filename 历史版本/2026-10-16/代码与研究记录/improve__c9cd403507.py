# -*- coding: utf-8 -*-
"""完善批次：
 1) 仿真目录整理（legacy/ 隔离废版与诊断脚本）
 2) 修正 v2/F1_F2 的误导性标签
 3) 技术路线并入优化建议（阀态感知、BOCD、流量计校核、精度升级、第三测点）
 4) 合并重复的验收记录
"""
import os, io, shutil, re

WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
SIM = os.path.join(WS, "simulation", "project_review")
DOCS = os.path.join(WS, "docs")
ARCH = os.path.join(WS, "archive")

log = []

# ---------- 1) 仿真目录整理 ----------
legacy = os.path.join(SIM, "legacy")
os.makedirs(legacy, exist_ok=True)

# 废版（已知 bug：注入窗口与标定窗口重叠）
for n in ["E6_E7_corrected.py"]:
    src = os.path.join(SIM, n)
    if os.path.exists(src):
        shutil.move(src, os.path.join(legacy, n))
        log.append("隔离废版脚本 legacy/%s" % n)
for n in ["E6_E7_corrected.txt", "E6_E7_corrected.json"]:
    src = os.path.join(SIM, "results", n)
    if os.path.exists(src):
        shutil.move(src, os.path.join(legacy, n))
        log.append("隔离废版结果 legacy/%s" % n)

# 诊断脚本（重构过程中的排查记录，保留但不属主线）
for n in ["diag.py", "diag2.py", "diag3.py", "smoke.py"]:
    src = os.path.join(SIM, n)
    if os.path.exists(src):
        shutil.move(src, os.path.join(legacy, n))
        log.append("隔离诊断脚本 legacy/%s" % n)

# ---------- 2) 修正误导性标签 ----------
def fix_label(path, old, new):
    t = io.open(path, encoding="utf-8").read()
    if old in t:
        io.open(path, "w", encoding="utf-8").write(t.replace(old, new))
        return True
    return False

p2 = os.path.join(SIM, "E6_E7_v2.py")
if fix_label(p2,
             'A("  ⇒ 满足『全检出 + 零误报』的 U 上限 = %.2f kPa（1σ）" % (max(ok_u) if ok_u else float("nan")))',
             'A("  ⇒ 在 0—%.2f kPa 的测试范围内全部『全检出 + 零误报』；" % (max(ok_u) if ok_u else 0.0))\n'
             '    A("     未观察到失效拐点，真实失效点高于测试上限（另见 F1_F2.py 扩展到 5 kPa）")'):
    log.append("修正 E6_E7_v2.py 的 U 标签")

pf = os.path.join(SIM, "F1_F2.py")
if fix_label(pf,
             'A("  ⇒ 保持『全检出 + 零误报』的 U 上限 = %.2f kPa（1σ）" % (max(ok_u) if ok_u else float("nan")))',
             'A("  ⇒ 在 0—%.2f kPa 的测试范围内保持『全检出 + 零误报』" % (max(ok_u) if ok_u else 0.0))\n'
             '    A("     结论：判据对压力测量精度的敏感度低；瓶颈在故障幅度而非传感器精度")'):
    log.append("修正 F1_F2.py 的 U 标签")

# ---------- 3) 技术路线并入优化建议 ----------
TR = os.path.join(DOCS, "技术路线_申报书版.md")
t = io.open(TR, encoding="utf-8").read()
if "附三：方案优化建议" not in t:
    add = """

---

# 附三：方案优化建议（多维最优性评估结论）

依据 [方案最优性评估_多维.md](方案最优性评估_多维.md)，对本路线作以下优化。
**架构、理论框架、边缘算法三层已是最优，不作更换**；以下 5 处是在预算内的增量改进。

| 优先级 | 优化项 | 增量成本 | 收益 | 落在哪一环节 |
|---|---|---|---|---|
| **1** | **增加阀态感知**（微动开关或霍尔，约 5 元） | **≈5 元** | **工况标签由"流量阶跃推断"变为"直接测得"** | 环节三 |
| **2** | **主机端增加 BOCD 贝叶斯变点后验** | 0（软件） | 与边缘 CUSUM 互校；对齐当前主流方法 | 环节四 |
| 3 | 流量计压损标定，或增设孔板差压通道 | 0—300 元 | 消除区段阻力 R̂ 的污染 | 环节三 |
| 4 | 差压精度由 ±0.25%FS 升至 **±0.1%FS** | 300—800 元 | 信号/不确定度由 9.7 提升至 **24.2** | 环节二 |
| 5 | 增加下游第三压力测点 | 80—350 元 | 可分区段定位，共模分量可分离 | 环节二 |

**预算校核**：当前材料费 1980—4510 元；全部优化增量 385—1455 元；
优化后 **2365—5965 元**，仍在 **6300 元**额度内。

## 为什么第 1 项性价比最高

工况分档是本判据的核心（见环节三、环节四）。此前"当前处于哪个工况"要靠
**流量阶跃检测从数据反推**——这是一个推断，存在不确定性。
加一个 5 元的微动开关或霍尔元件贴在阀上，可**直接读出阀态**，
把推断变成测量，**用极小代价消除判据的最大不确定性来源**。

## 为什么不引入深度学习

| 方法 | 时兴度 | 本项目适合度 |
|---|---|---|
| LSTM / Transformer / PINN | 很高 | ★★☆☆☆ **数据量不足** |
| **BOCD 贝叶斯在线变点** | 高 | ★★★★☆ 建议增加（主机端） |
| **CUSUM 累积和** | 中高 | ★★★★☆ **理论最优，保留为边缘主判据** |

本项目只有**几十次独立操作**的标注数据。文献中深度学习类方法的高准确率
多在台架长时序列上取得；在数据量不足时强行使用，**反而降低结论可信度**。

**CUSUM 并非落后**：对"变化幅度未知"的检测问题，它在给定虚警率下使最坏情况
检测延迟最小（Lorden 1971），且本项目已做到**门限由 ARR₀ 反推**而非拍定。

## 最优算法组合

```
边缘（MCU）：CUSUM          —— 快、省、理论最优、可解释
主机（PC） ：BOCD 变点后验   —— 准、对齐主流、与边缘互校
```

边缘负责实时报警，主机负责回答"变点发生在第几次灌水"。
两者互校，既满足实时性，又用上当前主流方法，**且不需要更多数据**。

## 上报策略的最优形式

由"4 种策略对照"明确为**分级策略**：

```
常态：1—5 秒巡航（按轮灌节拍调整；停灌期降频或休眠）
检测到异常候选：自动加密到 1 秒，直至确认或排除
异常确认后：事件优先上报 + 接收确认 + 恢复重传
```

**理由**：与"一天只有 1—4 小时有流量"的实际节拍匹配，兼顾即时性与读取/发送代价。
"""
    t = t.rstrip() + add
    io.open(TR, "w", encoding="utf-8").write(t)
    log.append("技术路线并入「附三：方案优化建议」")

print("\n".join(log))

# ---------- 4) 合并验收记录 ----------
A1 = os.path.join(DOCS, "技术验收记录_自洽性与口径统一.md")
A2 = os.path.join(DOCS, "立项阶段总验收记录.md")
if os.path.exists(A1) and os.path.exists(A2):
    t1 = io.open(A1, encoding="utf-8").read()
    t2 = io.open(A2, encoding="utf-8").read()
    # 把 A1 的内容作为 A2 的一节并入
    body = re.sub(r"^#[^\n]*\n", "", t1)          # 去掉 A1 的一级标题
    body = body.replace("\n## ", "\n### ")         # 降一级
    merged = t2.rstrip() + "\n\n---\n\n## 附：技术验收记录（自洽性与口径统一）\n" + body.strip() + "\n"
    io.open(A2, "w", encoding="utf-8").write(merged)
    shutil.move(A1, os.path.join(ARCH, "docs_历史", "技术验收记录_自洽性与口径统一.md"))
    log.append("合并验收记录：技术验收记录 -> 立项阶段总验收记录（原文归档）")

print("\n".join(log[-1:]))
print("\n=== simulation/project_review 整理后 ===")
for n in sorted(os.listdir(SIM)):
    p = os.path.join(SIM, n)
    if os.path.isdir(p):
        print("   DIR  %-10s %d 个文件" % (n, len(os.listdir(p))))
    else:
        print("   FILE %s" % n)
