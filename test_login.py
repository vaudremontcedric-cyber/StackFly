"""
Test connexion avec TestUser2 (deja cree)
Flux: F5 -> Tab(loginUser) -> paste user -> Tab -> paste pwd -> Enter (login)
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
    key_down(vk); key_up(vk); time.sleep(delay)

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
    key_down(0x11); key_down(0x56)
    time.sleep(0.08)
    key_up(0x56); key_up(0x11)
    time.sleep(0.25)

# Trouver Chrome RescueBudget
hwnds = []
def enum_cb(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        l = user32.GetWindowTextLengthW(hwnd)
        if l > 0:
            buf = ctypes.create_unicode_buffer(l + 1)
            user32.GetWindowTextW(hwnd, buf, l + 1)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            if cls.value == 'Chrome_WidgetWin_1' and 'RescueBudget' in buf.value:
                hwnds.append((hwnd, buf.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)

if not hwnds:
    print("ERREUR: Chrome RescueBudget non trouve")
    exit(1)

hwnd = hwnds[0][0]
user32.ShowWindow(hwnd, 3)
time.sleep(0.4)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# 1. F5 pour reset la page
print("[1] F5 rechargement...")
key_press(0x1B, 0.1)
key_press(0x74, 2.5)  # F5

# 2. Le focus est sur loginUser (premier champ)
# En principe le focus va automatiquement sur #loginUser au chargement
print("[2] Identifiant: TestUser2")
paste("TestUser2")

# 3. Tab -> loginPass
key_press(0x09, 0.2)
print("[3] Mot de passe: test1234")
paste("test1234")

# 4. Enter -> doLogin()
print("[4] Enter -> connexion...")
key_press(0x0D, 3.0)

print("=== Test login termine ===")
