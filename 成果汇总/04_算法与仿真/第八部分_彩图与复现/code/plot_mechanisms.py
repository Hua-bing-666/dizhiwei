"""Reference-led scientific plots, rebuilt from frozen observations and models.

No smoothing beyond the protocol's causal ten-sample mean. No selected seed search.
The first original seed 10300 is fixed for all illustrative trajectories.
"""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text

B=Path(__file__).resolve().parents[1];E=B/'evidence';O=B/'figures'
sys.path.insert(0,str(B/'code/snapshot'))
import review_diagnosis as d
D=json.loads((E/'simulation_report.json').read_text(encoding='utf-8'))
EX=json.loads((E/'extension_report.json').read_text(encoding='utf-8'))
TRIALS=list(csv.DictReader((E/'paired_method_results.csv').open(encoding='utf-8-sig')))
BLUE='#2B648D';RED='#D65A55';GREEN='#54836B';INK='#272D32';GRAY='#8B9196';FAINT='#EFF1F2'
METHODS=['threshold','guarded_fast','hybrid'];NAMES=['固定门限','稳健门限','累积组合']
COLORS=[GRAY,BLUE,RED]
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Microsoft YaHei'],
 'font.size':9.1,'axes.labelsize':9.5,'xtick.labelsize':8.7,'ytick.labelsize':8.7,
 'legend.fontsize':8.8,'axes.linewidth':.8,'xtick.major.width':.75,'ytick.major.width':.75,
 'xtick.major.size':3.3,'ytick.major.size':3.3,'axes.spines.top':False,'axes.spines.right':False,
 'axes.grid':False,'axes.unicode_minus':False,'axes.labelpad':6,
 'text.color':INK,'axes.edgecolor':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
 'pdf.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'mechanisms-20261027','lines.solid_capstyle':'round'})
