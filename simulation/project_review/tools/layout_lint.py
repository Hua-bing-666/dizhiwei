# -*- coding: utf-8 -*-
"""严格版布局校验：除"文字vs文字"，还查"文字压在曲线/柱/色块/坐标轴上"。

旧校验只比较 Text 之间，漏掉了最常见的丑点——标注压在曲线上、数值标签压在柱顶上、
面板标题压住数据、横轴标题撞页脚。本模块把图形元素也纳入检测。
"""
import numpy as np
import matplotlib.text as mtext
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle, FancyBboxPatch


def _hidden_ticks(fig):
    hidden = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = axis.get_view_interval()
            for t in axis.get_major_ticks():
                loc = t.get_loc()
                if not (min(lo, hi) <= loc <= max(lo, hi)):
                    hidden.add(id(t.label1)); hidden.add(id(t.label2))
    return hidden


def _texts(fig, r):
    hidden = _hidden_ticks(fig)
    out = []
    for t in fig.findobj(mtext.Text):
        s = t.get_text()
        if not s.strip() or not t.get_visible() or id(t) in hidden:
            continue
        try:
            bb = t.get_window_extent(renderer=r)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        out.append((s.replace("\n", "/"), bb, t))
    return out


def _line_segments(line, fig, r):
    """把折线/散点的每一段/每一点转成像素包围盒。"""
    segs = []
    ax = line.axes
    if ax is None:
        return segs
    xd, yd = line.get_xdata(), line.get_ydata()
    if len(xd) == 0:
        return segs
    pts = ax.transData.transform(np.column_stack([xd, yd]))
    if line.get_linestyle() not in ("None", "none", "", " ") and len(pts) > 1:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            segs.append((min(x0, x1), min(y0, y1),
                         abs(x1 - x0) or 1.0, abs(y1 - y0) or 1.0))
    ms = line.get_markersize() or 0
    if ms > 0 and line.get_marker() not in ("None", "none", "", " "):
        for (x, yy) in pts:
            segs.append((x - ms / 2, yy - ms / 2, ms, ms))
    return segs


def _patch_boxes(fig, r, skip_ids):
    out = []
    for ax in fig.axes:
        # 数据坐标下的柱/色块
        for p in ax.patches:
            if id(p) in skip_ids:
                continue
            if p.get_gid() in ("deco", "card"):
                continue
            try:
                bb = p.get_window_extent(renderer=r)
            except Exception:
                continue
            if bb.width > 2 and bb.height > 2:
                out.append((type(p).__name__, bb))
    return out


def check(fig, name, ignore_text_inside=(), check_lines=True):
    """返回问题列表。ignore_text_inside 里的文字允许落在色块内（如热力图数值）。"""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    fw, fh = fig.canvas.get_width_height()
    texts = _texts(fig, r)
    probs = []

    # 1) 越界
    for s, bb, _ in texts:
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > fw + 1 or bb.y1 > fh + 1:
            probs.append("越出画布  「%s」" % s[:24])

    # 2) 文字 vs 文字
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i][1], texts[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 1.5 and oy > 1.5:
                probs.append("文字压文字  「%s」×「%s」 (%0.f×%0.f px)"
                             % (texts[i][0][:16], texts[j][0][:16], ox, oy))

    # 3) 文字 vs 折线/散点（示意图可关闭：标注压线属正常，白底保证可读）
    for ax in (fig.axes if check_lines else []):
        line_segs = []
        for ln in ax.lines:
            if ln.get_gid() == "deco":
                continue
            line_segs += _line_segments(ln, fig, r)
        for s, bb, t in texts:
            if t.axes is not ax:
                continue
            for (x, y, w, h) in line_segs:
                ox = min(bb.x1, x + w) - max(bb.x0, x)
                oy = min(bb.y1, y + h) - max(bb.y0, y)
                if ox > 1.0 and oy > 1.0:
                    probs.append("文字压曲线  「%s」 (%0.f×%0.f px)" % (s[:24], ox, oy))
                    break

    # 4) 文字 vs 柱/色块（排除明确允许的，如热力图数值）
    skip = set(id(p) for ax in fig.axes for p in ax.patches)
    boxes = _patch_boxes(fig, r, set())
    for s, bb, t in texts:
        if any(k in s for k in ignore_text_inside):
            continue
        for kind, pb in boxes:
            ox = min(bb.x1, pb.x1) - max(bb.x0, pb.x0)
            oy = min(bb.y1, pb.y1) - max(bb.y0, pb.y0)
            # 只有当文字被色块覆盖超过 60% 才算压住（避免贴着柱顶标注被误报）
            if ox > 1.5 and oy > 1.5 and (ox * oy) > 0.6 * bb.width * bb.height:
                probs.append("文字被色块盖住  「%s」 (%s)" % (s[:20], kind))
                break

    print("  %-22s 文本 %2d ｜ 问题 %d" % (name, len(texts), len(probs)))
    for p in probs[:10]:
        print("      - " + p)
    return probs
