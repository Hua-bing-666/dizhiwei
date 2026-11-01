# -*- coding: utf-8 -*-
"""诊断：supply 扰动为什么也会让检据误报？误报由哪个通道驱动？"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features
from E3_corrected import calibrate_clean, resid

d = load(); kind, sigma, seed = parse_ids(d["ids"])
CAL_H = [(20, 175)]

for sg in [0.3, 3.0]:
    i = int(np.where((kind == "supply") & (sigma == sg))[0][0])
    o = d["obs"][i]
    f = features(o); cal = calibrate_clean(f, CAL_H)
    eq, er = resid(f, cal)
    v = f["valid"]
    print("=" * 76)
    print("supply|%.1f 首条：标定参数 n=%.4f r0=%.4f s_q=%.5f s_r=%.5f" % (
        sg, cal["n"], cal["r0"], cal["s_q"], cal["s_r"]))
    print("  t     P0      P1      Q      e_Q        e_R       z_Q      z_R")
    for tt in [60, 150, 179, 200, 250, 300, 400, 500, 599]:
        zq = eq[tt] / cal["s_q"]; zr = er[tt] / cal["s_r"]
        print("  %3d %7.2f %7.2f %6.3f %+9.5f %+9.5f %+8.2f %+8.2f" % (
            tt, o[tt, 0], o[tt, 1], o[tt, 2], eq[tt], er[tt], zq, zr))
    # 分段残差统计
    print("  --- 分段 ---")
    for lab, lo, hi in [("健康 20-175", 20, 175), ("扰动 200-599", 200, 599)]:
        m = np.zeros(len(eq), bool); m[lo:hi] = True; m &= v
        print("    %-14s e_Q 均值%+9.5f 标准差%9.5f | e_R 均值%+9.5f 标准差%9.5f" % (
            lab, eq[m].mean(), eq[m].std(), er[m].mean(), er[m].std()))
    print("    z_Q 最大值 %.1f | z_R 最大值 %.1f" % (
        np.nanmax(eq[200:600] / cal["s_q"]), np.nanmax(er[200:600] / cal["s_r"])))
