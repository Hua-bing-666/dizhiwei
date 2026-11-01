# -*- coding: utf-8 -*-
"""项目仿真实验 E2—E8：判据对比、ARL0、切换敏感性、参照差分、二维边界、U 需求、真实节拍校核。

数据基础（已核实）：观测来自 heldout_observations.npz，
反推 R=0.79、C=0.280、log-log 指数 n=0.49，与申报书 R=0.8/Cn=0.28/n=0.5 一致。
"""
import os, sys, json, itertools
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

from lib_sim import (load, parse_ids, features, calibrate, residuals,
                     detector_original, detector_cusum,
                     MON_START, FAULT_START, T_END)

# ---------- 全局标定口径（诊断后修正：跨工况联合标定）----------
CAL_WINDOWS = [(20, 175), (300, 599)]     # B 阀“关”的工况


def calib_mask(T):
    m = np.zeros(T, bool)
    for lo, hi in CAL_WINDOWS:
        m[lo:min(hi + 1, T)] = True
    return m


def calibrate2(f, windows=CAL_WINDOWS, N=1):
    """改进标定：跨工况联合 + 可调平均窗长 N。

    先按窗口内的点拟合 n，再算增益、r0 与稳健尺度。
    """
    T = len(f["valid"])
    m = np.zeros(T, bool)
    for lo, hi in windows:
        m[lo:min(hi + 1, T)] = True
    m &= f["valid"] & np.isfinite(f["K"])
    p1, q, rh = f["p1"][m], f["q"][m], f["Rh"][m]
    lg = np.polyfit(np.log(p1 / 100.0), np.log(q), 1)
    n, a = float(lg[0]), float(np.exp(lg[1]))
    q_ref = a * (p1 / 100.0) ** n
    gain = float(np.median(q / q_ref))
    r0 = float(np.median(rh))
    eq = q / (gain * q_ref) - 1.0
    er = rh - r0

    def sc(x, floor):
        s = 1.4826 * np.median(np.abs(x - np.median(x)))
        return max(float(s), floor)
    return dict(n=n, a=a, gain=gain, r0=r0,
                s_q=sc(eq, 1e-5), s_r=sc(er, 1e-4))


def residuals2(f, cal):
    q, p1, Rh = f["q"], f["p1"], f["Rh"]
    q_ref = cal["a"] * (p1 / 100.0) ** cal["n"]
    with np.errstate(invalid="ignore", divide="ignore"):
        return q / (cal["gain"] * q_ref) - 1.0, Rh - cal["r0"]


def first_conf(conf, lo=MON_START):
    w = np.where(conf[lo:] > 0)[0]
    return int(w[0] + lo) if len(w) else None


def run_cusum(eq, er, cal, k=0.5, h=5.0, valid=None):
    T = len(eq)
    if valid is None:
        valid = np.ones(T, bool)
    zq = np.where(valid, eq / cal["s_q"], 0.0)
    zr = np.where(valid, er / cal["s_r"], 0.0)
    Sq = np.zeros(T); Sr = np.zeros(T)
    for i in range(1, T):
        Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
        Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    a = Sq > h; b = Sr > h
    lab = np.zeros(T, int)
    lab[a & ~b] = 1; lab[b & ~a] = 2; lab[a & b] = 3
    return dict(Sq=Sq, Sr=Sr, label=lab)


def orig_label(eq, er, valid, th_q=0.06, th_r=0.6):
    a = (eq > th_q) & valid
    b = (er > th_r) & valid
    lab = np.zeros(len(eq), int)
    lab[a & ~b] = 1; lab[b & ~a] = 2; lab[a & b] = 3
    return lab


def persist(lab, n):
    out = np.zeros(len(lab), int); cnt = 0; cur = 0
    for i in range(len(lab)):
        if lab[i] > 0 and lab[i] == cur:
            cnt += 1
        elif lab[i] > 0:
            cur = lab[i]; cnt = 1
        else:
            cur = 0; cnt = 0
        if cnt >= n:
            out[i] = cur
    return out


