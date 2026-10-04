"""Two scoped proposed-design figures; distinguish radio bridge from PC storage."""
from pathlib import Path
import hashlib,json
import draw_interface_review as drawing
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'application/figures/presentation_review'
OUT.mkdir(exist_ok=True);drawing.OUT=OUT

def architecture():
    f=drawing.Figure('system_responsibilities',690,'系统任务结构：感知、交付、维护与独立评价','拟实施系统；一个感知节点、一个接收模块及现有PC，不代表已实物联调。')
    f.box(30,150,220,180,['感知诊断节点','P0 / P1 / Q','质量 / 候选模式','日志 / 事件缓存'],fill='#eaf1f7')
    f.box(300,150,160,180,['接收模块','E220','USB-TTL桥接','数据库在PC'],fill='#eef5f2')
    f.box(510,150,210,180,['PC接收服务','校验 / 去重','SQLite事务','提交后ACK'],fill='#eef5f2')
    f.box(775,150,200,180,['本地Web','趋势 / 证据','查看 / 处置','复测 / 留痕'],fill='#eaf1f7')
    for a,b,label in [(250,300,'LoRa'),(460,510,'UART'),(720,775,'读库')]:
        f.line([(a,204),(b,204)],True,label=label+' uplink');f.text((a+b)/2,136,label,23,anchor='middle')
    for a,b in [(510,460),(300,250)]:f.line([(a,282),(b,282)],True,label='commit ACK return');f.text((a+b)/2,362,'ACK',23,anchor='middle')
    f.line([(775,282),(720,282)],True,label='manual maintenance write to PC');f.text(747,362,'留痕',23,anchor='middle')
    f.box(30,445,310,116,['清水台架与独立参照','操作 / 压力参考 / 收集','标签独立于检测结果'],fill='#f8f2e8')
    f.box(415,445,560,116,['独立实验评价','对照检测、交付及维护记录','另测整机能量，保留误报与失败'])
    f.line([(140,445),(140,330)],True,label='bench to node sampling');f.text(158,417,'采集',23)
    f.line([(340,503),(415,503)],True,label='independent truth to evaluation')
    for x,mid in [(220,470),(615,615),(875,875)]:
        f.line([(x,330),(x,393),(mid,393),(mid,445)],True,True,label='evaluation logs')
    f.text(28,616,'实线：测量/业务连接；虚线：评价记录。ACK与人工查看、复测归档分开。')
    f.text(28,660,'无线模块只桥接字节；数据库事务在PC服务完成，真实接入尚待验证。',color='#52636a')
    f.save()

def workflow():
    f=drawing.Figure('diagnosis_proposal',850,'候选诊断处理流程与输出边界','拟实施处理流程；当前仿真仅含固定阈值与持续判据，切换门控未实现。')
    f.box(30,128,590,85,['保存原始P0/P1/Q与时间','核对配置、健康参照与操作信息'])
    def diamond(cx,cy,w,h,text):
        f.items.append(f'<path d="M {cx} {cy-h/2} L {cx+w/2} {cy} L {cx} {cy+h/2} L {cx-w/2} {cy} Z" fill="white" stroke="#172b30" stroke-width="2"/>')
        f.text(cx,cy+8,text,24,anchor='middle')
    f.line([(325,213),(325,235)],True,label='quality check');diamond(325,285,590,100,'数据有效且参照可比？')
    f.line([(620,285),(742,285)],True,label='invalid or unknown condition');f.text(680,266,'否',anchor='middle')
    f.box(742,237,228,96,['无效或暂缓判断','保留原值与原因'])
    f.line([(325,335),(325,371)],True,label='valid computation');f.text(363,363,'是')
    f.box(30,371,590,116,['计算特征并检验持续偏离','K=Q/√P1；R̂=(P0−P1)/Q²','按标定与误差预算冻结阈值'])
    f.line([(325,487),(325,519)],True,label='persistence check');diamond(325,569,590,100,'持续异常是否满足？')
    f.line([(620,569),(742,569)],True,label='no sustained departure');f.text(680,550,'否',anchor='middle')
    f.box(742,521,228,96,['继续保存记录','偏离不足不报故障'])
    f.line([(325,619),(325,655)],True,label='candidate output');f.text(363,647,'是')
    f.box(30,655,590,100,['输出候选模式与事件','泄漏 / 受限 / 异常待检查'])
    f.text(28,804,'未知正常负载仍可与泄漏同形；模式提示必须经独立核查。')
    f.text(28,838,'操作状态、时序对齐和误差区间门控须在真实采集后实现与验证。',color='#52636a');f.save()

if __name__=='__main__':
    architecture();workflow()
    water=ROOT/'application/figures/dual_pressure_layout.svg'
    (OUT/'water_layout.svg').write_bytes(water.read_bytes())
    drawing.records.append({'name':'water_layout','width':1000,'height':650,'classification':'proposed_water_relationship','connections':[],'svg_sha256':hashlib.sha256(water.read_bytes()).hexdigest(),'minimum_text_px':23,'minimum_text_pt_at_425pt_width':9.775,'copied_source':'application/figures/dual_pressure_layout.svg'})
    source=[Path(__file__),ROOT/'scripts/draw_interface_review.py',ROOT/'simulation/interface_review/interface_spec.json',ROOT/'simulation/diagnosis_review/protocol.json',water]
    data={'classification':'proposed_system_responsibility_and_workflow_not_implemented_firmware','physical_data':False,'figures':drawing.records,'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source}}
    (OUT/'figure_provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
