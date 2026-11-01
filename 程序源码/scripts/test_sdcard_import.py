# -*- coding: utf-8 -*-
"""SD 卡 CSV 导入链路测试：把 firmware/build/out_normal.csv 直接喂进平台，
验证桌面端会话生成成功、样本可查询、事件可列出。"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'prototype'))
sys.path.insert(0, str(ROOT/'simulation'))
from platform_service import Platform

def main():
    csv_path = ROOT / 'firmware' / 'build' / 'out_normal.csv'
    if not csv_path.exists():
        print('缺少测试文件:', csv_path)
        print('请先编译并运行固件 host 回放，或提供其他 SD 卡 CSV。')
        return 1
    text = csv_path.read_text(encoding='utf-8')
    db_path = ROOT / 'tmp' / 'sdcard_import_test.sqlite'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    platform = Platform(str(db_path))
    try:
        state = platform.import_sdcard(text, label='测试：out_normal.csv')
        print('导入成功')
        print('  会话 session:', state['run']['session'])
        print('  导入行数:', state['run']['imported_rows'])
        print('  处理样本数:', state['run']['processed_samples'])
        print('  事件数:', state['run']['events_count'])
        print('  当前样本:', state.get('current'))
        # 查询历史
        hist = platform.history(state['run']['session'])
        print('  history 返回样本数:', len(hist['samples']))
        print('  history 返回事件数:', len(hist['events']))
    finally:
        platform.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
