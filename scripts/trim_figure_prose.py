# -*- coding: utf-8 -*-
"""精简图中冗余的解释性文字：保留图例、标签、机制说明，删去重复的免责声明与长篇注释。

原则（2026-10-17 用户要求）：
  - **保留**：图例、坐标轴名、框内标签、数据值、以及把机理/逻辑讲清楚的短注；
  - **删除**：与图注重复的免责声明、方法论长注、来源页脚——这些放正文里说，不占图面。
  - 只改 <text> 内容，不动任何几何、颜色、字号。

做法：对每张图的**所有副本**（application/figures/<来源目录>/ 与 application/figures/quality_review/）
做同一组替换；每一条都先断言旧文本存在，避免悄悄失效。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGDIR = ROOT / 'application' / 'figures'

# 图名 -> [(旧文本, 新文本或 None 表示删除), ...]
TRIMS = {
    'system_responsibilities': [
        ('拟实施系统；一个感知节点、一个接收模块及现有PC，不代表已实物联调。',
         '拟实施系统；不代表已实物联调'),
        ('实线：测量/业务连接；虚线：评价记录。ACK与人工查看、复测归档分开。',
         '实线：测量/业务；虚线：评价记录'),
        ('无线模块只桥接字节；数据库事务在PC服务完成，真实接入尚待验证。', None),
    ],
    'water_layout': [
        ('P0/P1采用侧向测压；Q位于分流前。泄漏先独立计量，再人工回水。',
         'P0/P1 侧向测压；Q 位于分流前'),
    ],
    'collection_overview': [
        ('候选结构用于预实验和重复验证；设备包络暂定，尚未制造。', '候选结构；尚未制造'),
    ],
    'measurement_interfaces': [
        ('候选功能原理；压力采用两路4—20mA，流量脉冲转换为3.3V。',
         '压力两路 4—20 mA；流量脉冲转 3.3 V'),
        ('正常量程0.6—3.0V；20mA耗散0.06W；22mA已达3.3V。', '量程 0.6—3.0 V'),
        ('台架共地；24V不进ADC。保护、掉电注入、实际引脚与标定尚待验证。', '台架共地；24 V 不进 ADC'),
        ('候选功能图，非可投板原理图或接线完成证明。', '功能接口方案，非投板原理图'),
    ],
    'diagnosis_proposal': [
        ('拟实施处理流程；当前仿真仅含固定阈值与持续判据，切换门控未实现。', '拟实施处理流程'),
        ('操作状态、时序对齐和误差区间门控须在真实采集后实现与验证。', None),
    ],
    'durable_event_sequence': [
        ('主机参考协议已执行字节/事务检查；图示为拟接入真实LoRa的职责关系。',
         '拟接入真实 LoRa 的职责关系'),
        ('以下为另一条路径：上面的ACK未到达节点', '另一条路径：ACK 未到达节点'),
        ('ACK表示接收端保存；人工已查看、处置与同工况复测分别记录。', None),
    ],
    'noise_outcomes_print': [
        ('480个噪声试次；每场景、每σ20个种子，同一试次比较两条固定规则。',
         '每场景、每 σ 20 个种子'),
    ],
    'failure_counterexamples': [
        ('两例均为seed=10300、σ=0.3kPa；对应原始三通道和同一因果滤波。',
         'seed=10300，σ=0.3 kPa'),
    ],
    'sampling_window_tradeoff': [
        ('模型最大泄漏与理想计数分析；非容器标定、真实传感器或固件测试。',
         '模型分析；非容器标定或固件测试'),
        ('20,000组恒定流量/脉冲相位检查不包括漏脉冲、抖动或器件误差。',
         '不含漏脉冲、抖动或器件误差'),
    ],
}


def copies(name):
    return sorted(FIGDIR.rglob(name + '.svg'))


def main():
    changed = deleted = 0
    for name, rules in TRIMS.items():
        files = copies(name)
        if not files:
            print('  ! 找不到', name)
            continue
        for path in files:
            text = path.read_text(encoding='utf-8')
            for old, new in rules:
                if old not in text:
                    print('  ! %s：未找到旧文本 %r（%s）' % (name, old[:24], path.name))
                    continue
                if new is None:
                    # 删掉整个 <text ...>...</text> 元素
                    import re
                    pattern = re.compile(r'<text[^>]*>[^<]*' + re.escape(old) + r'[^<]*</text>')
                    text, n = pattern.subn('', text)
                    if n == 0:
                        print('  ! %s：删除失败 %r' % (name, old[:24]))
                        continue
                    deleted += n
                else:
                    text = text.replace(old, new, 1)
                    changed += 1
            path.write_text(text, encoding='utf-8')
        print('  ✓ %-28s %d 处替换，%d 处删除；副本 %d 个'
              % (name, sum(1 for _, n in rules if n), sum(1 for _, n in rules if n is None), len(files)))
    print('\n合计：改写 %d 处、删除 %d 处文字。几何与配色未改动。' % (changed, deleted))


if __name__ == '__main__':
    main()
