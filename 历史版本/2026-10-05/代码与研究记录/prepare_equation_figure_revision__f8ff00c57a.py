"""Simplify design annotations without modifying measurements or synthetic series."""
from pathlib import Path
from lxml import etree as E
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures/equation_revision'
OUT.mkdir(parents=True, exist_ok=True)
REPLACEMENTS = {
    'system_responsibilities': {
        '系统任务结构：感知、交付、维护与独立评价': '支管巡检系统组成与数据流',
        '拟实施系统；一个感知节点、一个接收模块及现有PC，不代表已实物联调。': '系统方案：感知节点、LoRa接收端与本地巡检平台。',
        '无线模块只桥接字节；数据库事务在PC服务完成，真实接入尚待验证。': '无线模块负责字节传输；PC服务负责事务存储与接收确认。'
    },
    'water_layout': {'工作点待核': '稳压调节'},
    'collection_overview': {
        '候选结构用于预实验和重复验证；设备包络暂定，尚未制造。': '参数化概念模型，展示测点、管路与独立计量布局。'
    },
    'measurement_interfaces': {
        '候选功能原理；压力采用两路4—20mA，流量脉冲转换为3.3V。': '功能接口设计：双路压力采集与脉冲流量计数。',
        '具体定值待验证': '量程匹配与滤波',
        'ADS1115': '模数转换', 'PGA ±4.096V': '双路模拟输入',
        'PB7/SDA': 'I²C SDA', 'PB6/SCL': 'I²C SCL',
        'SEN0549': '脉冲流量计', 'SN74LVC1G17': '电平转换',
        '输入允许至5.5V': '5V → 3.3V', 'TIM2_CH1': '硬件计数器', 'PA0计数': '脉冲计数',
        '台架共地；24V不进ADC。保护、掉电注入、实际引脚与标定尚待验证。': '台架共地；压力回路与主控信号接口分级调理。',
        '候选功能图，非可投板原理图或接线完成证明。': '功能接口方案，用于采集电平与信号路径论证。'
    },
    'diagnosis_proposal': {
        '候选诊断处理流程与输出边界': '支管异常诊断流程设计',
        '拟实施处理流程；当前仿真仅含固定阈值与持续判据，切换门控未实现。': '拟研究流程：质量检查、工况匹配、联合特征与持续确认。',
        'K=Q/√P1；R̂=(P0−P1)/Q²': '负载特征 / 区段阻力估计',
        '未知正常负载仍可与泄漏同形；模式提示必须经独立核查。': '异常模式用于提示巡检，故障原因由独立核查确认。',
        '操作状态、时序对齐和误差区间门控须在真实采集后实现与验证。': '健康参照、操作状态与测量误差共同约束分类。'
    },
    'durable_event_sequence': {
        '主机参考协议已执行字节/事务检查；图示为拟接入真实LoRa的职责关系。': '通信方案设计：本地日志、接收事务与确认重传。',
        '8次/300秒候选上限；超限保留未确认记录，不承诺必然送达。': '有限重试后保留未确认事件；链路恢复后继续核对。'
    },
    'noise_outcomes_print': {
        '种子统计：如实保留失败与方法差异': '压力噪声对早期识别的影响',
        '柱为有效早期次数/20；误差线为噪声模型内的Wilson95%区间。': '柱为有效早期次数/20；误差线为模型内Wilson95%区间。'
    },
    'failure_counterexamples': {
        '失败反例：变化模式不能直接等同故障原因': '诊断边界：负载歧义与压力漂移',
        '两例均为seed=10300、σ=0.3kPa；对应原始三通道和同一因果滤波。': '合成模型：seed=10300，σ=0.3kPa；三通道采用同一因果滤波。',
        '未知正常负载与泄漏可产生完全相同观测；入口压力漂移也会触发受限模式。': '负载变化与泄漏可产生同形观测，需结合操作状态核查。',
        '需保留待核查输出，先标定与记录操作；不能靠换一个算法保证辨因。': '压力漂移会改变阻力估计；标定误差须纳入诊断评价。'
    }
}
records = []
for name, changes in REPLACEMENTS.items():
    source = ROOT / 'application/figures/quality_review' / (name + '.svg')
    data = source.read_bytes()
    root = E.fromstring(data)
    seen = set()
    for el in root.findall('.//{http://www.w3.org/2000/svg}text'):
        if el.text in changes:
            seen.add(el.text)
            el.text = changes[el.text]
    assert seen == set(changes), (name, set(changes) - seen)
    # Only text nodes are changed: geometry, marker placement, paths and series remain identical.
    before = E.fromstring(data)
    for tree in (root, before):
        for el in tree.findall('.//{http://www.w3.org/2000/svg}text'):
            el.text = ''
    assert E.tostring(root) == E.tostring(before), name
    root = E.fromstring(data)
    for el in root.findall('.//{http://www.w3.org/2000/svg}text'):
        if el.text in changes:
            el.text = changes[el.text]
    path = OUT / (name + '.svg')
    path.write_bytes(E.tostring(root, encoding='utf-8'))
    records.append({'name': name, 'source': source.relative_to(ROOT).as_posix(),
                    'source_sha256': hashlib.sha256(data).hexdigest(),
                    'svg': path.relative_to(ROOT).as_posix(),
                    'changed_labels': changes, 'geometry_and_data_unchanged': True})

target = ROOT / 'simulation/equation_figure_review'
target.mkdir(parents=True, exist_ok=True)
(target / 'figure_sources.json').write_text(json.dumps({'date': '2026-10-05', 'figures': records,
    'physical_validation': False}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print('Prepared eight figures with clearer design annotations; geometry and data unchanged.')
