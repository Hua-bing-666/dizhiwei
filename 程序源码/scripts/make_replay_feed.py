# -*- coding: utf-8 -*-
"""把仿真留出轨迹导出为最小链路的回放数据源。

输出 CSV 列：t_ms,p0_kpa,p1_kpa,q_lpm
固件主机回放会把它反算成 4-20 mA / 12 位码 / 540 脉冲每升，因此量化误差被真实复现。
"""
import os
import sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ = os.path.join(ROOT, "simulation", "cusum_review", "heldout_observations.npz")
OUTDIR = os.path.join(ROOT, "firmware", "data")


def main():
    z = np.load(NPZ, allow_pickle=True)
    obs = z["observed"]
    t = z["t"]
    ids = [str(x) for x in z["trial_ids"]]
    kinds = [i.split("|")[0] for i in ids]

    uniq = sorted(set(kinds))
    print("kind values:", uniq[:20])

    os.makedirs(OUTDIR, exist_ok=True)
    picked = {}
    for k in uniq:
        if k in picked:
            continue
        idx = kinds.index(k)
        picked[k] = idx

    for k, idx in picked.items():
        o = obs[idx]
        path = os.path.join(OUTDIR, "feed_%s.csv" % k.replace("/", "_"))
        with open(path, "w", encoding="utf-8") as f:
            f.write("# replay feed: kind=%s trial=%s\n" % (k, ids[idx]))
            f.write("# t_ms,p0_kpa,p1_kpa,q_lpm\n")
            for i, tt in enumerate(t):
                f.write("%d,%.6f,%.6f,%.6f\n" % (
                    int(tt * 1000), o[i, 0], o[i, 1], o[i, 2]))
        print("wrote %s  (kind=%s, %.1f s)" % (path, k, t[-1]))
        print("   trial id:", ids[idx])


if __name__ == "__main__":
    main()
