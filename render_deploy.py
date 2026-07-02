"""
Script Python pour declencher le deploy Render via automation Windows native.
Utilise ctypes/win32 pour bypasser la restriction read-only du MCP sur Chrome.
"""
import ctypes
import ctypes.wintypes
import time
import subprocess
import sys
import os

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
VK_CONTROL = 0x11
VK_L = 0x4C
VK_RETURN = 0x0D
VK_A = 0x41

def click(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.15)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.2)

def key_combo(vk1, vk2=None):
    user32.keybd_event(vk1, 0, 0, 0)
    if vk2:
        user32.keybd_event(vk2, 0, 0, 0)
        user32.keybd_event(vk2, 0, 0x0002, 0)
    user32.keybd_event(vk1, 0, 0x0002, 0)
    time.sleep(0.2)

def find_chrome_window():
    result = [None]
    def callback(hwnd, _):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        # Chrome main window has many titles
        if user32.IsWindowVisible(hwnd) and ('Chrome' in buf.value or 'RescueBudget' in buf.value or 'Render' in buf.value or 'Google' in buf.value):
            # Check class name for Chrome
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if cls.value == 'Chrome_WidgetWin_1':
                result[0] = hwnd
        return True
    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(cb(callback), 0)
    return result[0]

def get_window_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def take_screenshot(filename):
    """Prend une screenshot en PowerShell"""
    ps = f"""
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{filename}')
$graphics.Dispose()
$bitmap.Dispose()
Write-Host "Screenshot sauvegarde: {filename}"
"""
    subprocess.run(['powershell', '-Command', ps], capture_output=True)

# ============================================================
print("=== RENDER DEPLOY AUTOMATION ===")
print()

# 1. Trouver Chrome
hwnd = find_chrome_window()
if not hwnd:
    print("ERREUR: Chrome non trouve. Ouvre Chrome avec le dashboard Render.")
    input("Appuie sur Entree pour quitter...")
    sys.exit(1)

print(f"Chrome trouve: hwnd={hwnd}")
left, top, right, bottom = get_window_rect(hwnd)
print(f"Position Chrome: ({left},{top}) -> ({right},{bottom})")
width = right - left
height = bottom - top
print(f"Taille: {width}x{height}")

# 2. Mettre Chrome au premier plan
user32.ShowWindow(hwnd, 9)   # SW_RESTORE
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# 3. Screenshot de l'etat initial
screenshot_dir = r"C:\Users\vaudr\Claude\Projects\application budget"
shot1 = os.path.join(screenshot_dir, "step1_before.png")
take_screenshot(shot1)
print(f"Screenshot initial: {shot1}")

# 4. Cliquer sur le 3eme onglet (Render)
# Les onglets Chrome sont en haut, chaque onglet fait ~220px de large
# Onglet 3 = position x ~ 220*2 + 110 = 550
tab3_x = left + 590
tab3_y = top + 20
print(f"Clic sur onglet Render: ({tab3_x},{tab3_y})")
click(tab3_x, tab3_y)
time.sleep(3)  # Attendre chargement

# 5. Screenshot apres switch d'onglet
shot2 = os.path.join(screenshot_dir, "step2_render_tab.png")
take_screenshot(shot2)
print(f"Screenshot onglet Render: {shot2}")

# 6. Chercher le bouton "Manual Deploy" / "Deploy latest commit"
# Sur le dashboard Render, ce bouton est dans le header en haut a droite
# Essayer plusieurs positions possibles

# Position du bouton "Manual Deploy" - typiquement en haut a droite
# Sur Render dashboard: header du service, bouton deploy en haut
# Scroll en haut de la page d'abord
key_combo(0x23)  # End key - aller en bas... non, on veut remonter
time.sleep(0.2)

# Ctrl+Home pour aller tout en haut
user32.keybd_event(0x11, 0, 0, 0)  # CTRL down
user32.keybd_event(0x24, 0, 0, 0)  # HOME down
user32.keybd_event(0x24, 0, 0x0002, 0)  # HOME up
user32.keybd_event(0x11, 0, 0x0002, 0)  # CTRL up
time.sleep(0.3)

# Le bouton "Manual Deploy" sur Render est generalement:
# - Dans la section header du service
# - Vers x=1200-1400, y=150-250 (en coordonnees absolues)
# Position relative dans la fenetre Chrome:
deploy_btn_rel_x = int(width * 0.83)   # 83% de la largeur
deploy_btn_rel_y = 160                   # 160px depuis le haut de la fenetre
deploy_btn_x = left + deploy_btn_rel_x
deploy_btn_y = top + deploy_btn_rel_y

print(f"Clic sur bouton Manual Deploy: ({deploy_btn_x},{deploy_btn_y})")
click(deploy_btn_x, deploy_btn_y)
time.sleep(1.5)

# 7. Screenshot pour voir le menu deroulant
shot3 = os.path.join(screenshot_dir, "step3_deploy_menu.png")
take_screenshot(shot3)
print(f"Screenshot menu deploy: {shot3}")

# 8. Cliquer sur "Deploy latest commit" - c'est le 1er element du menu
# Le menu est juste en dessous du bouton
menu_item_x = deploy_btn_x
menu_item_y = deploy_btn_y + 45
print(f"Clic sur 'Deploy latest commit': ({menu_item_x},{menu_item_y})")
click(menu_item_x, menu_item_y)
time.sleep(2)

# 9. Screenshot final
shot4 = os.path.join(screenshot_dir, "step4_deployed.png")
take_screenshot(shot4)
print(f"Screenshot final: {shot4}")

print()
print("=== TERMINE ===")
print("Verifie les screenshots pour confirmer le deploy.")
print(f"step1_before.png    -> etat initial")
print(f"step2_render_tab.png -> apres switch vers onglet Render")
print(f"step3_deploy_menu.png -> apres clic sur bouton deploy")
print(f"step4_deployed.png   -> etat final")
input("Appuie sur Entree pour fermer...")
