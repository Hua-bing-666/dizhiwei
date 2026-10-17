# -*- coding: utf-8 -*-
"""不重叠块判据库（block-wise, non-overlapping）。

为什么要有这个库
----------------
既有判据链是：10 s 因果滑动均值 → 每 1 s 出一个判据样本 → CUSUM 逐样本累积。
相邻判据样本重叠 90%，CUSUM 把它们当作独立样本累积，有效样本数被高估约
W 倍（W=10），于是门限被系统性低估。实测表现为：

  * 重叠版 h=61 在 160 条健康轨迹上误报 38.1%（最早 157 s）；
  * 若把误报压到 5%，需要 h≈1045 —— 比教科书量级高一到两个数量级；
  * 根因不是模型不行，而是"样本独立性"假设被破坏。

本库把判据改为**不重叠块**：每 W 秒只出一个判据样本，块内做算术平均。
这样相邻样本之间不再共享原始数据，CUSUM 的独立增量假设成立，门限回到
教科书量级，且门限与 ARL0 之间有可解释的对应关系。

时间分辨率代价：判据更新周期由 1 s 变为 W 秒（W=10 时检出时延以 10 s 计）。

数据真实性：观测来自 simulation/cusum_review/heldout_observations.npz，
为合成数据（physical_data=False），本库结论不可直接外推为实物识别率。
"""
import numpy as np

# ---------- 时间常量（秒）----------
W_DEFAULT = 10          # 块长度，与固件 sampler 的 WINDOW_BINS 一致
CAL_BINS = (2, 18)      # 标定块区间 [起点, 终点)，对应 t=20—180 s
MON_BIN = 18            # 监测起点块索引（t=180 s）
FAULT_BIN = 36          # 故障起始块索引（t=360 s）

# 物理模型常数（与 lib_sim 反推值一致）
C_MODEL = 0.280
R_MODEL = 0.79

# 指数不可辨识：单工况内 P1 跨度仅约 0.34%，log-log 回归随噪声在
# -1.46 ~ -0.19 之间乱跳。故默认固定为孔口出流理论值 0.5。
N_FIXED = 0.5


def blocks(obs_1, W=W_DEFAULT):
    """把 (T,3) 轨迹切成不重叠块，块内取算术平均。

    返回 dict，各数组长度为 nb = T // W（不足一块的尾部丢弃）。
    """
    o = np.asarray(obs_1, float)
    T = len(o)
    nb = T // W
    o = o[:nb * W].reshape(nb, W, 3)
    P0 = o[:, :, 0].mean(axis=1)
    P1 = o[:, :, 1].mean(axis=1)
    Q = o[:, :, 2].mean(axis=1)
    valid = (P1 > 10.0) & (Q > 0.5)
    with np.errstate(invalid="ignore", divide="ignore"):
        Rh = (P0 - P1) / Q ** 2
        K = Q / np.sqrt(P1)
    return dict(p0=P0, p1=P1, q=Q, Rh=Rh, K=K, valid=valid, W=W, nb=nb)


def calib(b, idx=None, n_exp=N_FIXED):
    """在给定块索引上标定健康参照与稳健尺度。

    n_exp: 压力指数。None 表示由 log-log 回归得到（不推荐，见上）。
    """
    if idx is None:
        idx = np.arange(CAL_BINS[0], CAL_BINS[1])
    idx = np.asarray(idx, int)
    v = b["valid"][idx]
    idx = idx[v]
    p1, q, rh = b["p1"][idx], b["q"][idx], b["Rh"][idx]

    if n_exp is None:
        lg = np.polyfit(np.log(p1 / 100.0), np.log(q), 1)
        n = float(lg[0])
    else:
        n = float(n_exp)
    # 几何拟合截距
    a = float(np.exp(np.mean(np.log(q) - n * np.log(p1 / 100.0))))
    q_ref = a * (p1 / 100.0) ** n
    gain = float(np.median(q / q_ref))
    if not np.isfinite(gain) or gain < 1e-9:
        gain = 1.0
    r0 = float(np.median(rh))

    eq = q / (gain * q_ref) - 1.0
    er = rh - r0

    def scale(x, floor):
        m = float(np.median(x))
        s = 1.4826 * float(np.median(np.abs(x - m)))
        return max(s, floor)

    return dict(n=n, a=a, gain=gain, r0=r0,
                s_q=scale(eq, 1e-5), s_r=scale(er, 1e-4),
                n_bins=len(idx))


