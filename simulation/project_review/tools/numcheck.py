# -*- coding: utf-8 -*-
"""核对技术文档中的关键数字与全局核算是否一致（抓过时/矛盾数字）。"""
import os, re

WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
DOCS = os.path.join(WS, "docs")

def read(p):
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try: return open(p, encoding=enc).read()
        except Exception: continue
    return ""

# 全局核算的"正确值"
TRUTH = {
    "最大健康压降": ["9.44", "10.04"],
    "健康流量@160": ["3.44", "3.54"],
    "最大流量@50%泄漏": ["4.97", "4.34", "5.00"],
    "容器容量": ["678.6"],
    "取样时长": ["20 秒", "20秒", "18 秒", "18秒"],
    "差压不确定度": ["0.050", "0.05"],
    "5%信号/U": ["9.68", "14.52", "19.36", "10.3", "15.4", "20.6"],
}

files = [f for f in os.listdir(DOCS) if f.endswith(".md")]
print("=== 关键数字在各现行文档中的出现情况 ===")
for topic, keys in TRUTH.items():
    print("\n【%s】" % topic)
    for k in keys:
        hits = []
        for f in files:
            n = read(os.path.join(DOCS, f)).count(k)
            if n: hits.append("%s×%d" % (f.replace(".md", ""), n))
        if hits:
            print("   %-10s %s" % (k, "; ".join(hits[:5])))
        else:
            print("   %-10s （未出现）" % k)

# 重点：找出仍然写着 10.04 的地方（与本次 9.44 不一致）
print("\n" + "=" * 80)
print("=== 「10.04」出现位置（本次核算为 9.44，需确认口径）===")
for f in files:
    t = read(os.path.join(DOCS, f))
    for m in re.finditer("10\\.04", t):
        i = m.start()
        print("  %-40s ...%s..." % (f.replace(".md", ""), t[max(0, i-50):i+30].replace("\n", " ")))

print("\n=== 「20 秒」取样出现位置 ===")
for f in files:
    t = read(os.path.join(DOCS, f))
    for m in re.finditer("20\\s*秒", t):
        i = m.start()
        print("  %-40s ...%s..." % (f.replace(".md", ""), t[max(0, i-50):i+40].replace("\n", " ")))
