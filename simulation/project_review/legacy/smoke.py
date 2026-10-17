# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import *

d = load()
kind, sigma, seed = parse_ids(d["ids"])
print("数据:", d["obs"].shape, " 类别:", sorted(set(kind)), " σ:", sorted(set(sigma)))

# 挑 leak|0.3 第一条
idx = int(np.where((kind == "leak") & (sigma == 0.3))[0][0])
f = features(d["obs"][idx])
cal = calibrate(f)
print("\n=== 标定结果（leak|0.3 首条）===")
for kk in ["n", "a", "gain", "r0", "s_q", "s_r"]:
    print("  %-6s = %.6g" % (kk, cal[kk]))

det = detector_original(f, cal)
cus = detector_cusum(f, cal)

def first_conf(conf, lo=MON_START):
    w = np.where(conf[lo:] > 0)[0]
    return int(w[0] + lo) if len(w) else None

print("\n=== 检出时刻 ===")
print("  原判据首次确认 t =", first_conf(det["confirmed"]))
print("  CUSUM 首次确认 t =", first_conf(cus["confirmed"]))

print("\n=== 故障前后残差与统计量（抽点）===")
eq, er = det["eq"], det["er"]
for tt in [130, 300, 359, 380, 420, 500, 600]:
    print("  t=%3d  e_Q=%+8.4f  e_R=%+8.4f  Sq=%7.3f  Sr=%7.3f  label=%d conf=%d" % (
        tt, eq[tt], er[tt], cus["Sq"][tt], cus["Sr"][tt], cus["label"][tt], cus["confirmed"][tt]))

# 再看 restriction
idx2 = int(np.where((kind == "restriction") & (sigma == 0.3))[0][0])
f2 = features(d["obs"][idx2]); c2 = calibrate(f2)
d2 = detector_original(f2, c2); u2 = detector_cusum(f2, c2)
print("\n=== restriction|0.3 ===")
print("  原判据首次确认 t =", first_conf(d2["confirmed"]))
print("  CUSUM 首次确认 t =", first_conf(u2["confirmed"]))
for tt in [359, 420, 500, 600]:
    print("  t=%3d  e_Q=%+8.4f  e_R=%+8.4f  Sq=%7.3f  Sr=%7.3f  conf=%d" % (
        tt, d2["eq"][tt], d2["er"][tt], u2["Sq"][tt], u2["Sr"][tt], u2["confirmed"][tt]))
