"""
Script v4 - Clic precis sur le bouton "Manual Deploy" visible sur la page.
La page est deja sur dashboard.render.com/web/srv-d8qnpbvavr4c73djols0
Il faut:
1. Fermer le popup Outbound IP (Escape)
2. Cliquer sur "Manual Deploy" (bouton tout en haut a droite)
3. Cliquer sur "Deploy latest commit"
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
    time.sleep(0.25)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.4)

def press_escape():
    user32.keybd_event(0x1B, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(0x1B, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.3)

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

print("=== RENDER DEPLOY v4 ===")
print("Cible: bouton 'Manual Deploy' sur page service StackFly")

hwnd = get_chrome()
if not hwnd:
    print("ERREUR: Chrome non trouve!")
    sys.exit(1)

buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(hwnd, buf, 512)
rect = ctypes.wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
print(f"Chrome: hwnd={hwnd}, pos=({rect.left},{rect.top}) -> ({rect.right},{rect.bottom})")

# Mettre Chrome au premier plan
user32.ShowWindow(hwnd, 3)
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# 1. Fermer le popup (Escape ou clic dans zone neutre)
print("\n1. Fermeture du popup (Escape)...")
press_escape()
time.sleep(0.5)
# Clic dans zone neutre au milieu de la page pour fermer le popup
click(700, 450)
time.sleep(0.5)

take_screenshot(os.path.join(base_dir, "v4_step1_closed_popup.png"))

# 2. Cliquer sur le bouton "Manual Deploy"
# Sur l'ecran maximise (1456x816), le bouton "Manual Deploy" est en haut a droite
# D'apres la screenshot, il est a environ x=1325, y=235
# Mais la fenetre Chrome maximisee a left=-7, donc coords absolues:
# Si la fenetre est maximisee et left=-7:
#   x_screen = x_win + left = x_win - 7
# On veut cliquer sur "Manual Deploy": x_screen=1325, y_screen=235

manual_deploy_x = 1325
manual_deploy_y = 235
print(f"\n2. Clic 'Manual Deploy': ({manual_deploy_x},{manual_deploy_y})")
click(manual_deploy_x, manual_deploy_y)
time.sleep(1.5)

take_screenshot(os.path.join(base_dir, "v4_step2_menu.png"))

# 3. Clic sur "Deploy latest commit" (premier element du dropdown)
# Le dropdown apparait juste sous le bouton
deploy_latest_x = manual_deploy_x
deploy_latest_y = manual_deploy_y + 45
print(f"\n3. Clic 'Deploy latest commit': ({deploy_latest_x},{deploy_latest_y})")
click(deploy_latest_x, deploy_latest_y)
time.sleep(3)

take_screenshot(os.path.join(base_dir, "v4_step3_deploying.png"))

print("\n=== TERMINE ===")
print("Verifie v4_step*.png pour confirmer le deploy")
input("Appuie sur Entree pour fermer...")
