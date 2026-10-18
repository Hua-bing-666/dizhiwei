"""Remove redundant labels; redraw numeric plots for monochrome printing."""
from pathlib import Path
from lxml import etree as E
import hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures/submission_upgrade'
DATA = ROOT / 'simulation/submission_upgrade'
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
S = '{http://www.w3.org/2000/svg}'
sha = lambda b: hashlib.sha256(b).hexdigest()
records = []

config = {
 'system_responsibilities': (110, 640, [
  '支管巡检系统组成与数据流', '系统方案：感知节点、LoRa接收端与本地巡检平台。',
  '无线模块负责字节传输；PC服务负责事务存储与接收确认。']),
 'water_layout': (0, 650, []),
 'collection_overview': (65, 885, [
  '清水台架：测量、注入与独立计量', '参数化概念模型，展示测点、管路与独立计量布局。']),
 'measurement_interfaces': (85, 903, [
  '感知节点：双压力与流量采集接口', '功能接口设计：双路压力采集与脉冲流量计数。',
  '功能接口方案，用于采集电平与信号路径论证。']),
 'diagnosis_proposal': (110, 780, [
  '支管异常诊断流程设计', '拟研究流程：质量检查、工况匹配、联合特征与持续确认。',
  '异常模式用于提示巡检，故障原因由独立核查确认。',
  '健康参照、操作状态与测量误差共同约束分类。']),
 'durable_event_sequence': (110, 930, [
  '事件可靠交付：持久化确认与重复去重', '通信方案设计：本地日志、接收事务与确认重传。']),
}
for name, (top, bottom, remove) in config.items():
 source = ROOT / 'application/figures/equation_revision' / (name + '.svg')
 before = E.fromstring(source.read_bytes())
 root = E.fromstring(source.read_bytes())
 seen = []
 for el in list(root.findall('.//' + S + 'text')):
  if el.text in remove:
   seen.append(el.text)
   el.getparent().remove(el)
 assert sorted(seen) == sorted(remove), (name, seen)
 # Exact geometry comparison, including connection/arrow coordinates.
 def geometry(tree):
  return [E.tostring(e) for e in tree.iter() if e.tag in
          [S + k for k in ['path','polyline','polygon','rect','circle','ellipse','line','image']]]
 assert geometry(root) == geometry(before), name
 # Retained labels keep text, position and type size exactly as before.
 retained_before = [E.tostring(e) for e in before.findall('.//' + S + 'text') if e.text not in remove]
 assert [E.tostring(e) for e in root.findall('.//' + S + 'text')] == retained_before
 root.set('viewBox', f'0 {top} 1000 {bottom-top}')
 root.set('height', str(bottom-top))
 target = OUT / (name + '.svg')
 target.write_bytes(E.tostring(root, encoding='utf-8'))
 records.append({'name':name,'source':source.relative_to(ROOT).as_posix(),
  'source_sha256':sha(source.read_bytes()),'svg':target.relative_to(ROOT).as_posix(),
  'removed_labels':seen,'geometry_unchanged':True,'retained_labels_unchanged':True,
  'viewport_crop':[0,top,1000,bottom-top]})

summary_source = ROOT / 'simulation/diagnosis_review/summary.json'
D = json.loads(summary_source.read_text(encoding='utf-8'))
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,
 'svg.fonttype':'none','font.size':14,'axes.labelsize':14,'axes.titlesize':14,
 'xtick.labelsize':14,'ytick.labelsize':14,'legend.fontsize':14,
 'axes.spines.top':False,'axes.spines.right':False})