def resid_blocks(b, cal):
    """全序列块级残差（未归一化）。"""
    q, p1, rh = b["q"], b["p1"], b["Rh"]
    q_ref = cal["a"] * (p1 / 100.0) ** cal["n"]
    with np.errstate(invalid="ignore", divide="ignore"):
        eq = q / (cal["gain"] * q_ref) - 1.0
        er = rh - cal["r0"]
    return eq, er


def cusum_run(eq, er, cal, k=0.5, mask=None):
    """在块序列上运行双路 CUSUM。mask 为 True 表示该块参与累积。"""
    T = len(eq)
    zq = eq / cal["s_q"]
    zr = er / cal["s_r"]
    if mask is None:
        mask = np.ones(T, bool)
    mask = np.asarray(mask, bool) & np.isfinite(zq) & np.isfinite(zr)
    Sq = np.zeros(T)
    Sr = np.zeros(T)
    for i in range(1, T):
        if not mask[i]:
            Sq[i] = Sq[i - 1]
            Sr[i] = Sr[i - 1]
            continue
        Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
        Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    return np.maximum(Sq, Sr), Sq, Sr


def evaluate(o, h, W=W_DEFAULT, k=0.5, cal_idx=None, n_exp=N_FIXED,
             mon_bin=MON_BIN, fault_bin=FAULT_BIN, t_end_bin=None):
    """对单条轨迹跑完整块判据链。

    返回 dict：
      peak_health  健康监测段（mon_bin..fault_bin-1）的 CUSUM 峰值
      fa           健康监测段是否越限
      det          故障段（fault_bin..末）是否越限
      t_det        故障段首次越限的块索引（None 表示未检出）
    """
    b = blocks(o, W)
    c = calib(b, cal_idx, n_exp=n_exp)
    eq, er = resid_blocks(b, c)
    m, _, _ = cusum_run(eq, er, c, k=k)
    nb = b["nb"]
    end = nb if t_end_bin is None else min(t_end_bin, nb)
    seg_h = m[mon_bin:fault_bin]
    seg_f = m[fault_bin:end]
    ph = float(np.nanmax(seg_h)) if seg_h.size else 0.0
    w = np.where(seg_f > h)[0]
    return dict(peak_health=ph, fa=bool(ph > h), det=bool(w.size > 0),
                t_det=(int(w[0] + fault_bin) if w.size else None),
                cal=c, nblocks=nb)


# ---------- 故障注入（块对齐）----------

def inject_leak(o, b0, nb_blk, amp):
    """等效泄漏：负载系数 K = Q/√P1 增大 (1+amp)，区段阻力 Rh 不变。

    实现为**纯乘性扰动**，在观测自身的坐标系内做，不引入模型常数：
        Q  *= (1+amp)
        ΔP *= (1+amp)²        （因 Rh = ΔP/Q² 须保持不变）
        P1  不变
        P0 = P1 + ΔP
    于是 K = Q/√P1 增大 (1+amp)，Rh 严格不变，且逐点噪声结构原样保留。

    ⚠ 两处必须避开的坑
    ------------------
    (1) 既有实现（E6_E7_v2.inject_leak）是「Q *= (1+amp)，再按 Q=C√P1 反解 P1、P0」。
        那等价于保持负载系数 C 不变、抬高供压使流量增大，注入的是**供压扰动**而非泄漏。
        在该口径下 K = Q/√P1 = C 严格不变，泄漏判据检不出任何幅度——本库首次运行时
        连 +50% 都是 0/40，就是这个原因。
    (2) 用 C_MODEL/R_MODEL 重算整条水力关系会破坏数据自洽（数据的实际 C、R 与模型常数
        有偏差，amp=0 都不能还原）。故不采用，改在数据坐标系内做乘性扰动。

    近似与方向：恒供压下真实泄漏还会让 P1 略降（+10% 泄漏约 −1.2%），使 Q 的增幅略小于
    amp。本实现忽略该二阶项，**偏乐观约 1%**。
    """
    o = o.copy()
    t0 = b0 * W_DEFAULT
    t1 = min(t0 + nb_blk * W_DEFAULT, len(o))
    g = 1.0 + amp
    for j in range(t0, t1):
        dp = o[j, 0] - o[j, 1]
        o[j, 2] = o[j, 2] * g
        o[j, 0] = o[j, 1] + dp * g * g
    return o


def inject_restriction(o, b0, nb_blk, rel):
    """等效过流受限：区段阻力 Rh = ΔP/Q² 增大 (1+rel)，负载系数 K 不变。

    同样在数据坐标系内做乘性扰动：
        ΔP *= (1+rel),  P1、Q 不变,  P0 = P1 + ΔP
    于是 Rh 增大 (1+rel)，K = Q/√P1 严格不变，噪声结构原样保留。

    近似与方向：恒供压下真实受限还会让 Q 略降（+30% 阻力约 −0.9%），本实现忽略，
    **偏乐观约 1%**。
    """
    o = o.copy()
    t0 = b0 * W_DEFAULT
    t1 = min(t0 + nb_blk * W_DEFAULT, len(o))
    g = 1.0 + rel
    for j in range(t0, t1):
        dp = o[j, 0] - o[j, 1]
        o[j, 0] = o[j, 1] + dp * g
    return o


