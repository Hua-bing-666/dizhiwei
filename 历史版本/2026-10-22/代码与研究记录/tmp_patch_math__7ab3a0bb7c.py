# -*- coding: utf-8 -*-
"""把所有图内的公式改成 matplotlib mathtext 排版（正确的根号、下标、希腊字母）。"""
import io

P = "simulation/project_review/make_figures.py"
t = io.open(P, encoding="utf-8").read()

# (旧, 新) —— 只改显示字符串，不改用于 JSON 查表的键名
REPL = [
    # --- rcParams：显式指定 mathtext 字体 ---
    ("    'svg.fonttype': 'none',\n    'font.size': 13,",
     "    'svg.fonttype': 'none',\n    'mathtext.fontset': 'dejavusans',\n"
     "    'mathtext.default': 'regular',\n    'font.size': 13,"),

    # --- 门限符号 h* ---
    ('ax_b.text(e9["h_star"] + 2.5, 104, "h*=%d" % e9["h_star"], ha="left",',
     'ax_b.text(e9["h_star"] + 2.5, 104, r"$h^*$=%d" % e9["h_star"], ha="left",'),
    ('ax_a.text(39, H_STAR + 0.7, "h*=%d" % H_STAR, ha="right", va="bottom",',
     'ax_a.text(39, H_STAR + 0.7, r"$h^*$=%d" % H_STAR, ha="right", va="bottom",'),
    ('ax.text(600, 27.5, "h*=26", ha="right", va="bottom", fontsize=12,',
     'ax.text(600, 27.5, r"$h^*$=26", ha="right", va="bottom", fontsize=12,'),
    ('ax.text(26.4, ax.get_ylim()[1] * 0.86, "h*=26", ha="left", va="top",',
     'ax.text(26.4, ax.get_ylim()[1] * 0.86, r"$h^*$=26", ha="left", va="top",'),

    # --- 希腊字母 ---
    ('ax_a.set_xlabel("噪声相关时间 τ（s）")',
     'ax_a.set_xlabel(r"噪声相关时间 $\\tau$（s）")'),
    ('ax_b.set_xlabel("噪声相关时间 τ（s）")',
     'ax_b.set_xlabel(r"噪声相关时间 $\\tau$（s）")'),
    ('ax_b.set_ylabel("固定 h*=26 时误报率（%）")',
     'ax_b.set_ylabel(r"固定 $h^*$=26 时误报率（%）")'),
    ('ax_b.set_xlabel("压力噪声 σ（kPa）")',
     'ax_b.set_xlabel(r"压力噪声 $\\sigma$（kPa）")'),
    ('ax.set_xlabel("压力噪声 σ（kPa）")',
     'ax.set_xlabel(r"压力噪声 $\\sigma$（kPa）")'),
    ('ax.text(595, 3.4, "±3σ", ha="right", va="bottom", fontsize=12,',
     'ax.text(595, 3.4, r"$\\pm3\\sigma$", ha="right", va="bottom", fontsize=12,'),

    # --- 指数与下标 ---
    ('ax_b.set_ylabel("拟合指数偏差 |n−0.5|")',
     'ax_b.set_ylabel(r"拟合指数偏差 $|n-0.5|$")'),
    ('ax_a.set_ylabel("指数 n 的不确定度")',
     'ax_a.set_ylabel(r"指数 $n$ 的不确定度")'),

    # --- 增益漂移：显示标签用数学排版（键名保持原样）---
    ('short = ["流量 Q", "表压 P1", "差压 ΔP"]',
     'short = [r"流量 $Q$", r"表压 $P_1$", r"差压 $\\Delta P$"]'),
    ('ax_b.set_xlabel("Q 通道增益漂移（%）")',
     'ax_b.set_xlabel(r"$Q$ 通道增益漂移（%）")'),

    # --- 特征平面 ---
    ('ax.set_xlabel("负载系数相对变化 ΔK/K（%）")',
     'ax.set_xlabel(r"负载系数相对变化 $\\Delta K/K$（%）")'),
    ('ax.set_ylabel("区段阻力相对变化 ΔRh/Rh（%）")',
     'ax.set_ylabel(r"区段阻力相对变化 $\\Delta R_h/R_h$（%）")'),

    # --- 散点图：健康关系式（含根号）---
    ('label="健康关系 Q = C·√P1")',
     'label=r"健康关系 $Q=C\\sqrt{P_1}$")'),
    ('ax.set_xlabel("下游压力 P1（kPa）")',
     'ax.set_xlabel(r"下游压力 $P_1$（kPa）")'),
    ('ax.set_ylabel("支管流量 Q（L/min）")',
     'ax.set_ylabel(r"支管流量 $Q$（L/min）")'),

    # --- 残差时序 ---
    ('(ax1, zq_h, zq_f, "z_Q（K 通道）")',
     '(ax1, zq_h, zq_f, r"$z_Q$（K 通道）")'),
    ('(ax2, zr_h, zr_f, "z_R（Rh 通道）")',
     '(ax2, zr_h, zr_f, r"$z_R$（Rh 通道）")'),

    # --- 时域波形 ---
    ('axes[0].set_ylabel("P0（kPa）")', 'axes[0].set_ylabel(r"$P_0$（kPa）")'),
    ('axes[1].set_ylabel("P1（kPa）")', 'axes[1].set_ylabel(r"$P_1$（kPa）")'),
    ('axes[2].set_ylabel("Q（L/min）")', 'axes[2].set_ylabel(r"$Q$（L/min）")'),

    # --- 不确定度 ---
    ('ax_a.set_xlabel("压力测量不确定度 U（kPa）")',
     'ax_a.set_xlabel(r"压力测量不确定度 $U$（kPa）")'),
]

miss = []
for old, new in REPL:
    if old not in t:
        miss.append(old[:56])
        continue
    t = t.replace(old, new)

io.open(P, "w", encoding="utf-8").write(t)
print("替换成功 %d 处" % (len(REPL) - len(miss)))
if miss:
    print("未命中 %d 处：" % len(miss))
    for m in miss:
        print("   ", m)
