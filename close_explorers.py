import ctypes
import ctypes.wintypes
import time

user32 = ctypes.windll.user32
WM_CLOSE = 0x0010

def enum_cb(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if cls_buf.value == 'CabinetWClass':  # File Explorer class
                print(f"Closing Explorer: {buf.value}")
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)
print("Done")
