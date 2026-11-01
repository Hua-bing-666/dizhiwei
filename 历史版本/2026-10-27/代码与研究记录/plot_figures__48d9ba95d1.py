"""Nature-inspired scientific figures, native print dimensions; no invented data."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.colors import LinearSegmentedColormap

B=Path(__file__).resolve().parents[1]; E=B/'evidence'; O=B/'figures';O.mkdir(exist_ok=True)
D=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
Z=np.load(E/'trace_data.npz');R=list(csv.DictReader((E/'paired_method_results.csv').open(encoding='utf-8-sig')))
C=['#0072B2','#009E73','#D55E00'];GRAY='#69747C';BLACK='#252B30'
METHODS=['threshold','guarded_fast','hybrid'];NAMES=['固定门限','稳健门限','稳健＋累积'];MARKERS=['s','o','^']
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei'],
    'axes.unicode_minus':False,'font.size':8.2,'axes.labelsize':8.2,'axes.titlesize':9,
    'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':7.8,'axes.linewidth':.65,
    'xtick.major.width':.65,'ytick.major.width':.65,'xtick.major.size':3,'ytick.major.size':3,
    'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':BLACK,'text.color':BLACK,
    'axes.labelcolor':BLACK,'xtick.color':BLACK,'ytick.color':BLACK,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'path','savefig.facecolor':'white',
    'svg.hashsalt':'section8-20261027','lines.solid_capstyle':'round'})
RECORDS=[]
def clean(ax):
    ax.set_axisbelow(True);ax.grid(axis='y',color='#E8ECEF',linewidth=.45)
def title(ax,letter,s):
    ax.set_title(s,loc='left',pad=9,fontweight='normal')
    ax.text(-.055/ax.get_position().width,1.055,letter,transform=ax.transAxes,fontsize=11,fontweight='bold',va='bottom')
def key():
    return [Line2D([],[],color=c,marker=m,lw=1.1,markersize=4,label=n) for c,m,n in zip(C,MARKERS,NAMES)]
def group(scene,sigma,method):
    return next(g for g in D['groups'] if (g['batch'],g['scene'],g['sigma'],g['method'])==('holdout100',scene,sigma,method))
def save(fig,name,description):
    fig.canvas.draw();rend=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height()
    texts=[]
    for item in fig.findobj(Text):
        if not item.get_visible() or not item.get_text():continue
        bb=item.get_window_extent(rend)
        if bb.width==0 or bb.height==0:continue
        assert bb.x0>=-.5 and bb.y0>=-.5 and bb.x1<=w+.5 and bb.y1<=h+.5,(name,item.get_text(),bb.bounds,w,h)
        texts.append(dict(text=item.get_text(),pt=item.get_fontsize(),bounds=list(bb.bounds)))
    for ext in ['png','pdf','svg']:
        fig.savefig(O/f'{name}.{ext}',dpi=600,metadata={'Creator':'Reproducible Section 8 simulation'} if ext=='pdf' else None)
    RECORDS.append(dict(name=name,description=description,size_mm=(fig.get_size_inches()*25.4).tolist(),
        raster_dpi=600,min_font_pt=min(t['pt'] for t in texts),text_within_canvas=True,texts=texts,
        output_sha256={ext:hashlib.sha256((O/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ['png','pdf','svg']}))
    plt.close(fig)

def comparison():
    fig,axes=plt.subplots(2,2,figsize=(5.7,4.45))
    fig.subplots_adjust(left=.125,right=.97,bottom=.11,top=.87,wspace=.45,hspace=.68)
    fig.legend(handles=key(),loc='upper center',bbox_to_anchor=(.54,.995),ncol=3,frameon=False,columnspacing=1.25)
    for ax,scene,letter,label in zip(axes[0],['leak','restriction'],['a','b'],['渐进泄漏','局部受限']):
        for j,(method,c,m) in enumerate(zip(METHODS,C,MARKERS)):
            gg=[group(scene,s,method) for s in [.3,3.,10.]];x=np.arange(3)+(j-1)*.21
            y=np.array([g['early'] for g in gg]);ci=np.array([g['early_ci95'] for g in gg])*100
            ax.errorbar(x,y,yerr=np.maximum(0,np.array([y-ci[:,0],ci[:,1]-y])),fmt=m,color=c,
                markersize=4.4,lw=.9,capsize=2,markeredgewidth=.7,markerfacecolor='white',zorder=3+j)
        ax.set(xticks=range(3),xticklabels=['0.3','3','10'],xlim=(-.5,2.5),ylim=(-3,105),yticks=[0,25,50,75,100],
            xlabel='压力噪声 σ / kPa',ylabel='有效早期 / %')
        clean(ax);title(ax,letter,label)
    ax=axes[1,0];a=np.array([[group('long_normal',s,m)['false_trials'] for s in [.3,3.,10.]] for m in METHODS])
    cmap=LinearSegmentedColormap.from_list('misfires',['#F2F6F9','#7EACC7','#215D81'])
    ax.imshow(a,cmap=cmap,vmin=0,vmax=100,aspect='auto',extent=(-.5,2.5,2.5,-.5))
    for i in range(3):
        for j in range(3):ax.text(j,i,f'{a[i,j]}/100',ha='center',va='center',fontsize=8,color='white' if a[i,j]>60 else BLACK)
    ax.set(xticks=range(3),xticklabels=['0.3','3','10'],yticks=range(3),yticklabels=NAMES,
        xlabel='压力噪声 σ / kPa')
    ax.tick_params(axis='y',length=0,pad=4,labelsize=7.6);ax.tick_params(axis='x',length=0)
    ax.spines['left'].set_visible(False);ax.spines['bottom'].set_visible(False)
    title(ax,'c','长时正常误报试次')
    ax=axes[1,1]
    for j,(method,c,m) in enumerate(zip(METHODS,C,MARKERS)):
        gg=[group(scene,10.,method) for scene in ['leak','restriction']]
        y=np.array([g['median_lead_s'] for g in gg]);qq=np.array([g['lead_q25_q75'] for g in gg])
        ax.errorbar(np.arange(2)+(j-1)*.21,y,yerr=np.array([y-qq[:,0],qq[:,1]-y]),fmt=m,color=c,
            markersize=4.4,lw=.9,capsize=2,markeredgewidth=.7,markerfacecolor='white')
    ax.set(xticks=[0,1],xticklabels=['泄漏','受限'],xlim=(-.5,1.5),ylim=(0,130),yticks=[0,30,60,90,120],ylabel='提前量 / s')
    ax.text(.5,-.32,'σ = 10 kPa，仅有效早期试次',transform=ax.transAxes,ha='center',fontsize=7.5)
    clean(ax);title(ax,'d','提前量中位数与四分位距')
    save(fig,'图8-1_候选判据扩展验证','100 new noise seeds per stratum. Wilson 95% intervals for early proportions; long-normal false counts; conditional lead median and IQR.')

def counterexamples():
    fig,axes=plt.subplots(2,1,figsize=(5.7,3.9))
    fig.subplots_adjust(left=.15,right=.975,bottom=.12,top=.90,hspace=.92)
    t=np.arange(601)
    def envelope(ax,arr,c,label):
        lo,med,hi=np.quantile(arr,[.025,.5,.975],axis=0)
        ax.fill_between(t,lo,hi,color=c,alpha=.15,linewidth=0)
        ax.plot(t,med,color=c,lw=1.25,label=label);return med
    ax=axes[0];med=envelope(ax,Z['leak_k_3'],C[0],'等效泄漏')
    assert np.array_equal(Z['leak_k_3'],Z['load_k_3'])
    ids=np.arange(330,601,15);ax.plot(t[ids],med[ids],ls='none',marker='o',markersize=3.5,markerfacecolor='white',
        markeredgecolor=C[2],markeredgewidth=.85,label='未知正常负载')
    ax.axhline(6,color=GRAY,lw=.85,ls=(0,(4,3)),label='6%门限')
    ax.set(xlim=(330,600),ylim=(-5,41),yticks=[0,10,20,30,40],ylabel='K 相对参照变化 / %',xlabel='模型时间 / s')
    ax.legend(loc='upper left',frameon=False,ncol=3,columnspacing=.9,handlelength=1.5,bbox_to_anchor=(0,1.02))
    title(ax,'a','负载变化与泄漏具有相同观测')
    ax=axes[1];envelope(ax,Z['drift_r_3'],C[2],'上游压力漂移')
    envelope(ax,Z['normal_r_3'],C[0],'无漂移对照')
    ax.axhline(.6,color=GRAY,lw=.85,ls=(0,(4,3)),label='0.6 门限')
    ax.set(xlim=(330,600),ylim=(-.55,1.8),yticks=[0,.5,1.,1.5],ylabel='ΔR / [kPa/(L/min)²]',xlabel='模型时间 / s')
    ax.legend(loc='upper left',frameon=False,ncol=3,columnspacing=.9,handlelength=1.5,bbox_to_anchor=(0,1.02))
    title(ax,'b','真实阻力未变，压力漂移仍可越限')
    for ax in axes:
        ax.set_xticks([360,420,480,540,600]);ax.axvline(360,color='#B0BAC1',lw=.7,ls=':');clean(ax)
    save(fig,'图8-2_负载歧义与漂移反例','Initial K/R model, 20 original seeds, sigma=3 kPa. Median and central 95% noise-draw envelope; not a confidence interval for the mean.')

def traces():
    fig,axes=plt.subplots(2,2,figsize=(6.7,4.6))
    fig.subplots_adjust(left=.105,right=.975,bottom=.105,top=.91,hspace=.60,wspace=.36)
    for col,(scene,name) in enumerate([('leak','渐进泄漏'),('restriction','局部受限')]):
        stem=f'{scene}_10';severity=Z[stem+'_severity']*100;t=np.arange(len(severity));ax=axes[0,col]
        ax.plot(t,severity,color=BLACK,lw=1.2,label='模型流量偏离')
        ax.axhline(15,color=GRAY,lw=.8,ls='--');critical=int(np.flatnonzero(severity>=15)[0])
        ax.axvline(critical,color=GRAY,lw=.8,ls=':')
        for j,(method,c,m) in enumerate(zip(METHODS,C,MARKERS)):
            rr=next(r for r in R if r['batch']=='holdout100' and r['scene']==scene and float(r['sigma'])==10 and int(r['seed'])==61000 and r['method']==method)
            tt=int(rr['first_correct_s']) if rr['first_correct_s'] else None
            if tt is not None:ax.scatter(tt,severity[tt],s=22,marker=m,edgecolor=c,facecolor='white',linewidth=.8,zorder=3)
        ax.text(.03,.93,f'15%参照：{critical} s',transform=ax.transAxes,va='top',fontsize=8)
        ax.set(xlim=(330,550),xticks=[350,400,450,500,550],ylim=(-1,34),xlabel='模型时间 / s',ylabel='流量偏离 / %');clean(ax);title(ax,'ab'[col],name)
        x=Z[stem+'_features'];j=0 if scene=='leak' else 1
        scale=100 if j==0 else 1;ax=axes[1,col]
        ax.plot(x[:,0],x[:,j+1]*scale,color=C[0],lw=1.,label='残差')
        ax.axhline([.06,.6][j]*scale,color=C[0],ls=(0,(4,3)),lw=.85,label='固定门限')
        ax.axhline(Z[stem+'_thresholds'][j]*scale,color=C[1],ls=(0,(2,2)),lw=1.,label='稳健门限')
        ax.set(xlim=(130,550),xticks=[150,250,350,450,550],xlabel='模型时间 / s',ylabel='相对流量残差 / %' if j==0 else '阻力残差 / [kPa/(L/min)²]')
        clean(ax);title(ax,'cd'[col],'同一因果窗口的残差与门限')
        ax.legend(frameon=False,loc='upper left',fontsize=7)
    fig.legend(handles=key(),loc='upper center',bbox_to_anchor=(.53,1.0),ncol=3,frameon=False)
    save(fig,'补图S1_高噪声时序与门限','Predeclared first holdout seed=61000; sigma=10 kPa; markers are first correct confirmations, not proof of valid early outcome.')

comparison();counterexamples();traces()
(E/'figure_checks.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8')
print('Three figures exported as 600 dpi PNG, vector PDF and outlined SVG.')
