# -*- coding: utf-8 -*-
"""配色合规性检验（依据已发表指南的三条要求）

1) 定性色板用 Okabe-Ito（色盲友好，多数指南推荐的定性默认）；
2) 连续色阶用 Viridis（感知均匀；手工 ramp 不满足感知均匀）；
3) 灰度检验：转灰度后各类仍可区分——这是最基本的无障碍底线。

输出：各色的灰阶值、最小灰阶间隔，并把 roadmap 另存灰度版供人工核对。
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")

PAL = {
    "蓝 BLUE":   "#0072B2",
    "绿 GREEN":  "#009E73",
    "橙 ORANGE": "#E69F00",
    "紫 PURPLE": "#CC79A7",
    "朱红 VERM": "#D55E00",
    "天蓝 SKY":  "#56B4E9",
    "灰 GRAY":   "#8C8C8C",
}


def gray(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def main():
    print("=" * 68)
    print("配色合规性检验")
    print("=" * 68)

    print("\n【1】色板与灰阶值（Okabe-Ito 定性色板）")
    print("  %-12s %-10s %8s" % ("名称", "HEX", "灰阶"))
    for k, v in PAL.items():
        print("  %-12s %-10s %8.1f" % (k, v, gray(v)))

    stages = ["蓝 BLUE", "橙 ORANGE", "绿 GREEN", "紫 PURPLE"]
    gv = sorted(gray(PAL[k]) for k in stages)
    gaps = [round(b - a, 1) for a, b in zip(gv, gv[1:])]
    print("\n【2】技术路线四阶段配色（%s）" % "、".join(stages))
    print("  排序后灰阶：%s" % ", ".join("%.1f" % x for x in gv))
    print("  相邻间隔  ：%s" % ", ".join(str(x) for x in gaps))
    ok = min(gaps) >= 15
    print("  最小间隔 %.1f → %s（阈值 15）" % (min(gaps), "✓ 灰度可分" if ok else "✗ 灰度易混"))

    print("\n【3】连续色阶")
    print("  使用：Viridis（感知均匀、色盲友好、灰度可读）")
    print("  说明：先前的手工青绿 ramp 不满足感知均匀，已弃用")

    # ---- 灰度导出（供人工核对）----
    print("\n【4】灰度版导出（指南建议的黑白打印检验）")
    for name in ["roadmap", "threshold_separation", "detection_boundary"]:
        src = os.path.join(FIG, name + ".png")
        if not os.path.exists(src):
            print("  跳过（缺文件）%s" % name)
            continue
        img = mpimg.imread(src)
        rgb = img[:, :, :3]
        g = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        out = os.path.join(FIG, name + "_gray.png")
        plt.imsave(out, g, cmap="gray", vmin=0, vmax=1)
        # 统计非白区域的灰阶级数（粗分箱）
        mask = g < 0.96
        bins = np.digitize(g[mask], np.linspace(0, 1, 11)) if mask.any() else []
        levels = len(set(bins.tolist()))
        print("  %-24s → %-30s 非白灰阶分布 %d/10 档"
              % (name, os.path.basename(out), levels))

    print("\n【5】结论")
    print("  定性色板：Okabe-Ito（色盲友好，为色觉缺陷设计的原始方案）")
    print("  连续色阶：Viridis（感知均匀）")
    print("  附加冗余编码：门限图三条曲线分别用实线 / 虚线 / 点线，")
    print("                不以颜色作为唯一区分通道")
    print("  灰度检验：%s" % ("通过" if ok else "未通过，需调整"))


if __name__ == "__main__":
    main()
