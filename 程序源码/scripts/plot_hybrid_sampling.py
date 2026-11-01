"""Question-driven, grayscale-readable standalone evidence figures."""
from pathlib import Path
import csv, hashlib, json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
import review_hybrid_sampling as m
DATA=m.OUT;OUT=ROOT/'deliverables/组合诊断与事件采集图';OUT.mkdir(exist_ok=True)
S=json.loads((DATA/'summary.json').read_text(encoding='utf-8'));P=S['parameters']
NAMES={'threshold':'原持续阈值','cusum':'原CUSUM','plain_or':'原阈值 或 CUSUM',
       'plain_and':'原阈值 且 CUSUM','guarded_fast':'噪声保护快速通道',
       'bounded':'60点有界累积','hybrid':'快速＋有界累积'}
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
    'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,'xtick.labelsize':12,'ytick.labelsize':12,
    'svg.fonttype':'none','svg.hashsalt':'hybrid-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]

def group(stage,sigma,scene,method,profile=''):
    return next(g for g in S[stage+'_groups'] if g['exponent']==.5 and g['sigma']==sigma and g['scene']==scene and g['method']==method and g['profile']==profile)

def save(fig,name,question):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();spans=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text():continue
        b=t.get_window_extent(renderer)
        assert b.x0>=0 and b.y0>=0 and b.x1<=w and b.y1<=h,(name,t.get_text(),b.bounds)
        assert t.get_fontsize()>=11,(name,t.get_text())
        spans.append(dict(text=t.get_text(),box=list(b.bounds),font_pt=t.get_fontsize()))
    for i,a in enumerate(spans):
        x,y,ww,hh=a['box']
        for b in spans[i+1:]:
            xx,yy,www,hhh=b['box']
            assert min(x+ww,xx+www)-max(x,xx)<=1 or min(y+hh,yy+hhh)-max(y,yy)<=1,(name,'text overlap',a['text'],b['text'])
    for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
    svg=OUT/f'{name}.svg';svg.write_text('\n'.join(l.rstrip() for l in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    CHECKS.append(dict(name=name,question=question,text_within_canvas=True,text_collision_check=True,
        minimum_font_pt=min(t['font_pt'] for t in spans),texts=spans,
        source_summary_sha256=m.sha(DATA/'summary.json'),
        file_sha256={ext:m.sha(OUT/f'{name}.{ext}') for ext in ['png','svg']}))
    plt.close(fig)

def matrix(ax,values,labels,cols,title,maximum):
    a=np.array(values);ax.imshow(a,cmap='Greys',vmin=0,vmax=maximum,aspect='auto')
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):ax.text(j,i,str(int(a[i,j])),ha='center',va='center',color='white' if a[i,j]>=maximum*.6 else '#222',fontsize=12)
    ax.set(yticks=range(len(labels)),yticklabels=labels,xticks=range(len(cols)),xticklabels=cols,title=title)
    ax.set_xticks(np.arange(-.5,len(cols),1),minor=True);ax.set_yticks(np.arange(-.5,len(labels),1),minor=True)
    ax.grid(which='minor',color='#ccc',lw=.8);ax.tick_params(which='minor',length=0);ax.tick_params(length=0,pad=8)
    for spine in ax.spines.values():spine.set_visible(False)

def fusion():
    fig,axes=plt.subplots(2,1,figsize=(11.6,10.5));fig.subplots_adjust(left=.29,right=.96,bottom=.16,top=.86,hspace=.48)
    methods=m.FUSIONS;sigmas=[.3,10.]
    values=[[group('fusion',s,sc,method)['early'] for s in sigmas for sc in ['leak','restriction','fast_leak_switch']] for method in methods]
    cols=[f'{label}\nσ={s:g}' for s in sigmas for label in ['缓变泄漏','局部受限','切换快漏']]
    matrix(axes[0],values,[NAMES[x] for x in methods],cols,'有效早期检出次数 / 20（越大越好）',20)
    values=[[group('fusion',s,sc,method)['false_trials'] for sc,s in [('long_normal',.3),('long_normal',10.),('drift',.3),('load_unknown',.3)]] for method in methods]
    matrix(axes[1],values,[NAMES[x] for x in methods],['长时正常\nσ=0.3','长时正常\nσ=10','压力漂移\nσ=0.3','未报负载变化\nσ=0.3'],'无水路故障场景：出现故障模式误报的试次 / 20（越小越好）',20)
    fig.suptitle('组合有收益，也会继承原方法的误报',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.035,'全部为合成回放；模型指数0.5，固定1Hz，各组20种子。σ为压力噪声标准差，单位kPa。\n有效早期要求无故障前误报、首次故障后模式正确，且早于模型流量偏差15%的时刻。\n压力漂移与未报负载变化单列，不能用普通健康水路结果代替。',fontsize=12,linespacing=1.5)
    save(fig,'01_组合方法收益与反例','组合是否同时提升缓变、快速故障和无故障稳健性？')

def acquisition():
    fig,axes=plt.subplots(2,1,figsize=(11.6,9.8));fig.subplots_adjust(left=.23,right=.95,bottom=.15,top=.81,hspace=.58)
    scene_names={'normal':'正常','leak':'缓变泄漏','fast_leak_switch':'切换快漏'}
    labels=[];eligible=[];insufficient=[];unread=[]
    for scene in scene_names:
        for profile in ['fixed','adaptive']:
            g=group('sensor',.3,scene,'hybrid',profile);a=g['mean_eligible_frames'];b=g['mean_insufficient_frames']
            labels.append(scene_names[scene]+('·固定1Hz' if profile=='fixed' else '·5秒巡检'))
            eligible.append(a);insufficient.append(b);unread.append(471-a-b)
    y=np.arange(6)
    axes[0].barh(y,eligible,color='#444',label='完整实采窗，可诊断')
    axes[0].barh(y,insufficient,left=eligible,color='#ddd',edgecolor='#888',hatch='///',label='已读取，诊断窗不足')
    axes[0].barh(y,unread,left=np.array(eligible)+insufficient,color='white',edgecolor='#aaa',hatch='..',label='该秒未采压力')
    axes[0].set(yticks=y,yticklabels=labels,xlim=(0,480),xticks=[0,100,200,300,400],xlabel='监测段471个逐秒时刻中的平均数量 / 12种子',title='少读压力与诊断可用性必须一起呈现（σ=0.3kPa）')
    axes[0].invert_yaxis();axes[0].legend(loc='lower left',bbox_to_anchor=(-.2,1.15),ncol=3,frameon=False)
    for i,n in enumerate(eligible):
        if n>40:axes[0].text(n/2,i,f'{n:.0f}',ha='center',va='center',color='white',fontsize=12)
    with (DATA/'wake_phase_results.csv').open(encoding='utf-8') as f:rr=list(csv.DictReader(f))
    methods=m.SENSOR_METHODS
    values=[[sum(r['early_valid']=='True' for r in rr if float(r['sigma'])==s and r['method']==method) for s in [.3,3.,10.]] for method in methods]
    matrix(axes[1],values,[NAMES[x] for x in methods],['σ=0.3kPa','σ=3kPa','σ=10kPa'],'切换快速泄漏：五种巡检起始时刻下的有效早期次数 / 60',60)
    fig.suptitle('事件采集减少读取，但不等于持续诊断或节能实测',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.025,'全部为合成回放；流量脉冲假定连续计数，压力只使用实际读取点；模型指数0.5。\n下图为12个噪声种子×5个起始时刻，重复使用同一批轨迹，不是60次独立实物实验。\n高噪声下组合57/60有效早期；未采压力与不足窗口都不能标记为正常。',fontsize=12,linespacing=1.5)
    save(fig,'02_采集覆盖与起始时刻','降低读取次数是否牺牲诊断窗口及早期时机？')

def failure():
    # Deterministic selection: the first failing hybrid phase row in stored order.
    with (DATA/'wake_phase_results.csv').open(encoding='utf-8') as f:rr=list(csv.DictReader(f))
    r=next(r for r in rr if r['method']=='hybrid' and r['early_valid']=='False')
    seed=int(r['seed']);phase=int(r['phase']);sigma=float(r['sigma']);tr=m.trajectory('fast_leak_switch',.5)
    obs=m.observe(tr,sigma,seed,'fast_leak_switch');ref=P['baseline']['references']['n0.5']
    replay=m.sensor_replay(obs,seed,ref,'adaptive',P['h_bounded_sensor']['adaptive'],phase)
    fig,axes=plt.subplots(2,1,figsize=(11.8,8.2));fig.subplots_adjust(left=.12,right=.70,bottom=.18,top=.84,hspace=.6)
    first=int(r['first_post_s']);critical=int(r['critical_s'])
    for ax in axes:
        ax.axvline(180,color='#777',ls=':',lw=1.6,label='故障起点 180s')
        ax.axvline(critical,color='#333',ls='--',lw=1.6,label=f'模型15%参照 {critical}s')
        ax.axvline(first,color='black',ls='-.',lw=1.6,label=f'首次正确检出 {first}s')
        ax.set_xlim(160,235);ax.set_xticks([160,180,200,220]);ax.grid(alpha=.13)
    acq=np.array(replay['acquired']);valid=np.array([x['t'] for x in replay['records'] if x['valid']]);triggers=np.array(replay['triggers'])
    axes[0].scatter(acq,np.zeros(len(acq)),marker='|',s=90,color='#555')
    axes[0].scatter(triggers,np.ones(len(triggers)),marker='^',s=23,facecolors='white',edgecolors='#333')
    axes[0].scatter(valid,np.full(len(valid),2),marker='s',s=16,color='#222')
    axes[0].set(yticks=[0,1,2],yticklabels=['压力实采','升频触发','完整诊断窗'],ylim=(-.5,2.5),xlabel='时间 / s',title='只允许实采点形成压力窗')
    axes[0].legend(loc='upper left',bbox_to_anchor=(1.03,1.02),frameon=False,labelspacing=1.4)
    t=np.array([x['t'] for x in replay['records']]);scale=np.array(replay['context']['scale'])
    fast=np.array([x['x'][0]/max(.06,6*scale[0]) if x['valid'] else np.nan for x in replay['records']])
    slow=np.array([x['bounded'][0]/P['h_bounded_sensor']['adaptive'][0] if x['valid'] else np.nan for x in replay['records']])
    axes[1].plot(t,fast,color='#444',ls='-',lw=1.6,label='泄漏快速量 / 门限')
    axes[1].plot(t,slow,color='black',ls='--',lw=1.6,label='泄漏累积量 / 门限')
    axes[1].axhline(1,color='#999',ls=':',label='通道越限位置 1')
    shown=(t>=160)&(t<=235)
    upper=float(np.ceil(np.nanmax(np.r_[fast[shown],slow[shown]])+.3))
    axes[1].set(xlabel='时间 / s',ylabel='无量纲',title='通道越限后仍须五帧连续同模式确认',ylim=(-1.2,upper),yticks=np.arange(0,upper,2))
    handles,labels=axes[1].get_legend_handles_labels();axes[1].legend(handles[3:],labels[3:],loc='upper left',bbox_to_anchor=(1.03,1.02),frameon=False,labelspacing=1.4)
    fig.suptitle('保留失败案例：巡检起始时刻会改变检出时机',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.04,f'合成切换快速泄漏；σ={sigma:g}kPa，种子{seed}，巡检起始偏移{phase}s；按记录顺序取首个失败案例。\n首次正确检出{first}s，晚于模型参照{critical}s；不足窗口处断线，未补入未采压力。\n模型15%参照只用于离线评价，不是农艺阈值，也不输入在线算法。',fontsize=12,linespacing=1.5)
    save(fig,'03_巡检相位失败案例','事件触发为何仍可能错过快速故障的早期窗口？')

if __name__=='__main__':
    fusion();acquisition();failure()
    m.dump('figure_checks.json',dict(figures=CHECKS,scope='standalone images; insertion into Word not checked'))
    print(f'{len(CHECKS)} figures passed text-boundary/collision checks.')
