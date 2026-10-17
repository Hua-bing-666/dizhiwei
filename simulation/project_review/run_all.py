# -*- coding: utf-8 -*-
"""滴智卫仿真统一入口：一条命令复现全部复核实验。

用法（仓库根目录）：
    python simulation/project_review/run_all.py

执行顺序（有依赖，不可调换）：
    ident        → 可辨识性：单工况 vs 跨工况拟合指数 n
    E9           → ★块判据：样本独立性修正 + ARL0 重定门限 + 可检边界重扫
    E10          → ★真实性缺口补齐：独立传感器噪声/时间相关性、C_eff 漂移、
                   增益漂移、强基线对照
    E3_corrected → 重叠版门限反推（保留作对照，其 h=61 已被 E9 取代）
    E6_E7_v2     → 可检边界与 U 需求（旧口径，仅供对照）
    E4_v2        → 轮灌切换敏感性 + 暂态抑制代价
    F1_F2        → 干管参照差分收益
    make_figures → 三张图

历史说明一：早期入口 run_experiments.py 使用错误门限 h=5，
其 E6 输出全 0/8、E7 误报 8/8，结论已被取代；该脚本已移入 legacy/，
不得作为结论来源。

历史说明二：E3_corrected / E6_E7_v2 建立在**重叠窗口**判据上（每 1 s 一个
判据样本），门限因此被高估约 57 倍；另有 inject_leak 注入的是"供压扰动"
而非泄漏（该口径下 K=Q/√P1 严格不变）。两者的定量结论均已作废，
现以 E9 为唯一有效来源，保留它们仅作方法学对照。

全部数据为合成轨迹（physical_data=False），非田间实测。
"""
import os, sys, subprocess, time, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable

STEPS = [
    ("可辨识性分析",        "ident.py"),
    ("★块判据与门限重定",  "E9_block_threshold.py"),
    ("★真实性缺口补齐",    "E10_robustness.py"),
    ("重叠版门限(对照)",    "E3_corrected.py"),
    ("可检边界旧口径(对照)", "E6_E7_v2.py"),
    ("轮灌切换敏感性",      "E4_v2.py"),
    ("干管参照差分收益",    "F1_F2.py"),
    ("图件生成",            "make_figures.py"),
]


def main():
    t0 = time.time()
    log = []
    print("滴智卫仿真复现 —— 统一入口")
    print("Python: %s" % PY)
    print("=" * 78)
    ok = True
    for name, script in STEPS:
        path = HERE / script
        if not path.exists():
            print("[缺失] %-22s %s" % (name, script))
            ok = False
            continue
        ts = time.time()
        r = subprocess.run([PY, str(path)], cwd=str(ROOT),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        dt = time.time() - ts
        status = "OK" if r.returncode == 0 else "FAIL(%d)" % r.returncode
        print("[%-9s] %-22s %6.1fs" % (status, name, dt))
        if r.returncode != 0:
            ok = False
            print(r.stdout[-2000:])
            print(r.stderr[-2000:])
        log.append(dict(step=name, script=script, returncode=r.returncode,
                        seconds=round(dt, 2)))
    print("=" * 78)
    print("总耗时 %.1f s；状态：%s" % (time.time() - t0, "全部通过" if ok else "存在失败"))
    print("结果目录：%s" % (HERE / "results"))
    print("图件目录：%s" % (HERE / "figures"))
    (HERE / "results" / "run_all_log.json").write_text(
        __import__("json").dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