# =====================================================================
def E2_E3(d, kind, sigma):
    """E2 判据对比 + E3 ARL0"""
    out = {"E2": [], "E3": {}}
    # ---- E2：在三类轨迹上比检出时刻与误报 ----
    rows = []
    for kd in ["leak", "restriction"]:
        for sg in [0.3, 1.0, 3.0, 10.0]:
            idxs = np.where((kind == kd) & (sigma == sg))[0]
            n_leak_orig = n_leak_cus = 0
            t_orig, t_cus = [], []
            fa_orig = fa_cus = 0
            for i in idxs:
                f = features(d["obs"][i]); cal = calibrate2(f)
                eq, er = residuals2(f, cal); v = f["valid"]
                lo = persist(orig_label(eq, er, v), 5)
                cu = run_cusum(eq, er, cal, valid=v)["label"]
                # 故障前误报
                if np.any(lo[MON_START:FAULT_START] > 0): fa_orig += 1
                if np.any(cu[MON_START:FAULT_START] > 0): fa_cus += 1
                to = first_conf(lo); tc = first_conf(cu)
                if to is not None: t_orig.append(to)
                if tc is not None: t_cus.append(tc)
            rows.append(dict(kind=kd, sigma=sg, n=len(idxs),
                             t_orig=(np.median(t_orig) if t_orig else None),
                             t_cus=(np.median(t_cus) if t_cus else None),
                             detect_orig="%d/%d" % (len(t_orig), len(idxs)),
                             detect_cus="%d/%d" % (len(t_cus), len(idxs)),
                             fa_orig="%d/%d" % (fa_orig, len(idxs)),
                             fa_cus="%d/%d" % (fa_cus, len(idxs))))
    out["E2"] = rows

    # ---- E3：ARL0（健康工况长序列）----
    # 把 normal 轨迹（σ=0.3/1/3）的 B 阀“关”工况拼成长序列
    arl = {}
    for sg in [0.3, 1.0, 3.0, 10.0]:
        idxs = np.where((kind == "normal") & (sigma == sg))[0]
        for h in [3, 4, 5, 6, 8, 10]:
            runs = []
            for i in idxs:
                f = features(d["obs"][i]); cal = calibrate2(f)
                eq, er = residuals2(f, cal); v = f["valid"]
                lab = run_cusum(eq, er, cal, h=h, valid=v)["label"]
                # 取 B 阀关的健康段（20-175 与 300-599），统计首次报警位置
                for lo, hi in [(MON_START, 175), (300, 599)]:
                    seg = lab[lo:hi]
                    w = np.where(seg > 0)[0]
                    if len(w):
                        runs.append(int(w[0]))
                    else:
                        runs.append(len(seg))
            runs = np.array(runs, float)
            # 若全部未报警，ARL 取下限（右删失）
            censored = np.mean(runs >= (599 - 300)) if len(runs) else 0.0
            arl["sigma=%.1f|h=%d" % (sg, h)] = dict(
                n=len(runs), mean_minutes=float(np.mean(runs)) / 60.0,
                median_minutes=float(np.median(runs)) / 60.0,
                min_minutes=float(np.min(runs)) / 60.0,
                frac_no_alarm=float(censored))
    out["E3"] = arl
    return out


def E4(d, kind, sigma):
    """E4 切换敏感性：注入不同时长/幅度的流量阶跃，看误报率"""
    out = []
    idxs = np.where((kind == "normal") & (sigma == sigma))[0][:12]
    C, R = 0.280, 0.79
    for T_sw in [1, 3, 5, 10, 30, 60]:
        for amp in [0.05, 0.10, 0.20]:
            fa_cus = fa_orig = 0; n = 0
            for i in idxs:
                o = d["obs"][i].copy()
                # 在 t=450 处注入：Q 阶跃 -amp 相对量，线性过渡 T_sw 秒后回到原值
                t0 = 450
                for j in range(T_sw):
                    tt = t0 + j
                    if tt >= T_sw + t0 or tt >= len(o):
                        break
                    w = 1.0 if j < T_sw else 0.0
                    scale = 1.0 - amp * w
                    Q = o[tt, 2] * scale
                    P1 = (Q / C) ** 2
                    P0 = P1 + R * Q ** 2
                    o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Q
                f = features(o); cal = calibrate2(f)
                eq, er = residuals2(f, cal); v = f["valid"]
                lo = persist(orig_label(eq, er, v), 5)
                cu = run_cusum(eq, er, cal, valid=v)["label"]
                seg = slice(t0, min(t0 + T_sw + 40, len(o)))
                if np.any(lo[seg] > 0): fa_orig += 1
                if np.any(cu[seg] > 0): fa_cus += 1
                n += 1
            out.append(dict(T_switch_s=T_sw, amp_rel=amp, n=n,
                            fa_orig="%d/%d" % (fa_orig, n),
                            fa_cusum="%d/%d" % (fa_cus, n)))
    return out