RECORDS=[];RAW={};ILL={}
def save(fig,name,kind,data):
 fig.canvas.draw();ren=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();texts=[]
 for txt in fig.findobj(Text):
  if not txt.get_visible() or not txt.get_text():continue
  bb=txt.get_window_extent(ren)
  if bb.width==0 or bb.height==0:continue
  assert bb.x0>=-.6 and bb.y0>=-.6 and bb.x1<=w+.6 and bb.y1<=h+.6,(name,txt.get_text(),bb.bounds,w,h)
  texts.append(dict(text=txt.get_text(),font_pt=txt.get_fontsize(),bounds=list(bb.bounds)))
 for ext in ['png','pdf','svg']:
  fig.savefig(O/f'{name}.{ext}',dpi=600,facecolor='white',metadata={'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None} if ext=='svg' else None)
 RECORDS.append(dict(name=name,type=kind,width_mm=fig.get_figwidth()*25.4,height_mm=fig.get_figheight()*25.4,
   minimum_font_pt=min(t['font_pt'] for t in texts),all_text_inside=True,texts=texts,data=data,
   sha256={ext:hashlib.sha256((O/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ['png','pdf','svg']}))
 plt.close(fig)
def letter(ax,s):ax.text(-.105,1.04,s,transform=ax.transAxes,fontsize=11,fontweight='bold',va='bottom')
def replay(scene,sigma=3.,seed=10300):
 t,truth,healthy,severity=d.truth(scene)
 obs=truth+np.random.default_rng(seed).normal(0,[sigma,sigma,.02],truth.shape)
 if scene=='drift':obs[:,0]+=10*np.clip((t-360)/180,0,1)
 f=d.classify(obs,'physical');m=d.evaluate(scene,f,severity)
 for key,a in [('truth',truth),('observed',obs),('mean',f['mean']),('k',f['k']),('r',f['r']),('severity',severity)]:RAW[f'{scene}_{key}']=a
 ILL[scene]=dict(seed=seed,pressure_sigma_kpa=sigma,k0=f['k0'],r0=f['r0'],**m)
 return t,obs,f,m
REPLAYS={s:replay(s) for s in ['leak','restriction','load_unknown','drift']}
assert np.array_equal(RAW['leak_observed'],RAW['load_unknown_observed'])

def time_plate(scene,name):
 t,obs,f,m=REPLAYS[scene];fig,axs=plt.subplots(3,1,figsize=(6.65,5.15),sharex=True,
    gridspec_kw={'height_ratios':[1.15,1,1]})
 fig.subplots_adjust(left=.13,right=.875,bottom=.105,top=.88,hspace=.31)
 for ax,s in zip(axs,'abc'):
  ax.axvspan(360,540,color=FAINT,zorder=0);ax.set_xlim(0,600);letter(ax,s)
 ax=axs[0]
 # Raw pressure is deliberately omitted; the displayed estimate is exactly the protocol mean.
 ax.plot(t,f['mean'][:,0],color=BLUE,lw=1.35,label=r'$P_0$ 支管入口')
 ax.plot(t,f['mean'][:,1],color=RED,lw=1.35,label=r'$P_1$ 下游')
 right=ax.twinx();right.spines['top'].set_visible(False);right.spines['right'].set_visible(True)
 right.plot(t,f['mean'][:,2],color=GREEN,lw=1.5)
 right.set_ylabel('流量 (L/min)',color=GREEN,labelpad=5);right.tick_params(axis='y',colors=GREEN)
 if scene=='leak':ax.set(ylim=(94,123),yticks=[100,110,120]);right.set(ylim=(2.55,4.15),yticks=[3,3.5,4])
 else:ax.set(ylim=(60,125),yticks=[70,90,110]);right.set(ylim=(2.1,3.25),yticks=[2.2,2.6,3.0])
 ax.set_ylabel('压力 (kPa)')
 fig.legend(handles=[Line2D([],[],color=BLUE,lw=1.5,label=r'$P_0$ 支管入口'),
  Line2D([],[],color=RED,lw=1.5,label=r'$P_1$ 下游'),Line2D([],[],color=GREEN,lw=1.5,label=r'$Q$ 流量')],
  loc='upper center',bbox_to_anchor=(.51,.985),ncol=3,frameon=False,columnspacing=1.7,handlelength=2.)
 k=100*(f['k']/f['k0']-1);r=f['r']-f['r0']
 axs[1].axhline(6,color=BLUE,lw=.8,ls=(0,(4,3)));axs[1].plot(t,k,color=BLUE,lw=1.55)
 axs[1].set_ylabel('K 相对变化 (%)');axs[1].set(ylim=(-8,36 if scene=='leak' else 8),yticks=[0,15,30] if scene=='leak' else [-6,0,6])
 axs[1].text(12,7,'+6%',color=BLUE,va='bottom',fontsize=8.5)
 axs[2].axhline(.6,color=RED,lw=.8,ls=(0,(4,3)));axs[2].plot(t,r,color=RED,lw=1.4)
 axs[2].set_ylabel(r'$\Delta R$ (kPa min$^2$ L$^{-2}$)')
 axs[2].set(ylim=(-.8,1.0) if scene=='leak' else (-.8,8.0),yticks=[-.6,0,.6] if scene=='leak' else [0,3,6])
 axs[2].text(12,.65,'+0.6',color=RED,va='bottom',fontsize=8.5)
 confirm=m['first_correct_s'];critical=m['critical_s'];target=axs[1] if scene=='leak' else axs[2]
 for ax in axs:
  ax.axvline(confirm,color=INK,lw=.85,ls=(0,(1.5,2.8)))
  ax.axvline(critical,color=GRAY,lw=.85,ls=(0,(5,3)))
 target.annotate('',xy=(critical,.73),xytext=(confirm,.73),xycoords=('data','axes fraction'),
   arrowprops=dict(arrowstyle='<->',color=INK,lw=.8,shrinkA=0,shrinkB=0))
 target.text((confirm+critical)/2,.80,f'提前 {critical-confirm} s',transform=target.get_xaxis_transform(),ha='center',fontsize=9)
 axs[2].set_xlabel('时间 (s)');axs[2].set_xticks([0,120,240,360,480,600])
 save(fig,name,'three_channel_temporal_evidence',dict(scene=scene,**ILL[scene],confirm_s=confirm,reference_s=critical,
   lead_s=critical-confirm,display='causal ten-sample channel means; no extra visual smoothing',fault_start_s=360,fault_end_s=540))

def feature_plane():
 fig,ax=plt.subplots(figsize=(6.65,4.45));fig.subplots_adjust(left=.145,right=.97,bottom=.16,top=.84)
 from matplotlib.patches import Rectangle
 ax.add_patch(Rectangle((.925,-.72),1.06-.925,.6+.72,facecolor=FAINT,edgecolor='none',zorder=0))
 ax.axvline(1.06,color=GRAY,lw=.75,ls=(0,(4,3)))
 ax.axhline(.6,color=GRAY,lw=.75,ls=(0,(4,3)))
 paths=[]
 # Both overlapping scenarios have the identical full one-second path.
 # A thick pale leak path under a narrower dashed load path exposes coincidence honestly.
 for scene,color,ls,lw,alpha in [('leak',RED,'-',3.7,.64),('load_unknown',BLUE,(0,(4,2.5)),1.25,1),('drift',GREEN,'-',1.55,1)]:
  t,obs,f,m=REPLAYS[scene];sel=t>=360;x=f['k'][sel]/f['k0'];y=f['r'][sel]-f['r0']
  ax.plot(x,y,color=color,ls=ls,lw=lw,alpha=alpha,zorder=3)
  paths.append(dict(scene=scene,t=t[sel].tolist(),k_ratio=x.tolist(),delta_r=y.tolist()))
  if scene!='load_unknown':ax.scatter(x[-1],y[-1],s=30,facecolor=color,edgecolor='white',lw=.65,zorder=4)
 ax.scatter([REPLAYS['leak'][2]['k'][360]/REPLAYS['leak'][2]['k0']],
  [REPLAYS['leak'][2]['r'][360]-REPLAYS['leak'][2]['r0']],marker='o',s=22,color=INK,edgecolor='white',lw=.5,zorder=5)
 ax.text(1.235,.42,'泄漏与未知负载重合',color=BLUE,ha='center',fontsize=9)
 f=REPLAYS['drift'][2];xy=(f['k'][-1]/f['k0'],f['r'][-1]-f['r0'])
 ax.annotate('测压漂移越过 R 门限',xy=xy,xytext=(1.075,1.43),fontsize=9,
  arrowprops=dict(arrowstyle='-',color=GREEN,lw=.75))
 ax.text(1.325,.64,'+0.6',color=GRAY,ha='right',fontsize=8.5)
 ax.set(xlim=(.925,1.345),ylim=(-.72,1.72),xticks=[.95,1.05,1.15,1.25],yticks=[-.6,0,.6,1.2],
  xlabel=r'$K/K_0$',ylabel=r'$\Delta R$ (kPa min$^2$ L$^{-2}$)')
 fig.legend(handles=[Line2D([],[],color=RED,lw=3.5,alpha=.64,label='渐进泄漏'),
  Line2D([],[],color=BLUE,lw=1.4,ls='--',label='未知负载'),Line2D([],[],color=GREEN,lw=1.6,label='测压漂移')],
  loc='upper center',bbox_to_anchor=(.54,.985),ncol=3,frameon=False,columnspacing=1.9)
 save(fig,'图8-2_特征轨迹与诊断歧义','paired_feature_trajectories',dict(paths=paths,seed=10300,sigma_kpa=3.,
  coincident_observation_max_error=0.,time_s=[360,600],subsampling=False))

def comparison():
 fig,axs=plt.subplots(1,3,figsize=(6.65,2.65),sharey=True)
 fig.subplots_adjust(left=.16,right=.965,bottom=.22,top=.80,wspace=.25)
 records=[]
 for ax,scene,title,ltr in zip(axs,['leak','restriction','long_normal'],['泄漏有效早期','受限有效早期','正常误报'],'abc'):
  for j,(method,c) in enumerate(zip(METHODS,COLORS)):
   g=next(g for g in D['groups'] if (g['batch'],g['scene'],g['sigma'],g['method'])==('holdout100',scene,10.,method))
   value=g['false_trials'] if scene=='long_normal' else g['early'];ci=np.array(g['false_ci95'] if scene=='long_normal' else g['early_ci95'])*100
   ax.errorbar(value,j,xerr=[[max(0,value-ci[0])],[max(0,ci[1]-value)]],fmt='o',ms=6.5,color=c,lw=1.25,capsize=3,mew=.9,zorder=3)
   ax.text(value-4 if value>=80 else value+5,j-.19,f'{value}%',ha='right' if value>=80 else 'left',fontsize=9,color=c)
   records.append(dict(scene=scene,method=method,n=100,k=value,ci95_percent=ci.tolist()))
  ax.set(xlim=(-3,105),ylim=(2.5,-.65),xticks=[0,50,100],yticks=range(3),yticklabels=NAMES)
  ax.tick_params(axis='y',length=0,pad=8);ax.spines['left'].set_visible(False)
  ax.set_title(title,fontsize=9.5,pad=17);letter(ax,ltr)
 fig.supxlabel('试次比例 (%)',x=.55,y=.04,fontsize=9.5)
 save(fig,'图8-3_候选方法与不确定性','point_interval_comparison',dict(sigma_kpa=10,groups=records,interval='Wilson 95%'))

def amplitude():
 fig,axs=plt.subplots(1,2,figsize=(6.65,3.65),sharey=True)
 fig.subplots_adjust(left=.105,right=.965,bottom=.20,top=.77,wspace=.22)
 records=[]
 for ax,scene,title,ltr in zip(axs,['leak','restriction'],['渐进泄漏','渐进受限'],'ab'):
  for sigma,c,marker in zip([.3,3.,10.],[GRAY,BLUE,RED],['o','s','^']):
   gs=[next(g for g in EX['amplitude_groups'] if (g['scene'],g['sigma'],g['amplitude'])==(scene,sigma,a)) for a in [.05,.1,.15,.2,.3]]
   xx=np.array([5,10,15,20,30]);yy=np.array([g['correct'] for g in gs]);ci=np.array([d.wilson(int(y),100) for y in yy])*100
   ax.fill_between(xx,ci[:,0],ci[:,1],color=c,alpha=.075,lw=0)
   ax.plot(xx,yy,color=c,marker=marker,ms={.3:6.5,3.:5.3,10.:4.5}[sigma],mfc='none',mew=1.0,lw=1.15,label=f'{sigma:g} kPa',clip_on=False)
   records.append(dict(scene=scene,sigma=sigma,amplitude_percent=xx.tolist(),correct=yy.tolist(),n=100,wilson95_percent=ci.tolist()))
  ax.set(xlim=(4,31),ylim=(-2,105),xticks=[5,10,20,30],yticks=[0,50,100]);ax.set_title(title,pad=15,fontsize=9.5);letter(ax,ltr)
  # Sparse direct endpoint labels make the low-amplitude limitation visible.
  if scene=='leak':ax.text(6.1,4,'2%',color=GRAY,fontsize=8.6)
  else:ax.text(6.2,24,'22%',color=RED,fontsize=8.6)
 axs[0].set_ylabel('正确提示 (%)')
 handles=[Line2D([],[],color=c,marker=m,ms=4.5,mfc='white',lw=1.2,label=f'σ = {s:g} kPa') for s,c,m in zip([.3,3.,10.],[GRAY,BLUE,RED],['o','s','^'])]
 fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.53,.985),ncol=3,frameon=False,columnspacing=1.5)
 fig.supxlabel('终值流量偏离 (%)',x=.53,y=.045,fontsize=9.5)
 save(fig,'图8-4_故障幅值与检出响应','discrete_response_with_binomial_intervals',dict(groups=records,
   connecting_segments='guides through measured levels, not a calibrated continuous detection model'))

def lead_ecdf():
 fig,axs=plt.subplots(1,2,figsize=(6.65,3.6),sharey=True)
 fig.subplots_adjust(left=.105,right=.965,bottom=.20,top=.79,wspace=.24)
 records=[]
 for ax,scene,title,ltr in zip(axs,['leak','restriction'],['泄漏','受限'],'ab'):
  for method,c,ls in zip(METHODS,COLORS,[':', '-', '--']):
   v=np.array([float(r['lead_s']) for r in TRIALS if r['batch']=='holdout100' and r['scene']==scene and float(r['sigma'])==10 and r['method']==method and r['early_valid']=='True'])
   x,count=np.unique(np.sort(v),return_counts=True);cdf=np.cumsum(count)/len(v)*100
   ax.step(np.r_[0,x,160],np.r_[0,cdf,100],where='post',color=c,lw=1.6,ls=ls)
   records.append(dict(scene=scene,method=method,n=len(v),values_s=v.tolist(),x_s=x.tolist(),cdf_percent=cdf.tolist()))
  ax.set(xlim=(0,150),ylim=(0,104),xticks=[0,50,100,150],yticks=[0,50,100]);ax.set_title(title,pad=16,fontsize=9.5);letter(ax,ltr)
 axs[0].set_ylabel('累计试次比例 (%)')
 fig.legend(handles=[Line2D([],[],color=c,ls=ls,lw=1.6,label=n) for c,ls,n in zip(COLORS,[':','-','--'],NAMES)],
  loc='upper center',bbox_to_anchor=(.53,.985),ncol=3,frameon=False,columnspacing=1.9)
 fig.supxlabel('有效早期提前量 (s)',x=.53,y=.045,fontsize=9.5)
 save(fig,'补图S2_提前量经验分布','conditional_empirical_cdf',dict(sigma_kpa=10,groups=records,conditioning='valid early trials only'))

def tradeoff():
 fig,ax=plt.subplots(figsize=(6.65,3.55));fig.subplots_adjust(left=.13,right=.965,bottom=.20,top=.94)
 records=[]
 for scene,c,label in [('leak',BLUE,'渐进泄漏'),('fast_leak_switch',RED,'切换期快泄漏')]:
  gs=[next(g for g in EX['sampling_groups'] if g['scene']==scene and g['period']==p) for p in [1,2,5]]
  xx=np.array([g['pressure_reads_median'] for g in gs]);yy=np.array([g['lead_median_s'] for g in gs])
  ax.plot(xx,yy,color=c,lw=1.4)
  for j,g in enumerate(gs):
   xci=np.array(g['pressure_reads_iqr']);yci=np.array(g['lead_iqr_s'])
   ax.errorbar(xx[j],yy[j],xerr=[[xx[j]-xci[0]],[xci[1]-xx[j]]],yerr=[[yy[j]-yci[0]],[yci[1]-yy[j]]],
    fmt='o',ms=5.8,color=c,mfc='white',lw=.9,capsize=2,mew=1.,zorder=4)
   ax.text(xx[j],yy[j]+6,f'{g["period"]} s',ha='center',fontsize=8.7)
  ax.text(302,yy[-1]-8,label,color=c,fontsize=9.5)
  records.append(dict(scene=scene,groups=gs))
 ax.set(xlim=(285,505),ylim=(-8,71),xticks=[300,350,400,450,500],yticks=[0,25,50],xlabel='压力读取次数',ylabel='有效早期提前量 (s)')
 save(fig,'图8-5_采集次数与响应余量','acquisition_tradeoff_with_iqr',records)

time_plate('leak','图8-1_泄漏信号与判据演变')
feature_plane();comparison();amplitude()
time_plate('restriction','补图S1_受限信号与判据演变')
lead_ecdf();tradeoff()
np.savez_compressed(E/'mechanism_observations.npz',t=np.arange(601),**RAW)
(E/'mechanism_replay.json').write_text(json.dumps(ILL,ensure_ascii=False,indent=2),encoding='utf-8')
(E/'figure_checks.json').write_text(json.dumps(RECORDS,ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported seven figures with PNG PDF SVG and exact underlying arrays.')
print(json.dumps({s:{k:v for k,v in row.items() if k in ['first_correct_s','critical_s','valid_lead_s','early_valid']} for s,row in ILL.items()},ensure_ascii=False))
