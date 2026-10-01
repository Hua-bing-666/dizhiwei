"""Illustrative hydraulic model for proposal figures; NOT field measurements.

Run: python simulation/run_simulation.py
Requires numpy and matplotlib. Assumptions are documented in simulation/README.md.
"""
from pathlib import Path
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'simulation' / 'results'
FIG = ROOT / 'application' / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
COLORS = ['#156078', '#dc7038', '#468a63', '#7654a3']


def equilibrium(b_open, fault):
    # kPa and L/min. Equivalent quadratic resistances; not emitter-level CFD.
    c_a = .35 + (.18 if fault == 'leak' else 0.)
    r_a = .8 + (8. if fault == 'restriction' else 0.)
    g_a = c_a / np.sqrt(1 + r_a * c_a**2)
    g_b = .35 / np.sqrt(1 + .8 * .35**2) if b_open else 0.
    p = 120 / (1 + .4 * (g_a + g_b)**2)
    q_a = g_a * np.sqrt(p)
    # Sensor A: after added restriction, before equivalent emitter load.
    p_sensor = p - (8. * q_a**2 if fault == 'restriction' else 0.)
    return p, p_sensor, q_a


def simulate(kind):
    rng = np.random.default_rng(20261002)  # common noise realization for illustration
    t = np.arange(601)
    b = (t >= 180) & (t < 300)
    start, end = (190, 280) if kind == 'overlap' else (360, 500)
    fault = (t >= start) & (t < end) if kind != 'normal' else np.zeros(len(t), bool)
    p = np.zeros(len(t)); q = np.zeros(len(t))
    ep = np.zeros(len(t)); eq = np.zeros(len(t))
    p[0], q[0] = equilibrium(False, '')[1:]
    ep[0], eq[0] = p[0], q[0]
    for i in range(1, len(t)):
        f = ('restriction' if kind == 'restriction' else 'leak') if fault[i] else ''
        _, ps, qs = equilibrium(bool(b[i]), f)
        _, ps0, qs0 = equilibrium(bool(b[i]), '')
        # First-order illustrative dynamics. Reference deliberately has different tau.
        p[i] = p[i-1] + (ps-p[i-1])*(1-np.exp(-1/6))
        q[i] = q[i-1] + (qs-q[i-1])*(1-np.exp(-1/6))
        ep[i] = ep[i-1] + (ps0-ep[i-1])*(1-np.exp(-1/9))
        eq[i] = eq[i-1] + (qs0-eq[i-1])*(1-np.exp(-1/9))
    p += rng.normal(0, .6, len(t))
    q += rng.normal(0, .02, len(t))
    raw = (abs(p-ep) > 6) | (abs(q-eq) > .15)
    alarm = np.zeros(len(t), bool)
    run = 0
    for i, a in enumerate(raw):
        run = run+1 if a else 0
        alarm[i] = run >= 3
    changes = np.r_[False, alarm[1:] != alarm[:-1]]
    periodic = t % 10 == 0
    priority = periodic | changes
    event = np.zeros(len(t), bool)
    last = 0
    for i in range(len(t)):
        if i == 0 or changes[i] or i-last >= 60 or abs(p[i]-p[last]) >= 2 or abs(q[i]-q[last]) >= .1:
            event[i] = True; last = i
    data = dict(t=t, pressure=p, flow=q, expected_pressure=ep,
                expected_flow=eq, valve=b, fault=fault, alarm=alarm,
                periodic=periodic, priority=priority, event=event)
    assert np.all(np.isfinite(p)) and np.all(np.isfinite(q))
    assert np.min(p) > 0 and np.min(q) > 0
    assert np.all(priority >= periodic) and np.all(event[changes])
    packet_indices = np.flatnonzero(event)
    assert max(np.diff(packet_indices), default=0) <= 60
    return {k: np.round(v, 4).tolist() if v.dtype.kind == 'f' else v.astype(int).tolist() for k,v in data.items()}


NAMES = {'normal':'正常轮灌', 'leak':'稳定期等效泄漏',
         'restriction':'稳定期节流', 'overlap':'轮灌切换期间等效泄漏'}
bundle = {k: dict(name=name, **simulate(k)) for k,name in NAMES.items()}
stats = {}
for key,d in bundle.items():
    with (OUT / f'{key}.csv').open('w', newline='', encoding='utf-8-sig') as f:
        cols = [k for k in d if k != 'name']
        w = csv.writer(f); w.writerow(cols); w.writerows(zip(*(d[k] for k in cols)))
    stats[key] = {'name':d['name'], 'periodic_packets':sum(d['periodic']),
                  'periodic_priority_packets':sum(d['priority']), 'event_packets':sum(d['event'])}
    fig, axes = plt.subplots(3,1,figsize=(11,7.7),sharex=True,gridspec_kw={'height_ratios':[2,2,1]})
    fig.suptitle(d['name']+'｜简化模型仿真 · 非实测数据', fontsize=15)
    for ax,field,expected,label in zip(axes[:2], ['pressure','flow'], ['expected_pressure','expected_flow'], ['A支路压力 / kPa','A支路流量 / (L/min)']):
        ax.plot(d['t'], d[field],color=COLORS[0],lw=1.5,label='模拟传感器读数')
        ax.plot(d['t'], d[expected],color=COLORS[2],lw=1.3,ls='--',label='已知阀态的健康参考（假设）')
        for a,z in [(180,300)]: ax.axvspan(a,z,color='#e8bc48',alpha=.13)
        fi=np.flatnonzero(d['fault'])
        if len(fi): ax.axvspan(fi[0],fi[-1],color='#dc7038',alpha=.14)
        ax.set_ylabel(label); ax.grid(alpha=.2); ax.legend(loc='best',fontsize=9)
    axes[2].step(d['t'],d['valve'],label='B支路开启',color=COLORS[2])
    axes[2].step(d['t'],np.array(d['alarm'])*.8,label='示意告警（为便于阅读移至0.8）',color=COLORS[1])
    axes[2].scatter(np.array(d['t'])[np.array(d['event'],bool)],np.full(sum(d['event']),-.2),s=9,label='事件上报')
    axes[2].set_yticks([0,1]);axes[2].set_ylabel('状态 / 0或1');axes[2].set_xlabel('时间 / s')
    axes[2].legend(loc='upper right',fontsize=9,ncol=3);axes[2].grid(alpha=.2)
    fig.text(.07,.012,'黄色：B支路正常开启；橙色：人为设定异常。参数未标定；未计入无线丢包、整机能耗和真实滴头堵塞。',fontsize=9)
    fig.tight_layout(rect=[0,.025,1,.965])
    for ext in ['png','svg']:fig.savefig(FIG/f'{key}.{ext}',dpi=180)
    plt.close(fig)

(OUT/'scenarios.json').write_text(json.dumps(bundle,ensure_ascii=False),encoding='utf-8')
(OUT/'packet_counts.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
template=(ROOT/'simulation'/'viewer.template.html').read_text(encoding='utf-8')
(ROOT/'application'/'仿真演示.html').write_text(template.replace('__SCENARIOS__',json.dumps(bundle,ensure_ascii=False)),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2))
print('Generated four scenarios, figures and offline HTML. Physical checks passed.')
