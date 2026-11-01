# -*- coding: utf-8 -*-
"""E4 修正版：轮灌切换敏感性 —— 在正确门限 h=61 下重测，并评估暂态抑制机制。

修正三处（相对 run_experiments.py 的旧 E4）：
 1) 旧 E4 用 h=5（已被 E3 证伪：健康段误报 40/40），此处改用 h=61；
 2) 旧 E4 只报误报、不报检出损失，无法判断取舍，此处同时统计；
 3) 新增「暂态抑制」：切换暂态期间冻结累积和，检验能否压住切换误报。

物理口径：残差 eq = Q/(gain·Q_ref(P1)) - 1 已按压力补偿，
稳态工况切换应被吸收；真正引起误报的是切换**暂态**（响应滞后）。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from lib_sim import load, parse_ids, features, MON_START, FAULT_START
from E3_corrected import calibrate_clean, resid

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)

H_REC = 61.0
C_MODEL, R_MODEL = 0.280, 0.79
K_SLOPE = 0.5
CAL_WIN = [(20, 175), (305, 355)]


def cusum_series(eq, er, cal, k=K_SLOPE):
    """两路 CUSUM 逐时刻最大值序列。"""
    T = len(eq)
    zq = eq / cal["s_q"]; zr = er / cal["s_r"]
    Sq = np.zeros(T); Sr = np.zeros(T)
    for i in range(1, T):
        Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
        Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    return np.maximum(Sq, Sr)


def cusum_series_masked(eq, er, cal, mask, k=K_SLOPE):
    """暂态抑制版：被屏蔽时刻冻结累积和（不归零，保守处理）。"""
    T = len(eq)
    zq = eq / cal["s_q"]; zr = er / cal["s_r"]
    Sq = np.zeros(T); Sr = np.zeros(T)
    for i in range(1, T):
        if mask[i]:
            Sq[i] = Sq[i - 1]; Sr[i] = Sr[i - 1]
        else:
            Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
            Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    return np.maximum(Sq, Sr)


def transient_mask(f, mult=3.0):
    """以压力 1 秒差分构建暂态掩码：超过健康段稳健尺度的 mult 倍即判为暂态。"""
    p1 = f["p1"]
    d = np.abs(np.diff(p1, prepend=p1[0]))
    base = d[MON_START:FAULT_START]
    base = base[np.isfinite(base)]
    s = 1.4826 * np.median(np.abs(base - np.median(base)))
    thr = max(mult * s, 1e-6)
    return d > thr, thr, float(s)


def inject_switch(o, t0, dur, amp, C=C_MODEL, R=R_MODEL):
    """注入流量阶跃：Q 相对下降 amp，持续 dur 秒后恢复（模拟邻支路抢水）。"""
    o = o.copy()
    for j in range(dur):
        tt = t0 + j
        if tt >= len(o):
            break
        Q = o[tt, 2] * (1.0 - amp)
        P1 = (Q / C) ** 2
        P0 = P1 + R * Q ** 2
        o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Q
    return o


def resid_fixed_n(f, cal, n=0.5):
    """标定失配变体：强制使用名义指数 n=0.5，而非按本条轨迹拟合的 n。"""
    q, p1, Rh = f["q"], f["p1"], f["Rh"]
    m = f["valid"] & np.isfinite(f["K"])
    m &= (np.arange(len(q)) >= MON_START) & (np.arange(len(q)) < FAULT_START)
    lg_a = float(np.exp(np.mean(np.log(q[m]) - n * np.log(p1[m] / 100.0))))
    q_ref = lg_a * (p1 / 100.0) ** n
    gain = float(np.median((q / q_ref)[m]))
    r0 = float(np.median(Rh[m]))
    with np.errstate(invalid="ignore", divide="ignore"):
        eq = q / (gain * q_ref) - 1.0
        er = Rh - r0
    def sc(x, fl):
        return max(float(1.4826 * np.median(np.abs(x - np.median(x)))), fl)
    c2 = dict(cal); c2.update(s_q=sc(eq[m], 1e-5), s_r=sc(er[m], 1e-4))
    return eq, er, c2
    """注入流量阶跃：Q 相对下降 amp，持续 dur 秒后恢复（模拟邻支路抢水）。"""
    o = o.copy()
    for j in range(dur):
        tt = t0 + j
        if tt >= len(o):
            break
        Q = o[tt, 2] * (1.0 - amp)
        P1 = (Q / C) ** 2
        P0 = P1 + R * Q ** 2
        o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Q
    return o


def main():
    d = load(); kind, sigma, seed = parse_ids(d["ids"])
    L = []; A = L.append

    A("=" * 78)
    A("E4 修正版：轮灌切换敏感性（门限 h=%.0f，含暂态抑制对照）" % H_REC)
    A("=" * 78)
    A("口径：在健康轨迹 t=450 注入邻支路抢水阶跃（流量相对下降 amp，持续 T_sw 秒后恢复）")
    A("      误报 = 注入窗口及之后 40 s 内 CUSUM 越过门限；检出损失在文末单独核算")
    A("")

    idxs = np.where((kind == "normal") & (sigma == 1.0))[0][:12]
    A("样本：normal / σ=1.0，n=%d" % len(idxs))
    A("")
    A("  %-10s %-8s %-12s %-12s %-12s %s" % (
        "切换时长(s)", "幅度", "注入前已报", "注入引发", "失配n=0.5", "抑制后引发"))

    rows = []
    for T_sw in [1, 3, 5, 10, 30, 60]:
        for amp in [0.05, 0.10, 0.20]:
            fa_base = fa_inj = fa_mis = fa_msk = 0; n = 0; thrs = []
            for i in idxs:
                o = inject_switch(d["obs"][i], 450, T_sw, amp)
                f = features(o); cal = calibrate_clean(f, CAL_WIN)
                eq, er = resid(f, cal)
                mx_raw = cusum_series(eq, er, cal)
                msk, thr, s = transient_mask(f)
                thrs.append(thr)
                mx_msk = cusum_series_masked(eq, er, cal, msk)
                eq2, er2, c2 = resid_fixed_n(f, cal)
                mx_mis = cusum_series(eq2, er2, c2)
                pre = slice(410, 450)
                seg = slice(450, min(450 + T_sw + 40, len(o)))
                if np.nanmax(mx_raw[pre]) > H_REC: fa_base += 1
                if np.nanmax(mx_raw[seg]) > H_REC: fa_inj += 1
                if np.nanmax(mx_mis[seg]) > H_REC: fa_mis += 1
                if np.nanmax(mx_msk[seg]) > H_REC: fa_msk += 1
                n += 1
            rows.append(dict(T_switch_s=T_sw, amp_rel=amp, n=n,
                             fa_base="%d/%d" % (fa_base, n),
                             fa_inj="%d/%d" % (fa_inj, n),
                             fa_misspec="%d/%d" % (fa_mis, n),
                             fa_masked="%d/%d" % (fa_msk, n),
                             thr=float(np.median(thrs))))
            A("  %-10d %-8.2f %-12s %-12s %-12s %s" % (
                T_sw, amp, rows[-1]["fa_base"], rows[-1]["fa_inj"],
                rows[-1]["fa_misspec"], rows[-1]["fa_masked"]))
    A("")
    A("列含义：注入前已报 = 410—449 s 内已越限（与本次切换无关的既有误报）；")
    A("        注入引发 = 注入窗及后 40 s 内越限；失配 n=0.5 = 强制名义指数时的误报；")
    A("        抑制后引发 = 叠加暂态抑制后的误报。")

    # ---- 抑制机制的代价：真实故障是否也被屏蔽掉 ----
    A("【代价核算】暂态抑制对真实故障检出的影响（h=%.0f）" % H_REC)
    A("  %-12s %-6s %-16s %-16s %s" % (
        "故障", "σ", "检出(裸)", "检出(抑制)", "中位检出t 裸/抑制"))
    cost = []
    for kd in ["leak", "restriction", "drift", "load_unknown"]:
        for sg in [0.3, 1.0, 3.0, 10.0]:
            sel = np.where((kind == kd) & (sigma == sg))[0]
            d_raw = d_msk = 0; tr = []; tm = []
            for i in sel:
                f = features(d["obs"][i]); cal = calibrate_clean(f, CAL_WIN)
                eq, er = resid(f, cal)
                mx_raw = cusum_series(eq, er, cal)
                msk, _, _ = transient_mask(f)
                mx_msk = cusum_series_masked(eq, er, cal, msk)
                w = np.where(mx_raw[FAULT_START:] > H_REC)[0]
                if len(w): d_raw += 1; tr.append(w[0] + FAULT_START)
                w2 = np.where(mx_msk[FAULT_START:] > H_REC)[0]
                if len(w2): d_msk += 1; tm.append(w2[0] + FAULT_START)
            cost.append(dict(kind=kd, sigma=sg,
                             det_raw="%d/%d" % (d_raw, len(sel)),
                             det_masked="%d/%d" % (d_msk, len(sel)),
                             t_raw=float(np.median(tr)) if tr else None,
                             t_masked=float(np.median(tm)) if tm else None))
            A("  %-12s %-6.1f %-16s %-16s %s / %s" % (
                kd, sg, cost[-1]["det_raw"], cost[-1]["det_masked"],
                ("%.0f" % cost[-1]["t_raw"]) if cost[-1]["t_raw"] else "—",
                ("%.0f" % cost[-1]["t_masked"]) if cost[-1]["t_masked"] else "—"))
    A("")
    A("说明：暂态掩码取自压力 1 秒差分的 3 倍稳健尺度；被屏蔽时刻冻结累积和而非归零，")
    A("      因此代价是检出时延增加，而非漏检。数据为合成轨迹（physical_data=False）。")

    txt = "\n".join(L)
    open(os.path.join(RES, "E4_v2.txt"), "w", encoding="utf-8").write(txt + "\n")
    json.dump(dict(rows=rows, cost=cost, h=H_REC),
              open(os.path.join(RES, "E4_v2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
