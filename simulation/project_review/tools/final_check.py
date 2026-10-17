# -*- coding: utf-8 -*-
"""最终全量校验：链接 / 口径 / 结构 / 备份 / 引用。"""
import os, re, io, zipfile

WS = r"C:\Users\Lenovo\Desktop\大创想法 - 副本"
ok = bad = 0
def line(s):
    print(s)

line("=" * 84)
line("最终全量校验")
line("=" * 84)

# ---------- 1) README 链接 ----------
t = io.open(os.path.join(WS, "README.md"), encoding="utf-8").read()
links = [L for L in re.findall(r"\]\(([^)]+)\)", t)
         if not L.startswith(("http", "#"))]
badl = [L for L in links if not os.path.exists(os.path.join(WS, L.replace("/", os.sep)))]
line("\n【1】README 链接：%d 个，失效 %d 个" % (len(links), len(badl)))
for b in badl: line("   ✗ %s" % b)
ok += len(links) - len(badl); bad += len(badl)

# ---------- 2) 现行 docs 链接（相对路径）----------
D = os.path.join(WS, "docs")
dfiles = [f for f in os.listdir(D) if f.endswith(".md")]
tot = bad2 = 0
for f in dfiles:
    s = io.open(os.path.join(D, f), encoding="utf-8").read()
    for L in re.findall(r"\]\(([^)]+)\)", s):
        if L.startswith(("http", "#")): continue
        tot += 1
        p = os.path.join(D, L.replace("/", os.sep))
        if not os.path.exists(p):
            bad2 += 1
            line("   ✗ %s -> %s" % (f, L))
line("\n【2】docs 内相对链接：%d 个，失效 %d 个" % (tot, bad2))
ok += tot - bad2; bad += bad2

# ---------- 3) 口径 ----------
line("\n【3】口径统一（现行 docs + README，排除验收记录中故意保留的旧值对照）")
# 验收记录类文档以表格形式记录"修正前→修正后"，含旧值属正常，排除
SKIP_PREFIX = ("技术验收记录", "立项阶段总验收记录", "申报书修改验收记录")
body = "\n".join(io.open(os.path.join(D, f), encoding="utf-8").read()
                 for f in dfiles if not f.startswith(SKIP_PREFIX))
allt = t + "\n" + body
for k, want in [("10.04", 0), ("9.33", 1), ("10.3 / 15.4 / 20.6", 0),
                ("9.7 / 14.5 / 19.4", 1), ("20 秒取样", 0), ("18 秒", 1),
                ("92.8", 1), ("h=61", 1), ("0—20kPa", 1)]:
    n = allt.count(k)
    good = (n == 0) if want == 0 else (n > 0)
    line("   %-22s 出现 %3d 次  %s" % (k, n, "✓" if good else "✗"))
    if good: ok += 1
    else: bad += 1

# ---------- 4) 结构 ----------
line("\n【4】结构")
line("   docs 文档数: %d（现行）" % len(dfiles))
arch = os.path.join(WS, "archive")
line("   archive 内容: %s" % ", ".join(sorted(os.listdir(arch))))
top_docx = [f for f in os.listdir(WS) if f.endswith(".docx")]
line("   顶层 docx: %s" % ", ".join(sorted(top_docx)))
line("   tmp: %s" % ("空 ✓" if not os.listdir(os.path.join(WS, "tmp")) else "非空 ✗"))
sim = os.path.join(WS, "simulation", "project_review")
line("   仿真代码: %d 个 .py" % len([f for f in os.listdir(sim) if f.endswith(".py")]))
line("   复核工具: %d 个" % len(os.listdir(os.path.join(sim, "tools"))))
line("   结果文件: %d 个" % len(os.listdir(os.path.join(sim, "results"))))
line("   图: %d 个" % len(os.listdir(os.path.join(sim, "figures"))))

# ---------- 5) 申报书完整性 ----------
line("\n【5】申报书（项目书，本次未动）")
P = os.path.join(WS, "大创申报书_正式稿6.docx")
x = zipfile.ZipFile(P).read("word/document.xml").decode("utf-8")
line("   结构: 表格 %d | 图片 %d | 公式 %d | 杂散圆点 %d" % (
    x.count("<w:tbl>"), x.count("<w:drawing>"),
    x.count("<m:oMath>"), x.count("\u2219")))
for k in ["92.8", "差压", "挑战杯", "十五五", "专用材料费"]:
    line("   含「%s」: %s" % (k, "✓" if k in x else "✗"))
line("   备份存在: %s" % ("✓" if os.path.exists(P.replace(".docx", "_备份.docx")) else "✗"))

# ---------- 6) 仓库备份 ----------
line("\n【6】仓库备份")
b = r"C:\Users\Lenovo\Desktop\滴智卫_git备份_20261016.bundle"
if os.path.exists(b):
    line("   %s  %.1f MB  ✓" % (os.path.basename(b), os.path.getsize(b) / 1024 / 1024))
else:
    line("   ✗ 未找到")

line("\n" + "=" * 84)
line("校验项：通过 %d，失败 %d" % (ok, bad))
line("=" * 84)
