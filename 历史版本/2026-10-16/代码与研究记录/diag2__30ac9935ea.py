# -*- coding: utf-8 -*-
"""诊断 CUSUM 过灵敏的根因。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features, MON_START, FAULT_START
from run_experiments import calibrate2, residuals2, run_cusum, CAL_WINDOWS

d = load(); kind, sigma, seed = parse_ids(d["ids"])
i = int(np.where((kind == "normal") & (sigma == 0.3))[0][0])
o = d["obs"][i]
f = features(o); cal = calibrate2(f)
eq, er = residuals2(f, cal)
v = f["valid"]

print("=== 标定参数 ===")
for k in ["n", "a", "gain", "r0", "s_q", "s_r"]:
    print("  %-6s = %.6g" % (k, cal[k]))
print("  标定窗口:", CAL_WINDOWS)

print("\n=== 残差在不同时段的分布 ===")
segs = [("健康 B关 20-175", 20, 175), ("健康 B开 200-298", 200, 298),
        ("健康 B关 305-355", 305, 355), ("故障前段 130-359", 130, 359),
        ("故障段 400-599", 400, 599)]
for lab, lo, hi in segs:
    m = np.zeros(len(eq), bool); m[lo:hi] = True; m &= v
    if m.sum() == 0:
        print("  %-20s 无有效样本" % lab); continue
    print("  %-20s n=%3d  e_Q 均值%+9.5f 尺度(1.4826MAD)%9.5f | e_R 均值%+9.5f 尺度%9.5f" % (
        lab, m.sum(), eq[m].mean(), 1.4826*np.median(np.abs(eq[m]-np.median(eq[m]))),
        er[m].mean(), 1.4826*np.median(np.abs(er[m]-np.median(er[m])))))

print("\n=== z 统计量（用标定尺度归一）===")
for lab, lo, hi in segs:
    m = np.zeros(len(eq), bool); m[lo:hi] = True; m &= v
    if m.sum() == 0: continue
    zq = eq[m]/cal["s_q"]; zr = er[m]/cal["s_r"]
    print("  %-20s z_Q 均值%+8.2f 最大%+9.1f | z_R 均值%+8.2f 最大%+9.1f" % (
        lab, zq.mean(), zq.max(), zr.mean(), zr.max()))

print("\n=== 为什么 B开 段 z 会很大？ ===")
print("  标定窗口含 B关(20-175)与 B开(300-599 的早期？)")
for lo, hi in CAL_WINDOWS:
    m = np.zeros(len(eq), bool); m[lo:hi] = True; m &= v
    print("    窗口 %d-%d: 有效%d  e_Q均值%+9.5f  e_R均值%+9.5f" % (
        lo, hi, m.sum(), eq[m].mean(), er[m].mean()))

print("\n=== 关键：300-599 里含故障！ ===")
print("  该数据集的故障从 t=360 开始（见 diagnosis_feasibility.py）")
print("  ⇒ 标定窗口 (300,599) 把故障段当成健康，污染了参照")
for lo, hi, tag in [(300, 359, "健康"), (400, 599, "故障")]:
    m = np.zeros(len(eq), bool); m[lo:hi] = True; m &= v
    print("    %s %d-%d: e_Q均值%+9.5f  e_R均值%+9.5f" % (
        tag, lo, hi, eq[m].mean(), er[m].mean()))
