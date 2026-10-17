# -*- coding: utf-8 -*-
import os, io, shutil
WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
p = os.path.join(WS, "docs", "诊断算法客观评价.md")
shutil.copy2(p, os.path.join(WS, "archive", "docs_改前备", "诊断算法客观评价.md"))
t = io.open(p, encoding="utf-8").read()
orig = t

# 1) simulation/DIAGNOSIS.md 从 docs/ 出发应为 ../simulation/DIAGNOSIS.md
t = t.replace("](simulation/DIAGNOSIS.md)", "](../simulation/DIAGNOSIS.md)")
# 2) 重复路径 docs/archive/... -> ../archive/...
t = t.replace("](docs/archive/docs_历史/", "](../archive/docs_历史/")
t = t.replace("(docs/archive/docs_历史/", "(../archive/docs_历史/")

assert t != orig, "未发生替换"
io.open(p, "w", encoding="utf-8").write(t)
print("已修正。当前链接：")
import re
for L in re.findall(r"\]\(([^)]+)\)", t):
    if L.startswith(("http", "#")): continue
    ok = os.path.exists(os.path.join(WS, "docs", L.replace("/", os.sep)))
    print("   %-56s %s" % (L, "✓" if ok else "✗"))