def E5(d, kind, sigma):
    """E5 干管参照差分收益：加一路上游参照后的误报率变化"""
    from lib_sim import load
    out = []
    rng = np.random.default_rng(20261014)
    for sg in [0.3, 1.0, 3.0, 10.0]:
        idxs = np.where((kind == "supply") & (sigma == sg))[0]
        fa_wo = fa_w = 0; n = 0
        for i in idxs:
            o = d["obs"][i].copy()
            f = features(o); cal = calibrate2(f)
            eq, er = residuals2(f, cal); v = f["valid"]
            lab = run_cusum(eq, er, cal, valid=v)["label"]
            if np.any(lab[MON_START:FAULT_START] > 0): fa_wo += 1
            # 构造“干管参照”：用 P0 加独立噪声模拟首部测点，做一阶差分归一化
            Ps = o[:, 0] + 0.79 * o[:, 2] ** 2          # 反推供压
            Ps_ref = Ps + rng.normal(0, sg * 0.5, len(Ps))
            # 用参照归一化 P0
            o2 = o.copy()
            o2[:, 0] = o[:, 0] - (Ps_ref - np.median(Ps_ref))
            f2 = features(o2); cal2 = calibrate2(f2)
            eq2, er2 = residuals2(f2, cal2); v2 = f2["valid"]
            lab2 = run_cusum(eq2, er2, cal2, valid=v2)["label"]
            if np.any(lab2[MON_START:FAULT_START] > 0): fa_w += 1
            n += 1
        out.append(dict(sigma=sg, n=n,
                        false_alarm_no_ref="%d/%d" % (fa_wo, n),
                        false_alarm_with_ref="%d/%d" % (fa_w, n)))
    return out


def E6(d, kind, sigma=1.0):
    """E6 二维可检边界：故障幅度 × 持续时长"""
    C, R = 0.280, 0.79
    out = []
    amps = [0.03, 0.05, 0.08, 0.10, 0.15, 0.20]
    durs = [5, 15, 30, 60, 120, 300]
    idxs = np.where((kind == "normal") & (sigma == sigma))[0][:8]
    for amp in amps:
        row = []
        for dur in durs:
            det = 0; n = 0
            for i in idxs:
                o = d["obs"][i].copy()
                t0 = 400
                for j in range(dur):
                    tt = t0 + j
                    if tt >= len(o): break
                    Q = o[tt, 2] * (1 + amp)         # 泄漏：Q 增大
                    P1 = (Q / C) ** 2
                    P0 = P1 + R * Q ** 2
                    o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Q
                f = features(o); cal = calibrate2(f)
                eq, er = residuals2(f, cal); v = f["valid"]
                lab = run_cusum(eq, er, cal, valid=v)["label"]
                seg = slice(MON_START, FAULT_START)
                if np.any(lab[seg] > 0):
                    n += 1; continue          # 故障前误报，不计
                w = np.where(lab[t0:t0 + dur + 60] > 0)[0]
                if len(w): det += 1
                n += 1
            row.append("%d/%d" % (det, n))
        out.append(dict(amplitude=amp, by_duration=dict((str(k), v) for k, v in zip(durs, row))))
    return out


