"""Select figures by argument, then build a fixed-width inspection artifact."""
from pathlib import Path
from html import escape
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/presentation_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    definitions=[
      ('F01','系统职责与独立评价','application/figures/presentation_review/system_responsibilities','proposed_system','方案：总体结构','测量、无线桥接、PC持久化与维护怎样组成系统？','数据库事务由PC服务完成，无线模块只桥接字节；实验标签独立。','拟实施职责图，未实物联调；不是本轮网站实际数据接入链。'),
      ('F02','双支路水路与观测区段','application/figures/presentation_review/water_layout','proposed_water_layout','方案：水力感知','为什么选P0/P1/Q，故障怎样注入和独立计量？','两压力为侧取压；Q在分流前包含正常与泄漏总量，B仅提供正常扰动。','水路关系非厂家尺寸图；流量计/接头压损、背压和供水待实测。'),
      ('F03','清水台架参数化装配候选','application/figures/collection_review/collection_overview','concept_cad','方案：台架实施','这个结构怎样服务预实验与重复操作？','装配布局、取压、受限及独立收集来自同一候选实体场景。','未制造；采购尺寸、整体装配及长时排水待验证，概念检查不等于可加工。'),
      ('F04','双压力与流量采集接口','application/figures/interface_review/measurement_interfaces','candidate_functional_interface','方案：采集硬件','电源、电压范围和脉冲电平怎样接到主控？','两路150Ω采样；ADC 3.3V；5V流量脉冲经容忍缓冲器转换。','保护/滤波定值未冻结，22mA已到ADC轨；不是投板或接线完成证据。'),
      ('F05','拟实施诊断流程与输出边界','application/figures/presentation_review/diagnosis_proposal','proposed_workflow','方案：诊断','无效、未持续偏离和候选异常怎样分别处理？','原始记录保留，持续偏离才生成模式提示，模式仍需独立核查。','切换门控及完整误差区间判定尚未实现；当前仿真只含固定阈值与持续规则。'),
      ('F06','不同压力噪声下的配对规则统计','application/figures/presentation_review/noise_outcomes_print','uncalibrated_simulation_print_variant','方案/基础：仿真','候选规则的收益和代价是否随噪声条件改变？','高压力噪声下固定Q规则更好，保留劣势；打印版仅增加纹理区分。','每格20种子，基础序列跨场景/噪声复用；区间为假定噪声模型内统计，不是实测准确率。'),
      ('F07','未知负载与压力漂移反例','application/figures/diagnosis_review/failure_counterexamples','uncalibrated_simulation_counterexample','方案/基础：失败边界','变化模式为什么不能直接当作故障原因？','未知正常负载可与泄漏同观测；真实阻力未变时漂移仍能触发受限模式。','seed10300示例；不得推出真实设备辨因或已实现误报抑制。'),
      ('F08','持久化确认与丢ACK路径','application/figures/interface_review/durable_event_sequence','candidate_protocol_host_checked','方案：可靠告警','怎样区分接收保存、重复去重与人工核查？','PC事务成功后确认，重发复用原身份；人工查看和复测分开。','主机字节/事务已检查；真实串口、RF、节点掉电未验，FIFO反例不满足20s期限。'),
      ('F09','运行主站诊断面板局部','application/figures/presentation_review/website_diagnosis_panel','actual_browser_synthetic_ui_capture','已有基础：软件','当前确实实现了哪一部分界面？','来自实际运行主站的原生截图，展示候选状态、特征、核查提示与事件入口。','合成观测，LoRa未接入；K/R̂用10点均值；不证明诊断性能或实物维修。')
    ]
    records=[]
    for ident,title,base,kind,section,question,claim,limit in definitions:
        png=ROOT/(base+'.png');svg=ROOT/(base+'.svg')
        assert png.is_file()
        source=[png]+([svg] if svg.is_file() else [])
        records.append({'id':ident,'title':title,'classification':kind,'placement':section,'question':question,'supported_claim':claim,'limit':limit,'png':png.relative_to(ROOT).as_posix(),'svg':svg.relative_to(ROOT).as_posix() if svg.exists() else None,'width_pt':425,'caption':f'{ident} {title}。'+limit,'sha256':{p.suffix.lstrip('.'):sha(p) for p in source}})
    supplements=[
      ('量程与测量界限','application/figures/diagnosis_review/range_and_measurement.png','量程/误差附表已足够时保留链接，不再重复正文图'),
      ('单次有效早期示例','application/figures/diagnosis_review/early_reference_example.png','需要解释早期定义时使用，不能替代全部成功/失败统计'),
      ('有界误差敏感性','application/figures/diagnosis_review/bounded_error_margin.png','支持阈值进入条件；静态界限不是分类器性能'),
      ('电源和候选引脚','application/figures/interface_review/power_and_pin_resources.png','支持接口附件，不与正文采集图重复展开'),
      ('泄漏容量与时长','application/figures/collection_review/collection_metering.png','支持短时计量及长时排水待项'),
      ('安装与取出空间','application/figures/collection_review/collection_installation.png','支持概念几何/检修讨论，非制造验收'),
      ('网页总览原生截图','application/figures/presentation_review/website_overview_desktop.png','仅作电子附件；整屏缩入Word达不到9pt，不纳入正文'),
      ('网页事件列表原生截图','application/figures/presentation_review/website_events_desktop.png','仅作电子附件，记录为人工演示；不是无线交付证据')
    ]
    supplemental=[{'title':t,'png':p,'decision':why,'default_word_insertion':False,'sha256':sha(ROOT/p)} for t,p,why in supplements]
    selection={'date':'2026-10-04','classification':'application_figure_selection_and_proof_not_final_word_layout','physical_data':False,'word_width_pt':425,'main_figures':records,'supplemental':supplemental,'replacement_policy':['system_scope → F01：区分模块桥接和PC持久化','bench_model → F03：使用收集优化同源布局','pressure_frontend → F04：补齐5V流量电平与未冻结保护','diagnosis_flow → F05：明确拟实施与当前仿真的差别','protocol_sequence → F08：正常和丢ACK路径分开','platform_replay → F09：使用当前运行主站而非旧研究面板','旧量程与早期图不继续混用新旧参数；按最新数据和目的选图'],'tables_for_A11':['T1 候选资源与条件预算：金额上限/展示价/报价分开','T2 四工作包：交付、指标、资源与证据对应','T3 独立故障、正常干扰与通信实验矩阵','T4 三阶段进度与里程碑：进入条件、任务与成果时间分开'],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'simulation/presentation_review/web_replay.json',ROOT/'simulation/presentation_review/capture_checks.json',ROOT/'application/figures/presentation_review/figure_provenance.json',ROOT/'application/figures/presentation_review/statistics_provenance.json']}}
    (OUT/'figure_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    panels=[]
    for r in records:
        local='../'+r['png'];panels.append(f'<article id="{r["id"]}" data-figure="{r["id"]}"><div class="figure-header"><span>{r["id"]}</span><h2>{escape(r["title"])}</h2></div><div class="image"><img src="{escape(local,quote=True)}" alt="{escape(r["title"],quote=True)}"></div><p class="caption">{escape(r["caption"])}</p><dl><dt>回答问题</dt><dd>{escape(r["question"])}</dd><dt>正文论点</dt><dd>{escape(r["supported_claim"])}</dd><dt>拟放位置</dt><dd>{escape(r["placement"])}</dd></dl><a class="source" href="{escape(local,quote=True)}">打开原图</a></article>')
    nav=''.join(f'<a href="#{r["id"]}">{r["id"]}</a>' for r in records)
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>申报图文取舍与呈现审阅</title><style>
    *{box-sizing:border-box}body{margin:0;color:#19343c;background:#edf1f3;font:14px/1.7 'Microsoft YaHei',sans-serif}header{max-width:850px;margin:36px auto 22px;padding:0 24px}h1{font-size:25px;margin:0 0 8px}header p{color:#50666e}nav{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:16px 0}a{color:#246652;text-underline-offset:4px}nav a,button{background:white;border:1px solid #afc3ca;border-radius:6px;padding:8px 12px;min-height:44px;font:inherit;text-decoration:none;cursor:pointer}a:focus-visible,button:focus-visible{outline:3px solid #315c95;outline-offset:3px}article{width:calc(473pt + 2px);max-width:calc(100% - 32px);margin:24px auto;padding:24pt;background:white;border:1px solid #d5dfe3;border-radius:9px;break-inside:avoid}h2{font-size:13pt;margin:0}.figure-header{display:flex;gap:12px;align-items:center;margin-bottom:12pt}.figure-header>span{font-size:10pt;font-weight:bold;color:#526b73}.image{width:425pt;max-width:100%;line-height:0}.image img{display:block;width:100%;height:auto}.caption{font:10.5pt/1.55 SimSun,'Microsoft YaHei',serif;margin:10pt 0}dl{font:10.5pt/1.6 SimSun,'Microsoft YaHei',serif;border-top:1px solid #dce4e7;padding-top:10pt;margin:10pt 0}dt{font-weight:bold}dd{margin:0 0 8pt}.source{font-size:10pt}.gray .image img{filter:grayscale(1)}@media print{header{display:none}body{background:white}article{border:0;border-radius:0;margin:0;break-after:page}}@media(max-width:650px){header{margin-top:22px}article{padding:18px}.caption,dl{font-size:13px}}
    </style><header><h1>申报图文取舍与呈现审阅</h1><p>九张正文候选图。宽屏按425pt显示，图注逐项说明论点与边界；手机缩放不替代字号验收。本页是配套图文审阅，学校Word/PDF尚未整合。</p><nav>__NAV__<button id="gray" aria-pressed="false">查看灰度</button></nav><p><a href="../docs/网站佐证与申报图表分项验收.md">取舍与验收报告</a> · <a href="index.html">运行主站</a></p></header>__PANELS__<script>document.getElementById('gray').addEventListener('click',function(){const on=document.documentElement.classList.toggle('gray');this.setAttribute('aria-pressed',String(on));this.textContent=on?'恢复彩色':'查看灰度';});</script></html>'''
    html=html.replace('__NAV__',nav).replace('__PANELS__',''.join(panels))
    (ROOT/'deliverables/申报图文取舍与呈现审阅.html').write_text(html,encoding='utf-8',newline='\n')
    print('9 main figures selected; 8 supporting links; 425pt inspection artifact built, not Word acceptance.')
if __name__=='__main__':main()
