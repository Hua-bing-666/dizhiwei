from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import hashlib
import json
import shutil
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'tmp/experiment_language_20261028'
QA.mkdir(parents=True, exist_ok=True)
SOURCE = Path('C:/Users/Lenovo/Desktop/3(1).docx')
OUTPUT = QA / '3(1)_语言与口径修订.docx'
BACKUP = QA / '3(1)_原始备份.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q = lambda name: '{' + W + '}' + name
NS = {'w': W}

# Each source paragraph supplies its original paragraph-format baseline.
CONTENT = [
    (0, '3.4 实验方案'),
    (1, '3.4.1 实验目标'),
    (2, '围绕南疆规模化棉田膜下滴灌的支管巡检需求，在A、B双支路清水台架上开展等效泄漏、局部过流受限及正常扰动对照试验。重点考察压力—流量联合判断对小幅持续异常的识别能力，以及供压调整、邻支路启闭对识别结果的影响；在此基础上，比较事件触发采集与周期上报策略，完成监测节点、LoRa接收端和本地巡检平台的联调。试验以独立参考测量和故障操作记录核验结果，形成支管级异常提示与人工复测的验证依据。'),
    (3, '3.4.2 实验步骤'),
    (4, '（1）台架装配与测量接入。按前述水路与测点布置方案搭建共用水源的A、B双支路台架。A支路依次设置上游取压口P0、可调受限元件R、下游取压口P1和流量计，流量计下游分为正常出流与泄漏旁路；B支路设置切换阀和可调负载，用于模拟邻支路启闭及负载变化。两取压口保持同高，装配后完成固定、排气和密封检查，水路与采集电路之间设置防溅隔离。'),
    (5, '（2）电路检查与参考标定。核对24V压力回路、150Ω取样电阻、ADS1115及3.3V逻辑接口的接线和输入范围，随后开展测量标定。压力选取不少于5个工作点进行升、降压标定，每点重复读取不少于3次，并在相同压力下比较两通道读数；流量采用容积法或称重计时法，在不少于5个工作点校核脉冲系数。保存参考仪器信息、原始读数和标定残差，建立健康状态下的压力—流量关系与区段等效阻力参照。'),
    (6, '（3）故障与正常扰动对照。在80、120、160kPa三档供压及B支路开启、关闭两种状态下，分别设置5%、10%、15%三档等效泄漏和受限。泄漏程度按独立计量的旁路泄漏量占同工况健康总流量的比例设置；受限程度按同工况下A支路总流量相对健康值的下降幅度设置。泄漏水由独立容器分次收集，按收集量与持续时间计量。每种组合至少进行3次独立操作，主要故障试验不少于108次；另设供压调整、B支路启闭和末端负载变化等正常对照，记录操作时刻、阀态和参考测量。'),
    (7, '（4）判据与切换过程检验。以每1s读取压力、连续累计流量脉冲作为固定采集基线，按10s不重叠数据块更新判据。采用不同批次数据建立健康参照、选择门限和验证效果，比较固定门限、基于健康数据波动设置的稳健门限及块级CUSUM方法。在轮灌切换和供压调整期间同步注入部分故障，记录判断暂停时长、故障检出情况及恢复判断后的识别时延，评价工况复判对误报和漏检的影响。'),
    (8, '（5）事件触发采集对照。以固定1s采集为基准，比较不同巡航间隔下的事件触发策略。流量脉冲保持连续计数，压力或流量出现持续变化后切换为1s采集，取得完整有效的10s数据块后复核异常。各策略在相同工况和观察时长下运行，统计压力读取次数、异常检出率、误报率和识别时延，同时记录稀疏采集及切换期间的数据可用情况，据此确定巡航间隔、触发门限与保持时长。'),
    (9, '（6）无线传输与连续运行。设置稳定接收、遮挡衰减和受控阻断三类链路条件，比较快周期、慢周期、原始事件和限频事件四种上报策略，每种组合至少完成3个独立批次，共不少于36次。各策略采用相同送达时限，统计事件唯一落库比例、期限内送达比例、确认往返时延及重传次数，并检查链路恢复后的缓存补发。完成不少于8小时正常连续运行和不少于3次重启测试，核对数据缺失、缓存恢复与数据库记录；同步测量节点电流，比较各策略的通信开销与用电情况。'),
    (10, '（7）系统联调与维护复测。选取典型故障，贯通采集、判断、LoRa传输、存储、平台提示和人工复测，检查支管编号、测点区段及原始记录的对应关系。平台分别记录接收确认、人工查看、处置和复测状态，异常消除并经复测确认后关闭事件。验证数据按独立批次或日期留出，故障与策略对照安排在2027年5—8月完成，形成可追溯的原始记录和试验数据集。'),
    (11, '3.4.3 预期结果与分析方法'),
    (12, '预期形成双支路台架的标定结果、健康参照模型及故障与正常扰动数据集，给出5%—15%等效变化下的识别表现。其中，10%和15%故障组以异常候选检出率不低于90%为目标，正常连续运行以误报频次不高于1次/小时为目标；5%组用于考察小幅异常的辨识能力。健康试次误报率按出现异常候选的试次数占健康验证试次数的比例统计，识别时延按故障注入至首次对应候选形成的时间统计，并分别列出漏检和判断不可用的情况。'),
    (13, '结果分析围绕方法比较、扰动影响和采集通信开销展开。采用相同验证批次比较各类判据，以压力、流量、区段阻力和累积统计量曲线展示异常发展及候选形成过程；按供压、故障程度和B支路状态汇总检出、误报与时延，并报告试次数和统计区间。对事件触发策略，重点比较读取次数减少所带来的识别时延变化；对上报策略，结合送达比例、时延和实测电流评价通信效果。'),
    (14, '前期合成试验用于筛选判据、分析噪声影响和安排试验参数，台架阶段通过独立标定与留出批次验证其实际表现。最终形成适用工况、可辨识程度及误差来源的分析结论，提出节点参数与人工复测流程的调整建议，为后续棉田试用和论文研究提供依据。'),
    (17, '3.5 要解决的主要问题'),
    (18, '（1）小幅变化的测量与辨识。两路压力测量的一致性和小流量计数分辨力直接影响异常识别。按SEN0549标称540脉冲/L计算，0.3L/min流量在10s内约产生27个脉冲，单脉冲对应约3.7%的相对变化。试验通过双压力通道同压对照、流量独立计量和健康参照标定评估测量误差；以10s数据块为基线，补充30s、60s不重叠块对照，分析分辨力改善与识别时延之间的关系，确定适合5%—15%等效变化识别的工作范围与窗口长度。'),
    (19, '（2）正常调节与支管异常的区分。供压调整、B支路启闭及末端负载变化均会改变A支路的压力和流量。项目利用压力—流量健康参照补偿供压变化，结合区段等效阻力、块级CUSUM和切换后的工况复判，识别持续偏离。试验将上述正常调节与泄漏、受限进行配对比较，评价阀态信息和不同测量通道的作用。平台提示到支管及测点区段，异常原因结合操作记录与人工复测确定。'),
    (20, '（3）健康参照与门限的适配。健康参照需要覆盖不同供压和负载状态，门限设置还应兼顾小幅异常检出与正常波动抑制。项目采用独立健康批次拟合参照关系、估计残差波动，再用留出批次比较固定门限、稳健门限和块级CUSUM的表现。通过分别去除工况信息或单路压力的对照，分析各部分的贡献；结合维护前后配对复测，考察参照随时间的变化，形成参数更新与重新标定的依据。'),
    (22, '（4）事件触发采集的及时性。降低压力读取频率可以减少采集次数，但也会推迟异常触发。项目以连续脉冲计数保留流量变化信息，将低频巡航与触发后1s采集相结合，重点检验缓慢变化、突发变化及轮灌切换三类过程。通过同工况对照确定巡航间隔、触发门限和保持时长，使策略选择同时反映读取次数、漏检、误报与识别时延，形成与节点判断相配套的采集方案。'),
    (23, '（5）异常信息的可靠送达与复测衔接。LoRa链路中断、重复上报及节点重启可能造成事件延迟或记录重复。项目采用事件身份、缓存重传、落库后确认和去重机制，保持节点与平台记录的一致性，并通过真实无线、重启和连续运行试验检验效果。平台将异常提示与查看、处置、复测记录关联，使接收确认和维护完成各有明确状态；结合节点电流测量，评价不同上报策略的通信开销。'),
    (24, '目前已形成双支路台架概念设计、集中参数水力模型、采集接口方案和本地巡检平台原型，并积累了合成试验与主机回放记录。后续按器件接入、独立标定、台架对照和系统联调逐步实施，最终形成监测原型、试验数据集及支管巡检方法的验证结果。'),
]

