"""滴智卫 · 横版曲线系统总体结构图（黑白学术风，适合 Word 插入）。

参考用户偏好：减少竖版、使用圆角矩形框 + 曲线箭头、横向为主。
"""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "系统总体结构_横版曲线_单色学术版.svg"

W, H = 1500, 880
FONT = "Microsoft YaHei, SimSun, sans-serif"
INK = "#1a1a1a"
GRAY = "#555555"

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text(x, y, t, size=18, bold=False, anchor="middle", fill=INK):
    w = "700" if bold else "400"
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{w}" text-anchor="{anchor}" fill="{fill}">{esc(t)}</text>')

def box(x, y, w, h, lines, dashed=False, fs=17, gap=None):
    dash = ' stroke-dasharray="8 5"' if dashed else ""
    gap = gap or (fs + 10)
    first = y + h / 2 - ((len(lines) - 1) * gap) / 2 + fs * 0.35
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="white" '
         f'stroke="{INK}" stroke-width="2"{dash}/>')
    for i, ln in enumerate(lines):
        s += text(x + w / 2, first + i * gap, ln, fs, bold=(i == 0))
    return s

def curve_arrow(start, end, bend=0, label="", dashed=False, w=2.0):
    sx, sy = start
    ex, ey = end
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy) or 1
    ux, uy = -dy / length, dx / length
    cx, cy = mx + bend * ux, my + bend * uy
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    path = f"M {sx} {sy} Q {cx} {cy} {ex} {ey}"
    s = (f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="{w}"{dash} '
         f'marker-end="url(#ar)"/>')
    # label at t=0.5 of quadratic bezier
    if label:
        lx = 0.25 * sx + 0.5 * cx + 0.25 * ex
        ly = 0.25 * sy + 0.5 * cy + 0.25 * ey
        # offset perpendicular so text doesn't sit exactly on line
        off = 10 if bend >= 0 else -10
        lxo = lx + off * ux
        lyo = ly + off * uy
        s += text(lxo, lyo + 5, label, 15, bold=True)
    return s

def straight_arrow(start, end, label="", dashed=False, w=2.0):
    sx, sy = start
    ex, ey = end
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    s = (f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" fill="none" stroke="{INK}" '
         f'stroke-width="{w}"{dash} marker-end="url(#ar)"/>')
    if label:
        lx, ly = (sx + ex) / 2, (sy + ey) / 2
        s += text(lx, ly - 8, label, 15, bold=True)
    return s

