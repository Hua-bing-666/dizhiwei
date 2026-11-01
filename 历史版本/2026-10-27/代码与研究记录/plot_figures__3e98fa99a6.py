"""Compact figures with only axes, data, uncertainty and essential keys."""
from pathlib import Path
import json,hashlib,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text

B=Path(__file__).resolve().parents[1];E=B/'evidence';O=B/'figures';O.mkdir(exist_ok=True)
D=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
Z=np.load(E/'trace_data.npz')
X=json.loads((E/'extension_report.json').read_text(encoding='utf-8'))
XZ=np.load(E/'extension_curves.npz')
METHODS=['threshold','guarded_fast','hybrid']
NAMES=['固定门限','稳健门限','累积组合']
COLORS=['#6C7884','#397EAC','#C97B55']
MARKERS=['s','o','^']
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Microsoft YaHei'],
    'font.size':7.2,'axes.labelsize':7.5,'xtick.labelsize':7.2,'ytick.labelsize':7.2,
    'legend.fontsize':7.2,'axes.spines.top':False,'axes.spines.right':False,
    'axes.linewidth':.65,'xtick.major.width':.6,'ytick.major.width':.6,
    'xtick.major.size':2.5,'ytick.major.size':2.5,'axes.labelpad':3,
    'text.color':'#202020','axes.labelcolor':'#202020','xtick.color':'#202020','ytick.color':'#202020',
    'axes.edgecolor':'#202020','axes.grid':False,'axes.unicode_minus':False,
    'lines.solid_capstyle':'round','pdf.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'section8-redraw-v2'})
# Use a single CJK-capable font for complete, consistent labels.
plt.rcParams['font.sans-serif']=['Microsoft YaHei']
RECORDS=[]
def group(scene,sigma,method):
    return next(g for g in D['groups'] if (g['batch'],g['scene'],g['sigma'],g['method'])==('holdout100',scene,sigma,method))
def panel(ax,letter):
    ax.text(-.05/ax.get_position().width,1.045,letter,transform=ax.transAxes,
        ha='left',va='bottom',fontsize=8.5,fontweight='bold')
