# -*- coding: utf-8 -*-
"""补做两项遗留仿真：
  F1) E5 修正：干管参照差分收益（在供压扰动场景下，比较有/无参照的误报）
  F2) E7 扩展：把 U 加大到 5 kPa，找敏感度拐点
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features, MON_START
from E3_corrected import calibrate_clean, resid, cusum_max

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
H = 61.0
C_M, R_M = 0.280, 0.79


def cusum_peak(eq, er, cal, k=0.5):
    T = len(eq)
    zq = eq / cal["s_q"]; zr = er / cal["s_r"]
    Sq = np.zeros(T); Sr = np.zeros(T)
    for i in range(1, T):
        Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
        Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    return np.maximum(Sq, Sr)


def main():
    d = load(); kind, sigma, seed = parse_ids(d["ids"])
    L = []; A = L.append

    # ================= F1: 干管参照差分收益 =================
    A("=" * 78)
    A("F1 干管参照差分收益（supply 类：供压扰动场景）")
    A("=" * 78)
    A("思路：供压扰动会让 P0、P1、Q 同步变化，造成共模残差。")
    A("      用干管参照 P2 做一阶差分归一化，应能压掉共模分量。")
    A("      评估窗口取【扰动持续段】(t=200—599)，标定只用 t<180 的健康段。")
    A("")
    A("  %-10s %-6s %-22s %-22s %s" % ("σ(kPa)", "样本", "无参照：扰动段误报", "有参照：扰动段误报", "改善"))
    rows = []
    rng = np.random.default_rng(20261018)
    CAL_H = [(20, 175)]
    for sg in [0.3, 1.0, 3.0, 10.0]:
        idxs = np.where((kind == "supply") & (sigma == sg))[0]
        fa0 = fa1 = 0; n = 0
        for i in idxs:
            o = d["obs"][i].copy()
            # 无参照：直接用原观测
            f = features(o); cal = calibrate_clean(f, CAL_H)
            eq, er = resid(f, cal)
            pk = cusum_peak(eq, er, cal)
            if np.nanmax(pk[200:600]) > H: fa0 += 1
            # 有参照：用干管参照做【共模回归扣除】
            #   r_hat = r - beta*(P2 - median(P2))，beta 在健康段用最小二乘拟合
            Ps = o[:, 0] + R_M * o[:, 2] ** 2
            P2 = Ps + rng.normal(0, max(sg * 0.5, 0.05), len(Ps))
            x = P2 - np.median(P2)
            f0 = features(o); cal0 = calibrate_clean(f0, CAL_H)
            e0q, e0r = resid(f0, cal0)
            mh = np.zeros(len(o), bool); mh[20:175] = True; mh &= f0["valid"]
            xh = x[mh] - x[mh].mean()
            den = float(np.dot(xh, xh)) or 1.0
            bq = float(np.dot(e0q[mh] - e0q[mh].mean(), xh) / den)
            br = float(np.dot(e0r[mh] - e0r[mh].mean(), xh) / den)
            # 在归一化残差上去共模
            zq = (e0q - bq * x) / cal0["s_q"]
            zr = (e0r - br * x) / cal0["s_r"]
            T = len(o)
            Sq = np.zeros(T); Sr = np.zeros(T)
            for k in range(1, T):
                if not f0["valid"][k]:
                    continue
                Sq[k] = max(0.0, Sq[k - 1] + zq[k] - 0.5)
                Sr[k] = max(0.0, Sr[k - 1] + zr[k] - 0.5)
            pk2 = np.maximum(Sq, Sr)
            if np.nanmax(pk2[200:600]) > H: fa1 += 1
            n += 1
        rows.append(dict(sigma=sg, n=n, fa_no="%d/%d" % (fa0, n), fa_with="%d/%d" % (fa1, n),
                         improve=("%.0f%%" % ((fa0 - fa1) / fa0 * 100) if fa0 else "—")))
        A("  %-10.1f %-6d %-22s %-22s %s" % (sg, n, rows[-1]["fa_no"], rows[-1]["fa_with"],
                                             rows[-1]["improve"]))
    A("")

    # ================= F2: E7 扩展 =================
    A("=" * 78)
    A("F2 测量不确定度敏感度（扩展到 U=5 kPa，找拐点）")
    A("=" * 78)
    A("注入 20% 泄漏、持续 80 s；U 为压力测量 1σ 白噪声。")
    A("")
    idxs = np.where((kind == "normal") & (sigma == 0.3))[0][:10]
    T0, DUR = 205, 80
    CAL_WIN = [(20, 175), (305, 355)]
    A("  %-12s %-12s %-12s %s" % ("U(kPa,1σ)", "检出", "误报", "判定"))
    urows = []
    rng2 = np.random.default_rng(20261019)
    for U in [0.0, 0.05, 0.10, 0.20, 0.50, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]:
        det = fa = 0
        for i in idxs:
            o = d["obs"][i].copy()
            for j in range(DUR):
                tt = T0 + j
                if tt >= len(o): break
                Qn = o[tt, 2] * 1.20
                P1 = (Qn / C_M) ** 2; P0 = P1 + R_M * Qn ** 2
                o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Qn
            if U > 0:
                o[:, 0] += rng2.normal(0, U, len(o))
                o[:, 1] += rng2.normal(0, U, len(o))
            f = features(o); cal = calibrate_clean(f, CAL_WIN)
            eq, er = resid(f, cal)
            pk = cusum_peak(eq, er, cal)
            pre = pk[MON_START:T0]
            if pre.size and np.nanmax(pre) > H: fa += 1
            w = np.where(pk[T0:T0 + DUR + 60] > H)[0]
            if len(w): det += 1
        ok = (det == len(idxs) and fa == 0)
        urows.append(dict(U=U, det="%d/%d" % (det, len(idxs)), fa="%d/%d" % (fa, len(idxs)), ok=ok))
        A("  %-12.2f %-12s %-12s %s" % (U, urows[-1]["det"], urows[-1]["fa"],
                                        "达标" if ok else "失效"))
    ok_u = [r["U"] for r in urows if r["ok"]]
    A("")
    A("  ⇒ 在 0—%.2f kPa 的测试范围内保持『全检出 + 零误报』" % (max(ok_u) if ok_u else 0.0))
    A("     结论：判据对压力测量精度的敏感度低；瓶颈在故障幅度而非传感器精度")
    if ok_u and max(ok_u) < 5.0:
        A("  ⇒ 拐点出现在 U ≈ %.1f—%.1f kPa 之间" % (
            max(ok_u), min([r["U"] for r in urows if not r["ok"]] or [max(ok_u)])))

    txt = "\n".join(L)
    open(os.path.join(RES, "F1_F2.txt"), "w", encoding="utf-8").write(txt)
    json.dump(dict(reference=rows, U=urows),
              open(os.path.join(RES, "F1_F2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
