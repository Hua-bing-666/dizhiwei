import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.dirname(os.path.abspath(__file__))
LW = 2.0


def res_h(ax, x, y, w=0.75, h=0.26):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, lw=LW))


def res_v(ax, x, y, h=0.75, w=0.26):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, lw=LW))


def cap_v(ax, x, y, gap=0.16, w=0.32):
    ax.plot([x - w, x + w], [y + gap, y + gap], color="k", lw=LW)
    ax.plot([x - w, x + w], [y - gap, y - gap], color="k", lw=LW)


fig, ax = plt.subplots(figsize=(10.0, 4.8), dpi=220)
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis("off")

GY = 1.35
# 端子
ax.add_patch(FancyBboxPatch((0.9, 1.9), 0.7, 3.2, boxstyle="round,pad=0.02", fill=False, lw=LW))
for y, lab, col in [(4.55, "VCC  红线", "#c0392b"), (3.85, "GND  黑线", "#111111"),
                    (3.15, "OUT  绿线", "#1e8449")]:
    ax.plot([1.6, 2.15], [y, y], color="k", lw=LW)
    ax.text(2.2, y + 0.30, lab, ha="left", fontsize=8.5, color=col)

ax.text(1.28, 1.62, "SEN0549", ha="center", fontsize=9.5, weight="bold")

# VCC
ax.plot([2.15, 2.75], [4.55, 4.55], color="k", lw=LW)
ax.text(2.75, 4.78, "+5 V", fontsize=11, weight="bold")

# GND
ax.plot([2.15, 2.45], [3.85, 3.85], color="k", lw=LW)
ax.plot([2.45, 2.45], [3.85, GY], color="k", lw=LW)

# OUT -> R1 -> node
ax.plot([2.15, 3.25], [3.15, 3.15], color="k", lw=LW)
res_h(ax, 3.62, 3.15)
ax.plot([4.0, 4.9], [3.15, 3.15], color="k", lw=LW)

# 分压 R2
ax.plot([4.9, 4.9], [GY, 3.15], color="k", lw=LW)
res_v(ax, 4.9, 2.35)
ax.text(3.62, 3.55, "R1 10 kΩ", fontsize=9, ha="center")
ax.text(5.12, 2.62, "R2 20 kΩ", fontsize=9, va="center")

# 滤波电容
ax.plot([4.9, 5.75], [3.15, 3.15], color="k", lw=LW)
ax.plot([5.75, 5.75], [GY, 3.15], color="k", lw=LW)
cap_v(ax, 5.75, 2.35)
ax.text(6.0, 2.15, "C 100 nF", fontsize=8.5, va="top", ha="left")

# 到 MCU
ax.plot([5.75, 7.4], [3.15, 3.15], color="k", lw=LW)
ax.plot([4.9], [3.15], marker="o", ms=6, color="k")

ax.add_patch(FancyBboxPatch((7.4, 2.35), 2.9, 1.7, boxstyle="round,pad=0.02", fill=False, lw=LW))
ax.text(8.85, 3.75, "GD32F103CBT6", ha="center", fontsize=10, weight="bold")
ax.text(8.85, 3.05, "PA0 / TIMER1_CH0", ha="center", fontsize=9.5)
ax.text(8.85, 2.65, "（输入捕获计数）", ha="center", fontsize=8.5)

# 地轨
ax.plot([2.45, 8.0], [GY, GY], color="k", lw=LW)
for xx in [2.45, 4.9, 5.75]:
    ax.plot([xx], [GY], marker="o", ms=5, color="k")
gx = 7.0
ax.plot([gx, gx], [GY, GY - 0.22], color="k", lw=LW)
ax.plot([gx - 0.22, gx + 0.22], [GY - 0.22, GY - 0.22], color="k", lw=LW)
ax.plot([gx - 0.13, gx + 0.13], [GY - 0.33, GY - 0.33], color="k", lw=LW)

ax.text(6.0, 5.55, "SEN0549 脉冲输出接入主控（5 V 供电 + 电阻分压至 3.3 V）",
        ha="center", fontsize=11.5, weight="bold")
ax.text(6.0, 0.62, "官方输出高电平 > 4.7 V（5 V 供电），GD32 为 3.3 V 系统，必须分压；"
                   "R1 10 kΩ / R2 20 kΩ 得 3.3 V，配 100 nF 抑制毛刺",
        ha="center", fontsize=8.5, color="#444444")
ax.text(6.0, 0.28, "本图为项目自绘，非 DFRobot 官方资料；官方仅给出三线色定义",
        ha="center", fontsize=8.5, color="#b03030")

fig.savefig(os.path.join(OUT, "SEN0549_接口电路_5V转3.3V分压.png"), bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print("done")
