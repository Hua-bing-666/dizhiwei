# 离线研究工作台界面重设计与来源记录

2026年10月4日。本轮将网页与三维查看器统一为研究工作台，保留所有模型结果及证据身份。

## 检索及技能使用

根据用户要求，使用技能安装器从nextlevelbuilder/ui-ux-pro-max-skill的.claude/skills/ui-ux-pro-max路径安装UI UX Pro Max，安装于C:/Users/Lenovo/.codex/skills/ui-ux-pro-max。已读取本地SKILL.md及界面复核规则，并运行设计系统检索和Three.js响应式指导检索。安装将在后续对话可用；本轮直接按已读取的技能执行。

GitHub API在本轮查询时返回该仓库132790星，shadcn-ui/ui为125057星，tabler/tabler为41810星；均为查询时快照，非质量保证。仓库均标注MIT。主来源为[技能仓库](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)、[shadcn/ui](https://github.com/shadcn-ui/ui)、[Tabler](https://github.com/tabler/tabler)。不下载图片冒充实物，不直接复制他人整页界面。

最初广义农业仪表盘查询的展示网站模式不适配，改用internal analytics dashboard查询。第二次命中的Minimalism & Swiss Style及可访问性规则适配；Enterprise Gateway营销模式仍不适用，明确弃用。实际设计决策保存在design-system/drip-research-console/pages/research-workspace.md，不将无关匹配自动执行到项目。

## 具体改动

统一深色窄侧栏、白色内容区、清晰标题与绿色主要动作，重新安排顶部章节、状态、文件入口和三维入口。首页把已有模型结果、计划实验与当前资源分别呈现，降低重复说明的密度。移除大块渐变展示和固定图片高度造成的留白。

诊断页面提供P0/P1/Q读数、质量、有限模式、核查查看及按需展开的维护表单。输入备注和人工复测依据后才允许记录相应阶段；离线不能归档为恢复。本地保存与导出是可操作的演示功能，不是SQLite接收端或真实维修记录。三维查看器统一控件与注释，增加返回入口、按钮旋转缩放和键盘操作。

所有页面本地打开，未加载在线字体、远程图标或CDN。图标由本项目绘制；三维库沿用已核验的Three.js及MIT归属，模型由本项目参数化几何生成。申报书局部截图来自真实运行的页面，仅通过出版视图隐藏非必要表单。

## 检查范围

scripts/verify_research_ui.mjs在独立Edge会话中检查375、768、1024、1440四种宽度，每种宽度8章导航，共32项导航和页面溢出检查。另检查维护前置条件、刷新后的本地保存、实际导出JSON、离线归档拒绝、无效状态、三维四种宽度及按钮键盘操作；记录真实浏览器异常与外部网络请求。

程序检查后查看实际首页、诊断页、三维查看器和出版截图，修复首页图片比例及临时截图页面切换问题。软件检查不代表实物系统、无线距离、射频功耗或田间性能已经验证。记录见deliverables/界面验收记录.json。
