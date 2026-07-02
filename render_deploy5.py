"""
Script v5 - Identification precise de Chrome browser (vs Cowork).
Cherche la fenetre avec '- Google Chrome' dans le titre.
Ouvre un nouvel onglet Render, clique Manual Deploy.
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

def ctrl_key(vk):
    key_down(0x11)  # CTRL
    press_key(vk)
    key_up(0x11)
    time.sleep(0.3)

def type_via_clipboard(text):
    ps = f'Set-Clipboard -Value @"\n{text}\n"@'
    subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{text}"'],
                   capture_output=True, timeout=5)
    time.sleep(0.3)
    ctrl_key(0x41)  # Ctrl+A
    time.sleep(0.1)
    ctrl_key(0x56)  # Ctrl+V
    time.sleep(0.3)

def press_enter():
    press_key(0x0D)

def press_escape():
    press_key(0x1B)
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

def find_chrome_browser():
    """Trouve le vrai navigateur Chrome (pas Cowork)."""
    results = []
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            title = buf.value
            # Chrome browser a toujours "- Google Chrome" dans son titre
            if cls.value == 'Chrome_WidgetWin_1' and '- Google Chrome' in title:
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 600 and h > 400:
                    results.append((hwnd, title, w * h))
        return True
    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(cb(callback), 0)
    if results:
        # Prendre la plus grande fenetre
        results.sort(key=lambda x: x[2], reverse=True)
        return results[0][0], results[0][1]
    return None, None

base_dir = r"C:\Users\vaudr\Claude\Projects\application budget"

print("=== RENDER DEPLOY v5 ===")

hwnd, title = find_chrome_browser()
if not hwnd:
    # Ouvrir Chrome si pas trouve
    print("Chrome non trouve, ouverture...")
    subprocess.Popen(['start', 'chrome'], shell=True)
    time.sleep(3)
    hwnd, title = find_chrome_browser()
    if not hwnd:
        print("ERREUR: Chrome introuvable!")
        sys.exit(1)

print(f"Chrome trouve: hwnd={hwnd}, titre='{title[:70]}'")

# Obtenir position Chrome
rect = ctypes.wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
print(f"Position: ({rect.left},{rect.top}) -> ({rect.right},{rect.bottom})")

# Mettre Chrome au premier plan
user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(0.8)

# Screenshot initial
take_screenshot(os.path.join(base_dir, "v5_step1_chrome.png"))
print("Screenshot v5_step1 pris")

# Ouvrir nouvel onglet et naviguer vers Render dashboard
print("\nOuverture nouvel onglet Render...")
ctrl_key(0x54)  # Ctrl+T - nouvel onglet
time.sleep(0.5)

# Taper l'URL
render_url = "https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0"
subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{render_url}"'],
               capture_output=True, timeout=5)
time.sleep(0.3)
ctrl_key(0x56)  # Ctrl+V pour coller l'URL
time.sleep(0.3)
press_enter()
print(f"Navigation vers: {render_url}")
time.sleep(5)  # Attendre chargement page

take_screenshot(os.path.join(base_dir, "v5_step2_render.png"))
print("Screenshot v5_step2 pris")

# Fermer popup eventuel avec Escape
press_escape()
time.sleep(0.5)
# Clic dans zone neutre pour fermer popup
click(700, 450)
time.sleep(0.5)

# Scroller en haut
ctrl_key(0x24)  # Ctrl+Home
time.sleep(0.3)

# Cliquer sur "Manual Deploy" - bouton en haut a droite
# Sur ecran 1456px de large, le bouton est a droite ~x=1315, y=235
manual_x = 1315
manual_y = 235
print(f"\nClic 'Manual Deploy': ({manual_x},{manual_y})")
click(manual_x, manual_y)
time.sleep(1.5)

take_screenshot(os.path.join(base_dir, "v5_step3_menu.png"))
print("Screenshot v5_step3 pris")

# Clic sur "Deploy latest commit" dans le dropdown
# Il apparait juste sous le bouton, ~45px plus bas
deploy_x = manual_x
deploy_y = manual_y + 45
print(f"Clic 'Deploy latest commit': ({deploy_x},{deploy_y})")
click(deploy_x, deploy_y)
time.sleep(3)

take_screenshot(os.path.join(base_dir, "v5_step4_deploying.png"))
print("Screenshot v5_step4 pris")

print("\n=== TERMINE ===")
print("Le deploy devrait etre en cours.")
print("Verifier: https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0")
