import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import os

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.dirname(os.path.abspath(__file__))
LW = 2.0

# ============ 图1 引脚图 ============
fig, ax = plt.subplots(figsize=(7.2, 6.4), dpi=220)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

W, H = 3.3, 5.8
x0, y0 = 3.1, 2.2
ax.add_patch(Rectangle((x0, y0), W, H, fill=False, lw=LW * 1.4))
ax.text(x0 + W / 2, y0 + H * 0.62, "E220-400T22D", ha="center", va="center",
        fontsize=12, weight="bold", rotation=90)
ax.text(x0 + W / 2, y0 + H * 0.28, "21 × 36 mm", ha="center", va="center",
        fontsize=9, rotation=90, color="#333333")

pins = ["M0", "M1", "RXD", "TXD", "AUX", "VCC", "GND"]
ys = [y0 + H - 0.55 - i * 0.76 for i in range(7)]
for i, (n, y) in enumerate(zip(pins, ys)):
    ax.plot([x0 - 0.55, x0], [y, y], color="k", lw=LW * 2.0)
    ax.text(x0 - 0.70, y, f"{i+1}", ha="right", va="center", fontsize=10)
    ax.text(x0 - 1.05, y, n, ha="right", va="center", fontsize=11, weight="bold")

# SMA
ax.plot([x0 + W, x0 + W + 0.45], [y0 + H / 2, y0 + H / 2], color="k", lw=LW * 2)
ax.add_patch(Rectangle((x0 + W + 0.45, y0 + H / 2 - 0.42), 0.75, 0.84, fill=False, lw=LW))
ax.text(x0 + W + 0.82, y0 + H / 2 + 0.62, "SMA-K", ha="center", fontsize=9.5)

# 固定孔
for i in range(4):
    ax.add_patch(Circle((x0 + 0.55 + i * 0.75, y0 + 0.55), 0.12, fill=False,
                        lw=1.4, ls="--"))
ax.text(x0 + W / 2, y0 + 0.15, "8—11 固定孔（与 GND 相连）", ha="center", fontsize=8.5,
        color="#333333")

ax.text(5.0, 9.2, "E220-400T22D 引脚定义（顶视）", ha="center", fontsize=13, weight="bold")
ax.text(5.0, 1.15, "依据亿佰特官网产品页「引脚定义」表绘制（ebyte.com/product/1077.html）",
        ha="center", fontsize=8.5, color="#444444")
ax.text(5.0, 0.80, "M0/M1 不可悬空；VCC 2.3—5.5 V；通信电平 3.3 V TTL",
        ha="center", fontsize=8.5, color="#444444")

fig.savefig(os.path.join(OUT, "E220-400T22D_引脚图.png"), bbox_inches="tight", facecolor="white")
plt.close(fig)

# ============ 图2 与 MCU 连接 ============
fig, ax = plt.subplots(figsize=(9.8, 5.4), dpi=220)
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis("off")

ax.add_patch(FancyBboxPatch((0.8, 1.9), 3.8, 4.0, boxstyle="round,pad=0.02",
                            fill=False, lw=LW))
ax.text(2.7, 5.62, "GD32F103CBT6", ha="center", fontsize=11, weight="bold")
ax.text(2.7, 5.28, "（3.3 V 系统）", ha="center", fontsize=9)

ax.add_patch(FancyBboxPatch((7.5, 1.9), 3.8, 4.0, boxstyle="round,pad=0.02",
                            fill=False, lw=LW))
ax.text(9.4, 5.62, "E220-400T22D", ha="center", fontsize=11, weight="bold")
ax.text(9.4, 5.28, "LoRa 模块", ha="center", fontsize=9)

left_pins = [("PA9  (USART0_TX)", 4.85), ("PA10 (USART0_RX)", 4.30),
             ("PB0  (GPIO 输出)", 3.75), ("PB1  (GPIO 输出)", 3.20),
             ("PB2  (GPIO 输入)", 2.65)]
right_pins = [("RXD", 4.85), ("TXD", 4.30), ("M0", 3.75), ("M1", 3.20), ("AUX", 2.65)]

for name, y in left_pins:
    ax.text(4.5, y, name, ha="right", va="center", fontsize=9)
for name, y in right_pins:
    ax.text(7.6, y, name, ha="left", va="center", fontsize=9.5, weight="bold")

for y in [4.85, 4.30, 3.75, 3.20, 2.65]:
    ax.annotate("", xy=(7.46, y), xytext=(4.66, y),
                arrowprops=dict(arrowstyle="<->", lw=1.4, color="k",
                                shrinkA=0, shrinkB=0))

ax.text(6.06, 5.02, "TX / RX 交叉", ha="center", fontsize=8, color="#555555")

# 电源
ax.plot([2.7, 9.4], [1.55, 1.55], color="k", lw=1.4)
ax.text(2.7, 1.30, "3V3", ha="center", fontsize=8.5)
ax.text(9.4, 1.30, "VCC", ha="center", fontsize=8.5)
ax.text(6.05, 1.62, "3.3 V", ha="center", fontsize=8)

ax.plot([2.7, 9.4], [1.05, 1.05], color="k", lw=1.4)
ax.text(2.7, 0.80, "GND", ha="center", fontsize=8.5)
ax.text(9.4, 0.80, "GND", ha="center", fontsize=8.5)

ax.text(6.05, 6.55, "E220-400T22D 与主控 UART 连接（3.3 V TTL，可直连）",
        ha="center", fontsize=11.5, weight="bold")
ax.text(6.05, 0.38, "TX/RX 必须交叉；M0/M1 由 GPIO 控制四种工作模式；AUX 可悬空，接 MCU 用于唤醒/忙判断",
        ha="center", fontsize=8.5, color="#444444")

fig.savefig(os.path.join(OUT, "E220-400T22D_与MCU连接示意.png"), bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print("done")
