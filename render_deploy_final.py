import ctypes
import ctypes.wintypes
import subprocess
import time
import sys

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

RENDER_URL = "https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0"

def find_chrome_hwnd():
    hwnds = []
    def callback(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                class_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buf, 256)
                cls = class_buf.value
                if cls == "Chrome_WidgetWin_1" and length > 3:
                    hwnds.append((hwnd, title))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    cb = WNDENUMPROC(callback)
    user32.EnumWindows(cb, 0)
    # prefer window with Render in title, else pick largest title
    for hwnd, title in hwnds:
        if "Render" in title or "StackFly" in title:
            return hwnd
    if hwnds:
        return hwnds[0][0]
    return None

def open_render():
    # Step 1: Open URL in Chrome via start command
    subprocess.Popen(['cmd', '/c', 'start', 'chrome', '--new-tab', RENDER_URL],
                     creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(4)

    # Step 2: Find Chrome and bring to front
    hwnd = find_chrome_hwnd()
    if not hwnd:
        print("Chrome not found!")
        return False

    # Step 3: Bring Chrome to foreground
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    time.sleep(1)

    # Step 4: Navigate to Render dashboard via Ctrl+L
    # Press Ctrl+L to focus address bar
    VK_CONTROL = 0x11
    VK_L = 0x4C
    KEYEVENTF_KEYUP = 0x0002

    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_L, 0, 0, 0)
    time.sleep(0.1)
    user32.keybd_event(VK_L, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.5)

    # Select all and type URL
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(0x41, 0, 0, 0)  # Ctrl+A
    time.sleep(0.1)
    user32.keybd_event(0x41, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)

    # Type URL using clipboard
    import subprocess as sp
    clip = f'echo {RENDER_URL}| clip'
    sp.run(clip, shell=True)
    time.sleep(0.3)

    # Paste
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(0x56, 0, 0, 0)  # Ctrl+V
    time.sleep(0.1)
    user32.keybd_event(0x56, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.3)

    # Press Enter
    user32.keybd_event(0x0D, 0, 0, 0)
    time.sleep(0.1)
    user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)

    print(f"Navigated Chrome to: {RENDER_URL}")
    print("Please click 'Manual Deploy' on the Render dashboard.")
    return True

if __name__ == "__main__":
    open_render()
