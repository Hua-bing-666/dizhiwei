"""Timing and retry-boundary figures from accepted host checks."""
from pathlib import Path
import csv
import json
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.text import Text

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'));sys.path.insert(0,str(ROOT/'prototype'))
import review_protocol_session as m
from acquisition_timing import nominal_schedule
from session_transport import SessionSender
from compact_protocol import EVENT,Snapshot

DATA=m.OUT;OUT=ROOT/'deliverables/通信帧与采集时序图'
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
                     'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,
                     'xtick.labelsize':12,'ytick.labelsize':12,'svg.fonttype':'none',
                     'svg.hashsalt':'protocol-session-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]


def save(fig,name,question):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();width,height=fig.canvas.get_width_height();spans=[]
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text():continue
        box=text.get_window_extent(renderer)
        assert box.x0>=0 and box.y0>=0 and box.x1<=width and box.y1<=height,(name,text.get_text())
        assert text.get_fontsize()>=11
        spans.append(dict(text=text.get_text(),box=list(box.bounds),font_pt=text.get_fontsize()))
    for i,a in enumerate(spans):
        x,y,w,h=a['box']
        for b in spans[i+1:]:
            xx,yy,ww,hh=b['box']
            assert min(x+w,xx+ww)-max(x,xx)<=1 or min(y+h,yy+hh)-max(y,yy)<=1,(name,a['text'],b['text'])
    for ext in ['png','svg']:
        path=OUT/f'{name}.{ext}'
        fig.savefig(path,dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':path.write_text('\n'.join(s.rstrip() for s in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    CHECKS.append(dict(name=name,question=question,text_within_canvas=True,text_collision_check=True,
                       minimum_font_pt=min(v['font_pt'] for v in spans),texts=spans,
                       file_sha256={ext:m.sha(OUT/f'{name}.{ext}') for ext in ['png','svg']}))
    plt.close(fig)


def timing():
    reads=nominal_schedule(1000,.9,0)
    fig,ax=plt.subplots(figsize=(11.4,4.2));fig.subplots_adjust(left=.16,right=.97,bottom=.22,top=.88)
    for y,read,color in [(2,reads[0],'.82'),(1,reads[1],'.95')]:
        left=read.started_ms-1000;right=read.completed_ms-1000
        ax.add_patch(Rectangle((left,y-.23),right-left,.46,facecolor=color,edgecolor='black',lw=1.1))
        ax.text((left+right)/2,y,'配置·转换·读取',ha='center',va='center')
    ax.axvline(0,color='black',linestyle='--',lw=1)
    ax.errorbar(0,0,xerr=1,fmt='D',color='black',ms=6,capsize=5,label='计数端点及±1ms容差')
    fig.legend(*ax.get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.56,.995),frameon=False)
    ax.set(xlim=(-32,5),ylim=(-.5,2.55),yticks=[0,1,2],yticklabels=['计数锁存','P1转换及读取','P0转换及读取'],
           xticks=[-30,-20,-10,0],xlabel='相对计数端点的时间 / ms')
    ax.grid(axis='x',alpha=.15)
    save(fig,'01_双压力转换与计数端点','双压力怎样依次转换，怎样在一秒计数端点前完成记录？')


def retries():
    schedules={};s=Snapshot(1000,1,7,1,540,12000,11000,6000,0,0x87,0,20,10)
    for policy in ['rapid8','burst_backoff']:
        sender=SessionSender(':memory:',policy=policy);sender.enqueue(EVENT,s.pack()+b'\x01\xff',0)
        schedules[policy]=[t/1000 for t in range(0,108001,1000) if sender.pick(t) is not None];sender.close()
    m.dump('retry_schedule_examples.json',schedules)
    with (DATA/'boundary_results.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    fig,axes=plt.subplots(2,1,figsize=(11.4,7.6));fig.subplots_adjust(left=.18,right=.96,top=.84,bottom=.12,hspace=.60)
    for y,policy,marker in [(1,'rapid8','o'),(0,'burst_backoff','s')]:
        values=schedules[policy];axes[0].plot(values,[y]*len(values),linestyle='-',color='black',lw=1,marker=marker,ms=6,mfc='black' if y else 'white')
    axes[0].set(yticks=[0,1],yticklabels=['快速＋间隔重试','固定快速重试'],ylim=(-.4,1.4),
                xlim=(-2,90),xticks=[0,20,40,60,80],xlabel='事件生成后的时间 / s',title='无确认且无其他排队帧：八次派发时刻')
    axes[0].grid(axis='x',alpha=.15)
    x=np.arange(3);width=.30
    for j,(policy,label,color,hatch) in enumerate([('rapid8','固定快速重试','.45',''),('burst_backoff','快速＋间隔重试','white','///')]):
        values=[];totals=[]
        for duration in [20,120,360]:
            group=[r for r in rows if r['policy']==policy and int(r['outage_seconds'])==duration]
            values.append(sum(int(v['missing_events']) for v in group));totals.append(sum(int(v['generated_events']) for v in group))
        pos=x+(j-.5)*width
        axes[1].bar(pos,values,width=width,color=color,hatch=hatch,edgecolor='black',label=label)
        for xx,value,total in zip(pos,values,totals):axes[1].text(xx,value+2,f'{value}/{total}',ha='center',va='bottom',fontsize=12)
    axes[1].set(xticks=x,xticklabels=['20秒中断','120秒中断','360秒中断'],ylim=(0,88),
                ylabel='缺失事件 / 条',title='新种子边界检查：缺失事件 / 生成事件')
    axes[1].grid(axis='y',alpha=.15)
    fig.legend(*axes[1].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.56,.99),ncol=2,frameon=False)
    save(fig,'02_重试预算与长中断边界','延长重试间隔能否跨过中断，哪些中断长度仍会耗尽预算？')


if __name__=='__main__':
    m.parameters()
    for name in ['codec','session','timing','byte_link']:
        a=json.loads((DATA/f'{name}_acceptance.json').read_text(encoding='utf-8'))
        assert a['passed'] and a['parameters_sha256']==m.sha(DATA/'frozen_parameters.json')
    OUT.mkdir(exist_ok=True);timing();retries()
    m.dump('figure_checks.json',dict(figures=CHECKS,sources={name:m.sha(DATA/name) for name in
                                                          ['timing_results.csv','boundary_results.csv','retry_schedule_examples.json','byte_link_acceptance.json']},
                                     scope='Standalone host-simulation diagrams; Word/physical timing not checked'))
    print('Two protocol/timing figures passed font, bounds and text-collision checks.')
