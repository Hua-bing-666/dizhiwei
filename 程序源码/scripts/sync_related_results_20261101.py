"""Curate specifically requested conversation outputs; never publish chat logs."""
from pathlib import Path
from zipfile import ZipFile
import json, hashlib, shutil, re, os

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
RESULT = BASE / '成果汇总'
MANIFEST_PATH = RESULT / '文件清单.json'
manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
records = {x['文件']: x for x in manifest['文件']}
added = []

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(relative, text):
    p = BASE / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + '\n', encoding='utf-8')
    return p

def copy(source, relative, purpose):
    source = ROOT / source
    target = RESULT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert digest(target) == digest(source)
    name = target.relative_to(BASE).as_posix()
    records[name] = {'文件': name, '来源': source.relative_to(ROOT).as_posix(),
                     '来源目录': '原工作目录', '用途': purpose,
                     '字节数': target.stat().st_size, 'SHA256': digest(target)}
    added.append(name)

copy('output/第八部分_正文融图完善_20261027/第八部分_正文融图与平台补图稿.docx',
     '01_申报与汇报/已有基础_正文融图与平台补图稿_20261027.docx', '第八部分最新独立正文；五张主图已在用户v4中')
copy('output/第四部分_国内外研究现状_20261028/国内外研究现状_规范引用稿.docx',
     '01_申报与汇报/国内外研究现状_规范引用稿_20261028.docx', '第四部分独立修订，正文上标引用及八篇文献')
copy('deliverables/硬件模块图文修订_20261027/硬件模块设计_图文修订稿.docx',
     '01_申报与汇报/硬件模块设计_图文修订稿_20261027.docx', '硬件模块独立修订稿')
copy('deliverables/经费预算修订_20261028/经费预算表_四项简洁稿.docx',
     '01_申报与汇报/经费预算_四项简洁候选稿_20261028.docx', '讨论形成的预算候选，未覆盖用户随后确认的v4预算')
for name in ['图3-11_事件接收确认与重传去重_彩色版.png',
             '图3-9_双支路清水台架与测点布置_逻辑修订版.png',
             '图3-9_水力逻辑修订说明.md', '图3-9_逻辑修订版_绘图提示词.txt', '图3-11_绘图提示词.txt']:
    copy('deliverables/图表美化/' + name, '02_系统与技术图件/07_彩色原理图与设计说明/' + name,
         '彩色图及逻辑修订记录；Q前置水路为候选方案，尚未替换v4正文')
for p in (ROOT / 'deliverables/硬件模块图文修订_20261027').rglob('*'):
    if p.is_file() and p.suffix != '.docx':
        copy(p.relative_to(ROOT), '06_硬件选型与资料/硬件模块图文配套/' + p.relative_to(ROOT / 'deliverables/硬件模块图文修订_20261027').as_posix(), '硬件独立插图与来源')

# Preserve original subdirectory names because the reproducibility code uses them.
source_bundle = ROOT / 'output/第八部分_机制与轨迹图组_20261027'
bundle_relative = '04_算法与仿真/第八部分_彩图与复现'
for p in source_bundle.rglob('*'):
    if not p.is_file() or '__pycache__' in p.parts or p.suffix.lower() in ['.pyc', '.log']:
        continue
    if any(x.startswith('page-') for x in p.parts):
        continue
    copy(p.relative_to(ROOT), bundle_relative + '/' + p.relative_to(source_bundle).as_posix(),
         '第八部分七张机制与轨迹图、冻结参数、原始合成记录、代码及原核验记录')
for p in (ROOT / 'output/第八部分_正文融图完善_20261027/figures').glob('*.png'):
    if '平台' in p.name:
        copy(p.relative_to(ROOT), '05_软件与桌面演示/平台截图/' + p.name, '已有软件运行截图，非本次运行')

THREADS = {
    '目标与成果': '01a178e2-da33-7300-891c-8b95b1068e13',
    '年度计划与彩图': '01a17920-c7cf-78e0-b4c9-74d2f90fdfc1',
    '彩图仿真与研究现状': '01a1793c-0676-72e0-bc26-971b87d1f0e6',
    '块级诊断图': '01a17956-08e9-7531-a2c6-6fc6037339d5',
}

def assistant_messages(ident):
    path = next(Path('C:/Users/Lenovo/.codex/sessions/2026/10').rglob('*' + ident + '.jsonl'))
    messages = []
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = row.get('payload', {})
        if row.get('type') == 'response_item' and p.get('type') == 'message' and p.get('role') == 'assistant':
            text = '\n'.join(c.get('text', '') for c in p.get('content', []) if c.get('type') == 'output_text')
            if text:
                messages.append(text)
    return messages

goals = [t for t in assistant_messages(THREADS['目标与成果'])
         if '**3.2 项目目标**' in t and '**项目预期成果**' in t][-1]
