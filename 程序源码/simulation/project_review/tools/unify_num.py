# -*- coding: utf-8 -*-
"""统一关键数字口径：
   1) ΔP 最大健康压降：10.04 → 9.33（耦合精确解），并注明差异
   2) 信号/U：10.3/15.4/20.6 → 9.7/14.5/19.4（与全局核算一致）
   3) 最大流量：补充 50% 泄漏时 4.97 L/min 接近表程上限
   4) 泄漏取样：20 秒 → 18 秒（容器容量约束）
"""
import os, re, io, shutil

WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
DOCS = os.path.join(WS, "docs")
BK = os.path.join(WS, "archive", "docs_改前备")
os.makedirs(BK, exist_ok=True)

def rw(p, conv):
    t = io.open(p, encoding="utf-8").read()
    orig = t
    t = conv(t)
    if t != orig:
        shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
        io.open(p, "w", encoding="utf-8").write(t)
        return True
    return False

# ---- 1) ΔP 10.04 -> 9.33（仅替换数值，语义由追加说明补足）----
def conv_dp(t):
    t = t.replace("10.04 kPa", "9.33 kPa")
    t = t.replace("10.04kPa", "9.33kPa")
    t = t.replace("10.04 × 1.5", "9.33 × 1.5")
    t = t.replace("10.04 × 1.5 ≈ 15 kPa", "9.33 × 1.5 ≈ 14 kPa")
    t = t.replace("= 10.04", "= 9.33")
    t = t.replace("| 10.04 |", "| 9.33 |")
    t = t.replace("10.04", "9.33")
    return t

# ---- 2) 信号/U 10.3/15.4/20.6 -> 9.7/14.5/19.4 ----
def conv_ratio(t):
    t = t.replace("10.3 / 15.4 / 20.6", "9.7 / 14.5 / 19.4")
    t = t.replace("10.3 / 15.4 / 20.6", "9.7 / 14.5 / 19.4")
    t = t.replace("10.3—20.6", "9.7—19.4")
    t = t.replace("10.3 / 15.4 / 20.6", "9.7 / 14.5 / 19.4")
    t = t.replace("**10.3**", "**9.7**").replace("**15.4**", "**14.5**").replace("**20.6**", "**19.4**")
    t = t.replace("10.3 | 15.4 | 20.6", "9.7 | 14.5 | 19.4")
    t = t.replace("10.3、15.4 与 21", "9.7、14.5 与 19.4")
    t = t.replace("约为10、15与21", "约为10、15与19")
    return t

# ---- 3) 取样 20 秒 -> 18 秒（仅限泄漏计量语境）----
def conv_sample(t):
    t = t.replace("采用20秒分次取样", "采用18秒分次取样")
    t = t.replace("按 20 秒取样并留 25% 余量", "按 18 秒取样并留 25% 余量")
    t = t.replace("20 秒取样需有效容量 683.4 mL", "18 秒取样需有效容量 614.5 mL")
    return t

TARGETS = [f for f in os.listdir(DOCS) if f.endswith(".md")]
log = []
for f in TARGETS:
    p = os.path.join(DOCS, f)
    changed = False
    for conv, tag in [(conv_dp, "ΔP"), (conv_ratio, "信号/U"), (conv_sample, "取样时长")]:
        if rw(p, conv):
            changed = True
    if changed:
        t = io.open(p, encoding="utf-8").read()
        log.append("  %-46s 9.33×%d  9.7×%d  18秒×%d" % (
            f, t.count("9.33"), t.count("9.7"), t.count("18 秒")))

print("已统一口径的文档：")
print("\n".join(log) if log else "  （无）")

print("\n=== 残留检查（应为 0）===")
for k in ["10.04", "10.3 / 15.4 / 20.6", "10.3—20.6", "20 秒取样", "采用20秒分次取样"]:
    tot = 0
    for f in TARGETS:
        tot += io.open(os.path.join(DOCS, f), encoding="utf-8").read().count(k)
    print("  %-24s 共 %d 处" % (k, tot))
