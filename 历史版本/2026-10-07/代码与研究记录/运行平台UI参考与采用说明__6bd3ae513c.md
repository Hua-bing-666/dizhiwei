# 运行平台 UI 参考与采用说明

2026年10月7日查看以下 GitHub 官方仓库。星数是当时页面显示的约数，会变化；选型以用途与已有本地程序兼容性为准。

| 仓库 | 当时显示星数 | 采用的思路 | 本轮采用方式 |
| --- | ---: | --- | --- |
| [Tabler](https://github.com/tabler/tabler) | 41.8k | 导航分组、摘要与表格的层级、统一间距 | 自行编写HTML/CSS，不引入整套Bootstrap或第三方图表插件 |
| [ThingsBoard](https://github.com/thingsboard/thingsboard) | 22.5k | 设备、遥测、事件与历史各自负责一类工作 | 借鉴信息结构，保持现有本机Python服务 |
| [Lucide](https://github.com/lucide-icons/lucide) | 24.9k | 一致的线性图标、24像素图标坐标 | 原生SVG重新绘制，不下载图标包 |
| [model-viewer](https://github.com/google/model-viewer) | 8.3k | 模型检查、相机预设、说明与操作配合 | 保留原有离线Three.js与实际CAD网格，自行实现检查交互 |

使用本机 ui-ux-pro-max 的整体设计及减少动态效果查询。整体查询匹配了运行看板，但推荐的玻璃透明效果和营销页面行动按钮不适用于本项目，未照搬；采用其中的来源真实性、可访问性、字重和信息层级建议。具体设计规则记录在 design-system/drip-research-console/pages/operations-v1.2.md。

参考仓库未作为可执行安装脚本运行，没有新增联网CDN依赖。原有Three.js及其许可证继续随三维网页保留。没有把参考系统的多租户、云服务或真实设备能力写成项目已经实现的内容。