goals = goals[goals.index('**3.2 项目目标**'):]
write('成果汇总/01_申报与汇报/项目目标与预期成果_讨论修订稿.md',
      '# 项目目标与预期成果讨论稿\n\n来源：用户指定的目标修订聊天，保留最近一版完整目标与预期成果文字。作为修订依据阅读，当前提交口径以用户确认的v4为主。\n\n' + goals)
schedule = [t for t in assistant_messages(THREADS['年度计划与彩图'])
            if t.startswith('2027年3—4月') and '2028年1—2月' in t][-1]
schedule = schedule.replace('压力、差压及流量参考标定', '两路压力及流量参考标定')
write('成果汇总/07_实施规划与核对/年度目标与工作内容_2027年3月至2028年2月.md',
      '# 年度目标与工作内容\n\n按用户确定的2027年3月至2028年2月实施期整理。两路压力与一路流量为当前测量配置；压力和差压的评价不另增加第三路压力传感器。\n\n' + schedule)

write('成果汇总/04_算法与仿真/第八部分彩图与复现说明.md', '''# 第八部分彩图与复现说明

## 当前呈现

[最新独立正文](../01_申报与汇报/已有基础_正文融图与平台补图稿_20261027.docx)包含五张主图及已有平台截图。用户确认的v4已包含这五张主图，未重复替换。

[彩图与复现目录](第八部分_彩图与复现/)按原结构保留：figures存放5张主图、2张补图的600 dpi PNG、SVG和PDF；evidence存放冻结参数、试次记录与核验结果；code存放绘图和独立复算程序。设计来源是期刊科研图的简洁分面样式，不是Nature发表成果。

## 方法版本

这组彩图对应既有固定门限、稳健门限及累积组合对照，数据来自合成轨迹。较新的10秒不重叠块CUSUM在`simulation/project_review/`中单独研究。两组方法、门限和试验批次分别保留，不互用识别率。

## 核验入口

在仓库根目录运行：

```powershell
python "成果汇总/04_算法与仿真/第八部分_彩图与复现/code/verify_figures.py"
```

依赖numpy、Pillow、pypdf和python-docx。核验会独立复算水力模型、方法统计、区间与采样相位，检查图像、矢量文件和机制稿内嵌图；不重跑全部随机仿真，也不代表真实台架试验。

绘图入口为code/plot_mechanisms.py，重画需要matplotlib。运行绘图或扩展脚本会覆盖该目录对应输出，执行前保留副本。
''')
write('成果汇总/07_实施规划与核对/跨聊天更新与版本对照_20261101.md', '''# 跨聊天更新与版本对照

## 本次纳入的内容

| 来源主题 | 本地落位 | 状态 |
| --- | --- | --- |
| 项目目标、预期成果、硬件及预算 | 01申报与汇报、06硬件资料 | 保留讨论文字、硬件图文稿、四项预算候选 |
| 年度计划、水路与ACK彩图 | 07实施规划、02系统图件 | 年度计划按2028年2月结束；水路布局分版本 |
| 第八部分仿真彩图、第四部分研究现状 | 04算法仿真、01申报与汇报 | 收录最新独立正文及完整机制图复现资料 |
| 横版块级CUSUM流程 | 02系统图件/06块级CUSUM流程 | 此前已收录9760像素PNG及SVG，本次补充来源关系 |

## 当前文档和讨论稿的区别

用户2026年11月1日确认的v4仍作为当前申报书，原文件逐字节保留。本次整理更新资料、计划与索引，没有直接改写该Word文件。

1. **年度结束时间。** 当前v4末段仍写“2028年1—3月”，与用户明确的实施期不一致。独立年度计划统一为“2028年1—2月”；下次编辑主文档时只需同步该段。
2. **水路布置。** v4正文及现用彩图为P0—R—P1—Q—分流。后续逻辑修订图为Q—P0—R—P1—分流，属于另一种布置。后者作为候选，若采用应同步正文、台架模型与装配图；不能仅凭绘制更晚就替换现用图。
3. **预算。** 当前v4为材料5000、印刷2000、资料及知识产权4500、其他500元，总额12000元。四项简洁稿来自较早的讨论，单列为候选，未覆盖用户后来确认的预算。
4. **仿真方法。** 第八部分彩图对应既有候选方法对照；10秒不重叠块CUSUM为另一研究版本。图、参数与数据按各自方法使用。
5. **已有基础。** v4已内嵌五张机制与轨迹主图和彩色ACK图。本次补齐独立PNG、SVG、PDF、代码和数据，保留较早构图在原output目录，不堆入当前分类目录。

## 核验范围

本次检查文件来源、目录链接、原始文件完整性，并运行既有彩图的独立数值和图件核验。没有新增实测数据、重编译桌面程序或修改硬件选型。
''')