def E7(d, kind, sigma=0.3):
    """E7 反推测量不确定度需求：加不同水平压力噪声，看可检边界"""
    C, R = 0.280, 0.79
    out = []
    rng = np.random.default_rng(20261015)
    idxs = np.where((kind == "normal") & (sigma == sigma))[0][:8]
    for U in [0.02, 0.05, 0.09, 0.15, 0.30, 0.50, 1.00]:   # kPa, 视为 1σ
        det = 0; fa = 0; n = 0
        for i in idxs:
            o = d["obs"][i].copy()
            # 故障段注入 +10% 泄漏，持续 300s；全段加测量噪声
            t0 = 400
            for j in range(300):
                tt = t0 + j
                if tt >= len(o): break
                Q = o[tt, 2] * 1.10
                P1 = (Q / C) ** 2; P0 = P1 + R * Q ** 2
                o[tt, 0] = P0; o[tt, 1] = P1; o[tt, 2] = Q
            o[:, 0] += rng.normal(0, U, len(o))
            o[:, 1] += rng.normal(0, U, len(o))
            f = features(o); cal = calibrate2(f)
            eq, er = residuals2(f, cal); v = f["valid"]
            lab = run_cusum(eq, er, cal, valid=v)["label"]
            if np.any(lab[MON_START:FAULT_START] > 0): fa += 1
            w = np.where(lab[t0:t0 + 360] > 0)[0]
            if len(w): det += 1
            n += 1
        out.append(dict(U_kPa=U, detected="%d/%d" % (det, n), false_alarm="%d/%d" % (fa, n)))
    return out


def E8(d, kind, sigma=1.0):
    """E8 真实灌水节拍校核：把一天切成 灌水窗口 + 停灌，看判据能否工作"""
    out = []
    # 一次灌水 0.4—1.8h；停灌至下一轮。按 1Hz 采样，一天 86400 点太大，
    # 用“时间压缩”思路：只统计判据在“有流量”与“无流量”时的行为。
    C, R = 0.280, 0.79
    idxs = np.where((kind == "normal") & (sigma == sigma))[0][:8]
    for win_min in [24, 60, 108]:          # 0.4h / 1.0h / 1.8h
        det = 0; fa = 0; n = 0
        for i in idxs:
            o = d["obs"][i].copy()
            # 前 360s 作为“本灌水窗口”，后 240s 作为“停灌”（Q→0，P→静压）
            t0 = 360
            for tt in range(t0, len(o)):
                o[tt, 2] = 0.02                       # 停灌：流量近零
                o[tt, 1] = 100.0                      # 静压
                o[tt, 0] = 100.0
            f = features(o); cal = calibrate2(f)
            eq, er = residuals2(f, cal); v = f["valid"]
            lab = run_cusum(eq, er, cal, valid=v)["label"]
            # 停灌段不应报警（Q 不合法 → valid=False → 不报警）
            if np.any(lab[t0:] > 0): fa += 1
            # 灌水段注入 +10% 故障
            o2 = d["obs"][i].copy()
            for tt in range(180, 360):
                Q = o2[tt, 2] * 1.10
                P1 = (Q / C) ** 2; P0 = P1 + R * Q ** 2
                o2[tt, 0] = P0; o2[tt, 1] = P1; o2[tt, 2] = Q
            f2 = features(o2); cal2 = calibrate2(f2)
            eq2, er2 = residuals2(f2, cal2); v2 = f2["valid"]
            lab2 = run_cusum(eq2, er2, cal2, valid=v2)["label"]
            w = np.where(lab2[180:360] > 0)[0]
            if len(w): det += 1
            n += 1
        out.append(dict(window_min=win_min, n=n,
                        detect_in_window="%d/%d" % (det, n),
                        false_alarm_in_idle="%d/%d" % (fa, n)))
    return out


