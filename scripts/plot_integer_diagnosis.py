"""Actual three-way replay outputs; grayscale causal-window comparison."""
from pathlib import Path
import json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'simulation'))
import review_integer_diagnosis as m
OUT=ROOT/'deliverables/整数诊断验证图'
plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':12,
                     'axes.labelsize':12,'axes.titlesize':14,'legend.fontsize':11,'xtick.labelsize':11,'ytick.labelsize':11,
                     'svg.fonttype':'none','svg.hashsalt':'integer-diagnosis-20261006','axes.spines.top':False,'axes.spines.right':False})
def main():
    m.parameters()
    acceptance=json.loads((m.OUT/'replay_acceptance.json').read_text(encoding='utf-8'));assert acceptance['passed']
    data=json.loads((m.OUT/'examples.json').read_text(encoding='utf-8'))
    fig,axes=plt.subplots(3,2,figsize=(13.8,9.3),sharex='col')
    fig.subplots_adjust(left=.14,right=.97,top=.80,bottom=.13,wspace=.40,hspace=.25)
    for col,(name,lo,hi,title) in enumerate([('pulse8',345,395,'8秒合成泄漏'),('counter_reset',405,445,'累计计数回退')]):
        ex=data[name];indices=[j for j,t in enumerate(ex['t_s']) if lo<=t<=hi];x=np.array([ex['t_s'][j] for j in indices])
        for row in range(3):
            ax=axes[row,col]
            def yvalues(rows):
                return [rows[j][1] if row==0 else (-1 if not rows[j][2] else rows[j][3]) if row==1 else int(rows[j][0]==0) for j in indices]
            original=yvalues(ex['original']);integer=yvalues(ex['integer'])
            assert original==integer
            if name=='pulse8':ax.axvspan(360,368,color='.92',zorder=0)
            else:ax.axvline(420,color='.55',ls=':',lw=1)
            ax.step(x,integer,where='post',color='black',lw=1.8)
            # Marker at each actual endpoint; line segments are discrete state holds.
            ax.plot(x[::2],np.array(original)[::2],color='black',marker='o',mfc='white',ms=4,ls='none')
            if row==0:
                ax.set(yticks=[0,1,4],yticklabels=['无模式证据','泄漏模式','不可用'],ylim=(-.4,4.4),title=title)
            elif row==1:ax.set(yticks=[-1,0,1],yticklabels=['不可用','未提示','待复核'],ylim=(-1.3,1.3))
            else:ax.set(yticks=[0,1],yticklabels=['无效','有效'],ylim=(-.2,1.2))
            if col==0:ax.set_ylabel(['主诊断输出','三秒复核提示','测量状态'][row],labelpad=16)
            if row==2:ax.set_xlabel('内部采样索引 t（1 s/点）',labelpad=10)
            ax.set_xlim(lo-.8,hi+.8);ax.set_xticks(np.arange(lo,hi+1,10));ax.grid(axis='y',color='.92')
    fig.legend([Line2D([],[],color='black',lw=1.8),Line2D([],[],color='black',marker='o',mfc='white',ls='none'),Patch(facecolor='.92')],
               ['整数C输出','原浮点输出（每2点标记）','合成泄漏区间（左列）'],loc='upper center',bbox_to_anchor=(.55,.96),ncol=3,frameon=False)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();w,h=fig.canvas.get_width_height();texts=[]
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text():continue
        b=t.get_window_extent(renderer);assert 0<=b.x0 and 0<=b.y0 and b.x1<=w and b.y1<=h,t.get_text()
        assert t.get_fontsize()>=11
        texts.append(dict(text=t.get_text(),box=list(b.bounds),font_pt=t.get_fontsize()))
    for i,a in enumerate(texts):
        x,y,ww,hh=a['box']
        for b in texts[i+1:]:
            xx,yy,bw,bh=b['box']
            assert min(x+ww,xx+bw)-max(x,xx)<=1 or min(y+hh,yy+bh)-max(y,yy)<=1,(a['text'],b['text'])
    OUT.mkdir(exist_ok=True);name='01_主诊断短窗与质量恢复对照'
    for ext in ['png','svg']:
        p=OUT/(name+'.'+ext);fig.savefig(p,dpi=180,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':p.write_text('\n'.join(s.rstrip() for s in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    m.dump('figure_checks.json',dict(name=name,question='三秒提示是否代替主诊断？计数回退后会不会继续沿用有效状态？',
            minimum_font_pt=min(t['font_pt'] for t in texts),text_within_canvas=True,text_collision_check=True,texts=texts,
            sources={n:m.sha(m.OUT/n) for n in ['examples.json','results_summary.json','replay_acceptance.json']},
            plot_script_sha256=m.sha(Path(__file__)),file_sha256={ext:m.sha(OUT/(name+'.'+ext)) for ext in ['png','svg']},
            scope='Actual synthetic example outputs, seed 51000, sigma 0.3; not Word insertion or physical measurement'))
    print('One six-panel grayscale comparison generated with text bounds and collision checks.')
if __name__=='__main__':main()
