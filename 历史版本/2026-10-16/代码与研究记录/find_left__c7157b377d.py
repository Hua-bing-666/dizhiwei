# -*- coding: utf-8 -*-
import os, io, re
WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
D = os.path.join(WS, "docs")

print("=== 1) 残留 10.04 的位置 ===")
targets = [os.path.join(WS, "README.md")] + [os.path.join(D, f) for f in os.listdir(D) if f.endswith(".md")]
for p in targets:
    t = io.open(p, encoding="utf-8").read()
    for m in re.finditer("10\\.04", t):
        i = m.start()
        print("  %-42s ...%s..." % (os.path.basename(p), t[max(0,i-60):i+40].replace("\n"," ")))

print("\n=== 2) 残留 10.3 / 15.4 / 20.6 的位置 ===")
for p in targets:
    t = io.open(p, encoding="utf-8").read()
    for m in re.finditer("10\\.3\\s*/\\s*15\\.4\\s*/\\s*20\\.6", t):
        i = m.start()
        print("  %-42s ...%s..." % (os.path.basename(p), t[max(0,i-60):i+50].replace("\n"," ")))

print("\n=== 3) 诊断算法客观评价.md 里的失效链接 ===")
p = os.path.join(D, "诊断算法客观评价.md")
t = io.open(p, encoding="utf-8").read()
for L in re.findall(r"\]\(([^)]+)\)", t):
    print("  %s" % L)
