"""Integrate verified journal references and their concrete scope into the application."""
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
meta_path = ROOT/'docs/中文文献来源核验.json'
records = json.loads(meta_path.read_text(encoding='utf-8'))
for record in records:
    record['metadata'] = [(k,v) for k,v in record.get('metadata',[]) if not any(x in k.lower() for x in ['abstract','description','keywords','subject','rights'])]
meta_path.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

def item(language, authors, title, journal, year, volume, issue, pages, doi, url, support, limit, verification):
    return dict(language=language,authors=authors,title=title,journal=journal,year=year,volume=volume,issue=issue,pages=pages,doi=doi,url=url,support=support,limit=limit,verification=verification)

CN = [
    item('中文','李慧琴, 王潭刚, 孔宪辉','新疆南疆棉花“滴水出苗”技术问题及建议','中国棉花',2022,'49','6','36-38','10.11963/cc20220080','https://journal.cricaas.com.cn/zgmh/CN/10.11963/cc20220080','南疆应用背景与滴灌压力管理','技术建议不是故障诊断装置的性能试验','期刊页面题名作者、卷期页码及摘要'),
    item('中文','丁法龙, 茅泽育, 王文娥, 等','滴灌管主流道沿程压力分布模型及验证','农业工程学报',2019,'35','3','117-124','10.11975/j.issn.1002-6819.2019.03.015',records[0]['url'],'沿程压力模型需要水力分析与测压验证','分布式滴灌管模型不能直接等同集中平方律模型','期刊元数据与摘要'),
    item('中文','王亚林, 李京芳, 鄢锐, 等','圆柱式滴头内镶及外包对滴灌毛管水力特性影响的模拟研究','华南农业大学学报',2021,'42','4','106-112','10.7671/j.issn.1001-411X.202009004',records[6]['url'],'滴头安装形态影响毛管压损，仿真应有实测校核','该文CFD与灌水试验不是本项目已有成果','期刊HTML题名作者、引文格式、摘要及全文'),
    item('中文','喻黎明, 曹丽, 李娜, 等','额定流量与毛管位置对纽扣式滴头堵塞的影响及机理分析','农业工程学报',2023,'39','20','123-131','10.11975/j.issn.1002-6819.202307109',records[1]['url'],'含沙水堵塞受滴头流量和毛管位置影响','清水节流阀不复现泥沙沉积机理','期刊元数据与摘要'),
    item('中文','王惠, 凌刚, 查晴, 等','肥料种类与浓度对灌水器堵塞特征的影响及防堵策略','农业工程学报',2023,'39','5','53-60','10.11975/j.issn.1002-6819.202212095',records[2]['url'],'水肥化学堵塞需要长期试验及材料分析','本期不开展化学堵塞材料机理验证','期刊元数据与摘要'),
    item('中文','张唯一, 肖洋, 马长健, 等','水流近壁面水力剪切力对滴灌系统碳酸钙污垢的影响','农业工程学报',2023,'39','7','137-144','10.11975/j.issn.1002-6819.202208008',records[3]['url'],'水力条件与化学污垢存在耦合','不能把阻力增加提示解释为碳酸钙成分识别','期刊元数据、原文首页引文与摘要'),
    item('中文','付建民, 赵振洋, 陈国明, 等','液相管道流量与压力对小孔泄漏速率的影响','石油学报',2016,'37','2','257-265','10.7623/syxb201602013',records[10]['url'],'泄漏速率与压力、流量及运行条件相关','油气输送研究的参数及精度不能直接移植滴灌','浏览工具读取期刊页面引文与摘要；本机requests未成功'),
    item('中文','龚骏, 税爱社, 包建明, 等','多工况下基于RBF神经网络的管道泄漏检测','油气储运',2015,'34','7','759-763','10.6047/j.issn.1000-8241.2015.07.017',records[7]['url'],'正常工况调节与泄漏需要区分','研究对象和算法条件不同，不引用其识别率作为本项目目标依据','期刊元数据与摘要；页面迁移日期不当作发表年'),
    item('中文','马大中, 胡旭光, 孙秋野, 等','基于数据特征融合的管网信息物理异常诊断方法','自动化学报',2019,'45','1','163-173','10.16383/j.aas.2018.c180383',records[8]['url'],'区分物理异常与传输中断、错误异常','输油管网方法不代表本原型已实现CNN或信息攻击检测','期刊引文、元数据、摘要及页面图表；DOI含2018但发表年为2019'),
    item('中文','孟祥, 赵莹, 徐卓威, 等','基于LoRa技术的农田智能灌溉系统设计','中国农机化学报',2023,'44','9','161-168','10.13733/j.jcam.issn.2095-5553.2023.09.023',records[4]['url'],'农田LoRa节点、通信与灌溉系统组成已有研究','LoRa灌溉本身不是创新，其无线指标不能作为本项目实测','期刊元数据与摘要'),
    item('中文','刘天翔, 郭文忠, 韩晓蓓, 等','基于称量反馈的设施番茄灌溉系统的构建与应用','农业工程学报',2024,'40','13','85-96','10.11975/j.issn.1002-6819.202401146',records[5]['url'],'传感、称量反馈、灌溉通信和系统集成的研究实例','设施番茄闭环灌溉不同于南疆支管故障巡检','期刊元数据与摘要'),
]
EN = [
    item('英文','Petit J, García S M, Molle B, et al','Methods for drip irrigation clogging detection, analysis and understanding: State of the art and perspectives','Agricultural Water Management',2022,'272','','107873','10.1016/j.agwat.2022.107873','https://www.sciencedirect.com/science/article/pii/S0378377422004206','水力监测为间接方法，最初堵塞阶段可能不可观测','不等于所有水力故障都能提前识别','保留原引用，出版社摘要及引文核对'),
    item('英文','Somaali N, Hayouni M, Sboui L, et al','HydroNeuro: A Data-Efficient IoT Sensing and Edge-AI Framework for Real-Time Hydraulic Anomaly Detection','Sensors',2026,'26','10','3010','10.3390/s26103010','https://www.mdpi.com/1424-8220/26/10/3010','阀态、嵌入式异常感知与扰动鲁棒性已有研究','不宣称本项目已具有Edge-AI性能','保留原引用，出版社论文与版本记录核对'),
    item('英文','Loukatos D, Fragkos A, Londra P, et al','A Simple Platform for Emulating Irrigation Scenarios and Its Applicability for Big Data Collection Toward Water Preservation via In Situ Experiments','Land',2026,'15','3','464','10.3390/land15030464','https://www.mdpi.com/2073-445X/15/3/464','可控阀、压力流量与LoRa灌溉模拟平台','本项目台架架构不是首创；模拟不等于真实堵塞','保留原引用，出版社正式版核对，未改为预印本'),
    item('英文','Lozoya C, Favela-Contreras A, Aguilar-Gonzalez A, et al','Energy-Efficient Wireless Communication Strategy for Precision Agriculture Irrigation Control','Sensors',2021,'21','16','5541','10.3390/s21165541','https://pmc.ncbi.nlm.nih.gov/articles/PMC8402102/','事件通信、周期对照和实际功耗评价','原文的节能比例不能作为本项目预计实测收益','保留原引用，原文PMC及出版社PDF核对'),
    item('英文','Orihuela L, Bareiro J, Reales F, et al','Long-term assessment of event-based communication for irrigation control in a bell pepper farm','IFAC-PapersOnLine',2025,'59','23','44-49','10.1016/j.ifacol.2025.11.761','https://www.sciencedirect.com/science/article/pii/S2405896325024590','农业事件通信的长期现场评价','灌溉控制不等于故障告警；本项目尚无长期实测','保留原引用，出版社检索记录及会议官方程序44-49页作者表核对'),
    item('英文','Sun Z, Wang Z, Li J','Identification and Evaluation of the Main Constraints on Cotton Production Within a Collective Drip Irrigation System in Southern Xinjiang, China','Agronomy',2025,'15','4','760','10.3390/agronomy15040760','https://www.mdpi.com/2073-4395/15/4/760','南疆集体滴灌棉花生产约束','不能据此给出本原型节水、增产比例','保留原引用，出版社资料及作者同题会议稿核对'),
]
refs = CN+EN
for n, ref in enumerate(refs,1):
    ref['number']=n
    issue = '('+ref['issue']+')' if ref['issue'] else ''
    ref['citation']=f"[{n}] {ref['authors']}. {ref['title']}[J]. {ref['journal']}, {ref['year']}, {ref['volume']}{issue}: {ref['pages']}. DOI:{ref['doi']}."
