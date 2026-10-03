"""Print-readable monochrome design diagrams. No physical or CFD validation.

Every PNG is rendered from its editable SVG using a fresh browser profile.
The old PNG is removed and a newly produced file is awaited before returning.
"""
from pathlib import Path
from html import escape
import json
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'application/figures'
TMP = ROOT / 'tmp/application_diagrams'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
records = []


class Drawing:
    def __init__(self, name, height):
        self.name, self.width, self.height = name, 1000, height
        self.items, self.texts = [], []

    def text(self, x, y, value, size=23, bold=False, anchor='middle'):
        self.items.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(value)}</text>')
        self.texts.append({'text': value, 'size_px': size})

    def box(self, x, y, w, h, title, lines=(), dashed=False, fill='white', stroke='black'):
        dash = ' stroke-dasharray="7 5"' if dashed else ''
        self.items.append(f'<g data-kind="box" data-x="{x}" data-y="{y}" data-w="{w}" data-h="{h}">')
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"{dash}/>')
        n = len(lines)
        assert h >= 24 + 30*(n+1), (self.name, title, h, n)
        start = y + (h - (n * 30 + 27)) / 2 + 22
        self.text(x + w/2, start, title, 25, True)
        for i, line in enumerate(lines):
            self.text(x + w/2, start + 31 + i*30, line)
        self.items.append('</g>')

    def diamond(self, cx, cy, w, h, lines):
        self.items.append(f'<path d="M {cx} {cy-h/2} L {cx+w/2} {cy} L {cx} {cy+h/2} L {cx-w/2} {cy} Z" fill="white" stroke="black" stroke-width="2"/>')
        for i, line in enumerate(lines):
            self.text(cx, cy + 8 + (i-(len(lines)-1)/2)*29, line)

    def path(self, points, arrow=True, dashed=False, color='black'):
        d = 'M ' + ' L '.join(f'{x} {y}' for x, y in points)
        self.items.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"'+ (' stroke-dasharray="7 5"' if dashed else '') + (' marker-end="url(#arrow)"' if arrow else '') + '/>')

    def label(self, x, y, value):
        width = sum(12 if c.isascii() else 23 for c in value) + 10
        self.items.append(f'<rect x="{x-width/2}" y="{y-22}" width="{width}" height="28" fill="white"/>')
        self.text(x, y, value)

    def sensor(self, x, y, label):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="26" fill="white" stroke="black" stroke-width="2"/>')
        self.text(x, y+8, label, 24, True)

    def footer(self, lines):
        for i, line in enumerate(lines):
            self.text(24, self.height - 20 - (len(lines)-1-i)*31, line, anchor='start')

    def render(self):
        assert all(t['size_px'] >= 23 for t in self.texts)
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{self.height}" viewBox="0 0 1000 {self.height}"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M 0 0 L 8 4 L 0 8 Z" fill="black"/></marker></defs><rect width="1000" height="{self.height}" fill="white"/><g font-family="Microsoft YaHei, SimSun, sans-serif" fill="black">' + ''.join(self.items) + '</g></svg>'
        (OUT / (self.name+'.svg')).write_text(svg+'\n', encoding='utf-8', newline='\n')
        html = TMP / (self.name+'.html')
        check = """<script>const errors=[];for(const g of document.querySelectorAll('[data-kind=box]')){const x=+g.dataset.x,y=+g.dataset.y,w=+g.dataset.w,h=+g.dataset.h;for(const t of g.querySelectorAll('text')){const b=t.getBBox();if(b.x<x+3||b.y<y+3||b.x+b.width>x+w-3||b.y+b.height>y+h-3)errors.push(t.textContent)}}const receipt=document.createElement('p');receipt.style.cssText='font:20px Arial;color:black';receipt.textContent=errors.length?'DIAGRAM_LAYOUT_FAIL '+errors.join(' / '):'DIAGRAM_LAYOUT_PASS';document.body.append(receipt);</script>"""
        html.write_text(f'<html><meta charset="utf-8"><style>html,body{{margin:0;width:1000px}}svg{{display:block}}@page{{size:1000px {self.height+60}px;margin:0}}</style>'+svg+check+'</html>', encoding='utf-8')
        dest = OUT / (self.name+'.png')
        dest.unlink(missing_ok=True)
        profile = TMP / ('edge-'+uuid.uuid4().hex[:12])
        proof = TMP / (self.name+'-layout.pdf')
        proof.unlink(missing_ok=True)
        subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars', '--no-pdf-header-footer', '--force-device-scale-factor=2', '--user-data-dir='+str(profile), f'--window-size=1000,{self.height}', '--screenshot='+str(dest), '--print-to-pdf='+str(proof), html.as_uri()], capture_output=True, check=True, timeout=35, creationflags=subprocess.CREATE_NO_WINDOW)
        deadline = time.monotonic()+25
        while not dest.exists() or dest.stat().st_size < 1000 or not proof.exists() or proof.stat().st_size < 1000:
            if time.monotonic()>deadline:
                raise RuntimeError('Fresh diagram not produced: '+str(dest))
            time.sleep(.2)
        import pymupdf
        receipt = ''.join(p.get_text() for p in pymupdf.open(proof))
        assert 'DIAGRAM_LAYOUT_PASS' in receipt and 'DIAGRAM_LAYOUT_FAIL' not in receipt, receipt[-1200:]
        records.append({'name': self.name, 'width': 1000, 'height': self.height, 'classification': 'proposed_design_not_physical_validation', 'minimum_text_px': min(t['size_px'] for t in self.texts), 'minimum_text_pt_at_425pt_width': round(min(t['size_px'] for t in self.texts)*425/1000, 2), 'labels': [t['text'] for t in self.texts]})
        print(self.name, 'rendered', flush=True)


def architecture():
    d = Drawing('system_scope', 550)
    d.box(20, 20, 280, 145, '清水台架与独立参照', ['共同供水 / A、B支路', 'P0、P1、Q与操作记录', '参考表 / 收集量 / 时间'])
    d.box(360, 20, 280, 145, '感知与本地诊断节点', ['标定 / 质量 / 运行状态', '健康参照与持续判据', '原始日志与事件摘要'])
    d.box(700, 20, 280, 145, 'LoRa接收与本地存储', ['接收 / 持久化 / 去重', '存储后发送ACK', '断链与待补发状态'])
    d.path([(300, 92), (360, 92)])
    d.path([(640, 92), (700, 92)])
    d.path([(840, 165), (840, 218)])
    d.box(700, 218, 280, 145, '管理软件与人工核查', ['趋势 / 事件 / 异常区段', '查看证据与处理确认', '历史回放与CSV导出'])
    d.box(360, 218, 280, 145, '独立实验与性能评价', ['故障程度及参照标签', '本地提示 / 远端送达', '漏检 / 误报 / 两段延迟'])
    d.path([(700, 285), (640, 285)])
    d.path([(160, 165), (160, 285), (360, 285)])
    d.label(235, 272, '独立标签')
    d.path([(500, 363), (500, 398)])
    d.box(180, 398, 640, 90, '项目交付与研究结论', ['台架和原型 / 数据和复现程序 / 辨识边界和通信取舍'])
    d.footer(['1个感知节点与1个接收端；管理确认结束闭环，现场扩展另行验证。'])
    d.render()


def water_layout():
    d = Drawing('dual_pressure_layout', 590)
    d.box(20, 90, 155, 100, '可调供水', ['工作点待核定'])
    d.path([(175, 140), (220, 140), (220, 106), (915, 106)], arrow=False)
    d.path([(220, 140), (220, 300), (915, 300)], arrow=False)
    for x, label, note in [(290, 'P0', '区段入口'), (570, 'P1', '受限下游'), (700, 'Q', 'A总流量')]:
        d.sensor(x, 106, label)
        d.text(x, 53, note)
    d.box(362, 79, 145, 54, '受限元件')
    d.box(815, 79, 145, 54, 'A正常负载')
    d.path([(768, 106), (768, 205), (970, 205)], arrow=False)
    d.box(815, 178, 145, 54, '泄漏调节阀')
    d.text(817, 269, '独立收集量与计时')
    d.box(362, 273, 145, 54, 'B切换阀')
    d.box(815, 273, 145, 54, 'B正常负载')
    d.text(569, 348, 'B模拟共同供水下的正常负载切换')
    d.path([(960, 106), (980, 106), (980, 385), (220, 385), (220, 430)], arrow=True)
    d.path([(960, 300), (980, 300)], arrow=False)
    d.box(70, 430, 350, 90, '回水或收集装置', ['泄漏支路收集后另行回水'])
    d.path([(70, 461), (12, 461), (12, 140), (20, 140)], dashed=True)
    d.footer(['布点与水路结构示意；接头、稳压、排气和防溅措施须在装配前核定。'])
    d.render()


def hardware():
    d = Drawing('hardware_node', 610)
    d.box(20, 20, 290, 120, '压力P0与P1', ['MPM489 / 4—20mA', '150Ω采样 → ADS1115'])
    d.box(20, 182, 290, 114, 'SEN0549流量Q', ['5V脉冲 → 3.3V转换', '定时计数 / 原始脉冲数'])
    d.box(20, 332, 290, 90, '操作状态与配置', ['阀态 / 时间 / 标定编号'])
    d.box(380, 55, 260, 315, 'STM32F103C8T6', ['I²C读双压力', '定时器计流量脉冲', '质量检查与持续判据', 'UART通信 / SPI日志', '会话序号与事件队列'])
    for y, destination_y, label in [(80, 110, 'I²C'), (236, 214, '计数'), (377, 320, '状态')]:
        d.path([(310, y), (343, y), (343, destination_y), (380, destination_y)])
        d.label(345, (y+destination_y)/2-14, label)
    d.box(715, 30, 265, 120, 'E220 LoRa模块', ['UART / 3.3V逻辑', '事件上报与ACK接收'])
    d.box(715, 205, 265, 95, 'microSD本地日志', ['原始测量与事件状态'])
    d.path([(640, 105), (675, 105), (675, 90), (715, 90)])
    d.path([(640, 257), (715, 257)])
    d.box(715, 350, 265, 117, '接收端与已有电脑', ['另一E220 → USB-TTL', 'Python / SQLite / Web'])
    d.path([(965, 150), (991, 150), (991, 406), (980, 406)], dashed=True)
    d.box(20, 466, 620, 90, '供电与接口保护按器件条件分别设计', ['压力供电 / 5V脉冲 / 3.3V逻辑须区分'])
    d.footer(['功能连接方案，非已完成电路；引脚、电流、保护及同步误差需实物核对。'])
    d.render()


def hydraulic_model():
    d = Drawing('hydraulic_model', 660)
    d.box(20, 55, 125, 65, '供压Ps')
    d.path([(145, 87), (190, 87), (190, 198), (242, 198)], arrow=False)
    d.box(242, 166, 150, 65, '共同阻力Rc')
    d.path([(392, 198), (448, 198), (448, 86), (973, 86)], arrow=False)
    d.path([(448, 198), (448, 321), (973, 321)], arrow=False)
    d.sensor(468, 86, 'P0')
    d.box(520, 59, 140, 54, 'A区段R')
    d.sensor(718, 86, 'P1')
    d.sensor(790, 86, 'Q')
    d.box(835, 59, 145, 54, '正常负载Cₙ')
    d.path([(819, 86), (819, 206), (973, 206)], arrow=False)
    d.box(835, 179, 145, 54, '泄漏负载Cₗ')
    d.box(520, 294, 140, 54, 'B区段阻力')
    d.box(747, 294, 225, 54, 'B状态与正常负载')
    d.text(190, 280, '共同供水压降')
    d.text(190, 314, '由A、B总流量决定')
    d.box(20, 401, 960, 114, '平方律等效关系与可解释特征', ['P0 − P1 = R·Q²；Q = (Cₙ + Cₗ)·√P1', 'K = Q/√P1；R̂ = (P0 − P1)/Q²'])
    d.text(22, 546, 'P单位kPa，Q单位L/min；R单位kPa/(L/min)²，C单位(L/min)/√kPa。', anchor='start')
    d.text(22, 580, 'R增加模拟受限；Cₗ增加模拟泄漏。未知Cₙ增加可与泄漏同形。', anchor='start')
    d.footer(['未标定集中模型：非压力补偿负载、理想同步、单故障；不含水锤或CFD。', '示意不代表管网尺寸或标定结果，实际压损与参数由清水试验核定。'])
    d.render()


def acquisition():
    d = Drawing('acquisition_flow', 850)
    d.box(55, 15, 520, 85, '启动与恢复', ['载入配置、标定编号、会话及未确认队列'])
    d.path([(315, 100), (315, 123)])
    d.box(55, 123, 520, 85, '采集并记录采样时间', ['P0 / P1分时ADC；Q脉冲与操作状态'])
    d.path([(315, 208), (315, 237)])
    d.diamond(315, 290, 490, 106, ['量程、同步、缺测和', '非物理读数检查通过？'])
    d.path([(560, 290), (670, 290)])
    d.label(613, 278, '否')
    d.box(670, 246, 305, 88, '标记数据无效', ['记录原因；停止原因判断'])
    d.path([(315, 343), (315, 373)])
    d.label(345, 366, '是')
    d.box(55, 373, 520, 87, '换算与计数窗口对齐', ['保留原始值；换算P0 / P1 / Q'])
    d.path([(315, 460), (315, 488)])
    d.diamond(315, 544, 490, 112, ['阀态和工况已知，', '且切换等待条件满足？'])
    d.path([(560, 544), (670, 544)])
    d.label(613, 532, '否')
    d.box(670, 500, 305, 88, '切换或状态未知', ['保留趋势；异常待检查'])
    d.path([(315, 600), (315, 627)])
    d.label(345, 621, '是')
    d.box(55, 627, 520, 85, '提交诊断输入', ['有效测量 / 状态 / 时间 / 健康参照编号'])
    d.path([(315, 712), (315, 742)])
    d.box(55, 742, 520, 60, '原始日志追加后进入下一采集周期')
    d.path([(975, 290), (988, 290), (988, 772), (575, 772)])
    d.path([(975, 544), (988, 544)], arrow=False)
    d.path([(55, 772), (23, 772), (23, 163), (55, 163)], dashed=True)
    d.footer(['拟实施流程；等待段仍评价漏检与误报，原始记录不因筛选而删除。'])
    d.render()


def diagnosis():
    d = Drawing('diagnosis_flow', 950)
    d.box(40, 16, 515, 85, '接收质量有效且状态明确的数据', ['采用已冻结的同工况健康参照'])
    d.path([(297, 101), (297, 119)])
    d.diamond(297, 174, 490, 110, ['Q、P1及健康压降满足', '本次试验的可计算条件？'])
    d.path([(542, 174), (652, 174)])
    d.label(600, 163, '否')
    d.box(652, 132, 320, 85, '不可可靠解释', ['记录低流量或压差不足'])
    d.path([(297, 229), (297, 258)])
    d.label(327, 250, '是')
    d.box(40, 258, 515, 114, '计算特征并记录不确定度', ['K = Q/√P1；R̂ = (P0−P1)/Q²', '比较同工况健康特征与误差区间'])
    d.path([(297, 372), (297, 399)])
    d.diamond(297, 458, 490, 118, ['偏离超过冻结判据，', '并满足持续条件？'])
    d.path([(542, 458), (652, 458)])
    d.label(600, 446, '否')
    d.box(652, 414, 320, 88, '当前未形成可靠异常', ['继续采样；保留趋势与日志'])
    d.path([(297, 517), (297, 546)])
    d.label(327, 538, '是')
    d.box(40, 546, 515, 114, '检查模式与适用条件', ['K偏离 / R̂偏离 / 运行状态', '偏置、未知负载与混合变化另行核查'])
    d.path([(297, 660), (297, 687)])
    d.diamond(297, 742, 490, 110, ['单一模式证据足够，', '且符合标定与状态条件？'])
    d.path([(542, 742), (652, 742)])
    d.label(600, 730, '否')
    d.box(652, 699, 320, 85, '异常待检查', ['保存证据；不指定唯一原因'])
    d.path([(297, 797), (297, 824)])
    d.label(327, 816, '是')
    d.box(40, 824, 515, 85, '汇总提示与事件证据', ['有限模式或待检查；保存首次提示时间'])
    d.path([(972, 174), (988, 174), (988, 868), (555, 868)])
    d.path([(972, 742), (988, 742)], arrow=False)
    d.footer(['拟实施判据须经标定小试冻结；低压弱异常和原因歧义保留为失败边界。'])
    d.render()


def protocol():
    d = Drawing('protocol_loop', 875)
    d.text(255, 31, '感知节点与本地事件队列', 26, True)
    d.text(760, 31, '接收端与本地管理软件', 26, True)
    d.box(25, 59, 455, 90, '新事件写入待确认队列', ['设备 / 会话 / 序号 / 发生时间 / 证据'])
    d.path([(252, 149), (252, 178)])
    d.box(25, 178, 455, 85, '发送队首事件并记录发送时间', ['断链保留待补发状态与原始日志'])
    d.path([(480, 215), (540, 215)])
    d.label(510, 195, '事件')
    d.box(540, 178, 440, 85, '接收并检查格式与事件身份', ['设备 + 会话 + 序号联合识别'])
    d.path([(760, 263), (760, 284)])
    d.diamond(760, 332, 400, 96, ['已持久化的重复事件？'])
    d.path([(760, 380), (760, 410)])
    d.label(790, 400, '否')
    d.box(540, 410, 440, 85, '先持久化再发送事件ACK', ['唯一记录；接收时间与错误日志'])
    d.path([(960, 332), (991, 332), (991, 518), (760, 518)])
    d.label(978, 315, '是')
    d.label(881, 528, '重复仍ACK')
    d.path([(760, 495), (760, 518)], arrow=False)
    d.box(540, 544, 440, 85, '记录已接收事件并呈现趋势', ['ACK只确认存储；处理确认另记'])
    d.path([(760, 518), (760, 544)])
    d.path([(760, 518), (500, 518), (500, 332), (450, 332)])
    d.label(500, 444, 'ACK')
    d.path([(252, 263), (252, 284)])
    d.diamond(252, 332, 395, 96, ['超时前收到匹配ACK？'])
    d.path([(252, 380), (252, 410)])
    d.label(280, 401, '是')
    d.box(25, 410, 455, 85, '确认完成并移除对应队列项', ['记录确认时间；准备下一事件'])
    d.path([(55, 332), (10, 332), (10, 567), (25, 567)])
    d.label(26, 393, '否')
    d.box(25, 530, 455, 114, '记录超时并限次退避重试', ['本轮重试耗尽仍保留待确认状态', '恢复后的再次发送规则由实测冻结'])
    d.path([(252, 530), (252, 507), (490, 507), (490, 165), (252, 165), (252, 178)], dashed=True)
    d.box(25, 675, 955, 114, '异常与恢复检查', ['队列满：明确记录丢弃或拒绝及缺口；重启：恢复队列或明确标记丢失', '离线显示 / ACK丢失后的重复接收 / 会话唯一性 / 处理确认均需实测'])
    d.footer(['拟实施协议；缓存、掉电策略、超时、重试和空中时间由无线试验核定。', '模型回放参数不是固件定值；远端接收时间与管理确认时间分别保存。'])
    d.render()


def experiment():
    d = Drawing('experiment_flow', 905)
    d.box(45, 15, 510, 85, '冻结预实验配置与评价定义', ['量程 / 标定 / 健康参照 / 程度 / 失效参照'])
    d.path([(300, 100), (300, 122)])
    d.diamond(300, 181, 490, 118, ['测量误差、供水稳定性', '与独立标签满足试验条件？'])
    d.path([(545, 181), (650, 181)])
    d.label(597, 170, '否')
    d.box(650, 137, 325, 88, '调整台架或测量方案', ['保留失败记录后重新校核'])
    d.path([(812, 137), (812, 108), (570, 108), (570, 55), (555, 55)])
    d.path([(300, 240), (300, 267)])
    d.label(330, 258, '是')
    d.box(45, 267, 510, 114, '执行独立操作与强对照', ['2类型×3供压×3程度×至少3重复', '正常与切换对照另做；保留原始日志'])
    d.path([(300, 381), (300, 408)])
    d.box(45, 408, 510, 114, '按独立日或批次留出验证', ['小试调参 / 留出批次验证', '固定阈值等强基线；测点与状态消融'])
    d.path([(300, 522), (300, 549)])
    d.box(45, 549, 510, 114, '同检测结果下比较四种上报策略', ['真实LoRa / 缓存ACK / 阻断与恢复', '独立计量整机能量；记录两段延迟'])
    d.path([(300, 663), (300, 690)])
    d.box(45, 690, 510, 114, '归档可复现结果与失败边界', ['试次漏检 / 每小时误报 / 提前量分布', '帧字节 / 送达率 / 能量 / 原始证据'])
    d.box(650, 323, 325, 145, '结项基本交付', ['真实台架与系统演示', '日志 / 数据 / 技术报告', '至少8小时连续记录'])
    d.box(650, 501, 325, 145, '论文数据与贡献审核', ['独立标签及跨批次结果', '强基线 / 消融 / 局限', '导师审核后形成论文稿'])
    d.path([(555, 747), (615, 747), (615, 382), (650, 382)])
    d.path([(615, 560), (650, 560)])
    d.footer(['拟实施验证流程；相邻样本和程序种子不计为独立物理重复。', '现场试验以许可为条件；只有正常数据时不报告田间故障准确率。'])
    d.render()


if __name__ == '__main__':
    from build_application_visuals import main
    main()
