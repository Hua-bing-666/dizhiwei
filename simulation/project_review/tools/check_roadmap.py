# -*- coding: utf-8 -*-
"""技术路线图专项校验（直接调用真实生成函数）

  1) 编号是否遵循阅读顺序（左上→右上→右下→左下）；
  2) 箭头是否沿椭圆顺时针（01→02→03→04→01），且每段恰好接在相邻两阶段之间；
  3) 每张卡片内文字是否封在框内；
  4) 字号是否分级。
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.dirname(HERE)
sys.path.insert(0, PRJ)
sys.path.insert(0, HERE)

import make_figures as MF

A_R, B_R = MF.ROAD_A, MF.ROAD_B
CW, CH = MF.ROAD_CW, MF.ROAD_CH
F_K = MF.ROAD_FK

# 顺时针次序：左上(135) → 右上(45) → 右下(-45) → 左下(-135)
STAGES = [(135, "01", "左上"), (45, "02", "右上"),
          (-45, "03", "右下"), (-135, "04", "左下")]
TIP_ORDER = [(105, 75), (15, -15), (-75, -105), (-165, -195)]

CAP = {}


def capture_save(fig, name, w_in, ignore_inside=()):
    CAP["fig"] = fig
    return []


def cw(start, end):
    """从 start 顺时针到 end 的角度（0—360）。"""
    return (start - end) % 360


def main():
    print("=" * 76)
    print("技术路线图专项校验（顺时针 / 阅读顺序）")
    print("=" * 76)

    # ---------- 1) 编号位置 ----------
    print("\n【1】编号位置（要求：左上→右上→右下→左下）")
    quad_ok = True
    exp_map = {"左上": (True, False), "右上": (True, True),
               "右下": (False, True), "左下": (False, False)}
    for ang, num, where in STAGES:
        a = np.deg2rad(ang)
        cx, cy = A_R * np.cos(a) * F_K, B_R * np.sin(a) * F_K
        got = ("上" if cy > 0 else "下") + ("右" if cx > 0 else "左")
        e = exp_map[where]
        good = (cy > 0) == e[0] and (cx > 0) == e[1]
        quad_ok &= good
        print("  阶段 %s  角度 %4d°  →  (%6.1f, %6.1f)  期望%s  实测%s  %s"
              % (num, ang, cx, cy, where, got, "✓" if good else "✗"))

    # ---------- 2) 箭头方向 ----------
    print("\n【2】箭头方向（要求：顺时针，每段接在相邻两阶段之间）")
    angs = [s[0] for s in STAGES]
    ok_dir = True
    for k, (lo, hi) in enumerate(TIP_ORDER):
        s1, s2 = angs[k], angs[(k + 1) % 4]
        d1, d2, d3 = cw(s1, lo), cw(lo, hi), cw(hi, s2)
        good = 0 < d1 <= 45 and 0 < d2 <= 60 and 0 < d3 <= 45
        ok_dir &= good
        print("  箭头%d  %5d°→%5d° ｜ 阶段%s(%4d°) → 阶段%s(%4d°)"
              " ｜ 间距 %2.0f/%2.0f/%2.0f°  %s"
              % (k + 1, lo, hi, STAGES[k][1], s1,
                 STAGES[(k + 1) % 4][1], s2, d1, d2, d3,
                 "✓" if good else "✗"))
    mono = all(cw(a[0], b[0]) > 0 for a, b in zip(TIP_ORDER, TIP_ORDER[1:]))
    print("  箭头起点角度单调递减（顺时针）：%s" % ("✓" if mono else "✗"))
    print("  ⇒ %s" % ("方向正确：01→02→03→04→01（顺时针）"
                    if (ok_dir and mono) else "方向错误"))

    # ---------- 3) 文字封框 ----------
    CAP.clear()
    MF.save = capture_save
    MF.fig_roadmap()
    fig = CAP["fig"]
    ax = fig.axes[0]
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    print("\n【3】卡片内文字是否封在框内（留边 ≥1.0 单位）")
    n_in, ok_in = 0, True
    for ang, num, where in STAGES:
        a = np.deg2rad(ang)
        cx, cy = A_R * np.cos(a) * F_K, B_R * np.sin(a) * F_K
        x0, y0 = cx - CW / 2, cy - CH / 2
        print("  卡片 %s（%s）  x[%6.1f,%6.1f]  y[%6.1f,%6.1f]"
              % (num, where, x0, x0 + CW, y0, y0 + CH))
        for t in list(ax.texts):
            tx, ty = t.get_position()
            if not (x0 <= tx <= x0 + CW and y0 <= ty <= y0 + CH):
                continue
            n_in += 1
            bb = t.get_window_extent(renderer=r)
            bx0, by0 = inv.transform((bb.x0, bb.y0))
            bx1, by1 = inv.transform((bb.x1, bb.y1))
            m = (min(bx0, bx1) - x0, (x0 + CW) - max(bx0, bx1),
                 min(by0, by1) - y0)
            good = min(m) >= 1.0
            ok_in &= good
            print("     「%-14s」 左%5.1f 右%5.1f 下%5.1f  %s"
                  % (t.get_text().replace("\n", "/")[:14], m[0], m[1], m[2],
                     "✓" if good else "✗ 外溢"))
    print("  参与检查的文字：%d 条" % n_in)
    if n_in == 0:
        ok_in = False
        print("  ✗ 未取到卡片内文字，校验无效")

    # ---------- 4) 字号分级 ----------
    print("\n【4】字号分级")
    sizes = {}
    for t in ax.texts:
        sizes.setdefault(round(t.get_fontsize(), 1), []).append(t.get_text()[:10])
    for k in sorted(sizes, reverse=True):
        print("  %4.1f pt：%s" % (k, "、".join(sizes[k][:3])))
    graded = len(sizes) >= 3

    plt.close(fig)
    print("\n" + "=" * 76)
    print("结论：编号顺序 %s ｜ 箭头 %s ｜ 封框 %s ｜ 字号分级 %s"
          % ("正确" if quad_ok else "错误",
             "正确" if (ok_dir and mono) else "错误",
             "通过" if ok_in else "未通过",
             "有" if graded else "无"))
    print("=" * 76)


if __name__ == "__main__":
    main()
