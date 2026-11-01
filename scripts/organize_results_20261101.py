"""Collect project artifacts without changing either source working directory."""
from pathlib import Path
import subprocess, shutil, hashlib, json, re

BASE = Path(__file__).resolve().parents[1]
OUTER = BASE.parent
DEST = OUTER / '成果整理_20261101'
RESULT = DEST / '成果汇总'
MANIFEST = []

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git_files(*args):
    return [x for x in subprocess.check_output(['git', *args, '-z'], cwd=BASE).decode('utf-8').split('\0') if x]

def allowed(relative):
    p = Path(relative)
    return not (p.suffix.lower() in {'.sqlite', '.db', '.log', '.exe', '.pyc'}
                or any(x in p.parts for x in ['.git', 'tmp', 'output', '__pycache__', 'node_modules', '.workbuddy', 'build'])
                or p.name.startswith(('~$', '.env')) or p.name == 'tmp_patch_math.py')

source_files = sorted(set(git_files('ls-files')) | set(git_files('ls-files', '--others', '--exclude-standard')))
for name in source_files:
    src = BASE / name
    if src.is_file() and allowed(name):
        dst = DEST / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

# Remove generated local data only from the new export worktree.
for name in git_files('ls-files'):
    if not allowed(name):
        p = DEST / name
        if p.is_file():
            p.unlink()

def collect(relative, target, source_root=BASE, purpose=''):
    src = source_root / relative
    if not src.is_file():
        raise FileNotFoundError(src)
    dst = RESULT / target
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(src) == sha(dst)
    MANIFEST.append({'文件': dst.relative_to(DEST).as_posix(), '来源': str(src.relative_to(source_root)).replace('\\', '/'),
                     '来源目录': '当前研究目录' if source_root == BASE else '原工作目录',
                     '用途': purpose, '字节数': dst.stat().st_size, 'SHA256': sha(dst)})

def write(name, text):
    p = DEST / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + '\n', encoding='utf-8')

collect('tmp/v4_section_merge_20261028/大创申报书v4_替换校核稿.docx', '01_申报与汇报/申报书_整合参考稿_20261028.docx', purpose='已留存的v4分节合并版本，不代表用户此后手工修改稿')
collect('tmp/experiment_language_20261028/3(1)_语言与口径修订.docx', '01_申报与汇报/实验方案与关键问题_语言修订稿_20261028.docx', purpose='3.4与3.5分节修订')
collect('tmp/references_spacing_20261028/1_参考文献间距修正.docx', '01_申报与汇报/参考文献_间距修订稿_20261028.docx', purpose='五篇中文和三篇英文文献')
collect('deliverables/3_测量平台与软件设计_公式规范精简稿.docx', '01_申报与汇报/测量平台与软件设计_公式分节稿_20261027.docx', purpose='公式原分节稿；最终清理已体现在整合参考稿中')
collect('deliverables/项目实施方案_最终版_20261019.docx', '01_申报与汇报/项目实施方案_历史参考稿_20261019.docx', purpose='实施安排历史版本')
collect('deliverables/立项答辩.pptx', '01_申报与汇报/立项答辩_已有演示稿.pptx', purpose='已有PPT，需与当前方案校对后使用')

for name, dest in [
    ('系统组成与研究边界_框图_20261026', '01_系统组成与研究边界'),
    ('总体设计_横版_Word矢量_20261027', '02_系统总体设计_横版'),
    ('技术路线图_申报书插图_20261027', '03_技术路线_申报插图'),
    ('总体设计_硬件与信息流_Word矢量_20261027', '04_硬件与信息流'),
    ('图3-8_双支路台架三维布局', '05_双支路台架三维布局'),
]:
    for ext in ['.png', '.svg', '.emf']:
        if (BASE / 'deliverables' / (name + ext)).is_file():
            collect('deliverables/' + name + ext, '02_系统与技术图件/' + dest + ext, purpose='申报插图；矢量文件用于Word插入')
