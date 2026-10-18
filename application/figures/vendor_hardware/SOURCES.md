# 硬件器件资料库来源清单（SOURCES）

> 本目录 `vendor_hardware/` 为「滴智卫」项目全部关键硬件器件的一手资料库，
> 覆盖 8 个器件：GD32F103CBT6（MCU）、SGM58031（ADC）、MDM490（差压变送器）、
> SEN0549（脉冲流量计）、E220-400T22D（LoRa）、XL4015（5 V Buck）、
> MP2359（3.3 V Buck）、XL6009（24 V Boost）。
>
> 整理日期：2026-10-18。所有文件均于 2026-10-18 当日抓取、核对或复核。
> 逐文件 sha256 见同目录 `provenance.json`。
>
> **纪律**：本目录只放官方一手资料与本项目自绘图/脚本；
> 爬取中间产物（HTML、bin、缩略图、重复 PDF）已于 2026-10-18 全部清除。
> 新增文件必须在本清单与 provenance.json 同步登记。

## 一、来源分级

| 级别 | 含义 | 本库实例 |
|---|---|---|
| A 原厂 | 厂商官网/原厂数据手册/原厂选型资料 | 全部 PDF、官网截图、官网产品图 |
| B 代理/商城 | 授权代理商或电商平台页面（仅作实物图、丝印核对） | 立创商城实物图 |
| C 本项目 | 本项目自绘电路图/脚本/整理稿 | 各 `draw_*.py`、接口电路图、参数 md |

## 二、分器件来源

### 1. GD32F103CBT6（MCU，国产化冻结首选）
| 文件 | 级别 | 来源 |
|---|---|---|
| `GD32F103xx_Datasheet_官方.pdf` | A | GigaDevice 官方《GD32F103xx Datasheet》Rev 3.1（2024-12），112 页；引脚表 Table 2-8（p43—45）、引脚图 Figure 2-6（p16）、电源/复位 Figure 4-1/4-6、功耗 Table 4-10 |
| `GD32F103CBT6_LQFP48_引脚图.png` | A | 数据手册 Figure 2-6 原图 |
| `GD32F103CBT6_典型外围电路_官方推荐.png` | A | 数据手册 Figure 4-1 / 4-6 原图 |
| `GD32F103CBT6_实物_LQFP48_立创商城.jpg` | B | 立创商城商品图（丝印 GD32F103 / CBT6 可辨） |
| `GD32F103CBT6_引脚定义与关键参数.md` | C | 本项目整理；含主频口径（108 MHz）与外设命名对照注 |

### 2. SGM58031（16 位 ADC，P2P 替代 ADS1115）
| 文件 | 级别 | 来源 |
|---|---|---|
| `SGM58031_Datasheet_官方.pdf` | A | 圣邦微电子（SG Micro）官方《SGM58031 Datasheet》MAY 2023, REV. A.3，27 页；PIN DESCRIPTION / PIN CONFIGURATIONS（p3） |
| `SGM58031_引脚图_MSOP10_TDFN.png` | A | 数据手册封装顶视图 |
| `SGM58031_典型应用电路_基础硬件连接.png` | A | 数据手册典型应用图 |
| `SGM58031_实物_MSOP10_立创商城.jpg` | B | 立创商城商品图（丝印 SGM58031 / XMS10） |
| `SGM58031_引脚定义与关键参数.md` | C | 本项目整理 |

### 3. MDM490（差压变送器，0—40 kPa 档）
| 文件 | 级别 | 来源 |
|---|---|---|
| `MDM490_量程档位表_官方.png` | A | 麦克传感器官网选型表截图；**量程口径以此为准：系列 0—40 kPa 起，最小标准档 0—40 kPa（订货号 K040/m400），仅 ±0.5%FS 一档** |
| `MDM490_产品概述与性能指标_官方.png` | A | 官网产品页：原理、特点、性能指标表 |
| `MDM490_外形结构与输出参数_官方.png` | A | 官网：输出形式（电流/电压，两线/三线）与外形尺寸 |
| `MDM490_电气连接定义_官方.png` | A | 官网：四芯插件 B1 四种接法引脚分配 |
| `MDM490_差压变送器实物_麦克官方资料.png` | A | 官方选型资料内嵌实物图（285×293，自 `application/figures/web_ref/` 归位复制，未重复下载） |
| `MDM490_引脚定义与关键参数.md` | C | 本项目整理；双证据：官网截图（本目录）+ 官方选型资料《MDM490 型差压变送器》V6.0 02/2025（`application/figures/web_ref/MDM490_选型资料V6_2025-02_麦克官方.pdf`） |

### 4. SEN0549（脉冲流量计）
| 文件 | 级别 | 来源 |
|---|---|---|
| `SEN0549_流量计实物_DFRobot官网.jpg` | A | DFRobot 官网产品图 |
| `SEN0549_引脚与线色_DFRobot官方.png` | A | 官方线色定义图（绿 OUT / 红 VCC / 黑 GND） |
| `SEN0549_外形尺寸图_DFRobot官方.jpg` | A | 官方尺寸图 |
| `SEN0549_接口电路_5V转3.3V分压.png` | C | 本项目自绘 |
| `SEN0549_引脚定义与关键参数.md` | C | 本项目整理；来源：DFRobot 中文 Wiki <https://wiki.dfrobot.com.cn/SKU_SEN0549_Gravity_Water_Flow_Sensor_G1_4> 与官方商城页 <https://dfrobot.com.cn/goods-3561.html>（2026-10-18 两处核对一致） |
| `draw_sen0549.py` | C | 本项目绘图脚本 |