write('成果汇总/02_系统与技术图件/07_彩色原理图与设计说明/版本说明.md', '''# 彩色图版本说明

ACK彩图已出现在用户确认的v4中，接收确认表示服务保存事件后的应答，不代表人工查看或维护完成。

本目录的水路逻辑修订图采用Q前置方案，与v4现用的Q后置方案不同，作为后续设计候选。配套说明保留其假设、模型关系和可替换文字；当前v4正文不因本次整理而更改。图件为示意用途。
''')

readme = BASE / 'README.md'
text = readme.read_text(encoding='utf-8')
text = text.replace('## 从这里看成果', '本次跨聊天更新：[版本对照](成果汇总/07_实施规划与核对/跨聊天更新与版本对照_20261101.md)，含第八部分彩图复现、研究现状、年度计划与设计候选。\n\n## 从这里看成果')
text = text.replace('| 算法与仿真 | [研究说明](成果汇总/04_算法与仿真/研究说明.md) | 不重叠块CUSUM、合成对照与结果图 |', '| 算法与仿真 | [研究说明](成果汇总/04_算法与仿真/研究说明.md) | 块级CUSUM及[第八部分彩图复现](成果汇总/04_算法与仿真/第八部分彩图与复现说明.md) |')
readme.write_text(text, encoding='utf-8')
p = RESULT / '01_申报与汇报/材料说明.md'
text = p.read_text(encoding='utf-8') + '''
## 补充修订材料

- [项目目标与预期成果讨论稿](项目目标与预期成果_讨论修订稿.md)
- [研究现状规范引用稿](国内外研究现状_规范引用稿_20261028.docx)
- [已有基础正文与平台补图稿](已有基础_正文融图与平台补图稿_20261027.docx)
- [硬件模块图文稿](硬件模块设计_图文修订稿_20261027.docx)
- [四项预算候选稿](经费预算_四项简洁候选稿_20261028.docx)
- [年度目标与工作内容](../07_实施规划与核对/年度目标与工作内容_2027年3月至2028年2月.md)

这些是独立修订与来源材料，不自动替代已确认的v4。差异见[跨聊天版本对照](../07_实施规划与核对/跨聊天更新与版本对照_20261101.md)。
'''
p.write_text(text, encoding='utf-8')
p = RESULT / '04_算法与仿真/研究说明.md'
p.write_text(p.read_text(encoding='utf-8') + '\n另见[第八部分彩图与复现说明](第八部分彩图与复现说明.md)，既有方法对照和新块级研究分别管理。\n', encoding='utf-8')
p = RESULT / '成果目录.md'
p.write_text(p.read_text(encoding='utf-8') + '\n本次补充成果及口径差异见[跨聊天更新与版本对照](07_实施规划与核对/跨聊天更新与版本对照_20261101.md)。\n', encoding='utf-8')

# Rebase imported original-readme links into the curated working tree.
for name in added:
    p = BASE / name
    if p.suffix != '.md':
        continue
    text = p.read_text(encoding='utf-8')
    def rewrite(match):
        target = match[1]
        if target.startswith(('http:', 'https:', '#', '<')):
            return match[0]
        resolved = (p.parent / target).resolve()
        if resolved.exists():
            return match[0]
        source = ROOT / records[name]['来源']
        old_target = (source.parent / target).resolve()
        if old_target.exists():
            return '](' + Path(os.path.relpath(old_target, p.parent)).as_posix() + ')'
        return match[0]
    revised = re.sub(r'\]\(([^)]+)\)', rewrite, text)
    if revised != text:
        p.write_text(revised, encoding='utf-8')
        records[name]['原始SHA256'] = records[name]['SHA256']
        records[name]['SHA256'] = digest(p)
        records[name]['字节数'] = p.stat().st_size

manifest['文件'] = list(records.values())
manifest['成果文件数'] = len(records)
manifest['本次补充文件数'] = len(added)
manifest['关联聊天'] = THREADS
MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
(RESULT / '07_实施规划与核对/关联来源.json').write_text(json.dumps(THREADS, ensure_ascii=False, indent=2), encoding='utf-8')

write('../当前项目入口.md', '''# 当前项目入口

整理后的工作目录：[成果整理_20261101](成果整理_20261101/README.md)。

- [当前申报书v4](成果整理_20261101/成果汇总/01_申报与汇报/申报书_当前定稿_v4_20261101.docx)
- [完整成果目录](成果整理_20261101/成果汇总/成果目录.md)
- [跨聊天更新与版本对照](成果整理_20261101/成果汇总/07_实施规划与核对/跨聊天更新与版本对照_20261101.md)
- [年度目标与工作内容](成果整理_20261101/成果汇总/07_实施规划与核对/年度目标与工作内容_2027年3月至2028年2月.md)
- [GitHub仓库](https://github.com/Hua-bing-666/dizhiwei)

原工作目录与“副本”保留历史内容；新材料先进入整理目录，避免两套版本交叉覆盖。
''')
print(json.dumps({'new_files': len(added), 'manifest_files': len(records), 'word_proposal_unchanged': True}, ensure_ascii=False))
