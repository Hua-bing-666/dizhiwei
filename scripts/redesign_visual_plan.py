"""Apply the user's requested visual correction to the retained, factual roster."""
from pathlib import Path
import json,re,shutil
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'projects/drip-research_ppt169_20261002'
TMP=ROOT/'tmp/visual_redesign';TMP.mkdir(parents=True,exist_ok=True)
for name in ['立项答辩.pptx','立项答辩审阅版.pdf']:
    if not (TMP/name).exists():shutil.copy2(ROOT/'deliverables'/name,TMP/name)
titles=['南疆滴灌支管早期故障诊断','看见变化，才能判断故障','研究增量，落在实验里','一个系统，四个工作包','测点包围目标区段','早期，必须早于失效判据','少发帧，也要保住证据','测点增加，边界仍然存在','把诊断结果交给使用者','用独立实验兑现研究目标','一年推进，按条件过关','交付原型，也交付证据','相同观测，可能有不同原因','申报、结项、论文分层完成','来源与可复现记录']
deck=json.loads((P/'analysis/deck_content.json').read_text(encoding='utf-8'))
oldtitles=[d['title'] for d in deck]
for d,title in zip(deck,titles):d['title']=title
(P/'analysis/deck_content.json').write_text(json.dumps(deck,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
spec=(P/'design_spec.md').read_text(encoding='utf-8')
lock=(P/'spec_lock.md').read_text(encoding='utf-8')
for old,new in zip(oldtitles,titles):spec=spec.replace(old,new)
for path in [ROOT/'application/PPT逐页内容与讲稿.md',P/'notes/total.md']:
    value=path.read_text(encoding='utf-8')
    for old,new in zip(oldtitles,titles):value=value.replace(old,new)
    path.write_text(value.rstrip()+'\n',encoding='utf-8',newline='\n')
spec=spec.replace('SimHei, Arial','Microsoft YaHei, Arial').replace('| SimHei |','| Microsoft YaHei |')
spec=spec.replace('稳定的页眉、细分隔线与来源脚注建立研究材料的秩序。证据页让坐标与数据占主导，系统页以连接和包含表达真实依赖，结尾保留显著留白；平面颜色表示状态而非装饰。','深色场景及架构页与浅色证据页交替；场景以滴灌田块概念模型为主体，架构用分层关系，管理用真实合成回放界面，证据页标出首次提示和失效参照。避免全文字横线页，源注缩为一行，保留模拟和设计状态。')
spec=spec.replace('深绿结构线与暖白证据版面','农业科技场景与清晰研究证据').replace('| Display | 60 |','| Display | 64 |\n| Hero | 72 |\n| Diagram label | 20 |')
spec=spec.replace('| Grid | #E0E7E2 | 坐标辅助线 |','| Grid | #E0E7E2 | 坐标辅助线 |\n| Dark surface | #092E2B | 场景和架构主体 |\n| Signal | #78DFC5 | 深底感知与通信 |\n| Warm highlight | #F3C77B | 深底研究重点 |')
lock=lock.replace('title_family: SimHei, Arial','title_family: Microsoft YaHei, Arial').replace('- display: 60','- display: 64\n- hero: 72\n- diagram_label: 20')
lock=lock.replace('- grid: #E0E7E2','- grid: #E0E7E2\n- dark_surface: #092E2B\n- signal: #78DFC5\n- warm_highlight: #F3C77B')
lock=lock.replace('暖白证据版面、深绿结构线、克制异常强调；以坐标、依赖和阶段表达语义，图表与系统页具有不同空间组织','深色场景/架构与浅色证据交替；概念场景、分层系统、布点、软件界面、判据标注和实验网格各有对应载体')
compositions=['标题与田块/节点/接收端概念模型左右展开','滴灌支管场景与正常/泄漏/受限三个状态映射','三条已有工作到候选增量的对应关系','感知—诊断—可靠通信—管理分层并列，研究工作归属明确','上侧测点水路，下侧测点角色与两个特征；原生公式','主图标出首次提示/失效，右栏给示例提前量；两类型区分','两个匹配坐标图，底部共享解释；语义图例和单位完整','12/20重点与两条失效证据、成立条件并排','合成回放界面为主体，右栏设备/趋势/事件/回放功能','54次独立操作的实验矩阵，三个验证层级及8h条件','时间门槛横向推进，下侧预算分类与借用条件','一个原型与一组可复现证据作为两类成果','两个原因汇入同一观测，条件决定输出','三个阶段各自列出材料/系统/论文完成要求','文献DOI与程序/协议按来源分组']
for i,comp in enumerate(compositions,1):
    pattern=rf'(#### Slide {i:02}[^\n]*\n)'
    spec=re.sub(pattern,lambda m:m[1]+'\n- **Composition**: '+comp+'\n',spec,count=1)
(P/'design_spec.md').write_text(spec,encoding='utf-8',newline='\n')
(P/'spec_lock.md').write_text(lock,encoding='utf-8',newline='\n')
(P/'analysis/production_decisions.md').open('a',encoding='utf-8').write('\n2026-10-03视觉纠正：用户指出视觉效果明显不符合要求。旧稿静态结构/程序检查不能证明设计完成度。保留15页研究事实与顺序，重构场景、架构、布点、早期证据和软件页，按实际PPTX原生渲染检查，未改变合成结果为实测。\n')
(ROOT/'docs/视觉复核与重设计.md').write_text('''# 视觉复核与重设计

2026年10月3日，依据用户对视觉效果的反馈。旧版文件技术检查通过，视觉完成度不达标；不以“能打开”“不越界”替代设计评价。

| 范围 | 旧版具体问题 | 本轮纠正 |
| --- | --- | --- |
| 封面与场景 | 右侧只有P/Q线框，缺少滴灌支管与系统使用场景；概念图还遗漏第二压力点 | 完整场景概念模型，P0/P1/Q、接收端和管理关系，明确非实物 |
| 工作包与系统 | 多页文字加横线；系统页再次重复流程，未展示软件 | 四层架构有归属；用真实合成回放界面解释管理任务 |
| 水路布点 | 几何符号过于粗略，角色需要依赖正文解释 | 分开水路、测点角色与特征，受限前/后及总流量关系明确 |
| 早期证据 | 只有两条渐进曲线与水平判据，没有突出首次正确提示 | 加入真实模型记录的检测和临界时刻，标注示例提前量 |
| 文档插图 | 三幅宽图塞在同一页；标题重复，小图标注难读，水路线穿过元件文字 | 拆分图页、缩短图中文字，图注保持证据状态，重新原生导出 |
| 网站 | 以大段文字和重复面板组织，场景与诊断入口不突出 | 场景主体、清晰入口与当前回放界面，保留离线/无效状态 |

保持原题目、四工作包、2000元启动估算、2027.03—2028.02和真实证据边界。参考PPT用于判断科技项目的视觉组织，不复制其团队、商业收益、实物照片或效果比例。
''',encoding='utf-8',newline='\n')
print('Visual revision plan applied to the retained 15-slide project.')
