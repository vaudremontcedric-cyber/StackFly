"""
deploy_v7.py - Click Manual Deploy on Render dashboard already open in Chrome.
Uses aggressive focus management with retries.
"""
import ctypes, ctypes.wintypes, time, subprocess, sys, os

user32 = ctypes.windll.user32
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

def get_title(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(128)
    user32.GetClassNameW(hwnd, buf, 128)
    return buf.value

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.3)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.15)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.5)

def screenshot(path):
    ps = f"""Add-Type -AssemblyName System.Windows.Forms
$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$b=New-Object System.Drawing.Bitmap($s.Width,$s.Height)
$g=[System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size)
$b.Save('{path}')
$g.Dispose(); $b.Dispose()"""
    subprocess.run(['powershell','-Command',ps], capture_output=True, timeout=10)

def all_windows():
    wins = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            cls = get_class(hwnd)
            if cls == 'Chrome_WidgetWin_1':
                t = get_title(hwnd)
                r = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                w, h = r.right-r.left, r.bottom-r.top
                if w > 400 and h > 300:
                    wins.append({'hwnd': hwnd, 'title': t, 'w': w, 'h': h})
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return wins

base = r"C:\Users\vaudr\Claude\Projects\application budget"

# Find all Chrome_WidgetWin_1 windows
all_wins = all_windows()
print(f"Found {len(all_wins)} Chrome_WidgetWin_1 windows:")
for w in all_wins:
    print(f"  {w['hwnd']}: '{w['title'][:80]}'")

# Separate Chrome browser from Cowork
chrome_hwnd = None
cowork_hwnds = []
for w in all_wins:
    if '- Google Chrome' in w['title']:
        if chrome_hwnd is None or w['w']*w['h'] > 0:
            chrome_hwnd = w['hwnd']
            chrome_title = w['title']
    else:
        cowork_hwnds.append(w['hwnd'])

if not chrome_hwnd:
    print("Chrome not found! Opening...")
    subprocess.Popen(['start', 'chrome', 'https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0'], shell=True)
    time.sleep(5)
    all_wins = all_windows()
    for w in all_wins:
        if '- Google Chrome' in w['title']:
            chrome_hwnd = w['hwnd']
            chrome_title = w['title']

print(f"\nChrome: {chrome_hwnd} '{chrome_title[:80]}'")
print(f"Minimizing {len(cowork_hwnds)} Cowork windows...")

# Aggressively minimize all non-Chrome windows
for hwnd in cowork_hwnds:
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    time.sleep(0.3)

# Wait for animations to complete
time.sleep(1.5)

# Bring Chrome to top AGGRESSIVELY
user32.ShowWindow(chrome_hwnd, SW_MAXIMIZE)
time.sleep(0.5)
# Attach our thread to Chrome's input queue for reliable SetForegroundWindow
tid_chrome = user32.GetWindowThreadProcessId(chrome_hwnd, None)
tid_self = ctypes.windll.kernel32.GetCurrentThreadId()
user32.AttachThreadInput(tid_self, tid_chrome, True)
user32.BringWindowToTop(chrome_hwnd)
user32.SetForegroundWindow(chrome_hwnd)
user32.SetFocus(chrome_hwnd)
user32.AttachThreadInput(tid_self, tid_chrome, False)
time.sleep(1.0)

screenshot(os.path.join(base, "v7_step1_chrome.png"))
print("Screenshot v7_step1 taken")

# Scroll to top of page to ensure button is visible
user32.SetCursorPos(728, 400)
time.sleep(0.2)
# Ctrl+Home to scroll to top
user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
time.sleep(0.05)
user32.keybd_event(0x24, 0, 0, 0)  # Home down
time.sleep(0.05)
user32.keybd_event(0x24, 0, 0x0002, 0)  # Home up
time.sleep(0.05)
user32.keybd_event(0x11, 0, 0x0002, 0)  # Ctrl up
time.sleep(0.5)

# "Manual Deploy" button is at ~x=1314, y=282 on 1456px wide screen
manual_x, manual_y = 1314, 282
print(f"Clicking Manual Deploy at ({manual_x}, {manual_y})...")
click(manual_x, manual_y)
time.sleep(2.0)

screenshot(os.path.join(base, "v7_step2_menu.png"))
print("Screenshot v7_step2 taken")

# "Deploy latest commit" appears in dropdown ~35px below
deploy_x, deploy_y = 1314, 317
print(f"Clicking Deploy latest commit at ({deploy_x}, {deploy_y})...")
click(deploy_x, deploy_y)
time.sleep(3.0)

screenshot(os.path.join(base, "v7_step3_done.png"))
print("Screenshot v7_step3 taken")

# Restore Cowork
print("Restoring Cowork windows...")
for hwnd in cowork_hwnds:
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.3)

print("\n=== DONE ===")
print("Check v7_step*.png for verification")
