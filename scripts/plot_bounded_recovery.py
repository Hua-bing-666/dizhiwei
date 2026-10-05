"""Gray-scale recovery evidence from accepted byte replay, not radio plots."""
from pathlib import Path
import csv
import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_bounded_recovery as m
OUT=ROOT/'deliverables/断连恢复与有界补发图'
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
                     'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,
                     'xtick.labelsize':12,'ytick.labelsize':12,'svg.fonttype':'none',
                     'svg.hashsalt':'bounded-recovery-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]


def rows(name):
    with (m.OUT/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))


def save(fig,name,question):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();width,height=fig.canvas.get_width_height();spans=[]
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():continue
        b=text.get_window_extent(renderer)
        assert b.x0>=0 and b.y0>=0 and b.x1<=width and b.y1<=height,(name,text.get_text())
        assert text.get_fontsize()>=11
        spans.append(dict(text=text.get_text(),box=list(b.bounds),font_pt=text.get_fontsize()))
    for i,a in enumerate(spans):
        x,y,w,h=a['box']
        for b in spans[i+1:]:
            xx,yy,ww,hh=b['box']
            assert min(x+w,xx+ww)-max(x,xx)<=1 or min(y+h,yy+hh)-max(y,yy)<=1,(name,a['text'],b['text'])
    for ext in ['png','svg']:
        path=OUT/f'{name}.{ext}'
        fig.savefig(path,dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':path.write_text('\n'.join(s.rstrip() for s in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    CHECKS.append(dict(name=name,question=question,minimum_font_pt=min(s['font_pt'] for s in spans),
                       text_within_canvas=True,text_collision_check=True,texts=spans,
                       file_sha256={ext:m.sha(OUT/f'{name}.{ext}') for ext in ['png','svg']}))
    plt.close(fig)


def timeline():
    data=json.loads((m.OUT/'recovery_example.json').read_text(encoding='utf-8'))
    fig,ax=plt.subplots(figsize=(11.6,5.0));fig.subplots_adjust(left=.14,right=.97,bottom=.20,top=.80)
    ax.axvspan(351,351+data['duration'],facecolor='.94',edgecolor='.75',hatch='///',lw=.6)
    selected=[r for r in data['dispatch_trace'] if 350<=r['t_s']+1<=505]
    keys=sorted({tuple(r['key']) for r in selected});positions={key:len(keys)-i-1 for i,key in enumerate(keys)}
    for key in keys:
        same=[r for r in selected if tuple(r['key'])==key]
        ax.plot([r['t_s']+1 for r in same],[positions[key]]*len(same),color='.55',lw=.8)
    for r in selected:
        ax.plot(r['t_s']+1,positions[tuple(r['key'])],marker='s' if r['probe'] else 'o',ms=5,
                mfc='black' if r['ack'] else 'white',mec='black',linestyle='none')
        if r['reactivated']:
            ax.axvline(r['t_s']+1,ls=':',color='black',lw=1.2)
    labels=[('探测' if next(r['probe'] for r in selected if tuple(r['key'])==key) else '业务')+' '+str(key[2]) for key in keys]
    ax.set(yticks=[positions[key] for key in keys],yticklabels=labels,ylim=(-.5,len(keys)-.5),xlim=(350,505),
           xticks=[350,380,410,440,470,500],xlabel='回放时间 / s')
    ax.grid(axis='x',alpha=.12)
    handles=[Line2D([],[],color='black',marker='o',ls='none',label='及时ACK'),
             Line2D([],[],color='black',marker='o',mfc='white',ls='none',label='未获ACK'),
             Patch(facecolor='.94',edgecolor='.75',hatch='///',label='仿真阻断'),
             Line2D([],[],color='black',ls=':',label='触发补发')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,.99),ncol=4,frameon=False)
    save(fig,'01_ACK触发的恢复过程','恢复由哪一次有效确认触发，而不是由中断结束时间直接触发？')


def outcomes():
    boundary=rows('boundary_results.csv');main=rows('paired_results.csv')
    styles=[('burst_backoff','上轮间隔重试','.45',''),('bounded_recovery','条件探测＋有界补发','white','///')]
    fig,axes=plt.subplots(2,1,figsize=(11.6,7.8));fig.subplots_adjust(left=.14,right=.97,bottom=.12,top=.84,hspace=.64)
    x=np.arange(3);width=.30;all_missing=[];all_bytes=[]
    for j,(policy,label,color,hatch) in enumerate(styles):
        pos=x+(j-.5)*width;missing=[];totals=[];byte_means=[]
        for duration in [20,120,360]:
            group=[r for r in boundary if r['policy']==policy and int(r['outage_seconds'])==duration]
            missing.append(sum(int(r['missing_events']) for r in group));totals.append(sum(int(r['generated_events']) for r in group))
        axes[0].bar(pos,missing,width,color=color,hatch=hatch,edgecolor='black',label=label)
        for xx,n,total in zip(pos,missing,totals):axes[0].text(xx,n+2,f'{n}/{total}',ha='center',va='bottom',fontsize=12)
        for mode in ['clean','loss','outage']:
            group=[r for r in main if r['policy']==policy and r['mode']==mode]
            byte_means.append(sum(int(r['attempted_uart_bytes_including_ack']) for r in group)/len(group))
        axes[1].bar(pos,byte_means,width,color=color,hatch=hatch,edgecolor='black')
        for xx,n in zip(pos,byte_means):axes[1].text(xx,n+70,f'{n:,.0f}',ha='center',va='bottom',fontsize=12)
        all_missing.extend(missing);all_bytes.extend(byte_means)
    axes[0].set(xticks=x,xticklabels=['20秒中断','120秒中断','360秒中断'],ylim=(0,max(all_missing)+18),
                ylabel='缺失事件 / 条',title='边界对照：缺失事件 / 生成事件')
    axes[1].set(xticks=x,xticklabels=['清洁链路','随机丢失','60秒中断'],ylim=(0,max(all_bytes)*1.25),
                ylabel='平均派发及ACK字节 / B',title='主对照：每次回放的字节开销（含探测）')
    for ax in axes:ax.grid(axis='y',alpha=.15)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.55,.99),ncol=2,frameon=False)
    save(fig,'02_恢复效果与字节开销','补发改善哪些中断条件，又增加了多少主机字节开销？')


if __name__=='__main__':
    m.parameters()
    for name in ['identity','budget','replay']:
        a=json.loads((m.OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    OUT.mkdir(exist_ok=True);timeline();outcomes()
    m.dump('figure_checks.json',dict(figures=CHECKS,plot_script_sha256=m.sha(Path(__file__)),
                                    sources={name:m.sha(m.OUT/name) for name in
                                             ['recovery_example.json','paired_results.csv','boundary_results.csv','replay_acceptance.json']},
                                    scope='Standalone software figures; Word insertion and physical radio not verified'))
    print('Two figures passed font, bounds and text-collision checks.')