S = []
S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append('<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
         f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker></defs>')
S.append(f'<rect width="{W}" height="{H}" fill="white"/>')

# ───────────────── 顶部技术主线轴（横向） ─────────────────
S.append(text(40, 38, "技术主线", 18, bold=True))
axis = ["测 量", "判 断", "传 输", "展示与核查"]
ax_x = 160
for i, nm in enumerate(axis):
    x = ax_x + i * 180
    S.append(box(x, 16, 110, 36, [nm], fs=15))
    if i < len(axis) - 1:
        S.append(straight_arrow((x + 110, 34), (x + 180, 34), w=1.8))

# ───────────────── 1. 双支路清水台架（左侧） ─────────────────
# A 支路
S.append(box(60, 170, 260, 150,
             ["A 支路（被测支管）",
              "供水首部 → P₀ 取压 → 受限段 R →",
              "P₁ 取压 → 流量计 Q → 正常负载 / 泄漏旁路",
              "独立收集与计量（参考流量）"], fs=14, gap=24))
# B 支路
S.append(box(60, 360, 260, 110,
             ["B 支路（扰动模拟）",
              "开关阀：模拟邻支路轮灌切换",
              "末端可调堵塞：模拟下游背压抬升"], fs=14, gap=23))
# 传感器
S.append(box(60, 520, 260, 70,
             ["压力变送器 ×2  (P₀ / P₁)", "4–20 mA → ADS1115  (I²C)"], fs=14))
# 扰动特征库（虚线）
S.append(box(60, 640, 260, 70,
             ["扰动特征库", "上游瞬态扰动 / 首部·干管参照"], dashed=True, fs=14))

# ───────────────── 2. 感知诊断节点（中左，核心） ─────────────────
# ADS1115
S.append(box(420, 120, 240, 80,
             ["ADS1115 16 位 ADC", "（I²C 总线）"], fs=15))
# STM32 主控（核心）
S.append(box(420, 340, 260, 220,
             ["STM32F103C8T6 主控",
              "1 Hz 采样 → 10 点滑动平均",
              "健康参照 Q_ref / R₀",
              "残差 e_Q / e_R → 双时间窗判决",
              "3 s 待复核提示 / 10 s 事件确认"], fs=15, gap=28))
# microSD
S.append(box(420, 620, 110, 70,
             ["microSD 日志", "（SPI1）"], fs=14))
# LED/蜂鸣器
S.append(box(570, 620, 110, 70,
             ["LED / 蜂鸣器", "（预留演示）"], dashed=True, fs=14))
# E220 LoRa 模块
S.append(box(570, 120, 110, 80,
             ["E220", "LoRa 模块", "（USART1）"], fs=14))

# 节点虚线容器
S.append(f'<rect x="380" y="90" width="330" height="620" rx="14" fill="none" '
         f'stroke="{INK}" stroke-width="1.6" stroke-dasharray="10 6"/>')
S.append(text(395, 118, "感知诊断节点（现场侧）", 17, bold=True))

# ───────────────── 3. 通信（中右） ─────────────────
# E220 接收模块
S.append(box(840, 120, 150, 80,
             ["E220 接收模块", "USB-TTL  (3.3 V)"], fs=14))
# LoRa 链路标注框（装饰性，无实线）
S.append(text(775, 100, "LoRa 433 MHz 无线链路", 16, bold=True))
S.append(text(775, 125, "事件 57 B / 遥测 55 B / 应答 24 B · 未确认有界重传", 14, fill=GRAY))

# ───────────────── 4. PC 接收服务（右侧） ─────────────────
S.append(box(1080, 120, 200, 120,
             ["PC 接收服务",
              "帧校验（CRC）/ 去重",
              "SQLite 事务写入",
              "提交后回复 ACK"], fs=15, gap=24))

# ───────────────── 5. 本地巡检平台 + 人工闭环（最右） ─────────────────
S.append(box(1080, 360, 340, 140,
             ["本地巡检平台（八页面）",
              "总览 · 支管监测 · 异常事件 · 设备链路",
              "历史记录 · 实验管理 · 台架管理 · 设置",
              "状态趋势 / 核查复测记录 / 模拟控制请求"], fs=15, gap=26))
S.append(box(1080, 570, 340, 140,
             ["巡检闭环（人工流程）",
              "① 接收提示 → ② 下田核查 → ③ 现场处置",
              "④ 同工况复测 → ⑤ 记录归档（回写平台）"], dashed=True, fs=15, gap=26))

# ───────────────── 曲线连接 ─────────────────
# 1 采集：A 支路 → STM32
S.append(curve_arrow((320, 245), (420, 420), bend=-50, label="采集 P₀ / P₁ / Q", w=2.6))
# B 支路 → A 支路：扰动耦合（虚线）
S.append(curve_arrow((320, 415), (200, 320), bend=35, label="共同供压扰动", dashed=True, w=1.8))
# 扰动特征库 → A 支路（虚线）
S.append(curve_arrow((320, 675), (200, 320), bend=-55, label="扰动 / 参照测点", dashed=True, w=1.8))
# 压力变送器 → ADS1115（细实线）
S.append(curve_arrow((320, 555), (540, 200), bend=40, label="4–20 mA", w=1.5))
# ADS1115 → STM32
S.append(straight_arrow((540, 200), (540, 340), label="I²C1", w=1.8))
# STM32 → microSD
S.append(straight_arrow((490, 560), (475, 620), label="SPI1", w=1.6))
# STM32 → E220
S.append(curve_arrow((680, 400), (570, 200), bend=50, label="USART1 事件上报", w=2.6))
# E220 → 接收模块（LoRa 主链路）
S.append(curve_arrow((680, 160), (840, 160), bend=0, label="事件帧 / 遥测帧", w=2.6))
# ACK：接收模块 → E220（虚线）
S.append(curve_arrow((840, 200), (680, 200), bend=0, label="ACK 24 B", dashed=True, w=1.8))
# 接收模块 → PC 服务
S.append(straight_arrow((990, 160), (1080, 180), label="串口", w=2.0))
# PC 服务 → 平台
S.append(straight_arrow((1180, 240), (1180, 360), label="读库 / 事件", w=2.2))
# 平台 → 巡检闭环
S.append(straight_arrow((1340, 500), (1340, 570), label="告警", dashed=True, w=1.8))
# 巡检闭环 → 平台（归档回写）
S.append(straight_arrow((1260, 570), (1260, 500), label="复测归档", dashed=True, w=1.8))
# PC 服务 ACK 回传示意（返回接收模块，虚线）
S.append(curve_arrow((1080, 240), (990, 220), bend=-30, label="ACK 下行", dashed=True, w=1.5))

# ───────────────── 脚注 ─────────────────
S.append(text(40, 820,
              "注：实线为数据 / 业务流；虚线为共同扰动、参照测点、人工流程、预留接口或反馈。P₀ / P₁ 为监测区段上下游压力，Q 为分流前总流量。",
              14, anchor="start", fill=GRAY))
S.append(text(40, 848,
              "A 支路为被测支管，B 支路模拟邻支路轮灌扰动；台架侧操作标签与参考计量独立于诊断结果记录，用于独立实验评价。",
              14, anchor="start", fill=GRAY))

S.append("</svg>")
OUT.write_text("\n".join(S), encoding="utf-8")
print(f"written: {OUT} ({OUT.stat().st_size} bytes)")
