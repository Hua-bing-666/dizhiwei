"""Windows desktop host for the existing C/SQLite operations platform."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import hashlib
import json
import logging
import os
import sys
import threading
import tempfile

ROOT = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'prototype'), str(ROOT/'simulation')]
TITLE = '滴智卫 · 支管巡检平台 V1.3'


def message(text, error=False):
    ctypes.windll.user32.MessageBoxW(None, text, TITLE, 0x10 if error else 0x40)


def data_directory():
    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else ROOT/'tmp/desktop_runtime'
    folder = base/'data'
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder/'.write-check'
        probe.write_text('ok', encoding='ascii')
        probe.unlink()
    except OSError:
        folder = Path(os.environ['LOCALAPPDATA'])/'DizhiweiDesktop'/'data'
        folder.mkdir(parents=True, exist_ok=True)
    return folder


class Instance:
    """Windows releases the mutex even after a crash; no stale lock file."""
    def __init__(self, folder):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel.CreateMutexW.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        key = hashlib.sha256(str(folder.resolve()).casefold().encode()).hexdigest()[:32]
        self.handle = self.kernel.CreateMutexW(None, False, 'Local\\Dizhiwei-'+key)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.exists = ctypes.get_last_error() == 183

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


class LocalService:
    def __init__(self, folder):
        self.folder = folder
        self.ready = threading.Event()
        self.http = None
        self.error = None
        self.thread = threading.Thread(target=self.run, name='SQLite-service')

    def run(self):
        try:
            from run_platform import create_server
            self.http = create_server(0, self.folder/'operations.sqlite')
            self.url = f'http://127.0.0.1:{self.http.server_port}'
            (self.folder/'runtime.json').write_text(json.dumps(dict(
                pid=os.getpid(), url=self.url, version='1.3.0', database=str(self.folder/'operations.sqlite')
            ), ensure_ascii=False), encoding='utf-8')
            logging.info('Service ready: %s', self.url)
            self.ready.set()
            self.http.serve_forever(poll_interval=.15)
        except Exception as exc:
            self.error = exc
            logging.exception('Local service failed')
            self.ready.set()
        finally:
            if self.http:
                self.http.server_close()
                self.http.platform.close()
            (self.folder/'runtime.json').unlink(missing_ok=True)
            logging.info('SQLite and C worker closed')

    def start(self):
        self.thread.start()
        # Wait for actual readiness, not a fixed sleep; errors retain a log.
        self.ready.wait()
        if self.error:
            raise RuntimeError(str(self.error)) from self.error

    def close(self):
        if self.http and self.thread.is_alive():
            self.http.shutdown()
        if self.thread.ident:
            self.thread.join(timeout=12)
            if self.thread.is_alive():
                raise RuntimeError('本地服务未能及时退出，请保留桌面日志。')


class DesktopAPI:
    def __init__(self, folder):
        self._window = None
        self._folder = folder
        self._preferences_lock = threading.Lock()

    def read_preferences(self):
        with self._preferences_lock:
            return self._read_preferences()

    def _read_preferences(self):
        result=dict(theme='light',chart_range=180)
        try:
            stored=json.loads((self._folder/'preferences.json').read_text(encoding='utf-8'))
            if stored.get('theme') in ('light','dark'):result['theme']=stored['theme']
            if type(stored.get('chart_range')) is int and stored['chart_range'] in (0,180,600):result['chart_range']=stored['chart_range']
        except (OSError,ValueError,AttributeError):pass
        return result

    def save_preferences(self, values):
        if not isinstance(values,dict) or set(values)-{'theme','chart_range'}:
            raise ValueError('偏好参数无效。')
        if 'theme' in values and values['theme'] not in ('light','dark'):
            raise ValueError('配色参数无效。')
        if 'chart_range' in values and (type(values['chart_range']) is not int or values['chart_range'] not in (0,180,600)):
            raise ValueError('曲线范围无效。')
        with self._preferences_lock:
            result={**self._read_preferences(),**values}
            target=self._folder/'preferences.json'
            temporary=target.with_suffix('.tmp')
            temporary.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
            os.replace(temporary,target)
        return result

    def save_export(self, name, text):
        """Native save dialog: consecutive exports are not browser downloads."""
        if name not in ('drip-samples.csv','drip-records.json','drip-legacy-workspace.json'):
            return dict(saved=False,error='导出文件名称无效。')
        if not isinstance(text,str) or len(text.encode('utf-8'))>32*1024*1024:
            return dict(saved=False,error='导出内容无效或超过 32 MB，请分会话导出。')
        import webview
        suffix=Path(name).suffix
        result=self._window.create_file_dialog(webview.FileDialog.SAVE,
            save_filename=name, file_types=(f'{suffix[1:].upper()} 文件 (*{suffix})',))
        if not result:
            return dict(saved=False,cancelled=True)
        target=Path(result[0] if isinstance(result,(tuple,list)) else result)
        if not target.suffix:target=target.with_suffix(suffix)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',
                    dir=target.parent,prefix='.drip-export-',suffix='.tmp',delete=False) as stream:
                temporary=Path(stream.name)
                stream.write(text)
            os.replace(temporary,target)
            logging.info('Export saved: %s',target)
            return dict(saved=True,path=str(target))
        except OSError:
            logging.exception('Export failed')
            return dict(saved=False,error='保存失败，请检查目标文件夹权限或文件是否被占用。')
        finally:
            if temporary:temporary.unlink(missing_ok=True)


def main():
    folder = data_directory()
    instance = Instance(folder)
    if instance.exists:
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user.FindWindowW.restype = wintypes.HWND
        user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user.IsIconic.argtypes = [wintypes.HWND]
        user.IsIconic.restype = wintypes.BOOL
        user.SetForegroundWindow.argtypes = [wintypes.HWND]
        handle = user.FindWindowW(None, TITLE)
        if handle:
            if user.IsIconic(handle):
                user.ShowWindow(handle, 9)
            user.SetForegroundWindow(handle)
        instance.close()
        return
    log_stream = (folder/'desktop.log').open('a', encoding='utf-8', buffering=1)
    sys.stdout = sys.stderr = log_stream
    logging.basicConfig(stream=log_stream, level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    service = LocalService(folder)
    try:
        logging.info('Desktop 1.3.0 starting; data=%s', folder)
        service.start()
        import webview
        from webview.menu import Menu, MenuAction, MenuSeparator
        webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
        api=DesktopAPI(folder)
        window = webview.create_window(TITLE, service.url+'/?desktop=1',
                                       width=1100, height=740, min_size=(760, 520),
                                       maximized=True, js_api=api,
                                       text_select=True, background_color='#f7f9f8')
        api._window=window
        menu = [Menu('文件', [
            MenuAction('打开数据文件夹', lambda: os.startfile(str(folder))),
            MenuSeparator(), MenuAction('退出', window.destroy)
        ]), Menu('帮助', [MenuAction('关于滴智卫', lambda: message(
            '滴智卫 · 支管巡检平台\n版本 1.3.0\n\n'
            'C 诊断核心 / 本地 SQLite / 清水试验台架模型\n'
            '当前使用合成数据与软件回放，未接入实物传感器或无线设备。\n\n'
            f'数据目录：{folder}\n关闭程序后，记录仍保留在本机。'
        ))])]
        webview.start(gui='edgechromium', private_mode=False,
                      storage_path=str(folder/'webview'), menu=menu,
                      icon=str(ROOT/'desktop/app.ico'),
                      localization={'global.quitConfirmation':'确认退出滴智卫？',
                                    'global.saveFile':'保存文件', 'global.cancel':'取消'})
    except Exception as exc:
        logging.exception('Desktop startup/runtime error')
        message(f'桌面版未能正常启动：{exc}\n\n'
                f'日志：{folder / "desktop.log"}\n'
                '请确认解压了完整文件夹，并已安装 Microsoft Edge WebView2 Runtime。', True)
    finally:
        service.close()
        instance.close()
        logging.info('Desktop exited')
        log_stream.flush()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        message(f'无法启动滴智卫：{exc}', True)
