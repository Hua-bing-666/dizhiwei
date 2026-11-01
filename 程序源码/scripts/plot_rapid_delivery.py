"""Two separately accepted work packages, with grayscale encodings."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_rapid_delivery as m
DATA=m.OUT;OUT=ROOT/'deliverables/快速复核与可靠上报图';OUT.mkdir(exist_ok=True)
S=json.loads((DATA/'attention_summary.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
    'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,'xtick.labelsize':12,'ytick.labelsize':12,
    'svg.fonttype':'none','svg.hashsalt':'rapid-delivery-20261006','axes.spines.top':False,'axes.spines.right':False})
CHECKS=[]
def save(fig,name,question):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();spans=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text():continue
        b=t.get_window_extent(renderer)
        assert b.x0>=0 and b.y0>=0 and b.x1<=w and b.y1<=h,(name,t.get_text())
        assert t.get_fontsize()>=11
        spans.append(dict(text=t.get_text(),box=list(b.bounds),font_pt=t.get_fontsize()))
    for i,a in enumerate(spans):
        x,y,ww,hh=a['box']
        for b in spans[i+1:]:
            xx,yy,www,hhh=b['box']
            assert min(x+ww,xx+www)-max(x,xx)<=1 or min(y+hh,yy+hhh)-max(y,yy)<=1,(name,a['text'],b['text'])
    for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
    svg=OUT/f'{name}.svg';svg.write_text('\n'.join(l.rstrip() for l in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    CHECKS.append(dict(name=name,question=question,text_within_canvas=True,text_collision_check=True,
        minimum_font_pt=min(x['font_pt'] for x in spans),texts=spans,file_sha256={ext:m.sha(OUT/f'{name}.{ext}') for ext in ['png','svg']}))
    plt.close(fig)
def group(scene,sigma,method):return next(g for g in S['groups'] if g['scene']==scene and g['sigma']==sigma and g['method']==method)
def matrix(ax,values,rows,cols,title):
    a=np.array(values);ax.imshow(a,cmap='Greys',vmin=0,vmax=16,aspect='auto')
    for i in range(len(rows)):
        for j in range(len(cols)):ax.text(j,i,str(int(a[i,j])),ha='center',va='center',color='white' if a[i,j]>=10 else '#222',fontsize=12)
    ax.set(yticks=range(len(rows)),yticklabels=rows,xticks=range(len(cols)),xticklabels=cols,title=title)
    ax.set_xticks(np.arange(-.5,len(cols),1),minor=True);ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
    ax.grid(which='minor',color='#ccc',lw=.8);ax.tick_params(which='minor',length=0);ax.tick_params(length=0,pad=8)
    for sp in ax.spines.values():sp.set_visible(False)
def attention():
    methods=['guarded_fast','hybrid','rapid1','rapid3'];labels=['十秒保护快速通道','十秒快速＋累积','一秒窗·复核提示','三秒窗·复核提示']
    fig,axes=plt.subplots(2,1,figsize=(11.4,9.1));fig.subplots_adjust(left=.29,right=.96,bottom=.18,top=.84,hspace=.5)
    matrix(axes[0],[[group('pulse8',s,m)['during'] for s in [.3,3.,10.]] for m in methods],labels,
        ['σ=0.3kPa','σ=3kPa','σ=10kPa'],'8秒泄漏：恢复前出现提示的试次 / 16')
    matrix(axes[1],[[group(sc,10.,m)['early'] for sc in ['leak_r90','leak_r720','fast_leak_switch']] for m in methods],labels,
        ['90秒渐变','720秒渐变','45秒切换渐变'],'高噪声：模型15%参照前有效提示 / 16')
    fig.suptitle('短窗改善短时提示，不能替代主诊断',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.035,'合成模型指数0.5；固定1Hz实采；新种子43000—43015。σ为压力噪声标准差。\n本图统一比较异常提示时机；短窗不确认故障类型，不触发实际阀门。\n下图要求无故障前提示；压力漂移仍可能产生提示，提示本身不能证明水路故障。',fontsize=12,linespacing=1.5)
    save(fig,'01_短窗提示收益与代价','短窗是否改善短时关注，是否在高噪声下牺牲缓变识别？')
def delivery():
    with (DATA/'delivery_results.csv').open(encoding='utf-8') as f:rr=list(csv.DictReader(f))
    strategies=['periodic10','periodic60','event60'];names=['每10秒定期','每60秒定期','事件即时＋60秒状态']
    modes=['clean','loss','outage'];x=np.arange(3);width=.23
    fig,axes=plt.subplots(2,1,figsize=(11.4,8.9));fig.subplots_adjust(left=.12,right=.96,bottom=.18,top=.80,hspace=.55)
    for j,(strategy,name,color,hatch) in enumerate(zip(strategies,names,['#444','#aaa','white'],['','///','..'])):
        avg=[];worst=[]
        for mode in modes:
            r=[v for v in rr if v['strategy']==strategy and v['mode']==mode]
            avg.append(np.mean([int(v['attempts']) for v in r]));worst.append(max(int(v['max_delivery_lag_s']) for v in r))
        for ax,values in zip(axes,[avg,worst]):
            xpos=x+(j-1)*width;ax.bar(xpos,values,width=width,color=color,edgecolor='#555',hatch=hatch,label=name)
            for xx,v in zip(xpos,values):ax.text(xx,v+1.2,f'{v:.1f}' if ax is axes[0] else str(int(v)),ha='center',va='bottom',fontsize=11)
    for ax in axes:
        ax.set_xticks(x,labels=['无丢包','数据丢包20%\nACK丢失25%','180—210秒\n链路中断']);ax.grid(axis='y',alpha=.15)
    axes[0].set(ylabel='发送尝试 / 次',ylim=(0,100),title='同一事件流：发送尝试平均数量（每组12个链路种子）')
    axes[0].legend(loc='lower left',bbox_to_anchor=(0,1.16),ncol=3,frameon=False)
    axes[1].set(ylabel='事件生成至首次入库 / s',ylim=(0,76),title='两条事件在12个种子中的最大首次入库延迟')
    fig.suptitle('采集不变，事件上报缩短等待；丢包仍需缓存与确认',y=.97,fontsize=17,weight='bold')
    fig.text(.07,.03,'完全为软件链路模拟；同一条192秒复核事件与197秒主诊断事件，观察至720秒。\n12个网络种子在策略间复用；无丢包与固定中断场景不受随机数影响。\n仅模拟事件和状态时间戳，不含实际LoRa空中时序、完整传感载荷或能耗。',fontsize=12,linespacing=1.5)
    save(fig,'02_上报次数与入库延迟','事件上报怎样在采集不变的情况下权衡发送数与送达等待？')
if __name__=='__main__':
    attention();delivery();m.dump('figure_checks.json',dict(figures=CHECKS,scope='standalone; Word layout not checked',
        sources={name:m.sha(DATA/name) for name in ['attention_summary.json','delivery_summary.json','delivery_results.csv']}))
    print('Two figures passed text bounds and collision checks.')