def main():
    d = load(); kind, sigma, seed = parse_ids(d["ids"])
    d["sigma"] = sigma
    rep = {}
    print("E2/E3 ..."); rep.update(E2_E3(d, kind, sigma))
    print("E4 ...");    rep["E4"] = E4(d, kind, 1.0)
    print("E5 ...");    rep["E5"] = E5(d, kind, sigma)
    print("E6 ...");    rep["E6"] = E6(d, kind, 1.0)
    print("E7 ...");    rep["E7"] = E7(d, kind)
    print("E8 ...");    rep["E8"] = E8(d, kind, 1.0)
    with open(os.path.join(RES, "E_report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1, default=float)

    # 文本报告
    L = []
    A = L.append
    A("=" * 74); A("E2 判据对比（原双阈值+5次确认  vs  CUSUM h=5）"); A("=" * 74)
    A("  %-12s %-6s %-9s %-11s %-11s %-10s %s" % (
        "故障", "σ(kPa)", "检出(原)", "检出(CUSUM)", "中位t(原)", "中位t(CU)", "故障前误报 原/CU"))
    for r in rep["E2"]:
        A("  %-12s %-6.1f %-9s %-11s %-11s %-10s %s / %s" % (
            r["kind"], r["sigma"], r["detect_orig"], r["detect_cus"],
            ("%.0f" % r["t_orig"]) if r["t_orig"] else "—",
            ("%.0f" % r["t_cus"]) if r["t_cus"] else "—",
            r["fa_orig"], r["fa_cus"]))
    A("")
    A("=" * 74); A("E3 CUSUM 门限 h 与平均误报间隔 ARL0"); A("=" * 74)
    A("  %-22s %-6s %-14s %-14s %s" % ("条件", "样本", "均值(分钟)", "中位(分钟)", "未报警比例"))
    for k, v in rep["E3"].items():
        A("  %-22s %-6d %-14.2f %-14.2f %.2f" % (
            k, v["n"], v["mean_minutes"], v["median_minutes"], v["frac_no_alarm"]))
    A("")
    A("=" * 74); A("E4 切换敏感性（注入不同时长/幅度的流量阶跃）"); A("=" * 74)
    A("  %-10s %-8s %-8s %s" % ("切换时长(s)", "幅度", "样本", "误报 原/CUSUM"))
    for r in rep["E4"]:
        A("  %-10d %-8.2f %-8d %s / %s" % (
            r["T_switch_s"], r["amp_rel"], r["n"], r["fa_orig"], r["fa_cusum"]))
    A("")
    A("=" * 74); A("E5 干管参照差分收益（供压扰动场景）"); A("=" * 74)
    A("  %-10s %-8s %-20s %s" % ("σ(kPa)", "样本", "无误报 无参照组", "有参照组"))
    for r in rep["E5"]:
        A("  %-10.1f %-8d %-20s %s" % (
            r["sigma"], r["n"], r["false_alarm_no_ref"], r["false_alarm_with_ref"]))
    A("")
    A("=" * 74); A("E6 二维可检边界（泄漏幅度 × 持续时长，σ=1.0kPa）"); A("=" * 74)
    durs = [5, 15, 30, 60, 120, 300]
    A("  幅度\\时长  " + "  ".join("%6ds" % x for x in durs))
    for r in rep["E6"]:
        A("  %6.1f%%    " % (r["amplitude"] * 100) +
          "  ".join("%7s" % r["by_duration"][str(x)] for x in durs))
    A("")
    A("=" * 74); A("E7 反推测量不确定度需求（+10% 泄漏，持续 300s）"); A("=" * 74)
    A("  %-12s %-12s %s" % ("U(kPa,1σ)", "检出", "故障前误报"))
    for r in rep["E7"]:
        A("  %-12.2f %-12s %s" % (r["U_kPa"], r["detected"], r["false_alarm"]))
    A("")
    A("=" * 74); A("E8 真实灌水节拍校核"); A("=" * 74)
    A("  %-14s %-8s %-18s %s" % ("灌水窗口(min)", "样本", "窗口内检出", "停灌段误报"))
    for r in rep["E8"]:
        A("  %-14d %-8d %-18s %s" % (
            r["window_min"], r["n"], r["detect_in_window"], r["false_alarm_in_idle"]))
    txt = "\n".join(L)
    with open(os.path.join(RES, "E_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
