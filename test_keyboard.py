"""
Test RescueBudget via keyboard navigation — DPI-independent.
Flux: F5 → Tab×5 → Enter (showRegister) → fill form → Enter (doRegister)
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

# --- Trouver Chrome RescueBudget ---
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
user32.ShowWindow(hwnd, 3)      # SW_MAXIMIZE
time.sleep(0.4)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# === 1. Rafraîchir la page pour partir de form-login ===
print("[1] F5 – rechargement...")
key_press(0x1B, 0.1)  # Escape (ferme éventuel autocomplete)
key_press(0x74, 2.5)  # F5 + attendre chargement

# === 2. Tab x5 → arrive sur ltab-register (Créer un compte) ===
print("[2] Tab ×5 pour atteindre 'Créer un compte'...")
# Tab order: loginUser(1) → loginPass(2) → btn-login(3) → ltab-login(4) → ltab-register(5)
for i in range(5):
    key_press(0x09, 0.18)  # Tab

# === 3. Enter → showRegister() → regUser reçoit le focus ===
print("[3] Enter → active 'Créer un compte'...")
key_press(0x0D, 0.5)  # Enter
time.sleep(0.4)  # Attendre setTimeout(100ms) de showRegister

# === 4. Saisir identifiant (regUser est focalisé) ===
print("[4] Identifiant: TestUser2")
paste("TestUser2")
time.sleep(0.1)

# === 5. Enter → focus sur regPass ===
key_press(0x0D, 0.25)
print("[5] Mot de passe: test1234")
paste("test1234")
time.sleep(0.1)

# === 6. Enter → focus sur regPass2 ===
key_press(0x0D, 0.25)
print("[6] Confirmer: test1234")
paste("test1234")
time.sleep(0.1)

# === 7. Enter → doRegister() ===
print("[7] Enter → doRegister()...")
key_press(0x0D, 3.0)  # attendre 3s après soumission

print("=== Test terminé. Prendre screenshot. ===")
