"""Prepare a separate release; historical receipts and document remain intact."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def save(path,s):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8',newline='\n')

s=(ROOT/'scripts/verify_presentation_site.mjs').read_text(encoding='utf-8')
s=s.replace("'presentation_site_review'","'quality_site_review'").replace("date:'2026-10-04'","date:'2026-10-05'")
s=s.replace("'simulation/presentation_review','site_checks.json'","'simulation/quality_review','site_checks.json'")
s=s.replace("await copyFile(path.join(scratch,'overview-final-desktop.png'),path.join(root,'deliverables','网站预览.png'));",'')
extra='''
 await send('Emulation.setDeviceMetricsOverride',{width:667,height:375,deviceScaleFactor:1,mobile:false});
 for(const page of pages){await evaluate(`operations.navigate('${page}')`);const result=await evaluate(`(()=>{if(document.documentElement.scrollWidth>innerWidth+1)throw Error('Landscape overflow');return {page:'${page}',width:innerWidth,height:innerHeight,overflow:false}})()`);report.navigation_checks.push(result);}
 await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1120,deviceScaleFactor:1,mobile:false});
 await check('chart_current_time_marker_and_accessible_description',`operations.setReplay({scenario:'leak',noise:'0.3',quality:'replay',time:450});operations.navigate('overview');for(const el of document.querySelectorAll('#overview-pressure svg,#overview-flow svg')){if(!el.querySelector('title')||!el.querySelector('desc'))throw Error('Accessible chart text missing');if(!el.querySelector('desc').textContent.includes('450'))throw Error('Current time missing');}if(!document.querySelector('#overview-pressure svg circle'))throw Error('Pressure current marker missing');`);
 await screen('quality-overview-desktop');
 await send('Emulation.setDeviceMetricsOverride',{width:375,height:1120,deviceScaleFactor:1,mobile:false});await screen('quality-overview-mobile');
'''
s=s.replace(" if(report.console_errors.length||report.external_requests.length)",extra+" if(report.console_errors.length||report.external_requests.length)")
save('scripts/verify_quality_site.mjs',s)

s=(ROOT/'scripts/capture_application_panel.mjs').read_text(encoding='utf-8')
s=s.replace('application/figures/application_integration','application/figures/quality_review').replace("'application_panel_capture'","'quality_panel_capture'").replace('simulation/application_integration/website_capture_checks.json','simulation/quality_review/website_capture_checks.json')
save('scripts/capture_quality_panel.mjs',s)

source=ROOT/'application/正式模板正文.md';s=source.read_text(encoding='utf-8')
for folder in ['presentation_review','collection_review','interface_review','diagnosis_review','application_integration']:
    s=s.replace(f'(figures/{folder}/', '(figures/quality_review/')
old='当前24组模型网格最大泄漏1.055L/min，30秒取样并乘1.25余量需要659.4mL；候选空腔几何容量678.6mL。杯口与出口保持20mm自由出流间隙，收集不应淹没出口或形成背压。几何容量尚未扣除防溅和安全液位，实际有效容量不足时缩短取样或更换容器。长时连续实验另设排水与分次取样，不能用小杯承接8小时泄漏。'
new='当前24组模型网格最大泄漏1.055L/min，候选空腔几何容量678.6mL。原30秒取样乘1.25余量需659.4mL，尚未扣除防溅和安全液位；本轮改为拟采用20秒分次取样，按同一上界需要439.6mL。实施前量取实际有效容量，至少达到440mL方采用该时长；实际泄漏超过模型上界时重算。杯口与出口保持20mm自由出流间隙，收集不得淹没出口或形成背压。长时实验另设排水，计时与称量误差须纳入标定。容量及取样窗口分析另附电子图，不把空腔计算当作容器实测。'
assert old in s or new in s;s=s.replace(old,new)
old='现有高斯回放没有实现离散脉冲计数，不可写成完整采集固件验证。'
new='新增20,000组恒定流量与脉冲相位枚举验证理想计数步长，未包含抖动、漏脉冲及器件误差。现有高斯诊断回放未实现脉冲计数；实施时须另测10秒窗约5秒均值滞后对提前量的影响，不能将这些计算写成固件验证。'
assert old in s or new in s;s=s.replace(old,new)
s=s.replace('2026年10月5日申报正文整合稿。','2026年10月5日格式优化申报正文。')
s=s.replace('基础结项后优先延伸跨工况迁移：同台架增加负载档和独立日期，比较冻结参照、少量健康重标定及实测经验模型，以整档留出研究测量误差与适应成本[2,12,13]。第二方向是在新增真实节点、公共供压参照和同步日志后研究多支管共同扰动、局部异常及事件竞争[10,13]。第三方向依赖长期维护配对记录，检验参照漂移、复测稳定性和人工核查工作量[12,16]。扩展具有具体数据与资源进入条件，不挤占单区段基础验证。','结项后优先研究跨工况迁移：增加负载档和日期，比较冻结参照、少量健康重标定与经验模型，整档留出评价误差和适应成本[2,12,13]。新增节点、公共供压和同步日志后，再研究多支管共同扰动、局部异常与事件竞争[10,13]。长期维护配对记录可用于检验参照漂移、复测稳定性及核查工作量[12,16]。扩展须落实数据和资源，基础任务仍为单区段验证。')
s=s.replace('种子10300、σ=0.3kPa示例：泄漏402s确认、454s到演示参照，提前52s；受限384s确认、494s到参照，提前110s。单轨迹、种子统计和失败数量分别报告，不以个别成功提前量掩盖误报。独立参照不输入检测规则。','种子10300、σ=0.3kPa：泄漏402s确认、454s到演示参照，提前52s；受限384s确认、494s到参照，提前110s。单轨迹、种子统计与失败数分别报告；成功提前量不能掩盖误报，独立参照不输入检测规则。')
s=s.replace('单轨迹、种子统计与失败数分别报告；成功提前量不能掩盖误报，独立参照不输入检测规则。','独立参照不输入检测规则；单轨迹提前量不能掩盖总体失败。')
s=s.replace('六页面四宽度、19项软件流程及3个实际导出检查通过','本轮六页面四宽度及横屏、20项软件流程和3个实际导出检查通过')
save('application/正式模板正文.md',s)

s=(ROOT/'scripts/prepare_application_payload.py').read_text(encoding='utf-8')
s=s.replace("ROOT/'tmp/reference_review'","ROOT/'tmp/quality_application'").replace('width=380 if','width=390 if').replace('else 410','else 420').replace('[55,105,155,110]','[70,100,145,110]')
save('scripts/prepare_quality_payload.py',s)
s=(ROOT/'scripts/fill_application_template.ps1').read_text(encoding='utf-8-sig')
s=s.replace('tmp\\application_integration\\candidate','tmp\\quality_application\\candidate').replace('tmp\\reference_review\\application_payload.json','tmp\\quality_application\\application_payload.json').replace('$native.Range.Font.Size=9.5','$native.Range.Font.Size=10.5').replace('$caption.Font.Size=9','$caption.Font.Size=9.5')
s=s.replace('^(有效早期要求|已形成17篇|图9展示|对288个静态有界误差组合|已核对17个候选引脚)', '^(运行\\s*Web|种子10300|有效早期要求|已形成17篇|图9展示|对288个静态有界误差组合|已核对17个候选引脚)')
s=s.replace("$p.Range.Font.Size = 10.5\n            $p.Range.ParagraphFormat.LeftIndent=0\n            $p.Range.ParagraphFormat.RightIndent=0\n            $p.Range.ParagraphFormat.Alignment=1", "$p.Range.Font.Size = 15\n            $p.Range.ParagraphFormat.CharacterUnitFirstLineIndent=0\n            $p.Range.ParagraphFormat.LeftIndent=135\n            $p.Range.ParagraphFormat.FirstLineIndent=-75\n            $p.Range.ParagraphFormat.RightIndent=0\n            $p.Range.ParagraphFormat.Alignment=0")
s=s.replace('$p.Range.Text = "起止时间：2027年3月至2028年2月`r"', '$p.Range.Text = "起止时间：2027年3月至2028年2月`r";$p.Range.ParagraphFormat.LeftIndent=60;$p.Range.ParagraphFormat.FirstLineIndent=0;$p.Range.Font.Size=15')
save('scripts/fill_quality_application.ps1',s)
print('Prepared separate quality scripts and revised nine-section source.')
