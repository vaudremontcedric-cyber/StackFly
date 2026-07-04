"""
Ouvre localhost:10000 dans Chrome via keyboard (DPI-independent)
"""
import ctypes
import ctypes.wintypes
import time

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

KEYEVENTF_KEYUP = 0x0002

def key_down(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.04)

def key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.04)

def key_press(vk, delay=0.15):
    key_down(vk)
    key_up(vk)
    time.sleep(delay)

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
    time.sleep(0.06)
    key_up(0x56)
    key_up(0x11)
    time.sleep(0.2)

# Trouver Chrome
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

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)

if not hwnds:
    print("ERREUR: Chrome non trouve")
    exit(1)

hwnd = hwnds[0][0]
print(f"Chrome trouve: {hwnds[0][1]}")
user32.ShowWindow(hwnd, 3)
time.sleep(0.4)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# Ctrl+T -> nouvel onglet
print("Ctrl+T...")
key_down(0x11)
key_press(0x54, 0.3)
key_up(0x11)
time.sleep(0.5)

# Ctrl+L -> barre d'adresse
key_down(0x11)
key_press(0x4C, 0.3)
key_up(0x11)
time.sleep(0.3)

# Taper l'URL
print("Saisie URL...")
paste("file:///C:/Users/vaudr/Claude/Projects/application%20budget/CoachFinancier.html")
time.sleep(0.2)
key_press(0x0D, 3.5)  # Enter + attente chargement

print("=== Navigation terminee ===")
