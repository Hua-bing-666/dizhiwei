# -*- coding: utf-8 -*-
"""诊断：标定段选择与残差尺度"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features

d = load(); kind, sigma, seed = parse_ids(d["ids"])

def calib_probe(idx, tag):
    o = d["obs"][idx]
    P0, P1, Q = o[:, 0], o[:, 1], o[:, 2]
    print("\n=== %s ===" % tag)
    print("  t     P0      P1      Q      (P0-P1)/Q^2   Q/sqrt(P1)")
    for tt in [30, 60, 100, 150, 179, 200, 250, 299, 320, 359, 400, 500, 600]:
        R = (P0[tt] - P1[tt]) / Q[tt] ** 2
        C = Q[tt] / np.sqrt(P1[tt])
        print("  %3d  %7.2f %7.2f %6.3f   %8.4f     %7.4f" % (tt, P0[tt], P1[tt], Q[tt], R, C))

# normal 轨迹：看 B 阀开关的影响
iN = int(np.where((kind == "normal") & (sigma == 0.3))[0][0])
calib_probe(iN, "normal|0.3 首条（B 阀 180-299 开）")

# 分窗口拟合 n
def fit_n(idx, lo, hi):
    o = d["obs"][idx]
    P1 = o[lo:hi, 1]; Q = o[lo:hi, 2]
    m = (P1 > 10) & (Q > 0.5)
    lg = np.polyfit(np.log(P1[m] / 100), np.log(Q[m]), 1)
    return lg[0], float(np.exp(lg[1]))

print("\n=== 分窗口拟合指数 n ===")
for tag, idx in [("normal", iN),
                 ("leak", int(np.where((kind == "leak") & (sigma == 0.3))[0][0])),
                 ("restriction", int(np.where((kind == "restriction") & (sigma == 0.3))[0][0]))]:
    for lo, hi, lab in [(20, 120, "20-119"), (20, 176, "20-175"),
                        (20, 300, "20-299"), (20, 360, "20-359"),
                        (300, 360, "300-359")]:
        n, a = fit_n(idx, lo, hi)
        print("  %-12s %-9s n=%+8.4f  a=%.4f" % (tag, lab, n, a))

# 残差尺度：用不同窗口
print("\n=== 残差尺度（以 normal 首条为例）===")
o = d["obs"][iN]
f = features(o)
for lo, hi, lab in [(20, 120, "20-119"), (20, 176, "20-175"), (20, 300, "20-299")]:
    P1 = f["p1"][lo:hi]; Q = f["q"][lo:hi]; Rh = f["Rh"][lo:hi]
    m = f["valid"][lo:hi]
    P1s, Qs, Rs = P1[m], Q[m], Rh[m]
    lg = np.polyfit(np.log(P1s / 100), np.log(Qs), 1)
    n, a = lg[0], float(np.exp(lg[1]))
    q_ref = a * (P1s / 100) ** n
    gain = np.median(Qs / q_ref)
    r0 = np.median(Rs)
    eq = Qs / (gain * q_ref) - 1
    er = Rs - r0
    sq = 1.4826 * np.median(np.abs(eq - np.median(eq)))
    sr = 1.4826 * np.median(np.abs(er - np.median(er)))
    print("  %-9s n=%+8.4f r0=%.4f  e_Q 均值%+.4f 尺度%.5f | e_R 均值%+.4f 尺度%.5f" % (
        lab, n, r0, np.mean(eq), sq, np.mean(er), sr))

# 全健康段（20-359，排除 B 开关 180-299）
print("\n=== 用 20-179 + 300-359 联合标定 ===")
mask = ((np.arange(len(f["valid"])) >= 20) & (np.arange(len(f["valid"])) <= 179)) | \
       ((np.arange(len(f["valid"])) >= 300) & (np.arange(len(f["valid"])) <= 359))
mask &= f["valid"]
P1s, Qs, Rs = f["p1"][mask], f["q"][mask], f["Rh"][mask]
lg = np.polyfit(np.log(P1s / 100), np.log(Qs), 1)
n, a = lg[0], float(np.exp(lg[1]))
q_ref = a * (P1s / 100) ** n
gain = np.median(Qs / q_ref); r0 = np.median(Rs)
eq = Qs / (gain * q_ref) - 1; er = Rs - r0
sq = 1.4826 * np.median(np.abs(eq - np.median(eq)))
sr = 1.4826 * np.median(np.abs(er - np.median(er)))
print("  n=%+.4f a=%.4f r0=%.4f  e_Q 尺度%.5f  e_R 尺度%.5f  样本%d" % (n, a, r0, sq, sr, mask.sum()))
