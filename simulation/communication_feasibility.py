"""Matched detection and ACK/retention rules: communication trade-off simulation.

All channel parameters are hypothetical. No LoRa hardware or energy measurements.
"""
from pathlib import Path
import csv,json
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from run_simulation import simulate,COLORS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'simulation'/'communication_results';OUT.mkdir(parents=True,exist_ok=True)
FIG=ROOT/'application'/'figures'
SEEDS=list(range(9200,9220))
POLICIES={'p10':'10秒周期＋可靠告警','p30':'30秒周期＋可靠告警',
          'raw':'原始变化触发＋可靠告警','bounded':'滤波变化触发＋限频＋可靠告警'}
CASES=[('normal','正常轮灌','normal',{}),('leak','明显泄漏','leak',{}),
       ('weak','弱等效泄漏','leak',{'leak_delta':.0035}),
       ('short','切换期8秒异常','overlap',{'duration':8}),
       ('source','允许供压变化（假设）','normal',{'source_change':-12}),
       ('noise','较大噪声','normal',{'noise_pressure':3,'noise_flow':.1}),
       ('drift','测量慢漂移','normal',{'pressure_drift':-8,'flow_drift':-.2}),
       ('missing','阀态缺失','normal',{'valve_unavailable':True})]


def ewma(values):
    out=np.array(values,float).copy()
    for i in range(1,len(out)):out[i]=.2*out[i]+.8*out[i-1]
    return out


def replay(data,policy,loss,seed,*,burst_seconds=15,queue_limit=16):
    # Every policy carries the SAME filtered measurements and fixed local detector result.
    p=np.array(data['pressure']);q=np.array(data['flow']);fp=ewma(p);fq=ewma(q)
    alarm=np.array(data['alarm'],bool)
    transitions=np.flatnonzero(alarm!=np.r_[False,alarm[:-1]])
    starts={i:int(alarm[t]) for i,t in enumerate(transitions)}
    generated={int(t):i for i,t in enumerate(transitions)}
    rng=np.random.default_rng(seed+50000)
    # Indexed by wall time, so all policies face the same exogenous channel realization.
    up_good=rng.random(661)>=loss;ack_good=rng.random(661)>=loss
    fi=np.flatnonzero(data['fault']);burst=int(fi[0]) if len(fi) else 360
    up_good[burst:burst+burst_seconds]=False;ack_good[burst:burst+burst_seconds]=False
    pending=deque();first_received={};acks={};seen=set()
    due=0;attempts=0;last_telemetry=0;last_p=float(p[0]);last_q=float(q[0])
    # No free initial synchronization: errors/AoI are defined after first reception.
    held_p=None;held_q=None;stamp=None
    uplinks=0;downlinks=0;overflow=0;duplicates=0;tx=[];errors=[];ages=[]
    for t in range(661):
        if t in acks and pending and pending[0]==acks[t]:
            pending.popleft();attempts=0;due=t
        if t in generated:
            if len(pending)<queue_limit:pending.append(generated[t])
            else:overflow+=1
            if len(pending)==1:due=t
        j=min(t,600)
        if policy=='p10':regular=t%10==0
        elif policy=='p30':regular=t%30==0
        elif policy=='raw':regular=t==0 or t-last_telemetry>=60 or abs(p[j]-last_p)>=2 or abs(q[j]-last_q)>=.1
        else:regular=t==0 or t-last_telemetry>=60 or (t-last_telemetry>=5 and (abs(fp[j]-last_p)>=3 or abs(fq[j]-last_q)>=.12))
        urgent=bool(pending) and t>=due
        if regular or urgent:
            uplinks+=1;tx.append(t)
            event=pending[0] if pending else None
            if event is not None:
                attempts+=1;due=t+(4 if attempts<4 else 10)
            if regular:
                last_telemetry=t
                last_p=float(fp[j] if policy=='bounded' else p[j])
                last_q=float(fq[j] if policy=='bounded' else q[j])
            if up_good[t]:
                held_p=float(fp[j]);held_q=float(fq[j]);stamp=t
                if event is not None:
                    if event in seen:duplicates+=1
                    else:first_received[event]=t;seen.add(event)
                    downlinks+=1
                    if ack_good[t] and t<660:acks[t+1]=event
        if t<=600 and stamp is not None:
            errors.append((abs(held_p-fp[t]),abs(held_q-fq[t])))
            ages.append(t-stamp)
    onset_ids=[i for i,a in starts.items() if a]
    delayed=[first_received[i]-int(transitions[i]) for i in onset_ids if i in first_received]
    timely=sum(i in first_received and first_received[i]-int(transitions[i])<=20 for i in onset_ids)
    error=np.array(errors)
    return dict(uplinks=uplinks,acks=downlinks,total_frames=uplinks+downlinks,
        drain_uplinks=sum(t>600 for t in tx),local_onsets=len(onset_ids),
        received_onsets=len(delayed),timely20=timely,
        delay_p95=float(np.percentile(delayed,95)) if delayed else None,
        pressure_mae=float(error[:,0].mean()) if len(error) else None,
        flow_mae=float(error[:,1].mean()) if len(error) else None,
        age_p95=float(np.percentile(ages,95)) if ages else None,coverage=len(ages)/601,
        overflow=overflow,duplicates=duplicates)