def inject_restriction_physical(o, b0, nb_blk, rel, cal=None):
    """受限注入的**物理口径**：恒供压，用**轨迹自身反推**的 C、R 重解水力关系。

    联立  P0 = P1 + R'·Q²,  Q = C·√P1  ⇒  P1 = P0/(1+R'·C²),  Q = C·√P1
    即阻力增大后流量略降、P1 略升、ΔP 明显增大。

    ⚠ 必须用轨迹自身反推的 C、R，不能用全局 C_MODEL/R_MODEL：
    数据的实际参数与模型常数有偏差（实测 K=0.2795 vs 0.280、Rh=0.7733 vs 0.790），
    用全局常数重算会在 rel=0 时都不能还原（P1 偏差 3.6 kPa），注入幅度随之失真。
    cal 为 blocks()+calib() 得到的 dict，取其中 gain·a 与 r0 作为该轨迹的 C、R。

    口径差异（与 inject_restriction 对照）：
      乘性口径     ΔP *= (1+rel)，Q 不变        —— 偏乐观约 1%
      物理口径     Q 略降、P1 略升、ΔP 增大更多  —— 更接近真实受限
    两者都保留，申报口径取**较保守者**。
    """
    o = o.copy()
    if cal is None:
        b = blocks(o)
        cal = calib(b)
    # 在标定段中位 P1 处，把 Q_ref = gain·a·(P1/100)^n 化为 Q = C_eff·√P1 的形式
    p1_ref = float(np.median(blocks(o)["p1"][CAL_BINS[0]:CAL_BINS[1]]))
    C_eff = cal["gain"] * cal["a"] * (p1_ref / 100.0) ** cal["n"] / np.sqrt(p1_ref)
    R_eff = float(cal["r0"])
    Rp = R_eff * (1.0 + rel)
    t0 = b0 * W_DEFAULT
    t1 = min(t0 + nb_blk * W_DEFAULT, len(o))
    for j in range(t0, t1):
        P0 = o[j, 0]
        P1 = P0 / (1.0 + Rp * C_eff ** 2)
        Q = C_eff * np.sqrt(P1)
        o[j, 0] = P0
        o[j, 1] = P1
        o[j, 2] = Q
    return o


# ---------- 真实性缺口扰动（E10 用）----------

def add_sensor_noise(o, sigma_gp=0.0, sigma_dp=0.0, sigma_q_rel=0.0,
                     tau_s=0.0, rng=None):
    """叠加**各通道独立**的传感器测量噪声（既有数据完全没有建模的部分）。

    这是 E10 诊断出的最大建模缺口：既有留出数据的噪声是各通道**共同**的过程扰动
    （供压/流态波动），被比值型特征 K=Q/√P1 与 Rh=ΔP/Q² 抵消掉——实测 K 通道
    稳健尺度仅 0.24%。真实系统除此之外还有**每通道独立**的测量噪声，它们
    **不会**被比值抵消，才是决定 CUSUM 门限的因素。故门限必须在叠加本噪声后重标。

    按物理通道建模（不是简单给三列加噪声）：
        P1_meas = P1 + n_gp          表压变送器噪声
        ΔP_meas = (P0-P1) + n_dp    差压变送器噪声
        P0_meas = P1_meas + ΔP_meas （P0 是重构量，继承两者）
        Q_meas  = Q · (1 + n_q)     流量计噪声（相对）

    设计工况取值（与 BOM v2 冻结规格一致）：
        sigma_gp    = 200 kPa × 0.5%FS = 1.0    kPa
        sigma_dp    =  35 kPa × 0.5%FS = 0.175  kPa
        sigma_q_rel = 1%（SEN0549 标称；10 s 块内脉冲量化约 ±0.38%，并入）

    tau_s: AR(1) 相关时间常数。tau_s=0 为白噪声。
    """
    o = np.asarray(o, float).copy()
    T = len(o)
    if rng is None:
        rng = np.random.default_rng(0)
    phi = 0.0 if tau_s <= 0 else float(np.exp(-1.0 / tau_s))

    def ar1(sigma):
        if sigma <= 0:
            return np.zeros(T)
        amp = sigma * np.sqrt(max(1.0 - phi * phi, 1e-12))
        eps = rng.normal(0.0, amp, T)
        x = np.empty(T)
        x[0] = eps[0] / np.sqrt(max(1.0 - phi * phi, 1e-12))
        for t in range(1, T):
            x[t] = phi * x[t - 1] + eps[t]
        return x

    n_gp = ar1(sigma_gp)
    n_dp = ar1(sigma_dp)
    n_q = ar1(sigma_q_rel) if sigma_q_rel > 0 else np.zeros(T)
    dp_true = o[:, 0] - o[:, 1]
    p1m = o[:, 1] + n_gp
    dpm = dp_true + n_dp
    o[:, 1] = p1m
    o[:, 0] = p1m + dpm
    o[:, 2] = o[:, 2] * (1.0 + n_q)
    return o


