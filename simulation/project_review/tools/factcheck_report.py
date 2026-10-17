# -*- coding: utf-8 -*-
"""核实现状呈报中的事实性断言。"""
import os, io, re, zipfile, subprocess, sys

WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
DOCS = os.path.join(WS, "docs")
P = os.path.join(WS, "大创申报书_正式稿6.docx")

def rd(p):
    for e in ("utf-8", "utf-8-sig", "gbk"):
        try: return io.open(p, encoding=e).read()
        except Exception: continue
    return ""

print("=" * 88)
print("【N1】docs 份数与 README 口径")
print("=" * 88)
md = sorted(f for f in os.listdir(DOCS) if f.endswith(".md"))
print("  实际 docs/*.md = %d 份" % len(md))
for f in md: print("     %s" % f)
rm = rd(os.path.join(WS, "README.md"))
m = re.search(r"现行\s*(\d+)\s*份", rm)
print("  README 声称: %s" % (m.group(1) if m else "未找到"))
missing = [f for f in md if f not in rm]
print("  README 索引漏列 %d 份:" % len(missing))
for f in missing: print("     %s" % f)

print("\n" + "=" * 88)
print("【N5】git 与仓库状态")
print("=" * 88)
for cmd in [["git", "rev-parse", "--short", "HEAD"],
            ["git", "log", "-1", "--format=%cd (%h %s)", "--date=short"],
            ["git", "status", "--porcelain"]]:
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "").strip()
    if cmd[1] == "status":
        n = len(out.split("\n")) if out else 0
        print("  未提交改动: %d 项" % n)
    else:
        print("  %s" % out)

print("\n" + "=" * 88)
print("【firmware】行数与内容")
print("=" * 88)
fw = os.path.join(WS, "firmware")
if os.path.isdir(fw):
    for f in sorted(os.listdir(fw)):
        p = os.path.join(fw, f)
        if os.path.isfile(p):
            t = rd(p)
            print("  %-30s %5d 行" % (f, t.count("\n") + 1))
    allt = "\n".join(rd(os.path.join(fw, f)) for f in os.listdir(fw) if os.path.isfile(os.path.join(fw, f)))
    for k in ["HAL_", "ADC", "TIM", "USART", "FLASH", "BUILD_HARNESS", "RTC"]:
        print("  含 %-14s: %s" % (k, "是" if k in allt else "否"))
    print("  tests/ 存在: %s" % os.path.isdir(os.path.join(WS, "tests")))
    import glob
    tp = glob.glob(os.path.join(WS, "**", "test_*.py"), recursive=True) + \
         glob.glob(os.path.join(WS, "**", "*_test.py"), recursive=True)
    print("  pytest 测试文件: %d 个" % len(tp))

print("\n" + "=" * 88)
print("【申报书】呈报所引段落的实际情况（只报告，不修改）")
print("=" * 88)
x = zipfile.ZipFile(P).read("word/document.xml").decode("utf-8")
checks = [
    ("p178 固定门限 0.06/0.6", "0.06"),
    ("CUSUM 是否出现", "CUSUM"),
    ("h=61 是否出现", "h=61"),
    ("ADS1115", "ADS1115"),
    ("SGM58031", "SGM58031"),
    ("0—20kPa", "0—20kPa"),
    ("±0.25%FS", "0.25%FS"),
    ("10.04 kPa", "10.04"),
    ("1.055 L/min", "1.055"),
    ("20 秒取样", "20秒"),
    ("22dBm", "22dBm"),
    ("研究问题", "研究问题"),
    ("必做", "必做"),
    ("第几次灌水", "第几次灌水"),
    ("切换 1—5 分钟", "1—5分钟"),
    ("17%—18%", "17%—18%"),
]
for name, k in checks:
    print("  %-26s %s" % (name, "★出现" if k in x else "未出现"))

print("\n" + "=" * 88)
print("【N4】三张图是否存在")
print("=" * 88)
figs = os.path.join(WS, "simulation", "project_review", "figures")
if os.path.isdir(figs):
    for f in sorted(os.listdir(figs)):
        print("  %-32s %8d B" % (f, os.path.getsize(os.path.join(figs, f))))

print("\n" + "=" * 88)
print("【N3】E4 结果实际值")
print("=" * 88)
e = rd(os.path.join(WS, "simulation", "project_review", "results", "E_report.txt"))
if "E4" in e:
    seg = e.split("E4 切换敏感性")[1].split("====")[0]
    print(seg[:1200])
