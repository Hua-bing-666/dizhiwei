# -*- coding: utf-8 -*-
"""SD 卡 CSV 导入器（命令行）。

把固件写在 SD 卡上的 CSV 直接导入桌面端 SQLite，生成一个可在 Web/桌面平台查看的会话。

用法：
    python scripts/import_sdcard_csv.py <sdcard.csv> [--db path/to/operations.sqlite] [--label "田间 1# 节点"]

CSV 格式：固件输出的表头与数据行，例如：
    seq,unix_ms,p0_centi,p1_centi,dp_centi,q_milli,count10,quality,zq_milli,zr_milli,sq_milli,alarm
    0,1000,11650,10975,675,0,26,4,0,0,0,0

说明：
- 本导入器使用合成健康参照作为候选配置（approved=0），仅供桌面端查看与核查，
  不能替代真实台架标定后的健康参照。
- q_milli 是 10 s 平均流量，导入时按 540 pulses/L 反推近似累计脉冲。
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'prototype'))
sys.path.insert(0, str(ROOT / 'simulation'))
from platform_service import Platform


def main():
    ap = argparse.ArgumentParser(description='把节点 SD 卡 CSV 导入滴智卫桌面端 SQLite')
    ap.add_argument('csv', help='SD 卡 CSV 文件路径')
    ap.add_argument('--db', default=str(ROOT / 'tmp' / 'desktop_runtime' / 'operations.sqlite'),
                    help='目标桌面端 SQLite 路径（默认 tmp/desktop_runtime/operations.sqlite）')
    ap.add_argument('--label', default='SD card import', help='会话标签')
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f'文件不存在：{csv_path}', file=sys.stderr)
        return 1
    text = csv_path.read_text(encoding='utf-8')
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    platform = Platform(str(db_path))
    try:
        state = platform.import_sdcard(text, label=args.label)
        run = state['run']
        print(f'导入成功：session={run["session"]}')
        print(f'  文件：{csv_path}')
        print(f'  标签：{run["label"]}')
        print(f'  导入行数：{run["imported_rows"]}')
        print(f'  处理样本数：{run["processed_samples"]}')
        print(f'  事件数：{run["events_count"]}')
        print(f'  数据库：{db_path}')
    finally:
        platform.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