### 5. E220-400T22D（LoRa 模块）
| 文件 | 级别 | 来源 |
|---|---|---|
| `E220-400T22D_UserManual_CN_亿佰特官方.pdf` | A | 亿佰特官方《E220-xxxTxxx 系列用户使用手册》中文版，40 页，官网页面 ID 1077 下载 |
| `E220-400T22D_实物_亿佰特官网.jpg` | A | 官网产品图 |
| `E220-400T22D_引脚图.png` | C | 按官网引脚表重绘（手册覆盖 T22S 18 脚邮票孔封装，与 400T22D 7 脚直插排布不同，**引脚表严格按产品页整理**） |
| `E220-400T22D_与MCU连接示意.png` | C | 本项目自绘：GD32F103CBT6 UART 连接 |
| `E220-400T22D_引脚定义与关键参数.md` | C | 本项目整理；来源：官网产品页 <https://www.ebyte.com/product/1077.html> + 上述手册 |
| `draw_e220.py` | C | 本项目绘图脚本 |

### 6. XL4015（5 V / 5 A Buck）
| 文件 | 级别 | 来源 |
|---|---|---|
| `XL4015_Datasheet_官方_EN.pdf` / `_CN.pdf` | A | 芯龙半导体（XLSEMI）官方数据手册《5A 180KHz 36V Buck DC to DC Converter》Rev 2.0，取自 xlsemi.com/datasheet/XL4015-EN.pdf |
| `XL4015_引脚图_TO263-5L.png` | A | 手册 Figure 2 引脚排布（顶视） |
| `XL4015_典型应用电路_8-36V转5V5A.png` | A | 手册典型应用图 |
| `XL4015_实物_TO263-5L_立创商城.jpg` | B | 立创商城商品图（丝印 XLSEMI / XL4015E1） |
| `XL4015_引脚定义与关键参数.md` | C | 本项目整理 |

### 7. MP2359（3.3 V Buck）
| 文件 | 级别 | 来源 |
|---|---|---|
| `MP2359_Datasheet_MPS官方Rev1.21.pdf` | A | MPS（Monolithic Power Systems）官方数据手册《MP2359 1.2A, 24V, 1.4MHz Step-Down Converter in a TSOT23-6》Rev. 1.21（7/18/2011），11 页，2026-10-18 下载并逐页核对 |
| `MP2359_实物_TSOT23-6_立创商城.jpg` | B | 立创商城 MP2359DJ-LF-Z（编号 C14259）商品实物照，TSOT-23-6，丝印 F8HA（F8 = MP2359DJ 官方顶标）；抓取时显示现货 0，采购前复核库存 |
| `MP2359_实物尺寸_格尺参照_立创商城.jpg` | B | 同商品格尺参照照（同一芯片，供封装尺寸目视核对） |
| `MP2359_引脚图_重绘.png` | C | 按官方引脚定义重绘（1 BST / 2 GND / 3 FB / 4 EN / 5 IN / 6 SW） |
| `MP2359_典型应用电路_5V转3.3V_重绘.png` | C | 依据官方 Typical Application 改写为 5 V 输入 |
| `MP2359_引脚定义与关键参数.md` | C | 本项目整理；参数已与 EC 表逐项核对；**含 NRND 风险注**（MPS 官网标注"新设计不推荐"，备选替代 MP2331HGTL-Z） |
| `draw_mp2359.py` | C | 本项目绘图脚本 |

### 8. XL6009（24 V Boost，高边开关供电）
| 文件 | 级别 | 来源 |
|---|---|---|
| `XL6009_Datasheet_Rev1.1.pdf` | A | 芯龙半导体官方数据手册《XL6009 400KHz 60V 4A Switching Current Boost / Buck-Boost / Inverting DC/DC Converter》Rev 1.1（www.xlsemi.com），8 页；官网 datasheet 目录已 404，取自原厂排版 PDF 镜像（页脚仍为 www.xlsemi.com），内容未删改 |
| `XL6009_封装外形图_官方Figure1.png` | A | 数据手册 Figure 1 封装外形（TO263-5L），本目录 PDF 第 1 页 300 dpi 裁剪 |
| `XL6009_引脚图_TO263-5L.png` | A | 手册 Figure 2 引脚排布（顶视） |
| `XL6009_典型应用电路_升压.png` | A | 手册 Figure 4：Boost，输入 12—16 V |
| `XL6009_引脚定义与关键参数.md` | C | 本项目整理；含「升级 XL6019E1」为代理商说法（非原厂公告）的来源层级注；**含实物照缺口记录**（原厂产品页 404、立创未收录、JLCPCB 仅占位图，暂以官方封装外形图代替，到货后补拍） |

## 三、已知口径提醒（申报书引用时）

1. **MDM490 量程**：原厂最小标准档为 0—40 kPa（K040/m400），±0.5%FS；渠道资料「35 kPa」系误植，已全库修正。
2. **GD32F103 主频**：官方标称最高 108 MHz；「72 MHz」系 STM32F103 误记，已全库修正。
3. **E220-400T22D 引脚**：系列手册为 T22S 18 脚邮票孔封装，本项目 D 版为 7 脚直插，**引脚定义以官网产品页为准**。
4. **MP2359 NRND**：原厂标注新设计不推荐，申报书如提及需注明来源层级与替代方案；另注意立创现货为 0（需订货）。
5. **GD32 外设命名**：官方手册 USART0/SPI0/TIMER3_CH0 = 本项目 USART1/SPI1/TIM4_CH1，详见 GD32 md 内对照表。
6. **XL6009 实物照缺口**：官方渠道无可下载实物照片，暂以数据手册封装外形图（Figure 1）代替；与 XL4015 同为 TO263-5L 封装可参照。采购到货后补拍登记。
