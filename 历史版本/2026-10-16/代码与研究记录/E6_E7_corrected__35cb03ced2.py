# -*- coding: utf-8 -*-
"""E6/E7 修正版：最小可检幅度、二维边界、不确定度需求。

修正：故障注入放在数据集的干净健康段内（t<360），避免与原有故障叠加。
注入方式：按 Q' = Q·(1+amp)，由模型反算 P1=(Q'/C)^2、P0=P1+R·Q'^2（对泄漏，R 不变）。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features, MON_START

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
from E3_corrected import calibrate_clean, resid, cusum_max, HEALTHY_WINDOWS

H_REC = 61.0          # 由 E3 修正版反推
C_MODEL, R_MODEL = 0.280, 0.79


def inject_leak(o, t0, dur, amp, C=C_MODEL, R=R_MODEL):
    o = o.copy()
    for j in range(dur):
        tt = t0 + j
        if tt >= len(o): break
        Qn = o[tt, 2] * (1.0 + amp)
        P1 = (Qn / C) ** 2
        P0 = P1 + R * Qn ** 2
        o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Qn
    return o


def inject_restriction(o, t0, dur, rel_R, C=C_MODEL, R=R_MODEL):
    """受限：区段阻力增至 R*(1+rel_R)，流量随之下降（保持同一 Ps 近似）"""
    o = o.copy()
    Ps = o[:, 0].mean() + R * (o[:, 2].mean() ** 2)
    for j in range(dur):
        tt = t0 + j
        if tt >= len(o): break
        Rnew = R * (1.0 + rel_R)
        # Ps = P1 + (Rc+Rnew)Q^2, Q = C sqrt(P1) → P1 = (Q/C)^2
        # 解 Q： Ps = (Q/C)^2 + (Rc+Rnew)Q^2
        Rc = max(R - 0.0, 0.0)
        k = 1.0 / C ** 2 + (Rc + Rnew)
        Qn = np.sqrt(Ps / k)
        P1 = (Qn / C) ** 2
        P0 = P1 + Rnew * Qn ** 2
        o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Qn
    return o


def evaluate(o, t0, dur, h=H_REC, extra_noise=0.0, rng=None):
    if extra_noise > 0 and rng is not None:
        o = o.copy()
        o[:, 0] = o[:, 0] + rng.normal(0, extra_noise, len(o))
        o[:, 1] = o[:, 1] + rng.normal(0, extra_noise, len(o))
    f = features(o); cal = calibrate_clean(f)
    eq, er = resid(f, cal)
    mx, _, _ = cusum_max(eq, er, cal)
    pre = mx[MON_START:t0]
    fa = bool(pre.size and np.nanmax(pre) > h)
    w = np.where(mx[t0:t0 + dur + 60] > h)[0]
    return dict(fa=fa, detected=len(w) > 0,
                t_det=(int(w[0] + t0) if len(w) else None))


def main():
    d = load(); kind, sigma, seed = parse_ids(d["ids"])
    L = []; A = L.append

    # 健康轨迹：用 t<360 的干净段。避开 200—298（B 阀开），
    # 注入点取 t0=305，此时监测段 130—305 有充足健康样本
    idxs = np.where((kind == "normal") & (sigma == 1.0))[0][:10]
    T0, DUR = 305, 50           # 305—355，全部落在 B 阀关段且 t<360

    A("=" * 78)
    A("E6 修正版：最小可检幅度（注入位置 t=%d，时长 %ds，h=%.0f）" % (T0, DUR, H_REC))
    A("=" * 78)
    A("【1】泄漏：相对流量增量 → 检出率")
    A("  %-10s %-16s %-16s %s" % ("幅度", "检出(原始)", "误报(原始)", "中位检出t"))
    amp_rows = []
    for amp in [0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30]:
        det = fa = 0; ts = []
        for i in idxs:
            o = inject_leak(d["obs"][i], T0, DUR, amp)
            r = evaluate(o, T0, DUR)
            if r["detected"]: det += 1; ts.append(r["t_det"])
            if r["fa"]: fa += 1
        amp_rows.append(dict(amp=amp, n=len(idxs),
                             det="%d/%d" % (det, len(idxs)), fa="%d/%d" % (fa, len(idxs)),
                             t=(float(np.median(ts)) if ts else None)))
        A("  %-10s %-16s %-16s %s" % (
            "%.0f%%" % (amp * 100), amp_rows[-1]["det"], amp_rows[-1]["fa"],
            ("%.0f" % amp_rows[-1]["t"]) if amp_rows[-1]["t"] else "—"))
    A("")

    A("【2】受限：相对阻力增量 → 检出率")
    res_rows = []
    for rel in [0.10, 0.20, 0.30, 0.50, 0.80, 1.20, 2.00, 3.00]:
        det = fa = 0; ts = []
        for i in idxs:
            o = inject_restriction(d["obs"][i], T0, DUR, rel)
            r = evaluate(o, T0, DUR)
            if r["detected"]: det += 1; ts.append(r["t_det"])
            if r["fa"]: fa += 1
        res_rows.append(dict(rel_R=rel, n=len(idxs),
                             det="%d/%d" % (det, len(idxs)), fa="%d/%d" % (fa, len(idxs)),
                             t=(float(np.median(ts)) if ts else None)))
        A("  R +%-8s %-16s %-16s %s" % (
            "%.0f%%" % (rel * 100), res_rows[-1]["det"], res_rows[-1]["fa"],
            ("%.0f" % res_rows[-1]["t"]) if res_rows[-1]["t"] else "—"))
    A("")

    A("=" * 78)
    A("E6b 二维边界：幅度 × 时长（泄漏，σ=1.0）")
    A("=" * 78)
    durs = [5, 10, 20, 40, 60]
    grid = {}
    A("  幅度\\时长   " + "  ".join("%6ds" % x for x in durs))
    for amp in [0.03, 0.05, 0.10, 0.20]:
        row = []
        for du in durs:
            if T0 + du > 195:      # 不越过 B 开段
                row.append("—"); continue
            det = 0
            for i in idxs:
                o = inject_leak(d["obs"][i], T0, du, amp)
                r = evaluate(o, T0, du)
                if r["detected"] and not r["fa"]: det += 1
            row.append("%d/%d" % (det, len(idxs)))
        grid["%.2f" % amp] = dict(zip([str(x) for x in durs], row))
        A("  %6.1f%%     " % (amp * 100) + "  ".join("%6s" % v for v in row))
    A("")

    A("=" * 78)
    A("E7 修正版：压力测量不确定度 U 需求（20%% 泄漏，60s，h=61）")
    A("=" * 78)
    rng = np.random.default_rng(20261016)
    A("  %-14s %-14s %s" % ("U(kPa, 1σ)", "检出率", "误报率"))
    u_rows = []
    for U in [0.0, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.80, 1.20, 2.00]:
        det = fa = 0
        for i in idxs:
            o = inject_leak(d["obs"][i], T0, DUR, 0.20)
            r = evaluate(o, T0, DUR, extra_noise=U, rng=rng)
            if r["detected"]: det += 1
            if r["fa"]: fa += 1
        flg = ""
        if det >= len(idxs) and fa == 0: flg = "  ← 达标"
        u_rows.append(dict(U=U, n=len(idxs), det="%d/%d" % (det, len(idxs)),
                           fa="%d/%d" % (fa, len(idxs)), ok=(det == len(idxs) and fa == 0)))
        A("  %-14.2f %-14s %s%s" % (U, u_rows[-1]["det"], u_rows[-1]["fa"], flg))
    A("")
    ok = [r for r in u_rows if r["ok"]]
    if ok:
        A("  ⇒ 在『检出 100%% 且零误报』条件下，压力测量不确定度 U 需 ≤ %.2f kPa（1σ）" % max(r["U"] for r in ok))
    else:
        A("  ⇒ 未找到同时满足『全检出 + 零误报』的 U 取值")

    txt = "\n".join(L)
    open(os.path.join(RES, "E6_E7_corrected.txt"), "w", encoding="utf-8").write(txt)
    json.dump(dict(amplitude=amp_rows, restriction=res_rows, grid=grid, U=u_rows),
              open(os.path.join(RES, "E6_E7_corrected.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
