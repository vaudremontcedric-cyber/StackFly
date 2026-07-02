"""
Script v3 - Navigation directe vers la page Render et clic Manual Deploy.
Chrome est deja au premier plan sur la tab Render.
"""
import ctypes
import ctypes.wintypes
import time
import subprocess
import sys
import os

user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
KEYEVENTF_KEYUP = 0x0002

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.2)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)

def key_down(vk):
    user32.keybd_event(vk, 0, 0, 0)

def key_up(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def press_key(vk):
    key_down(vk)
    time.sleep(0.05)
    key_up(vk)
    time.sleep(0.1)

def ctrl_l():
    """Ouvre la barre d'adresse Chrome"""
    key_down(0x11)  # CTRL
    press_key(0x4C)  # L
    key_up(0x11)
    time.sleep(0.5)

def type_text(text):
    """Type text via clipboard for reliability"""
    # Use PowerShell to set clipboard
    ps = f'Set-Clipboard -Value "{text}"'
    subprocess.run(['powershell', '-Command', ps], capture_output=True, timeout=5)
    time.sleep(0.3)
    # Ctrl+A to select all, then Ctrl+V to paste
    key_down(0x11)  # CTRL
    press_key(0x41)  # A
    key_up(0x11)
    time.sleep(0.1)
    key_down(0x11)  # CTRL
    press_key(0x56)  # V
    key_up(0x11)
    time.sleep(0.3)

def press_enter():
    press_key(0x0D)

def take_screenshot(filename):
    ps = f"""
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{filename}')
$graphics.Dispose(); $bitmap.Dispose()
"""
    subprocess.run(['powershell', '-Command', ps], capture_output=True, timeout=10)
    print(f"Screenshot: {filename}")

def get_chrome():
    chrome_hwnd = None
    chrome_size = 0
    def callback(hwnd, _):
        nonlocal chrome_hwnd, chrome_size
        if user32.IsWindowVisible(hwnd):
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value == 'Chrome_WidgetWin_1':
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 800 and h > 400:
                    buf = ctypes.create_unicode_buffer(512)
                    user32.GetWindowTextW(hwnd, buf, 512)
                    # Prendre Chrome, pas Claude
                    if 'Claude' not in buf.value:
                        size = w * h
                        if size > chrome_size:
                            chrome_hwnd = hwnd
                            chrome_size = size
        return True
    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(cb(callback), 0)
    return chrome_hwnd

base_dir = r"C:\Users\vaudr\Claude\Projects\application budget"

print("=== RENDER DEPLOY v3 ===")

# Trouver Chrome (exclure Claude)
hwnd = get_chrome()
if not hwnd:
    print("ERREUR: Chrome non trouve!")
    sys.exit(1)

buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(hwnd, buf, 512)
rect = ctypes.wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
print(f"Chrome: hwnd={hwnd}, titre='{buf.value[:60]}', pos=({rect.left},{rect.top})")

# Mettre Chrome au premier plan
user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# Screenshot initial
take_screenshot(os.path.join(base_dir, "v3_step1_before.png"))

# Naviguer vers la page principale du service StackFly
print("\nNavigation vers la page du service Render...")
ctrl_l()
time.sleep(0.3)
type_text("https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0")
time.sleep(0.2)
press_enter()
time.sleep(5)  # Attendre le chargement

take_screenshot(os.path.join(base_dir, "v3_step2_service.png"))
print("Page service chargee")

# Sur la page service Render, le bouton "Manual Deploy" est dans le header
# Generalement en haut a droite du contenu principal
# Screen maximise 1456x816 (ou similar)
# Le bouton est a droite, vers x=1250-1380, y=180-220

# D'abord scroller vers le haut au cas ou
key_down(0x11)  # CTRL
press_key(0x24)  # HOME
key_up(0x11)
time.sleep(0.5)

# Clic sur le bouton "Manual Deploy"
# Sur Render la page service principale a le bouton en haut a droite
# Coords approximatives sur ecran maximise:
deploy_btn_x = 1280
deploy_btn_y = 200
print(f"\nClic 'Manual Deploy': ({deploy_btn_x},{deploy_btn_y})")
click(deploy_btn_x, deploy_btn_y)
time.sleep(1.5)

take_screenshot(os.path.join(base_dir, "v3_step3_menu.png"))

# Clic sur "Deploy latest commit"
deploy_item_x = deploy_btn_x
deploy_item_y = deploy_btn_y + 45
print(f"Clic 'Deploy latest commit': ({deploy_item_x},{deploy_item_y})")
click(deploy_item_x, deploy_item_y)
time.sleep(3)

take_screenshot(os.path.join(base_dir, "v3_step4_final.png"))

print("\n=== TERMINE ===")
print("Verifie les screenshots v3_step*.png")
input("Appuie sur Entree pour fermer...")
