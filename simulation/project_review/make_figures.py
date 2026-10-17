# -*- coding: utf-8 -*-
"""生成申报书最关键的三张图（2026-10-17 更新版）：
  图A 技术路线图（16:9 横版，四阶段，阶段间依赖链）
  图B 判据样本独立性修正与门限重定（块版 vs 重叠版 + 门限扫描）
  图C 两类故障的最小可检幅度 × 持续时长二维边界（泄漏 / 受限）
风格遵循：Microsoft YaHei、字号 ≥13pt、PNG+SVG、dpi=200、配色 ≤4。
数据来源：E9_block_threshold.json（2026-10-17 跑出的现行边界）。
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei'],
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'font.size': 13.5,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 13.5,
    'ytick.labelsize': 13.5,
    'legend.fontsize': 13.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

G, O, M, B = "#1b7f4b", "#d95f02", "#6b6b6b", "#2b6cb0"


def _out_of_view_labels(fig):
    """收集"位于坐标区视图范围之外"的刻度标签对象。

    matplotlib 会为定位器产生的所有刻度保留 Text 对象，即使该刻度在视图
    范围之外、实际并不绘制。它们的 window_extent 仍会返回一个坐标，若不排除
    就会造成大量假阳性重叠告警。
    """
    hidden = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = axis.get_view_interval()
            for tick in axis.get_major_ticks():
                loc = tick.get_loc()
                if not (min(lo, hi) <= loc <= max(lo, hi)):
                    hidden.add(id(tick.label1))
                    hidden.add(id(tick.label2))
    return hidden


def verify_layout(fig, name):
    """客观校验：所有文本必须在画布内，且两两不重叠（容差 2 px）。"""
    import matplotlib.text as mtext
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    hidden = _out_of_view_labels(fig)
    items = []
    for t in fig.findobj(mtext.Text):
        s = t.get_text()
        if not s.strip() or not t.get_visible() or id(t) in hidden:
            continue
        try:
            bb = t.get_window_extent(renderer=renderer)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        items.append((s.replace("\n", "/")[:26], bb))
    fw, fh = fig.canvas.get_width_height()
    problems = []
    for s, bb in items:
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > fw + 2 or bb.y1 > fh + 2:
            problems.append("越出画布: %s" % s)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 2 and oy > 2:
                problems.append("重叠: %s <> %s (%.0fx%.0f px)" % (items[i][0], items[j][0], ox, oy))
    if problems:
        print("  ✗ %s 布局问题 %d 处：" % (name, len(problems)))
        for p in problems:
            print("      -", p)
    else:
        print("  ✓ %s 布局校验通过（%d 个文本，无越界、无重叠）" % (name, len(items)))
    return problems


def save(fig, name):
    # 校验字号
    for ax in fig.get_axes():
        for t in ax.texts + ax.get_xticklabels() + ax.get_yticklabels():
            if t.get_fontsize() < 13:
                raise AssertionError("字号 %s < 13: %s" % (t.get_fontsize(), t.get_text()))
    verify_layout(fig, name)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT, name + "." + ext), dpi=200, facecolor="white")
    plt.close(fig)
    print("  ✓ %s" % name)


# =====================================================================
# 图A 技术路线图（与旧版一致）
# =====================================================================
def fig_roadmap():
    fig = plt.figure(figsize=(7.6, 12.0))
    fig.text(.045, .978, "图A　项目技术路线", fontsize=18, weight='bold', va='top')
    fig.text(.045, .948,
             "四阶段递进：上一阶段的产出即下一阶段的输入，形成闭合逻辑链",
             fontsize=13.5, va='top', color=M)

    ax = fig.add_axes([.04, .03, .92, .875])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    stages = [
        ("阶段一　测量与建模", "2027.3—4", G, [
            "器件选型与装配",
            "跨工况参考标定",
            "健康关系与分档参照",
            "有线采集通路",
        ], "标定曲线、残差与工作区边界"),
        ("阶段二　判据与实验", "2027.5—6", B, [
            "双参数判据与门限",
            "工况分档与参照",
            "54—72 次故障实验",
            "三类扰动对照",
        ], "独立操作级数据集、性能曲线与可检边界"),
        ("阶段三　通信与联调", "2027.7—8", O, [
            "LoRa 真实链路对照",
            "接收服务与落库",
            "8 小时连续记录",
            "重启与恢复测试",
        ], "发收日志、延迟与能耗数据"),
        ("阶段四　验证与成果", "2027.9—2028.2", M, [
            "留出批次与消融",
            "论文与软著",
            "竞赛参与",
            "原型与结题报告",
        ], "论文稿与软著、原型与结项材料"),
    ]

    seg, gap, top = 23.0, 2.2, 99.0
    for i, (name, period, col, tasks, out) in enumerate(stages):
        y0 = top - (i + 1) * seg - i * gap          # 段底
        # 标题条（阶段名 + 时间）
        ax.add_patch(FancyBboxPatch((1, y0 + 18), 98, 5,
                                    boxstyle="round,pad=0.2,rounding_size=0.8",
                                    fc=col, ec=col, alpha=.92))
        ax.text(50, y0 + 20.5, "%s　（%s）" % (name, period), ha="center", va="center",
                color="white", fontsize=13.5, weight="bold")
        # 任务横排 4 格
        tw, tgap = 23.5, 1.33
        for j, t in enumerate(tasks):
            x = 1 + j * (tw + tgap)
            ax.add_patch(FancyBboxPatch((x, y0 + 9.5), tw, 7,
                                        boxstyle="round,pad=0.15,rounding_size=0.6",
                                        fc="white", ec=col, lw=1.6))
            ax.text(x + tw / 2, y0 + 13, t, ha="center", va="center",
                    fontsize=13, color="#222222")
        # 阶段产出条
        ax.add_patch(FancyBboxPatch((1, y0 + 1), 98, 6,
                                    boxstyle="round,pad=0.2,rounding_size=0.8",
                                    fc=col, ec=col, alpha=.16))
        ax.text(4, y0 + 4, "阶段产出：" + out, ha="left", va="center",
                fontsize=13, color=col, weight="bold")
        # 段间向下箭头
        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((50, y0 - 0.2), (50, y0 - gap + 0.2),
                                         arrowstyle="-|>", mutation_scale=16,
                                         color=M, lw=2.0))
    save(fig, "roadmap")


# =====================================================================
# 图B 门限重定：重叠版 vs 块版 + 块版门限扫描
# =====================================================================
def fig_threshold():
    e9 = json.load(open(os.path.join(RES, "E9_block_threshold.json"), encoding="utf-8"))

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 9.8))
    fig.text(.035, .988, "图B　判据样本独立性修正与门限重定",
             fontsize=18, weight='bold', va='top')
    fig.text(.035, .950,
             "上：健康段累积和峰值（对数纵轴）；下：块版门限扫描",
             fontsize=13.5, va='top', color=M)

    # 左：峰值分布对比（对数纵轴：重叠版最大值 8051.8 与块版 25.8 差 265 倍，
    # 线性轴会把 P90/最大值全部截断到顶，必须用对数轴才看得出来）
    ax = axes[0]
    labs = ["重叠版\n(1 s/样本)", "块版\n(10 s/样本)"]
    p50 = [e9["overlap_peaks"]["p50"], e9["block_peaks"]["p50"]]
    p90 = [e9["overlap_peaks"]["p90"], e9["block_peaks"]["p90"]]
    pmax = [e9["overlap_peaks"]["max"], e9["block_peaks"]["max"]]
    x = np.arange(len(labs)); w = .24
    ax.bar(x - w, np.array(p50) - 1.0, w, bottom=1, color=G, alpha=.85, label="P50")
    ax.bar(x, np.array(p90) - 1.0, w, bottom=1, color=B, alpha=.85, label="P90")
    ax.bar(x + w, np.array(pmax) - 1.0, w, bottom=1, color=O, alpha=.85, label="最大值")
    ax.set_yscale('log')
    ax.set(xlabel="判据版本", ylabel="累积和峰值（对数纵轴）",
           xticks=x, xticklabels=labs, ylim=(1, 60000))
    ax.set_yticks([1, 10, 100, 1000, 10000])
    for lbl in ax.get_xticklabels():
        lbl.set_linespacing(1.9)
    ax.grid(alpha=.15, axis="y", which="both"); ax.set_axisbelow(True)
    ax.legend(loc="upper right", framealpha=.95)
    ax.set_title("健康段累积和峰值分布", fontsize=14, pad=8)
    for xi, v50, v90, vm in zip(x, p50, p90, pmax):
        ax.text(xi - w, v50 * 1.15, "%.1f" % v50, ha="center", fontsize=13, color=G)
        ax.text(xi, v90 * 1.15, "%.1f" % v90, ha="center", fontsize=13, color=B)
        ax.text(xi + w, vm * 1.15, "%.1f" % vm, ha="center", fontsize=13, color=O)

    # 右：块版门限扫描
    ax = axes[1]
    sweep = [r for r in e9["sweep"] if r["h"] <= 120]  # 只画到 120
    hs = [r["h"] for r in sweep]
    far = [r["far"] * 100 for r in sweep]
    det_leak = [r["det_leak"] * 100 for r in sweep]
    det_restr = [r["det_restriction"] * 100 for r in sweep]

    ax.plot(hs, far, "o-", color=O, lw=2.5, ms=6, label="健康段误报率")
    ax.plot(hs, det_leak, "s--", color=G, lw=2.5, ms=5, label="泄漏检出率")
    ax.plot(hs, det_restr, "^:", color=B, lw=2.5, ms=5, label="受限检出率")
    ax.axvline(26, color=M, ls="--", lw=2, label="冻结门限 h*=26")
    # 结论文字放在右下空白区（误报率≈0、检出率≈100 之间），避免压线压图例
    ax.text(44, 12, "h*=26：FAR 0.00%",
            fontsize=13, color=M, ha="left", va="bottom", linespacing=1.7)
    ax.set(xlabel="累积和门限 h", ylabel="百分比（%）",
           ylim=(-4, 108), xlim=(0, 120))
    ax.grid(alpha=.15); ax.set_axisbelow(True)
    # 图例放到坐标区下方：放在坐标区内会压住检出率曲线，贴着坐标区又会压住 x 轴标题
    ax.legend(loc="center right", frameon=False)
    ax.set_title("块版门限扫描", fontsize=14, pad=8)

    fig.subplots_adjust(left=.115, right=.97, top=.86, bottom=.09, hspace=.58)
    fig.text(.035, .035,
             "数据：E9_block_threshold.json",
             fontsize=13, va='bottom', color=M)
    save(fig, "threshold_separation")


# =====================================================================
# 图C 两类故障的最小可检幅度 × 持续时长二维边界
# =====================================================================
def parse_grid(grid):
    pairs = sorted(grid.items(), key=lambda kv: float(kv[0]))
    amps = [float(k) for k, _ in pairs]
    durs = sorted(int(k) for k in pairs[0][1].keys())
    Z = np.zeros((len(amps), len(durs)))
    for i, (_, row) in enumerate(pairs):
        for j, d in enumerate(durs):
            num, den = row[str(d)].split("/")
            Z[i, j] = float(num) / float(den) * 100
    return amps, durs, Z


def fig_boundary():
    e9 = json.load(open(os.path.join(RES, "E9_block_threshold.json"), encoding="utf-8"))
    leak_amp, leak_dur, Z_leak = parse_grid(e9["grid"])
    restr_amp, restr_dur, Z_restr = parse_grid(e9["grid_restriction"])

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 10.0))
    fig.text(.035, .988, "图C　最小可检幅度与持续时长的二维边界",
             fontsize=18, weight='bold', va='top')
    fig.text(.035, .950,
             "色块内数字 = 检出数 / 40 轨迹",
             fontsize=13.5, va='top', color=M)

    def draw_heatmap(ax, amps, durs, Z, title, ylabel, boundary_index=None):
        im = ax.imshow(Z, cmap="YlGn", vmin=0, vmax=100, aspect="auto", origin="lower")
        ax.set_xticks(range(len(durs)), [str(d) for d in durs])
        ax.set_yticks(range(len(amps)), ["%.0f%%" % (a * 100) for a in amps])
        # 边界说明写进标题，不压在色块上
        ax.set(xlabel="故障持续时长（秒）", ylabel=ylabel, title=title)
        ax.xaxis.set_label_coords(.5, -.11)
        ax.title.set_linespacing(1.5)
        for i in range(len(amps)):
            for j in range(len(durs)):
                ax.text(j, i, "%.0f" % Z[i, j], ha="center", va="center",
                        fontsize=13, color="#1a1a1a" if Z[i, j] < 60 else "white")
        cb = fig.colorbar(im, ax=ax, fraction=.04, pad=.02)
        cb.set_label("检出率（%）", fontsize=13.5)
        cb.ax.tick_params(labelsize=13)
        if boundary_index is not None:
            # 画在"边界行"与下一更大幅度行之间的格线上，不压任何数字
            ax.axhline(boundary_index + 0.5, color=O, ls="--", lw=2.2)

    # 泄漏：+2% 是 80 s 边界（首行）
    ax = axes[0]
    draw_heatmap(ax, leak_amp, leak_dur, Z_leak,
                 title="等效泄漏（流量相对增量）\n+2% 为 80 s 检出边界",
                 ylabel="泄漏幅度（相对健康流量）",
                 boundary_index=leak_amp.index(0.02))

    # 受限：+50% 是 80 s 边界
    ax = axes[1]
    draw_heatmap(ax, restr_amp, restr_dur, Z_restr,
                 title="等效过流受限（阻力相对增量）\n+50% 为 80 s 检出边界",
                 ylabel="受限幅度（相对健康阻力）",
                 boundary_index=restr_amp.index(0.50))

    fig.subplots_adjust(left=.17, right=.87, top=.855, bottom=.10, hspace=.48)
    fig.text(.035, .015,
             "数据：E9_block_threshold.json；门限 h*=26",
             fontsize=13, va='bottom', color=M)
    save(fig, "detection_boundary")


if __name__ == "__main__":
    print("生成图：")
    fig_roadmap()
    fig_threshold()
    fig_boundary()
    print("\n输出目录:", OUT)
    for f in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, f)
        print("  %-34s %8.0f B" % (f, os.path.getsize(p)))
