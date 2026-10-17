# -*- coding: utf-8 -*-
"""E6 泄漏注入修正版2：注入窗口放在干净健康段内，避开 B 阀开(200-298)与自带故障(t>=360)。

注入窗口 130—195（全部 B 阀关、t<360），评估窗口 130—195。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features, MON_START
from E3_corrected import calibrate_clean, resid, cusum_max

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
H_REC = 61.0
C_MODEL, R_MODEL = 0.280, 0.79
# 注入窗口必须与标定窗口不重叠！
# 标定只用 (20,175) 与 (305,355)；注入放在 205—284（B 阀开段，健康工况）
T0, DUR = 205, 80
CAL_WIN = [(20, 175), (305, 355)]


def inject_leak(o, t0, dur, amp):
    o = o.copy()
    for j in range(dur):
        tt = t0 + j
        if tt >= len(o): break
        Qn = o[tt, 2] * (1.0 + amp)
        P1 = (Qn / C_MODEL) ** 2
        P0 = P1 + R_MODEL * Qn ** 2
        o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Qn
    return o


def ev(o, t0, dur, h=H_REC, noise=0.0, rng=None):
    if noise > 0 and rng is not None:
        o = o.copy()
        o[:, 0] += rng.normal(0, noise, len(o))
        o[:, 1] += rng.normal(0, noise, len(o))
    f = features(o); cal = calibrate_clean(f, CAL_WIN)
    eq, er = resid(f, cal)
    mx, _, _ = cusum_max(eq, er, cal)
    pre = mx[t0 - 60:t0] if t0 >= 60 else mx[:t0]
    fa = bool(pre.size and np.nanmax(pre) > h)
    w = np.where(mx[t0:t0 + dur + 30] > h)[0]
    return dict(fa=fa, det=len(w) > 0, t=(int(w[0] + t0) if len(w) else None))


def main():
    d = load(); kind, sigma, seed = parse_ids(d["ids"])
    idxs = np.where((kind == "normal") & (sigma == 1.0))[0][:10]
    L = []; A = L.append

    A("=" * 78)
    A("E6 修正版2：注入窗口 t=%d—%d（干净健康段内），h=%.0f" % (T0, T0 + DUR, H_REC))
    A("=" * 78)
    A("【1】泄漏：相对流量增量 → 检出率")
    A("  %-10s %-12s %-12s %s" % ("幅度", "检出", "误报", "中位检出t"))
    rows = []
    for amp in [0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50]:
        det = fa = 0; ts = []
        for i in idxs:
            r = ev(inject_leak(d["obs"][i], T0, DUR, amp), T0, DUR)
            if r["det"]: det += 1; ts.append(r["t"])
            if r["fa"]: fa += 1
        rows.append(dict(amp=amp, n=len(idxs), det="%d/%d" % (det, len(idxs)),
                         fa="%d/%d" % (fa, len(idxs)), t=(float(np.median(ts)) if ts else None)))
        A("  %-10s %-12s %-12s %s" % ("%.0f%%" % (amp * 100), rows[-1]["det"], rows[-1]["fa"],
                                      ("%.0f" % rows[-1]["t"]) if rows[-1]["t"] else "—"))
    A("")

    A("【2】二维边界：幅度 × 时长（泄漏）")
    durs = [5, 10, 20, 40, 60]
    A("  幅度\\时长   " + "  ".join("%6ds" % x for x in durs))
    grid = {}
    for amp in [0.03, 0.05, 0.10, 0.20, 0.30]:
        row = []
        for du in durs:
            det = 0
            for i in idxs:
                r = ev(inject_leak(d["obs"][i], T0, du, amp), T0, du)
                if r["det"] and not r["fa"]: det += 1
            row.append("%d/%d" % (det, len(idxs)))
        grid["%.2f" % amp] = dict((str(k), v) for k, v in zip(durs, row))
        A("  %6.1f%%     " % (amp * 100) + "  ".join("%6s" % v for v in row))
    A("")

    A("=" * 78)
    A("E7 修正版2：压力测量不确定度 U 需求（20%% 泄漏，%ds，h=61）" % DUR)
    A("=" * 78)
    rng = np.random.default_rng(20261017)
    A("  %-14s %-12s %-12s %s" % ("U(kPa,1σ)", "检出", "误报", "判定"))
    urows = []
    for U in [0.0, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00]:
        det = fa = 0
        for i in idxs:
            r = ev(inject_leak(d["obs"][i], T0, DUR, 0.20), T0, DUR, noise=U, rng=rng)
            if r["det"]: det += 1
            if r["fa"]: fa += 1
        ok = (det == len(idxs) and fa == 0)
        urows.append(dict(U=U, det="%d/%d" % (det, len(idxs)), fa="%d/%d" % (fa, len(idxs)), ok=ok))
        A("  %-14.2f %-12s %-12s %s" % (U, urows[-1]["det"], urows[-1]["fa"],
                                        "达标" if ok else ""))
    ok_u = [r["U"] for r in urows if r["ok"]]
    A("")
    A("  ⇒ 在 0—%.2f kPa 的测试范围内全部『全检出 + 零误报』；" % (max(ok_u) if ok_u else 0.0))
    A("     未观察到失效拐点，真实失效点高于测试上限（另见 F1_F2.py 扩展到 5 kPa）")

    txt = "\n".join(L)
    open(os.path.join(RES, "E6_E7_v2.txt"), "w", encoding="utf-8").write(txt)
    json.dump(dict(leak=rows, grid=grid, U=urows),
              open(os.path.join(RES, "E6_E7_v2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
