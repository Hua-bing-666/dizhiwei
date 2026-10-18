import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Arc
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.dirname(os.path.abspath(__file__))
LW = 2.0


def ic_box(ax, x0, x1, y0, y1):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=LW * 1.4))


def cap(ax, x, y, vertical=True, gap=0.16, w=0.32):
    if vertical:
        ax.plot([x - w, x + w], [y + gap, y + gap], color="k", lw=LW)
        ax.plot([x - w, x + w], [y - gap, y - gap], color="k", lw=LW)
    else:
        ax.plot([x - gap, x - gap], [y - w, y + w], color="k", lw=LW)
        ax.plot([x + gap, x + gap], [y - w, y + w], color="k", lw=LW)


def res(ax, x, y, h=0.62, w=0.26):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, lw=LW))


def ind(ax, x0, x1, y, n=4):
    r = (x1 - x0) / (2 * n)
    for i in range(n):
        ax.add_patch(Arc((x0 + r * (2 * i + 1), y), 2 * r, 2 * r,
                         theta1=0, theta2=180, lw=LW))


def diode(ax, x, yc, h=0.36):
    ax.add_patch(Polygon([[x - 0.26, yc - h / 2], [x + 0.26, yc - h / 2], [x, yc + h / 2]],
                         closed=True, fill=False, lw=LW))
    ax.plot([x - 0.26, x + 0.26], [yc + h / 2, yc + h / 2], color="k", lw=LW)


# ================= 图 1：引脚图 =================
fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=220)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")

ic_box(ax, 3.4, 6.6, 1.7, 4.4)
ax.text(5.0, 3.35, "MP2359", ha="center", va="center", fontsize=17, weight="bold")
ax.text(5.0, 2.95, "TSOT23-6 / SOT23-6", ha="center", va="center", fontsize=9.5)
ax.text(5.0, 2.62, "（顶视 / TOP VIEW）", ha="center", va="center", fontsize=9.5)
ax.plot([3.78], [4.05], marker="o", ms=8, color="k")

left = [("1", "BST", 3.72), ("2", "GND", 3.05), ("3", "FB", 2.38)]
right = [("6", "SW", 3.72), ("5", "IN", 3.05), ("4", "EN", 2.38)]

for num, name, y in left:
    ax.plot([2.75, 3.4], [y, y], color="k", lw=LW * 2.2)
    ax.text(3.58, y, num, ha="left", va="center", fontsize=11)
    ax.text(2.6, y, name, ha="right", va="center", fontsize=13)

for num, name, y in right:
    ax.plot([6.6, 7.25], [y, y], color="k", lw=LW * 2.2)
    ax.text(6.42, y, num, ha="right", va="center", fontsize=11)
    ax.text(7.4, y, name, ha="left", va="center", fontsize=13)

ax.text(5.0, 0.6, "依据 MPS《MP2359 Datasheet》Rev.1.21 Pin Functions 表绘制",
        ha="center", va="center", fontsize=9, color="#444444")
fig.savefig(os.path.join(OUT, "MP2359_引脚图_重绘.png"), bbox_inches="tight", facecolor="white")
plt.close(fig)

# ================= 图 2：典型应用电路 =================
fig, ax = plt.subplots(figsize=(11.0, 6.0), dpi=220)
ax.set_xlim(0, 13.0)
ax.set_ylim(0, 7.2)
ax.axis("off")

GNDY = 1.25
x0, x1, y0, y1 = 4.2, 7.0, 2.5, 5.3
IN_Y, EN_Y, SW_Y, FB_Y = 4.75, 3.05, 4.75, 3.05
BST_X, GND_X = 5.05, 6.1

ic_box(ax, x0, x1, y0, y1)
ax.text(5.6, 4.02, "MP2359", ha="center", va="center", fontsize=15, weight="bold")
ax.text(5.6, 3.62, "U1", ha="center", va="center", fontsize=9.5)

ax.text(x0 + 0.1, IN_Y + 0.17, "5 IN", fontsize=10)
ax.text(x0 + 0.1, EN_Y + 0.17, "4 EN", fontsize=10)
ax.text(x1 - 0.1, SW_Y + 0.17, "6 SW", fontsize=10, ha="right")
ax.text(x1 - 0.1, FB_Y + 0.17, "3 FB", fontsize=10, ha="right")
ax.text(BST_X + 0.1, y1 - 0.32, "1 BST", fontsize=10, ha="left")
ax.text(GND_X + 0.1, y0 + 0.14, "2 GND", fontsize=10, ha="left")

