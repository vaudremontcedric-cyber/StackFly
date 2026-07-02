"""
deploy_v8 - Navigate Chrome to Render, then click Manual Deploy.
Navigates via address bar to ensure we're on the right page.
"""
import ctypes, ctypes.wintypes, time, subprocess, sys, os

user32 = ctypes.windll.user32
SW_MINIMIZE = 6
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

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.3)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.15)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.5)

def key_down(vk): user32.keybd_event(vk, 0, 0, 0)
def key_up(vk):   user32.keybd_event(vk, 0, 0x0002, 0)

def key(vk):
    key_down(vk); time.sleep(0.05); key_up(vk); time.sleep(0.1)

def ctrl(vk):
    key_down(0x11); key(vk); key_up(0x11); time.sleep(0.3)

def screenshot(path):
    ps = f"""Add-Type -AssemblyName System.Windows.Forms
$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$b=New-Object System.Drawing.Bitmap($s.Width,$s.Height)
$g=[System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size)
$b.Save('{path}')
$g.Dispose(); $b.Dispose()"""
    subprocess.run(['powershell','-Command',ps], capture_output=True, timeout=10)

def all_chrome():
    wins = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            if get_class(hwnd) == 'Chrome_WidgetWin_1':
                t = get_title(hwnd)
                r = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                w, h = r.right-r.left, r.bottom-r.top
                if w > 400 and h > 300:
                    wins.append({'hwnd': hwnd, 'title': t})
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return wins

def focus_chrome(hwnd):
    tid_ch = user32.GetWindowThreadProcessId(hwnd, None)
    tid_me = ctypes.windll.kernel32.GetCurrentThreadId()
    user32.AttachThreadInput(tid_me, tid_ch, True)
    user32.ShowWindow(hwnd, SW_MAXIMIZE)
    time.sleep(0.3)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetFocus(hwnd)
    user32.AttachThreadInput(tid_me, tid_ch, False)
    time.sleep(1.2)

base = r"C:\Users\vaudr\Claude\Projects\application budget"
render_url = "https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0"

# Find Chrome
wins = all_chrome()
chrome_hwnd = None
cowork_hwnds = []
for w in wins:
    if '- Google Chrome' in w['title']:
        chrome_hwnd = w['hwnd']
        print(f"Chrome: {w['hwnd']} '{w['title'][:70]}'")
    else:
        cowork_hwnds.append(w['hwnd'])
        print(f"Cowork: {w['hwnd']} '{w['title'][:70]}'")

if not chrome_hwnd:
    print("Chrome not found, launching...")
    subprocess.Popen(['start', 'chrome'], shell=True)
    time.sleep(4)
    wins = all_chrome()
    for w in wins:
        if '- Google Chrome' in w['title']:
            chrome_hwnd = w['hwnd']

# Minimize Cowork
for hwnd in cowork_hwnds:
    user32.ShowWindow(hwnd, SW_MINIMIZE)
time.sleep(1.0)

# Focus Chrome
focus_chrome(chrome_hwnd)
screenshot(os.path.join(base, "v8_s1_focused.png"))

# Navigate to Render via address bar
subprocess.run(['powershell', '-Command', f'Set-Clipboard -Value "{render_url}"'], capture_output=True, timeout=5)
time.sleep(0.3)

ctrl(0x4C)   # Ctrl+L - focus address bar
time.sleep(0.5)
ctrl(0x41)   # Ctrl+A - select all
time.sleep(0.2)
ctrl(0x56)   # Ctrl+V - paste URL
time.sleep(0.3)
key(0x0D)    # Enter
print("Navigating to Render... waiting 10s")
time.sleep(10)

screenshot(os.path.join(base, "v8_s2_render.png"))
key(0x1B)   # Escape - close any popup
time.sleep(0.5)

# Click Manual Deploy button - top right area
# Button is at ~x=1314, y=282 on maximized window
manual_x, manual_y = 1314, 282
print(f"Clicking Manual Deploy at ({manual_x},{manual_y})")
click(manual_x, manual_y)
time.sleep(2.5)

screenshot(os.path.join(base, "v8_s3_menu.png"))

# Deploy latest commit - first item in dropdown, ~35px lower
deploy_x, deploy_y = 1314, 317
print(f"Clicking Deploy latest commit at ({deploy_x},{deploy_y})")
click(deploy_x, deploy_y)
time.sleep(4)

screenshot(os.path.join(base, "v8_s4_result.png"))

# Restore Cowork
for hwnd in cowork_hwnds:
    user32.ShowWindow(hwnd, SW_MAXIMIZE)
    time.sleep(0.3)

print("=== DONE - check v8_s*.png ===")
