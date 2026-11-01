"""Publication-style, grayscale-readable plots from locked synthetic results."""
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
from review_cusum import cusum_classify
from review_diagnosis import classify

DATA=ROOT/'simulation/cusum_review'
OUT=ROOT/'deliverables/算法对照图'
OUT.mkdir(parents=True,exist_ok=True)
D=json.loads((DATA/'summary.json').read_text(encoding='utf-8'))
P=json.loads((DATA/'frozen_parameters.json').read_text(encoding='utf-8'))
LEVELS=[.3,1.,3.,10.]
NAMES={'flow_only':'单流量阈值','physical':'联合持续阈值','cusum':'联合特征＋CUSUM'}
STYLE={'flow_only':dict(color='#586472',ls=':',marker='s'),
       'physical':dict(color='#246c63',ls='--',marker='o'),
       'cusum':dict(color='#af602e',ls='-',marker='^')}
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,
                     'font.size':12,'axes.labelsize':12,'axes.titlesize':14,
                     'xtick.labelsize':12,'ytick.labelsize':12,'legend.fontsize':12,
                     'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none',
                     'svg.hashsalt':'cusum-20261006'})
RECORDS=[]

def group(kind,sigma,method):
    return next(g for g in D['groups'] if g['kind']==kind and g['pressure_sigma_kpa']==sigma and g['method']==method)

def save(fig,name,description):
    fig.canvas.draw(); renderer=fig.canvas.get_renderer(); w,h=fig.canvas.get_width_height()
    spans=[]
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text(): continue
        bbox=text.get_window_extent(renderer)
        assert bbox.x0>=0 and bbox.y0>=0 and bbox.x1<=w and bbox.y1<=h,(name,text.get_text(),bbox.bounds)
        assert text.get_fontsize()>=11
        spans.append(dict(text=text.get_text(),font_pt=text.get_fontsize(),box=list(bbox.bounds)))
    for i,a in enumerate(spans):
        ax,ay,aw,ah=a['box']
        for b in spans[i+1:]:
            bx,by,bw,bh=b['box']
            overlap_w=min(ax+aw,bx+bw)-max(ax,bx)
            overlap_h=min(ay+ah,by+bh)-max(ay,by)
            assert overlap_w<=1 or overlap_h<=1,(name,'text collision',a['text'],b['text'])
    for ext in ('png','svg'):
        fig.savefig(OUT/f'{name}.{ext}',dpi=180,facecolor='white',
                    metadata={'Date':None} if ext=='svg' else None)
    svg=OUT/f'{name}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
                   encoding='utf-8',newline='\n')
    RECORDS.append(dict(name=name,question=description,canvas_px=[w,h],
                        text_within_canvas=True,minimum_font_pt=min(s['font_pt'] for s in spans),
                        text_pair_collision_check=True,
                        grayscale_encoding='Distinct solid/dashed/dotted lines and triangle/circle/square markers; color is redundant.',
                        source_summary_sha256=hashlib.sha256((DATA/'summary.json').read_bytes()).hexdigest(),
                        file_sha256={ext:hashlib.sha256((OUT/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ('png','svg')},
                        texts=spans))
    plt.close(fig)

def outcome():
    fig,axes=plt.subplots(2,2,figsize=(10.5,8.7))
    fig.subplots_adjust(left=.09,right=.97,bottom=.19,top=.81,hspace=.65,wspace=.35)
    for row,(kind,label) in enumerate([('leak','等效泄漏'),('restriction','等效受限')]):
        for method in NAMES:
            gg=[group(kind,s,method) for s in LEVELS]
            axes[row,0].plot(range(4),[g['early_trials'] for g in gg],lw=2,markersize=7,label=NAMES[method],**STYLE[method])
            axes[row,1].plot(range(4),[g['median_valid_lead_s'] for g in gg],lw=2,markersize=7,label=NAMES[method],**STYLE[method])
        axes[row,0].set(ylim=(-2,42),yticks=[0,10,20,30,40],ylabel='有效早期次数 / 40',title=label)
        axes[row,1].set(ylim=(0,125),yticks=[0,30,60,90,120],ylabel='有效试次提前量中位数 / s',title=label)
        for ax in axes[row]:
            ax.set(xticks=range(4),xticklabels=['0.3','1','3','10'],xlabel='每个压力通道的噪声σ / kPa')
            ax.grid(alpha=.18); ax.set_axisbelow(True)
    fig.suptitle('故障检出：减少误报与缩短延迟需要权衡',x=.5,y=.97,fontsize=17,weight='bold')
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.91),ncol=3,frameon=False)
    fig.text(.09,.035,'合成数据；每场景、每噪声40个留出种子；三方法使用同一观测。\n有效早期须无前期误报、首次模式正确且早于15%模型参照；提前量仅统计有效试次。',fontsize=12,linespacing=1.45)
    save(fig,'01_故障检出与提前量','CUSUM是否在相同观测和评价规则下提高有效早期并缩短延迟？')