cusum = BASE / 'deliverables/块CUSUM诊断流程_横版大字清晰版_20261027'
for p in sorted(cusum.iterdir()):
    if p.suffix.lower() in ['.svg', '.png', '.emf']:
        collect(p.relative_to(BASE), '02_系统与技术图件/06_块级CUSUM流程/' + p.name, purpose='块级判断流程')

collect('deliverables/清水试验台架_V1.2.html', '03_台架与三维模型/双支路清水台架_交互模型.html', purpose='离线交互台架')
for p in (BASE / 'application/models/system_upgrade').iterdir():
    if p.is_file():
        translated = {'bench_layout.glb': '双支路台架.glb', 'bench_layout.step': '双支路台架.step',
                      'bench_layout.obj': 'bench_layout.obj', 'bench_layout.mtl': 'bench_layout.mtl',
                      'bench_layout.json': '台架结构参数.json', 'bench_scene.json': '台架场景参数.json',
                      'guard_checks.json': '模型空间检查.json'}
        collect(p.relative_to(BASE), '03_台架与三维模型/模型源文件/' + translated.get(p.name, p.name), purpose='设计模型；OBJ与MTL保留成对原名')

for stem, title in [('E9_block_threshold', '01_块级门限与幅度对照'), ('E10_robustness', '02_噪声与漂移鲁棒性'), ('E11_switching', '03_轮灌切换对照')]:
    for ext in ['.json', '.txt']:
        collect('simulation/project_review/results/' + stem + ext, '04_算法与仿真/结果记录/' + title + ext, purpose='已有合成实验记录；本次未重跑')
for stem, title in [('cusum_trace', '累积统计量示例'), ('noise_tau', '噪声与持续时间对照'), ('switching_margin', '切换对照'), ('detection_boundary', '检出边界')]:
    for ext in ['.svg', '.png']:
        p = BASE / 'simulation/project_review/figures' / (stem + ext)
        if p.is_file():
            collect(p.relative_to(BASE), '04_算法与仿真/结果图/' + title + ext, purpose='合成实验图')

for p in ['docs/项目内容与结构总览.md', 'docs/3_公式与方法审校说明_20261027.md']:
    collect(p, '07_实施规划与核对/' + Path(p).name, purpose='范围、实现状态与审校依据')

# Preserve internal relative links within supplier materials.
for folder, title in [('硬件图片与原理图_20261027', '器件图片与原理资料'), ('1500元台架选型与原图_20261027', '台架选型与采购参考')]:
    for p in sorted((OUTER / folder).rglob('*')):
        if p.is_file() and p.suffix.lower() not in ['.zip', '.exe', '.log']:
            collect(p.relative_to(OUTER), '06_硬件选型与资料/' + title + '/' + p.relative_to(OUTER / folder).as_posix(), source_root=OUTER, purpose='国内采购候选和厂家资料；报价以采购时为准')

