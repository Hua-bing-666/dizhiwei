"""Admission illustrations and paired effects; gray-scale host evidence."""
from pathlib import Path
import csv
import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_event_admission as m
OUT=ROOT/'deliverables/事件优先与遥测保留图'
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
                     'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,
                     'xtick.labelsize':12,'ytick.labelsize':12,'svg.fonttype':'none',
                     'svg.hashsalt':'event-admission-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]


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
    CHECKS.append(dict(name=name,question=question,minimum_font_pt=min(v['font_pt'] for v in spans),
                       text_within_canvas=True,text_collision_check=True,texts=spans,
                       file_sha256={ext:m.sha(OUT/f'{name}.{ext}') for ext in ['png','svg']}))
    plt.close(fig)


def capacity():
    data=json.loads((m.OUT/'queue_example.json').read_text(encoding='utf-8'));steps=data['steps']
    x=np.arange(len(steps));events=[r['events'] for r in steps];telemetry=[r['telemetry'] for r in steps]
    fig,ax=plt.subplots(figsize=(11.6,4.6));fig.subplots_adjust(left=.12,right=.97,bottom=.23,top=.80)
    ax.bar(x,events,.52,color='.50',edgecolor='black',label='事件')
    ax.bar(x,telemetry,.52,bottom=events,color='white',hatch='...',edgecolor='black',label='普通遥测')
    ax.axhline(data['capacity'],color='black',ls='--',lw=1,label='示例容量：4')
    for xx,r in zip(x,steps):
        if not r['accepted']:ax.plot(xx,data['capacity']+.30,marker='x',color='black',ms=8,ls='none')
    handles,labels=ax.get_legend_handles_labels()
    handles.append(Line2D([],[],color='black',marker='x',ls='none'));labels.append('本次请求被拒绝')
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.55,.99),ncol=4,frameon=False)
    ax.set(xticks=x,xticklabels=[('事件' if r['kind']==1 else '遥测')+str(r['source_seq']) for r in steps],
           ylim=(0,4.9),yticks=[0,1,2,3,4],ylabel='待确认业务记录 / 条',xlabel='按顺序提交的业务请求')
    ax.grid(axis='y',alpha=.12)
    save(fig,'01_事件接纳与遥测让位','满队列时谁保留、谁退出，拒绝之后队列是否仍保存原事件？')


def effects():
    with (m.OUT/'paired_results.csv').open(encoding='utf-8') as f:regression=list(csv.DictReader(f))
    with (m.OUT/'holdout_results.csv').open(encoding='utf-8') as f:holdout=list(csv.DictReader(f))
    conditions=[([r for r in regression if r['dataset']=='holdout_results.csv' and r['mode']=='ack_blackout'],'49000系列\nACK全丢'),
                ([r for r in holdout if r['mode']=='ack_blackout'],'50000系列\nACK全丢'),
                ([r for r in regression if r['dataset']=='boundary_results.csv' and r['outage_seconds']=='360'],'47000系列\n360秒中断')]
    fig,axes=plt.subplots(2,1,figsize=(11.6,8.1));fig.subplots_adjust(left=.14,right=.97,bottom=.14,top=.84,hspace=.74)
    x=np.arange(3);width=.30;all_missing=[];all_bytes=[]
    for j,(policy,label,color,hatch) in enumerate([('bounded_recovery','上轮有界恢复','.45',''),('event_priority','事件优先＋最新遥测','white','///')]):
        missing=[];totals=[];cost=[]
        for rows,_ in conditions:
            group=[r for r in rows if r['policy']==policy]
            missing.append(sum(int(r['missing_events']) for r in group));totals.append(sum(int(r['generated_events']) for r in group))
            cost.append(sum(int(r['attempted_uart_bytes_including_ack']) for r in group)/len(group))
        pos=x+(j-.5)*width
        axes[0].bar(pos,missing,width,color=color,hatch=hatch,edgecolor='black',label=label)
        axes[1].bar(pos,cost,width,color=color,hatch=hatch,edgecolor='black')
        for xx,n,total in zip(pos,missing,totals):axes[0].text(xx,n+1.3,f'{n}/{total}',ha='center',va='bottom',fontsize=12)
        for xx,n in zip(pos,cost):axes[1].text(xx,n+200,f'{n:,.0f}',ha='center',va='bottom',fontsize=12)
        all_missing.extend(missing);all_bytes.extend(cost)
    labels=[label for _,label in conditions]
    axes[0].set(xticks=x,xticklabels=labels,ylim=(0,max(all_missing)+12),ylabel='缺失事件 / 条',title='缺失事件 / 生成事件')
    axes[1].set(xticks=x,xticklabels=labels,ylim=(0,max(all_bytes)*1.23),ylabel='平均派发及ACK字节 / B',title='同一条件下的平均字节开销（含探测）')
    for ax in axes:ax.grid(axis='y',alpha=.12)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.55,.99),ncol=2,frameon=False)
    save(fig,'02_事件缺失与通信取舍','接纳策略能减少哪些缺失，通信开销和长中断的限制是什么？')


if __name__=='__main__':
    m.parameters()
    for name in ['admission','storage','replay']:
        a=json.loads((m.OUT/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==m.sha(m.OUT/'frozen_parameters.json')
    OUT.mkdir(exist_ok=True);capacity();effects()
    m.dump('figure_checks.json',dict(figures=CHECKS,plot_script_sha256=m.sha(Path(__file__)),
                                    sources={name:m.sha(m.OUT/name) for name in ['queue_example.json','paired_results.csv','holdout_results.csv','replay_acceptance.json']},
                                    scope='Standalone logical and synthetic evidence; not Word or physical radio acceptance'))
    print('Two admission figures passed font, bounds and text-collision checks.')