def main():
    trials=[]
    for key,name,kind,params in CASES:
        for seed in SEEDS:
            data=simulate(kind,seed=seed,**params)
            for loss in [0,.1,.3]:
                for policy in POLICIES:
                    trials.append(dict(case=key,name=name,policy=policy,loss=loss,seed=seed,
                                       **replay(data,policy,loss,seed)))
    summaries=[]
    for key,name,_,_ in CASES:
        for loss in [0,.1,.3]:
            for policy in POLICIES:
                rows=[r for r in trials if r['case']==key and r['loss']==loss and r['policy']==policy]
                delays=[r['delay_p95'] for r in rows if r['delay_p95'] is not None]
                summaries.append(dict(case=key,name=name,policy=policy,loss=loss,n=len(rows),
                    uplinks_mean=float(np.mean([r['uplinks'] for r in rows])),
                    frames_mean=float(np.mean([r['total_frames'] for r in rows])),
                    local_onsets=sum(r['local_onsets'] for r in rows),
                    received_onsets=sum(r['received_onsets'] for r in rows),
                    timely20=sum(r['timely20'] for r in rows),
                    pressure_mae=float(np.mean([r['pressure_mae'] for r in rows])),
                    flow_mae=float(np.mean([r['flow_mae'] for r in rows])),
                    age_p95_mean=float(np.mean([r['age_p95'] for r in rows])),
                    mean_trial_delay_p95=float(np.mean(delays)) if delays else None,
                    coverage_mean=float(np.mean([r['coverage'] for r in rows])),
                    overflow=sum(r['overflow'] for r in rows)))
    payload=dict(data_class='uncalibrated_channel_replay',seeds=SEEDS,policies=POLICIES,
        cases=[dict(key=k,name=n,kind=t,parameters=p) for k,n,t,p in CASES],summary=summaries,
        assumptions=dict(sample_seconds=1,observation_seconds=601,drain_seconds=60,
            ewma_alpha=.2,burst_loss_seconds=15,queue_limit=16,ack_delay_seconds=1,
            ack_timeout_seconds=4,retry_backoff_after_four_attempts_seconds=10,
            alarm_deadline_seconds=20,actual_airtime=False,hardware_energy=False))
    (OUT/'summary.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    with (OUT/'trials.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trials[0]),lineterminator='\n');w.writeheader();w.writerows(trials)

    fig,axes=plt.subplots(1,2,figsize=(12,5.8))
    for ax,key,title in zip(axes,['normal','noise'],['正常轮灌','较大噪声']):
        rows=[r for r in summaries if r['case']==key and r['loss']==.1]
        for i,r in enumerate(rows):
            ax.scatter(r['frames_mean'],r['pressure_mae'],s=80,color=['#164C45','#426B91','#B4512B','#83639B'][i],label=POLICIES[r['policy']])
            ax.annotate(['周期10s','周期30s','原始事件','滤波限频事件'][i],(r['frames_mean'],r['pressure_mae']),xytext=(6,9),textcoords='offset points',fontsize=9)
        ax.set_title(title);ax.set_xlabel('发送帧数：上行＋确认，含60s清队列');ax.set_ylabel('远端重构滤波压力的平均绝对误差 / kPa');ax.grid(alpha=.2);ax.margins(x=.18,y=.2)
    fig.suptitle('相同检测与告警确认规则下的通信取舍｜未标定仿真 · 非LoRa实测',fontsize=14)
    fig.text(.04,.015,'假定随机丢包10%＋15s全丢包；所有策略发送同一滤波载荷。误差只相对本地模拟滤波值，不是田间压力精度。',fontsize=9)
    fig.tight_layout(rect=[0,.04,1,.94]);fig.savefig(FIG/'communication_tradeoff.png',dpi=180)
    svg=FIG/'communication_tradeoff.svg';fig.savefig(svg,metadata={'Date':None});svg.write_text('\n'.join(x.rstrip() for x in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n');plt.close(fig)
    for r in summaries:
        if r['loss']==.1 and r['case'] in {'normal','noise','short'}:
            print(r['case'],r['policy'],f"frames={r['frames_mean']:.1f}; pressure_MAE={r['pressure_mae']:.3f}; timely20={r['timely20']}/{r['local_onsets']}")
    assert all(r['overflow']==0 for r in summaries)
    assert len(trials)==1920 and len(summaries)==96
    print('1920 communication replays completed. All costs are frame counts; no real energy or radio timing claim.')


if __name__ == "__main__":
    main()
