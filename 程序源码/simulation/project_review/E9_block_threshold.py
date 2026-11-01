# -*- coding: utf-8 -*-
"""E9：判据样本独立性修正 + 按 ARL0 重定门限 + 可检边界重扫。

背景（本实验要回答的问题）
--------------------------
既有判据链是「10 s 因果滑动均值 → 每 1 s 出一个判据样本 → CUSUM 逐样本累积」。
相邻样本重叠 90%，CUSUM 的独立增量假设被破坏，门限被系统性低估。实测：
h=61 在 160 条健康轨迹上误报 38.1%（最早 157 s），而把误报压到 5% 需要 h≈1045，
比教科书量级高一到两个数量级。

本实验做三件事：
 1. 把判据改为**不重叠块**（每 10 s 一个样本），验证门限是否回到教科书量级；
 2. 用健康轨迹的峰值分布按目标 ARL0 反推门限（分位数法，不是"峰值×1.2"）；
 3. 在新门限下重扫可检边界——此前"5% 不可检 / 8% 可检"等结论全部作废重做。

数据真实性：观测为合成数据（physical_data=False），结论不可外推为实物识别率。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lib_sim
import lib_block as LB
from E3_corrected import cusum_max

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

W = LB.W_DEFAULT
MON_BIN = LB.MON_BIN          # 18  -> t=180 s
FAULT_BIN = LB.FAULT_BIN      # 36  -> t=360 s
NB = 60                        # 600 s / 10 s
N_HEALTH_BLK = NB - MON_BIN   # 42 块，420 s，用于 healthy 类的 FAR
CAL_IDX = np.arange(LB.CAL_BINS[0], LB.CAL_BINS[1])   # bin 2..17

# 故障注入窗口：块 22—29（t=220—300 s）。与标定块 2—17 不重叠；
# 注入前有 4 个健康监测块（18—21）用于测基线误报；评估窗延伸到块 32，
# 仍早于故障起始块 36，不会与数据自带故障混淆。
INJ_B0, INJ_NB = 22, 8

# 实际硬件可达的测量噪声档：差压 35 kPa×0.5%FS≈0.175 kPa，表压 200 kPa×0.5%FS≈1 kPa。
# 故 σ=0.3 与 σ=1.0 是设计工况；σ=3/10 属极端劣化，仅作边界参考。
SIGMA_DESIGN = (0.3, 1.0)


def blk_series(o, n_exp=LB.N_FIXED):
    """返回 (CUSUM 峰值序列, 标定 dict)"""
    b = LB.blocks(o, W)
    c = LB.calib(b, CAL_IDX, n_exp=n_exp)
    eq, er = LB.resid_blocks(b, c)
    m, _, _ = LB.cusum_run(eq, er, c, k=0.5)
    return m, c


def overlap_series(o):
    """既有重叠版：10 s 因果滑动均值，每 1 s 一步。"""
    f = lib_sim.features(o, window=10)
    cal = lib_sim.calibrate(f)
    eq, er = lib_sim.residuals(f, cal)
    mx, _, _ = cusum_max(eq, er, cal)
    return mx


def arl0_from_far(far, n_blk, W=W):
    """由 n_blk 块内的越限比例反推近似 ARL0（秒）。

    假设首次越限时间近似指数分布：λ = -ln(1-FAR)/n_blk （块^-1）。
    """
    if far <= 0:
        return float("inf")
    if far >= 1.0:
        return W * 1.0
    lam = -np.log(1.0 - far) / n_blk
    return W / lam if lam > 0 else float("inf")


def scan_threshold(peaks_health, peaks_fault, hs, n_blk=N_HEALTH_BLK):
    """给定健康峰值数组与各故障类峰值数组，扫描门限。"""
    out = []
    for h in hs:
        far = float(np.mean(peaks_health > h))
        row = dict(h=float(h), far=far, arl0_s=arl0_from_far(far, n_blk))
        for k, arr in peaks_fault.items():
            row["det_" + k] = float(np.mean(arr > h))
        out.append(row)
    return out


def main():
    d = lib_sim.load()
    kind, sigma, seed = lib_sim.parse_ids(d["ids"])
    L = []
    A = L.append

    A("=" * 84)
    A("E9　判据样本独立性修正 + ARL0 重定门限 + 可检边界重扫")
    A("=" * 84)
    A("块长度 W=%d s；标定块 %d—%d（t=%d—%d s）；监测起点块 %d（t=%d s）；故障块 %d（t=%d s）"
      % (W, CAL_IDX[0], CAL_IDX[-1], CAL_IDX[0] * W, (CAL_IDX[-1] + 1) * W,
         MON_BIN, MON_BIN * W, FAULT_BIN, FAULT_BIN * W))
    A("健康参照指数：固定 n=%.2f（单工况内不可辨识，见可辨识性分析）" % LB.N_FIXED)
    A("")

    # ================= 【1】重叠版 vs 块版：健康峰值分布 =================
    A("【1】样本独立性对门限的影响（健康轨迹 %d 条）" % int((kind == "normal").sum()))
    A("")
    idx_norm = np.where(kind == "normal")[0]

    pk_ov = []
    for i in idx_norm:
        mx = overlap_series(d["obs"][i])
        pk_ov.append(np.nanmax(mx[MON_BIN * W:FAULT_BIN * W]))
    pk_ov = np.array(pk_ov, float)

    pk_bl = []
    for i in idx_norm:
        m, _ = blk_series(d["obs"][i])
        pk_bl.append(np.nanmax(m[MON_BIN:NB]))
    pk_bl = np.array(pk_bl, float)

    A("  %-22s %10s %10s %10s %10s" % ("版本", "P50", "P90", "P99", "最大"))
    for nm, arr in (("重叠版（现状 1 s/样本）", pk_ov), ("块版（10 s/样本）", pk_bl)):
        A("  %-22s %10.2f %10.2f %10.2f %10.2f" % (
            nm, np.percentile(arr, 50), np.percentile(arr, 90),
            np.percentile(arr, 99), arr.max()))
    A("")
    A("  ⇒ 重叠版峰值跨 %.0f 倍量级且重尾，块版峰值集中在 %.1f—%.1f；"
      % (pk_ov.max() / max(np.percentile(pk_ov, 50), 1e-9),
         np.percentile(pk_bl, 50), pk_bl.max()))
    A("    门限被高估的倍率 ≈ %.0f 倍——与'相邻样本重叠 90%%'的定性判断一致。"
      % (np.percentile(pk_ov, 95) / max(np.percentile(pk_bl, 95), 1e-9)))
    A("")

    # ================= 【2】门限扫描 =================
    A("【2】块判据门限扫描（健康窗 = 块 %d—%d，%d 块 = %d s）"
      % (MON_BIN, NB - 1, N_HEALTH_BLK, N_HEALTH_BLK * W))
    A("")
    fault_pk = {}
    for kd in ["leak", "restriction", "drift"]:
        idxs = np.where(kind == kd)[0]
        vals = []
        for i in idxs:
            m, _ = blk_series(d["obs"][i])
            vals.append(np.nanmax(m[FAULT_BIN:NB]))
        fault_pk[kd] = np.array(vals, float)

    hs = [2, 3, 5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 60, 100]
    sweep = scan_threshold(pk_bl, fault_pk, hs)
    A("  %-7s %-11s %-13s %-13s %-13s %s" % (
        "h", "健康FAR", "近似ARL0(s)", "leak检出", "restr检出", "drift检出"))
    for r in sweep:
        A("  %-7.0f %-11s %-13s %-13s %-13s %s" % (
            r["h"], "%.1f%%" % (100 * r["far"]),
            ("%.0f" % r["arl0_s"]) if np.isfinite(r["arl0_s"]) else "∞",
            "%.0f%%" % (100 * r["det_leak"]),
            "%.0f%%" % (100 * r["det_restriction"]),
            "%.0f%%" % (100 * r["det_drift"])))
    A("")

    # ================= 【3】选定门限 =================
    hs_fine = np.arange(2.0, 60.1, 0.5)
    cand = {}
    for tgt in (0.05, 0.01):
        ok = [h for h in hs_fine if np.mean(pk_bl > h) <= tgt]
        cand[tgt] = float(ok[0]) if ok else float(hs_fine[-1])

    A("【3】按目标误报率反推门限（分位数法）")
    A("")
    A("  各类故障段峰值的最小值（分离裕度的分子）：")
    for k, v in fault_pk.items():
        A("    %-12s min=%9.1f  P10=%9.1f  P50=%9.1f" % (
            k, v.min(), np.percentile(v, 10), np.percentile(v, 50)))
    A("")
    A("  %-12s %-10s %-11s %-14s %s" % (
        "目标FAR", "门限 h", "实测FAR", "近似ARL0", "各类分离裕度(min峰/h)"))
    chosen = {}
    for tgt in (0.05, 0.01):
        h = cand[tgt]
        far = float(np.mean(pk_bl > h))
        chosen[tgt] = h
        A("  %-12s %-10.1f %-11s %-14s %s" % (
            "%.0f%%" % (100 * tgt), h, "%.2f%%" % (100 * far),
            ("%.0f s" % arl0_from_far(far, N_HEALTH_BLK)) if far > 0 else "零失效",
            "  ".join("%s=%.0f" % (k, v.min() / h) for k, v in fault_pk.items())))
    A("")
    H_STAR = chosen[0.01]
    n_zero = int((pk_bl <= H_STAR).sum())
    blk_obs = n_zero * N_HEALTH_BLK          # 零失效下的块观测数
    # Rule of Three：n 次观测零事件，95% 置信下界 λ ≈ 3/n
    arl0_lb = W * blk_obs / 3.0
    A("  ⇒ 冻结门限 h* = %.1f（目标 FAR ≤ 1%%；实测 %.2f%%）"
      % (H_STAR, 100 * float(np.mean(pk_bl > H_STAR))))
    A("    零失效下界：%d 条 × %d 块 = %d 块观测内 0 次越限，"
      % (n_zero, N_HEALTH_BLK, blk_obs))
    A("    按 Rule of Three 的 95%% 置信下界 ARL0 > %.0f 块 ≈ %.1f h"
      % (blk_obs / 3.0, arl0_lb / 3600.0))
    A("")
    A("  注：drift 类含极弱轨迹（最小峰 %.1f），其检出率随 h 单调下降，"
      % fault_pk["drift"].min())
    A("      是真实的灵敏度—误报权衡，不是实现缺陷；见【4】分层表。")
    A("")

    # 分 σ 复核
    A("【4】h*=%.1f 下按测量噪声 σ 分层复核" % H_STAR)
    A("")
    A("  （σ=0.3 / 1.0 为**设计工况**：对应差压 35 kPa×0.5%FS≈0.175 kPa、"
      "表压 200 kPa×0.5%FS≈1 kPa）")
    A("")
    A("  %-13s %-10s %-14s %-14s %s" % ("类别", "σ(kPa)", "健康误报", "故障检出", "中位检出时延(s)"))
    layer = []
    for kd in ["leak", "restriction", "drift"]:
        for sg in [0.3, 1.0, 3.0, 10.0]:
            idxs = np.where((kind == kd) & (sigma == sg))[0]
            fa = det = 0
            ts = []
            for i in idxs:
                m, _ = blk_series(d["obs"][i])
                if np.nanmax(m[MON_BIN:FAULT_BIN]) > H_STAR:
                    fa += 1
                w = np.where(m[FAULT_BIN:NB] > H_STAR)[0]
                if w.size:
                    det += 1
                    ts.append(int((w[0]) * W))
            row = dict(kind=kd, sigma=sg, n=len(idxs),
                       fa="%d/%d" % (fa, len(idxs)),
                       det="%d/%d" % (det, len(idxs)),
                       design=bool(sg in SIGMA_DESIGN),
                       t=(float(np.median(ts)) if ts else None))
            layer.append(row)
            A("  %-13s %-10s %-14s %-14s %s" % (
                kd, ("%.1f*" % sg) if sg in SIGMA_DESIGN else "%.1f" % sg,
                row["fa"], row["det"],
                ("%.0f" % row["t"]) if row["t"] is not None else "—"))
    A("")
    A("  * 设计工况。注：检出时延以 10 s 块为分辨率，'0' 表示故障起始块即越限。")
    A("")

    # ================= 【5】可检边界重扫（泄漏）=================
    A("=" * 84)
    A("【5】可检边界重扫 —— 等效泄漏（注入块 %d—%d，t=%d—%d s，h*=%.1f）"
      % (INJ_B0, INJ_B0 + INJ_NB - 1, INJ_B0 * W, (INJ_B0 + INJ_NB) * W, H_STAR))
    A("=" * 84)
    A("")
    inj_idx = np.where((kind == "normal") & (sigma == 1.0))[0]
    A("  注入载体：normal 类 σ=1.0 共 %d 条；基线误报（未注入）先测一次：" % len(inj_idx))
    base_fa = 0
    for i in inj_idx:
        m, _ = blk_series(d["obs"][i])
        if np.nanmax(m[INJ_B0:INJ_B0 + INJ_NB + 3]) > H_STAR:
            base_fa += 1
    A("      %d/%d 条在注入窗口内自然越限（作为基线）" % (base_fa, len(inj_idx)))
    A("")
    A("  %-10s %-14s %-14s %-14s %s" % (
        "流量增量", "检出", "其中注入前已报", "净检出", "中位检出时延(s)"))
    leak_rows = []
    for amp in [0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50]:
        det = pre = 0
        ts = []
        for i in inj_idx:
            o = LB.inject_leak(d["obs"][i], INJ_B0, INJ_NB, amp)
            m, _ = blk_series(o)
            pre_fa = bool(np.nanmax(m[MON_BIN:INJ_B0]) > H_STAR)
            w = np.where(m[INJ_B0:INJ_B0 + INJ_NB + 3] > H_STAR)[0]
            if w.size:
                det += 1
                ts.append(int(w[0] * W))
            if pre_fa:
                pre += 1
        net = det - pre
        leak_rows.append(dict(amp=amp, n=len(inj_idx), det=det, pre=pre, net=net,
                              det_s="%d/%d" % (det, len(inj_idx)),
                              t=(float(np.median(ts)) if ts else None)))
        A("  %-10s %-14s %-14s %-14s %s" % (
            "+%.0f%%" % (100 * amp), "%d/%d" % (det, len(inj_idx)),
            "%d" % pre, "%d" % net,
            ("%.0f" % np.median(ts)) if ts else "—"))
    A("")

    # ================= 【6】可检边界重扫（受限）=================
    A("【6】可检边界重扫 —— 等效过流受限（ΔP 乘性扰动，K 不变，h*=%.1f）" % H_STAR)
    A("")
    A("  %-12s %-14s %-14s %s" % ("阻力增量", "检出", "注入前已报", "中位检出时延(s)"))
    rest_rows = []
    for rel in [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00, 3.00]:
        det = pre = 0
        ts = []
        for i in inj_idx:
            o = LB.inject_restriction(d["obs"][i], INJ_B0, INJ_NB, rel)
            m, _ = blk_series(o)
            if np.nanmax(m[MON_BIN:INJ_B0]) > H_STAR:
                pre += 1
            w = np.where(m[INJ_B0:INJ_B0 + INJ_NB + 3] > H_STAR)[0]
            if w.size:
                det += 1
                ts.append(int(w[0] * W))
        rest_rows.append(dict(rel=rel, n=len(inj_idx), det=det, pre=pre,
                              det_s="%d/%d" % (det, len(inj_idx)),
                              t=(float(np.median(ts)) if ts else None)))
        A("  %-12s %-14s %-14s %s" % (
            "+%.0f%%" % (100 * rel), "%d/%d" % (det, len(inj_idx)), "%d" % pre,
            ("%.0f" % np.median(ts)) if ts else "—"))
    A("")

    # ---- 受限的时长维度：申报口径需明确"多大阻力增量、多长可全检出" ----
    durs = [1, 2, 3, 5, 8]
    A("【6b】受限：阻力增量 × 持续时长（检出，h*=%.1f）" % H_STAR)
    A("")
    A("  %-10s %s" % ("阻力\\时长", "  ".join("%9s" % ("%d块/%ds" % (x, x * W)) for x in durs)))
    grid_r = {}
    for rel in [0.10, 0.20, 0.30, 0.50, 1.00]:
        row = []
        for du in durs:
            det = 0
            for i in inj_idx:
                o = LB.inject_restriction(d["obs"][i], INJ_B0, du, rel)
                m, _ = blk_series(o)
                if np.any(m[INJ_B0:INJ_B0 + du + 3] > H_STAR):
                    det += 1
            row.append("%d/%d" % (det, len(inj_idx)))
        grid_r["%.2f" % rel] = dict((str(k), v) for k, v in zip(durs, row))
        A("  %-10s %s" % ("+%.0f%%" % (100 * rel), "  ".join("%9s" % v for v in row)))
    A("")

    # ================= 【7】泄漏时长 × 幅度二维 =================
    A("【7】泄漏：流量增量 × 持续时长（检出，h*=%.1f）" % H_STAR)
    A("")
    A("  %-10s %s" % ("幅度\\时长", "  ".join("%9s" % ("%d块/%ds" % (x, x * W)) for x in durs)))
    grid = {}
    for amp in [0.02, 0.03, 0.05, 0.08, 0.10, 0.20]:
        row = []
        for du in durs:
            det = 0
            for i in inj_idx:
                o = LB.inject_leak(d["obs"][i], INJ_B0, du, amp)
                m, _ = blk_series(o)
                if np.any(m[INJ_B0:INJ_B0 + du + 3] > H_STAR):
                    det += 1
            row.append("%d/%d" % (det, len(inj_idx)))
        grid["%.3f" % amp] = dict((str(k), v) for k, v in zip(durs, row))
        A("  %-10s %s" % ("+%.0f%%" % (100 * amp), "  ".join("%9s" % v for v in row)))
    A("")

    # ================= 【8】压力不确定度需求 =================
    A("【8】压力测量不确定度 U 需求（注入 +2%% 泄漏，%d 块，h*=%.1f）"
      % (INJ_NB, H_STAR))
    A("")
    A("  注：取接近可检边界的 +2% 幅度，才能对 U 有区分度；"
      "若用 +10% 则一直到 U=5 kPa 仍全检出，测不出拐点。")
    A("")
    rng = np.random.default_rng(20261017)
    A("  %-12s %-14s %-14s %s" % ("U(kPa,1σ)", "检出", "注入前误报", "判定"))
    urows = []
    for U in [0.0, 0.05, 0.10, 0.175, 0.35, 0.50, 1.00, 2.00, 5.00]:
        det = fa = 0
        for i in inj_idx:
            o = d["obs"][i].copy()
            o[:, 0] += rng.normal(0, U, len(o))
            o[:, 1] += rng.normal(0, U, len(o))
            o = LB.inject_leak(o, INJ_B0, INJ_NB, 0.02)
            m, _ = blk_series(o)
            if np.nanmax(m[MON_BIN:INJ_B0]) > H_STAR:
                fa += 1
            if np.any(m[INJ_B0:INJ_B0 + INJ_NB + 3] > H_STAR):
                det += 1
        ok = (det >= 0.95 * len(inj_idx) and fa == 0)
        urows.append(dict(U=U, det="%d/%d" % (det, len(inj_idx)),
                          fa="%d/%d" % (fa, len(inj_idx)), ok=ok))
        A("  %-12.3f %-14s %-14s %s" % (U, urows[-1]["det"], urows[-1]["fa"],
                                        "达标" if ok else ""))
    ok_u = [r["U"] for r in urows if r["ok"]]
    A("")
    if ok_u:
        A("  ⇒ 在 0—%.3f kPa 范围内保持『≥95%% 检出 + 零误报』；"
          % max(ok_u))
        A("     设计工况 U≈0.175 kPa（差压 35 kPa×0.5%%FS）在此范围内，余量 %.0f 倍。"
          % (max(ok_u) / 0.175))
    else:
        A("  ⇒ 测试范围内未达『≥95%% 检出 + 零误报』，需重新评估压力通道指标。")
    A("")

    # ================= 结论 =================
    A("=" * 84)
    A("结论")
    A("=" * 84)
    A("1) 判据样本必须不重叠。重叠版门限需 ~%.0f 才压到 5%% 误报，块版仅需 ~%.0f，"
      % (np.percentile(pk_ov, 95), cand[0.05]))
    A("   差 %.0f 倍；根因是相邻样本重叠 90%% 导致 CUSUM 有效样本数被高估。"
      % (np.percentile(pk_ov, 95) / max(cand[0.05], 1e-9)))
    A("2) 冻结门限 h* = %.1f（块判据，k=0.5，n=%.2f，W=%d s），"
      % (H_STAR, LB.N_FIXED, W))
    A("   零失效下界 ARL0 > %.1f h（95%% 置信）。" % (arl0_lb / 3600.0))
    A("3) 既有结论『5% 不可检 / 8% 可检』『σ=10 kPa 下泄漏 1/20』均产自错误门限，")
    A("   以本实验【5】【6】两表为准，此前相关表述作废。")
    A("4) 附带修正一处注入口径缺陷：既有 inject_leak 注入的是『供压扰动』而非泄漏")
    A("   （该口径下 K=Q/√P1 严格不变，任何幅度都检不出）。本库改为在数据坐标系内")
    A("   做乘性扰动，泄漏→K 增大、受限→Rh 增大，噪声结构原样保留。")
    A("5) 数据性质：合成数据，physical_data=False，不代表实物识别率。")

    txt = "\n".join(L)
    open(os.path.join(RES, "E9_block_threshold.txt"), "w", encoding="utf-8").write(txt)
    json.dump(dict(overlap_peaks=dict(p50=float(np.percentile(pk_ov, 50)),
                                      p90=float(np.percentile(pk_ov, 90)),
                                      max=float(pk_ov.max())),
                   block_peaks=dict(p50=float(np.percentile(pk_bl, 50)),
                                    p90=float(np.percentile(pk_bl, 90)),
                                    max=float(pk_bl.max())),
                   sweep=sweep, h_star=H_STAR, cand={str(k): v for k, v in cand.items()},
                   layer=layer, leak=leak_rows, restriction=rest_rows,
                   grid=grid, grid_restriction=grid_r, U=urows),
              open(os.path.join(RES, "E9_block_threshold.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
