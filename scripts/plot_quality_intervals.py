"""Fourth-round grayscale evidence; no claims of physical measurements."""
from pathlib import Path
import json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_quality_intervals as m
DATA=m.OUT;OUT=ROOT/'deliverables/质量检查与采样间隔图';OUT.mkdir(exist_ok=True)
S=json.loads((DATA/'summary.json').read_text(encoding='utf-8'));P=S['parameters']
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
    'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,'xtick.labelsize':12,'ytick.labelsize':12,
    'svg.fonttype':'none','svg.hashsalt':'quality-interval-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]

def g(stage,scene,sigma,period=1,quality='range',phase=0):
    return next(g for g in S[stage+'_groups'] if g['scene']==scene and g['sigma']==sigma and g['period']==period and g['phase']==phase and g['quality']==quality and g['method']=='hybrid')

def save(fig,name,question):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();spans=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text():continue
        b=t.get_window_extent(renderer)
        assert b.x0>=0 and b.y0>=0 and b.x1<=w and b.y1<=h,(name,t.get_text(),b.bounds)
        assert t.get_fontsize()>=11
        spans.append(dict(text=t.get_text(),box=list(b.bounds),font_pt=t.get_fontsize()))
    for i,a in enumerate(spans):
        x,y,ww,hh=a['box']
        for b in spans[i+1:]:
            xx,yy,www,hhh=b['box']
            assert min(x+ww,xx+www)-max(x,xx)<=1 or min(y+hh,yy+hhh)-max(y,yy)<=1,(name,'text overlap',a['text'],b['text'])
    for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
    svg=OUT/f'{name}.svg';svg.write_text('\n'.join(l.rstrip() for l in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    CHECKS.append(dict(name=name,question=question,text_within_canvas=True,text_collision_check=True,
        minimum_font_pt=min(t['font_pt'] for t in spans),texts=spans,source_summary_sha256=m.sha(DATA/'summary.json'),
        file_sha256={ext:m.sha(OUT/f'{name}.{ext}') for ext in ['png','svg']}))
    plt.close(fig)

def matrix(ax,values,rows,cols,title):
    a=np.array(values);ax.imshow(a,cmap='Greys',vmin=0,vmax=16,aspect='auto')
    for i in range(len(rows)):
        for j in range(len(cols)):ax.text(j,i,str(int(a[i,j])),ha='center',va='center',color='white' if a[i,j]>=10 else '#222',fontsize=12)
    ax.set(yticks=range(len(rows)),yticklabels=rows,xticks=range(len(cols)),xticklabels=cols,title=title)
    ax.set_xticks(np.arange(-.5,len(cols),1),minor=True);ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
    ax.grid(which='minor',color='#ccc',lw=.8);ax.tick_params(which='minor',length=0);ax.tick_params(length=0,pad=8)
    for sp in ax.spines.values():sp.set_visible(False)

def quality():
    fig,axes=plt.subplots(3,1,figsize=(11.8,10.3));fig.subplots_adjust(left=.19,right=.96,bottom=.18,top=.85,hspace=.9)
    scenes=['spike_range','nan_pressure','counter_reset','drift_p0','bias_initial','bad_calibration']
    cols=['250kPa\n单点尖峰','五秒\n压力缺失','流量\n计数复位','量程内\n压力漂移','初始\n压力偏置','标定期\n缺失读数']
    rows=['仅有限值检查','有限值＋量程检查']
    for ax,key,title in zip(axes,['false_trials','quality_flagged_trials','baseline_accepted'],
        ['水路故障模式误报试次 / 16（越小越好）','监测期出现读数质量提示的试次 / 16','初始标定通过数值检查的试次 / 16']):
        matrix(ax,[[g('quality',sc,.3,quality=mode)[key] for sc in scenes] for mode in ['finite','range']],rows,cols,title)
    fig.suptitle('数值质量检查能拦住坏读数，不能证明传感器准确',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.035,'全部为合成数据；指数0.5，σ=0.3kPa，固定1Hz，快速＋有界累积；每组16种子。\n候选压力范围0—200kPa。量程内漂移与偏置没有被识别为读数质量问题。\n标定期缺失读数时不启动诊断，因此零水路告警不能解释为水路正常。',fontsize=12,linespacing=1.5)
    save(fig,'01_质量检查收益与边界','有限值和量程检查具体解决什么、遗漏什么？')

def intervals():
    fig,axes=plt.subplots(2,1,figsize=(11.8,9.4));fig.subplots_adjust(left=.18,right=.96,bottom=.18,top=.85,hspace=.56)
    scenes=['leak_r30','leak_r90','leak_r360','leak_r720','fast_leak_switch']
    labels=['固定1Hz','2秒巡检','5秒巡检']
    matrix(axes[0],[[g('sampling',sc,10.,period)['early'] for sc in scenes] for period in m.PERIODS],labels,
        ['泄漏\n30秒渐变','泄漏\n90秒渐变','泄漏\n360秒渐变','泄漏\n720秒渐变','切换泄漏\n45秒渐变'],
        '高噪声下有效早期检出 / 16（σ=10kPa，越大越好）')
    matrix(axes[1],[[g('sampling',sc,sigma,period)['correct_during_fault'] for sigma in [.3,10.] for sc in ['pulse8','pulse20','pulse40']] for period in m.PERIODS],labels,
        [f'{duration}秒故障\nσ={sigma:g}' for sigma in [.3,10.] for duration in [8,20,40]],
        '短时泄漏：故障仍存在时确认正确模式的试次 / 16')
    fig.suptitle('短巡检间隔仍受观测窗与确认时延约束',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.035,'全部为合成回放；各组16种子，起始偏移0秒，组合算法；其余偏移单列保存。\n上图有效早期须无故障前误报、首次故障后模式正确，且早于模型15%流量偏差参照。\n下图仅计恢复前正确模式确认，未排除故障前误报；它不等同于有效早期或现场准确率。',fontsize=12,linespacing=1.5)
    save(fig,'02_采样间隔与故障时间尺度','减少采样能否兼顾不同渐变速度与短时故障？')

def short_event():
    tr,obs,counts=m.inputs('pulse8',.3,m.TEST[0]);fig,axes=plt.subplots(2,1,figsize=(12,8.4))
    fig.subplots_adjust(left=.12,right=.72,bottom=.20,top=.84,hspace=.65)
    for ax in axes:
        ax.axvspan(360,368,color='#eee');ax.set_xlim(354,390);ax.set_xticks([355,360,365,370,375,380,385]);ax.grid(alpha=.14)
    axes[0].plot(tr['t'],tr['severity']*100,color='#333',lw=1.8,label='真实流量偏差（仅评价）')
    axes[0].axhline(15,color='#888',ls='--',label='模型早期参照 15%')
    axes[0].set(ylabel='相对健康流量偏差 / %',xlabel='时间 / s',title='故障持续360—368秒；此后水路恢复',ylim=(-2,50),yticks=[0,15,30,45])
    axes[0].legend(loc='upper left',bbox_to_anchor=(1.02,1.02),frameon=False,labelspacing=1.4)
    examples=[];seen_event_labels=set()
    for y,period in enumerate(m.PERIODS):
        out=m.replay(obs,counts,P['reference'],P['limits'][str(period)],period,0)
        acq=np.array(out['acquired']);valid=np.array([r['t'] for r in out['records'] if r['valid']])
        axes[1].scatter(acq,np.full(len(acq),y-.16),marker='|',s=70,color='#777',label='实际压力读取' if y==0 else None)
        axes[1].scatter(valid,np.full(len(valid),y+.07),marker='s',s=12,color='#333',label='完整诊断窗' if y==0 else None)
        for code,marker,label in [('leak_pattern','o','泄漏模式确认'),('uncertain','x','不确定模式确认')]:
            ev=[e['t_s'] for e in out['decisions']['hybrid']['events'] if e['pattern']==code]
            if not ev:continue
            axes[1].scatter(ev,np.full(len(ev),y+.33),marker=marker,s=45,color='black',label=label if code not in seen_event_labels else None)
            seen_event_labels.add(code)
        examples.append(dict(period=period,events=out['decisions']['hybrid']['events']))
    axes[1].set(yticks=[0,1,2],yticklabels=['固定1Hz','2秒巡检','5秒巡检'],ylim=(-.5,2.7),xlabel='时间 / s',title='实际读取、完整窗口与模式确认分别记录')
    axes[1].legend(loc='upper left',bbox_to_anchor=(1.02,1.02),frameon=False,labelspacing=1.4)
    fig.suptitle('保留短时故障案例：恢复后的确认不算及时检出',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.045,f'合成8秒泄漏；σ=0.3kPa，指数0.5，首个测试种子{m.TEST[0]}，起始偏移0秒。\n灰色区为故障持续期；这里只展示354—390秒。压力窗口需十个实采点，模式需五帧连续确认。\n真实故障起止和严重程度只用于离线评价，不提供给逐秒程序。',fontsize=12,linespacing=1.5)
    save(fig,'03_八秒故障实采与迟报','巡检、窗口与恢复后的迟报怎样在同一时间轴上核对？')
    m.dump('short_example_events.json',dict(seed=m.TEST[0],scene='pulse8',sigma=.3,examples=examples))

if __name__=='__main__':
    quality();intervals();short_event();m.dump('figure_checks.json',dict(figures=CHECKS,scope='standalone; Word layout not checked'))
    print('Three figures passed automated text bounds and collision checks.')
