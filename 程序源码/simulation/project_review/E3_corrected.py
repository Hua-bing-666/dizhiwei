# -*- coding: utf-8 -*-
"""E3 修正版：用干净健康段标定，正确测 ARL0，反推门限 h。

修正两处：
 1) 标定窗口只用 t<360 的健康段（数据集故障从 t=360 开始）
 2) ARL0 只在健康段统计，避免把故障响应当误报
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features, MON_START, FAULT_START

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)

# 干净健康窗口（t<360，且避开/包含 B 阀两种状态）
HEALTHY_WINDOWS = [(20, 175), (200, 298), (305, 355)]


def calibrate_clean(f, windows=HEALTHY_WINDOWS):
    T = len(f["valid"]); m = np.zeros(T, bool)
    for lo, hi in windows:
        m[lo:min(hi + 1, T)] = True
    m &= f["valid"] & np.isfinite(f["K"])
    p1, q, rh = f["p1"][m], f["q"][m], f["Rh"][m]
    lg = np.polyfit(np.log(p1 / 100.0), np.log(q), 1)
    n, a = float(lg[0]), float(np.exp(lg[1]))
    q_ref = a * (p1 / 100.0) ** n
    gain = float(np.median(q / q_ref)); r0 = float(np.median(rh))
    eq = q / (gain * q_ref) - 1.0; er = rh - r0
    def sc(x, fl):
        return max(float(1.4826 * np.median(np.abs(x - np.median(x)))), fl)
    return dict(n=n, a=a, gain=gain, r0=r0, s_q=sc(eq, 1e-5), s_r=sc(er, 1e-4))


def resid(f, cal):
    q, p1, Rh = f["q"], f["p1"], f["Rh"]
    q_ref = cal["a"] * (p1 / 100.0) ** cal["n"]
    with np.errstate(invalid="ignore", divide="ignore"):
        return q / (cal["gain"] * q_ref) - 1.0, Rh - cal["r0"]


def cusum_max(eq, er, cal, k=0.5):
    """返回每时刻两路 CUSUM 的最大值（未设门限）"""
    T = len(eq)
    zq = eq / cal["s_q"]; zr = er / cal["s_r"]
    Sq = np.zeros(T); Sr = np.zeros(T)
    for i in range(1, T):
        Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
        Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    return np.maximum(Sq, Sr), Sq, Sr


def main():
    d = load(); kind, sigma, seed = parse_ids(d["ids"])
    L = []; A = L.append
    A("=" * 78)
    A("E3 修正版：干净健康段标定 → CUSUM 峰值分布 → 反推门限 h")
    A("=" * 78)
    A("健康窗口（t<360，避开故障）: %s" % (HEALTHY_WINDOWS,))
    A("")

    # ---- 第一步：健康段的 CUSUM 峰值分布（用每条轨迹自己标定）----
    A("【1】各 σ 下，健康段（20—355）的 CUSUM 峰值分布")
    A("     （若门限 h 高于该峰值，则健康段不误报）")
    A("  %-10s %-6s %-12s %-12s %-12s %s" % ("σ(kPa)", "样本", "P50", "P90", "P99", "最大"))
    peaks = {}
    for sg in [0.3, 1.0, 3.0, 10.0]:
        idxs = np.where((kind == "normal") & (sigma == sg))[0]
        pk = []
        for i in idxs:
            f = features(d["obs"][i]); cal = calibrate_clean(f)
            eq, er = resid(f, cal)
            mx, _, _ = cusum_max(eq, er, cal)
            seg = mx[20:356]
            pk.append(np.nanmax(seg))
        pk = np.array(pk, float)
        peaks["sigma=%.1f" % sg] = dict(
            n=len(pk), p50=float(np.percentile(pk, 50)), p90=float(np.percentile(pk, 90)),
            p99=float(np.percentile(pk, 99)), max=float(pk.max()))
        A("  %-10.1f %-6d %-12.2f %-12.2f %-12.2f %.2f" % (
            sg, len(pk), np.percentile(pk, 50), np.percentile(pk, 90),
            np.percentile(pk, 99), pk.max()))
    A("")

    # ---- 第二步：跨 σ 统一门限（取所有 σ 中健康峰值最大者 + 余量）----
    allmax = max(v["max"] for v in peaks.values())
    allp99 = max(v["p99"] for v in peaks.values())
    A("【2】跨 σ 统一门限的推荐值")
    A("     健康段峰值最大 = %.2f（来自最差 σ）" % allmax)
    A("     健康段 P99 最大 = %.2f" % allp99)
    A("     ⇒ 建议 h = %.1f（= 健康峰值最大 × 1.2，留 20%% 余量）" % (allmax * 1.2))
    h_rec = float(np.ceil(allmax * 1.2))
    A("     ⇒ 取整 h = %.0f" % h_rec)
    A("")

    # ---- 第三步：用推荐门限复测检出与误报 ----
    A("【3】用 h=%.0f 复测（健康段=误报，故障段=检出）" % h_rec)
    A("  %-12s %-6s %-14s %-14s %s" % ("故障", "σ", "健康段误报", "故障段检出", "中位检出t"))
    rows = []
    for kd in ["leak", "restriction", "drift", "load_unknown"]:
        for sg in [0.3, 1.0, 3.0, 10.0]:
            idxs = np.where((kind == kd) & (sigma == sg))[0]
            fa = det = 0; ts = []
            for i in idxs:
                f = features(d["obs"][i]); cal = calibrate_clean(f)
                eq, er = resid(f, cal)
                mx, _, _ = cusum_max(eq, er, cal)
                if np.nanmax(mx[MON_START:FAULT_START]) > h_rec:
                    fa += 1
                w = np.where(mx[FAULT_START:] > h_rec)[0]
                if len(w):
                    det += 1; ts.append(int(w[0] + FAULT_START))
            rows.append(dict(kind=kd, sigma=sg, n=len(idxs),
                             fa="%d/%d" % (fa, len(idxs)),
                             det="%d/%d" % (det, len(idxs)),
                             t=(float(np.median(ts)) if ts else None)))
            A("  %-12s %-6.1f %-14s %-14s %s" % (
                kd, sg, rows[-1]["fa"], rows[-1]["det"],
                ("%.0f" % rows[-1]["t"]) if rows[-1]["t"] else "—"))
    A("")

    # ---- 第四步：门限扫描，看检出-误报权衡 ----
    A("【4】门限扫描（leak 类，σ=1.0）")
    A("  %-8s %-14s %s" % ("h", "健康段误报", "故障段检出"))
    sweep = []
    idxs = np.where((kind == "leak") & (sigma == 1.0))[0]
    cache = []
    for i in idxs:
        f = features(d["obs"][i]); cal = calibrate_clean(f)
        eq, er = resid(f, cal)
        mx, _, _ = cusum_max(eq, er, cal)
        cache.append(mx)
    for h in [5, 10, 15, 20, 30, 40, 60, 80, 100, 150, 200]:
        fa = det = 0
        for mx in cache:
            if np.nanmax(mx[MON_START:FAULT_START]) > h: fa += 1
            if np.any(mx[FAULT_START:] > h): det += 1
        sweep.append(dict(h=h, fa="%d/%d" % (fa, len(cache)), det="%d/%d" % (det, len(cache))))
        A("  %-8d %-14s %s" % (h, sweep[-1]["fa"], sweep[-1]["det"]))
    A("")

    txt = "\n".join(L)
    open(os.path.join(RES, "E3_corrected.txt"), "w", encoding="utf-8").write(txt)
    json.dump(dict(peaks=peaks, h_recommended=h_rec, rows=rows, sweep=sweep),
              open(os.path.join(RES, "E3_corrected.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
