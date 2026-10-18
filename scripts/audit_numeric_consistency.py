# -*- coding: utf-8 -*-
"""A6　全项目数值口径统一审计。

目的：把散落在 README / docs / application / 申报书 docx 中的"受控数值"扫出来，
      与冻结口径逐条比对，输出冲突清单，防止申报材料互相打架。

用法：
    python scripts/audit_numeric_consistency.py                # 扫描并输出报告
    python scripts/audit_numeric_consistency.py --banner        # 另：给历史文档加盖废止横幅
    python scripts/audit_numeric_consistency.py --json          # 只输出 JSON

判定口径文件：本文件顶部的 RULES 常量（唯一真源）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "数值口径统一清单.md"
OUT_JSON = ROOT / "docs" / "数值口径统一清单.json"

# ---------------------------------------------------------------------------
# 冻结口径字典（唯一真源）
# ---------------------------------------------------------------------------

# 现行文档：口径必须与 CANON 一致
CURRENT_DOCS = {
    "README.md",
    "docs/项目方案与技术路线_现状呈报.md",
    "docs/项目方案批判性复核.md",
    "docs/项目修改计划_P0P1P2.md",
    "docs/硬件选型与BOM冻结_v2.md",
    "docs/硬件软件匹配度审查_v2.2.md",
    "docs/田间落地可行性与硬件调整.md",
    "docs/仿真建模跑通记录.md",
    "docs/固件最小链路跑通记录.md",
    "docs/仿真建模真实性缺口补齐_E10.md",
    "docs/项目方案与技术路线_现状呈报.md",
    "docs/技术路线_20261017.md",
    "docs/项目实施方案_分块版_申报书用.md",
    "docs/技术路线_申报书版.md",
    "docs/技术路线_分块版_申报书用.md",
    "docs/技术路线_分块详解与可行性验证.md",
    "docs/项目场景与边界_大创版.md",
    "docs/立项阶段总验收记录.md",
    "docs/申报书修改验收记录.md",
    "application/实施项目书.md",
    "docs/给老师汇报提纲.md",
}

# 历史文档：口径未同步，保留作方法学/推演过程对照，不再作为引用来源
HISTORY_DOCS = {
    "docs/硬件选型与BOM冻结.md",
    "docs/技术路线与验证方案_立项完成稿.md",
    "docs/最优替代方案与可行性验证.md",
    "docs/方案最优性评估_多维.md",
    "docs/检索信息清单与项目内容核对.md",
    "docs/检索结果汇总与项目执行规划.md",
    "docs/未确认项处置与执行计划_技术路线详解.md",
    "docs/文献定位与技术路线新意评估.md",
    "docs/基于场景与政策的项目任务规划.md",
    "docs/项目实施详细步骤与技术路线总纲.md",
    "docs/诊断算法客观评价.md",
    "docs/软硬件落地实施方案_成本与可实现性.md",
    "docs/项目实施方案_20261017.md",
    "docs/第三部分对抗性审查与优化计划.md",
    "docs/第三部分修改与项目执行计划_可验收版.md",
    "docs/可视化规范与配图方案.md",
}

# 复核/登记类文档：其本职就是引述"被废止值 → 现行值"的对照，
# 命中默认降为 REF（对照引用），不计入冲突。
REVIEW_DOCS = {
    "docs/项目方案批判性复核.md",
    "docs/项目修改计划_P0P1P2.md",
    "docs/立项阶段总验收记录.md",
    "docs/申报书修改验收记录.md",
    "docs/项目方案与技术路线_现状呈报.md",
    "docs/仿真建模跑通记录.md",
    "docs/固件最小链路跑通记录.md",
}

# 待重写文档：阶段二 B1（技术路线分块版）会整体覆盖，此处只登记不阻塞
PENDING_REWRITE = {
    "docs/技术路线_申报书版.md",
    "docs/技术路线_分块详解与可行性验证.md",
    "application/正式模板正文.md",
    "application/PPT逐页内容与讲稿.md",
}

# 冻结值（写进报告，人工核对用）
CANON = [
    ("N01", "差压变送器量程/精度", "0—40 kPa 档（厂家最小标准档，订货号 K040/m400）/ ±0.5%FS / U ≤ 0.20 kPa",
     "0—20 kPa、±0.25%FS、±0.1%FS 三档厂家均不存在；「35—40 kPa / 0—35 kPa」为渠道资料误植（官方选型表 V6.0 最小标准档为 0—40 kPa，400 mbar）"),
    ("N02", "判据结构", "10 s 不重叠块 + 块内算术平均 + 每块累积一次 CUSUM（k=0.5，n=0.50）",
     "1 s 重叠窗（相邻样本重叠 90%，有效样本数被高估，门限被高估约 57 倍）"),
    ("N03", "CUSUM 门限", "h* = 26（仿真条件；目标 FAR≤1%，实测 0.00%，ARL0>6.2 h @95%）",
     "h=61（重叠版反推）、h=5（教科书写法，健康段 40/40 误报）、0.06/0.6 旧门限"),
    ("N04", "泄漏可检边界", "+2%（80 s 注入窗，40/40）；+5% 需 20 s；+10% 需 10 s",
     "「5% 不可检 / 8% 可检」（产自错误门限与错误的注入口径）"),
    ("N05", "受限可检边界", "+50%（80 s 窗，40/40）；+30% 需 ≥5 min 累积（80 s 仅 32/40）",
     "「+30% 可检」「+20% 为 8/10」"),
    ("N06", "压力不确定度需求", "+2% 边界下 U ≤ 2.0 kPa 仍达标；设计工况 0.20 kPa（0—40 kPa 档 × ±0.5%FS），余量 10 倍",
     "「U 到 5 kPa 仍 10/10，瓶颈不在传感器精度」（该结论由 +10% 幅度测出，无区分度）"),
    ("N07", "采样契约", "1 s 提交 + 10 s 滑动判据窗（固件 end_ms=(t+1)*1000）", "—"),
    ("N08", "协议帧长", "55 / 57 / 24 B（第七轮后 v2）", "44 / 24 B（旧版）"),
    ("N09", "BOM 总额", "2409—5018 元（v2.2，含八项漏项）", "1980—4510 元（v1，漏八项）"),
    ("N10", "LoRa 发射功率", "≤10 dBm（433.05—434.79 MHz 免执照限值 10 mW e.r.p.）",
     "22 dBm / 22.5 dBm（≈178 mW，超标）"),
    ("N11", "MCU", "GD32F103CBT6（128 KB Flash）", "STM32F103C8T6 作为备选或正式选型（选型已定死 GD32）"),
    ("N12", "ADC", "SGM58031（pin-to-pin 兼容 ADS1115）", "以 ADS1115 作为正式选型"),
    ("N13", "慢漂移容限", "K 通道约 1%/h；Q 通道全程 ≤0.10%（等效 0.60%/h）", "—"),
    ("N14", "台架必测四项", "σ_gp/σ_dp/σ_q、噪声时间常数 τ（τ≤10 s 才可直接用块判据）、K 通道漂移速率（≥8 h 静置）、流量计长期稳定性（称重法）", "—"),
    ("N15", "仿真入口", "python simulation/project_review/run_all.py（七步，约 12.6 s 全绿）",
     "run_experiments.py（已移 legacy，使用错误门限 h=5）"),
    ("N16", "仿真数据性质", "合成数据 physical_data=False，20 个基础序列复用，不代表实物识别率", "把 480 试次写成独立实测"),
]

# 扫描规则：id, 级别(BLOCK=现行文档必须清零 / WARN=提示), 说明, 正则
RULES = [
    ("N01", "BLOCK", "差压量程写成 0—20 kPa（厂家无此档）",
     r"0[—\-~]20\s*kPa|20\s*kPa\s*差压|0[—\-~]20kPa"),
    ("N01", "BLOCK", "差压量程写成 ±0.25%FS / ±0.1%FS（厂家无此档）",
     r"±\s*0\.25\s*%FS|±\s*0\.1\s*%FS|0\.25%FS|0\.1%FS"),
    ("N01b", "BLOCK", "差压量程写成 35—40 kPa / 0—35 kPa（官方选型表 V6.0 最小标准档为 0—40 kPa，35 为渠道资料误植；本规则不认 ±0.5%FS 同现豁免，只认对照措辞）",
     r"35\s*[—\-~…]\s*40\s*kPa|0\s*[—\-~…]\s*35\s*kPa|0\.\.\.\s*35\s*kPa"),
    ("N03", "BLOCK", "门限写成 h=61 / h=5（已废止）",
     r"h\s*[=＝]\s*61\b|h\s*[=＝]\s*5\b|门限[^。\n；]{0,12}h\*?\s*[=＝]\s*(?:61|5)\b"),
    ("N03", "BLOCK", "旧门限数值 0.06 / 0.6", r"门限[^。\n；]{0,10}0\.0?6\b"),
    ("N03", "BLOCK", "固件门限常量非 26000", r"CUSUM_H_MILLI\s+(\d+)(?!\d)"),
    ("N04", "BLOCK", "泄漏边界写成 5% 不可检 / 8% 可检",
     r"5%\s*不可检|8%\s*可检|5%不可检|8%可检"),
    ("N05", "BLOCK", "受限边界写成 +30% 可检", r"[+＋]\s*30%[^。\n]{0,8}可检|受限[^。\n]{0,12}[+＋]\s*30%"),
    ("N06", "BLOCK", "不确定度结论写成 U 到 5 kPa 仍全检出",
     r"U\s*(?:到|至|达)\s*5\s*kPa|5\s*kPa[^。\n]{0,10}10/10|0[—\-~]5\s*kPa[^。\n]{0,12}10/10"),
    ("N08", "BLOCK", "帧长写成 44 B（旧版）", r"\b44\s*B\b|44\s*字节"),
    ("N09", "BLOCK", "BOM 写成 v1 口径 1980—4510 / 1050—2460 / 930—2050",
     r"1980[—\-~]4510|1050[—\-~]2460|930[—\-~]2050"),
    ("N10", "BLOCK", "LoRa 功率写成 22 dBm 或未写合规限值",
     r"22\.?5?\s*dBm|178\s*mW"),
    ("N15", "BLOCK", "引用已废弃入口 run_experiments.py", r"run_experiments\.py"),
    ("N17", "WARN", "MCU 主频写成 72 MHz（GD32F103 官方数据手册为最高 108 MHz；72 MHz 是 STM32F103 主频，属误记）",
     r"Cortex-M3[，；]?\s*72\s*MHz|72\s*MHz[；;]?\s*128\s*KB"),
    ("N12", "WARN", "出现 ADS1115（须注明 SGM58031 为 P2P 替代）", r"ADS1115"),
    ("N11", "WARN", "MCU 只写 STM32F103C8T6（冻结首选为 GD32F103CBT6）", r"STM32F103C8T6"),
    ("N16", "WARN", "480 试次/960 轨迹表述（须注明为合成复用）", r"480\s*(?:个)?\s*(?:合成)?试次|960\s*条"),
]

# 现行文档中"必须出现"的锚点（缺失即报错）
REQUIRED = {
    "README.md": [r"h\\?\*?\s*[=＝]\s*26", r"10\s*s\s*不重叠块|不重叠块", r"2409[—\-~]5018"],
}

# 同现标记：同一行（或上下一行）出现这些现行值标记时，判定为"对照引用"而非冲突。
# 理由：复核类文档普遍用「旧值 → 新值」表格引述被废止的数值，属正常使用。
CANON_MARKER = {
    "N01": [r"0\s*[—\-~]\s*40\s*kPa", r"±\s*0\.5\s*%FS", r"0\.5%FS"],
    "N03": [r"h\\?\*?\s*[=＝]\s*26", r"26000", r"26\.0", r"h\*=26"],
    "N04": [r"[+＋]\s*2%", r"\+2%", r"40/40"],
    "N05": [r"[+＋]\s*50%", r"5\s*min", r"32/40"],
    "N06": [r"2\.0\s*kPa", r"2\.000\s*kPa", r"0\.20\s*kPa", r"0\.175\s*kPa"],
    "N08": [r"55\s*B", r"57\s*B"],
    "N09": [r"2409", r"5018", r"v2\.2"],
    "N10": [r"10\s*dBm", r"10\s*mW", r"限值", r"合规"],
    # N16：合成数据规模表述——同现"复用/合成/独立实测"标记即为合规说明，不算冲突
    "N16": [r"复用", r"合成", r"独立实测", r"不代表实物"],
    "N15": [r"run_all\.py", r"legacy"],
}

# 全局"对照引用"标记：命中行的上下文出现这些词时，判定为引述被废止值（非冲突）。
GLOBAL_REF_MARKER = [
    r"作废", r"废止", r"旧结论", r"旧口径", r"旧判据", r"旧版", r"假象",
    r"已修正", r"已否定", r"已推翻", r"不得写入", r"不得引用", r"产自",
    r"混成一个量", r"不是物理边界", r"ROC", r"被废止",
]

BANNER = (
    "> ## ⚠ 口径状态：历史版本（2026-10-17 标记）\n"
    ">\n"
    "> 本文档为 2026-10-16 及以前的版本。其中**差压量程、判据门限、可检边界、BOM "
    "等数值已被后续复核推翻**，不再作为现行口径，也不得直接引用进申报书与论文。\n"
    ">\n"
    "> 现行口径见 [数值口径统一清单.md](数值口径统一清单.md)；保留本文档仅作方法学与推演过程对照。\n"
)


def read_docx_text(path: Path) -> list[str]:
    """不用 python-docx：直接解 zip 读 word/document.xml，按段落切分。"""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
    except Exception as exc:  # pragma: no cover
        return [f"<读取失败: {exc}>"]
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return [ln.strip() for ln in xml.split("\n") if ln.strip()]


def iter_targets():
    # 排除本脚本自身产出的报告，避免"报告引用废止值"被当成新冲突
    EXCLUDE = {"docs/数值口径统一清单.md"}
    files: list[tuple[str, Path]] = []
    for rel in sorted(CURRENT_DOCS | HISTORY_DOCS):
        p = ROOT / rel
        if p.exists():
            files.append((rel, p))
    # docs 下其余 md 一律按"未分类"扫描
    for p in sorted((ROOT / "docs").glob("*.md")):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if rel in CURRENT_DOCS or rel in HISTORY_DOCS or rel in EXCLUDE:
            continue
        files.append((rel, p))
    for p in sorted((ROOT / "application").glob("*.md")):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if rel in CURRENT_DOCS or rel in EXCLUDE:
            continue
        files.append((rel, p))
    # 申报书 docx（正文权威稿）
    for p in sorted(ROOT.glob("*.docx")):
        if "备份" in p.name or "修改前" in p.name:
            continue
        files.append((p.name, p))
    return files


def scan_file(rel: str, path: Path):
    if path.suffix.lower() == ".docx":
        lines = read_docx_text(path)
    else:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []
    hits = []
    lines = [ln.rstrip("\n") for ln in lines]
    for idx, line in enumerate(lines, 1):
        if not line.strip():
            continue
        # 对照引用判定窗口：本行 + 上下各一行
        window = "\n".join(lines[max(0, idx - 2): min(len(lines), idx + 1)])
        for rid, level, desc, pat in RULES:
            for m in re.finditer(pat, line):
                if rid == "N03" and m.group(0).strip().isdigit():
                    if m.group(1) == "26000":
                        continue
                    snippet = m.group(0)
                else:
                    snippet = m.group(0)
                # 同现现行值标记 ⇒ 判为对照引用
                if any(re.search(mk, window) for mk in CANON_MARKER.get(rid, [])):
                    level_out = "REF"
                elif any(re.search(mk, window) for mk in GLOBAL_REF_MARKER):
                    level_out = "REF"
                elif rel in REVIEW_DOCS:
                    level_out = "REF"
                elif rel in PENDING_REWRITE:
                    level_out = "TODO"
                else:
                    level_out = level
                hits.append({
                    "rule": rid, "level": level_out, "desc": desc,
                    "line": idx, "snippet": snippet,
                    "context": line.strip()[:180],
                })
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--banner", action="store_true", help="给历史文档加盖废止横幅")
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    args = ap.parse_args()

    results = {}
    for rel, path in iter_targets():
        hits = scan_file(rel, path)
        if hits:
            results[rel] = hits

    if args.banner:
        changed = []
        for rel in sorted(HISTORY_DOCS):
            p = ROOT / rel
            if not p.exists():
                continue
            txt = p.read_text(encoding="utf-8")
            if "口径状态：历史版本" in txt:
                continue
            p.write_text(BANNER + "\n" + txt, encoding="utf-8")
            changed.append(rel)
        print(f"[banner] 已标记 {len(changed)} 份历史文档")
        for c in changed:
            print("  -", c)

    # 汇总
    by_rule = {}
    for rel, hits in results.items():
        for h in hits:
            by_rule.setdefault(h["rule"], []).append({"file": rel, **h})

    total_block = sum(1 for _, hs in results.items() for h in hs if h["level"] == "BLOCK")
    total_ref = sum(1 for _, hs in results.items() for h in hs if h["level"] == "REF")
    total_todo = sum(1 for _, hs in results.items() for h in hs if h["level"] == "TODO")
    real = {f: [h for h in hs if h["level"] in ("BLOCK", "WARN")] for f, hs in results.items()}
    real = {f: hs for f, hs in real.items() if hs}
    cur_files = {f for f in real if f in CURRENT_DOCS}
    docx_files = {f for f in real if f.endswith(".docx")}
    block_in_current = sum(
        1 for f in results if f in CURRENT_DOCS for h in results[f] if h["level"] == "BLOCK"
    )

    # 现行文档必备锚点（缺失即报错）
    missing = []
    for rel, pats in REQUIRED.items():
        p = ROOT / rel
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        for pat in pats:
            if not re.search(pat, txt):
                missing.append((rel, pat))

    payload = {
        "frozen": [{"id": i, "item": it, "canonical": cv, "deprecated": dv} for i, it, cv, dv in CANON],
        "files_scanned": len(list(iter_targets())),
        "files_with_hits": len(results),
        "block_total": total_block,
        "block_in_current_docs": block_in_current,
        "ref_total": total_ref,
        "todo_total": total_todo,
        "current_docs_with_hits": sorted(cur_files),
        "docx_with_hits": sorted(docx_files),
        "missing_anchors": missing,
        "hits": results,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps({k: v for k, v in payload.items() if k != "hits"}, ensure_ascii=False, indent=2))
        return 0

    # ---- Markdown 报告 ----
    L = []
    L.append("# 数值口径统一清单（A6）\n")
    L.append("> 生成脚本：`scripts/audit_numeric_consistency.py`（可复现）　"
             f"扫描文件 **{payload['files_scanned']}** 份，命中 **{payload['files_with_hits']}** 份。\n")
    L.append(f"> BLOCK 级冲突：**{total_block}** 处；其中落在**现行文档**内 **{block_in_current}** 处"
             f"（必须清零），落在申报书 docx 内见 §3。\n")
    L.append(f"> 判定为「对照引用」（同现现行值标记或复核类文档，属正常引述）的命中 **{total_ref}** 处，不计冲突；\n"
             f"> 判定为「待重写」（阶段二 B1 覆盖）的命中 **{total_todo}** 处，见 §5。\n")
    L.append("\n---\n\n## 一、冻结口径字典（唯一真源）\n")
    L.append("| 编号 | 项 | 现行冻结值 | 已废止值 / 废止理由 |")
    L.append("|---|---|---|---|")
    for i, it, cv, dv in CANON:
        L.append(f"| {i} | {it} | {cv} | {dv} |")

    L.append("\n---\n\n## 一之二、现行文档必备锚点检查\n")
    if not missing:
        L.append(r"✅ README 已含 h\*=26 / 不重叠块 / 2409—5018 三个现行锚点。\n")
    else:
        L.append("| 文件 | 缺失锚点（正则） |")
        L.append("|---|---|")
        for rel, pat in missing:
            L.append(f"| {rel} | `{pat}` |")

    L.append("\n---\n\n## 二、现行文档中的冲突（必须清零）\n")
    cur = {f: [h for h in hs if h["level"] in ("BLOCK", "WARN")] for f, hs in results.items() if f in CURRENT_DOCS}
    cur = {f: hs for f, hs in cur.items() if hs}
    if not cur:
        L.append("✅ 无。\n")
    else:
        L.append("| 文件 | 行 | 级别 | 编号 | 问题 | 原文片段 |")
        L.append("|---|---|---|---|---|---|")
        for f in sorted(cur):
            for h in cur[f]:
                ctx = h["snippet"].replace("|", "\\|")[:60]
                L.append(f"| {f} | {h['line']} | {h['level']} | {h['rule']} | {h['desc']} | `{ctx}` |")

    L.append("\n---\n\n## 三、申报书正文（docx）中的冲突\n")
    d = {f: [h for h in hs if h["level"] in ("BLOCK", "WARN")] for f, hs in results.items() if f.endswith(".docx")}
    d = {f: hs for f, hs in d.items() if hs}
    if not d:
        L.append("✅ 无。\n")
    else:
        L.append("| 文件 | 行 | 级别 | 编号 | 问题 | 原文片段 |")
        L.append("|---|---|---|---|---|---|")
        for f in sorted(d):
            for h in d[f]:
                ctx = h["snippet"].replace("|", "\\|")[:60]
                L.append(f"| {f} | {h['line']} | {h['level']} | {h['rule']} | {h['desc']} | `{ctx}` |")
        L.append("\n> 说明：docx 行号为段落序号（按 `word/document.xml` 段落切分），"
                 "修改时以段落文本检索定位。申报书正文的口径改写属阶段二 B2 任务。\n")

    L.append("\n---\n\n## 四、历史文档中的冲突（口径已废止，仅登记）\n")
    hist = {f: hs for f, hs in results.items() if f in HISTORY_DOCS}
    hist = {f: hs for f, hs in hist.items() if hs}
    if not hist:
        L.append("无。\n")
    else:
        L.append("| 文件 | BLOCK | WARN | 处置 |")
        L.append("|---|---|---|---|")
        for f in sorted(hist):
            b = sum(1 for h in hist[f] if h["level"] == "BLOCK")
            w = sum(1 for h in hist[f] if h["level"] == "WARN")
            L.append(f"| {f} | {b} | {w} | 已盖「口径状态：历史版本」横幅，不得引用 |")

    L.append("\n---\n\n## 五、文档口径状态登记\n")
    L.append("### 现行（口径必须与此清单一致）\n")
    strict = sorted(CURRENT_DOCS - REVIEW_DOCS - PENDING_REWRITE)
    for f in strict:
        mark = "⚠ 有冲突" if f in cur else "✅"
        L.append(f"- {mark} `{f}`")
    L.append("\n### 待重写（阶段二 B1/B2 整体覆盖，此处仅登记）\n")
    for f in sorted(PENDING_REWRITE):
        L.append(f"- `{f}`")
    L.append("\n### 复核/过程记录类（允许引述被废止值作对照，命中降为 REF）\n")
    for f in sorted(REVIEW_DOCS):
        L.append(f"- `{f}`")
    L.append("\n### 历史（已盖横幅，保留作方法学对照）\n")
    for f in sorted(HISTORY_DOCS):
        L.append(f"- `{f}`")
    L.append("\n### 未分类（docs/application 下其余 md）\n")
    other = sorted(f for f in real if f not in CURRENT_DOCS and f not in HISTORY_DOCS and not f.endswith(".docx"))
    if other:
        for f in other:
            n = len(results[f])
            L.append(f"- `{f}`（{n} 处命中）")
    else:
        L.append("- 无命中")

    L.append(f"\n\n---\n\n*最后更新：2026-10-17（由 `scripts/audit_numeric_consistency.py` 生成，请勿手改结论行）*\n")
    OUT_MD.write_text("\n".join(L), encoding="utf-8")

    print(f"[audit] 扫描 {payload['files_scanned']} 份，命中 {payload['files_with_hits']} 份")
    print(f"[audit] BLOCK 总数 {total_block}，其中现行文档 {block_in_current} 处")
    print(f"[audit] 报告 -> {OUT_MD.relative_to(ROOT)}")
    print(f"[audit] 数据 -> {OUT_JSON.relative_to(ROOT)}")
    for f in sorted(cur):
        print(f"  ⚠ 现行文档冲突：{f}（{len(cur[f])} 处）")
    for f in sorted(d):
        print(f"  ⚠ 申报书冲突：{f}（{len(d[f])} 处）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
