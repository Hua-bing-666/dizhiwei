# -*- coding: utf-8 -*-
"""全量审计：仿真可复跑性、文档一致性、结构完整性、关键数字口径。"""
import os, io, re, subprocess, sys

WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
SIM = os.path.join(WS, "simulation", "project_review")
DOCS = os.path.join(WS, "docs")

def rd(p):
    for e in ("utf-8", "utf-8-sig", "gbk"):
        try: return io.open(p, encoding=e).read()
        except Exception: continue
    return ""

print("=" * 90)
print("【A】仿真资产完整性")
print("=" * 90)
scripts = sorted(f for f in os.listdir(SIM) if f.endswith(".py"))
tools = sorted(os.listdir(os.path.join(SIM, "tools")))
res = sorted(os.listdir(os.path.join(SIM, "results")))
figs = sorted(os.listdir(os.path.join(SIM, "figures")))
print("  主脚本 %d 个: %s" % (len(scripts), ", ".join(scripts)))
print("  复核工具 %d 个: %s" % (len(tools), ", ".join(tools)))
print("  结果文件 %d 个" % len(res))
print("  图 %d 个: %s" % (len(figs), ", ".join(figs)))

print("\n" + "=" * 90)
print("【B】仿真脚本可复跑性测试")
print("=" * 90)
for s in scripts:
    if s in ("lib_sim.py",):
        continue
    p = os.path.join(SIM, s)
    try:
        r = subprocess.run([sys.executable, s], cwd=SIM, capture_output=True,
                           text=True, timeout=600, encoding="utf-8", errors="replace")
        status = "OK" if r.returncode == 0 else "FAIL(%d)" % r.returncode
        tail = (r.stdout or "").strip().split("\n")[-1][:60] if r.stdout else ""
        print("  %-26s %-10s %s" % (s, status, tail))
        if r.returncode != 0:
            print("      stderr: %s" % (r.stderr or "")[-200:])
    except subprocess.TimeoutExpired:
        print("  %-26s TIMEOUT" % s)
    except Exception as e:
        print("  %-26s ERR %s" % (s, str(e)[:60]))

print("\n" + "=" * 90)
print("【C】文档清单与交叉引用")
print("=" * 90)
md = sorted(f for f in os.listdir(DOCS) if f.endswith(".md"))
js = sorted(f for f in os.listdir(DOCS) if f.endswith(".json"))
print("  md %d 个，json %d 个" % (len(md), len(js)))
bad = 0
for f in md:
    t = rd(os.path.join(DOCS, f))
    for L in re.findall(r"\]\(([^)]+)\)", t):
        if L.startswith(("http", "#")): continue
        p = os.path.join(DOCS, L.replace("/", os.sep))
        if not os.path.exists(p):
            bad += 1
            print("  ✗ %s -> %s" % (f, L))
print("  失效链接 %d 个" % bad)

print("\n" + "=" * 90)
print("【D】关键数字口径（现行 docs + README）")
print("=" * 90)
allt = rd(os.path.join(WS, "README.md")) + "\n".join(rd(os.path.join(DOCS, f)) for f in md)
for k, want in [("10.04", 0), ("9.33", 1), ("10.3 / 15.4 / 20.6", 0),
                ("20 秒取样", 0), ("18 秒", 1), ("h=61", 1), ("0—20kPa", 1),
                ("BOCD", 0), ("阀态", 0)]:
    n = allt.count(k)
    good = (n == 0) if want == 0 else (n > 0)
    print("  %-22s 出现 %3d 次  %s" % (k, n, "✓" if good else "✗"))

print("\n" + "=" * 90)
print("【E】项目结构")
print("=" * 90)
for n in sorted(os.listdir(WS)):
    p = os.path.join(WS, n)
    if os.path.isdir(p):
        c = sum(len(fs) for _, _, fs in os.walk(p))
        print("  DIR  %-22s %5d 文件" % (n, c))
    else:
        print("  FILE %-22s %10d B" % (n, os.path.getsize(p)))

print("\n" + "=" * 90)
print("【F】申报书数字与外部文档的差异（仅报告，不修改）")
print("=" * 90)
P = os.path.join(WS, "大创申报书_正式稿6.docx")
try:
    import zipfile
    x = zipfile.ZipFile(P).read("word/document.xml").decode("utf-8")
    for k in ["10.04", "9.33", "9.7", "0.05kPa", "1kPa", "600kPa"]:
        print("  申报书含「%s」: %s" % (k, "是" if k in x else "否"))
except Exception as e:
    print("  读取失败:", e)
