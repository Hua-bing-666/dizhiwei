# -*- coding: utf-8 -*-
"""项目仿真核心库：读数据、算特征、跑判据（原双阈值 / CUSUM）。

数据真实性说明：
  观测来自 simulation/cusum_review/heldout_observations.npz
  经反推核实：R=(P0-P1)/Q^2 中位 0.7928、C=Q/sqrt(P1) 中位 0.2799、
  log-log 拟合指数 n=0.4914，与申报书 R=0.8 / Cn=0.28 / n=0.5 一致。
"""
import numpy as np
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NPZ = os.path.join(ROOT, "cusum_review", "heldout_observations.npz")
OUT = HERE

# ---------- 标定窗口与监测起点（与既有冻结口径一致）----------
CAL_START, CAL_END = 20, 119      # 健康标定段
MON_START = 130                    # 监测起点
FAULT_START = 360                  # 故障起始（数据内）
T_END = 600

# ---------- 判据参数 ----------
TH_Q = 0.06          # 原判据：相对流量偏离阈值
TH_R = 0.6           # 原判据：阻力绝对增加阈值
PERSIST = 5          # 原判据：连续确认次数
K_CUSUM = 0.5        # CUSUM 参考值
H_CUSUM = 5.0        # CUSUM 门限（默认）


def load():
    z = np.load(NPZ, allow_pickle=True)
    return dict(obs=z["observed"], ids=z["trial_ids"], t=z["t"])


def parse_ids(ids):
    kind, sigma, seed = [], [], []
    for s in ids:
        a, b, c = str(s).split("|")
        kind.append(a); sigma.append(float(b)); seed.append(int(c))
    return np.array(kind), np.array(sigma), np.array(seed)


def features(obs_1, window=10):
    """因果滑动均值 → K、R̂，并给出派生量。

    obs_1: (T,3) 单条轨迹的 (P0,P1,Q)
    返回 dict，各数组长度与时间轴一致（前 window-1 个为 nan）
    """
    T = obs_1.shape[0]
    P0, P1, Q = obs_1[:, 0], obs_1[:, 1], obs_1[:, 2]
    # 因果均值
    def cmean(x):
        c = np.cumsum(np.insert(x, 0, 0.0))
        out = np.full(T, np.nan)
        out[window - 1:] = (c[window:] - c[:-window]) / window
        return out
    p0, p1, q = cmean(P0), cmean(P1), cmean(Q)
    valid = (p1 > 10) & (q > 0.5)
    with np.errstate(invalid="ignore", divide="ignore"):
        K = q / np.sqrt(p1)
        Rh = (p0 - p1) / q ** 2
    return dict(p0=p0, p1=p1, q=q, K=K, Rh=Rh, valid=valid)


def calibrate(f):
    """用健康标定段拟合参照与稳健尺度。返回 dict。"""
    cal = slice(CAL_START, CAL_END + 1)
    v = f["valid"][cal]
    p1 = f["p1"][cal][v]
    q = f["q"][cal][v]
    K = f["K"][cal][v]
    Rh = f["Rh"][cal][v]
    # 对数-对数拟合 Q_ref = a*(P1/100)^n
    lg = np.polyfit(np.log(p1 / 100.0), np.log(q), 1)
    n_fit, a_fit = lg[0], float(np.exp(lg[1]))
    q_ref = a_fit * (p1 / 100.0) ** n_fit
    gain = float(np.median(q / q_ref))          # 健康增益校正
    r0 = float(np.median(Rh))
    # 残差（在标定段上算）
    eq = q / (gain * q_ref) - 1.0
    er = Rh - r0
    # 稳健尺度 1.4826*MAD，设下限
    def scale(x, floor):
        m = np.median(x)
        s = 1.4826 * np.median(np.abs(x - m))
        return max(float(s), floor)
    s_q = scale(eq, 1e-4)
    s_r = scale(er, 1e-3)
    return dict(n=n_fit, a=a_fit, gain=gain, r0=r0, s_q=s_q, s_r=s_r,
                q_ref_at=lambda p1v: a_fit * (np.asarray(p1v) / 100.0) ** n_fit)


def residuals(f, cal):
    """监测段残差（未归一化）"""
    q, p1, Rh = f["q"], f["p1"], f["Rh"]
    q_ref = cal["a"] * (p1 / 100.0) ** cal["n"]
    with np.errstate(invalid="ignore", divide="ignore"):
        eq = q / (cal["gain"] * q_ref) - 1.0
        er = Rh - cal["r0"]
    return eq, er


def detector_original(f, cal, th_q=TH_Q, th_r=TH_R, persist=PERSIST):
    """原判据：残差超固定阈值 + 连续 persist 次同标签。"""
    eq, er = residuals(f, cal)
    v = f["valid"]
    T = len(eq)
    label = np.zeros(T, dtype=int)
    a = (eq > th_q) & v
    b = (er > th_r) & v
    label[a & ~b] = 1
    label[b & ~a] = 2
    label[a & b] = 3
    # 连续确认
    out = np.zeros(T, dtype=int)
    cnt = 0; cur = 0
    for i in range(T):
        if label[i] > 0 and label[i] == cur:
            cnt += 1
        elif label[i] > 0:
            cur = label[i]; cnt = 1
        else:
            cur = 0; cnt = 0
        if cnt >= persist:
            out[i] = cur
    return dict(label=label, confirmed=out, eq=eq, er=er)


def detector_cusum(f, cal, k=K_CUSUM, h_q=H_CUSUM, h_r=H_CUSUM, persist=1):
    """CUSUM 判据：稳健归一化残差 → 双路累积。"""
    eq, er = residuals(f, cal)
    v = f["valid"]
    T = len(eq)
    zq = eq / cal["s_q"]
    zr = er / cal["s_r"]
    zq = np.where(v, zq, 0.0)
    zr = np.where(v, zr, 0.0)
    Sq = np.zeros(T); Sr = np.zeros(T)
    for i in range(1, T):
        Sq[i] = max(0.0, Sq[i - 1] + zq[i] - k)
        Sr[i] = max(0.0, Sr[i - 1] + zr[i] - k)
    a = Sq > h_q
    b = Sr > h_r
    label = np.zeros(T, dtype=int)
    label[a & ~b] = 1
    label[b & ~a] = 2
    label[a & b] = 3
    out = np.zeros(T, dtype=int)
    cnt = 0; cur = 0
    for i in range(T):
        if label[i] > 0 and label[i] == cur:
            cnt += 1
        elif label[i] > 0:
            cur = label[i]; cnt = 1
        else:
            cur = 0; cnt = 0
        if cnt >= persist:
            out[i] = cur
    return dict(label=label, confirmed=out, Sq=Sq, Sr=Sr, zq=zq, zr=zr)
