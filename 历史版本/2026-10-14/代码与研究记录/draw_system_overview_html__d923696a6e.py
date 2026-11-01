"""滴智卫 · 横版曲线系统总体结构图 v2 —— HTML 内嵌 SVG（高清、无错位、无额外注释）。

v2 变化：
- 输出 HTML（deliverables/系统总体结构_横版曲线.html），内嵌矢量 SVG，任意缩放不失真
- 修正 v1 文字溢出/线条穿框问题：所有框宽按最长文本重新核算
- 按用户要求：除图注外不加任何注释（去掉脚注与"技术主线"说明文字），只保留
  顶部阶段轴、功能框、连接线与必要的连接标签
- 信号路径按真实电气连接：A支路→变送器→ADS1115→STM32；Q脉冲直入 TIM2
"""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "系统总体结构_横版曲线.html"

W, H = 1480, 780
FONT = "Microsoft YaHei, SimSun, sans-serif"
INK = "#1a1a1a"
GRAY = "#555555"

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text(x, y, t, size=15, bold=False, anchor="middle", fill=INK):
    w = "700" if bold else "400"
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{w}" text-anchor="{anchor}" fill="{fill}">{esc(t)}</text>')

def box(x, y, w, h, lines, dashed=False, fs=15, gap=None):
    dash = ' stroke-dasharray="8 5"' if dashed else ""
    gap = gap or (fs + 9)
    first = y + h / 2 - ((len(lines) - 1) * gap) / 2 + fs * 0.35
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="white" '
         f'stroke="{INK}" stroke-width="2"{dash}/>')
    for i, ln in enumerate(lines):
        s += text(x + w / 2, first + i * gap, ln, fs, bold=(i == 0))
    return s

def curve_arrow(start, end, bend=0, w=2.0, dashed=False):
    sx, sy = start
    ex, ey = end
    mx, my = (sx + ex) / 2, (sy + ey) / 2
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy) or 1
    ux, uy = -dy / length, dx / length
    cx, cy = mx + bend * ux, my + bend * uy
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    return (f'<path d="M {sx} {sy} Q {cx} {cy} {ex} {ey}" fill="none" '
            f'stroke="{INK}" stroke-width="{w}"{dash} marker-end="url(#ar)"/>')

def line_arrow(start, end, w=2.0, dashed=False):
    sx, sy = start
    ex, ey = end
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    return (f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="{INK}" '
            f'stroke-width="{w}"{dash} marker-end="url(#ar)"/>')

S = []
S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append('<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto">'
         f'<path d="M0 0 L8 4 L0 8 Z" fill="{INK}"/></marker></defs>')
S.append(f'<rect width="{W}" height="{H}" fill="white"/>')

# ───────── 顶部阶段轴（对应申报书 3.3 技术主线） ─────────
S.append(box(80, 20, 120, 40, ["测  量"], fs=15))
S.append(box(470, 20, 120, 40, ["判  断"], fs=15))
S.append(box(790, 20, 120, 40, ["传  输"], fs=15))
S.append(box(1140, 20, 170, 40, ["展示与核查"], fs=15))
S.append(line_arrow((200, 40), (470, 40), w=1.8))
S.append(line_arrow((590, 40), (790, 40), w=1.8))
S.append(line_arrow((910, 40), (1140, 40), w=1.8))

# ───────── 左列：双支路清水台架 ─────────
S.append(box(80, 170, 300, 160,
             ["A 支路（被测支管）",
              "供水首部（压力可调 / 扰动注入）→ P₀ 取压",
              "→ 受限段 R → P₁ 取压 → 流量计 Q",
              "→ 正常负载 / 泄漏旁路",
              "→ 独立收集与计量（参考流量）"], fs=14, gap=24))
S.append(box(80, 370, 300, 70,
             ["压力变送器 ×2（P₀ / P₁）", "4–20 mA · 0–200 kPa"], fs=14))
S.append(box(80, 480, 300, 100,
             ["B 支路（扰动模拟）",
              "开关阀：模拟邻支路轮灌切换",
              "末端可调堵塞：模拟下游背压抬升"], fs=14, gap=23))
S.append(box(80, 620, 300, 60,
             ["首部 / 干管参照测点", "（共同扰动参照）"], dashed=True, fs=14))

# ───────── 中列：感知诊断节点 ─────────
S.append(f'<rect x="395" y="100" width="355" height="640" rx="14" fill="none" '
         f'stroke="{INK}" stroke-width="1.6" stroke-dasharray="10 6"/>')
S.append(text(405, 124, "感知诊断节点（现场侧）", 16, bold=True, anchor="start"))

