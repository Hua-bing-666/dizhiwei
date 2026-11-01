# -*- coding: utf-8 -*-
"""P6 申报书内嵌图整改：图3-5（SN74LVC1G17 引脚图，改灰阶）与 图3-7（microSD 模块原理图，修正 Mirco→Micro）。

设计约束：
  - 与原 docx 内嵌图保持同一宽高比，重嵌时不改 wp:extent（版面零位移）。
    图3-5 原 388x499 → ratio 0.7776；图3-7 原 543x372 → ratio 1.4597。
  - 2× 超采样后 LANCZOS 降采样，获得抗锯齿线条。
  - 灰度体系（黑白打印可辨），文字对比度 ≥4.5:1。
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "application", "figures")
os.makedirs(OUT, exist_ok=True)

MSYH = "C:/Windows/Fonts/msyh.ttc"
MSYHBD = "C:/Windows/Fonts/msyhbd.ttc"
INK = (26, 26, 26)
GRAY = (110, 110, 110)
MID = (150, 150, 150)
FILL = (238, 238, 238)
FILL2 = (224, 224, 224)
EDGE = (60, 60, 60)
WHITE = (255, 255, 255)
SS = 2  # 超采样倍数


def font(sz, bold=False):
    return ImageFont.truetype(MSYHBD if bold else MSYH, sz * SS)


def canvas(w, h):
    im = Image.new("RGB", (w * SS, h * SS), WHITE)
    return im, ImageDraw.Draw(im), w, h


def down(im, w, h, name):
    im = im.resize((w, h), Image.LANCZOS)
    path = os.path.join(OUT, name)
    im.save(path, dpi=(300, 300))
    print("  ✓", name, im.size)
    return path


# ───────────────────────── 图3-5 SN74LVC1G17 引脚图（灰阶） ─────────────────────────
def fig_pinout():
    W, H = 776, 998
    im, d, _, _ = canvas(W, H)
    P = lambda *a: [v * SS for v in a]  # 坐标放大
    # 封装体
    bx0, by0, bx1, by1 = 300, 70, 742, 930
    d.rounded_rectangle(P(bx0, by0, bx1, by1), radius=18 * SS, fill=FILL,
                        outline=EDGE, width=5 * SS)
    # 1 脚取向标记
    d.ellipse(P(332, 108, 360, 136), fill=EDGE)
    # 5 个引脚
    pins = [(1, "N.C"), (2, "A"), (3, "GND"), (4, "Y"), (5, "VCC")]
    ys = [170, 330, 490, 650, 810]
    for (num, lab), y in zip(pins, ys):
        d.line(P(214, y, 300, y), fill=EDGE, width=6 * SS)
        d.ellipse(P(194, y - 16, 226, y + 16), fill=MID, outline=EDGE, width=3 * SS)
        d.text((262 * SS, (y - 5) * SS), str(num), font=font(46), fill=INK, anchor="ms")
        d.text((330 * SS, y * SS), lab, font=font(64, bold=True), fill=INK, anchor="lm")
    # 标题（小，图注另在正文）
    d.text((W / 2 * SS, 40 * SS), "SN74LVC1G17（SOT-23-5 顶视）",
           font=font(38), fill=GRAY, anchor="ms")
    return down(im, W, H, "图3-5_SN74LVC1G17引脚图_灰阶.png")


# ───────────────────────── 图3-7 microSD 模块原理图（Micro） ─────────────────────────
def fig_microsd():
    W, H = 1086, 744
    im, d, _, _ = canvas(W, H)
    P = lambda *a: [v * SS for v in a]
    # PCB 外形
    d.rounded_rectangle(P(30, 30, 1056, 714), radius=26 * SS, fill=FILL,
                        outline=EDGE, width=5 * SS)
    # 左侧 U 形凹槽示意
    d.rectangle(P(30, 320, 58, 424), fill=WHITE, outline=EDGE, width=4 * SS)
    d.text((66 * SS, 372 * SS), "凹槽", font=font(34), fill=GRAY, anchor="lm")
    # microSD 卡座（大件）
    d.rounded_rectangle(P(96, 150, 402, 628), radius=10 * SS, fill=WHITE,
                        outline=EDGE, width=4 * SS)
    d.text((249 * SS, 212 * SS), "Micro SD 卡座", font=font(44, bold=True), fill=INK, anchor="ms")
    # 电平转换电路
    d.rounded_rectangle(P(462, 118, 660, 318), radius=8 * SS, fill=FILL2,
                        outline=EDGE, width=4 * SS)
    d.text((561 * SS, 92 * SS), "电平转换电路", font=font(42, bold=True), fill=INK, anchor="ms")
    # 3.3V 稳压电路
    d.rounded_rectangle(P(462, 430, 660, 600), radius=8 * SS, fill=FILL2,
                        outline=EDGE, width=4 * SS)
    d.text((561 * SS, 632 * SS), "3.3V 稳压电路", font=font(40, bold=True), fill=INK, anchor="ms")
    # 控制接口（排针）
    d.rounded_rectangle(P(842, 170, 952, 600), radius=6 * SS, fill=WHITE,
                        outline=EDGE, width=4 * SS)
    for i in range(7):
        cy = 210 + i * 56
        d.ellipse(P(866, cy - 12, 890, cy + 12), outline=EDGE, width=3 * SS, fill=MID)
        d.ellipse(P(906, cy - 12, 930, cy + 12), outline=EDGE, width=3 * SS, fill=MID)
    d.text((858 * SS, 150 * SS), "控制接口", font=font(36, bold=True), fill=INK, anchor="ms")
    # M2 定位孔（四角）
    for (cx, cy) in [(120, 110), (966, 110), (120, 640), (966, 640)]:
        d.ellipse(P(cx - 20, cy - 20, cx + 20, cy + 20), outline=EDGE, width=4 * SS, fill=WHITE)
        d.ellipse(P(cx - 8, cy - 8, cx + 8, cy + 8), fill=MID)
    d.text((150 * SS, 110 * SS), "M2 定位孔", font=font(34), fill=GRAY, anchor="lm")
    # 连接走线（示意）
    d.line(P(402, 240, 462, 240), fill=MID, width=4 * SS)
    d.line(P(402, 500, 462, 500), fill=MID, width=4 * SS)
    d.line(P(660, 500, 842, 500), fill=MID, width=4 * SS)
    return down(im, W, H, "图3-7_microSD模块原理图.png")


if __name__ == "__main__":
    print("生成 P6 内嵌图：")
    fig_pinout()
    fig_microsd()
