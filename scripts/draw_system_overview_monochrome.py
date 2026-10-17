"""滴智卫 · 系统总体结构单色学术图（原生 SVG，黑白，可直接插入 Word）。

风格遵循仓库既有约定（scripts/draw_event_system_diagrams.py）：
- 纯黑白：#1a1a1a 描边、白色填充、无底色
- 实线 = 数据/业务流；虚线 = 人工流程、参照测点或预留接口
- 字体 Microsoft YaHei / SimSun；canvas 宽 1240
输出：deliverables/系统总体结构_单色学术版.svg
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "系统总体结构_单色学术版.svg"

W, H = 1390, 1470
FONT = "Microsoft YaHei, SimSun, sans-serif"
INK = "#1a1a1a"
GRAY = "#555555"

def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def badge(cx, cy, num):
    """主流程步骤编号：白底黑圈数字。"""
    return (f'<circle cx="{cx}" cy="{cy}" r="13" fill="white" stroke="{INK}" '
            f'stroke-width="2"/>' +
            text(cx, cy + 5, num, 14, bold=True))

def text(x, y, t, size=18, bold=False, anchor="middle", fill=INK):
    w = "700" if bold else "400"
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{w}" text-anchor="{anchor}" fill="{fill}">{esc(t)}</text>')

def box(x, y, w, h, lines, dashed=False, fs=18, title_bold=True, gap=None):
    dash = ' stroke-dasharray="8 5"' if dashed else ""
    gap = gap or (fs + 10)
    first = y + h / 2 - ((len(lines) - 1) * gap) / 2 + fs * 0.36
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="white" '
         f'stroke="{INK}" stroke-width="2"{dash}/>')
    for i, ln in enumerate(lines):
        s += text(x + w / 2, first + i * gap, ln, fs, bold=(i == 0 and title_bold))
    return s

def arrow(points, dashed=False, w=1.8):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    d = "M " + " L ".join(f"{px} {py}" for px, py in points)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}"{dash} '
            f'marker-end="url(#ar)"/>')

def plain_line(points, dashed=False, w=1.6):
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    d = "M " + " L ".join(f"{px} {py}" for px, py in points)
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}"{dash}/>'

def container(x, y, w, h, label):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="white" '
         f'stroke="{INK}" stroke-width="1.6" stroke-dasharray="10 6"/>')
    s += text(x + 12, y + 26, label, 19, bold=True, anchor="start")
    return s

def waves(cx, cy, direction):
    """三道电波弧线；direction=+1 向下张开, -1 向上张开。"""
    s = ""
    for i, r in enumerate((10, 20, 30)):
        dy = r * 0.62 * direction
        s += (f'<path d="M {cx-r} {cy} Q {cx} {cy+dy} {cx+r} {cy}" fill="none" '
              f'stroke="{INK}" stroke-width="1.6"/>')
    return s

S = []
S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}">')
S.append('<defs>'
         '<marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
         f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker>'
         '</defs>')
S.append(f'<rect width="{W}" height="{H}" fill="white"/>')

# ───────────────────────── 左侧主流程阶段轴（测量→判断→传输→展示与核查） ─────────────────────────
stages = [
    (263, "测  量"),      # 台架 + 传感：y 46..525
    (625, "判  断"),      # 感知诊断节点：y 455..840
    (905, "传  输"),      # LoRa + 接收端：y 850..1005
    (1154, "展示与核查"),  # PC + 平台 + 人工闭环：y 1010..1342
]
for i, (y, name) in enumerate(stages):
    S.append(box(30, y, 110, 44, [name], fs=17))
for (y0, y1) in ((307, 625), (669, 905), (949, 1154)):
    S.append(arrow([(85, y0), (85, y1)], w=2.2))
S.append(text(85, 240, "技术主线", 15, fill=GRAY))
S.append(text(85, 1380, "（申报书 3.3）", 14, fill=GRAY))

# ───────────────────────── 正文（右移 150） ─────────────────────────
S.append('<g transform="translate(150,0)">')

# ───────────────────────── 图例（右上） ─────────────────────────
S.append(box(940, 60, 270, 118, [], dashed=True, fs=16))
S.append(text(1075, 88, "图  例", 17, bold=True))
S.append(plain_line([(960, 112), (1030, 112)]))
S.append(text(1042, 117, "数据 / 业务流", 15, anchor="start"))
S.append(plain_line([(960, 142), (1030, 112 + 30)], dashed=True))
S.append(text(1042, 147, "人工 / 参照 / 预留", 15, anchor="start"))

# ───────────────────────── ① 双支路清水台架 ─────────────────────────
S.append(container(20, 46, 850, 394, "双支路清水台架（实验室验证平台）"))

# A 支路主链
S.append(text(40, 96, "A 支路（被测支管）", 16, anchor="start", fill=GRAY))
S.append(box(40, 106, 105, 62, ["供水首部", "（压力可调）"], fs=16))
S.append(box(165, 106, 62, 62, ["P₀", "取压"], fs=17))
S.append(box(247, 106, 88, 62, ["受限段 R", "（可调节流）"], fs=16))
S.append(box(355, 106, 62, 62, ["P₁", "取压"], fs=17))
S.append(box(433, 106, 86, 62, ["流量计 Q", "（SEN0549）"], fs=16))
S.append(box(543, 72, 108, 56, ["正常负载", "（滴头模拟）"], fs=16))
S.append(box(543, 144, 108, 56, ["泄漏旁路", "（可调阀门）"], fs=16))
S.append(box(669, 92, 180, 88, ["独立收集与计量", "（参考流量）"], fs=16))
for a, b in ((145, 165), (227, 247), (335, 355), (417, 433)):
    S.append(arrow([(a, 137), (b, 137)]))
S.append(arrow([(519, 137), (531, 137), (531, 100), (543, 100)]))
S.append(arrow([(519, 137), (531, 137), (531, 172), (543, 172)]))
S.append(arrow([(651, 100), (662, 100), (662, 120), (669, 120)]))
S.append(arrow([(651, 172), (662, 172), (662, 152), (669, 152)]))

# 压力变送器（台架现场仪表）
S.append(box(130, 196, 160, 64, ["压力变送器 ×2", "4–20 mA·0–200 kPa"], fs=15))
S.append(arrow([(196, 168), (196, 196)], dashed=True, w=1.4))
S.append(arrow([(386, 168), (386, 181), (240, 181), (240, 196)], dashed=True, w=1.4))

# B 支路（扰动模拟）
S.append(text(520, 282, "B 支路：模拟邻支路轮灌扰动", 16, anchor="start", fill=GRAY))
S.append(box(520, 290, 70, 58, ["B 支路", "供水"], fs=15))
S.append(box(604, 290, 130, 58, ["开关阀", "（模拟轮灌切换）"], fs=15))
S.append(box(748, 290, 101, 58, ["末端可调堵塞", "（背压抬升）"], fs=14))
for a, b in ((590, 604), (734, 748)):
    S.append(arrow([(a, 319), (b, 319)]))

# 扰动特征库设施（虚线）
S.append(box(40, 290, 140, 58, ["上游扰动注入", "（可调扰动阀）"], dashed=True, fs=14))
S.append(box(250, 290, 210, 58, ["首部 / 干管参照测点", "（共同扰动参照）"], dashed=True, fs=14))

# Q 脉冲长线（流量计 → 主控 TIM2）
S.append(plain_line([(476, 168), (476, 556)]))
S.append(text(484, 530, "脉冲输出 → TIM2", 15, anchor="start", fill=GRAY))

# ───────────────────────── ② 感知诊断节点 ─────────────────────────
S.append(container(20, 455, 850, 385, "感知诊断节点（现场侧）"))

S.append(box(150, 490, 190, 64, ["ADS1115 16 位 ADC", "（I²C 总线）"], fs=16))
S.append(arrow([(210, 260), (210, 490)], w=2.6))
S.append(badge(210, 368, "1"))
S.append(text(228, 373, "采集", 15, anchor="start", bold=True))
S.append(text(220, 412, "两路 4–20 mA", 15, anchor="start", fill=GRAY))

S.append(box(300, 580, 380, 150,
             ["STM32F103C8T6 主控",
              "采集 · 本地诊断 · 日志缓存（1 Hz 采样）",
              "10 点滑动平均 → 健康参照 Q_ref / R₀",
              "残差 e_Q / e_R → 双时间窗判决",
              "3s×2 待复核提示 / 10s×5 事件确认"],
             fs=16, gap=29))
S.append(arrow([(245, 554), (245, 600), (300, 600)], w=2.6))
S.append(text(262, 592, "I²C1", 14, anchor="start", fill=GRAY))
S.append(arrow([(476, 556), (476, 580)], w=1.5))

S.append(box(300, 772, 170, 56, ["microSD 日志", "（SPI1）"], fs=16))
S.append(arrow([(385, 730), (385, 772)]))
S.append(box(510, 772, 190, 56, ["LED / 蜂鸣器", "（演示接口，预留）"], dashed=True, fs=15))
S.append(arrow([(605, 730), (605, 772)], dashed=True))

S.append(box(740, 590, 110, 90, ["E220", "LoRa 模块", "（USART1）"], fs=15))
S.append(arrow([(680, 620), (740, 620)], w=2.6))
S.append(badge(710, 620, "2"))
S.append(text(710, 578, "本地诊断", 15, bold=True))

# ───────────────────────── ③ LoRa 无线链路 ─────────────────────────
S.append(arrow([(760, 680), (760, 900)], w=2.6))
S.append(arrow([(830, 900), (830, 680)], dashed=True))
S.append(badge(760, 795, "3"))
S.append(text(742, 792, "事件上报", 15, anchor="end", bold=True))
S.append(waves(795, 745, 1))
S.append(waves(795, 835, -1))
S.append(text(848, 728, "LoRa 433 MHz 无线链路", 15, anchor="start"))
S.append(text(848, 750, "事件帧 57 B / 遥测帧 55 B / 应答帧 24 B", 14, anchor="start", fill=GRAY))
S.append(text(848, 772, "未确认 → 有界重传", 14, anchor="start", fill=GRAY))
S.append(text(742, 830, "事件上行", 13, anchor="end", fill=GRAY))
S.append(text(842, 830, "ACK", 13, fill=GRAY))

# ───────────────────────── ④ 接收端与 PC 侧 ─────────────────────────
S.append(box(700, 900, 190, 70, ["E220 接收模块", "USB-TTL（3.3 V）串口桥接"], fs=15))
S.append(box(300, 1030, 380, 112,
             ["PC 接收服务",
              "帧校验（CRC）/ 去重",
              "SQLite 事务写入",
              "提交后回复 ACK"],
             fs=16, gap=26))
S.append(arrow([(795, 970), (795, 1000), (490, 1000), (490, 1030)], w=2.4))
S.append(badge(640, 1000, "4"))
S.append(text(640, 988, "校验入库", 15, bold=True))
S.append(text(700, 1024, "串口", 14, fill=GRAY))
S.append(arrow([(680, 1086), (705, 1086), (705, 935), (700, 935)], dashed=True))
S.append(text(712, 1020, "ACK 下行", 13, anchor="start", fill=GRAY))

S.append(box(240, 1190, 560, 152,
             ["本地巡检平台（八页面）",
              "总览 · 支管监测 · 异常事件 · 设备链路",
              "历史记录 · 实验管理 · 台架管理 · 设置",
              "状态与趋势呈现 ｜ 人工核查与复测记录 ｜ 模拟控制请求"],
             fs=16, gap=31))
S.append(arrow([(490, 1142), (490, 1190)], w=2.6))
S.append(badge(490, 1166, "5"))
S.append(text(512, 1172, "事件 / 读库", 14, anchor="start", fill=GRAY))

# ───────────────────────── ⑤ 巡检闭环（人工） ─────────────────────────
S.append(container(900, 980, 320, 362, "巡检闭环（人工流程）"))
steps = [
    (1016, ["① 接收提示", "支管编号-测点区段-建议检查部位"]),
    (1082, ["② 下田核查", "接头 / 管段 / 下游配水单元"]),
    (1148, ["③ 现场处置", "关阀 / 更换 / 紧固"]),
    (1214, ["④ 同工况复测", "确认处理效果"]),
    (1280, ["⑤ 记录归档", "复测结果回写平台"]),
]
for y, lines in steps:
    S.append(box(920, y, 280, 52, lines, dashed=True, fs=14))
for i in range(len(steps) - 1):
    y0 = steps[i][0] + 52
    y1 = steps[i + 1][0]
    S.append(arrow([(1060, y0), (1060, y1)], dashed=True))
# 平台 → ① 接收提示
S.append(arrow([(800, 1245), (880, 1245), (880, 1042), (920, 1042)], dashed=True, w=2.2))
S.append(badge(880, 1120, "6"))
S.append(text(868, 1104, "核查处置", 14, anchor="end", bold=True))
# ⑤ → 平台（回写）
S.append(arrow([(920, 1306), (868, 1306), (868, 1238), (800, 1238)], dashed=True, w=2.2))
S.append(badge(868, 1272, "7"))
S.append(text(856, 1290, "复测归档", 14, anchor="end", bold=True))

S.append("</g>")

# ───────────────────────── 脚注 ─────────────────────────
S.append(text(20, 1400,
              "主流程：1 采集（P₀/P₁/Q）→ 2 本地诊断 → 3 事件上报（LoRa）→ 4 接收校验入库 → 5 平台呈现 → 6 人工核查处置 → 7 复测归档（回写平台）。",
              14, anchor="start", fill=GRAY))
S.append(text(20, 1424,
              "注：实线为数据 / 业务流，虚线为人工流程、参照测点或预留接口；P₀/P₁ 为监测区段上下游压力，Q 为分流前总流量。",
              14, anchor="start", fill=GRAY))
S.append(text(20, 1448,
              "A 支路为被测支管，B 支路模拟邻支路轮灌扰动；台架侧操作标签与参考计量独立于诊断结果记录，用于独立实验评价。",
              14, anchor="start", fill=GRAY))

S.append("</svg>")
OUT.write_text("\n".join(S), encoding="utf-8")
print(f"written: {OUT} ({OUT.stat().st_size} bytes)")