write('README.md', '''# 滴智卫

基于LoRa的南疆滴灌支管道早期故障诊断物联网原型系统。

项目面向南疆规模化棉田膜下滴灌支管巡检，利用两路压力和一路流量识别等效泄漏、局部过流受限，结合LoRa通信和本地巡检平台，关联异常提示、人工核查与复测记录。实施计划为2027年3月至2028年2月。

## 从这里看成果

| 内容 | 入口 | 当前内容 |
| --- | --- | --- |
| 成果总览 | [成果目录](成果汇总/成果目录.md) | 分类、版本和阅读顺序 |
| 申报与汇报 | [材料说明](成果汇总/01_申报与汇报/材料说明.md) | 已留存整合稿、分节修订、参考文献和已有PPT |
| 系统与技术图件 | [图件说明](成果汇总/02_系统与技术图件/图件说明.md) | 系统组成、技术路线、信息流和CUSUM流程 |
| 台架与三维模型 | [模型说明](成果汇总/03_台架与三维模型/模型说明.md) | 离线交互模型、STEP、GLB及OBJ源文件 |
| 算法与仿真 | [研究说明](成果汇总/04_算法与仿真/研究说明.md) | 不重叠块CUSUM、合成对照与结果图 |
| 软件演示 | [运行说明](成果汇总/05_软件与桌面演示/运行说明.md) | 本地网页、Python服务、桌面源码及下载 |
| 国内硬件资料 | [选型说明](成果汇总/06_硬件选型与资料/选型说明.md) | 采购候选、原理资料与来源记录 |
| 实施规划 | [后续工作](成果汇总/07_实施规划与核对/后续工作.md) | 申报、台架验证与论文三阶段安排 |

## 源码目录

为保持脚本导入和资源路径可用，源码目录保留原名；面向阅读与交付的材料统一使用中文名称。

| 路径 | 作用 |
| --- | --- |
| `simulation/project_review/` | 当前块级诊断研究；E9门限、E10鲁棒性、E11切换对照 |
| `firmware/` | 节点采集编排、C诊断、协议和目标驱动 |
| `prototype/` | 接收、SQLite存储、事件身份、重传与控制模拟 |
| `scripts/run_platform.py` | 本地网页服务入口 |
| `desktop/` | Windows窗口与PyInstaller打包 |
| `application/models/` | 台架模型及参数 |
| `deliverables/` | 原有网页、图件与历次交付 |
| `docs/`、`archive/` | 研究说明与历史记录 |

## 当前完成程度

已有水力建模、合成算法对照、采集与协议的主机测试、巡检平台原型、桌面V1.3演示和台架设计模型。真实器件标定、台架装配、目标板外设联调、实际LoRa链路与整机电流测量属于实施阶段任务。

新块级CUSUM研究与既有桌面诊断调用链并存；桌面V1.3作为已有演示版本归档，本次整理未重编译EXE，也未重跑全部研究试验。

## 快速运行

```powershell
python -m pip install -r requirements-platform.txt
python scripts/run_platform.py --port 8765
```

浏览器打开 `http://127.0.0.1:8765`。桌面源码运行和Windows下载见[运行说明](成果汇总/05_软件与桌面演示/运行说明.md)。

整理日期：2026年11月1日。[文件清单](成果汇总/文件清单.json)记录来源、用途及SHA256，原工作目录保持原样。
''')

write('成果汇总/成果目录.md', '''# 项目成果目录

按“申报表达—技术论证—实现与验证—后续实施”组织现有成果。先读申报材料说明，再查看系统图和模型，最后对应算法记录与软件入口。

1. [申报与汇报](01_申报与汇报/材料说明.md)：整合参考稿、实验方案分节、公式分节、参考文献、项目简介和已有PPT。
2. [系统与技术图件](02_系统与技术图件/图件说明.md)：系统组成、总体设计、技术路线、信息流和块级诊断流程。
3. [台架与三维模型](03_台架与三维模型/模型说明.md)：双支路清水台架的交互视图与设计源文件。
4. [算法与仿真](04_算法与仿真/研究说明.md)：10秒不重叠块CUSUM及门限、噪声、切换对照。
5. [软件与桌面演示](05_软件与桌面演示/运行说明.md)：网页、本地服务、桌面程序和下载入口。
6. [硬件选型与资料](06_硬件选型与资料/选型说明.md)：国内采购候选、供应商资料和图片来源。
7. [实施规划与核对](07_实施规划与核对/后续工作.md)：实物验证、系统联调与论文安排。

命名采用“内容名称_用途或状态_日期”，例如“实验方案与关键问题_语言修订稿_20261028”。研究结果沿用实验编号，中文汇总名与原始记录一一对应。旧目录不因文件名带有“最终”就优先于较新的修订。
''')

