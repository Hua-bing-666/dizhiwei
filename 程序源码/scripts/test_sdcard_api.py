# -*- coding: utf-8 -*-
"""测试 /api/sdcard/import HTTP 端点。"""
import json, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'firmware' / 'build' / 'out_normal.csv'
DB = ROOT / 'tmp' / 'sdcard_api_test.sqlite'
PORT = 9876

def poll_state(retries=100):
    for i in range(retries):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/state', timeout=1)
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.3)
    return False

def main():
    if not CSV.exists():
        print('缺少测试 CSV:', CSV); return 1
    if DB.exists(): DB.unlink()
    proc = subprocess.Popen(
        [sys.executable, str(ROOT/'scripts'/'run_platform.py'), '--port', str(PORT), '--db', str(DB)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        if not poll_state():
            out, _ = proc.communicate(timeout=1)
            print('服务未启动'); print(out[-2000:]); return 1
        text = CSV.read_text(encoding='utf-8')
        data = json.dumps({'csv': text, 'label': 'api test out_normal'}).encode('utf-8')
        req = urllib.request.Request(f'http://127.0.0.1:{PORT}/api/sdcard/import', data=data,
                                     headers={'Content-Type': 'application/json'})
        try:
            resp = urllib.request.urlopen(req, timeout=60)
        except urllib.error.HTTPError as e:
            print('HTTP 400 body:', e.read().decode('utf-8'))
            raise
        result = json.loads(resp.read().decode('utf-8'))
        print('API 导入结果:')
        print('  session:', result['run']['session'])
        print('  imported_rows:', result['run']['imported_rows'])
        print('  processed_samples:', result['run']['processed_samples'])
        print('  events_count:', result['run']['events_count'])
        # verify history
        hist = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/history').read())
        print('  /api/history samples:', len(hist['samples']))
        return 0
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()

if __name__ == '__main__':
    sys.exit(main())
