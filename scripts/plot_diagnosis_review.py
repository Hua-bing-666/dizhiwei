"""Source-linked scientific plots, kept separate from the current application."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/diagnosis_review'
OUT=ROOT/'application/figures/diagnosis_review';OUT.mkdir(exist_ok=True)
D=json.loads((DATA/'summary.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'svg.fonttype':'none','font.size':13.5,'axes.labelsize':14,'axes.titlesize':16,'xtick.labelsize':13.5,'ytick.labelsize':13.5,'legend.fontsize':13.5,'axes.spines.top':False,'axes.spines.right':False})
G='#316d65';O='#ae6541';B='#3d678d';M='#59666c';L='#d5dddd';records=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def group(kind,sigma,method='physical'):
    return next(g for g in D['groups'] if g['kind']==kind and g['pressure_sigma_kpa']==sigma and g['method']==method)
def frame(title,subtitle,footer,height=8.2):
    fig,axes=plt.subplots(2,1,figsize=(8.5,height))
    fig.subplots_adjust(left=.145,right=.97,top=.80,bottom=.225,hspace=.95)
    fig.text(.04,.962,title,fontsize=18,weight='bold',va='top')
    fig.text(.04,.914,subtitle,fontsize=13.5,va='top',color=M)
    fig.text(.04,.045,footer,fontsize=13.5,va='bottom',color=M,linespacing=1.5)
    for ax in axes:ax.grid(alpha=.15);ax.set_axisbelow(True)
    return fig,axes
def save(fig,name,question,series=(),annotations=()):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height()
    spans=[]
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():continue
        bbox=text.get_window_extent(renderer);assert bbox.x0>=-1 and bbox.y0>=-1 and bbox.x1<=w+1 and bbox.y1<=h+1,(name,text.get_text(),bbox.bounds)
        assert text.get_fontsize()>=13,(name,text.get_text(),text.get_fontsize())
        spans.append({'text':text.get_text(),'font_pt':text.get_fontsize()})
    for ext in ['png','svg']:fig.savefig(OUT/(name+'.'+ext),dpi=200,facecolor='white')
    p=OUT/(name+'.svg');p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    records.append({'name':name,'question':question,'classification':'uncalibrated_simulation_not_physical_test','figure_width_pt':612,'minimum_text_pt':min(t['font_pt'] for t in spans),'minimum_text_pt_at_425pt_width':min(t['font_pt'] for t in spans)*425/612,'texts':spans,'series':series,'annotations':annotations,'sha256':{ext:sha(OUT/(name+'.'+ext)) for ext in ['png','svg']}})
    plt.close(fig);print(name,'rendered')
def ranges():
    with (ROOT/'simulation/hardware_results/range_grid.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    q=np.array([float(r['q_a_l_min']) for r in rows]);ref=np.linspace(min(q),max(q),180)
    fig,axes=frame('量程与分辨率：先核对测量条件','24个设计组合；C=0.28/0.37，R=0.8/8.0，供压80/120/160kPa。','模型计算；尚无真实泵工作曲线、完整采集误差或量程实测。\n标称误差界限不等于随机噪声σ，ADC码宽也不等于整机准确度。',7.6)
    ax=axes[0];ax.plot(ref,.8*ref**2,color=G,lw=2.5,label='参考健康压降：R=0.8')
    ax.axhline(1,color=O,ls='--',lw=2,label='仅两压力传感器最不利界限1kPa')
    ax.set(xlabel='流量Q / L/min',ylabel='压差 / kPa',xticks=[2,2.5,3,3.5,4],ylim=(0,17),yticks=[0,4,8,12,16],title='低压差测量需先限制采集误差');ax.legend(loc='upper left')
    ax=axes[1];ax.axvspan(.3,5,color=G,alpha=.08);ax.scatter(q,np.ones(24),color=G,s=35,zorder=3)
    for x in [min(q),max(q)]:ax.plot([x,x],[.88,1.08],color=O,lw=1.5)
    ax.text(2.6,1.24,f'24组模型流量：{min(q):.2f}—{max(q):.2f} L/min',ha='center',fontsize=13.5)
    ax.text(2.6,.65,'候选范围0.3—5L/min；1秒/10秒计数步长0.111/0.0111L/min',ha='center',fontsize=13.5)
    ax.set(xlim=(0,5.5),xticks=[0,1,2,3,4,5],ylim=(.55,1.4),yticks=[],xlabel='A支路总流量 / L/min',title='候选范围覆盖所枚举网格，供水能力仍待核定')
    save(fig,'range_and_measurement','当前参数是否落在候选量程内，哪些误差需先解决？',series=[{'curve':'reference_dp','q':ref.tolist(),'dp_kpa':(.8*ref**2).tolist()},{'curve':'grid_flow','q':q.tolist(),'source':'simulation/hardware_results/range_grid.csv'}])
def early():
    fig,axes=frame('有效早期：提示需在独立参照之前','单次示例：seed=10300，压力σ=0.3kPa；当前台架参数，10秒窗、5次确认。','15%为同工况健康总流量偏离的演示参照，非作物损失标准。\n图示单次轨迹不等于20种子统计；前期误报和首次错误类别会使早期无效。',8.2)
    series=[];annotations=[]
    for ax,kind,label,color in zip(axes,['leak','restriction'],['等效泄漏','等效受限'],[O,G]):
        tr=D['traces'][kind+'_0.3'];t=np.array(tr['t']);sev=100*np.array(tr['severity']);det=tr['first_correct_s'];crit=tr['critical_s']
        assert tr['early_valid'] and det<crit and tr['false_onsets']==0
        ax.plot(t,sev,color=color,lw=2.5,label='模型真值：健康流量偏离')
        ax.axhline(15,color=B,ls='--',lw=1.7)
        ax.axvline(360,color=M,ls=':',lw=1.4)
        ax.scatter([det],[sev[det]],color=color,s=45,zorder=5)
        ax.scatter([crit],[sev[crit]],facecolor='white',edgecolor=color,s=45,zorder=5)
        ax.annotate(f'持续提示 {det}s',xy=(det,sev[det]),xytext=(det+20,3),fontsize=13.5,color=color,arrowprops={'arrowstyle':'-','color':color})
        ax.annotate(f'演示参照 {crit}s',xy=(crit,sev[crit]),xytext=(crit-48,23),fontsize=13.5,color=color,arrowprops={'arrowstyle':'-','color':color})
        ax.set(xlim=(335,600),xticks=[350,400,450,500,550,600],ylim=(0,34),yticks=[0,10,20,30],xlabel='模型时间 / s',ylabel='健康总流量偏离 / %',title=f'{label}：本例提前{tr["valid_lead_s"]}秒')
        series.append({'kind':kind,'t':t.tolist(),'severity_percent':sev.tolist(),'trace_key':kind+'_0.3'})
        annotations.extend([{'kind':kind,'label':'first_correct','t':det,'y':float(sev[det])},{'kind':kind,'label':'critical','t':crit,'y':float(sev[crit])}])
    save(fig,'early_reference_example','什么样的持续提示才满足有效早期定义？',series,annotations)
def outcomes():
    fig,axes=frame('种子统计：如实保留失败与方法差异','480个噪声试次；每场景、每σ20个种子，同一试次比较两条固定规则。','柱为有效早期次数/20；误差线为噪声模型内的Wilson95%区间。\n固定流量规则在高压力噪声下表现更好；本图不证明物理特征规则优越。',8.2)
    fig.subplots_adjust(top=.75,hspace=1.05)
    series=[];xs=np.arange(4);levels=[.3,1,3,10]
    for ax,kind,label in zip(axes,['leak','restriction'],['等效泄漏','等效受限']):
        for method,name,color,offset in [('physical','K与R物理特征',G,-.18),('flow_only','固定Q相对阈值',M,.18)]:
            groups=[group(kind,s,method) for s in levels];values=np.array([r['early_trials'] for r in groups]);ci=np.array([r['early_wilson95'] for r in groups])*20
            ax.bar(xs+offset,values,width=.32,color=color,alpha=.9,label=name)
            ax.errorbar(xs+offset,values,yerr=np.array([values-ci[:,0],ci[:,1]-values]),fmt='none',ecolor='#212d33',capsize=4,lw=1.2)
            for x,value,upper in zip(xs+offset,values,ci[:,1]):ax.text(x,upper+.8,str(value),ha='center',fontsize=13.5)
            series.append({'kind':kind,'method':method,'sigma':levels,'values':values.tolist(),'ci_low_counts':ci[:,0].tolist(),'ci_high_counts':ci[:,1].tolist()})
        ax.set(xticks=xs,xticklabels=['0.3','1.0','3.0','10.0'],ylim=(0,25),yticks=[0,5,10,15,20],xlabel='每个压力点的随机噪声σ / kPa',ylabel='有效早期次数 / 20',title=label)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.55,.869),ncol=2,frameon=False)
    save(fig,'noise_outcomes','不同噪声下有多少试次严格满足早期，是否真比对照好？',series)
def counterexamples():
    fig,axes=frame('失败反例：变化模式不能直接等同故障原因','两例均为seed=10300、σ=0.3kPa；对应原始三通道和同一因果滤波。','未知正常负载与泄漏可产生完全相同观测；入口压力漂移也会触发受限模式。\n需保留待核查输出，先标定与记录操作；不能靠换一个算法保证辨因。',8.2)
    fig.subplots_adjust(top=.75,hspace=1.05)
    leak=D['traces']['leak_0.3'];unknown=D['traces']['load_unknown_0.3'];drift=D['traces']['drift_0.3']
    assert leak['observed']==unknown['observed'];t=np.array(leak['t']);k=100*(np.array(leak['k'])/leak['k0']-1)
    ax=axes[0];ax.plot(t,k,color=O,lw=2.5,label='等效泄漏');ax.plot(t[::10],k[::10],ls='none',marker='o',markerfacecolor='none',markersize=5,color=B,label='未知正常负载（同一观测）')
    ax.axhline(6,color=M,ls='--',label='K相对阈值6%');ax.set(xlim=(330,600),xticks=[350,400,450,500,550,600],ylim=(-2,36),yticks=[0,10,20,30],xlabel='模型时间 / s',ylabel='K相对健康参照变化 / %',title='三通道观测完全相同：无法仅凭这些信号辨因')
    handles,labels=ax.get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.54,.869),ncol=3,frameon=False,columnspacing=.7,handlelength=1.4)
    r=np.array(drift['r'])-drift['r0'];ax=axes[1];ax.plot(drift['t'],r,color=G,lw=2.5,label='压力漂移导致的R估计变化');ax.axhline(.6,color=M,ls='--',label='固定触发阈值0.6')
    ax.set(xlim=(330,600),xticks=[350,400,450,500,550,600],ylim=(-.1,1.4),yticks=[0,.5,1],xlabel='模型时间 / s',ylabel='R估计−参照 / kPa/(L/min)²',title='真实水力阻力未变，漂移仍触发受限模式');ax.legend(loc='upper left')
    save(fig,'failure_counterexamples','在哪些反例中，检测曲线看起来合理却不能说明真实故障？',series=[{'curve':'leak_unknown_k','t':t.tolist(),'values':k.tolist()},{'curve':'drift_r','t':drift['t'],'values':r.tolist()}])
def errors():
    fig,axes=frame('误差界限：可分离不等于阈值可用','每个误差假设36个工况目标；压力传感器、电阻、码宽和计数项分别列入。','追加残差为假设敏感性参数，尚无完整标定；两种流量口径均保留。\n“同时满足”仅指静态箱式界限内的故障触发与健康不误触发，不是实物准确率。',8.2)
    fig.subplots_adjust(top=.75,hspace=1.05)
    series=[];xx=np.array([0,.25,1,3])
    for ax,basis,label in zip(axes,['reading','full_scale'],['流量误差按读数1%假设','流量误差按5L/min满量程1%假设']):
        rows=[r for r in D['interval_summary'] if r['flow_error_basis']==basis]
        for key,name,color,marker in [('disjoint_cases','区间分离',B,'o'),('fixed_threshold_guarantee_cases','故障侧触发',O,'s'),('joint_stationary_guarantee_cases','触发且健康不误触发',G,'^')]:
            yy=[r[key] for r in rows];ax.plot(xx,yy,lw=2,marker=marker,color=color,label=name)
            series.append({'basis':basis,'quantity':key,'extra_bound':[r['extra_per_channel_bound_kpa'] for r in rows],'values':yy})
        ax.set(xlim=(-.08,3.15),xticks=xx,xticklabels=['0','0.25','1','3'],ylim=(-1,39),yticks=[0,12,24,36],xlabel='每个压力通道追加残差界限 / kPa',ylabel='满足条件的工况数 / 36',title=label)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.55,.869),ncol=3,frameon=False,columnspacing=1)
    save(fig,'bounded_error_margin','增加尚未标定的采集误差后，还能否分开健康与故障并使用阈值？',series)
if __name__=='__main__':
    ranges();early();outcomes();counterexamples();errors()
    (OUT/'figure_provenance.json').write_text(json.dumps({'classification':'uncalibrated_simulation_candidate','source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),DATA/'summary.json',DATA/'protocol.json',ROOT/'simulation/hardware_results/range_grid.csv']},'figures':records},ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