def finish(fig, name, series):
 fig.canvas.draw()
 renderer = fig.canvas.get_renderer()
 w,h = fig.canvas.get_width_height()
 for item in fig.findobj(matplotlib.text.Text):
  if not item.get_visible() or not item.get_text(): continue
  box = item.get_window_extent(renderer)
  assert box.x0 >= -1 and box.y0 >= -1 and box.x1 <= w+1 and box.y1 <= h+1, (name,item.get_text())
  assert item.get_fontsize() >= 14, (name,item.get_text())
 target=OUT/(name+'.svg')
 fig.savefig(target,facecolor='white')
 target.write_text('\n'.join(line.rstrip() for line in target.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
 records.append({'name':name,'source':summary_source.relative_to(ROOT).as_posix(),
  'source_sha256':sha(summary_source.read_bytes()),'svg':target.relative_to(ROOT).as_posix(),
  'data_unchanged':True,'monochrome':True,'series':series})
 plt.close(fig)

fig,axes=plt.subplots(2,1,figsize=(8.5,6.9))
fig.subplots_adjust(left=.145,right=.975,top=.84,bottom=.135,hspace=.85)
series=[]
levels=[.3,1,3,10]
for ax,kind,label in zip(axes,['leak','restriction'],['等效泄漏','局部受限']):
 for method,name,offset,hatch in [('physical','K/R联合特征',-.18,''),('flow_only','流量相对阈值',.18,'////')]:
  groups=[next(g for g in D['groups'] if g['kind']==kind and g['method']==method and g['pressure_sigma_kpa']==s) for s in levels]
  values=np.array([g['early_trials'] for g in groups])
  ci=np.array([g['early_wilson95'] for g in groups])*20
  xs=np.arange(4)+offset
  ax.bar(xs,values,width=.32,facecolor='white',edgecolor='black',hatch=hatch,linewidth=1.2,label=name,zorder=2)
  ax.errorbar(xs,values,yerr=np.array([values-ci[:,0],ci[:,1]-values]),fmt='none',ecolor='black',capsize=4,lw=1.2,zorder=3)
  for x,value,upper in zip(xs,values,ci[:,1]): ax.text(x,upper+.7,str(value),ha='center',fontsize=14)
  series.append({'kind':kind,'method':method,'sigma':levels,'values':values.tolist(),'ci_low_counts':ci[:,0].tolist(),'ci_high_counts':ci[:,1].tolist()})
 ax.set(xticks=np.arange(4),xticklabels=['0.3','1.0','3.0','10.0'],ylim=(0,25),yticks=[0,5,10,15,20],
        xlabel='压力随机噪声 σ / kPa',ylabel='有效早期次数 / 20',title=label)
 ax.grid(axis='y',color='.85',lw=.6,zorder=0);ax.set_axisbelow(True)
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.55,.975),ncol=2,frameon=False)
fig.text(.145,.018,'每组20个合成试次；误差线为模型内Wilson 95%区间。',fontsize=14)
finish(fig,'noise_outcomes_print',series)

fig,axes=plt.subplots(2,1,figsize=(8.5,6.9))
fig.subplots_adjust(left=.145,right=.975,top=.84,bottom=.105,hspace=.9)
leak=D['traces']['leak_0.3'];unknown=D['traces']['load_unknown_0.3'];drift=D['traces']['drift_0.3']
assert leak['observed']==unknown['observed']
t=np.array(leak['t']);k=100*(np.array(leak['k'])/leak['k0']-1)
ax=axes[0]
ax.plot(t,k,color='black',lw=2,label='等效泄漏')
ax.plot(t[::10],k[::10],ls='none',marker='o',markerfacecolor='white',markeredgecolor='black',markersize=5,label='未知正常负载（同一观测）')
ax.axhline(6,color='black',ls='--',lw=1.5,label='K相对阈值6%')
ax.set(xlim=(330,600),xticks=[350,400,450,500,550,600],ylim=(-2,36),yticks=[0,10,20,30],
       xlabel='模型时间 / s',ylabel='K相对参照变化 / %',title='负载变化与泄漏的观测歧义')
handles,labels=ax.get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.56,.975),ncol=3,frameon=False,columnspacing=.6,handlelength=1.4)
ax=axes[1];r=np.array(drift['r'])-drift['r0']
ax.plot(drift['t'],r,color='black',lw=2,label='压力漂移下的阻力估计')
ax.axhline(.6,color='black',ls='--',lw=1.5,label='固定触发阈值0.6')
ax.set(xlim=(330,600),xticks=[350,400,450,500,550,600],ylim=(-.1,1.4),yticks=[0,.5,1],
       xlabel='模型时间 / s',ylabel='R估计−参照 / kPa/(L/min)²',title='压力漂移的影响')
ax.legend(loc='upper left',frameon=False)
for ax in axes:ax.grid(color='.85',lw=.6);ax.set_axisbelow(True)
finish(fig,'failure_counterexamples',[{'curve':'leak_unknown_k','t':t.tolist(),'values':k.tolist()},
 {'curve':'drift_r','t':drift['t'],'values':r.tolist()}])
(DATA/'figure_sources.json').write_text(json.dumps({'date':'2026-10-05','physical_validation':False,
 'figures':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Eight figures prepared; six diagram geometries preserved, two charts regenerated from frozen numeric sources.')
