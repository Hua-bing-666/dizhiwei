"""Falsification-oriented checks of the illustrative proposal model, not field validation.

Run: python simulation/adversarial_audit.py
Frozen thresholds; noise-only replicates are NOT independent real experiments.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np
import matplotlib.pyplot as plt
from run_simulation import simulate, equilibrium, COLORS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'simulation'/'audit_results'
FIG = ROOT/'application'/'figures'
OUT.mkdir(parents=True,exist_ok=True)
SEEDS = list(range(8100,8120))
METHODS = {'fixed':'固定 P/Q 阈值', 'wait':'固定阈值＋切换等待',
           'normalized':'压力归一化流量', 'candidate':'原示意状态参考'}
CASES = [
    ('normal','正常切换','normal',{}),
    ('ideal','原设定大幅泄漏','leak',{}),
    ('weak','小幅等效泄漏','leak',{'leak_delta':.0035}),
    ('overlap','切换期间泄漏','overlap',{}),
    ('short','切换期短异常 8s','overlap',{'duration':8}),
    ('restriction','测点上游节流','restriction',{}),
    ('source','允许供压改变（假设）','normal',{'source_change':-12}),
    ('missing','正常切换但无阀态','normal',{'valve_unavailable':True}),
    ('late','正常切换阀态迟到 20s','normal',{'valve_delay':20}),
    ('noise','较大噪声下正常切换','normal',{'noise_pressure':3.,'noise_flow':.1}),
    ('drift','传感器慢漂移','normal',{'pressure_drift':-8,'flow_drift':-.2}),
    ('slow','健康动态变慢 30s','normal',{'actual_tau':30}),
]


def persistent(raw):
    out=np.zeros(len(raw),bool);run=0
    for i,a in enumerate(raw):
        run=run+1 if a else 0
        out[i]=run>=3
    return out


def detectors(d, valve_unavailable=False, valve_delay=0):
    p=np.array(d['pressure']);q=np.array(d['flow']);t=np.array(d['t'])
    # Same explicit initial healthy calibration segment for simple baselines.
    p0=np.mean(p[:60]);q0=np.mean(q[:60])
    raw=(abs(p-p0)>6)|(abs(q-q0)>.15)
    known_b=np.array(d['valve'],bool)
    if valve_unavailable: known_b[:]=False
    elif valve_delay: known_b=known_b[np.maximum(0,t-valve_delay)]
    switches=np.flatnonzero(np.r_[False,known_b[1:]!=known_b[:-1]])
    masked=raw.copy()
    for i in switches:masked[i:i+30]=False
    normalized=abs(q-q0*np.sqrt(p/p0))>.15
    return {'fixed':persistent(raw),'wait':persistent(masked),
            'normalized':persistent(normalized),'candidate':np.array(d['alarm'],bool)}


def event_metrics(alarm,truth):
    starts=np.flatnonzero(alarm & ~np.r_[False,alarm[:-1]])
    starts=starts[starts>=60]  # All methods evaluated after the initial healthy calibration.
    truth=np.array(truth,bool)
    fi=np.flatnonzero(truth)
    hit=starts[truth[starts]]
    return {'false_starts':int(sum(~truth[starts])),
            'detected':bool(len(hit)) if len(fi) else None,
            'delay':int(hit[0]-fi[0]) if len(fi) and len(hit) else None,
            'preexisting_alarm':bool(alarm[fi[0]-1]) if len(fi) and fi[0]>0 else False}


rows=[];examples={};summary=[]
for key,name,kind,kwargs in CASES:
    case_rows=[]
    for seed in SEEDS:
        d=simulate(kind,seed=seed,**kwargs)
        alg=detectors(d,kwargs.get('valve_unavailable',False),kwargs.get('valve_delay',0))
        for method,alarm in alg.items():
            met=event_metrics(alarm,d['fault'])
            row=dict(case=key,name=name,seed=seed,method=method,**met,
                     periodic_priority_packets=sum(d['priority']),event_packets=sum(d['event']))
            rows.append(row);case_rows.append(row)
        if seed==SEEDS[0]:examples[key]=dict(name=name,**d,detectors={k:v.astype(int).tolist() for k,v in alg.items()})
    for method in METHODS:
        mr=[r for r in case_rows if r['method']==method]
        delays=[r['delay'] for r in mr if r['delay'] is not None]
        summary.append(dict(case=key,name=name,method=method,n=len(mr),
            hits=sum(r['detected'] is True for r in mr),has_fault=mr[0]['detected'] is not None,
            false_mean=float(np.mean([r['false_starts'] for r in mr])),
            delay_median=float(np.median(delays)) if delays else None,
            preexisting=sum(r['preexisting_alarm'] for r in mr),
            event_mean=float(np.mean([r['event_packets'] for r in mr])),
            priority_mean=float(np.mean([r['periodic_priority_packets'] for r in mr]))))

# Fault amplitude x noise grid: all are uncalibrated model assumptions.
noise=[.02,.05,.1,.15];increments=[.001,.0035,.007,.0175,.035,.07,.18]
grid=[];normal_false=[]
for nf in noise:
    healthy_metrics=[]
    for seed in SEEDS:
        hd=simulate('normal',seed=seed,noise_flow=nf)
        healthy_metrics.append(event_metrics(np.array(hd['alarm'],bool),hd['fault'])['false_starts'])
    normal_false.append(float(np.mean(healthy_metrics)))
    line=[]
    for delta in increments:
        hits=sum(event_metrics(np.array((d:=simulate('leak',seed=s,leak_delta=delta,noise_flow=nf))['alarm'],bool),d['fault'])['detected'] for s in SEEDS)
        line.append(hits)
    grid.append(line)

# Counterexample: normal rotation is not observable in A when its inlet pressure is ideal regulated.
regulated=simulate('normal',common_resistance=0,noise_pressure=0,noise_flow=0)
assert max(regulated['pressure'])-min(regulated['pressure'])<1e-8
assert max(regulated['flow'])-min(regulated['flow'])<1e-8

# Exact same steady Pa,Q can represent two different locations/mechanisms.
# Upstream restriction vs source-pressure reduction: no identifiability claim is possible from Pa,Q alone.
pc,pa,qa=equilibrium(False,'restriction')
ga=.35/np.sqrt(1+.8*.35**2)
source_equivalent=pa*(1+.4*ga**2)
pc2,pa2,qa2=equilibrium(False,'',source_pressure=source_equivalent)
assert np.allclose([pa,qa],[pa2,qa2],rtol=1e-12)
counterexamples=dict(regulated_rotation={'pressure_change':0,'flow_change':0},
    indistinguishable_steady_states={'restriction_pressure':pa,'restriction_flow':qa,
    'equivalent_source_pressure':source_equivalent,'other_pressure':pa2,'other_flow':qa2})

# Packet loss replay: same local detection, no ACK/retry. Initial loss of the alarm transition is forced.
link=[]
for strategy in ['priority','event']:
    d=examples['ideal'];alarm=np.array(d['alarm'],bool);truth=np.array(d['fault'],bool)
    rising=np.flatnonzero(alarm&~np.r_[False,alarm[:-1]])[0]
    for loss in [0,.1,.3]:
        for seed in SEEDS:
            rng=np.random.default_rng(seed+50000)
            received=np.array(d[strategy],bool)&(rng.random(601)>=loss)
            received[rising:rising+15]=False
            held=False;remote=np.zeros(601,bool)
            for i in range(601):
                if received[i]:held=bool(alarm[i])
                remote[i]=held
            met=event_metrics(remote,truth)
            link.append(dict(strategy=strategy,loss=loss,seed=seed,**met))

payload=dict(schema=1,date='2026-10-02',data_class='uncalibrated_synthetic',
    software=dict(python=sys.version.split()[0],numpy=np.__version__),
    seeds=SEEDS,cases=[dict(key=k,name=n,kind=t,parameters=p) for k,n,t,p in CASES],
    methods=METHODS,summary=summary,examples=examples,grid=dict(noise_flow=noise,
    leak_delta=increments,hits=grid,normal_false_mean=normal_false,n=len(SEEDS)),counterexamples=counterexamples,link=link)
(OUT/'audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
with (OUT/'trials.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)

fig,axes=plt.subplots(1,2,figsize=(13,6.5),gridspec_kw={'width_ratios':[1.2,1]})
heat=np.array([[next(r for r in summary if r['case']==k and r['method']==m)['false_mean'] for m in METHODS] for k,_,_,_ in CASES])
im=axes[0].imshow(heat,cmap='YlOrRd',vmin=0,vmax=max(1,heat.max()),aspect='auto')
axes[0].set_xticks(range(4),list(METHODS.values()),rotation=20,ha='right',fontsize=9)
axes[0].set_yticks(range(len(CASES)),[x[1] for x in CASES],fontsize=10)
axes[0].set_title('平均误报告警起点 / 541秒评价窗',fontsize=12)
for i in range(len(CASES)):
    for j in range(4):axes[0].text(j,i,f'{heat[i,j]:.1f}',ha='center',va='center',fontsize=10)
axes[1].imshow(grid,cmap='Blues',vmin=0,vmax=len(SEEDS),aspect='auto')
axes[1].set_xticks(range(len(increments)),[f'{v/.35*100:.1f}%' for v in increments],rotation=30,ha='right')
axes[1].set_yticks(range(len(noise)),[f'{n}\n健康误报 {f:.1f}' for n,f in zip(noise,normal_false)],fontsize=9)
axes[1].set_xlabel('等效出流系数增加比例（不是实际漏水比例）')
axes[1].set_ylabel('流量噪声σ / (L/min)；匹配正常对照误报 / 541s')
axes[1].set_title('原示意判据：出现新告警的试次数 / 20',fontsize=12)
for i in range(len(noise)):
    for j in range(len(increments)):axes[1].text(j,i,f'{grid[i][j]}/20',ha='center',va='center',color='white' if grid[i][j]>12 else 'black',fontsize=9)
fig.suptitle('反例与敏感性检验｜未标定简化模型 · 非实测 · 非真实准确率',fontsize=15)
fig.text(.015,.015,'阈值冻结；每格仅改变随机噪声。噪声大时碰巧告警也计入检出，必须同时看左图误报，不能按命中次数选方法。',fontsize=9)
fig.tight_layout(rect=[0,.035,1,.94]);fig.savefig(FIG/'adversarial_boundaries.png',dpi=180)
svg=FIG/'adversarial_boundaries.svg';fig.savefig(svg,metadata={'Date':None});svg.write_text('\n'.join(x.rstrip() for x in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n');plt.close(fig)

template=(ROOT/'simulation'/'audit.template.html').read_text(encoding='utf-8')
(ROOT/'application'/'对抗性检验.html').write_text(template.replace('__AUDIT__',json.dumps(payload,ensure_ascii=False)),encoding='utf-8',newline='\n')
manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in [ROOT/'simulation/run_simulation.py',Path(__file__),ROOT/'simulation/audit.template.html',
                    OUT/'audit.json',OUT/'trials.csv',FIG/'adversarial_boundaries.png',
                    FIG/'adversarial_boundaries.svg',ROOT/'application/对抗性检验.html']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
for r in summary:
    if r['method']=='candidate':print(f"{r['name']}: hits={r['hits']}/{r['n'] if r['has_fault'] else '-'}; false={r['false_mean']:.2f}; event={r['event_mean']:.1f}; priority={r['priority_mean']:.1f}")
print('Steady-state ambiguity:',json.dumps(counterexamples,ensure_ascii=False))
print('Generated 240 challenge trials, 560 sensitivity trials, 80 matched healthy controls, 960 method evaluations and 120 packet-loss replays; all synthetic.')