write('成果汇总/01_申报与汇报/材料说明.md', '''# 申报与汇报材料

| 文件 | 阅读用途 |
| --- | --- |
| [申报书整合参考稿](申报书_整合参考稿_20261028.docx) | 留存的v4合并稿，含3.3.3和3.3.4公式清理 |
| [实验方案与关键问题](实验方案与关键问题_语言修订稿_20261028.docx) | 3.4与3.5的较新语言修订，统一采集和试验口径 |
| [参考文献](参考文献_间距修订稿_20261028.docx) | 5篇中文、3篇英文，已核查书目信息 |
| [公式分节稿](测量平台与软件设计_公式分节稿_20261027.docx) | 测量和软件方法原分节稿；公式末尾标点等以整合参考稿为准 |
| [实施方案历史参考稿](项目实施方案_历史参考稿_20261019.docx) | 工作包与任务安排参考 |
| [已有答辩稿](立项答辩_已有演示稿.pptx) | 原有演示稿，内容需按当前申报方案更新 |
| [项目简介](项目简介_三段稿.md) | 背景、系统做法与意义 |

整合参考稿与较新的分节修订分开留存，本次没有重新合成或改写Word正文。此前桌面的“大创申报书v4.docx”在本次整理时未找到，故使用已保存的合并文件，并明确版本用途。
''')

write('成果汇总/01_申报与汇报/项目简介_三段稿.md', '''# 项目简介

南疆棉田面积大，滴灌管线长，支管出现接头漏水、局部过流受限等问题时，往往需要人工沿线排查，费时费力，也容易发现不及时。轮灌开关和供水压力调整还会引起压力、流量变化，单看某一项读数，很难判断是正常调节还是管路出了问题。

针对上述问题，本项目拟研制基于LoRa的滴灌支管早期故障诊断物联网原型系统。系统以STM32为主控，采集两路压力和一路流量，结合健康状态下的压力—流量关系、区段等效阻力及块级累积和（CUSUM）方法识别持续异常，并通过工况复判减少正常调节造成的误报。节点采用常规低频观测、异常触发后加密采集的策略，经LoRa将异常信息上传至本地巡检平台，关联支管编号、测点区段与监测记录，支持人工核查、处置和复测。目前已形成水力模型、算法仿真及巡检软件原型，后续将通过双支路清水台架开展泄漏、受限与正常扰动对照，完成节点及系统联调验证。

项目旨在将支管运行监测与巡检维护衔接起来，帮助管理人员及时发现异常、缩小排查范围并核验处理效果，为南疆棉田滴灌管网的精细化管理提供技术参考，也为后续田间试用和诊断方法研究积累基础。
''')

