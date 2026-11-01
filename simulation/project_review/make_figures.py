# -*- coding: utf-8 -*-
"""申报书配图全套（2026-10-22 第 3 版，共 7 张）

本版三件事：
  1) 修面板对齐：同图内数据面板一律共用同一条底边与同一高度（差 ≤0.03 in），
     由 check_aligned() 硬校验。
  2) 风格再收一档：强调色 ≤2，线宽 1.0—1.6 pt，柱无描边，仅保留极浅横线。
  3) 补图：把 E10 / E9 里此前只有文字表格的结论画出来。

图内不写标题、副标题、分隔线、数据来源 —— 全部进图注。
尺寸：正文插图宽 410 pt；图内 13 pt 插入后须 ≥9 pt ⇒ 画布宽 ≤8.2 in。
校验：tools/layout_lint.py（越界 / 文字压文字 / 文字压曲线 / 文字被色块盖住）
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
import layout_lint

plt.rcParams.update({
    # 主字体用 Microsoft YaHei：Noto Sans SC 在 matplotlib 中对**旋转文字**
    # 会逐字重叠渲染（实测哈希一致、可复现），而雅黑正常。
    # 雅黑对本文所用 351 个汉字覆盖率 100%。
    'font.sans-serif': ['Microsoft YaHei', 'Noto Sans SC', 'DejaVu Sans'],
    'font.family': 'sans-serif',
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'mathtext.fontset': 'dejavusans',
    'mathtext.default': 'regular',
    'font.size': 13,
    'axes.labelsize': 13,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 13,
    'axes.linewidth': 0.6,
    'axes.edgecolor': '#333333',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.labelcolor': '#1A1A1A',
    'axes.labelpad': 2,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'xtick.major.size': 3.0, 'ytick.major.size': 3.0,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.color': '#333333', 'ytick.color': '#333333',
    'xtick.minor.visible': False,
    'lines.linewidth': 1.2,
    'legend.frameon': False,
})

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

# ---------------- 配色：按已发表指南选取 ----------------
# 定性色板用 Okabe-Ito（Okabe & Ito, 为色觉缺陷无障碍设计；多数现代风格指南
# 推荐的定性科研图表默认首选）。此处取 4 色，兼顾白底对比度与灰度可分性：
#   蓝 #0072B2  灰阶 94 ｜ 绿 #009E73  灰阶 121
#   橙 #E69F00  灰阶 163 ｜ 紫 #CC79A7  灰阶 142
# 相邻两类的最小灰阶差为 21，满足"转灰度仍可区分"的基本检验。
# 连续色阶用 Viridis：感知均匀、色盲友好、灰度打印效果佳；
# 不用手工调配的渐变（手工 ramp 通常不满足感知均匀）。
INK, GRAY, GRAY_L = '#1A1A1A', '#8C8C8C', '#D8D8D8'
GRAY_XL = '#F2F2F2'
BLUE   = '#0072B2'   # Okabe-Ito blue
GREEN  = '#009E73'   # Okabe-Ito bluish green
ORANGE = '#E69F00'   # Okabe-Ito orange
PURPLE = '#CC79A7'   # Okabe-Ito reddish purple
VERM   = '#D55E00'   # Okabe-Ito vermillion（告警/误报）
SKY    = '#56B4E9'   # Okabe-Ito sky blue

# 兼容旧变量名，避免大改调用处
TEAL, RED, CYAN = GREEN, VERM, SKY

CMAP_SEQ = 'viridis'
def gray_value(h):
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

DOC_W_PT, DOC_MIN_FONT = 410.0, 9.0
PANEL_TOL_IN = 0.03

# 技术路线图几何常量（校验器复用，避免两处脱节）
ROAD_A, ROAD_B = 48.0, 38.0     # 椭圆半轴（比值 1.26，近圆）
ROAD_CW, ROAD_CH = 30.0, 34.0   # 卡片宽高
ROAD_FK = 0.80                  # 卡片中心距 = 半轴 × FK


# =====================================================================
# 校验
# =====================================================================
def _data_axes(fig):
    out = []
    for a in fig.axes:
        if getattr(a, "_is_colorbar", False):
            continue
        if not a.axison:
            continue
        if a.get_position().width > 0.99:
            continue
        out.append(a)
    return out


def check_aligned(fig, name):
    axs = _data_axes(fig)
    if len(axs) < 2:
        return []
    fh = fig.get_size_inches()[1]
    fw = fig.get_size_inches()[0]
    b = [a.get_position().y0 for a in axs]
    h = [a.get_position().height for a in axs]
    t = [a.get_position().y1 for a in axs]
    x0 = [a.get_position().x0 for a in axs]
    w = [a.get_position().width for a in axs]

    side_by_side = (max(b) - min(b)) < 0.02 and (max(h) - min(h)) < 0.02
    stacked = (max(x0) - min(x0)) < 0.02 and (max(w) - min(w)) < 0.02

    probs = []
    if side_by_side:
        if (max(b) - min(b)) * fh > PANEL_TOL_IN:
            probs.append("面板底边不齐：%.2f in" % ((max(b) - min(b)) * fh))
        if (max(h) - min(h)) * fh > PANEL_TOL_IN:
            probs.append("面板高度不一：%.2f in" % ((max(h) - min(h)) * fh))
        print("       ✓ 并排面板对齐（底边差 %.3f in、高度差 %.3f in）"
              % ((max(b) - min(b)) * fh, (max(h) - min(h)) * fh))
    elif stacked:
        if (max(x0) - min(x0)) * fw > PANEL_TOL_IN:
            probs.append("堆叠面板左边不齐：%.2f in" % ((max(x0) - min(x0)) * fw))
        if (max(w) - min(w)) * fw > PANEL_TOL_IN:
            probs.append("堆叠面板宽度不一：%.2f in" % ((max(w) - min(w)) * fw))
        print("       ✓ 堆叠面板对齐（左边差 %.3f in、宽度差 %.3f in）"
              % ((max(x0) - min(x0)) * fw, (max(w) - min(w)) * fw))
    else:
        print("       · 非并排/堆叠布局，跳过对齐校验")

    if probs:
        print("       ✗ %s 对齐：" % name)
        for p in probs:
            print("          - " + p)
    return probs


def save(fig, name, w_in, ignore_inside=(), check_lines=True):
    probs = check_aligned(fig, name)
    probs += layout_lint.check(fig, name, ignore_text_inside=ignore_inside,
                               check_lines=check_lines)
    scale = DOC_W_PT / (w_in * 72.0)
    # 判据：图内最小字号 × 插入缩放 ≥ 9 pt（允许图内做字号分级）
    sizes = [tt.get_fontsize() for tt in fig.findobj(matplotlib.text.Text)
             if tt.get_text().strip() and tt.get_visible()]
    min_pt = min(sizes) if sizes else 13.0
    print("       画布 %.2f×%.2f in ｜ 缩放 %.2f× ｜ 最小字号 %.1f→%.1fpt %s"
          % (w_in, fig.get_size_inches()[1], scale, min_pt, min_pt * scale,
             "✓" if min_pt * scale >= DOC_MIN_FONT else "✗ 偏小"))
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT, "%s.%s" % (name, ext)),
                    dpi=300, facecolor="white")
    plt.close(fig)
    return probs


def mark_colorbar(cb):
    cb.ax._is_colorbar = True
    return cb


def two_panels(fig, left1, w1, left2, w2, bottom, height):
    a1 = fig.add_axes([left1, bottom, w1, height])
    a2 = fig.add_axes([left2, bottom, w2, height])
    return a1, a2


# =====================================================================
# 图 1：技术路线（环状闭环 · 字号分级 · 分块填充 · 箭头逆时针）
# =====================================================================
def fig_roadmap():
    W, H = 7.5, 6.0
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.008, 0.008, 0.984, 0.984])
    ax.set_xlim(-52, 52); ax.set_ylim(-50, 50); ax.axis("off")

    A_R, B_R = ROAD_A, ROAD_B
    CW, CH = ROAD_CW, ROAD_CH
    F_K = ROAD_FK

    stages = [
        (135, "01", "测量与建模", "2027.3—4", BLUE,
         ["器件选型与装配", "跨工况参考标定", "健康关系与分档", "有线采集通路"]),
        ( 45, "02", "判据与实验", "2027.5—6", ORANGE,
         ["双参数判据门限", "工况分档参照", "54—72 次实验", "三类扰动对照"]),
        (-45, "03", "通信与联调", "2027.7—8", GREEN,
         ["LoRa 真实链路", "接收服务落库", "8 小时连续记录", "重启与恢复"]),
        (-135, "04", "验证与成果", "2027.9—2028.2", PURPLE,
         ["留出批次与消融", "论文与软著", "竞赛参与", "原型与结题报告"]),
    ]

    # 不再画虚线椭圆（会与卡片相交、视觉上像断线）；
    # 闭环由四段连接卡片边缘的箭头本身构成。

    # 四块卡片：标题带（填色）+ 正文区（白底）两段式结构，文字分级
    HDR = 9.5                      # 标题带高度
    BODY = CH - HDR                # 正文区高度
    for ang, num, name, period, colr, tasks in stages:
        a = np.deg2rad(ang)
        cx, cy = A_R * np.cos(a) * F_K, B_R * np.sin(a) * F_K
        x0, y0 = cx - CW / 2, cy - CH / 2

        # 整卡底色（标题带颜色），再以白底覆盖正文区，形成两段式
        ax.add_patch(plt.Rectangle((x0, y0), CW, CH, fc=colr, ec=colr,
                                   lw=1.2, gid="card"))
        ax.add_patch(plt.Rectangle((x0, y0), CW, BODY, fc="white", ec=colr,
                                   lw=1.2, gid="card"))

        # 标题带：编号（13pt 白）+ 阶段名（15pt 白粗）
        yh = y0 + CH - HDR / 2
        ax.text(x0 + 2.4, yh, num, ha="left", va="center",
                fontsize=13, weight="bold", color="white")
        ax.text(x0 + 8.0, yh, name, ha="left", va="center",
                fontsize=15, weight="bold", color="white")
        # 正文区：时间（12pt 灰）+ 任务（12.5pt）
        ax.text(x0 + 2.4, y0 + BODY - 3.2, period, ha="left", va="center",
                fontsize=12, color=GRAY)
        ax.text(x0 + 2.4, y0 + BODY - 6.8, "\n".join(tasks), ha="left",
                va="top", fontsize=12.5, color=INK, linespacing=1.30)

    # 箭头：起点/终点距卡片留 2 单位缝隙，弧线向外凸，四段相连成闭环
    hx = A_R * np.cos(np.deg2rad(45)) * F_K     # 卡片中心横坐标
    hy = B_R * np.sin(np.deg2rad(45)) * F_K     # 卡片中心纵坐标
    inner = hx - CW / 2                         # 内侧边
    outer = hx + CW / 2                         # 外侧边
    g = 2.0                                     # 与卡片的缝隙
    tips = [
        ((-inner + g, hy), (inner - g, hy), -0.30),      # 01 → 02（上，向右）
        ((outer + g, hy), (outer + g, -hy), -0.20),      # 02 → 03（右，向下）
        ((inner - g, -hy), (-inner + g, -hy), -0.30),    # 03 → 04（下，向左）
        ((-outer - g, -hy), (-outer - g, hy), -0.20),    # 04 → 01（左，向上）
    ]
    for p0, p1, rad in tips:
        ax.add_patch(FancyArrowPatch(
            p0, p1, connectionstyle="arc3,rad=%.2f" % rad,
            arrowstyle="-|>", mutation_scale=14, color=GRAY, lw=1.3,
            shrinkA=0, shrinkB=0, gid="deco"))

    # 箭头上的文字：说明相邻阶段交付什么（白底遮住箭身，读作"标注在箭头上"）
    lab_kw = dict(ha="center", va="center", fontsize=12, color="#4D4D4D",
                  bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none"))
    ax.text(0, 24.6, "标定结果", **lab_kw)          # 01 → 02
    ax.text(48.4, 0, "判据参数", rotation=90, **lab_kw)   # 02 → 03
    ax.text(0, -24.6, "联调数据", **lab_kw)         # 03 → 04
    ax.text(-48.4, 0, "验证反馈", rotation=90, **lab_kw)  # 04 → 01

    # 中心：立题问题（单一段落，行距收紧）
    ax.text(0, 0, "支管故障\n能否从轮灌中分出", ha="center", va="center",
            fontsize=13, weight="bold", color=INK, linespacing=1.55)

    return save(fig, "roadmap", W)


# =====================================================================
# 图 2：样本独立性与门限
# =====================================================================
def fig_threshold():
    e9 = json.load(open(os.path.join(RES, "E9_block_threshold.json"), encoding="utf-8"))
    W, H = 8.0, 3.4
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.135, 0.255, 0.545, 0.415,
                            bottom=0.215, height=0.655)

    ov, bl = e9["overlap_peaks"], e9["block_peaks"]
    sets = [("重叠版", ov, RED), ("块版", bl, TEAL)]
    for yi, (lab, pk, colr) in enumerate(sets):
        y = 1 - yi
        for k, key in enumerate(["p50", "p90", "max"]):
            v = max(pk[key], 1.0)
            yy = y + (k - 1) * 0.22
            al = [0.42, 0.70, 1.0][k]
            ax_a.plot([1.0, v], [yy, yy], color=colr, lw=1.1, alpha=al,
                      solid_capstyle="butt")
            ax_a.plot([v], [yy], "o", ms=5.0, color=colr, alpha=al,
                      markeredgewidth=0)
            ax_a.text(v * 1.30, yy, "%.0f" % pk[key], va="center", ha="left",
                      fontsize=12, color=colr, alpha=min(1.0, al + 0.20))
    ax_a.set_xscale("log")
    ax_a.set_xlim(1, 130000)
    ax_a.set_ylim(-0.55, 1.55)
    ax_a.set_yticks([1, 0], [s[0] for s in sets])
    ax_a.set_xticks([1, 10, 100, 1000, 10000])
    ax_a.set_xlabel("健康段累积和峰值")
    ax_a.tick_params(axis="y", length=0)

    sweep = [r for r in e9["sweep"] if r["h"] <= 120]
    hs = [r["h"] for r in sweep]
    ax_b.plot(hs, [r["det_leak"] * 100 for r in sweep], "-", color=BLUE,
              lw=1.5, label="泄漏检出")
    ax_b.plot(hs, [r["det_restriction"] * 100 for r in sweep],
              linestyle=(0, (5, 2)), color=GREEN, lw=1.5, label="受限检出")
    ax_b.plot(hs, [r["far"] * 100 for r in sweep],
              linestyle=(0, (1.5, 1.8)), color=VERM, lw=1.5, label="健康误报")
    ax_b.axvline(e9["h_star"], color=GRAY, ls=(0, (4, 3)), lw=1.0)
    ax_b.text(e9["h_star"] + 2.5, 104, r"$h^*$=%d" % e9["h_star"], ha="left",
              va="bottom", fontsize=12, color=GRAY)
    ax_b.set_xlim(0, 120)
    ax_b.set_ylim(-5, 108)
    ax_b.set_xticks([0, 25, 50, 75, 100])
    ax_b.set_xlabel("累积和门限 h")
    ax_b.set_ylabel("百分比（%）")
    ax_b.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_b.set_axisbelow(True)
    ax_b.legend(loc="center right", bbox_to_anchor=(1.0, 0.42),
                handlelength=1.5, labelspacing=0.7)

    fig.text(0.032, 0.935, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.442, 0.935, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "threshold_separation", W)


# =====================================================================
# 图 3：二维可检边界
# =====================================================================
def _grid_matrix(grid):
    pairs = sorted(grid.items(), key=lambda kv: float(kv[0]))
    amps = [float(k) for k, _ in pairs]
    durs = sorted(int(k) for k in pairs[0][1].keys())
    Z = np.zeros((len(amps), len(durs)))
    for i, (_, row) in enumerate(pairs):
        for j, d in enumerate(durs):
            num, den = row[str(d)].split("/")
            Z[i, j] = float(num) / float(den) * 100.0
    return amps, durs, Z


def fig_boundary():
    e9 = json.load(open(os.path.join(RES, "E9_block_threshold.json"), encoding="utf-8"))
    W, H = 8.1, 3.5
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.105, 0.285, 0.545, 0.285,
                            bottom=0.175, height=0.645)

    panels = [
        (ax_a, "a", e9["grid"], "泄漏幅度", 0.02),
        (ax_b, "b", e9["grid_restriction"], "受限幅度", 0.50),
    ]
    for ax, tag, grid, ylab, edge in panels:
        amps, durs, Z = _grid_matrix(grid)
        im = ax.imshow(Z, cmap=CMAP_SEQ, vmin=0, vmax=100, aspect="auto",
                       origin="lower", interpolation="nearest")
        ax.set_xticks(range(len(durs)), [str(int(d) * 10) for d in durs])
        ax.set_yticks(range(len(amps)), ["%g%%" % (a * 100) for a in amps])
        ax.set_xlabel("持续时间（s）")
        ax.set_ylabel(ylab)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_xticks(np.arange(len(durs) + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(len(amps) + 1) - 0.5, minor=True)
        ax.grid(which="minor", color="white", lw=1.4)
        ax.tick_params(which="both", length=0)
        for i in range(len(amps)):
            for j in range(len(durs)):
                rgba = plt.get_cmap(CMAP_SEQ)(Z[i, j] / 100.0)
                lum = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                ax.text(j, i, "%.0f" % Z[i, j], ha="center", va="center",
                        fontsize=13, color="white" if lum < 0.5 else INK)
        # 边界行用虚线框标出（不用横线，避免贴到坐标轴上）
        if edge in amps:
            ax.add_patch(plt.Rectangle(
                (-0.5, amps.index(edge) - 0.5), len(durs), 1.0,
                fill=False, ec=VERM, lw=2.0, ls=(0, (4, 2.5)), zorder=6))
        cb = mark_colorbar(fig.colorbar(im, ax=ax, fraction=0.042, pad=0.02,
                                        ticks=[0, 25, 50, 75, 100]))
        cb.ax.tick_params(labelsize=13, length=2, width=0.6)
        cb.outline.set_linewidth(0.5)
        cb.outline.set_edgecolor(GRAY)
        fig.text(ax.get_position().x0 - 0.062, 0.855, tag,
                 fontsize=13, weight="bold", va="top")

    return save(fig, "detection_boundary", W, ignore_inside=tuple("0123456789"))


# =====================================================================
# 图 4：传感器噪声时间常数 vs 所需门限
# =====================================================================
def fig_noise_tau():
    e10 = json.load(open(os.path.join(RES, "E10_robustness.json"), encoding="utf-8"))
    rows = e10["noise_tau"]
    labels = ["基准", "0", "5", "30", "120"]
    h_need = [r["h_need"] for r in rows]
    far = [r["far"] * 100 for r in rows]

    W, H = 7.9, 3.3
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.095, 0.375, 0.585, 0.375,
                            bottom=0.235, height=0.615)
    x = np.arange(len(rows))

    ax_a.vlines(x, 0, h_need, color=TEAL, lw=1.6, zorder=3)
    ax_a.plot(x, h_need, "o", ms=7, color=TEAL, zorder=4, markeredgewidth=0)
    for xi, v in zip(x, h_need):
        ax_a.text(xi, v + 12, "%.0f" % v, ha="center", va="bottom",
                  fontsize=13, color=TEAL)
    ax_a.set_xticks(x, labels)
    ax_a.set_xlabel(r"噪声相关时间 $\tau$（s）")
    ax_a.set_ylabel("达 1% 误报所需门限 h")
    ax_a.set_ylim(0, 440)
    ax_a.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_a.set_axisbelow(True)

    ax_b.vlines(x, 0, far, color=RED, lw=1.6, zorder=3)
    ax_b.plot(x, far, "o", ms=7, color=RED, zorder=4, markeredgewidth=0)
    for xi, v in zip(x, far):
        ax_b.text(xi, v + 1.2, "%.1f" % v, ha="center", va="bottom",
                  fontsize=13, color=RED)
    ax_b.set_xticks(x, labels)
    ax_b.set_xlabel(r"噪声相关时间 $\tau$（s）")
    ax_b.set_ylabel(r"固定 $h^*$=26 时误报率（%）")
    ax_b.set_ylim(0, 47)
    ax_b.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_b.set_axisbelow(True)

    fig.text(0.018, 0.950, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.508, 0.950, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "noise_tau", W)


# =====================================================================
# 图 5：负载系数慢漂移 —— 固定 vs 自适应基线
# =====================================================================
def fig_ceff_drift():
    e10 = json.load(open(os.path.join(RES, "E10_robustness.json"), encoding="utf-8"))
    rows = e10["ceff_drift"]
    rate = [r["rate"] * 100 for r in rows]
    far_fix = [r["far_fix"] * 100 for r in rows]
    far_ad = [r["far_ad"] * 100 for r in rows]

    W, H = 7.2, 3.3
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.105, 0.215, 0.855, 0.635])

    ax.plot(rate, far_fix, "o-", color=RED, lw=1.5, ms=5,
            label="固定基线", zorder=4)
    ax.plot(rate, far_ad, "s-", color=TEAL, lw=1.5, ms=5,
            label="自适应基线", zorder=3)
    ax.axhline(1.0, color=GRAY, ls=(0, (4, 3)), lw=1.0, zorder=1)
    ax.set_xscale("symlog", linthresh=0.5)
    ax.set_xlim(-0.08, 11.5)
    ax.set_ylim(-4, 112)
    ax.set_xticks([0, 0.5, 1, 2, 5, 10], ["0", "0.5", "1", "2", "5", "10"])
    ax.set_xlabel("负载系数漂移速率（%/h）")
    ax.set_ylabel("健康段误报率（%）")
    ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", handlelength=1.6, labelspacing=0.7)

    return save(fig, "ceff_drift", W)


# =====================================================================
# 图 6：强基线对照 —— 检出与误报
# =====================================================================
def fig_baseline():
    """哑铃图：每类故障/工况一对点（朴素阈值 → 本方案），连线示差距。"""
    e10 = json.load(open(os.path.join(RES, "E10_robustness.json"), encoding="utf-8"))
    det = {r["kind"]: (r["d1"], r["d2"]) for r in e10["baseline_det"]}
    fa = {r["kind"]: (int(str(r["fa"]).split("/")[0]),
                      int(str(r["fb"]).split("/")[0]))
          for r in e10["baseline"]}

    W, H = 7.8, 3.5
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.150, 0.330, 0.610, 0.330,
                            bottom=0.345, height=0.505)

    def dumbbell(ax, data, xlim, col_b):
        keys = list(data.keys())
        y = np.arange(len(keys))[::-1]
        for yi, k in zip(y, keys):
            v1, v2 = data[k]
            same = abs(v2 - v1) < 0.5
            if not same:
                ax.plot([v1, v2], [yi, yi], color=GRAY_L, lw=2.4, zorder=2,
                        solid_capstyle="round")
                ax.plot([v1], [yi], "o", ms=8, color=GRAY, zorder=4,
                        markeredgewidth=0)
                ax.plot([v2], [yi], "o", ms=8, color=col_b, zorder=5,
                        markeredgewidth=0)
                ax.text(v1 - xlim * 0.020, yi, "%d" % v1, va="center",
                        ha="right", fontsize=13, color=GRAY)
                ax.text(v2 + xlim * 0.020, yi, "%d" % v2, va="center",
                        ha="left", fontsize=13, color=col_b)
            else:
                # 两法数值相同：只画一个点、只标一个数，避免重叠成"0◉0"
                ax.plot([v1], [yi], "o", ms=8, color=col_b, zorder=5,
                        markeredgewidth=0)
                ax.text(v1 + xlim * 0.020, yi, "%d" % v1, va="center",
                        ha="left", fontsize=13, color=col_b)
        ax.set_yticks(y, keys)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(-xlim * 0.10, xlim)
        ax.set_ylim(-0.6, len(keys) - 0.25)
        ax.grid(axis="x", color=GRAY_L, lw=0.5, alpha=0.8)
        ax.set_axisbelow(True)

    names = {"leak": "泄漏", "restriction": "受限", "drift": "漂移",
             "normal": "正常", "supply": "供压扰动", "load_unknown": "负载未知"}
    d_data = {names[k]: det[k] for k in ["leak", "restriction", "drift"]}
    f_data = {names[k]: fa[k] for k in ["normal", "supply", "load_unknown"]}

    dumbbell(ax_a, d_data, 98, TEAL)
    ax_a.set_xlabel("检出条数（共 80 条）")

    # 两面板统一用同一强调色，避免图例与点色不符
    dumbbell(ax_b, f_data, 98, TEAL)
    ax_b.set_xlabel("误报条数（共 80 条）")

    # 图级图例：两个灰/彩点
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", ms=7, color=GRAY,
                      label="朴素阈值"),
               Line2D([], [], marker="o", ls="", ms=7, color=TEAL,
                      label="本方案")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.012),
               ncol=2, handlelength=0.8, columnspacing=2.4)

    fig.text(0.052, 0.950, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.512, 0.950, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "baseline_compare", W)


# =====================================================================
# 图 7：测量不确定度需求 + 检出时延
# =====================================================================
def fig_uncertainty():
    e9 = json.load(open(os.path.join(RES, "E9_block_threshold.json"), encoding="utf-8"))
    U = e9["U"]
    us = [max(r["U"], 0.01) for r in U]
    det = [int(r["det"].split("/")[0]) for r in U]
    layer = e9["layer"]

    W, H = 7.9, 3.4
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.105, 0.375, 0.605, 0.355,
                            bottom=0.225, height=0.625)

    ax_a.plot(us, det, "o-", color=TEAL, lw=1.5, ms=5, zorder=4)
    ax_a.axhline(38, color=GRAY, ls=(0, (4, 3)), lw=1.0, zorder=1)
    ax_a.set_xscale("log")
    ax_a.set_xlim(0.008, 6)
    ax_a.set_ylim(0, 44)
    ax_a.set_xticks([0.01, 0.05, 0.175, 1, 5], ["0", "0.05", "0.175", "1", "5"])
    ax_a.set_xlabel(r"压力测量不确定度 $U$（kPa）")
    ax_a.set_ylabel("检出条数（共 40 条）")
    ax_a.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_a.set_axisbelow(True)

    for kd, (lab, colr) in {"leak": ("泄漏", TEAL), "restriction": ("受限", BLUE),
                            "drift": ("漂移", RED)}.items():
        pts = sorted((r["sigma"], r["t"]) for r in layer
                     if r["kind"] == kd and r["t"] is not None)
        ax_b.plot([p[0] for p in pts], [p[1] for p in pts], "o-",
                  color=colr, lw=1.3, ms=4.5, label=lab)
    ax_b.set_xscale("log")
    ax_b.set_xlim(0.22, 16)
    ax_b.set_xticks([0.3, 1, 3, 10], ["0.3", "1", "3", "10"])
    ax_b.set_xlabel(r"压力噪声 $\sigma$（kPa）")
    ax_b.set_ylabel("中位检出时延（s）")
    ax_b.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_b.set_axisbelow(True)
    ax_b.legend(loc="upper left", handlelength=1.4, labelspacing=0.6)

    fig.text(0.022, 0.952, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.522, 0.952, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "uncertainty_latency", W)


# =====================================================================
# 图 8：可辨识性 —— 压力跨度决定指数能否辨识
# =====================================================================
def fig_ident():
    span = [1, 2, 5, 10, 20, 50, 100]
    u_01 = [0.1005, 0.0505, 0.0205, 0.0105, 0.0055, 0.0025, 0.0014]
    u_1 = [1.0050, 0.5050, 0.2050, 0.1049, 0.0548, 0.0247, 0.0144]

    W, H = 7.9, 3.4
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.105, 0.375, 0.605, 0.355,
                            bottom=0.225, height=0.625)

    ax_a.plot(span, u_01, "o-", color=BLUE, lw=1.5, ms=5,
              label="流量噪声 0.1%")
    ax_a.plot(span, u_1, "s--", color=ORANGE, lw=1.5, ms=4.5,
              label="流量噪声 1%")
    ax_a.axhline(0.05, color=GRAY, ls=(0, (4, 3)), lw=1.0)
    ax_a.axvline(1, color=VERM, ls=(0, (1.5, 1.8)), lw=1.2)
    ax_a.axvline(20, color=GREEN, ls=(0, (5, 2)), lw=1.2)
    ax_a.set_xscale("log"); ax_a.set_yscale("log")
    ax_a.set_xlim(0.85, 160)
    ax_a.set_ylim(0.0008, 2.2)
    ax_a.set_xticks([1, 2, 5, 10, 20, 50, 100],
                    ["1", "2", "5", "10", "20", "50", "100"])
    ax_a.set_xlabel("压力跨度（相对值，%）")
    ax_a.set_ylabel(r"指数 $n$ 的不确定度")
    ax_a.grid(color=GRAY_L, lw=0.5, alpha=0.7)
    ax_a.set_axisbelow(True)
    ax_a.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2,
                handlelength=1.5, columnspacing=1.4)

    labels = ["单工况\n(跨度 1%)", "跨工况\n(跨度 100%)"]
    dev = [abs(-1.46 - 0.5), abs(0.4755 - 0.5)]
    x = np.arange(2)
    ax_b.bar(x, dev, 0.5, bottom=0.006, color=[VERM, GREEN], zorder=3)
    for xi, v, c in zip(x, dev, [VERM, GREEN]):
        ax_b.text(xi, v * 1.25, "%.2f" % v, ha="center", va="bottom",
                  fontsize=13, color=c)
    ax_b.set_yscale("log")
    ax_b.set_ylim(0.005, 40)
    ax_b.set_xticks(x, labels)
    ax_b.set_ylabel(r"拟合指数偏差 $|n-0.5|$")
    ax_b.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_b.set_axisbelow(True)

    fig.text(0.022, 0.950, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.522, 0.950, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "identifiability", W)


# =====================================================================
# 图 9：传感器增益漂移的容限
# =====================================================================
def fig_gain_drift():
    e10 = json.load(open(os.path.join(RES, "E10_robustness.json"), encoding="utf-8"))
    rows = e10["gain_drift"]

    def find(key):
        for r in rows:
            if r["name"] == key:
                return r
        return None

    W, H = 7.9, 3.4
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.115, 0.320, 0.595, 0.365,
                            bottom=0.265, height=0.585)

    names = ["δ_Q=+1%（Q 增益单漂）", "δ_P1=+1%（表压单漂）",
             "δ_ΔP=+1%（差压单漂）"]
    short = [r"流量 $Q$", r"表压 $P_1$", r"差压 $\Delta P$"]
    cols = [VERM, GREEN, BLUE]
    fars = []
    for n in names:
        r = find(n)
        fars.append(r["far"] * 100 if r else 0)
    x = np.arange(3)
    ax_a.bar(x, fars, 0.5, color=cols, zorder=3)
    for xi, v, c in zip(x, fars, cols):
        ax_a.text(xi, v + 2.2, "%.1f" % v, ha="center", va="bottom",
                  fontsize=13, color=c)
    ax_a.set_xticks(x, short)
    ax_a.set_ylim(0, 108)
    ax_a.set_ylabel("健康段误报率（%）")
    ax_a.set_xlabel("单通道增益漂移 +1%")
    ax_a.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_a.set_axisbelow(True)

    qs = [("δ_Q=+0.5%（温和）", 0.5), ("δ_Q=+1%（Q 增益单漂）", 1.0),
          ("δ_Q=+2%（劣化）", 2.0), ("δ_Q=+5%（严重）", 5.0)]
    xs, ys = [], []
    for n, d in qs:
        r = find(n)
        if r:
            xs.append(d)
            ys.append(r["far"] * 100)
    ax_b.plot(xs, ys, "o-", color=VERM, lw=1.5, ms=5, zorder=4)
    ax_b.set_xlim(0, 5.8)
    ax_b.set_ylim(-4, 112)
    ax_b.set_xlabel(r"$Q$ 通道增益漂移（%）")
    ax_b.set_ylabel("健康段误报率（%）")
    ax_b.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_b.set_axisbelow(True)

    fig.text(0.028, 0.950, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.508, 0.950, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "gain_drift", W)


# =====================================================================
# 图 10：轮灌切换的裕度与故障可检性（E11）
# =====================================================================
def fig_switching():
    e11 = json.load(open(os.path.join(RES, "E11_switching.json"), encoding="utf-8"))
    steady = e11["steady"]
    wl = e11["withleak"]
    H_STAR = e11["h_star"]

    W, H = 7.9, 3.5
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.105, 0.365, 0.595, 0.375,
                            bottom=0.245, height=0.605)

    for dur, colr, mk in [(10, BLUE, "o"), (50, GREEN, "s"), (120, PURPLE, "^")]:
        rows = [r for r in steady if int(r["dur_s"]) == dur]
        if not rows:
            continue
        rows.sort(key=lambda r: r["amp"])
        # 空心标记：三条曲线数值几乎相同而重合，空心可同时看见彼此
        ax_a.plot([r["amp"] * 100 for r in rows], [r["peak"] for r in rows],
                  mk + "-", color=colr, lw=1.2, ms=8, mfc="none", mew=1.5,
                  label="持续 %d s" % dur)
    ax_a.axhline(H_STAR, color=VERM, ls=(0, (5, 2)), lw=1.5)
    ax_a.text(39, H_STAR + 0.7, r"$h^*$=%d" % H_STAR, ha="right", va="bottom",
              fontsize=12, color=VERM)
    ax_a.set_xlim(0, 40)
    ax_a.set_ylim(0, 32)
    ax_a.set_xlabel("切换引起的流量变化（%）")
    ax_a.set_ylabel("健康段累积和峰值")
    ax_a.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_a.set_axisbelow(True)
    ax_a.legend(loc="center left", bbox_to_anchor=(0.01, 0.42),
                handlelength=1.5, labelspacing=0.5)

    durs = [int(r["dur_s"]) for r in wl]
    sw = [r["sw"] for r in wl]
    both = [r["both"] for r in wl]
    x = np.arange(len(durs))
    hb = 0.34
    ax_b.bar(x - hb / 2, sw, hb, color=GRAY, zorder=3, label="仅切换")
    ax_b.bar(x + hb / 2, both, hb, color=GREEN, zorder=3, label="切换 + 泄漏")
    for xi, v in zip(x - hb / 2, sw):
        ax_b.text(xi, v + 1.4, "%d" % v, ha="center", va="bottom",
                  fontsize=13, color=GRAY)
    for xi, v in zip(x + hb / 2, both):
        ax_b.text(xi, v + 1.4, "%d" % v, ha="center", va="bottom",
                  fontsize=13, color=GREEN)
    ax_b.set_xticks(x, [str(d) for d in durs])
    ax_b.set_xlabel("切换持续时间（s）")
    ax_b.set_ylabel("越限条数（共 40 条）")
    ax_b.set_ylim(0, 48)
    ax_b.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax_b.set_axisbelow(True)
    ax_b.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2,
                handlelength=1.5, columnspacing=1.4)

    fig.text(0.022, 0.960, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.512, 0.960, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "switching_margin", W)


# =====================================================================
# 图 11：暂态抑制的代价（检出时延增加）
# =====================================================================
def fig_suppression_cost():
    e4 = json.load(open(os.path.join(RES, "E4_v2.json"), encoding="utf-8"))
    cost = e4["cost"]

    W, H = 7.2, 3.3
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.100, 0.215, 0.700, 0.635])

    for kd, lab, colr in [("leak", "泄漏", BLUE), ("restriction", "受限", GREEN),
                          ("drift", "漂移", VERM)]:
        rows = sorted([r for r in cost if r["kind"] == kd],
                      key=lambda r: r["sigma"])
        sig = [r["sigma"] for r in rows]
        dt = [r["t_masked"] - r["t_raw"] for r in rows]
        ax.plot(sig, dt, "o-", color=colr, lw=1.4, ms=5, label=lab)

    # 只在最大值处标一个数，说明代价量级
    rmax = max(cost, key=lambda r: r["t_masked"] - r["t_raw"])
    vmax = rmax["t_masked"] - rmax["t_raw"]
    ax.text(rmax["sigma"], vmax + 4, "+%d s" % vmax, va="bottom",
            ha="center", fontsize=13, color=GREEN)

    ax.set_xscale("log")
    ax.set_xlim(0.22, 16)
    ax.set_xticks([0.3, 1, 3, 10], ["0.3", "1", "3", "10"])
    ax.set_ylim(-8, 125)
    ax.set_xlabel(r"压力噪声 $\sigma$（kPa）")
    ax.set_ylabel("检出时延增量（s）")
    ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="center left", bbox_to_anchor=(1.015, 0.5),
              handlelength=1.5, labelspacing=0.6)

    return save(fig, "suppression_cost", W)


# =====================================================================
# 图 12：甘特图（时间轴）
# =====================================================================
def fig_gantt():
    W, H = 7.9, 4.3
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.225, 0.135, 0.685, 0.815])
    ax.set_xlim(0, 12)
    ax.set_ylim(-0.6, 12.4)

    # (任务, 起, 止, 阶段色)
    rows = [
        ("器件选型与装配", 0.0, 1.0, BLUE),
        ("跨工况参考标定", 0.8, 1.9, BLUE),
        ("健康关系与分档", 1.2, 2.0, BLUE),
        ("判据与门限", 2.0, 2.9, ORANGE),
        ("工况分档参照", 2.2, 3.2, ORANGE),
        ("54—72 次实验", 3.0, 4.0, ORANGE),
        ("LoRa 链路", 4.0, 5.0, GREEN),
        ("8 小时记录", 5.0, 6.0, GREEN),
        ("重启与恢复", 5.5, 6.3, GREEN),
        ("留出批次与消融", 6.5, 8.5, PURPLE),
        ("论文与软著", 7.0, 11.5, PURPLE),
        ("原型与结题报告", 9.0, 12.0, PURPLE),
    ]
    for i, (name, t0, t1, colr) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, t1 - t0, left=t0, height=0.46, color=colr, zorder=3)

    ax.set_yticks(range(len(rows))[::-1], [r[0] for r in rows])
    ax.tick_params(axis="y", length=0)
    ax.set_xticks([0, 2, 4, 6, 9, 12],
                  ["2027.3", "2027.5", "2027.7", "2027.9", "2027.12", "2028.2"])
    ax.set_xlabel("时间")
    ax.set_ylim(-0.6, 12.4)
    ax.set_axisbelow(True)

    # 阶段分隔线
    for x in (2, 4, 6):
        ax.axvline(x, color=GRAY, ls=(0, (4, 3)), lw=0.9, zorder=1)

    return save(fig, "gantt", W)


# =====================================================================
# 图 13：泳道图（工作类型 × 阶段）
# =====================================================================
def fig_swimlane():
    W, H = 7.9, 4.0
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.008, 0.03, 0.984, 0.90])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    lanes = [
        ("硬件与供电", ["选型·装配", "—", "节点集成", "原型定型"]),
        ("固件与通信", ["采集通路", "判据实现", "LoRa·落库", "续航测试"]),
        ("算法与判据", ["健康关系", "门限·分档", "—", "留出消融"]),
        ("台架实验",   ["静态标定", "54—72 次", "长时记录", "复现试验"]),
        ("文档与成果", ["方案·记录", "数据整理", "测试报告", "论文软著"]),
    ]
    phases = [("阶段一", BLUE), ("阶段二", ORANGE),
              ("阶段三", GREEN), ("阶段四", PURPLE)]

    n_row, n_col = len(lanes), len(phases)
    lab_w = 17.0
    cw = (100.0 - lab_w) / n_col
    hdr_h = 11.0
    top = 100.0 - hdr_h
    rh = (top - 3.0) / n_row

    # 阶段表头
    for j, (pname, colr) in enumerate(phases):
        x = lab_w + j * cw
        ax.add_patch(plt.Rectangle((x + 0.4, top), cw - 1.4, hdr_h - 1.0,
                                   fc=colr, ec="none", gid="card"))
        ax.text(x + cw / 2, top + (hdr_h - 1.0) / 2, pname, ha="center",
                va="center", fontsize=13, weight="bold", color="white")
        if j < n_col - 1:
            ax.add_patch(FancyArrowPatch(
                (x + cw - 1.0, top + (hdr_h - 1.0) / 2),
                (x + cw + 0.4, top + (hdr_h - 1.0) / 2),
                arrowstyle="-|>", mutation_scale=9, color=GRAY, lw=0.9,
                shrinkA=0, shrinkB=0, gid="deco"))

    # 泳道
    for i, (lname, cells) in enumerate(lanes):
        y = top - (i + 1) * rh
        # 泳道底纹（隔行）
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0.4, y + 0.5), 99.2, rh - 1.0,
                                       fc=GRAY_XL, ec="none", zorder=0,
                                       gid="deco"))
        ax.text(1.6, y + rh / 2, lname, ha="left", va="center",
                fontsize=13, weight="bold", color=INK)
        for j, txt in enumerate(cells):
            x = lab_w + j * cw
            active = txt != "—"
            colr = phases[j][1]
            ax.add_patch(plt.Rectangle(
                (x + 1.2, y + rh * 0.22), cw - 2.8, rh * 0.56,
                fc=colr if active else "none",
                ec=colr if active else "none",
                lw=1.0, alpha=0.16 if active else 1.0, zorder=2,
                gid="card"))
            ax.text(x + cw / 2, y + rh / 2, txt, ha="center", va="center",
                    fontsize=12.5 if active else 12,
                    color=INK if active else GRAY, zorder=3)

    return save(fig, "swimlane", W)


# =====================================================================
# 图 14：特征平面 —— 各类扰动在 (ΔK, ΔRh) 上的响应方向
# =====================================================================
def fig_response_plane():
    # 数值取自 E10【4】"各类故障在三个通道上的响应幅度（设计工况均值）"
    pts = [
        ("受限", 0.01, 197.42, BLUE, 8, (11, 4)),
        ("漂移", 0.01, 31.97, GREEN, 8, (11, -3)),
        ("泄漏 ≡ 负载未知", 7.07, 0.08, VERM, 9, (-12, 14)),
        ("供压扰动 / 切换", 0.01, 0.09, GRAY, 8, (14, 7)),
    ]

    W, H = 7.0, 3.9
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.115, 0.20, 0.855, 0.68])

    for lab, dk, dr, colr, ms, off in pts:
        ax.plot([dk], [dr], "o", ms=ms, color=colr, zorder=5,
                markeredgewidth=0)
        ha = "left" if off[0] > 0 else "right"
        va = "bottom" if off[1] > 0 else "top"
        ax.annotate(lab, xy=(dk, dr),
                    xytext=(off[0], off[1]), textcoords="offset points",
                    fontsize=13, color=colr, ha=ha, va=va)

    # 参考线：1% 与 10%
    for v in (1, 10):
        ax.axhline(v, color=GRAY_L, lw=0.6, ls=(0, (4, 4)), zorder=1)
        ax.axvline(v, color=GRAY_L, lw=0.6, ls=(0, (4, 4)), zorder=1)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.006, 20)
    ax.set_ylim(0.04, 400)
    ax.set_xticks([0.01, 0.1, 1, 10], ["0.01", "0.1", "1", "10"])
    ax.set_yticks([0.1, 1, 10, 100], ["0.1", "1", "10", "100"])
    ax.set_xlabel(r"负载系数相对变化 $\Delta K/K$（%）")
    ax.set_ylabel(r"区段阻力相对变化 $\Delta R_h/R_h$（%）")
    ax.grid(color=GRAY_L, lw=0.4, alpha=0.35)
    ax.set_axisbelow(True)

    return save(fig, "response_plane", W)


# =====================================================================
# 图 15：CUSUM 时序示例（健康 vs +5% 泄漏）
# =====================================================================
def fig_cusum_trace():
    import numpy as _np
    P = os.path.join(os.path.dirname(HERE), "cusum_review",
                     "heldout_observations.npz")
    d = _np.load(P)
    obs, ids = d["observed"], d["trial_ids"]
    kind = _np.array([s.split("|")[0] for s in ids])
    i = int(_np.where(kind == "normal")[0][0])

    Wb = 10
    CALB = (2, 18)

    def stat(o, amp=None, b0=30, b1=48):
        n = len(o) // Wb
        z = o[:n * Wb].reshape(n, Wb, 3)
        P0 = z[:, :, 0].mean(1).copy()
        P1 = z[:, :, 1].mean(1).copy()
        Q = z[:, :, 2].mean(1).copy()
        if amp:
            for j in range(b0, min(b1, n)):
                dP = (P0[j] - P1[j]) * (1 + amp) ** 2
                Q[j] *= (1 + amp)
                P0[j] = P1[j] + dP
        K = Q / _np.sqrt(P1)
        Rh = (P0 - P1) / Q ** 2
        c = slice(*CALB)
        kref = _np.nanmedian(K[c]); rref = _np.nanmedian(Rh[c])
        sk = 1.4826 * _np.nanmedian(_np.abs(K[c] - kref))
        sr = 1.4826 * _np.nanmedian(_np.abs(Rh[c] - rref))
        zk = (K - kref) / max(sk, 1e-9)
        zr = (Rh - rref) / max(sr, 1e-9)
        Sk = _np.zeros(n); Sr = _np.zeros(n)
        for j in range(1, n):
            Sk[j] = max(0.0, Sk[j - 1] + zk[j] - 0.5)
            Sr[j] = max(0.0, Sr[j - 1] + zr[j] - 0.5)
        return _np.maximum(Sk, Sr)

    S_h = stat(obs[i])
    S_f = stat(obs[i], amp=0.02)
    t = _np.arange(len(S_h)) * Wb

    W, H = 7.4, 3.5
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.115, 0.225, 0.855, 0.645])

    ax.plot(t, S_h, "-", color=BLUE, lw=1.5, label="健康")
    ax.plot(t, S_f, "-", color=VERM, lw=1.5, label="注入 +2% 泄漏")
    ax.axhline(26, color=GRAY, ls=(0, (5, 3)), lw=1.2)
    ax.text(600, 27.5, r"$h^*$=26", ha="right", va="bottom", fontsize=12,
            color=GRAY)
    # 注入窗口：用图例色块表示，不在数据区放文字（避免压线）
    sp = ax.axvspan(300, 480, color=GRAY_L, alpha=0.45, zorder=0)
    sp.set_gid("deco")

    ax.set_xlim(0, 600)
    ax.set_ylim(0, 62)
    ax.set_xlabel("时间（s）")
    ax.set_ylabel("累积和统计量")
    ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax.set_axisbelow(True)
    from matplotlib.patches import Patch as _P
    h, l = ax.get_legend_handles_labels()
    h.append(_P(facecolor=GRAY_L, alpha=0.45, label="注入窗口"))
    l.append("注入窗口")
    ax.legend(h, l, loc="upper left", handlelength=1.6, labelspacing=0.5)

    return save(fig, "cusum_trace", W)


# =====================================================================
# 图 16：系统总体架构
# =====================================================================
def fig_architecture():
    W, H = 7.9, 4.0
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.008, 0.02, 0.984, 0.96])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    BH = 13.0                     # 框高（容纳两行 12 pt 文字）
    R = [72.0, 52.0, 32.0, 12.0]  # 四行底边

    def box(x, w, y, text, colr, fs=12):
        ax.add_patch(plt.Rectangle((x, y), w, BH, fc="white", ec=colr,
                                   lw=1.2, gid="card"))
        ax.text(x + w / 2, y + BH / 2, text, ha="center", va="center",
                fontsize=fs, color=INK, linespacing=1.3)

    def arrow(x0, y0, x1, y1, ls="-"):
        ax.add_patch(FancyArrowPatch(
            (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=11,
            color=GRAY, lw=1.1, linestyle=ls, shrinkA=0, shrinkB=0,
            gid="deco"))

    # 三组标题
    groups = [("现场：支管节点", BLUE, 2.0, 28.0),
              ("网关", ORANGE, 38.0, 20.0),
              ("机房：接收与平台", GREEN, 66.0, 32.0)]
    for name, colr, x, w in groups:
        ax.plot([x, x + w], [95, 95], color=colr, lw=2.0, solid_capstyle="butt")
        ax.text(x, 88.5, name, ha="left", va="center", fontsize=13,
                weight="bold", color=colr)

    # 组一：节点信号链（自上而下）
    box(2, 28, R[0], "三路传感器", BLUE)
    box(2, 28, R[1], "调理与 ADC", BLUE)
    box(2, 28, R[2], "GD32 主控", BLUE)
    box(2, 28, R[3], "LoRa 模块", BLUE)
    for a, b in [(R[0], R[1] + BH), (R[1], R[2] + BH), (R[2], R[3] + BH)]:
        arrow(16, a, 16, b)

    # 组二：网关（自上而下）
    box(38, 20, R[0], "LoRa 接收", ORANGE)
    box(38, 20, R[1], "串口转以太网", ORANGE)
    arrow(48, R[0], 48, R[1] + BH)

    # 无线链路：节点 LoRa → 网关 LoRa（虚线）
    arrow(30, R[3] + BH / 2, 38, R[0] + BH / 2, ls=(0, (5, 3)))

    # 组三：平台
    box(66, 14, R[1], "接收服务", GREEN)
    box(84, 14, R[1], "数据库", GREEN)
    box(66, 14, R[2], "巡检平台", GREEN)
    box(84, 14, R[2], "异常列表", GREEN)
    arrow(58, R[1] + BH / 2, 66, R[1] + BH / 2)
    arrow(80, R[1] + BH / 2, 84, R[1] + BH / 2)
    arrow(73, R[1], 73, R[2] + BH)
    arrow(80, R[2] + BH / 2, 84, R[2] + BH / 2)

    ax.text(2, 3.5, "供电：锂电池组 + DC-DC；无线为 LoRa，发射功率 ≤10 dBm",
            ha="left", va="center", fontsize=12, color=GRAY)

    return save(fig, "architecture", W)


# =====================================================================
# 仿真输出图公共：载入轨迹
# =====================================================================
_NPZ = os.path.join(os.path.dirname(HERE), "cusum_review",
                    "heldout_observations.npz")


def _load_traj():
    import numpy as _np
    d = _np.load(_NPZ)
    return d["observed"], d["trial_ids"]


def _pick(ids, kind, sig="1"):
    for i, s in enumerate(ids):
        if s.startswith(kind + "|" + sig + "|"):
            return i
    return None


def _resid_series(o, amp=None, b0=30, b1=48):
    """块级残差 z_q、z_r（供时序/散点图复用）。"""
    import numpy as _np
    Wb = 10
    n = len(o) // Wb
    z = o[:n * Wb].reshape(n, Wb, 3)
    P0 = z[:, :, 0].mean(1).copy()
    P1 = z[:, :, 1].mean(1).copy()
    Q = z[:, :, 2].mean(1).copy()
    if amp:
        for j in range(b0, min(b1, n)):
            dP = (P0[j] - P1[j]) * (1 + amp) ** 2
            Q[j] *= (1 + amp)
            P0[j] = P1[j] + dP
    K = Q / _np.sqrt(P1)
    Rh = (P0 - P1) / Q ** 2
    c = slice(2, 18)
    kref = _np.nanmedian(K[c]); rref = _np.nanmedian(Rh[c])
    sk = 1.4826 * _np.nanmedian(_np.abs(K[c] - kref))
    sr = 1.4826 * _np.nanmedian(_np.abs(Rh[c] - rref))
    return (_np.arange(n) * Wb, (K - kref) / max(sk, 1e-9),
            (Rh - rref) / max(sr, 1e-9))


# =====================================================================
# 图 17：三通道时域波形（健康 / 泄漏 / 受限）
# =====================================================================
def fig_waveforms():
    obs, ids = _load_traj()
    i_n, i_l, i_r = (_pick(ids, "normal"), _pick(ids, "leak"),
                     _pick(ids, "restriction"))
    t = np.arange(obs.shape[1])

    W, H = 7.6, 4.9
    fig = plt.figure(figsize=(W, H))
    axes = []
    for k in range(3):
        ax = fig.add_axes([0.105, 0.605 - k * 0.245, 0.795, 0.185])
        axes.append(ax)
        sp = ax.axvspan(360, 600, color=GRAY_L, alpha=0.40, zorder=0)
        sp.set_gid("deco")
        ax.plot(t, obs[i_n][:, k], "-", color=BLUE, lw=1.2, label="健康")
        ax.plot(t, obs[i_l][:, k], "-", color=VERM, lw=1.2, label="等效泄漏")
        ax.plot(t, obs[i_r][:, k], "-", color=GREEN, lw=1.2, label="等效受限")
        ax.set_xlim(0, 600)
        ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(labelbottom=(k == 2))

    axes[0].set_ylabel(r"$P_0$（kPa）")
    axes[1].set_ylabel(r"$P_1$（kPa）")
    axes[2].set_ylabel(r"$Q$（L/min）")
    axes[2].set_xlabel("时间（s）")

    # 图级图例置顶，避免压曲线
    hh, ll = axes[0].get_legend_handles_labels()
    fig.legend(hh, ll, loc="upper center", bbox_to_anchor=(0.55, 0.985),
               ncol=3, handlelength=1.8, columnspacing=2.4)

    for tag, ax in zip(["a", "b", "c"], axes):
        fig.text(0.012, ax.get_position().y1 + 0.008, tag, fontsize=13,
                 weight="bold", va="bottom")

    return save(fig, "waveforms", W)


# =====================================================================
# 图 18：P1–Q 散点（双对数）——单测点看不出受限
# =====================================================================
def fig_pq_scatter():
    obs, ids = _load_traj()
    i_n, i_l, i_r = (_pick(ids, "normal"), _pick(ids, "leak"),
                     _pick(ids, "restriction"))

    W, H = 7.2, 4.2
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.115, 0.175, 0.855, 0.72])

    p1 = np.linspace(70, 120, 200)
    ax.plot(p1, 0.28 * np.sqrt(p1), "-", color=GRAY, lw=1.4, zorder=2,
            label=r"健康关系 $Q=C\sqrt{P_1}$")

    for i, lab, colr, mk in [(i_n, "健康", BLUE, "o"),
                             (i_r, "等效受限", GREEN, "^"),
                             (i_l, "等效泄漏", VERM, "s")]:
        o = obs[i]
        ax.plot(o[::4, 1], o[::4, 2], mk, ms=3.2, color=colr, alpha=0.55,
                markeredgewidth=0, label=lab, zorder=3)

    ax.set_xlim(70, 120)
    ax.set_ylim(2.2, 4.0)
    ax.set_yticks([2.5, 3.0, 3.5, 4.0], ["2.5", "3.0", "3.5", "4.0"])
    ax.set_xlabel(r"下游压力 $P_1$（kPa）")
    ax.set_ylabel(r"支管流量 $Q$（L/min）")
    ax.grid(color=GRAY_L, lw=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", handlelength=1.4, labelspacing=0.5,
              markerscale=2.2)

    return save(fig, "pq_scatter", W)


# =====================================================================
# 图 19：块级残差时序（z_q / z_r）
# =====================================================================
def fig_residual_trace():
    obs, ids = _load_traj()
    i = _pick(ids, "normal")

    W, H = 7.6, 4.2
    fig = plt.figure(figsize=(W, H))
    ax1 = fig.add_axes([0.115, 0.575, 0.795, 0.335])
    ax2 = fig.add_axes([0.115, 0.155, 0.795, 0.335])

    tb, zq_h, zr_h = _resid_series(obs[i])
    _, zq_f, zr_f = _resid_series(obs[i], amp=0.02)

    for ax, zh, zf, ylab in [(ax1, zq_h, zq_f, r"$z_Q$（K 通道）"),
                             (ax2, zr_h, zr_f, r"$z_R$（Rh 通道）")]:
        ax.axhspan(-3, 3, color=GRAY_L, alpha=0.40, zorder=0)
        ax.axhline(0, color=GRAY, lw=0.8, zorder=1)
        ax.plot(tb, zh, "-", color=BLUE, lw=1.0, label="健康")
        ax.plot(tb, zf, ls=(0, (5, 2)), color=VERM, lw=1.2,
                label="注入 +2% 泄漏")
        ax.set_xlim(0, 600)
        ax.set_ylim(-6, 14)
        ax.set_ylabel(ylab)
        ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(labelbottom=(ax is ax2))
        ax.text(595, 3.4, r"$\pm3\sigma$", ha="right", va="bottom", fontsize=12,
                color=GRAY)

    ax2.set_xlabel("时间（s）")
    hh, ll = ax1.get_legend_handles_labels()
    fig.legend(hh, ll, loc="upper center", bbox_to_anchor=(0.55, 0.985),
               ncol=2, handlelength=1.8, columnspacing=2.4)

    fig.text(0.014, 0.918, "a", fontsize=13, weight="bold", va="top")
    fig.text(0.014, 0.458, "b", fontsize=13, weight="bold", va="top")
    return save(fig, "residual_trace", W)


# =====================================================================
# 图 20：健康段峰值分布直方图 + 冻结门限
# =====================================================================
def fig_peak_hist():
    obs, ids = _load_traj()
    idx = [i for i, s in enumerate(ids) if s.startswith("normal|")]
    peaks = []
    for i in idx:
        tb, zq, zr = _resid_series(obs[i])
        Sk = np.zeros(len(zq)); Sr = np.zeros(len(zq))
        for j in range(1, len(zq)):
            Sk[j] = max(0.0, Sk[j - 1] + zq[j] - 0.5)
            Sr[j] = max(0.0, Sr[j - 1] + zr[j] - 0.5)
        peaks.append(np.max(np.maximum(Sk, Sr)[18:]))
    peaks = np.array(peaks)

    W, H = 6.8, 3.6
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.115, 0.185, 0.855, 0.71])

    # 分箱右边界正好取 26，避免最后一根柱子跨过门限线造成"有样本超限"的误读
    bins = np.linspace(0, 26, 17)
    ax.hist(peaks, bins=bins, color=BLUE, alpha=0.55, edgecolor="white",
            linewidth=0.6, zorder=3)
    ax.axvline(26, color=VERM, ls=(0, (5, 3)), lw=1.6, zorder=4)
    ax.text(26.4, ax.get_ylim()[1] * 0.86, r"$h^*$=26", ha="left", va="top",
            fontsize=13, color=VERM)

    ax.set_xlim(0, 30)
    ax.set_xlabel("健康段累积和峰值")
    ax.set_ylabel("轨迹条数")
    ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax.set_axisbelow(True)

    return save(fig, "peak_hist", W)


# =====================================================================
# 图 21：箱线图 —— 各类扰动的累积和峰值分布
# =====================================================================
def _peak_by_kind():
    obs, ids = _load_traj()
    out = {}
    for kd in ["normal", "supply", "drift", "restriction", "leak",
               "load_unknown"]:
        idx = [i for i, s in enumerate(ids) if s.startswith(kd + "|")]
        pk = []
        for i in idx[:40]:
            tb, zq, zr = _resid_series(obs[i])
            Sk = np.zeros(len(zq)); Sr = np.zeros(len(zq))
            for j in range(1, len(zq)):
                Sk[j] = max(0.0, Sk[j - 1] + zq[j] - 0.5)
                Sr[j] = max(0.0, Sr[j - 1] + zr[j] - 0.5)
            pk.append(np.max(np.maximum(Sk, Sr)[36:]))
        out[kd] = np.array(pk)
    return out


def fig_peak_box():
    d = _peak_by_kind()
    names = {"normal": "正常", "supply": "供压扰动", "drift": "漂移",
             "restriction": "受限", "leak": "泄漏",
             "load_unknown": "负载未知"}
    order = ["normal", "supply", "drift", "restriction", "leak",
             "load_unknown"]
    cols = [GRAY, PURPLE, GREEN, BLUE, VERM, ORANGE]

    W, H = 7.4, 3.9
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.105, 0.215, 0.855, 0.66])

    bp = ax.boxplot([d[k] for k in order], patch_artist=True, widths=0.55,
                    medianprops=dict(color="white", lw=1.4),
                    flierprops=dict(marker="o", ms=3.5, mfc="none",
                                    mec=GRAY, mew=0.8),
                    whiskerprops=dict(color=GRAY, lw=0.9),
                    capprops=dict(color=GRAY, lw=0.9))
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c); patch.set_alpha(0.65); patch.set_edgecolor(c)
        patch.set_linewidth(1.0)

    ax.axhline(26, color=VERM, ls=(0, (5, 3)), lw=1.5, zorder=1)
    ax.text(6.45, 27.5, r"$h^*$=26", ha="right", va="bottom", fontsize=12,
            color=VERM)
    ax.set_yscale("log")
    ax.set_ylim(2, 20000)
    ax.set_xticks(range(1, 7), [names[k] for k in order])
    ax.set_ylabel("累积和峰值")
    ax.grid(axis="y", color=GRAY_L, lw=0.5, alpha=0.8)
    ax.set_axisbelow(True)

    return save(fig, "peak_box", W)


# =====================================================================
# 图 22：等高线图 —— 检出率随幅度与时长的变化
# =====================================================================
def fig_contour():
    e9 = json.load(open(os.path.join(RES, "E9_block_threshold.json"), encoding="utf-8"))
    W, H = 7.9, 3.8
    fig = plt.figure(figsize=(W, H))
    ax_a, ax_b = two_panels(fig, 0.105, 0.285, 0.575, 0.285,
                            bottom=0.215, height=0.665)

    panels = [(ax_a, "a", e9["grid"], "泄漏幅度（%）", 0.02),
              (ax_b, "b", e9["grid_restriction"], "受限幅度（%）", 0.50)]
    levels = [0, 20, 40, 60, 80, 100]
    cmap = plt.get_cmap(CMAP_SEQ)

    for ax, tag, grid, ylab, edge in panels:
        amps, durs, Z = _grid_matrix(grid)
        X, Y = np.meshgrid(durs, np.arange(len(amps)))
        cf = ax.contourf(X, Y, Z, levels=levels, cmap=cmap)
        ax.contour(X, Y, Z, levels=levels[1:-1], colors="white", linewidths=1.0)
        if edge in amps:
            ax.axhline(amps.index(edge), color=VERM, ls=(0, (5, 3)), lw=1.5)
        ax.set_yticks(range(len(amps)), ["%g" % (a * 100) for a in amps])
        ax.set_xticks(durs, [str(int(d) * 10) for d in durs])
        ax.set_ylim(-0.5, len(amps) - 0.5)
        ax.set_xlabel("持续时间（s）")
        ax.set_ylabel(ylab)
        ax.tick_params(length=3)
        cb = mark_colorbar(fig.colorbar(cf, ax=ax, fraction=0.042, pad=0.02,
                                        ticks=levels))
        cb.set_label("检出率（%）", fontsize=12, labelpad=2)
        cb.ax.tick_params(labelsize=12, length=2, width=0.6)
        cb.outline.set_linewidth(0.5)
        cb.outline.set_edgecolor(GRAY)
        fig.text(ax.get_position().x0 - 0.058, 0.895, tag, fontsize=13,
                 weight="bold", va="top")

    return save(fig, "contour_boundary", W)


# =====================================================================
# 图 23：混淆矩阵 —— 真值类别 × 哪个通道先越限
# =====================================================================
def fig_confusion():
    obs, ids = _load_traj()
    kinds = ["normal", "supply", "drift", "restriction", "leak",
             "load_unknown"]
    out_cols = ["无告警", "K 通道", "Rh 通道", "双通道"]
    M = np.zeros((len(kinds), len(out_cols)), int)

    for ri, kd in enumerate(kinds):
        idx = [i for i, s in enumerate(ids) if s.startswith(kd + "|")]
        for i in idx[:40]:
            tb, zq, zr = _resid_series(obs[i])
            Sk = np.zeros(len(zq)); Sr = np.zeros(len(zq))
            for j in range(1, len(zq)):
                Sk[j] = max(0.0, Sk[j - 1] + zq[j] - 0.5)
                Sr[j] = max(0.0, Sr[j - 1] + zr[j] - 0.5)
            mk = np.max(Sk[36:]) > 26
            mr = np.max(Sr[36:]) > 26
            ci = 3 if (mk and mr) else (1 if mk else (2 if mr else 0))
            M[ri, ci] += 1

    rowsum = M.sum(1, keepdims=True)
    R = M / np.maximum(rowsum, 1) * 100

    names = {"normal": "正常", "supply": "供压扰动", "drift": "漂移",
             "restriction": "受限", "leak": "泄漏",
             "load_unknown": "负载未知"}

    W, H = 7.4, 3.9
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.180, 0.245, 0.600, 0.645])

    im = ax.imshow(R, cmap=CMAP_SEQ, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(out_cols)), out_cols)
    ax.set_yticks(range(len(kinds)), [names[k] for k in kinds])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks(np.arange(len(out_cols) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(kinds) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="white", lw=1.6)
    ax.tick_params(which="both", length=0)

    for i in range(len(kinds)):
        for j in range(len(out_cols)):
            rgba = plt.get_cmap(CMAP_SEQ)(R[i, j] / 100.0)
            lum = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
            ax.text(j, i, "%d%%" % round(R[i, j]), ha="center", va="center",
                    fontsize=13, color="white" if lum < 0.5 else INK)

    cb = mark_colorbar(fig.colorbar(im, ax=ax, fraction=0.042, pad=0.02,
                                    ticks=[0, 25, 50, 75, 100]))
    cb.set_label("占该行比例（%）", fontsize=12, labelpad=3)
    cb.ax.tick_params(labelsize=12, length=2, width=0.6)
    cb.outline.set_linewidth(0.5)
    cb.outline.set_edgecolor(GRAY)

    return save(fig, "confusion_matrix", W, ignore_inside=tuple("0123456789%"))


if __name__ == "__main__":
    print("配图全套（23 张，严格校验 + 面板对齐）：")
    probs = []
    for fn in (fig_roadmap, fig_gantt, fig_swimlane,
               fig_architecture, fig_threshold, fig_boundary, fig_noise_tau,
               fig_ceff_drift, fig_baseline, fig_uncertainty,
               fig_ident, fig_gain_drift, fig_switching, fig_suppression_cost,
               fig_response_plane, fig_cusum_trace,
               fig_waveforms, fig_pq_scatter, fig_residual_trace,
               fig_peak_hist, fig_peak_box, fig_contour, fig_confusion):
        probs += fn()
    print("\n问题合计 %d 处" % len(probs))
