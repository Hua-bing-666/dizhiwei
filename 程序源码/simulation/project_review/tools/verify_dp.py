# -*- coding: utf-8 -*-
"""用实际仿真数据反推供压，验证 ΔP 到底该取 10.04 还是 9.44。

两套口径：
  A（未耦合近似）：P1 ≈ Ps，ΔP = R·Q²，其中 Q = C·√Ps
  B（耦合精确解）：P1 = Ps/(1+R·C²)，Q = C·√P1，ΔP = R·Q²
"""
import numpy as np, os

NPZ = r"C:\Users\Lenovo\Desktop\大创想法 - 副本\simulation\cusum_review\heldout_observations.npz"
z = np.load(NPZ, allow_pickle=True)
obs = z["observed"]; ids = z["trial_ids"]

kind = np.array([str(s).split("|")[0] for s in ids])
sigma = np.array([float(str(s).split("|")[1]) for s in ids])

C, R = 0.280, 0.79

print("=" * 84)
print("用实际仿真数据反推供压并检验两套口径")
print("=" * 84)

# 取正常轨迹，筛出高压工作段（P1 高、Q 高）视为 120kPa 档
idx = np.where((kind == "normal") & (sigma == 0.3))[0][:20]
rows = []
for i in idx:
    o = obs[i]
    m = np.zeros(len(o), bool)
    m[20:176] = True                    # B 阀关的健康段
    P0, P1, Q = o[m, 0], o[m, 1], o[m, 2]
    Ps_A = P0 + R * Q ** 2                       # 未耦合反推
    Ps_B = P1 + R * Q ** 2                       # 考虑 P1 已下降
    rows.append((P1.mean(), P0.mean(), Q.mean(),
                 np.median(Ps_A), np.median(Ps_B)))

print("\n%-6s %10s %10s %10s %12s %12s" % (
    "轨迹", "P1均值", "P0均值", "Q均值", "Ps(未耦合)", "Ps(考虑P1)"))
for k, r in enumerate(rows[:6]):
    print("%-6d %10.3f %10.3f %10.4f %12.3f %12.3f" % (k, r[0], r[1], r[2], r[3], r[4]))

P1m = np.mean([r[0] for r in rows])
P0m = np.mean([r[1] for r in rows])
Qm = np.mean([r[2] for r in rows])
DPm = P0m - P1m
print("\n汇总：P1=%.3f  P0=%.3f  Q=%.4f  ΔP=%.3f kPa" % (P1m, P0m, Qm, DPm))

print("\n【检验 1】用实测 ΔP 与 Q 反推 R")
print("  R_实测 = ΔP/Q² = %.4f / %.4f = %.4f" % (DPm, Qm ** 2, DPm / Qm ** 2))
print("  （设计值 R = 0.80，数据用 0.79）")

print("\n【检验 2】两套口径在该工况下的预测")
# 口径 A
Ps_fit_A = P1m + R * Qm ** 2
Q_A = C * np.sqrt(Ps_fit_A)
dp_A = R * Q_A ** 2
# 口径 B
Ps_fit_B = P0m + R * Qm ** 2
p1_B = Ps_fit_B / (1 + R * C ** 2)
Q_B = C * np.sqrt(p1_B)
dp_B = R * Q_B ** 2
print("  口径A（未耦合）：Ps=%.2f  Q=%.4f  P1=%.3f  ΔP=%.4f" % (
    Ps_fit_A, Q_A, Ps_fit_A, dp_A))
print("  口径B（耦合）：  Ps=%.2f  Q=%.4f  P1=%.3f  ΔP=%.4f" % (
    Ps_fit_B, Q_B, p1_B, dp_B))
print("  实测：         Ps=%.2f  Q=%.4f  P1=%.3f  ΔP=%.4f" % (
    P0m + R * Qm ** 2, Qm, P1m, DPm))

print("\n【检验 3】哪个 Q 更接近实测 %.4f？" % Qm)
err_A = abs(Q_A - Qm) / Qm * 100
err_B = abs(Q_B - Qm) / Qm * 100
print("  口径A 相对误差 %.3f%%" % err_A)
print("  口径B 相对误差 %.3f%%" % err_B)
print("  ⇒ %s 更准" % ("口径B（耦合）" if err_B < err_A else "口径A（未耦合）"))

print("\n【结论】160 kPa 档的最大健康压降应为：")
Ps = 160.0
p1_c = Ps / (1 + R * C ** 2)
q_c = C * np.sqrt(p1_c)
dp_c = R * q_c ** 2
q_u = C * np.sqrt(Ps)
dp_u = R * q_u ** 2
print("  耦合精确解：  Q=%.4f  P1=%.3f  ΔP=%.4f kPa" % (q_c, p1_c, dp_c))
print("  未耦合近似：  Q=%.4f  P1=%.3f  ΔP=%.4f kPa" % (q_u, Ps, dp_u))
print("  文献常用值：  ΔP=10.04 kPa（= R·C²·Ps，等价于未耦合近似）")
print("")
print("  ⇒ 两者相差 %.2f kPa（%.1f%%）" % (dp_u - dp_c, (dp_u - dp_c) / dp_c * 100))
print("  ⇒ 对量程选择无影响：20 kPa 档在两种口径下都满足 1.5 倍过载余量")
print("     （耦合 9.44×1.5=14.16；未耦合 10.04×1.5=15.06，均 < 20）")
print("  ⇒ 建议采用耦合精确解，并注明与未耦合近似的差异来源")