def save(fig,name,data):
    fig.canvas.draw();r=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();tt=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text():continue
        bb=t.get_window_extent(r)
        if bb.width==0 or bb.height==0:continue
        assert bb.x0>=-.5 and bb.y0>=-.5 and bb.x1<=w+.5 and bb.y1<=h+.5,(name,t.get_text(),bb.bounds,w,h)
        tt.append(dict(text=t.get_text(),pt=t.get_fontsize(),bounds=list(bb.bounds)))
    for ext in ['png','pdf','svg']:
        fig.savefig(O/f'{name}.{ext}',dpi=600,facecolor='white',
            metadata={'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None} if ext=='svg' else None)
    RECORDS.append(dict(name=name,width_mm=float(fig.get_figwidth()*25.4),height_mm=float(fig.get_figheight()*25.4),
        min_font_pt=min(t['pt'] for t in tt),gridlines=False,canvas_check=True,
        text_count=len(tt),texts=tt,data=data,editable_vector_text=True,
        sha256={ext:hashlib.sha256((O/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ['png','pdf','svg']}))
    plt.close(fig)

def comparison():
    fig,axs=plt.subplots(1,3,figsize=(5.7,2.28))
    fig.subplots_adjust(left=.09,right=.985,bottom=.22,top=.76,wspace=.32)
    handles=[Line2D([],[],color=c,marker=m,markersize=3,lw=.85,label=n,markeredgewidth=.55)
        for c,m,n in zip(COLORS,MARKERS,NAMES)]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,1.005),ncol=3,frameon=False,
        columnspacing=1.8,handlelength=1.8,handletextpad=.55)
    data=[]
    for ax,scene,letter,title in zip(axs,['leak','restriction','long_normal'],'abc',['泄漏早期','受限早期','正常误报']):
        for j,(method,c,m) in enumerate(zip(METHODS,COLORS,MARKERS)):
            gg=[group(scene,s,method) for s in [.3,3.,10.]]
            metric='false_trials' if scene=='long_normal' else 'early'
            ci_key='false_ci95' if scene=='long_normal' else 'early_ci95'
            y=np.array([g[metric] for g in gg]);ci=np.array([g[ci_key] for g in gg])*100
            x=np.array([.3,3.,10.])*np.exp((j-1)*.15)
            ax.plot(x,y,color=c,lw=.8,linestyle=['-','-','--'][j],zorder=2)
            ax.errorbar(x,y,yerr=np.maximum(0,np.array([y-ci[:,0],ci[:,1]-y])),color=c,
                fmt=m,markersize=2.8,markeredgewidth=.55,linewidth=.65,capsize=0,
                markerfacecolor='white',zorder=3)
            data.append(dict(scene=scene,method=method,metric=metric,values=y.tolist(),ci95_percent=ci.tolist()))
        ax.set_xscale('log');ax.minorticks_off()
        ax.set(xlim=(.22,13.6),ylim=(-4,106),xticks=[.3,3.,10.],xticklabels=['0.3','3','10'],yticks=[0,50,100])
        if scene!='leak':ax.set_yticklabels([])
        ax.text(.5,1.06,title,transform=ax.transAxes,ha='center',va='bottom',fontsize=7.6)
        panel(ax,letter)
    axs[0].set_ylabel('试次比例 (%)')
    fig.supxlabel('压力噪声 σ (kPa)',x=.54,y=.025,fontsize=7.5)
    save(fig,'图8-2_候选判据对照',data)

def counterexamples():
    fig,axs=plt.subplots(1,2,figsize=(5.7,2.23))
    fig.subplots_adjust(left=.105,right=.975,bottom=.245,top=.80,wspace=.38)
    t=np.arange(601);blue='#397EAC';orange='#C97B55';gray='#9AA0A5'
    data=[]
    def curve(ax,a,color,label):
        low,median,high=np.quantile(a,[.025,.5,.975],axis=0)
        ax.fill_between(t,low,high,color=color,alpha=.13,linewidth=0)
        ax.plot(t,median,color=color,lw=1.1,label=label)
        return median,low,high
    ax=axs[0]
    med,lo,hi=curve(ax,Z['leak_k_3'],blue,'泄漏')
    assert np.array_equal(Z['leak_k_3'],Z['load_k_3'])
    ix=np.array([390,450,510,570])
    ax.plot(t[ix],med[ix],ls='none',marker='o',markersize=3.5,markerfacecolor='white',
        markeredgecolor=orange,markeredgewidth=.8,label='负载')
    ax.axhline(6,color='#7F858A',lw=.7,ls=(0,(3,3)),zorder=0)
    ax.set(ylim=(-3,38),yticks=[0,15,30],ylabel='K 相对变化 (%)')
    ax.legend(loc='lower left',bbox_to_anchor=(-.03,1.005),frameon=False,ncol=2,
        columnspacing=1.25,handlelength=1.65,handletextpad=.45,borderaxespad=0)
    data.append(dict(panel='a',median=med.tolist(),low=lo.tolist(),high=hi.tolist(),load_same_observation=True))
    ax=axs[1]
    for arr,c,label in [(Z['drift_r_3'],blue,'漂移'),(Z['normal_r_3'],gray,'正常')]:
        med,lo,hi=curve(ax,arr,c,label)
        data.append(dict(panel='b',curve=label,median=med.tolist(),low=lo.tolist(),high=hi.tolist()))
    ax.axhline(.6,color='#7F858A',lw=.7,ls=(0,(3,3)),zorder=0)
    ax.set(ylim=(-.55,1.8),yticks=[0,.75,1.5],ylabel=r'$\Delta R$ (kPa min$^2$ L$^{-2}$)')
    ax.legend(loc='lower left',bbox_to_anchor=(-.03,1.005),frameon=False,ncol=2,
        columnspacing=1.25,handlelength=1.65,handletextpad=.45,borderaxespad=0)
    for ax,letter in zip(axs,'ab'):
        ax.set(xlim=(330,600),xticks=[360,480,600]);panel(ax,letter)
    fig.supxlabel('时间 (s)',x=.54,y=.025,fontsize=7.5)
    save(fig,'图8-4_观测歧义与测压漂移',data)

def waveform():
    fig,axs=plt.subplots(1,2,figsize=(5.7,2.28))
    fig.subplots_adjust(left=.105,right=.975,bottom=.235,top=.76,wspace=.34)
    data=[];t=np.arange(601)
    handles=[]
    for scene,c,label in zip(['normal','leak','restriction'],COLORS,['正常','泄漏','受限']):
        handles.append(Line2D([],[],color=c,lw=1.1,label=label))
        for ax,key in zip(axs,['p1','q10']):
            lo,mid,hi=np.quantile(XZ[scene+'_'+key],[.025,.5,.975],axis=0)
            ax.fill_between(t,lo,hi,color=c,alpha=.09,linewidth=0)
            ax.plot(t,mid,color=c,lw=1.0,ls='--' if scene=='normal' else '-')
            data.append(dict(scene=scene,quantity=key,median=mid.tolist(),low=lo.tolist(),high=hi.tolist()))
    axs[0].set(ylim=(55,120),yticks=[60,90,120],ylabel='下游压力 (kPa)')
    axs[1].set(ylim=(2.1,4.0),yticks=[2.2,3.0,3.8],ylabel='流量 (L/min)')
    for ax,letter in zip(axs,'ab'):
        ax.set(xlim=(330,600),xticks=[360,480,600]);panel(ax,letter)
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,1.005),ncol=3,frameon=False,columnspacing=2.)
    fig.supxlabel('时间 (s)',x=.54,y=.025,fontsize=7.5)
    save(fig,'图8-1_水力观测响应',data)

