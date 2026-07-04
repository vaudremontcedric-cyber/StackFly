import ctypes
import ctypes.wintypes
import time

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

def click(x, y, delay=0.25):
    user32.SetCursorPos(x, y)
    time.sleep(delay)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.09)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
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
    user32.keybd_event(0x11, 0, 0, 0)
    user32.keybd_event(0x56, 0, 0, 0)
    time.sleep(0.06)
    user32.keybd_event(0x56, 0, 2, 0)
    user32.keybd_event(0x11, 0, 2, 0)
    time.sleep(0.15)

# Trouver Chrome RescueBudget
hwnds = []
def enum_cb(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if cls_buf.value == 'Chrome_WidgetWin_1' and 'RescueBudget' in buf.value:
                hwnds.append((hwnd, buf.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)

if not hwnds:
    print("ERREUR: Chrome RescueBudget non trouvé")
    exit(1)

hwnd = hwnds[0][0]
user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# Coordonnées plein écran — form centrée x≈728
CX       = 728
TAB_CREER = CX     # Tab "Créer un compte" = centre exact
TAB_Y     = 658    # Ligne des onglets

print("=== TEST: Tab 'Créer un compte' ===")
click(TAB_CREER, TAB_Y)
time.sleep(0.8)

print("=== Remplir identifiant ===")
click(CX, 504)
paste("TestUser")

print("=== Mot de passe ===")
click(CX, 575)
paste("test1234")

print("=== Confirmer ===")
click(CX, 645)
paste("test1234")
time.sleep(0.3)

print("=== Soumettre 'Créer mon compte' ===")
click(CX, 706)
time.sleep(3)
print("Test terminé")