def controls():
    fig,axes=plt.subplots(3,1,figsize=(8.6,9.7))
    fig.subplots_adjust(left=.13,right=.96,bottom=.13,top=.84,hspace=.64)
    for ax,case,title in zip(axes,['normal','supply','long'],['正常水路含B支路切换：470秒监测','健康水路供压渐变：470秒监测','正常水路重复B切换：3470秒监测']):
        for method in NAMES:
            if case=='long': gg=[next(g for g in D['long_healthy'] if g['method']==method and g['pressure_sigma_kpa']==s) for s in LEVELS]
            else: gg=[group(case,s,method) for s in LEVELS]
            ax.plot(range(4),[g['false_alarm_trials'] for g in gg],lw=2,markersize=7,label=NAMES[method],**STYLE[method])
        ax.set(xticks=range(4),xticklabels=['0.3','1','3','10'],ylim=(-2,42),yticks=[0,10,20,30,40],
               xlabel='每个压力通道的噪声σ / kPa',ylabel='发生误报的试次 / 40',title=title)
        ax.grid(alpha=.18); ax.set_axisbelow(True)
    fig.suptitle('正常对照：短时门限不能保证长时间无误报',y=.975,fontsize=17,weight='bold')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.54,.925),ncol=3,frameon=False,columnspacing=1)
    fig.text(.13,.025,'全部为健康水路模型。每组40个种子；一次报警即计该试次出现误报。\n长时挑战复用留出种子，不作为新增独立实验；并未提供操作状态门控。',fontsize=12,linespacing=1.45)
    save(fig,'02_正常工况与长时误报','是否把压力变化当成故障，延长观测时间后是否仍可靠？')

def timing():
    raw=np.load(DATA/'heldout_observations.npz',allow_pickle=False)
    with (DATA/'paired_results.csv').open(encoding='utf-8',newline='') as f: rr=list(csv.DictReader(f))
    fig,axes=plt.subplots(2,1,figsize=(11.2,7.7))
    fig.subplots_adjust(left=.10,right=.64,bottom=.17,top=.84,hspace=.58)
    t=raw['t']
    for ax,kind,title in zip(axes,['leak','restriction'],['等效泄漏','等效受限']):
        tid=f'{kind}|3|22000'
        i=list(raw['trial_ids']).index(tid)
        sev=raw['severity_by_kind'][['normal','supply','leak','restriction','drift','load_unknown'].index(kind)]*100
        ax.plot(t,sev,color='#222222',lw=2,label='健康流量偏离（模型真值）')
        ax.axhline(15,color='#666666',lw=1.3,ls='-.')
        for method in NAMES:
            r=next(r for r in rr if r['trial_id']==tid and r['method']==method)
            d=int(r['first_correct_s']); critical=int(r['critical_s'])
            assert r['early_valid']=='True' and d<critical
            style=STYLE[method]
            ax.axvline(d,color=style['color'],ls=style['ls'],lw=1.6)
            ax.scatter([d],[sev[d]],marker=style['marker'],s=65,facecolor='white',edgecolor=style['color'],zorder=4)
            ax.plot([],[],label=f'{NAMES[method]}：{d}s',**style)
        ax.set(xlim=(350,540),xticks=[360,400,440,480,520],ylim=(0,34),yticks=[0,10,20,30],
               xlabel='模型时间 / s',ylabel='健康流量偏离 / %',title=f'{title}：15%参照在{critical}s')
        ax.legend(loc='upper left',bbox_to_anchor=(1.025,.95),fontsize=11,frameon=False)
        ax.grid(alpha=.15)
    fig.suptitle('同一轨迹：更复杂的算法未必更早检出',y=.97,fontsize=17,weight='bold')
    fig.text(.10,.035,'示例固定取首个留出种子22000，压力σ=3kPa；故障从360秒渐进增加。\n标记为五次持续确认后的首次正确提示；不使用单例代替40种子统计。',fontsize=12,linespacing=1.45)
    save(fig,'03_同观测检出时刻','在首个固定留出种子上，各算法何时首次确认？')

outcome(); controls(); timing()
(DATA/'figure_checks.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print('Three figures rendered with bounded text and grayscale-distinguishable encodings.')
