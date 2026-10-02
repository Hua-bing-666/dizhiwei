"""Two-pressure diagnostic hypothesis. Uncalibrated synthetic evidence only.

P0 at branch inlet, P1 after the branch restriction, Q before downstream
load/leak. Square-law resistance and non-compensating load assumed.
This new model is distinct from the older one-pressure communication replay.
"""
from pathlib import Path
import json, csv, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'simulation/diagnosis_results'
FIG = ROOT/'application/figures'
plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False

def hydraulic(ps=120., rc=.4, c=.35, r=.8, b=True):
    ga=c/math.sqrt(1+r*c*c)
    gb=.35/math.sqrt(1+.8*.35**2) if b else 0.
    p0=ps/(1+rc*(ga+gb)**2)
    p1=p0/(1+r*c*c)
    q=c*math.sqrt(p1)
    return np.array([p0,p1,q])

def run(kind, noise, seed):
    rng=np.random.default_rng(seed)
    t=np.arange(601); b=(t>=180)&(t<300)
    ramp=np.clip((t-360)/180,0,1)
    leak=.09*ramp if kind in ('leak','load_unknown') else np.zeros(601)
    resistance=4*ramp if kind=='restriction' else np.zeros(601)
    supply=120-30*ramp if kind=='supply' else np.full(601,120.)
    truth=np.array([hydraulic(float(supply[j]),c=.35+leak[j],r=.8+resistance[j],b=bool(b[j])) for j in t])
    healthy=np.array([hydraulic(float(supply[j]),b=bool(b[j])) for j in t])
    severity=np.abs(truth[:,2]-healthy[:,2])/healthy[:,2]
    observed=truth+rng.normal(0,[noise,noise,.02],truth.shape)
    if kind=='drift':observed[:,0]+=10*ramp
    # Stable rolling means. Outputs invalid for low flow/non-positive pressure.
    avg=np.vstack([observed[max(0,j-9):j+1].mean(axis=0) for j in t])
    valid=(avg[:,1]>10)&(avg[:,2]>.5)
    k=avg[:,2]/np.sqrt(np.maximum(avg[:,1],.001))
    rr=(avg[:,0]-avg[:,1])/np.maximum(avg[:,2]**2,.001)
    # Fixed planned thresholds, not optimized on the evaluated cases.
    # Calibration only uses first 120 healthy seconds of each synthetic trial.
    k0=float(np.median(k[20:120])); r0=float(np.median(rr[20:120]))
    kleak=(k/k0-1)>.06
    rrestrict=(rr-r0)>.6
    states=np.where(kleak & rrestrict,'uncertain',np.where(kleak,'leak_pattern',np.where(rrestrict,'restriction_pattern','normal')))
    states[~valid]='invalid'
    detected=None; fa=0; previous='normal'
    for j in range(130,601):
        s=states[j]
        if s not in ('normal','invalid') and len(set(states[j-4:j+1]))==1:
            if s!=previous:
                if j<360 or kind in ('normal','supply','drift','load_unknown'):fa+=1
                elif detected is None:detected=j
            previous=s
        elif s=='normal':previous='normal'
    critical=np.flatnonzero((t>=360)&(severity>=.15)) if kind in ('leak','restriction') else []
    crit=int(critical[0]) if len(critical) else None
    result=dict(kind=kind,pressure_noise_kpa=noise,seed=seed,false_onsets=fa,
                detected_s=detected,critical_s=crit,
                severity_at_detection=float(severity[detected]) if detected is not None else None,
                early_valid=bool(detected is not None and crit is not None and detected<crit and fa==0
                                 and states[detected]==('leak_pattern' if kind=='leak' else 'restriction_pattern')),
                lead_s=crit-detected if detected is not None and crit is not None else None,
                first_pattern=str(states[detected]) if detected is not None else None)
    trace=dict(t=t.tolist(),p0=truth[:,0].tolist(),p1=truth[:,1].tolist(),q=truth[:,2].tolist(),
               severity=severity.tolist(),k=k.tolist(),r=rr.tolist(),state=states.tolist(),**result)
    return result,trace

