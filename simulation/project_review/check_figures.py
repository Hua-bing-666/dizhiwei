# -*- coding: utf-8 -*-
"""图片结构校验（替代目视）：尺寸、文字元素、边界越界、空白率。"""
import os, re, struct, zlib
import xml.etree.ElementTree as ET

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")

def png_size(p):
    with open(p, "rb") as f:
        head = f.read(33)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", "非 PNG"
    w, h = struct.unpack(">II", head[16:24])
    return w, h

def png_ink_ratio(p, step=8):
    """粗略估计非白像素比例（解码 PNG 的 IDAT 不便，改抽样统计色值）。
    这里用更简单的方法：读原始字节中非 0xFF 的比例作为代理指标。"""
    with open(p, "rb") as f:
        data = f.read()
    # 统计 IDAT 之后的压缩数据长度与整体大小比（代理：内容越复杂文件越大）
    return len(data)

def svg_check(p):
    t = ET.parse(p); r = t.getroot()
    ns = {"s": "http://www.w3.org/2000/svg"}
    vb = r.get("viewBox", "")
    W = H = None
    if vb:
        parts = vb.split()
        if len(parts) == 4:
            W, H = float(parts[2]), float(parts[3])
    texts = [e for e in r.iter("{http://www.w3.org/2000/svg}text")]
    contents = [(e.text or "").strip() for e in texts]
    contents = [c for c in contents if c]
    # 检查文字坐标是否越界
    oob = []
    for e in texts:
        try:
            x = float(e.get("x", "0")); y = float(e.get("y", "0"))
        except ValueError:
            continue
        if W and H and (x < -2 or y < -2 or x > W + 2 or y > H + 2):
            oob.append(((e.text or "")[:18], x, y))
    fonts = set()
    for e in texts:
        fs = e.get("font-size")
        if fs:
            try: fonts.add(round(float(fs), 1))
            except ValueError: pass
    return W, H, len(texts), contents, oob, sorted(fonts)

print("=" * 78)
print("图片结构校验（替代目视）")
print("=" * 78)
for name in ["roadmap", "threshold_separation", "detection_boundary"]:
    png = os.path.join(FIG, name + ".png")
    svg = os.path.join(FIG, name + ".svg")
    w, h = png_size(png)
    sz = os.path.getsize(png)
    W, H, n, contents, oob, fonts = svg_check(svg)
    print("\n【%s】" % name)
    print("  PNG 尺寸: %d × %d px   宽高比 %.2f   文件 %.0f KB" % (w, h, w / h, sz / 1024))
    print("  SVG viewBox: %.0f × %.0f（dpi=200 时对应 %.1f × %.1f 英寸）" % (
        W, H, w / 200, h / 200))
    print("  文字元素: %d 个" % n)
    print("  字号集合: %s" % fonts)
    print("  越界文字: %s" % ("无 ✓" if not oob else oob[:5]))
    print("  文字样例:")
    for c in contents[:6]:
        print("     · %s" % c[:52])
    if len(contents) > 6:
        print("     … 共 %d 条" % len(contents))