S.append(box(400, 150, 160, 76, ["ADS1115 16 位 ADC", "（I²C 总线）"], fs=14))
S.append(box(590, 150, 150, 76, ["E220 LoRa 模块", "（USART1）"], fs=14))
S.append(box(420, 360, 270, 230,
             ["STM32F103C8T6 主控",
              "1 Hz 采样 → 10 点滑动平均",
              "健康参照 Q_ref / R₀",
              "残差 e_Q / e_R → 双时间窗判决",
              "3 s 待复核 / 10 s 事件确认"], fs=15, gap=27))
S.append(box(420, 650, 125, 70, ["microSD 日志", "（SPI1）"], fs=13))
S.append(box(575, 650, 115, 70, ["LED / 蜂鸣器", "（预留演示）"], dashed=True, fs=13))

# ───────── 中右：LoRa 链路与接收端 ─────────
S.append(text(800, 96, "LoRa 433 MHz（事件 57 B / 遥测 55 B / 应答 24 B）", 14, fill=GRAY))
S.append(box(860, 150, 170, 76, ["E220 接收模块", "USB-TTL（3.3 V）"], fs=14))

# ───────── 右列：PC 服务 / 平台 / 巡检闭环 ─────────
S.append(box(1090, 140, 210, 130,
             ["PC 接收服务",
              "帧校验（CRC）/ 去重",
              "SQLite 事务写入",
              "提交后回复 ACK"], fs=15, gap=24))
S.append(box(1090, 380, 350, 150,
             ["本地巡检平台（八页面）",
              "总览 · 支管监测 · 异常事件 · 设备链路",
              "历史记录 · 实验管理 · 台架管理 · 设置",
              "状态趋势 / 核查复测 / 模拟控制"], fs=15, gap=26))
S.append(box(1090, 600, 350, 130,
             ["巡检闭环（人工流程）",
              "① 接收提示 → ② 下田核查 → ③ 现场处置",
              "④ 同工况复测 → ⑤ 记录归档"], dashed=True, fs=15, gap=26))

# ───────── 连接 ─────────
# A 支路 → 变送器（取压）
S.append(line_arrow((230, 330), (230, 370), w=1.8))
S.append(text(245, 356, "P₀ / P₁ 取压", 13, anchor="start"))
# 变送器 → ADS1115
S.append(curve_arrow((380, 405), (480, 226), bend=35, w=1.8))
S.append(text(430, 300, "4–20 mA", 13))
# A 支路 → STM32（Q 脉冲）
S.append(curve_arrow((380, 250), (420, 430), bend=-25, w=2.4))
S.append(text(432, 345, "Q 脉冲 → TIM2", 13, anchor="start"))
# ADS1115 → STM32
S.append(line_arrow((480, 226), (480, 360), w=1.8))
S.append(text(495, 300, "I²C1", 13, anchor="start"))
# STM32 → E220
S.append(curve_arrow((650, 360), (665, 226), bend=40, w=2.4))
S.append(text(700, 300, "USART1", 13))
# E220 → 接收模块（LoRa 主链路）
S.append(line_arrow((740, 180), (860, 180), w=2.6))
S.append(text(800, 168, "事件 / 遥测帧", 13))
# ACK 回传
S.append(line_arrow((860, 208), (740, 208), w=1.6, dashed=True))
S.append(text(800, 230, "ACK", 13, fill=GRAY))
# 接收模块 → PC
S.append(line_arrow((1030, 180), (1090, 180), w=2.0))
S.append(text(1060, 168, "串口", 13))
# PC → 平台
S.append(line_arrow((1195, 270), (1195, 380), w=2.2))
S.append(text(1212, 330, "读库 / 事件", 13, anchor="start"))
# 平台 ↔ 巡检闭环
S.append(line_arrow((1390, 530), (1390, 600), w=1.8, dashed=True))
S.append(text(1405, 572, "告警", 13, anchor="start"))
S.append(line_arrow((1250, 600), (1250, 530), w=1.8, dashed=True))
S.append(text(1235, 572, "复测归档", 13, anchor="end"))
# B 支路 → A 支路（共同供压扰动）
S.append(curve_arrow((380, 530), (350, 330), bend=45, w=1.8, dashed=True))
S.append(text(400, 462, "共同供压扰动", 13))
# 参照测点 → B 支路
S.append(line_arrow((230, 620), (230, 580), w=1.6, dashed=True))

S.append("</svg>")

svg = "\n".join(S)
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>滴智卫 · 系统总体结构（横版）</title>
<style>
  body{{ margin:0; background:#fff; display:flex; justify-content:center; padding:16px; }}
  svg{{ max-width:100%; height:auto; }}
  @media print {{ body{{ padding:0; }} }}
</style>
</head>
<body>
{svg}
</body>
</html>
"""
OUT.write_text(html, encoding="utf-8")
print(f"written: {OUT} ({OUT.stat().st_size} bytes)")
