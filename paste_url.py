"""
Paste URL dans la barre d'adresse Chrome active + Enter
"""
import ctypes
import time

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

KEYEVENTF_KEYUP = 0x0002

def key_down(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)

def key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

def paste(text):
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE  = 0x0002
    encoded = (text + '\0').encode('utf-16-le')
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, encoded, len(encoded))
    kernel32.GlobalUnlock(h)
    user32.OpenClipboard(0)
    user32.EmptyClipboard()
    user32.SetClipboardData(CF_UNICODETEXT, h)
    user32.CloseClipboard()
    key_down(0x11)   # Ctrl
    key_down(0x56)   # V
    time.sleep(0.1)
    key_up(0x56)
    key_up(0x11)
    time.sleep(0.3)

# Trouver Chrome et le mettre au premier plan
hwnds = []
def enum_cb(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if cls_buf.value == 'Chrome_WidgetWin_1':
                hwnds.append((hwnd, buf.value))
    return True

import ctypes.wintypes
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)

if not hwnds:
    print("ERREUR: Chrome non trouve")
    exit(1)

hwnd = hwnds[0][0]
user32.SetForegroundWindow(hwnd)
time.sleep(0.5)

# Ctrl+L pour s'assurer que la barre est active
key_down(0x11)
key_down(0x4C)
time.sleep(0.05)
key_up(0x4C)
key_up(0x11)
time.sleep(0.4)

# Coller l'URL
url = "file:///C:/Users/vaudr/Claude/Projects/application%20budget/CoachFinancier.html"
print(f"Collage: {url}")
paste(url)
time.sleep(0.2)

# Enter
user32.keybd_event(0x0D, 0, 0, 0)
time.sleep(0.05)
user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)
time.sleep(4.0)  # attendre chargement

print("=== Done ===")
