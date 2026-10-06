"""Plot saved counter-endpoint fault trace; no invented measurements."""
from pathlib import Path
import json,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_acquisition_pipeline as m
assert json.loads((m.OUT/'final_acceptance.json').read_text(encoding='utf-8'))['passed']
data=json.loads((m.OUT/'fault_examples.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
                     'svg.fonttype':'none','svg.hashsalt':'acquisition-closeout-20261006'})
fig,axes=plt.subplots(2,1,figsize=(10.5,6.4),sharex=True)
fig.subplots_adjust(left=.12,right=.97,bottom=.13,top=.84,hspace=.28)
for name,label,style,marker in [('counter_reset','计数复位（当前端点已知）','-','o'),('late_counter','计数锁存迟到（当前端点排除）','--','s')]:
    rows=data[name];x=[r['sample_index'] for r in rows]
    for ax,key in zip(axes,['rapid_valid','status']):
        y=[r['fields'][key] if key=='rapid_valid' else int(r['fields'][key]==0) for r in rows]
        ax.step(x,y,where='post',ls=style,color='black',label=label,lw=1.6)
        ax.plot(x,y,ls='none',marker=marker,mfc='white',color='black',ms=4)
for ax,label in zip(axes,['三秒短窗','十秒主窗']):
    ax.set_ylabel(label,labelpad=13);ax.set_yticks([0,1],['不可用','有效']);ax.set_ylim(-.2,1.2)
    ax.set_xlim(417.5,433.5);ax.set_xticks(range(418,434,2));ax.grid(axis='y',color='.9')
    ax.axvline(420,color='.5',ls=':',lw=1)
axes[-1].set_xlabel('内部采样索引 t（1 s/点）',labelpad=10)
fig.legend(loc='upper center',ncol=1,frameon=False,bbox_to_anchor=(.55,.98))
handles,labels=axes[0].get_legend_handles_labels()
# The second subplot contains the same curves; deduplicate figure legend.
fig.legends[0].remove();fig.legend(handles,labels,loc='upper center',ncol=1,frameon=False,bbox_to_anchor=(.55,.98))
fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();texts=[]
for t in fig.findobj(Text):
    if not t.get_visible() or not t.get_text():continue
    box=t.get_window_extent(renderer);assert box.x0>=0 and box.y0>=0 and box.x1<=w and box.y1<=h,t.get_text()
    texts.append(dict(text=t.get_text(),box=list(box.bounds)))
for i,a in enumerate(texts):
    x,y,ww,hh=a['box']
    for b in texts[i+1:]:
        xx,yy,bw,bh=b['box']
        assert min(x+ww,xx+bw)-max(x,xx)<=1 or min(y+hh,yy+bh)-max(y,yy)<=1,(a['text'],b['text'])
out=ROOT/'deliverables/采集适配验证图';out.mkdir(exist_ok=True)
files={}
for ext in ['png','svg']:
    p=out/('计数端点有效性与窗口恢复.'+ext);fig.savefig(p,dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
    if ext=='svg':p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    files[ext]=m.sha(p)
m.dump('figure_checks.json',dict(text_bounds_passed=True,text_collision_passed=True,files=files,
                                source_sha256=m.sha(m.OUT/'fault_examples.json'),script_sha256=m.sha(Path(__file__)),
                                classification='Saved synthetic host outputs; not physical measurements',visual_review='pending'))
print('One grayscale saved-output figure generated; visual review pending.')
