"""Candidate range/measurement calculations; not calibrated hardware evidence."""
from pathlib import Path
import csv,json,itertools,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from diagnosis_feasibility import hydraulic
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/hardware_results';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12})
rows=[]
for ps,b,c,r in itertools.product([80,120,160],[False,True],[.28,.37],[.8,8.]):
    p0,p1,q=map(float,hydraulic(ps,c=c,r=r,b=b))
    qb=.35*math.sqrt(p0/(1+.8*.35**2)) if b else 0.
    rows.append(dict(ps_kpa=ps,b_open=b,c=c,r=r,p0_kpa=p0,p1_kpa=p1,q_a_l_min=q,q_total_l_min=q+qb))
with (OUT/'range_grid.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
minq=min(x['q_a_l_min'] for x in rows);maxq=max(x['q_a_l_min'] for x in rows)
total=max(x['q_total_l_min'] for x in rows)
assert .3<minq<=maxq<5 and max(x['p0_kpa'] for x in rows)<200
def feature_interval(p0,p1,q,full_scale=False):
    dq=(.05 if full_scale else q*.01)+60/(540*10)
    return ((q-dq)/math.sqrt(p1+.5),(q+dq)/math.sqrt(p1-.5)),((p0-p1-1)/(q+dq)**2,(p0-p1+1)/(q-dq)**2)
observability=[]
for ps,b,kind,degree in itertools.product([80,120,160],[False,True],['leak','restriction'],[.05,.1,.15]):
    healthy=hydraulic(ps,c=.28,b=b)
    lo,hi=(.28,.37) if kind=='leak' else (.8,8.)
    for _ in range(70):
        mid=(lo+hi)/2
        changed=hydraulic(ps,c=mid if kind=='leak' else .28,r=.8 if kind=='leak' else mid,b=b)
        severity=abs(changed[2]/healthy[2]-1)
        if severity<degree:lo=mid
        else:hi=mid
    assert abs(severity-degree)<1e-6,'Target severity not reachable in planned range'
    healthy_interval=feature_interval(*healthy)[0 if kind=='leak' else 1]
    fault_interval=feature_interval(*changed)[0 if kind=='leak' else 1]
    healthy_fs=feature_interval(*healthy,full_scale=True)[0 if kind=='leak' else 1]
    fault_fs=feature_interval(*changed,full_scale=True)[0 if kind=='leak' else 1]
    observability.append({'ps_kpa':ps,'b_open':b,'kind':kind,'target_degree':degree,'c_or_r':mid,'feature':('K' if kind=='leak' else 'Rhat'),'healthy_interval':healthy_interval,'fault_interval':fault_interval,'intervals_disjoint':bool(fault_interval[0]>healthy_interval[1]),'full_scale_healthy_interval':healthy_fs,'full_scale_fault_interval':fault_fs,'full_scale_intervals_disjoint':bool(fault_fs[0]>healthy_fs[1])})
with (OUT/'observability.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=observability[0],lineterminator='\n');w.writeheader();w.writerows(observability)
result={'classification':'uncalibrated_design_calculation_not_hardware_test','healthy_c':.28,'leak_max_c':.37,'r_range':[.8,8.],'grid_count':len(rows),'q_a_range_l_min':[minq,maxq],'max_total_flow_l_min':total,'pressure_sensor_only_dp_bound_kpa':1.,'shunt_v_range':[.6,3.],'adc_nominal_pressure_step_kpa':.000125/(.016*150)*200,'flow_quantization_l_min':{'1s':60/540,'10s':60/(540*10)},'excluded_sen0257_single_bound_kpa':[8,16],'severity_checks':len(observability),'disjoint_intervals':sum(x['intervals_disjoint'] for x in observability),'disjoint_by_kind_degree':{kind+'_'+str(degree):sum(x['intervals_disjoint'] for x in observability if x['kind']==kind and x['target_degree']==degree) for kind,degree in itertools.product(['leak','restriction'],[.05,.1,.15])},'caveat':'Optimistic bounded-error calculation includes only sensor nominal limits and count quantization, excluding ADC/shunt/temperature/calibration/skew; disjoint intervals are not detection accuracy or Gaussian noise sigma. Pump curve and continuous duty required.'}
result['flow_accuracy_assumptions']={'reading':'1% of reading','full_scale':'1% of upper range 5 L/min; conservative alternate interpretation'}
result['full_scale_disjoint_intervals']=sum(x['full_scale_intervals_disjoint'] for x in observability)
result['full_scale_disjoint_by_kind_degree']={kind+'_'+str(degree):sum(x['full_scale_intervals_disjoint'] for x in observability if x['kind']==kind and x['target_degree']==degree) for kind,degree in itertools.product(['leak','restriction'],[.05,.1,.15])}
(OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
fig,axes=plt.subplots(2,1,figsize=(8.5,6.7));fig.subplots_adjust(left=.12,right=.97,top=.91,bottom=.17,hspace=.65)
q=np.linspace(2,4.5,101);a=axes[0]
a.plot(q,.8*q*q,color='#164c45',lw=2.5,label='模型健康压降 RQ²（R=0.8）')
a.axhline(1,color='#426b91',ls='--',lw=2,label='候选双通道仅传感器界限 1kPa')
a.axhspan(16,32,color='#b4512b',alpha=.13,label='1.6MPa候选双通道界限 16—32kPa')
a.set(xlabel='A支路流量（L/min）',ylabel='压降或误差界限（kPa）',ylim=(0,34),title='量程选错时，测量误差可能覆盖健康压降');a.grid(alpha=.15);a.legend(fontsize=10,loc='upper left')
a=axes[1];grid=sorted(set(x['q_a_l_min'] for x in rows));a.scatter(grid,[1]*len(grid),color='#164c45',s=32,label='24组模型边界组合')
a.axvspan(.3,5,color='#164c45',alpha=.07,label='SEN0549标称流量范围');a.axvline(5,color='#b4512b',ls='--')
a.set(xlabel='A支路总流量（L/min）',yticks=[],ylim=(.65,1.4),xlim=(0,5.5),title=f'负载调整后，模型边界流量为 {minq:.2f}—{maxq:.2f} L/min')
a.text(.5,.75,'计数分辨率：1秒窗0.111；10秒窗0.0111 L/min\n10秒窗增加响应延迟，需纳入早期评价',fontsize=11,color='#556762');a.legend(fontsize=10,loc='upper left')
fig.text(.12,.055,'设计计算，非实测；压力标称界限并非完整采集误差。\n网格：80/120/160kPa × B开/关 × C=0.28/0.37 × R=0.8/8.0。',fontsize=10,color='#556762')
for ext in ['png','svg']:fig.savefig(ROOT/f'application/figures/hardware_feasibility.{ext}',dpi=200,facecolor='white')
svg_path=ROOT/'application/figures/hardware_feasibility.svg'
svg_path.write_text('\n'.join(x.rstrip() for x in svg_path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,ensure_ascii=False))
