"""Two data-derived integration figures; grayscale and collision checks."""
from pathlib import Path
import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulation'))
import review_integrated_monitor as m

DATA = m.OUT
OUT = ROOT / 'deliverables/端到端软件联调图'
plt.rcParams.update({'font.sans-serif': ['Microsoft YaHei'], 'axes.unicode_minus': False,
                     'font.size': 12, 'axes.labelsize': 12, 'axes.titlesize': 14,
                     'xtick.labelsize': 12, 'ytick.labelsize': 12, 'legend.fontsize': 11,
                     'svg.fonttype': 'none', 'svg.hashsalt': 'integrated-monitor-20261006',
                     'axes.spines.top': False, 'axes.spines.right': False})
CHECKS = []


def save(fig, name, question):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    spans = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():
            continue
        box = text.get_window_extent(renderer)
        assert box.x0 >= 0 and box.y0 >= 0 and box.x1 <= width and box.y1 <= height, (name, text.get_text())
        assert text.get_fontsize() >= 11
        spans.append(dict(text=text.get_text(), box=list(box.bounds), font_pt=text.get_fontsize()))
    for i, a in enumerate(spans):
        x, y, w, h = a['box']
        for b in spans[i+1:]:
            xx, yy, ww, hh = b['box']
            assert min(x+w, xx+ww)-max(x, xx) <= 1 or min(y+h, yy+hh)-max(y, yy) <= 1, (name, a['text'], b['text'])
    for ext in ['png', 'svg']:
        path = OUT / f'{name}.{ext}'
        fig.savefig(path, dpi=180, facecolor='white', metadata={'Date': None} if ext == 'svg' else None)
        if ext == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n', encoding='utf-8', newline='\n')
    CHECKS.append(dict(name=name, question=question, text_within_canvas=True, text_collision_check=True,
                       minimum_font_pt=min(v['font_pt'] for v in spans), texts=spans,
                       file_sha256={ext: m.sha(OUT / f'{name}.{ext}') for ext in ['png', 'svg']}))
    plt.close(fig)


def delivery(example):
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.2))
    fig.subplots_adjust(left=.18, right=.96, top=.85, bottom=.10, hspace=.60)
    handles = [Line2D([], [], color='black', marker='o', linestyle='None', label='本地生成'),
               Line2D([], [], color='black', marker='s', markerfacecolor='white', linestyle='None', label='首次入库'),
               Patch(facecolor='.9', label='链路中断')]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.55, .98), ncol=3, frameon=False)
    events = {v['event']['event_id']: v for v in example['received']}
    for y, kind in [(1, 'rapid_review'), (0, 'leak_pattern')]:
        e = next(v for v in example['generated'] if v['kind'] == kind)
        arrival = events[e['event_id']]['received']
        t = e['t_s']
        axes[0].annotate('', xy=(arrival, y), xytext=(t, y), arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
        axes[0].plot(t, y, 'ko', ms=7)
        axes[0].plot(arrival, y, 'ks', mfc='white', ms=7)
        axes[0].text((t+arrival)/2, y+.16, f'{arrival-t} s', ha='center', va='bottom')
    axes[0].set(yticks=[0, 1], yticklabels=['十秒主诊断', '三秒复核提示'], ylim=(-.45, 1.55),
                title='本地事件与首次入库', xlabel='统一模拟时钟 / s')
    view = [r for r in example['remote_views'] if 350 <= r['t_s'] <= 430]
    axes[1].step([v['t_s'] for v in view], [v['sample_age_s'] for v in view], where='post', color='black', lw=1.6)
    axes[1].axhline(65, color='black', linestyle='--', lw=1)
    axes[1].set(title='远端测量数据年龄', ylabel='最新测量年龄 / s', xlabel='统一模拟时钟 / s', ylim=(0, 110))
    axes[1].text(424, 68, '65秒阈值', ha='right', va='bottom')
    for ax in axes:
        ax.axvspan(350, 410, color='.9', zorder=-1)
        ax.set_xlim(348, 432)
        ax.set_xticks([350, 370, 390, 410, 430])
        ax.grid(axis='x', alpha=.15)
    save(fig, '01_事件送达与数据过期', '事件会否乱序送达，旧包补传会否伪装成实时数据？')


def quality(example):
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.2))
    fig.subplots_adjust(left=.18, right=.96, top=.84, bottom=.10, hspace=.58)
    records = [r for r in example['records'] if 350 <= r['t_s'] <= 390]
    t = np.array([r['t_s'] for r in records])
    p0 = [r['pressure_kpa'][0] for r in records]
    p1 = [np.nan if r['pressure_kpa'][1] is None else r['pressure_kpa'][1] for r in records]
    axes[0].plot(t, p0, color='black', lw=1.4, label='P0')
    axes[0].plot(t, p1, color='black', linestyle='--', lw=1.4, marker='o', ms=3, label='P1')
    axes[0].set(ylabel='压力 / kPa', title='逐秒压力记录')
    handles, labels = axes[0].get_legend_handles_labels()
    handles.append(Patch(facecolor='.9', label='P1缺失'))
    axes[0].legend(handles=handles, loc='upper left', bbox_to_anchor=(0, 1.36), ncol=3, frameon=False)
    for y, key, label in [(2, 'pressure_quality', '测量无效'), (1, 'window_incomplete', '窗口不足'), (0, 'valid', '数值可用')]:
        points = [r['t_s'] for r in records if r['measurement_status'] == key]
        axes[1].plot(points, [y]*len(points), color='black', linestyle='None', marker='s', ms=5)
    axes[1].set(yticks=[0, 1, 2], yticklabels=['数值可用', '窗口不足', '测量无效'], ylim=(-.5, 2.5),
                xlabel='统一模拟时钟 / s', title='测量质量与诊断窗口状态')
    for ax in axes:
        ax.axvspan(359.5, 364.5, color='.9', zorder=-1)
        ax.set_xlim(349, 391)
        ax.set_xticks([350, 360, 365, 374, 390])
        ax.grid(axis='x', alpha=.15)
    save(fig, '02_质量状态与窗口恢复', '传感读数恢复之后，何时才能恢复完整诊断窗口？')


if __name__ == '__main__':
    gate = json.loads((DATA / 'transport_acceptance.json').read_text(encoding='utf-8'))
    assert gate['passed'] and gate['parameters_sha256'] == m.sha(DATA / 'frozen_parameters.json')
    examples = json.loads((DATA / 'examples.json').read_text(encoding='utf-8'))
    assert gate['examples_sha256'] == m.sha(DATA / 'examples.json')
    OUT.mkdir(exist_ok=True)
    delivery(examples['pulse8:outage'])
    quality(examples['nan_pressure:clean'])
    m.dump('figure_checks.json', dict(figures=CHECKS, sources={name: m.sha(DATA / name) for name in
                                                            ['examples.json', 'transport_acceptance.json']},
                                     scope='Standalone figures; Word page layout not checked'))
    print('Two integration figures passed bounds, font and text-collision checks.')
