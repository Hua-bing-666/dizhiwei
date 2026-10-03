"""Print-readable Word figures, derived only from design and stored model traces."""
from pathlib import Path
import subprocess,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from author_visual_redesign import txt,box,ln,circ,arrow,G,A,B,M,S,W
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures';TMP=ROOT/'tmp/visual_redesign';TMP.mkdir(parents=True,exist_ok=True)
EDGE=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
def render(name,v,width,height):
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'+box(0,0,width,height,'#FFFFFF')+v+'</svg>'
    (OUT/(name+'.svg')).write_text(svg,encoding='utf-8',newline='\n')
    page=TMP/(name+'.html');page.write_text(f'<html><meta charset="utf-8"><style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden}}svg{{display:block;width:{width}px;height:{height}px}}</style>'+svg+'</html>',encoding='utf-8')
    subprocess.run([EDGE,'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars','--force-device-scale-factor=2','--user-data-dir='+str(TMP/'figure-profile'),f'--window-size={width},{height}','--screenshot='+str(OUT/(name+'.png')),page.as_uri()],capture_output=True,check=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)

v=''
rows=[('01','水力感知','P0 / P1 / Q、阀态与质量标志','原始测量','参考标定 / 程度标签'),('02','有限诊断','有限故障模式或异常待检查','本地证据','强基线 / 失败边界'),('03','LoRa告警','缓存、ACK、去重与恢复','可靠传输','离线 / 溢出记录'),('04','管理确认','趋势、事件确认、回放与导出','系统产出','台架 / 数据 / 报告')]
for j,(n,title,body,result,detail) in enumerate(rows):
    yy=12+j*106;v+=box(12,yy,876,89,S,r=6)+circ(49,yy+42,21,G)+txt(49,yy+49,n,20,'#FFFFFF',True,'middle')
    v+=txt(90,yy+32,title,24,G,True)+txt(90,yy+68,body,22,G)+txt(645,yy+33,result,24,G,True)+txt(645,yy+67,detail,20,M)
    if j<3:v+=arrow(439,yy+92,439,yy+104,G,2)
render('system_scope',v,900,432)
v=''
for a in [(99,161,231,161),(231,119,231,298),(231,119,847,119),(231,298,847,298)]:v+=ln(*a,G,5)
v+=box(23,132,130,58,S,G,5)+txt(88,169,'共同供水',24,G,False,'middle')
v+=box(389,97,111,44,'#F6ECE6',A,4)+txt(444,126,'受限元件',22,A,False,'middle')
for xx,label,desc in [(294,'P0','区段入口'),(585,'P1','受限下游'),(708,'Q','支管总流量')]:
    v+=circ(xx,119,24,W,G,2.5)+txt(xx,127,label,22,G,True,'middle')+txt(xx,60,desc,22,M,False,'middle')
v+=box(782,95,103,47,S,r=4)+txt(833,126,'A负载',22,G,False,'middle')
v+=ln(758,119,758,203,A,3)+ln(758,203,860,203,A,3)+txt(800,240,'泄漏旁路',22,A)
v+=box(431,276,112,44,S,G,4)+txt(487,306,'切换阀',22,G,False,'middle')
v+=box(782,276,103,44,S,r=4)+txt(833,306,'B负载',22,G,False,'middle')
v+=txt(24,366,'P0/P1包围受限区段；Q包含A负载与泄漏总流量。须参考标定。',22,M)
render('dual_pressure_layout',v,900,392)

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
print('Three print-readable design/model figures regenerated; no new physical evidence.')
