"""Data-first, high-contrast journal plates. No cosmetic data alteration."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.text import Text

B=Path(__file__).resolve().parents[1];E=B/'evidence';O=B/'figures';O.mkdir(exist_ok=True)
sys.path.insert(0,str(B/'code/snapshot'))
import review_diagnosis as initial
D=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
EX=json.loads((E/'extension_report.json').read_text(encoding='utf-8'))
Z=np.load(E/'trace_data.npz');X=np.load(E/'extension_curves.npz')
TRIALS=list(csv.DictReader((E/'paired_method_results.csv').open(encoding='utf-8-sig')))
BLUE='#1467D2';CORAL='#EF5B38';TEAL='#00A183';PURPLE='#8754CB'
INK='#202936';GRAY='#8A95A5';LIGHT='#DCE4EE'
METHODS=['threshold','guarded_fast','hybrid'];NAMES=['固定门限','稳健门限','累积组合']
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei'],
    'font.size':9.0,'axes.labelsize':9.0,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
    'legend.fontsize':8.4,'axes.linewidth':.85,'xtick.major.width':.8,'ytick.major.width':.8,
    'xtick.major.size':3.8,'ytick.major.size':3.8,'axes.spines.top':False,'axes.spines.right':False,
    'axes.grid':False,'axes.unicode_minus':False,'axes.labelpad':6,
    'text.color':INK,'axes.edgecolor':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
    'pdf.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'journal-20261027-v4','lines.solid_capstyle':'round'})
RECORDS=[]
def group(scene,method,sigma=10.):
    return next(g for g in D['groups'] if (g['batch'],g['scene'],g['sigma'],g['method'])==('holdout100',scene,sigma,method))
def panel(ax,letter,title=None):
    ax.text(-.055/ax.get_position().width,1.065,letter,transform=ax.transAxes,fontsize=11,fontweight='bold',va='bottom')
    if title:ax.text(.5,1.065,title,transform=ax.transAxes,ha='center',va='bottom',fontsize=9.5)
def save(fig,name,kind,data):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();texts=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text():continue
        bb=t.get_window_extent(renderer)
        if bb.width==0 or bb.height==0:continue
        assert bb.x0>=-.5 and bb.y0>=-.5 and bb.x1<=w+.5 and bb.y1<=h+.5,(name,t.get_text(),bb.bounds,w,h)
        texts.append(dict(text=t.get_text(),font_pt=t.get_fontsize(),bounds=list(bb.bounds)))
    for ext in ['png','pdf','svg']:
        fig.savefig(O/f'{name}.{ext}',dpi=600,facecolor='white',
            metadata={'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None} if ext=='svg' else None)
    RECORDS.append(dict(name=name,chart_type=kind,width_mm=fig.get_figwidth()*25.4,height_mm=fig.get_figheight()*25.4,
        text_inside_canvas=True,minimum_font_pt=min(t['font_pt'] for t in texts),texts=texts,data=data,
        sha256={ext:hashlib.sha256((O/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ['png','pdf','svg']}))
    plt.close(fig)

def phase_response():
    fig,ax=plt.subplots(figsize=(6.1,3.7));fig.subplots_adjust(left=.125,right=.97,bottom=.18,top=.94)
    t=np.arange(601);sel=(t>=360);data=[]
    # Every path is a paired P/Q observation realization, never shuffled marginals.
    for scene,c in [('leak',BLUE),('restriction',CORAL)]:
        q=X[scene+'_q10'][:,sel];p=X[scene+'_p1'][:,sel]
        for i in range(100):ax.plot(q[i,::2],p[i,::2],color=c,alpha=.035,lw=.65,zorder=1)
        mq=np.median(q,axis=0);mp=np.median(p,axis=0)
        ax.plot(mq,mp,color=c,lw=2.6,zorder=3)
        ax.annotate('',xy=(mq[113],mp[113]),xytext=(mq[83],mp[83]),
            arrowprops=dict(arrowstyle='-|>',lw=1.8,color=c,mutation_scale=13),zorder=4)
        ax.scatter([mq[-1]],[mp[-1]],s=66,facecolor=c,edgecolor='white',linewidth=1.1,zorder=5)
        label='泄漏' if scene=='leak' else '受限'
        xy=(mq[-1]+.055,mp[-1]+1.2) if scene=='leak' else (mq[-1]+.055,mp[-1]-1.)
        ax.text(*xy,label,fontsize=10,ha='left',va='center')
        data.append(dict(scene=scene,t=t[sel].tolist(),q_median=mq.tolist(),p1_median=mp.tolist(),paired_seed_paths=100))
    qh=float(np.median(X['normal_q10'][:,360]));ph=float(np.median(X['normal_p1'][:,360]))
    ax.scatter([qh],[ph],s=48,marker='D',color=INK,edgecolor='white',linewidth=.8,zorder=6)
    ax.text(qh-.01,ph+3.7,'健康起点',ha='center',fontsize=9)
    ax.set(xlim=(2.15,4.08),ylim=(63,117),xticks=[2.2,2.6,3.0,3.4,3.8],yticks=[70,90,110],
        xlabel='十秒计数流量 (L/min)',ylabel='下游压力 (kPa)')
    save(fig,'图8-1_压力流量响应轨迹','paired_response_trajectory',dict(paths=data,healthy=[qh,ph],start_s=360,end_s=600))

def outcomes():
    fig,axs=plt.subplots(1,3,figsize=(6.1,3.2),gridspec_kw={'width_ratios':[1,1,.85]})
    fig.subplots_adjust(left=.15,right=.97,bottom=.21,top=.73,wspace=.25)
    fig.legend(handles=[Patch(facecolor=BLUE,label='有效早期'),Patch(facecolor=CORAL,label='前期误报'),Patch(facecolor=LIGHT,label='其他未满足')],
        loc='upper center',bbox_to_anchor=(.55,.99),ncol=3,frameon=False,columnspacing=1.5,handlelength=1.3)
    data=[]
    for ax,scene,letter,label in zip(axs[:2],['leak','restriction'],'ab',['泄漏','受限']):
        for j,m in enumerate(METHODS):
            g=group(scene,m);prior=g['outcomes'].get('prior_false_alarm',0);early=g['early'];other=100-early-prior
            left=0
            for value,c in [(early,BLUE),(prior,CORAL),(other,LIGHT)]:
                ax.barh(j,value,left=left,height=.57,color=c,edgecolor='white',linewidth=.5)
                if value>=8:ax.text(left+value/2,j,str(value),ha='center',va='center',color='white' if c!=LIGHT else INK,fontsize=9.3,fontweight='bold')
                left+=value
            data.append(dict(scene=scene,method=m,early=early,prior_false=prior,other=other,n=100))
        ax.set(xlim=(0,100),ylim=(2.6,-.6),xticks=[0,50,100],yticks=range(3),yticklabels=NAMES if scene=='leak' else [])
        ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=8)
        panel(ax,letter,label)
    ax=axs[2]
    for j,m in enumerate(METHODS):
        v=group('long_normal',m)['false_trials'];ax.barh(j,v,height=.57,color=CORAL)
        ax.text(v-3 if v>=95 else v+4,j,str(v),ha='right' if v>=95 else 'left',va='center',
            fontsize=9.3,color='white' if v>=95 else INK,fontweight='bold')
        data.append(dict(scene='long_normal',method=m,false_trials=v,n=100))
    ax.set(xlim=(0,100),ylim=(2.6,-.6),xticks=[0,50,100],yticks=range(3),yticklabels=[])
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
    panel(ax,'c','正常误报')
    fig.supxlabel('试次比例 (%)',x=.56,y=.035,fontsize=9)
    save(fig,'图8-2_高噪声试次结局','stacked_outcome_comparison',dict(sigma_kpa=10,groups=data))

def amplitude_matrix():
    fig,axs=plt.subplots(1,2,figsize=(6.1,3.2))
    fig.subplots_adjust(left=.105,right=.85,bottom=.24,top=.80,wspace=.20)
    cmap=LinearSegmentedColormap.from_list('journal_blue',['#F3F7FF','#AFDFF4','#429AD5','#1454AD','#163579'])
    data=[];last=None
    for ax,scene,letter,label in zip(axs,['leak','restriction'],'ab',['泄漏','受限']):
        a=np.array([[next(g for g in EX['amplitude_groups'] if (g['scene'],g['sigma'],g['amplitude'])==(scene,sigma,amp))['correct']
            for amp in [.05,.1,.15,.2,.3]] for sigma in [.3,3.,10.]])
        last=ax.pcolormesh(np.arange(6),np.arange(4),a,cmap=cmap,vmin=0,vmax=100,edgecolors='white',linewidth=1.6,shading='flat')
        for i in range(3):
            for j in range(5):
                if a[i,j]<100:ax.text(j+.5,i+.5,str(a[i,j]),ha='center',va='center',
                    color='white' if a[i,j]>=65 else INK,fontsize=10,fontweight='bold')
        ax.set(xlim=(0,5),ylim=(3,0),xticks=np.arange(5)+.5,xticklabels=['5','10','15','20','30'],
            yticks=np.arange(3)+.5,yticklabels=['0.3','3','10'] if scene=='leak' else [])
        for sp in ax.spines.values():sp.set_visible(False)
        ax.tick_params(axis='both',length=0,pad=7);panel(ax,letter,label)
        data.append(dict(scene=scene,rows_sigma=[.3,3.,10.],columns_amplitude=[.05,.1,.15,.2,.3],correct_percent=a.tolist()))
    axs[0].set_ylabel('压力噪声 σ (kPa)',labelpad=9)
    fig.supxlabel('终值流量偏离 (%)',x=.50,y=.045,fontsize=9)
    cax=fig.add_axes([.885,.26,.018,.52]);cb=fig.colorbar(last,cax=cax,ticks=[0,50,100]);cb.outline.set_visible(False)
    cb.ax.tick_params(length=2.5,pad=3,labelsize=8);cb.set_label('正确提示 (%)',fontsize=8.5,labelpad=5)
    save(fig,'图8-3_离散检出边界','discrete_probability_matrix',data)

def joint_counterexamples():
    points=[]
    for scene in ['normal','leak','load_unknown','drift']:
        t,values,_,_=initial.truth(scene)
        for seed in range(10300,10320):
            obs=values+np.random.default_rng(seed).normal(0,[3.,3.,.02],values.shape)
            if scene=='drift':obs[:,0]+=10*np.clip((t-360)/180,0,1)
            f=initial.classify(obs,'physical')
            points.append(dict(scene=scene,seed=seed,k_relative_percent=float(100*(f['k'][-1]/f['k0']-1)),
                r_residual=float(f['r'][-1]-f['r0']),time_s=600))
    with (E/'joint_counterexample_points.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(points[0]));w.writeheader();w.writerows(points)
    fig,ax=plt.subplots(figsize=(6.1,3.65));fig.subplots_adjust(left=.13,right=.965,bottom=.19,top=.94)
    ax.axvline(6,color='#AEB8C6',lw=.85,ls=(0,(4,4)));ax.axhline(.6,color='#AEB8C6',lw=.85,ls=(0,(4,4)))
    styles=[('normal',GRAY,'o',23),('leak',BLUE,'o',25),('load_unknown',TEAL,'o',65),('drift',PURPLE,'^',32)]
    centers={}
    for scene,c,m,size in styles:
        rr=[r for r in points if r['scene']==scene];xx=[r['k_relative_percent'] for r in rr];yy=[r['r_residual'] for r in rr]
        ax.scatter(xx,yy,s=size,marker=m,facecolors='none' if scene=='load_unknown' else c,
            edgecolors=c if scene=='load_unknown' else 'white',linewidths=.9 if scene=='load_unknown' else .35,
            alpha=.88 if scene=='load_unknown' else .75,zorder=4 if scene=='load_unknown' else 3)
        centers[scene]=[float(np.median(xx)),float(np.median(yy))]
    ax.annotate('正常',xy=centers['normal'],xytext=(7.,-.31),fontsize=9.2,
        arrowprops=dict(arrowstyle='-',color=GRAY,lw=.7))
    ax.annotate('测压漂移',xy=centers['drift'],xytext=(9.5,1.35),fontsize=9.2,
        arrowprops=dict(arrowstyle='-',color=PURPLE,lw=.7))
    ax.annotate('泄漏 / 未知负载',xy=centers['leak'],xytext=(19.,.86),fontsize=9.2,
        arrowprops=dict(arrowstyle='-',color=TEAL,lw=.7))
    ax.set(xlim=(-3,36),ylim=(-.5,1.75),xticks=[0,10,20,30],yticks=[0,.6,1.2],
        xlabel='K 相对变化 (%)',ylabel=r'$\Delta R$ (kPa min$^2$ L$^{-2}$)')
    save(fig,'图8-4_终值特征与观测歧义','paired_terminal_feature_scatter',dict(points=points,centers=centers,pressure_sigma_kpa=3,seed_count=20))

def lead_distribution():
    fig,axs=plt.subplots(1,2,figsize=(6.1,3.35));fig.subplots_adjust(left=.15,right=.94,bottom=.21,top=.82,wspace=.34)
    data=[]
    for ax,scene,c,letter,label in zip(axs,['leak','restriction'],[BLUE,CORAL],'ab',['泄漏','受限']):
        arrays=[]
        for m in METHODS:
            rr=[r for r in TRIALS if r['batch']=='holdout100' and r['scene']==scene and float(r['sigma'])==10 and r['method']==m and r['early_valid']=='True']
            arrays.append(np.array([float(r['lead_s']) for r in rr]))
        vp=ax.violinplot(arrays,positions=range(3),orientation='horizontal',widths=.68,showextrema=False,bw_method=.45,points=100)
        for body in vp['bodies']:body.set_facecolor(c);body.set_edgecolor(c);body.set_alpha(.25);body.set_linewidth(.9)
        for j,(m,vals) in enumerate(zip(METHODS,arrays)):
            q=np.quantile(vals,[.25,.5,.75]);ax.plot([q[0],q[2]],[j,j],color=c,lw=3.3)
            ax.scatter([q[1]],[j],s=17,facecolor='white',edgecolor=c,linewidth=.8,zorder=4)
            ax.text(148,j,f'n={len(vals)}',ha='left',va='center',fontsize=8)
            data.append(dict(scene=scene,method=m,n=len(vals),lead_s=vals.tolist(),q25_q50_q75=q.tolist()))
        ax.set(xlim=(0,178),ylim=(2.6,-.6),xticks=[0,60,120],yticks=range(3),yticklabels=NAMES if scene=='leak' else [])
        ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=8);panel(ax,letter,label)
    fig.supxlabel('有效早期试次的提前量 (s)',x=.55,y=.035,fontsize=9)
    save(fig,'补图S1_提前量分布','conditional_lead_violin',data)

def acquisition_tradeoff():
    fig,ax=plt.subplots(figsize=(6.1,3.6));fig.subplots_adjust(left=.13,right=.96,bottom=.19,top=.94)
    data=[]
    for scene,c,label in [('leak',BLUE,'渐进泄漏'),('fast_leak_switch',CORAL,'切换期快泄漏')]:
        gg=[next(g for g in EX['sampling_groups'] if g['scene']==scene and g['period']==p) for p in [1,2,5]]
        xx=np.array([g['pressure_reads_median'] for g in gg]);yy=np.array([g['lead_median_s'] for g in gg])
        ax.plot(xx,yy,color=c,lw=2.2)
        for j,g in enumerate(gg):
            iq=np.array(g['pressure_reads_iqr']);lq=np.array(g['lead_iqr_s'])
            ax.errorbar(xx[j],yy[j],xerr=[[xx[j]-iq[0]],[iq[1]-xx[j]]],yerr=[[yy[j]-lq[0]],[lq[1]-yy[j]]],
                fmt='o',markersize=6,color=c,markerfacecolor='white' if j==0 else c,markeredgewidth=1.1,lw=.9,capsize=0,zorder=4)
            ax.text(xx[j],yy[j]+4.4,f'{g["period"]} s',ha='center',fontsize=8.5)
        ax.text(xx[-1]-3,yy[-1]-7.8,label,ha='left',va='center',fontsize=9.3)
        data.append(dict(scene=scene,groups=gg))
    ax.set(xlim=(285,505),ylim=(-4,68),xticks=[300,400,500],yticks=[0,30,60],
        xlabel='压力读取次数',ylabel='有效早期提前量 (s)')
    save(fig,'补图S2_采集代价与响应余量','paired_acquisition_tradeoff',data)

phase_response();outcomes();amplitude_matrix();joint_counterexamples();lead_distribution();acquisition_tradeoff()
(E/'figure_checks.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8')
print('Six journal plates exported. Source trials retained; only the visual encodings changed.')