def amplitude():
    fig,axs=plt.subplots(1,2,figsize=(5.7,2.28))
    fig.subplots_adjust(left=.10,right=.975,bottom=.235,top=.76,wspace=.28)
    data=[];xx=np.array([5,10,15,20,30])
    for ax,scene,letter,label in zip(axs,['leak','restriction'],'ab',['泄漏','受限']):
        for sigma,c,m in zip([.3,3.,10.],COLORS,MARKERS):
            gg=[next(g for g in X['amplitude_groups'] if (g['scene'],g['sigma'],g['amplitude'])==(scene,sigma,a)) for a in [.05,.1,.15,.2,.3]]
            y=np.array([g['correct'] for g in gg]);ci=np.array([g['ci95'] for g in gg])*100
            ax.fill_between(xx,ci[:,0],ci[:,1],color=c,alpha=.08,linewidth=0)
            ax.plot(xx,y,color=c,marker=m,markersize=2.6,markerfacecolor='white',markeredgewidth=.6,
                lw=.85,ls='--' if sigma==10 else '-')
            data.append(dict(scene=scene,sigma=sigma,amplitude_percent=xx.tolist(),correct=y.tolist(),ci95_percent=ci.tolist()))
        ax.set(xlim=(3.5,31.5),ylim=(-4,106),xticks=[5,15,30],yticks=[0,50,100])
        ax.text(.5,1.06,label,transform=ax.transAxes,ha='center',va='bottom',fontsize=7.6);panel(ax,letter)
    axs[0].set_ylabel('正确提示 (%)');axs[1].set_yticklabels([])
    fig.legend(handles=[Line2D([],[],color=c,marker=m,lw=.9,markersize=3,label=f'σ = {s:g} kPa') for s,c,m in zip([.3,3.,10.],COLORS,MARKERS)],
        loc='upper center',bbox_to_anchor=(.54,1.005),ncol=3,frameon=False,columnspacing=1.4)
    fig.supxlabel('终值流量偏离 (%)',x=.54,y=.025,fontsize=7.5)
    save(fig,'图8-3_幅值检出边界',data)