def add_ar1_noise(o, sigma, tau_s, rng, channels=(0, 1, 2)):
    """叠加 AR(1) 时间相关噪声（通用版，三列同幅度）。

    仅用于方法学对照；真实传感器噪声请用 add_sensor_noise 按通道建模。
    """
    o = np.asarray(o, float).copy()
    T = len(o)
    if tau_s <= 0:
        phi = 0.0
    else:
        phi = float(np.exp(-1.0 / tau_s))
    amp = sigma * np.sqrt(max(1.0 - phi * phi, 1e-12))
    for ch in channels:
        eps = rng.normal(0.0, amp, T)
        x = np.empty(T)
        x[0] = eps[0] / np.sqrt(max(1.0 - phi * phi, 1e-12))
        for t in range(1, T):
            x[t] = phi * x[t - 1] + eps[t]
        o[:, ch] += x
    return o


def add_ceff_drift(o, rate_per_h, rng=None, kind="ramp", t_start=0.0):
    """负载系数 C_eff = Q/√P1 的缓慢漂移（健康侧的真漂移，不是故障）。

    物理来源：滴头/孔板结垢与微堵、水温变化引起的黏度与出流系数变化、
    滴灌带压力补偿特性的慢时变。这些在田间是**必然存在**的，
    而判据若用固定健康基线，会把慢漂移累积成泄漏报警。

    kind:
      "ramp"  线性斜坡，rate_per_h 为每小时的相对变化率（如 0.02 = 2%/h）
      "rw"    随机游走，rate_per_h 为每小时的漂移标准差尺度
    实现：K *= (1+g(t))，ΔP *= (1+g(t))² 以保持 Rh 不变（纯负载侧漂移）。
    """
    o = np.asarray(o, float).copy()
    T = len(o)
    t = np.arange(T, dtype=float)
    hours = (t - t_start) / 3600.0
    if kind == "ramp":
        g = rate_per_h * hours
    elif kind == "rw":
        if rng is None:
            rng = np.random.default_rng(0)
        steps = rng.normal(0.0, rate_per_h / 60.0, T)   # 每分钟一步
        g = np.cumsum(steps) / 60.0                      # 累积为每小时速率尺度
    else:
        raise ValueError("kind must be 'ramp' or 'rw'")
    fac = 1.0 + g
    dp = o[:, 0] - o[:, 1]
    o[:, 2] = o[:, 2] * fac
    o[:, 0] = o[:, 1] + dp * fac ** 2
    return o


def add_gain_drift(o, delta_q=0.0, delta_p1=0.0, delta_dp=0.0, hours=1.0):
    """传感器增益漂移：测量值 = 真值 × (1 + δ·t/T_end)。

    物理来源：4—20 mA 变送器的温漂与长期稳定性、取样电阻温漂、ADC 参考漂移。
    注意三个通道的增益漂移是**相互独立**的，因此对判据的影响不是简单抵消：

        K  = Q/√P1      ⇒ 相对漂移 ≈ δ_Q − 0.5·δ_P1
        Rh = ΔP/Q²      ⇒ 相对漂移 ≈ δ_ΔP − 2·δ_Q

    即 Q 增益漂 1% 会让 Rh 漂 −2%，ΔP 增益漂 1% 会让 Rh 漂 +1%。
    这是"增益漂移"与"真实故障"最难区分的地方，必须量化容限。
    """
    o = np.asarray(o, float).copy()
    T = len(o)
    u = np.arange(T, dtype=float) / max(T - 1, 1)        # 0→1 全程
    if delta_q:
        o[:, 2] = o[:, 2] * (1.0 + delta_q * u)
    if delta_p1:
        o[:, 1] = o[:, 1] * (1.0 + delta_p1 * u)
    if delta_dp:
        dp = o[:, 0] - o[:, 1]
        o[:, 0] = o[:, 1] + dp * (1.0 + delta_dp * u)
    return o
