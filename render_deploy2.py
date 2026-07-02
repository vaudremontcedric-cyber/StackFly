"""
Script v2 - Corrige les coordonnees en fermant d'abord toutes les fenetres
qui couvrent Chrome, puis maximise Chrome et clique au bon endroit.
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
SW_MINIMIZE  = 6
SW_MAXIMIZE  = 3
SW_RESTORE   = 9

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.2)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)

def get_all_windows():
    windows = []
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if buf.value:
                windows.append((hwnd, buf.value, cls.value))
        return True
    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(cb(callback), 0)
    return windows

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

print("=== RENDER DEPLOY v2 ===")

# 1. Trouver toutes les fenetres
all_windows = get_all_windows()
chrome_hwnd = None

for hwnd, title, cls in all_windows:
    if cls == 'Chrome_WidgetWin_1' and user32.IsWindowVisible(hwnd):
        # Prendre la fenetre Chrome principale (celle avec la barre de titre)
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        if w > 800 and h > 400:  # Fenetre principale, pas les popups
            chrome_hwnd = hwnd
            print(f"Chrome: hwnd={hwnd}, titre='{title[:50]}', taille={w}x{h}")

if not chrome_hwnd:
    print("ERREUR: Chrome non trouve!")
    input("Entree...")
    sys.exit(1)

# 2. Minimiser toutes les autres fenetres visibles (sauf Chrome)
print("\nMinimisation des autres fenetres...")
for hwnd, title, cls in all_windows:
    if hwnd != chrome_hwnd and cls not in ('Shell_TrayWnd', 'WorkerW', 'Progman'):
        try:
            user32.ShowWindow(hwnd, SW_MINIMIZE)
        except:
            pass

time.sleep(0.5)

# 3. Maximiser et mettre Chrome au premier plan
print("Maximisation de Chrome...")
user32.ShowWindow(chrome_hwnd, SW_MAXIMIZE)
time.sleep(0.3)
user32.SetForegroundWindow(chrome_hwnd)
time.sleep(0.8)

# 4. Obtenir la position apres maximisation
rect = ctypes.wintypes.RECT()
user32.GetWindowRect(chrome_hwnd, ctypes.byref(rect))
left = rect.left
top = rect.top
right = rect.right
bottom = rect.bottom
w = right - left
h = bottom - top
print(f"Chrome maximise: ({left},{top}) -> ({right},{bottom}), taille={w}x{h}")

# Screenshot de base
base_dir = r"C:\Users\vaudr\Claude\Projects\application budget"
shot_before = os.path.join(base_dir, "v2_step1_before.png")
take_screenshot(shot_before)
print(f"Screenshot: {shot_before}")

# 5. Calculer les coordonnees Chrome (maximise, shadow=-7)
# En mode maximise Windows 10/11:
# - La fenetre depot a (-7,-7) mais le contenu visible commence a (0,0)
# - La barre de titre Chrome est a y=0 (masquee car maximisee)
# - Les onglets Chrome sont a y_screen ~ 5 a 35
# - y_screen = y_window - 7 (puisque left/top = -7)
# Donc: y_window = y_screen + 7

# Pour les onglets (dans la fenetre Chrome maximisee):
# Tab bar height: ~35px. Les tabs centraux sont a y_screen~20 => y_win=27
# Avec 3 tabs visibles sur ~1456px de large:
#   Tab 1: x ~ 0-220 => centre x_screen=110 => x_win=117
#   Tab 2: x ~ 220-430 => centre x_screen=325 => x_win=332
#   Tab 3: x ~ 430-640 => centre x_screen=535 => x_win=542
# Bouton + (nouveau tab): x_screen~650

# Coordonnees onglet Render (3eme onglet):
tab3_screen_x = 535
tab3_screen_y = 22
tab3_win_x = tab3_screen_x - left  # left = -7 => tab3_win_x = 542
tab3_win_y = tab3_screen_y - top   # top = -7  => tab3_win_y = 29

# En coordonnees ecran absolues:
tab3_abs_x = left + tab3_win_x  # = -7 + 542 = 535
tab3_abs_y = top + tab3_win_y   # = -7 + 29 = 22

print(f"\nClic onglet Render: screen=({tab3_abs_x},{tab3_abs_y})")
click(tab3_abs_x, tab3_abs_y)
time.sleep(3)

shot_tab = os.path.join(base_dir, "v2_step2_tab.png")
take_screenshot(shot_tab)
print(f"Screenshot: {shot_tab}")

# 6. Sur le dashboard Render, le bouton "Manual Deploy" est dans le header
# Apres la barre tabs + adresse + toolbar, le contenu commence vers y_screen=140
# Le header Render (nom du service) est vers y_screen=150-200
# Le bouton "Manual Deploy" est a DROITE du header, vers x_screen=1280-1370
# et y_screen=170-200

# Coordonnees du bouton Manual Deploy:
deploy_btn_screen_x = 1300
deploy_btn_screen_y = 185
print(f"\nClic bouton 'Manual Deploy': screen=({deploy_btn_screen_x},{deploy_btn_screen_y})")
click(deploy_btn_screen_x, deploy_btn_screen_y)
time.sleep(1.5)

shot_menu = os.path.join(base_dir, "v2_step3_menu.png")
take_screenshot(shot_menu)
print(f"Screenshot: {shot_menu}")

# 7. Dans le menu deroulant, "Deploy latest commit" est le 1er element
# Il apparait directement sous le bouton
deploy_item_screen_x = deploy_btn_screen_x
deploy_item_screen_y = deploy_btn_screen_y + 45
print(f"\nClic 'Deploy latest commit': screen=({deploy_item_screen_x},{deploy_item_screen_y})")
click(deploy_item_screen_x, deploy_item_screen_y)
time.sleep(2)

shot_final = os.path.join(base_dir, "v2_step4_final.png")
take_screenshot(shot_final)
print(f"Screenshot: {shot_final}")

print("\n=== TERMINE ===")
print("Verifie les screenshots v2_step*.png")
input("Appuie sur Entree pour fermer...")