with ZipFile(SOURCE) as z:
    parts = {name: z.read(name) for name in z.namelist()}
root = E.fromstring(parts['word/document.xml'])
body = root.find(q('body'))
original = body.findall(q('p'))
assert len(original) == 25
original_text = [''.join(p.xpath('.//w:t/text()', namespaces=NS)) for p in original]
assert original_text[0] == '3.4. 实验方案'
assert original_text[17] == '3.5. 要解决的主要问题'
assert not root.findall('.//w:drawing', NS)
if not BACKUP.exists():
    shutil.copyfile(SOURCE, BACKUP)

def setval(parent, key, value):
    node = parent.find(q(key))
    if node is None:
        node = E.SubElement(parent, q(key))
    node.set(q('val'), str(value))
    return node

headings = {0, 1, 3, 11, 17}
changes = []
for p in original:
    body.remove(p)

for source_index, text in CONTENT:
    p = E.Element(q('p'))
    old_pr = original[source_index].find(q('pPr'))
    pr = deepcopy(old_pr) if old_pr is not None else E.Element(q('pPr'))
    p.append(pr)
    # Preserve page geometry and source font size, while making hierarchy consistent.
    for name in ['rPr', 'outlineLvl', 'numPr']:
        for elem in list(pr.findall(q(name))):
            pr.remove(elem)
    title = source_index in headings
    setval(pr, 'jc', 'left' if title else 'both')
    setval(pr, 'keepNext', '1' if title else '0')
    setval(pr, 'keepLines', '1' if title else '0')
    setval(pr, 'widowControl', '1')
    setval(pr, 'snapToGrid', '0')
    setval(pr, 'autoSpaceDE', '0')
    setval(pr, 'autoSpaceDN', '0')
    sp = pr.find(q('spacing'))
    if sp is None:
        sp = E.SubElement(pr, q('spacing'))
    sp.set(q('before'), '100' if source_index in {0, 17} else '0')
    sp.set(q('after'), '80')
    sp.set(q('line'), '312')
    sp.set(q('lineRule'), 'auto')
    ind = pr.find(q('ind'))
    if ind is None:
        ind = E.SubElement(pr, q('ind'))
    for key in list(ind.attrib):
        del ind.attrib[key]
    ind.set(q('firstLine'), '0' if title else '420')
    if title:
        setval(pr, 'outlineLvl', '1' if source_index in {0, 17} else '2')
    groups = []
    for c in text:
        font = ('Times New Roman' if (c.isascii() and (c.isalnum() or c.isspace())) else '宋体')
        if groups and groups[-1][0] == font:
            groups[-1][1] += c
        else:
            groups.append([font, c])
    for font, s in groups:
        run = E.SubElement(p, q('r'))
        rp = E.SubElement(run, q('rPr'))
        f = E.SubElement(rp, q('rFonts'))
        for k in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
            f.set(q(k), font)
        setval(rp, 'sz', '21')
        setval(rp, 'szCs', '21')
        setval(rp, 'b', '1' if title else '0')
        setval(rp, 'snapToGrid', '0')
        setval(rp, 'spacing', '0')
        t = E.SubElement(run, q('t'))
        t.text = s
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    body.insert(len(body) - 1, p)
    changes.append({'source_paragraph': source_index, 'before': original_text[source_index], 'after': text})

