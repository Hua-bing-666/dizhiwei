# Regenerate the stored plot without overwriting design diagrams.
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from author_visual_redesign import G,A,B,M
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'application/figures'
data=json.loads((ROOT/'simulation/diagnosis_results/summary.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':13,'axes.titlesize':14,'axes.labelsize':13,'xtick.labelsize':12,'ytick.labelsize':12,'legend.fontsize':12})
fig,axes=plt.subplots(2,1,figsize=(8.5,7.6),layout='constrained')
for kind,label,col in [('leak','等效泄漏',A),('restriction','等效受限',G)]:
    tr=data['traces'][kind+'_0.3'];ax=axes[0]
    ax.plot(tr['t'],np.array(tr['severity'])*100,label=label,color=col,lw=2)
    ts=tr['detected_s'];tc=tr['critical_s'];yy=tr['severity_at_detection']*100
    ax.scatter(ts,yy,s=40,color=col,zorder=5)
    target=(445,24) if kind=='leak' else (363,11)
    ax.annotate(f'{label}提示 {ts}s',xy=(ts,yy),xytext=target,fontsize=12,color=col,arrowprops={'arrowstyle':'-','color':col})
    ax.scatter(tc,15,s=60,marker='|',color=col,zorder=5)
axes[0].axhline(15,color=B,linestyle='--',label='15%演示失效判据')
axes[0].set(xlim=(330,600),ylim=(0,30),xlabel='模型时间 / s',ylabel='健康流量偏离 / %',title='早期示例：提示在判据前，且无前期误报')
axes[0].legend(loc='upper left',fontsize=11);axes[0].grid(alpha=.18)
xx=np.arange(4)
for kind,label,col,offset in [('leak','等效泄漏',A,-.18),('restriction','等效受限',G,.18)]:
    values=[r['early_trials'] for r in data['summary'] if r['kind']==kind]
    axes[1].bar(xx+offset,values,width=.34,label=label,color=col)
    for x,n in zip(xx+offset,values):axes[1].text(x,n+.5,str(n),ha='center',fontsize=12,color=col)
axes[1].set(xticks=xx,xticklabels=['0.3','1.0','3.0','10.0'],ylim=(0,24),xlabel='各压力点噪声 σ / kPa',ylabel='正确提前发现 / 20次',title='20种子统计：增加噪声后，正确提前发现减少')
axes[1].legend(loc='upper right');axes[1].grid(axis='y',alpha=.18)
fig.suptitle('未标定合成模型；15%仅为演示参照，非实物识别率',fontsize=13,color=M)
for ext in ['png','svg']:fig.savefig(OUT/('early_diagnosis.'+ext),dpi=180,facecolor='white')
p=OUT/'early_diagnosis.svg';p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
plt.close(fig)
print('Stored early-diagnosis plot regenerated; no new physical evidence.')
