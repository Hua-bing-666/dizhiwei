# -*- coding: utf-8 -*-
"""技术路线图 · 单色学术版（申报书第三部分直接插入用）。

与 simulation/project_review/figures/roadmap.png（彩色四阶段版）的区别：
  - 单色：只用黑/白/灰，激光打印和黑白复印不丢信息；
  - 六环节：与《技术路线_申报书版》的环节划分一致，不是四阶段；
  - 画布 9 in 宽、全文字号 >=15 pt：插入 A4 纵向正文（约 420 pt 宽）时，
    最小字号仍有 15*420/648 = 9.7 pt，符合项目"主要字号 >=9.5 pt @420pt"
    的既有约定（彩色版 13.2 in 只有 5.7 pt）。
输出：deliverables/技术路线图_单色学术版.svg / .png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei'],
    'axes.unicode_minus': False,
    'svg.fonttype': 'none',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'deliverables')
os.makedirs(OUT, exist_ok=True)

INK = "#1a1a1a"
GRAY = "#555555"
FAINT = "#f2f2f2"

# 六环节：编号、名称、回答的问题、关键结论（现行口径）、产出
BLOCKS = [
    ("一", "现场与场景", "在哪、为谁做？",
     "监测对象落到支管；阿拉尔 25 万亩自动化灌溉",
     "场景边界与故障定义"),
    ("二", "测量与采集", "测得准不准？",
     "差压 0—40 kPa / ±0.5%FS + 干管参照 + 脉冲流量",
     "测点与采样契约"),
    ("三", "建模与标定", "基准怎么定？",
     "Q=C·P1^n、ΔP=R·Q²；固定 n=0.5，跨 ≥20% 跨度标定",
     "健康参照与残差尺度"),
    ("四", "判据与验证", "判得准不准？",
     "10 s 不重叠块 CUSUM，h*=26；泄漏 +2% / 受限 +50%",
     "误报率与可检边界"),
    ("五", "通信与平台", "怎么传到人？",
     "LoRa ≤10 dBm；帧 55/57/24 B；提交后 ACK；SD 卡可导回",
     "发收日志与事件链"),
    ("六", "实验与成果", "结论怎么可信？",
     "台架为主 54—72 次注入；保底 / 标准 / 加分三档",
     "数据集与原型"),
]

F_TITLE, F_SUB, F_BLOCK, F_CONC, F_TAG, F_FOOT = 19, 15, 15.5, 15, 15, 15


def build():
    fig = plt.figure(figsize=(9.0, 7.8))
    ax = fig.add_axes([.045, .065, .915, .84])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    fig.text(.045, .968, "图D　项目技术路线（单色学术版）",
             fontsize=F_TITLE, weight='bold', va='top', color=INK)
    fig.text(.045, .925,
             "六环节递进：上一环节的产出即下一环节的输入",
             fontsize=F_SUB, va='top', color=GRAY)

    n = len(BLOCKS)
    top, bottom = 87.0, 5.0
    slot = (top - bottom) / n
    h = slot * 0.78
    x0, w = 13.0, 74.0

    for i, (num, name, question, conclusion, output) in enumerate(BLOCKS):
        y = top - (i + 1) * slot + (slot - h) / 2
        fill = FAINT if i % 2 == 0 else "white"
        ax.add_patch(FancyBboxPatch((x0, y), w, h,
                                    boxstyle="round,pad=0.3,rounding_size=0.8",
                                    fc=fill, ec=INK, lw=1.6))
        # 编号徽标（白底黑圈）
        ax.add_patch(Circle((x0 - 6.2, y + h / 2), 4.2, fc="white", ec=INK, lw=1.8))
        ax.text(x0 - 6.2, y + h / 2 - 0.9, num, ha="center", va="center",
                fontsize=F_BLOCK, weight="bold", color=INK)
        # 第一行：左=环节名+问题，右=产出
        ax.text(x0 + 2.2, y + h - 0.9, "%s　· %s" % (name, question),
                ha="left", va="top", fontsize=F_BLOCK, weight="bold", color=INK)
        ax.text(x0 + w - 2.2, y + h - 1.0, "产出：" + output,
                ha="right", va="top", fontsize=F_TAG, color=GRAY)
        # 第二行：关键结论
        ax.text(x0 + 2.2, y + h * 0.30, conclusion,
                ha="left", va="center", fontsize=F_CONC, color=INK)
        # 环节间箭头
        if i < n - 1:
            ax.add_patch(FancyArrowPatch((x0 + w / 2, y - 0.4),
                                         (x0 + w / 2, y - (slot - h) + 0.4),
                                         arrowstyle="-|>", mutation_scale=14,
                                         color=INK, lw=1.6))

    return fig


def _hidden_tick_labels(fig):
    hidden = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = axis.get_view_interval()
            for tick in axis.get_major_ticks():
                loc = tick.get_loc()
                if not (min(lo, hi) <= loc <= max(lo, hi)):
                    hidden.add(id(tick.label1)); hidden.add(id(tick.label2))
    return hidden


def verify(fig, name):
    import matplotlib.text as mtext
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    hidden = _hidden_tick_labels(fig)
    items = []
    for t in fig.findobj(mtext.Text):
        s = t.get_text()
        if not s.strip() or not t.get_visible() or id(t) in hidden:
            continue
        bb = t.get_window_extent(renderer=r)
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


if __name__ == "__main__":
    fig = build()
    verify(fig, "roadmap_monochrome")
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(OUT, "技术路线图_单色学术版." + ext),
                    dpi=150, facecolor="white")
    plt.close(fig)
    print("输出目录:", os.path.abspath(OUT))
