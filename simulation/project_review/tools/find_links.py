# -*- coding: utf-8 -*-
import os, io, re
WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
p = os.path.join(WS, "docs", "诊断算法客观评价.md")
t = io.open(p, encoding="utf-8").read()
for key in ["simulation/DIAGNOSIS.md", "docs/archive/docs_历史/算法与软件最终方案.md",
            "算法与软件最终方案"]:
    print("=== %s ===" % key)
    for m in re.finditer(re.escape(key), t):
        i = m.start()
        print("   ...%s..." % t[max(0, i-90):i+70].replace("\n", " "))
    print()
# 检查目标是否存在
print("目标是否存在：")
for cand in ["simulation/DIAGNOSIS.md", "simulation/diagnosis_review/README.md",
             "archive/docs_历史/算法与软件最终方案.md"]:
    print("   %-52s %s" % (cand, os.path.exists(os.path.join(WS, cand.replace('/', os.sep)))))
