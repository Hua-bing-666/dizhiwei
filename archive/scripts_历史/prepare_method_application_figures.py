"""Application diagrams and plots from previously accepted, frozen replay data."""
from pathlib import Path
import csv, hashlib, json
from lxml import etree as E
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures/method_revision'
DATA = ROOT / 'application/method_revision'
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
S = 'http://www.w3.org/2000/svg'
svg = E.Element('{'+S+'}svg', nsmap={None:S}, width='1000', height='710', viewBox='0 0 1000 710')
def el(tag, **attrs):
    return E.Element('{'+S+'}'+tag, **{k.replace('_','-'):str(v) for k,v in attrs.items()})
svg.append(el('rect', x=0, y=0, width=1000, height=710, fill='white'))
defs = el('defs'); marker = el('marker', id='arrow', markerWidth=9, markerHeight=9, refX=8, refY=4.5, orient='auto', markerUnits='userSpaceOnUse')
marker.append(el('path', d='M0,0 L9,4.5 L0,9 Z', fill='#222'));defs.append(marker);svg.append(defs)
def box(x,y,w,h,lines):
    g=el('g', **{'data-box':'1','data-x':x,'data-y':y,'data-w':w,'data-h':h})
    g.append(el('rect',x=x,y=y,width=w,height=h,rx=2,fill='white',stroke='#222',stroke_width=2))
    step=34
    for i,t in enumerate(lines):
        text=el('text',x=x+w/2,y=y+h/2-(len(lines)-1)*step/2+i*step+9,
                text_anchor='middle',font_family='Microsoft YaHei, SimSun, sans-serif',font_size=26 if i==0 else 24,
                font_weight=600 if i==0 else 400,fill='#111')
        text.text=t;g.append(text)
    svg.append(g)
def arrow(d, head=True):
    attrs=dict(d=d,fill='none',stroke='#222',stroke_width=2)
    if head:attrs['marker_end']='url(#arrow)'
    svg.append(el('path',**attrs))
box(30,20,940,86,['压力与累计计数','转换时刻、锁存时刻及配置版本'])
arrow('M500,106 V140')
box(30,140,940,100,['测量检查与健康参照核验','参照不可用时停用判断；两个窗口分别检查有效性'])
arrow('M500,240 V260 H245 V286');arrow('M500,260 H755 V286')
box(30,286,430,140,['3秒短窗','4处计数端点、3次压力观测','独立残差尺度与门限'])
box(540,286,430,140,['10秒主窗','11处计数端点、10次压力观测','健康参照与双通道门限'])
arrow('M245,426 V464');arrow('M755,426 V464')
box(30,464,430,90,['连续2次出现正向越限','待复核提示'])
box(540,464,430,90,['连续5次同模式越限','泄漏、受限或待检查'])
arrow('M245,554 V581 H500',False);arrow('M755,554 V581 H500',False);arrow('M500,581 V611')
box(30,611,940,79,['分别保存窗口有效性、提示与候选模式','事件快照保留原采集时刻'])
path=OUT/'dual_window_diagnosis.svg';path.write_bytes(E.tostring(svg,encoding='utf-8'))

source=ROOT/'simulation/hybrid_sampling_review/sensor_results.csv'
accept=ROOT/'simulation/hybrid_sampling_review/acceptance.json'
assert json.loads(accept.read_text(encoding='utf-8'))['sensor_records_reproduced']==2592
rows=list(csv.DictReader(source.open(encoding='utf-8')))
methods=['threshold','guarded_fast','hybrid'];scenes=['leak','restriction','long_normal'];sigmas=['0.3','3.0','10.0']
selected=[];groups=[]
for scene in scenes:
    for sigma in sigmas:
        for method in methods:
            rr=[r for r in rows if r['scene']==scene and r['sigma']==sigma and r['method']==method and r['profile']=='fixed']
            assert len(rr)==12 and {int(r['seed']) for r in rr}==set(range(28000,28012))
            selected.extend(rr)
            groups.append(dict(scene=scene,sigma=float(sigma),method=method,n=12,
                early=sum(r['early_valid']=='True' for r in rr),
                false_trials=sum(int(r['false_onsets'])>0 for r in rr)))
with (DATA/'figure9_selected_records.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(selected)
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':15,'axes.unicode_minus':False,'svg.fonttype':'none',
                     'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(3,1,figsize=(8,7.2),sharex=True)
labels=['固定门限','稳健门限','稳健门限＋累积'];hatches=['','///','xx']
fig.legend([Patch(facecolor='white',edgecolor='black',hatch=h) for h in hatches],labels,
           ncol=3,loc='upper center',bbox_to_anchor=(.54,.995),frameon=False,fontsize=14.4,
           handlelength=1.5,columnspacing=1.2)
for ai,(ax,scene) in enumerate(zip(axes,scenes)):
    for mi,method in enumerate(methods):
        values=[next(g for g in groups if g['scene']==scene and g['sigma']==float(s) and g['method']==method)['false_trials' if scene=='long_normal' else 'early'] for s in sigmas]
        pos=np.arange(3)+(mi-1)*.24
        bars=ax.bar(pos,values,width=.22,color='white',edgecolor='black',linewidth=1.2,hatch=hatches[mi],zorder=3)
        for x,y in zip(pos,values):ax.text(x,y+.35,str(y),ha='center',va='bottom',fontsize=14.4)
    ax.set_ylim(0,14.6);ax.set_yticks([0,6,12]);ax.set_xlim(-.55,2.55)
    ax.set_ylabel('试次数 / 12')
    ax.set_title(['(a) 泄漏：有效早期','(b) 局部受限：有效早期','(c) 长时正常：发生确认误报'][ai],loc='left',pad=7,fontsize=15)
    ax.grid(axis='y',color='#ddd',linewidth=.6,zorder=0)
axes[-1].set_xticks(range(3),['0.3','3','10']);axes[-1].set_xlabel('压力随机噪声 σ / kPa',labelpad=6)
fig.subplots_adjust(left=.14,right=.97,bottom=.085,top=.90,hspace=.50)
fig.savefig(OUT/'candidate_comparison.png',dpi=250,facecolor='white')
fig.savefig(OUT/'candidate_comparison.svg',facecolor='white');plt.close(fig)
vector=OUT/'candidate_comparison.svg'
vector.write_text('\n'.join(line.rstrip() for line in vector.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
record=dict(physical_validation=False,source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),
  previous_acceptance_sha256=sha(accept),parameters_sha256=sha(ROOT/'simulation/hybrid_sampling_review/frozen_parameters.json'),
  selection='All three noise levels; both gradual faults and long-normal controls; fixed acquisition; all 12 frozen seeds; no new tuning.',
  groups=groups,all_trial_identifiers_retained=True,
  interpretation='Candidate-stage synthetic pulse frontend; not current integrated hardware performance or independent physical repeats.',
  figures=[dict(name='dual_window_diagnosis',svg=path.relative_to(ROOT).as_posix())])
(DATA/'figure_sources.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Prepared dual-window flowchart and auditable candidate comparison, 324 selected method records.')
