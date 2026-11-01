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
    save(fig,'图8-1_候选判据对照',data)

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
    save(fig,'图8-2_观测歧义与测压漂移',data)

comparison();counterexamples()
(E/'figure_checks.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8')
print('Two compact figures exported as 600 dpi PNG and editable PDF/SVG.')
