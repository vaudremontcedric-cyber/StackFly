"""
Script final - Lance Chrome directement avec l'URL Render, puis clique.
Copie a C:\deploy.py pour eviter les problemes de chemin avec espaces.
"""
import ctypes, ctypes.wintypes, time, subprocess, sys, os

user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
KEYEVENTF_KEYUP      = 0x0002

def click(x, y):
    user32.SetCursorPos(int(x), int(y)); time.sleep(0.2)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0); time.sleep(0.3)

def kdown(vk): user32.keybd_event(vk, 0, 0, 0)
def kup(vk):   user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
def key(vk):   kdown(vk); time.sleep(0.05); kup(vk); time.sleep(0.1)
def ctrl(vk):  kdown(0x11); key(vk); kup(0x11); time.sleep(0.3)
def escape():  key(0x1B); time.sleep(0.3)

def screenshot(path):
    ps = f'Add-Type -AssemblyName System.Windows.Forms; $s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $b=New-Object System.Drawing.Bitmap($s.Width,$s.Height); $g=[System.Drawing.Graphics]::FromImage($b); $g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size); $b.Save(\'{path}\'); $g.Dispose(); $b.Dispose()'
    subprocess.run(['powershell','-Command',ps], capture_output=True, timeout=10)

def find_render_chrome():
    """Cherche une fenetre Chrome avec 'Render' ou 'StackFly' dans le titre."""
    found = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            t = buf.value
            if cls.value == 'Chrome_WidgetWin_1' and ('Render' in t or 'StackFly' in t):
                r = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                w, h = r.right-r.left, r.bottom-r.top
                if w > 600 and h > 400:
                    found.append((hwnd, t, w*h))
        return True
    f = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(f(cb), 0)
    if found:
        found.sort(key=lambda x: x[2], reverse=True)
        return found[0][0], found[0][1]
    return None, None

base = r"C:\Users\vaudr\Claude\Projects\application budget"
render_url = "https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0"

print("=== DEPLOY FINAL ===")

# 1. Ouvrir Chrome avec l'URL Render
chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
chrome_exe = next((p for p in chrome_paths if os.path.exists(p)), None)

if chrome_exe:
    print(f"Ouverture Chrome: {render_url}")
    subprocess.Popen([chrome_exe, '--new-window', render_url])
    time.sleep(5)
else:
    print("chrome.exe non trouve, essai via start...")
    subprocess.Popen(f'start chrome "{render_url}"', shell=True)
    time.sleep(5)

screenshot(os.path.join(base, "final_step1.png"))

# 2. Trouver la fenetre Chrome avec 'Render'
print("Recherche fenetre Render Chrome...")
for attempt in range(5):
    hwnd, title = find_render_chrome()
    if hwnd:
        print(f"Trouve: hwnd={hwnd}, titre='{title[:60]}'")
        break
    print(f"Attente... ({attempt+1}/5)")
    time.sleep(2)

if not hwnd:
    print("ERREUR: Fenetre Render non trouvee!")
    screenshot(os.path.join(base, "final_error.png"))
    sys.exit(1)

# 3. Mettre au premier plan et maximiser
user32.ShowWindow(hwnd, 3)
time.sleep(0.5)
user32.SetForegroundWindow(hwnd)
time.sleep(1.0)

screenshot(os.path.join(base, "final_step2.png"))

# 4. Attendre chargement complet
print("Attente chargement Render...")
time.sleep(4)

# 5. Fermer popup eventuel
escape()
time.sleep(0.3)
click(700, 400)
time.sleep(0.5)
ctrl(0x24)  # Ctrl+Home
time.sleep(0.3)

screenshot(os.path.join(base, "final_step3_before_click.png"))

# 6. Clic sur "Manual Deploy" (haut droite, ~x=1315, y=235)
print("Clic Manual Deploy...")
click(1315, 235)
time.sleep(2.0)

screenshot(os.path.join(base, "final_step4_menu.png"))

# 7. Clic "Deploy latest commit" (dropdown, ~45px sous le bouton)
print("Clic Deploy latest commit...")
click(1315, 280)
time.sleep(3)

screenshot(os.path.join(base, "final_step5_done.png"))

print("=== TERMINE! Verifier final_step*.png ===")