# 输入
ax.plot([0.9, x0], [IN_Y, IN_Y], color="k", lw=LW)
ax.text(0.9, IN_Y + 0.30, "VIN 5 V", ha="center", fontsize=12, weight="bold")
ax.plot([1.85, 1.85], [GNDY, IN_Y], color="k", lw=LW)
cap(ax, 1.85, 3.35)
ax.text(2.07, 3.52, "C1\n10 μF", fontsize=9.5, va="bottom")

# EN
ax.plot([x0, 3.35], [EN_Y, EN_Y], color="k", lw=LW)
ax.plot([3.35, 3.35], [EN_Y, 3.6], color="k", lw=LW)
res(ax, 3.35, 3.92)
ax.plot([3.35, 3.35], [4.24, IN_Y], color="k", lw=LW)
ax.text(3.55, 3.92, "R_EN\n100 kΩ", fontsize=9.5, va="center")

# BST 与自举电容
ax.plot([BST_X, BST_X], [y1, 5.55], color="k", lw=LW)
cap(ax, BST_X, 5.72)
ax.plot([BST_X, BST_X], [5.88, 6.35], color="k", lw=LW)
ax.plot([BST_X, 7.30], [6.35, 6.35], color="k", lw=LW)
ax.plot([7.30, 7.30], [6.35, SW_Y], color="k", lw=LW)
ax.text(5.32, 6.05, "C_B 10 nF", fontsize=9.5, va="center")

# SW 主线
ax.plot([x1, 10.95], [SW_Y, SW_Y], color="k", lw=LW)
ind(ax, 8.15, 9.25, SW_Y)
ax.text(8.7, SW_Y + 0.30, "L1 4.7 μH", fontsize=9.5, ha="center")

# D1
ax.plot([7.55, 7.55], [GNDY, SW_Y], color="k", lw=LW)
diode(ax, 7.55, 2.62)
ax.text(7.72, 1.62, "D1\nB230A", fontsize=9.5, ha="left")

# 输出电容
ax.plot([9.65, 9.65], [GNDY, SW_Y], color="k", lw=LW)
cap(ax, 9.65, 3.45)
ax.text(9.87, 3.62, "C2\n22 μF", fontsize=9.5, va="bottom")

# 分压
ax.plot([10.95, 10.95], [GNDY, SW_Y], color="k", lw=LW)
res(ax, 10.95, 4.17)
ax.text(11.16, 4.17, "R1\n49.9 kΩ", fontsize=9.5, va="center")
res(ax, 10.95, 2.30)
ax.text(11.16, 2.30, "R2\n16.2 kΩ", fontsize=9.5, va="center")
ax.plot([10.95], [FB_Y], marker="o", ms=6, color="k")

ax.text(10.95, 5.35, "VOUT 3.3 V", fontsize=12, weight="bold", ha="center")

# FB 取样（走下方，避开器件）
ax.plot([x1, 7.15], [FB_Y, FB_Y], color="k", lw=LW)
ax.plot([7.15, 7.15], [FB_Y, 2.15], color="k", lw=LW)
ax.plot([7.15, 10.95], [2.15, 2.15], color="k", lw=LW)
ax.plot([10.95, 10.95], [2.15, FB_Y], color="k", lw=LW)

# 地轨
ax.plot([1.85, 10.95], [GNDY, GNDY], color="k", lw=LW)
ax.plot([GND_X, GND_X], [y0, GNDY], color="k", lw=LW)
for xx in [1.85, GND_X, 7.55, 9.65, 10.95]:
    ax.plot([xx], [GNDY], marker="o", ms=5, color="k")
ax.plot([1.85], [IN_Y], marker="o", ms=5, color="k")
for xx in [7.30, 7.55, 9.65]:
    ax.plot([xx], [SW_Y], marker="o", ms=5, color="k")

# 地符号
gx = 1.85
ax.plot([gx, gx], [GNDY, GNDY - 0.24], color="k", lw=LW)
ax.plot([gx - 0.22, gx + 0.22], [GNDY - 0.24, GNDY - 0.24], color="k", lw=LW)
ax.plot([gx - 0.13, gx + 0.13], [GNDY - 0.36, GNDY - 0.36], color="k", lw=LW)
ax.plot([gx - 0.05, gx + 0.05], [GNDY - 0.48, GNDY - 0.48], color="k", lw=LW)

ax.text(6.3, 0.78, "VOUT = 0.81 × (1 + R1/R2) ≈ 3.3 V（本项目 5 V 输入，元件值沿用官方典型应用）",
        ha="center", fontsize=10)
ax.text(6.3, 0.34, "依据 MPS《MP2359 Datasheet》Rev.1.21 Typical Application 重绘",
        ha="center", fontsize=9, color="#444444")

fig.savefig(os.path.join(OUT, "MP2359_典型应用电路_5V转3.3V_重绘.png"),
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("done")