assert len(refs)==17 and len(CN)>len(EN)
data={'date':'2026-10-04','chinese':len(CN),'english':len(EN),'chinese_share':round(len(CN)/len(refs),4),'no_physical_performance_claim':True,'references':refs}
(ROOT/'application/references.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

review='''## 四、国、内外研究现状和发展动态

### 1 南疆应用需求与研究对象

李慧琴等结合南疆棉花“滴水出苗”提出压力均匀、铺管及用水管理建议[1]，说明运行压力是区域滴灌管理中需要关注的条件。Sun等研究南疆集体滴灌棉花生产约束，涉及灌水深度和土壤条件[17]。这些工作支持选择南疆滴灌巡检场景，但不直接证明本原型能够节水或增产。本期以支管水力故障的可观测变化为对象，实际轮灌方式与安装条件仍需现场核对。

### 2 滴灌水力模型与测量依据

丁法龙等从变质量流动分析沿程压力，并以测压、测流试验验证模型[2]；王亚林等结合灌水试验与CFD研究不同滴头镶嵌方式对毛管水力特性的影响[3]。已有研究表明，实际滴灌压损需要考虑分布出流、结构与安装。本项目集中平方律模型仅用于监测区段的初步设计，不替代上述分布模型。实施时先检验健康压力—流量关系及残差，再冻结特征和阈值；拟通过布点、同步误差与差压不确定度的联合评价确定低成本测量的适用条件。

### 3 堵塞机理与早期监测边界

喻黎明等研究含沙水下额定流量、毛管位置与滴头堵塞的关系[4]；王惠等开展不同肥料及浓度的堵塞试验[5]；张唯一等研究近壁面水力剪切力与碳酸钙污垢的作用[6]。三类工作说明堵塞演化受水质、材料和水力条件影响。Petit等综述进一步指出，压力流量监测属于间接方法，未必反映滴头堵塞的最初阶段[12]。因此本项目用清水节流阀验证等效受限的水力响应，不把阀门操作写成泥沙、化学或生物堵塞试验；“早期”以独立测量确认的故障程度和预设失效参照评价，不宣称识别单滴头微观堵塞起点。

### 4 多工况诊断与可控验证

付建民等通过液相管道试验与模拟研究压力、流量对小孔泄漏速率的影响[7]；龚骏等研究多工况下泄漏与正常调节的区分[8]；马大中等将物理异常与信息传输异常纳入管网诊断[9]。这些输油或液相管道研究提供了耦合分析与异常分层的思路，参数、传感条件和识别率不能直接移植到滴灌。HydroNeuro研究阀态建模、嵌入式异常感知与扰动鲁棒性[13]，Loukatos等利用可控阀、压力流量及LoRa构建灌溉模拟平台[14]，也说明状态辅助和可控台架已有基础。本项目拟以同信息强基线、独立操作标签和跨批次留出验证研究渐进故障的辨识边界，保留未知负载、漂移及切换期间的失败实例。

### 5 农业物联网与通信评价

孟祥等完成基于LoRa的农田智能灌溉系统设计[10]；刘天翔等构建设施番茄称量反馈灌溉系统[11]，为传感、通信和软件组织提供国内系统研究实例。本项目将系统交付细化为测量节点、接收存储、有限诊断、事件证据与管理确认，不能仅以使用LoRa或增加页面作为创新。Lozoya等以田间对照评价事件通信与功耗[15]，Orihuela等开展农业事件通信的长期评估[16]。本项目拟在检测器、载荷和确认机制相同条件下比较周期与事件策略，将本地检测延迟、远端送达延迟和整机能量分别测量，不以发送帧数推算真实续航。

### 6 本项目拟研究的增量

上述中文研究构成场景、水力、堵塞、诊断和系统集成的主要依据，英文研究补充间接监测边界、可控平台及通信评价。拟研究的增量集中于两个问题：低成本双压力流量与操作信息在何种故障程度和误差条件下能够改善巡检提示；在统一检测与确认机制下，减少通信是否仍能维持远端及时告警。通过可重复台架、强对照与分层评价形成结论，是否具有可发表贡献以进一步全文研读和独立实测为准。

参考文献

'''
review += '\n\n'.join(r['citation'] for r in refs)
review += '\n\n制度参考：塔里木大学大学生创新创业训练计划实施细则，校教发〔2025〕1号，2025-01-02，https://jwc.taru.edu.cn/info/1035/3872.htm。本批要求以正式通知为准。\n\n'
path = ROOT/'application/正式模板正文.md'
text = path.read_text(encoding='utf-8')
text = re.sub(r'## 四、国、内外研究现状和发展动态\n.*?(?=## 五、)',lambda m:review,text,flags=re.S)
text = text.replace('2026年10月3日研究正文修订稿','2026年10月4日研究正文修订稿')
path.write_text(text,encoding='utf-8',newline='\n')

notes=['# 参考文献核验与正文对应','', '2026年10月4日。申报书保留原有6篇英文论文，新增11篇中文期刊文献，共17篇，中文占64.7%。学校制度及供应商资料单独列示，不充当中文学术论文数量。','', '核验范围为期刊原始页面、公开摘要、引文元数据及可取得的原文页面；不将摘要核对写成全部17篇均已逐页阅读全文。正文中的解释与方案取舍属于本项目分析，引用文献的原实验结果不当作本项目成绩。','', '| 编号 | 文献与原始入口 | 支撑的论证 | 不能推出的结论 | 核验范围 |','| --- | --- | --- | --- | --- |']
for r in refs:
    notes.append(f"| [{r['number']}] {r['language']} | [{r['title']}]({r['url']})；DOI {r['doi']} | {r['support']} | {r['limit']} | {r['verification']} |")
notes += ['', '编号按中文研究主题在前、英文补充在后组织。正文第四节逐项引用，文末有完整作者、期刊、年份、卷期、页码或文章号及DOI；页码依据期刊元数据，而不从DOI编号猜测。原[1]—[6]英文条目顺序保留，编号对应更新为[12]—[17]。', '', '执行前优先阅读全文[2][3][4][8][10][12]—[16]，核对试验标签、压力流量测点、正常调节对照、事件触发与能量测量。对新方法的原创性判断应继续检索直接相关工作，当前材料不宣称已经证明首创或发表条件。']
(ROOT/'docs/参考文献核验与正文对应.md').write_text('\n'.join(notes)+'\n',encoding='utf-8',newline='\n')
print('Integrated 11 Chinese + 6 retained English journal references; body cites all 17.')
