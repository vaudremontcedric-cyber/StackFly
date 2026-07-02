"""
Script v6 - Minimise Cowork avant de cliquer Chrome.
Solution au problème : Cowork volait le focus.
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
SW_MINIMIZE = 6
SW_RESTORE  = 9
SW_MAXIMIZE = 3

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

def get_title(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(128)
    user32.GetClassNameW(hwnd, buf, 128)
    return buf.value

def get_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.2)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.4)

def press_key(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.1)

def ctrl_key(vk):
    user32.keybd_event(0x11, 0, 0, 0)  # CTRL down
    press_key(vk)
    user32.keybd_event(0x11, 0, KEYEVENTF_KEYUP, 0)  # CTRL up
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

def find_all_chrome_windows():
    results = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            cls = get_class(hwnd)
            if cls == 'Chrome_WidgetWin_1':
                title = get_title(hwnd)
                rect = get_rect(hwnd)
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 400 and h > 300:
                    results.append({'hwnd': hwnd, 'title': title, 'w': w, 'h': h})
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return results

base_dir = r"C:\Users\vaudr\Claude\Projects\application budget"

print("=== RENDER DEPLOY v6 (Minimize Cowork) ===")

# 1. Trouver toutes les fenetres Chrome_WidgetWin_1
all_wins = find_all_chrome_windows()
print(f"Fenetres Chrome_WidgetWin_1 trouvees: {len(all_wins)}")
for w in all_wins:
    print(f"  hwnd={w['hwnd']} title='{w['title'][:80]}' size={w['w']}x{w['h']}")

# 2. Séparer Chrome navigateur vs Cowork
cowork_hwnds = []
chrome_hwnd = None
chrome_size = 0

for w in all_wins:
    title = w['title']
    hwnd = w['hwnd']
    if '- Google Chrome' in title:
        size = w['w'] * w['h']
        if size > chrome_size:
            chrome_hwnd = hwnd
            chrome_size = size
            chrome_title = title
    else:
        # C'est probablement Cowork ou un autre app Electron
        cowork_hwnds.append(hwnd)
        print(f"  => Cowork/Electron: hwnd={hwnd} '{title[:60]}'")

# 3. Minimiser TOUS les non-Chrome fenetres pour libérer le focus
print(f"\nMinimisation de {len(cowork_hwnds)} fenetre(s) Cowork/Electron...")
for hwnd in cowork_hwnds:
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    time.sleep(0.2)
    print(f"  Minimise: hwnd={hwnd}")

time.sleep(0.8)

# 4. Ouvrir Chrome si pas trouve
if not chrome_hwnd:
    print("Chrome non trouve, ouverture...")
    subprocess.Popen(['start', 'chrome'], shell=True)
    time.sleep(4)
    all_wins2 = find_all_chrome_windows()
    for w in all_wins2:
        if '- Google Chrome' in w['title']:
            size = w['w'] * w['h']
            if size > chrome_size:
                chrome_hwnd = w['hwnd']
                chrome_size = size
                chrome_title = w['title']
    if not chrome_hwnd:
        print("ERREUR: Chrome introuvable!")
        sys.exit(1)

print(f"\nChrome: hwnd={chrome_hwnd}, titre='{chrome_title[:80]}'")

# 5. Amener Chrome au premier plan
user32.ShowWindow(chrome_hwnd, SW_MAXIMIZE)
time.sleep(0.5)
result = user32.SetForegroundWindow(chrome_hwnd)
print(f"SetForegroundWindow result: {result}")
time.sleep(1.0)

# Screenshot pour vérifier
take_screenshot(os.path.join(base_dir, "v6_step1_chrome.png"))

# 6. Ouvrir un nouvel onglet Chrome et naviguer vers Render
render_url = "https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0"
print(f"\nNavigation vers: {render_url}")

# Coller l'URL dans la barre d'adresse
subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{render_url}"'],
               capture_output=True, timeout=5)
time.sleep(0.3)

# Ctrl+T pour nouvel onglet
ctrl_key(0x54)
time.sleep(0.8)

# Ctrl+V + Enter pour naviguer
ctrl_key(0x56)
time.sleep(0.3)
press_key(0x0D)  # Enter
print("URL envoyée, attente chargement page (8s)...")
time.sleep(8)

take_screenshot(os.path.join(base_dir, "v6_step2_render.png"))

# 7. Fermer popup eventuel
press_key(0x1B)  # Escape
time.sleep(0.5)

# 8. Cliquer sur "Manual Deploy"
# Sur écran 1456px, bouton en haut à droite ~x=1315, y=235
manual_x = 1315
manual_y = 235
print(f"\nClic 'Manual Deploy': ({manual_x},{manual_y})")
click(manual_x, manual_y)
time.sleep(1.5)

take_screenshot(os.path.join(base_dir, "v6_step3_menu.png"))

# 9. Clic "Deploy latest commit"
deploy_x = 1315
deploy_y = 280
print(f"Clic 'Deploy latest commit': ({deploy_x},{deploy_y})")
click(deploy_x, deploy_y)
time.sleep(3)

take_screenshot(os.path.join(base_dir, "v6_step4_deploying.png"))

# 10. Restaurer les fenetres Cowork
print("\nRestauration des fenetres Cowork...")
for hwnd in cowork_hwnds:
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.3)

print("\n=== TERMINE ===")
print(f"Deploy déclenché pour: {render_url}")
print("Vérifier v6_step*.png pour confirmation")