write('成果汇总/02_系统与技术图件/图件说明.md', '''# 系统与技术图件

编号01说明系统组成与研究边界；02展示横向总体设计；03展示技术路线；04展开硬件与信息流；05说明双支路台架布局；06为块级CUSUM判断流程。

PNG用于快速查看，SVG用于矢量编辑；配有EMF的图可用于Word矢量插入。请从文件插入，避免复制网页缩略图。这里是分类后的已有图件，没有新增绘图或改动技术关系。其他备选版仍保存在原deliverables目录。
''')
write('成果汇总/03_台架与三维模型/模型说明.md', '''# 双支路台架与三维模型

下载后用浏览器打开[交互模型](双支路清水台架_交互模型.html)。模型用于说明测点、受限元件、旁路、收集装置和装配空间。

[模型源文件](模型源文件/)保留GLB、STEP、OBJ及参数文件。OBJ内引用MTL，二者保留原名以便加载；其余交付名使用中文。完整原始模型位于`application/models/`。设计模型与空间检查记录不等同于实际装配或水路测试。
''')
write('成果汇总/04_算法与仿真/研究说明.md', '''# 算法与仿真成果

当前研究以压力—流量健康参照、区段等效阻力和双通道块级CUSUM为主线。固定采集基线每1秒读取压力，按10秒不重叠块更新判据；事件触发采集作为对照策略，流量脉冲持续计数。

| 分类结果 | 原始入口 | 用途 |
| --- | --- | --- |
| 门限与幅度对照 | `simulation/project_review/E9_block_threshold.py` | 门限、故障幅度与持续时间 |
| 噪声与漂移鲁棒性 | `simulation/project_review/E10_robustness.py` | 噪声相关性、漂移与工作范围 |
| 轮灌切换对照 | `simulation/project_review/E11_switching.py` | 切换干扰和判断暂停的影响 |
| 共享方法 | `simulation/project_review/lib_block.py` | 分块、健康参照、残差与CUSUM |

本目录记录和曲线来自现有合成试验，本次仅整理与校验文件，不重算识别率。实验记录中的模型参数和批次条件应与图表一并阅读。桌面V1.3仍保留既有诊断调用路径，新块级方法的端到端集成列入后续工作。
''')
write('成果汇总/05_软件与桌面演示/运行说明.md', '''# 巡检软件与桌面演示

## 本地网页

在仓库根目录安装依赖并启动服务：

```powershell
python -m pip install -r requirements-platform.txt
python scripts/run_platform.py --port 8765
```

打开 `http://127.0.0.1:8765`。网页文件为`deliverables/index.html`，接收与存储在`prototype/`。本地数据库由程序创建，不随仓库上传。

## Windows桌面

[下载桌面V1.3便携包](https://github.com/Hua-bing-666/dizhiwei/releases/tag/results-20261101)。解压完整目录后运行“滴智卫.exe”，保留随包依赖和许可证。

源码运行：

```powershell
python -m pip install -r desktop/requirements.txt
python desktop/app.py
```

桌面程序用于监测回放、异常事件、历史查询、三维查看和模拟控制。它是已有V1.3构建，本次没有重新编译，也没有将合成回放改称真实传感器数据。

## 目录分工

`desktop/`负责窗口和打包，`scripts/run_platform.py`负责本地服务，`prototype/`负责事件与SQLite，`deliverables/index.html`负责界面。项目文档和报告在成果目录阅读。
''')
write('成果汇总/06_硬件选型与资料/选型说明.md', '''# 国内硬件选型与资料

本目录保留两套既有材料：器件图片与原理资料、台架选型与采购参考。各子目录中的索引、来源链接与文件校验记录一并保留。

当前申报参考稿采用STM32F103C8T6、两路压力、ADS1115、SEN0549、microSD和E220无线模块。既有资料同时保留GD32、差压变送器等候选方案，供后续比较，不代表这些器件已同时采购或装配。价格与预算记录按原日期留存，采购时重新核对。
''')
write('成果汇总/07_实施规划与核对/后续工作.md', '''# 后续实施安排

| 阶段 | 主要工作 | 完成依据 |
| --- | --- | --- |
| 申报准备 | 合并已确认的分节修改，核对硬件、指标、图号、引文和PPT | 一份内容一致并逐页检查的学校模板申报稿 |
| 2027年3月至2028年2月 | 器件接入、独立标定、双支路台架、故障与正常对照、LoRa和连续运行 | 实物记录、独立标签、原始测量及结题材料 |
| 论文深化 | 从辨识边界、跨工况参照或事件采集取舍中选定主线 | 可复算的真实数据、对照分析和论文稿 |

最近工作顺序：统一器件与量程；对齐块级判据和采集、CSV、接收端；贯通平台展示与事件记录；完成目标板和真实水路验证。控制功能先按软件请求及指示输出演示安排。

已有成果的完整历史说明见本目录的《项目内容与结构总览》和《公式与方法审校说明》。其中10月26日的硬件候选与旧版本差异属于当时记录，应结合当前申报稿阅读。
''')

ignore = DEST / '.gitignore'
with ignore.open('a', encoding='utf-8') as f:
    f.write('\n# Runtime state and local build products\ndeliverables/data/\nfirmware/build/\n__img_tmp*/\ntmp_patch_math.py\n*.sqlite\n*.sqlite-*\n')

(RESULT / '文件清单.json').write_text(json.dumps({'整理日期': '2026-11-01', '成果文件数': len(MANIFEST), '文件': MANIFEST}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'collected_files': len(MANIFEST), 'collected_mb': round(sum(x['字节数'] for x in MANIFEST) / 1024 ** 2, 2), 'worktree': str(DEST)}, ensure_ascii=False))