def timing():
    rr=list(csv.DictReader((E/'timing_examples.csv').open(encoding='utf-8-sig')))
    fig,axs=plt.subplots(1,2,figsize=(5.7,2.28))
    fig.subplots_adjust(left=.10,right=.975,bottom=.235,top=.76,wspace=.28)
    t=np.arange(601);data=[]
    for ax,scene,letter,label in zip(axs,['leak','restriction'],'ab',['泄漏','受限']):
        sev=XZ['timing_'+scene+'_severity']*100
        ax.plot(t,sev,color='#333333',lw=1.05)
        ax.axhline(15,color='#9AA0A5',lw=.65,ls=(0,(3,3)))
        for method,c,m,size in zip(METHODS,COLORS,MARKERS,[4.6,2.8,3.4]):
            r=next(r for r in rr if r['scene']==scene and r['method']==method)
            assert r['early_valid']=='True'
            event=int(r['first_correct_s'])
            ax.plot(event,sev[event],color=c,marker=m,markersize=size,ls='none',markerfacecolor='white',markeredgewidth=.75)
            data.append(dict(scene=scene,method=method,confirmation_s=event,reference_s=int(r['critical_s']),severity_percent=float(sev[event])))
        ax.set(xlim=(360,510),ylim=(-1,26),xticks=[360,420,480],yticks=[0,10,20])
        ax.text(.5,1.06,label,transform=ax.transAxes,ha='center',va='bottom',fontsize=7.6);panel(ax,letter)
    axs[0].set_ylabel('流量偏离 (%)');axs[1].set_yticklabels([])
    fig.legend(handles=[Line2D([],[],color=c,marker=m,lw=0,markersize=3.4,label=n) for c,m,n in zip(COLORS,MARKERS,NAMES)],
        loc='upper center',bbox_to_anchor=(.54,1.005),ncol=3,frameon=False,columnspacing=1.6)
    fig.supxlabel('时间 (s)',x=.54,y=.025,fontsize=7.5)
    save(fig,'补图S1_首次提示时序',data)

def sampling():
    fig,axs=plt.subplots(1,2,figsize=(5.7,2.28))
    fig.subplots_adjust(left=.105,right=.975,bottom=.235,top=.76,wspace=.35)
    data=[]
    for scene,c,m,label in [('leak',COLORS[1],'o','渐进泄漏'),('fast_leak_switch',COLORS[2],'^','切换期快泄漏')]:
        gg=[next(g for g in X['sampling_groups'] if g['scene']==scene and g['period']==p) for p in [1,2,5]]
        for ax,median,iqr in [(axs[0],'lead_median_s','lead_iqr_s'),(axs[1],'pressure_reads_median','pressure_reads_iqr')]:
            y=np.array([g[median] for g in gg]);q=np.array([g[iqr] for g in gg])
            ax.plot([1,2,5],y,color=c,lw=.85)
            ax.errorbar([1,2,5],y,yerr=np.array([y-q[:,0],q[:,1]-y]),color=c,fmt=m,markersize=3.2,
                markerfacecolor='white',markeredgewidth=.65,lw=.7,capsize=0)
            data.append(dict(scene=scene,quantity=median,values=y.tolist(),iqr=q.tolist()))
    axs[0].set(ylabel='提前量 (s)',ylim=(0,65),yticks=[0,30,60])
    axs[1].set(ylabel='压力读取次数',ylim=(250,490),yticks=[250,350,450])
    for ax,letter in zip(axs,'ab'):
        ax.set(xlim=(.7,5.3),xticks=[1,2,5]);panel(ax,letter)
    fig.legend(handles=[Line2D([],[],color=c,marker=m,lw=.9,markersize=3,label=lab) for c,m,lab in [(COLORS[1],'o','渐进泄漏'),(COLORS[2],'^','切换期快泄漏')]],
        loc='upper center',bbox_to_anchor=(.54,1.005),ncol=2,frameon=False,columnspacing=2.)
    fig.supxlabel('巡航周期 (s)',x=.54,y=.025,fontsize=7.5)
    save(fig,'补图S2_采样响应与读取代价',data)

waveform();comparison();amplitude();counterexamples();timing();sampling()
(E/'figure_checks.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8')
print('Six compact figures exported as 600 dpi PNG and editable PDF/SVG.')