new_text = '\n'.join(t for _, t in CONTENT)
assert '10秒滚动' not in new_text
assert 'De25' not in new_text
assert '已验证' not in new_text
assert '1/12' not in new_text and '20/20' not in new_text
assert 2 * 3 * 3 * 2 * 3 == 108
for run in root.findall('.//w:r', NS):
    text = ''.join(run.xpath('./w:t/text()', namespaces=NS))
    if any(unicodedata.category(c).startswith('P') for c in text):
        fonts = run.find('./w:rPr/w:rFonts', NS)
        assert fonts.get(q('ascii')) == '宋体'

with ZipFile(OUTPUT, 'w') as z:
    for name, data in parts.items():
        z.writestr(name, E.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
                   if name == 'word/document.xml' else data)
with ZipFile(OUTPUT) as z:
    assert all(z.read(name) == data for name, data in parts.items() if name != 'word/document.xml')

receipt = {
    'source': str(SOURCE), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'candidate': str(OUTPUT), 'source_paragraphs': len(original), 'revised_paragraphs': len(CONTENT),
    'source_characters': sum(map(len, original_text)), 'revised_characters': sum(len(t) for _, t in CONTENT),
    'other_package_parts_unchanged': True,
    'basis': 'Current v4 sections 3.3.3 and 3.3.4, local block-CUSUM code and project scope records',
    'checks': ['fixed 1 s / 10 s non-overlapping baseline', '30 s / 60 s blocks only comparison',
               'leak and restriction degrees separately defined', '108 independent fault operations',
               '36 wireless strategy trials', 'no old synthetic counts presented as physical results',
               '90 percent and 1 per hour explicitly targets', 'no new common-reference sensor requirement',
               'archive records kept distinct from event closure', 'Song punctuation'],
    'changes': changes, 'render_review': 'pending',
}
(QA / 'revision_checks.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / '修订正文.txt').write_text(new_text, encoding='utf-8')
print(json.dumps({k: receipt[k] for k in ['source_paragraphs', 'revised_paragraphs', 'source_characters', 'revised_characters', 'candidate']}, ensure_ascii=False))
