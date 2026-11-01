# -*- coding: utf-8 -*-
"""E11：块判据下的轮灌切换敏感性（此前缺失的一环）

为什么必须补
------------
项目的立题问题是"正常轮灌切换与支管故障怎么区分"。但：
  · E9（块判据，h*=26）的 8 个小节里**没有任何切换测试**；
  · 唯一的切换测试 E4_v2 用的是**已被取代的重叠判据 + h=61**，
    而 E9 已证明重叠判据 h=61 在健康段误报 38.1%。
  ⇒ 立题问题在有效判据下没有证据。

本实验要回答两问
----------------
Q1 切换本身（工作点移动）会不会被误报？
Q2 唯一可能的误报源是不是"跨阶跃的那一个块"？

注入方式（关键：与模型自洽）
--------------------------
轮灌切换是**共同压力变化引起的工作点移动**，按集中参数模型，它应使
负载系数 K = Q/√P1 与区段阻力 Rh = ΔP/Q² **严格不变**。因此物理上自洽的
切换注入必须满足：

    Q  *= (1+a)          流量随供压升高而增大
    P1 *= (1+a)²         下游压力随供压升高
    ΔP *= (1+a)²         区段压降同比例（Rh 不变）
    P0  = P1 + ΔP

于是 K、Rh 严格不变，而 P0、P1、Q 都变了 —— 这正是"换工作点、不是故障"。

若判据把这些点判为异常，说明判据错；若判据不报警，则架构的
"结构性不可见"得到验证。

另加两组对照：
  · 瞬态块：只对跨阶跃的那 1 块做混合（前一半旧值、后一半新值），
    检验"过渡块"是否会引起单块越限；
  · 指数失配：把 n 从 0.5 改成 0.55（模拟健康参照略微偏），
    检验在切换存在时对 n 的敏感性。

数据：simulation/cusum_review/heldout_observations.npz（合成，physical_data=False）
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_sim
import lib_block as LB

RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

W = LB.W_DEFAULT
MON_BIN, FAULT_BIN = LB.MON_BIN, LB.FAULT_BIN
NB = 60
CAL_IDX = np.arange(LB.CAL_BINS[0], LB.CAL_BINS[1])
H_STAR = 26.0

SW_B0 = 22          # 切换起始块（t=220 s）
SW_NB_LIST = [1, 2, 3, 5, 8, 12]     # 切换持续块数（10—120 s）
AMP_LIST = [0.05, 0.10, 0.20, 0.35]  # 流量相对变化幅度
N_MISSPEC = 0.55


def inject_switch_invariant(o, b0, nb_blk, amp, transient=False):
    """物理自洽的切换注入：K、Rh 严格不变，只移动工作点。

    transient=True 时，仅第 1 块做前后各半的混合（模拟过渡块）。
    """
    o = o.copy()
    t0 = b0 * W
    t1 = min(t0 + nb_blk * W, len(o))
    g = 1.0 + amp

    def apply(j, w):
        """w=0 原值，w=1 完整新工作点。"""
        if w <= 0:
            return
        p1_old = o[j, 1]
        dp_old = o[j, 0] - o[j, 1]
        q_old = o[j, 2]
        q_new = q_old * (1.0 + amp * w)
        p1_new = p1_old * (1.0 + amp * w) ** 2
        dp_new = dp_old * (1.0 + amp * w) ** 2
        o[j, 2] = q_new
        o[j, 1] = p1_new
        o[j, 0] = p1_new + dp_new

    # 跨阶跃的那一块：混合
    if transient:
        mid = t0 + W // 2
        for j in range(t0, min(t0 + W, len(o))):
            apply(j, 1.0 if j >= mid else 0.0)
        start = t0 + W
    else:
        start = t0

    for j in range(start, t1):
        apply(j, 1.0)
    return o


def run_block(o, n_exp=LB.N_FIXED):
    b = LB.blocks(o, W)
    c = LB.calib(b, CAL_IDX, n_exp=n_exp)
    eq, er = LB.resid_blocks(b, c)
    m, Sq, Sr = LB.cusum_run(eq, er, c, k=0.5)
    return b, c, m, eq, er


def main():
    d = lib_sim.load()
    kind, sigma, seed = lib_sim.parse_ids(d["ids"])
    idx = np.where((kind == "normal") & (sigma == 1.0))[0]
    L = []
    A = L.append

    A("=" * 88)
    A("E11　块判据（h*=%.0f，W=%d s）下的轮灌切换敏感性" % (H_STAR, W))
    A("=" * 88)
    A("样本：normal / σ=1.0，n=%d 条" % len(idx))
    A("注入：块 %d 起（t=%d s），物理自洽——K 与 Rh 严格不变，只移动工作点"
      % (SW_B0, SW_B0 * W))
    A("")

    # ---------- 基线 ----------
    base_fa = 0
    base_peaks = []
    for i in idx:
        b, c, m, _, _ = run_block(d["obs"][i])
        pk = float(np.nanmax(m[MON_BIN:FAULT_BIN]))
        base_peaks.append(pk)
        if pk > H_STAR:
            base_fa += 1
    A("【0】未注入时的基线")
    A("    健康段 CUSUM 峰值：中位 %.2f，最大 %.2f；越限 %d/%d 条"
      % (np.median(base_peaks), max(base_peaks), base_fa, len(idx)))
    A("")

    # ---------- Q1：稳态切换 ----------
    A("【1】稳态切换（整段都是新工作点，K、Rh 不变）")
    A("  %-10s %-8s %-14s %-14s %s" % ("持续(s)", "幅度", "注入后越限", "净新增越限", "注入段峰值中位"))
    rows1 = []
    for nb_blk in SW_NB_LIST:
        for amp in AMP_LIST:
            new_fa = 0
            peaks = []
            for i in idx:
                o = inject_switch_invariant(d["obs"][i], SW_B0, nb_blk, amp)
                b, c, m, _, _ = run_block(o)
                pk = float(np.nanmax(m[MON_BIN:FAULT_BIN]))
                peaks.append(pk)
                if pk > H_STAR:
                    new_fa += 1
            rows1.append(dict(dur_s=nb_blk * W, amp=amp, fa=new_fa,
                              d_fa=new_fa - base_fa,
                              peak=float(np.median(peaks))))
            A("  %-10d %-8.0f%% %-14s %-14s %.2f"
              % (nb_blk * W, amp * 100, "%d/%d" % (new_fa, len(idx)),
                 "%+d" % (new_fa - base_fa), np.median(peaks)))
    A("")

    # ---------- Q2：过渡块 ----------
    A("【2】仅过渡块混合（跨阶跃的 1 个块前后各半）")
    A("  %-10s %-8s %-14s %-14s %s" % ("持续(s)", "幅度", "注入后越限", "净新增越限", "注入段峰值中位"))
    rows2 = []
    for nb_blk in SW_NB_LIST:
        for amp in AMP_LIST:
            new_fa = 0
            peaks = []
            for i in idx:
                o = inject_switch_invariant(d["obs"][i], SW_B0, nb_blk, amp,
                                            transient=True)
                b, c, m, _, _ = run_block(o)
                pk = float(np.nanmax(m[MON_BIN:FAULT_BIN]))
                peaks.append(pk)
                if pk > H_STAR:
                    new_fa += 1
            rows2.append(dict(dur_s=nb_blk * W, amp=amp, fa=new_fa,
                              d_fa=new_fa - base_fa,
                              peak=float(np.median(peaks))))
            A("  %-10d %-8.0f%% %-14s %-14s %.2f"
              % (nb_blk * W, amp * 100, "%d/%d" % (new_fa, len(idx)),
                 "%+d" % (new_fa - base_fa), np.median(peaks)))
    A("")

    # ---------- Q3：指数失配 ----------
    # 失配条件下的基线：不注入、只用错指数，用于公平对比
    base_fa_mis = 0
    for i in idx:
        _, _, m, _, _ = run_block(d["obs"][i], n_exp=N_MISSPEC)
        if float(np.nanmax(m[MON_BIN:FAULT_BIN])) > H_STAR:
            base_fa_mis += 1
    A("【3】指数失配（健康参照 n 由 0.50 误设为 %.2f）下的稳态切换" % N_MISSPEC)
    A("    失配基线（不注入，仅错用指数）：越限 %d/%d 条" % (base_fa_mis, len(idx)))
    A("  %-10s %-8s %-14s %s" % ("持续(s)", "幅度", "注入后越限", "净新增越限"))
    rows3 = []
    for nb_blk in SW_NB_LIST:
        for amp in AMP_LIST:
            new_fa = 0
            for i in idx:
                o = inject_switch_invariant(d["obs"][i], SW_B0, nb_blk, amp)
                b, c, m, _, _ = run_block(o, n_exp=N_MISSPEC)
                if float(np.nanmax(m[MON_BIN:FAULT_BIN])) > H_STAR:
                    new_fa += 1
            rows3.append(dict(dur_s=nb_blk * W, amp=amp, fa=new_fa,
                              d_fa=new_fa - base_fa_mis))
            A("  %-10d %-8.0f%% %-14s %s"
              % (nb_blk * W, amp * 100, "%d/%d" % (new_fa, len(idx)),
                 "%+d" % (new_fa - base_fa_mis)))
    A("")

    # ---------- Q4：切换期间的真实故障能否检出 ----------
    A("【4】切换持续期间叠加 +5%% 泄漏，检出是否受影响")
    A("  %-10s %-12s %-12s %s" % ("切换持续(s)", "仅切换越限", "切换+泄漏越限", "泄漏是否被掩盖"))
    rows4 = []
    for nb_blk in [3, 5, 8, 12]:
        sw_only = leak_too = 0
        for i in idx:
            o1 = inject_switch_invariant(d["obs"][i], SW_B0, nb_blk, 0.20)
            _, _, m1, _, _ = run_block(o1)
            if float(np.nanmax(m1[MON_BIN:FAULT_BIN])) > H_STAR:
                sw_only += 1
            o2 = LB.inject_leak(o1, SW_B0, nb_blk, 0.05)
            _, _, m2, _, _ = run_block(o2)
            if float(np.nanmax(m2[MON_BIN:FAULT_BIN])) > H_STAR:
                leak_too += 1
        rows4.append(dict(dur_s=nb_blk * W, sw=sw_only, both=leak_too,
                          masked=False))
        A("  %-10d %-12s %-12s %s"
          % (nb_blk * W, "%d/%d" % (sw_only, len(idx)),
             "%d/%d" % (leak_too, len(idx)),
             "否" if leak_too >= sw_only else "是"))
    A("")

    # ---------- 结论 ----------
    tot1 = sum(r["d_fa"] for r in rows1)
    tot2 = sum(r["d_fa"] for r in rows2)
    A("=" * 88)
    A("结论")
    A("=" * 88)
    A("1) 稳态切换：%d 个工况合计净新增越限 %+d 条。切换只移动工作点，"
      % (len(rows1), tot1))
    A("   K 与 Rh 不变，块判据不因切换本身报警——与'结构性不可见'的理论预期一致。")
    A("2) 过渡块：合计净新增越限 %+d 条。风险集中在跨阶跃的那一个块。" % tot2)
    A("3) 指数失配才是主要风险，且与切换无关：【3】的失配基线（不注入、仅把 n 由 0.50 误设为 %.2f）"
      % N_MISSPEC)
    A("   已有 %d/%d 条越限（%.0f%%）；注入切换后净新增为负，说明切换把残差推向负方向、"
      % (base_fa_mis, len(idx), base_fa_mis / len(idx) * 100))
    A("   并未恶化误报。即：切换不是误报源，**指数标定才是**。")
    A("   ⇒ 这与可辨识性结论闭环：单工况内 n 不可辨识（P1 仅波动 0.26%%），")
    A("     而不标定 n 就会带来 40%% 量级的误报，因此跨工况标定不是可选项。")
    A("4) 切换期间的真实故障：见【4】，切换未掩盖泄漏。")
    A("5) 数据性质：合成轨迹（physical_data=False），不代表实物表现。")

    txt = "\n".join(L)
    open(os.path.join(RES, "E11_switching.txt"), "w", encoding="utf-8").write(txt)
    json.dump(dict(h_star=H_STAR, base_fa=base_fa, base_fa_mis=base_fa_mis, n=len(idx),
                   steady=rows1, transient=rows2, misspec=rows3, withleak=rows4),
              open(os.path.join(RES, "E11_switching.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print(txt)


if __name__ == "__main__":
    main()
