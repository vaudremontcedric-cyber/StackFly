import ctypes
import ctypes.wintypes
import subprocess
import time

user32 = ctypes.windll.user32

# Step 1: Kill stale CMD windows that might block our click
subprocess.run(['taskkill', '/F', '/IM', 'cmd.exe'],
               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
time.sleep(0.5)

# Step 2: Find Chrome window with Render dashboard and bring to front
hwnds = []
def enum_cb(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if cls_buf.value == 'Chrome_WidgetWin_1':
                hwnds.append((hwnd, buf.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)

# Find Render/StackFly Chrome window
chrome_hwnd = None
for hwnd, title in hwnds:
    if 'StackFly' in title or 'Render' in title or 'dashboard' in title.lower():
        chrome_hwnd = hwnd
        print(f"Found Chrome: {title}")
        break
if not chrome_hwnd and hwnds:
    chrome_hwnd = hwnds[0][0]
    print(f"Using first Chrome: {hwnds[0][1]}")

# Step 3: Restore Chrome to foreground
if chrome_hwnd:
    user32.ShowWindow(chrome_hwnd, 9)  # SW_RESTORE
    time.sleep(0.3)
    user32.SetForegroundWindow(chrome_hwnd)
    time.sleep(0.5)

# Step 4: Click "Manual Deploy" at screen coordinates
x, y = 1315, 281
print(f"Clicking 'Manual Deploy' at ({x}, {y})")

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004

user32.SetCursorPos(x, y)
time.sleep(0.3)
user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.1)
user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
print("Clicked 'Manual Deploy'!")

time.sleep(1.2)

# Step 5: Click first dropdown option "Deploy latest commit"
x2, y2 = 1255, 325
user32.SetCursorPos(x2, y2)
time.sleep(0.3)
user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.1)
user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
print(f"Clicked dropdown option at ({x2}, {y2})")
print("Deploy triggered!")
