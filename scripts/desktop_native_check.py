"""Native Windows automation for EXE acceptance; not shipped with the app."""
import ctypes
from ctypes import wintypes
import json
import sys

user = ctypes.WinDLL('user32',use_last_error=True)
user.SetProcessDPIAware()
user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
user.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
user.IsWindowVisible.argtypes=[wintypes.HWND]
user.GetDlgCtrlID.argtypes=[wintypes.HWND]
user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
user.SendMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
user.SendMessageW.restype=wintypes.LPARAM
callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
user.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
user.EnumChildWindows.argtypes=[wintypes.HWND,callback_type,wintypes.LPARAM]


def info(handle):
    text=ctypes.create_unicode_buffer(512);cls=ctypes.create_unicode_buffer(256)
    user.GetWindowTextW(handle,text,512);user.GetClassNameW(handle,cls,256)
    pid=wintypes.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(pid))
    return dict(hwnd=handle,title=text.value,cls=cls.value,pid=pid.value,
                visible=bool(user.IsWindowVisible(handle)),id=user.GetDlgCtrlID(handle))


def windows(pid):
    result=[]
    @callback_type
    def visit(handle,_):
        row=info(handle)
        if row['pid']==pid and row['visible']:result.append(row)
        return True
    user.EnumWindows(visit,0)
    return result


action,pid=sys.argv[1],int(sys.argv[2])
rows=windows(pid)
if action=='list':print(json.dumps(rows,ensure_ascii=False))
elif action=='close':
    main=next(r for r in rows if r['title'].startswith('滴智卫 ·'))
    user.PostMessageW(main['hwnd'],0x10,0,0)
    print('WM_CLOSE posted')
elif action=='save':
    dialog=next(r for r in rows if r['cls']=='#32770')
    children=[]
    @callback_type
    def visit(handle,_):
        children.append(info(handle));return True
    user.EnumChildWindows(dialog['hwnd'],visit,0)
    edit=next(r for r in children if r['cls']=='Edit' and r['id']==1001 and r['visible'])
    name=ctypes.create_unicode_buffer(sys.argv[3])
    user.SendMessageW(edit['hwnd'],0xC,0,ctypes.cast(name,ctypes.c_void_p).value)
    user.PostMessageW(dialog['hwnd'],0x111,1,0)
    print('Save confirmed')
elif action=='screen':
    from PIL import ImageGrab
    main=next(r for r in rows if r['title'].startswith('滴智卫 ·'))
    user.SetForegroundWindow.argtypes=[wintypes.HWND]
    user.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    user.SetForegroundWindow(main['hwnd'])
    rect=wintypes.RECT();user.GetWindowRect(main['hwnd'],ctypes.byref(rect))
    ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom)).save(sys.argv[3])
    print('Native window captured')
