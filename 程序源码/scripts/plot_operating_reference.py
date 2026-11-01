"""Three evidence figures; text and grayscale-readable encodings checked."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from review_operating_reference import trajectory,features,decision
DATA=ROOT/'simulation/operating_reference_review'
OUT=ROOT/'deliverables/工况参照对照图';OUT.mkdir(exist_ok=True)
S=json.loads((DATA/'summary.json').read_text(encoding='utf-8'))
P=S['parameters'];R=np.load(DATA/'first_seed_examples.npz',allow_pickle=False)
NAMES={'flow':'单流量阈值','sqrt':'固定平方根参照','reference':'标定参照＋持续阈值',
       'reference_gate':'标定参照＋过渡暂停','cusum':'标定参照＋CUSUM','ewma':'标定参照＋EWMA'}
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
                     'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,
                     'xtick.labelsize':12,'ytick.labelsize':12,'svg.fonttype':'none',
                     'svg.hashsalt':'reference-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]
def group(ex,sigma,scene,method):
    return next(g for g in S['groups'] if g['exponent']==ex and g['sigma']==sigma and g['scene']==scene and g['method']==method)
def save(fig,name,question):
    fig.canvas.draw();r=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();spans=[]
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():continue
        b=text.get_window_extent(r)
        assert b.x0>=0 and b.y0>=0 and b.x1<=w and b.y1<=h,(name,text.get_text(),b.bounds)
        assert text.get_fontsize()>=11
        spans.append(dict(text=text.get_text(),box=list(b.bounds),font_pt=text.get_fontsize()))
    for i,a in enumerate(spans):
        x,y,ww,hh=a['box']
        for b in spans[i+1:]:
            xx,yy,www,hhh=b['box']
            assert min(x+ww,xx+www)-max(x,xx)<=1 or min(y+hh,yy+hhh)-max(y,yy)<=1,(name,'text collision',a['text'],b['text'])
    for ext in ['png','svg']:
        fig.savefig(OUT/f'{name}.{ext}',dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
    svg=OUT/f'{name}.svg';svg.write_text('\n'.join(l.rstrip() for l in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    CHECKS.append(dict(name=name,question=question,text_within_canvas=True,text_pair_collision_check=True,
                        minimum_font_pt=min(t['font_pt'] for t in spans),texts=spans,
                        source_summary_sha256=hashlib.sha256((DATA/'summary.json').read_bytes()).hexdigest(),
                        file_sha256={e:hashlib.sha256((OUT/f'{name}.{e}').read_bytes()).hexdigest() for e in ['png','svg']}))
    plt.close(fig)
def matrix(ax,values,rows,cols,title):
    a=np.array(values);ax.imshow(a,cmap='Greys',vmin=0,vmax=20,aspect='auto')
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):ax.text(j,i,str(int(a[i,j])),ha='center',va='center',fontsize=12,color='white' if a[i,j]>=12 else '#222222')
    ax.set(yticks=range(len(rows)),yticklabels=rows,xticks=range(len(cols)),xticklabels=cols,title=title)
    ax.set_xticks(np.arange(-.5,len(cols),1),minor=True)
    ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
    ax.grid(which='minor',color='#d5d5d5',lw=.8)
    ax.tick_params(which='minor',length=0)
    ax.tick_params(length=0,pad=8)
    for spine in ax.spines.values():spine.set_visible(False)
def reference():
    fig,axes=plt.subplots(2,1,figsize=(10.2,8.6))
    fig.subplots_adjust(left=.24,right=.96,bottom=.19,top=.83,hspace=.65)
    pressure=np.linspace(68,143,160)
    styles=[('-', 'o','#222222'),('--','s','#526474'),(':','^','#276f63'),('-.','D','#9b6237')]
    for ex,(ls,marker,color) in zip([0.,.3,.5,.8],styles):
        ref=P['references'][f'n{ex:g}'];q=ref['a_l_min']*(pressure/100)**ref['n_fitted']
        axes[0].plot(pressure,q,ls=ls,marker=marker,markevery=24,markersize=5,color=color,lw=2,label=f'拟合n＝{ref["n_fitted"]:.3f}')
    axes[0].set(xlabel='$P_1$ / kPa',ylabel='健康预测总流量 / L/min',title='四种压力敏感性模型的独立健康参照',xlim=(65,145),xticks=[70,90,110,130])
    axes[0].grid(alpha=.15);axes[0].legend(loc='upper left',ncol=2,frameon=False)
    cols=[f'{ex:g}\n{label}' for ex in [0.,.3,.5,.8] for label in ['降压','升压']]
    methods=['flow','sqrt','reference']
    values=[[group(ex,.3,sc,m)['false_trials'] for ex in [0.,.3,.5,.8] for sc in ['supply_step','supply_up']] for m in methods]
    matrix(axes[1],values,[NAMES[m] for m in methods],cols,'健康供压切换：发生故障模式误报的试次 / 20')
    axes[1].set_xlabel('模型健康负载指数与供压切换方向')
    fig.suptitle('先校准健康参照，再讨论诊断算法',y=.97,fontsize=17,weight='bold')
    fig.text(.08,.035,'全部为合成数据。上图由480个健康标定点拟合；下图压力σ＝0.3kPa。\n指数是模型敏感性设定，未对应实测滴灌带；边界外预测仍需独立验证。',fontsize=12,linespacing=1.45)
    save(fig,'01_健康参照与模型失配','固定平方根关系失配时，健康标定参照是否减少假故障？')
def compare():
    methods=list(NAMES);sigmas=[.3,3.,10.]
    fig,axes=plt.subplots(2,1,figsize=(10.2,8.8))
    fig.subplots_adjust(left=.30,right=.96,bottom=.17,top=.85,hspace=.43)
    vals=[[group(.5,s,k,m)['early'] for k in ['leak','restriction'] for s in sigmas] for m in methods]
    cols=[f'{label}\nσ={s:g}' for label in ['泄漏','受限'] for s in sigmas]
    matrix(axes[0],vals,[NAMES[m] for m in methods],cols,'有效早期检出次数 / 20（数值越大越好）')
    vals=[[group(.5,s,'long_normal',m)['false_trials'] for s in sigmas] for m in methods]
    matrix(axes[1],vals,[NAMES[m] for m in methods],[f'σ={s:g}kPa' for s in sigmas],'长时健康水路误报试次 / 20（数值越小越好）')
    fig.suptitle('六种候选：检出与长时误报必须同时看',y=.97,fontsize=17,weight='bold')
    fig.text(.08,.035,'合成模型指数0.5；固定1Hz；每组20种子。长时监测3470秒。\n门限仅用健康数据确定；过渡复核提示另计，不能因暂停诊断就称水路正常。',fontsize=12,linespacing=1.45)
    save(fig,'02_六方法检出与误报','候选方法是否兼顾有效早期和长时间误报？')
def gate():
    tr=trajectory('fast_leak_switch',.5);obs=R['0.5|0.3|fast_leak_switch_observed'];f=features(obs,P['references']['n0.5'])
    fig,axes=plt.subplots(2,1,figsize=(11.2,7.9))
    fig.subplots_adjust(left=.10,right=.65,bottom=.17,top=.85,hspace=.57)
    t=tr['t'];critical=int(np.flatnonzero((t>=180)&(tr['severity']>=.15))[0])
    for ax in axes:
        ax.set_xlim(165,235);ax.set_xticks([170,180,190,200,210,220,230]);ax.grid(alpha=.15)
        onset=np.flatnonzero(f['gate']&~np.r_[False,f['gate'][:-1]])
        for j in onset:
            ax.axvspan(j,min(j+20,len(t)),facecolor='#eeeeee',edgecolor='#aaaaaa',hatch='///',lw=.5,zorder=0)
    axes[0].plot(t,tr['severity']*100,color='#222222',lw=2,label='模型健康流量偏离')
    axes[0].axhline(15,color='#777777',ls='-.',lw=1.4)
    for method,color,ls,marker in [('reference','#276f63','--','o'),('reference_gate','#9b6237',':','s')]:
        d=decision(f,method,P);correct=[e['t_s'] for e in d['events'] if e['t_s']>=180 and e['pattern']=='leak_pattern'];first=correct[0]
        axes[0].axvline(first,color=color,ls=ls,lw=1.5)
        axes[0].scatter([first],[tr['severity'][first]*100],marker=marker,facecolor='white',edgecolor=color,s=65,zorder=5)
        axes[0].plot([],[],color=color,ls=ls,marker=marker,label=f'{NAMES[method]}：{first}s')
    axes[0].set(ylim=(0,34),yticks=[0,10,20,30],xlabel='模型时间 / s',ylabel='健康流量偏离 / %',title=f'快速泄漏与降压同时发生，15%参照在{critical}s')
    axes[0].legend(loc='upper left',bbox_to_anchor=(1.025,.95),frameon=False)
    axes[1].plot(t,f['avg'][:,0],color='#526474',ls='-',lw=2,label='$P_0$ 因果均值')
    axes[1].plot(t,f['avg'][:,1],color='#222222',ls='--',lw=2,label='$P_1$ 因果均值')
    axes[1].set(ylim=(45,125),yticks=[50,75,100,125],xlabel='模型时间 / s',ylabel='压力 / kPa',title='斜线区域仅表示压力变化引发的20秒复核暂停')
    axes[1].legend(loc='upper left',bbox_to_anchor=(1.025,.95),frameon=False)
    fig.suptitle('反例：压力过渡时暂停诊断，可能错过早期窗口',y=.97,fontsize=17,weight='bold')
    fig.text(.10,.035,'固定首个留出种子25000；压力σ＝0.3kPa；故障从180秒起、45秒渐进增加。\n门控只读压力；诊断不读取阀态或故障标签。本例不代表实物动作或水力瞬态。',fontsize=12,linespacing=1.45)
    save(fig,'03_过渡暂停的快速故障反例','传感器触发的过渡暂停是否遮住切换期间的故障？')
reference();compare();gate()
(DATA/'figure_checks.json').write_text(json.dumps(CHECKS,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Three figures passed text-boundary and text-collision checks.')
