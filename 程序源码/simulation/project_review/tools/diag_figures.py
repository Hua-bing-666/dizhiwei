# -*- coding: utf-8 -*-
"""诊断三张图的排版：画布比例、文字/容器宽度比、字号在文档中的等效大小。"""
import os, sys, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

plt.rcParams.update({'font.sans-serif': ['Microsoft YaHei'], 'font.size': 13.5})

print("=" * 78)
print("诊断：三张图的画布比例与文字拥挤度")
print("=" * 78)

SPECS = {
    "roadmap":              (7.6, 12.0),
    "threshold_separation": (7.6, 9.8),
    "detection_boundary":   (7.6, 10.0),
}
for name, (w, h) in SPECS.items():
    print("\n【%s】" % name)
    print("  画布      : %.1f × %.1f 英寸  → 宽高比 %.2f（%s）" % (
        w, h, w / h, "竖版" if h > w else "横版"))
    print("  输出像素  : %d × %d @200dpi" % (w * 200, h * 200))
    # 文档中按 410 pt 宽插入时的缩放
    ins_w = 410.0
    scale = ins_w / (w * 72)
    print("  插入文档  : 按 410pt 宽插入时缩放 %.2f×" % scale)
    print("  等效字号  : 13.5pt → 正文中约 %.1f pt" % (13.5 * scale))

print("\n" + "=" * 78)
print("诊断：技术路线图 4 列任务格子的文字容纳情况")
print("=" * 78)

# 复算 roadmap 的几何：canvas 7.6in，ax 占 92% 宽，xlim 0..100
fig = plt.figure(figsize=(7.6, 12.0), dpi=200)
ax = fig.add_axes([.04, .03, .92, .875])
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

# 轴宽（像素）→ 每 x 单位像素
bbox = ax.get_window_extent(renderer)
px_per_unit = bbox.width / 100.0
tw = 23.5
print("  坐标区宽 %.0f px，每单位 %.2f px；每个任务格宽 %.1f 单位 = %.0f px"
      % (bbox.width, px_per_unit, tw, tw * px_per_unit))

TASKS = ["器件选型与装配", "跨工况参考标定", "健康关系与分档参照", "有线采集通路",
         "双参数判据与门限", "工况分档与参照", "54—72 次故障实验", "三类扰动对照",
         "LoRa 真实链路对照", "接收服务与落库", "8 小时连续记录", "重启与恢复测试",
         "留出批次与消融", "论文与软著", "竞赛参与", "原型与结题报告"]
print("\n  %-22s %8s %8s %6s" % ("任务文字", "文字宽px", "格子宽px", "占比"))
worst = 0
for t in TASKS:
    txt = ax.text(0, 0, t, fontsize=13)
    bb = txt.get_window_extent(renderer=renderer)
    txt.remove()
    ratio = bb.width / (tw * px_per_unit)
    worst = max(worst, ratio)
    flag = " ← 超出" if ratio > 1.0 else (" ← 挤" if ratio > 0.92 else "")
    print("  %-22s %8.1f %8.1f %5.0f%%%s" % (t, bb.width, tw * px_per_unit, ratio * 100, flag))
print("\n  ⇒ 最宽文字占格子宽度的 %.0f%%" % (worst * 100))

# 阶段产出条：整行文字
OUTS = ["标定曲线、残差与工作区边界",
        "独立操作级数据集、性能曲线与可检边界",
        "发收日志、延迟与能耗数据",
        "论文稿与软著、原型与结项材料"]
print("\n  阶段产出条（放在 98 单位宽、左对齐 x=4 起）:")
bar_px = 98 * px_per_unit
for o in OUTS:
    txt = ax.text(0, 0, "阶段产出：" + o, fontsize=13, weight="bold")
    bb = txt.get_window_extent(renderer=renderer)
    txt.remove()
    avail = bar_px - 3 * px_per_unit  # 左侧留 3 单位
    flag = " ← 超出右边界" if bb.width > avail else ""
    print("    %-40s 宽%6.1f px / 可用%6.1f px  %s" % (
        ("阶段产出：" + o)[:36], bb.width, avail, flag))

plt.close(fig)

print("\n" + "=" * 78)
print("诊断：两图竖排双面板导致的高度")
print("=" * 78)
for name, (w, h), n in [("threshold_separation", (7.6, 9.8), 2),
                        ("detection_boundary", (7.6, 10.0), 2)]:
    print("  %-24s %d 个面板竖排，共 %.1f 英寸高；若横排可降到约 %.1f 英寸" % (
        name, n, h, max(6.0, h / 2 + 1.2)))