def main():
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    rows=[];traces={}
    for noise in [.3,1.,3.,10.]:
        for kind in ['normal','supply','leak','restriction','drift','load_unknown']:
            for seed in range(10300,10320):
                row,trace=run(kind,noise,seed);rows.append(row)
                if seed==10300:traces[f'{kind}_{noise}']=trace
    summary=[]
    for noise in [.3,1.,3.,10.]:
        for kind in ['normal','supply','leak','restriction','drift','load_unknown']:
            rr=[r for r in rows if r['kind']==kind and r['pressure_noise_kpa']==noise]
            valid_leads=[r['lead_s'] for r in rr if r['early_valid']]
            summary.append(dict(kind=kind,pressure_noise_kpa=noise,trials=len(rr),
                                detection_trials=sum(r['detected_s'] is not None for r in rr),
                                early_trials=sum(r['early_valid'] for r in rr),
                                mean_false_onsets=float(np.mean([r['false_onsets'] for r in rr])),
                                median_valid_lead_s=float(np.median(valid_leads)) if valid_leads else None))
    data=dict(classification='uncalibrated_synthetic_hypothesis',physical_data=False,
              model='P0-P1=R Q^2; Q=C sqrt(P1)',
              assumptions=['downstream equivalent leakage','single fault','known valve operation',
                           'square-law steady state','independent zero-mean nominal sensor noise',
                           'nominal model excludes sensor transients; entrance-pressure drift and unknown-load challenges included separately'],
              critical_fraction=.15,critical_note='illustrative hydraulic criterion, not agronomic or school standard',
              settings=dict(averaging_seconds=10,k_relative_threshold=.06,r_absolute_threshold=.6,persistence_seconds=5,
                            seeds=list(range(10300,10320)),flow_noise_l_min=.02),summary=summary,traces=traces)
    (OUT/'summary.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    with (OUT/'trials.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    fig,axes=plt.subplots(1,2,figsize=(12,4.4),layout='constrained')
    for kind,label,color in [('leak','下游等效泄漏','#B4512B'),('restriction','支管等效受限','#164C45')]:
        tr=traces[f'{kind}_0.3']; ax=axes[0]
        ax.plot(tr['t'],np.array(tr['severity'])*100,label=label,color=color)
        if tr['detected_s'] is not None:
            ax.scatter([tr['detected_s']],[tr['severity_at_detection']*100],color=color,s=40)
    axes[0].axhline(15,color='#426B91',linestyle='--',label='演示失效判据 15%')
    axes[0].set(xlim=(330,600),xlabel='模型时间 / s',ylabel='相对健康流量偏离 / %',title='渐进故障：早期需参照失效判据')
    axes[0].legend(fontsize=9);axes[0].grid(alpha=.2)
    xx=np.arange(4)
    for kind,label,offset,color in [('leak','等效泄漏',-.17,'#B4512B'),('restriction','等效受限',.17,'#164C45')]:
        ss=[r for r in summary if r['kind']==kind]
        axes[1].bar(xx+offset,[r['early_trials'] for r in ss],width=.32,label=label,color=color)
    axes[1].set(xticks=xx,xticklabels=['0.3','1.0','3.0','10.0'],ylim=(0,23),xlabel='两个压力点各自噪声 σ / kPa',ylabel='无前期误报且正确提前发现 / 20',title='增加测点仍受差压测量噪声制约')
    axes[1].legend(fontsize=9);axes[1].grid(axis='y',alpha=.2)
    fig.suptitle('未标定合成模型 · 480次试验 · 单故障及理想同步假设 · 非实物识别率',fontsize=11)
    for ext in ['png','svg']:fig.savefig(FIG/f'early_diagnosis.{ext}',dpi=160)
    svg=FIG/'early_diagnosis.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)
    print('480 synthetic trials written; summary and failure records in diagnosis_results. No physical validation.')

if __name__=='__main__':main()
