"""Engineering design diagrams, not photographs or fabricated hardware."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures'
plt.rcParams['font.sans-serif']=['SimHei'];plt.rcParams['axes.unicode_minus']=False
G='#164C45';A='#B4512B';B='#426B91'

def save(fig,name):
    for ext in ['png','svg']:fig.savefig(OUT/(name+'.'+ext),dpi=160,bbox_inches='tight',facecolor='#FAF9F5')
    svg=OUT/(name+'.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)

def main():
    fig,ax=plt.subplots(figsize=(12,4.6));ax.set(xlim=(0,12),ylim=(0,4.6));ax.axis('off')
    entries=[('水力感知','P0 / P1 / Q\n阀态与质量标志'),('本地诊断','有限故障模式\n或异常待检查'),('LoRa告警','缓存 / ACK / 去重\n离线与溢出记录'),('管理软件','趋势 / 事件确认\n回放 / 导出')]
    for i,(title,body) in enumerate(entries):
        x=.2+3*i;ax.add_patch(Rectangle((x,1.8),2.6,1.65,facecolor='#EEF3EF',edgecolor=G,lw=1.4))
        ax.text(x+.15,3.05,title,fontsize=16,color=G);ax.text(x+.15,2.32,body,fontsize=12,linespacing=1.8)
        if i<3:ax.add_patch(FancyArrowPatch((x+2.61,2.6),(x+2.98,2.6),arrowstyle='->',mutation_scale=15,color=G))
    ax.text(.2,4.1,'支管巡检的信息闭环',fontsize=20,color=G)
    ax.text(.2,1.12,'研究问题一：测点与工况信息如何支持渐进故障辨识及早期评价',fontsize=13,color=G)
    ax.text(.2,.52,'研究问题二：相同本地诊断下，可靠告警如何平衡通信开销与及时性',fontsize=13,color=G)
    ax.text(.2,.05,'设计示意 · 尚无在线实物 · 自动阀控不在基础交付范围',fontsize=10,color=A)
    save(fig,'system_scope')
    fig,ax=plt.subplots(figsize=(12,5));ax.set(xlim=(0,12),ylim=(0,5));ax.axis('off')
    ax.text(.15,4.55,'双支路台架及双压力测点设计',fontsize=20,color=G)
    def pipe(xs,ys,color=G):ax.plot(xs,ys,color=color,lw=3)
    pipe([.6,2.5,2.5,11],[2.7,2.7,3.55,3.55]);pipe([2.5,2.5,11],[2.7,1.5,1.5])
    ax.add_patch(Rectangle((.05,2.3),1.2,.8,facecolor='#EEF3EF',edgecolor=G));ax.text(.65,2.7,'供回水',ha='center',va='center',fontsize=11)
    for x,label in [(3.25,'P0'),(6.75,'P1'),(8.05,'Q')]:
        ax.add_patch(Circle((x,3.55),.25,facecolor='#FAF9F5',edgecolor=B,lw=2));ax.text(x,3.55,label,ha='center',va='center',fontsize=12,color=B)
    ax.add_patch(Rectangle((4.25,3.25),1.4,.6,facecolor='#F4ECE5',edgecolor=A));ax.text(4.95,3.55,'可调受限',ha='center',va='center',fontsize=12,color=A)
    ax.text(3.25,4.05,'入口参考',ha='center',fontsize=11);ax.text(6.75,4.05,'受限下游',ha='center',fontsize=11)
    pipe([8.95,8.95,10.8],[3.55,2.55,2.55],A);ax.text(9.85,2.18,'泄漏旁路＋量取',ha='center',fontsize=11,color=A)
    ax.text(10.2,3.9,'A下游等效负载',ha='center',fontsize=12)
    ax.add_patch(Rectangle((4.25,1.2),1.4,.6,facecolor='#EEF3EF',edgecolor=G));ax.text(4.95,1.5,'B切换阀',ha='center',va='center',fontsize=12)
    ax.text(9.8,1.9,'B等效负载',ha='center',fontsize=12)
    ax.text(.2,.62,'测点P0和P1包围目标受限区段；Q包含下游负载和泄漏总流量。',fontsize=12,color=G)
    ax.text(.2,.13,'设计示意，非实物照片；量程、健康压降和差压不确定度必须标定。节流不等于真实滴头堵塞。',fontsize=10,color=A)
    save(fig,'dual_pressure_layout')
    print('Design diagrams: system_scope and dual_pressure_layout')

if __name__=='__main__':main()
