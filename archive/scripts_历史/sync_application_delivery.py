"""Synchronize delivery labels after the application-first revision."""
from pathlib import Path
import pymupdf
ROOT=Path(__file__).resolve().parents[1]
def edit(path,old,new):
    p=ROOT/path;s=p.read_text(encoding='utf-8')
    if new in s:return
    s=s.replace(old,new);p.write_text(s,encoding='utf-8',newline='\n')
pages=pymupdf.open(ROOT/'deliverables/大创申报书_模板审阅版.pdf').page_count
scope=pymupdf.open(ROOT/'deliverables/项目书审阅版.pdf').page_count
edit('README.md','11页，原封面、九节正文、三幅图及原审批栏。',f'{pages}页，原封面、九节正文、9幅图、4张可编辑表及审批栏；图文按论证步骤展开。')
edit('README.md','5页，明确申报、结项、论文的不同标准。',f'{scope}页，明确申报、结项、论文的不同标准。')
edit('README.md','12页主讲、3页备用，附15页讲稿。','视觉修订草案，12页主讲、3页备用，附15页讲稿；最新硬件及预算尚待同步，后续再完成。')
edit('README.md','约2000元是借用参考仪器条件下的启动额度估计','约2000元以借用参考仪器及可调连续水源为前提，两压力传感器待询价，是启动额度估计')
edit('README.md','- [案例对照与老师建议分析]','- [国内硬件选型与淘宝入口](docs/国内硬件选型与可行性核对.md) / [国家级案例写法拆解](docs/国家级案例写法拆解与申报书改写.md)。\n- [案例对照与老师建议分析]')
edit('README.md','图形/PDF脚本依赖','诊断数据复跑后，应再运行 `scripts/redesign_document_figures.py` 恢复申报版图形；设计图运行 `scripts/build_application_design_figures.py`，硬件核对运行 `simulation/hardware_design_check.py`。PPT新图形源为 `scripts/author_visual_redesign.py`。`rewrite_application_argument.py`、`redesign_visual_plan.py`及`redesign_portal_surface.py`是一次性迁移脚本，不重复覆盖当前材料。\n\n图形/PDF脚本依赖')
edit('deliverables/使用说明.md','11页Word',f'{pages}页Word（9幅图、4张可编辑表）')
edit('deliverables/使用说明.md','单独的5页范围与执行文件',f'单独的{scope}页范围与执行文件')
edit('deliverables/使用说明.md','4. `立项答辩.pptx` 含','4. PPT目前为视觉修订草案，最新候选硬件与预算尚待同步，后续完成。`立项答辩.pptx` 含')
edit('deliverables/使用说明.md','Word和PPT完成WPS原生导出、逐页渲染与排版查看；网站完成','Word完成WPS原生导出和逐页排版复核；PPT原生导出为待同步草案。网站交互检查包含')
edit('deliverables/使用说明.md','提交前需填写真实负责人/团队/导师','国内硬件、淘宝入口、候选配图及量程约束见 `../docs/国内硬件选型与可行性核对.md`；配图非项目实物，入口不保证现货价格。压力报价与连续水源借用是待落实条件。\n\n提交前需填写真实负责人/团队/导师')
edit('scripts/portal.template.html','<h1>研究论证版答辩材料。</h1>','<h1>研究论证版答辩材料。</h1><p class="note">PPT视觉修订草案；最新候选硬件和预算尚待同步，申报范围以本轮正式Word为准。</p>')
edit('scripts/portal.template.html','2000元是额度估算，非报价；需借参考仪器。','2000元是额度估算，非报价；需借参考仪器及可调连续水源，两压力待询价。')
edit('scripts/portal.template.html','<a href="../docs/案例对照与老师建议分析.md">两个案例的特点及本项目调整</a>','<a href="../docs/案例对照与老师建议分析.md">两个案例的特点及本项目调整</a><a href="../docs/国家级案例写法拆解与申报书改写.md">国家级案例写法与图文改写</a><a href="../docs/国内硬件选型与可行性核对.md">国内候选硬件、淘宝入口与预算核对</a>')
if 'id="hardware-evidence"' not in (ROOT/'scripts/portal.template.html').read_text(encoding='utf-8'):
    edit('scripts/portal.template.html','<h2>文献与制度：','<div id="hardware-evidence"><h2>国内候选硬件与量程核对</h2><p>供应商配图用于选型，未采购、非项目实物。两压力报价与可调连续水源仍需落实。</p><img class="figure" src="../application/figures/hardware_candidates.png" alt="国内候选主控、压力和流量器件配图，非项目样机"><p><a href="https://item.taobao.com/item.htm?id=622908748357">亿佰特官网指向的淘宝入口</a> · <a href="../docs/国内硬件选型与可行性核对.md">全部采购入口及参数依据</a></p><img class="figure" src="../application/figures/hardware_feasibility.png" alt="24组未标定设计计算与候选量程核对"><p class="fine">原480次模型保留原参数；新增24组计算用于候选台架范围核对，均不是实物测试。</p></div><h2>文献与制度：')
print('Application',pages,'pages; scope',scope,'pages; PPT pending labels synchronized.')
