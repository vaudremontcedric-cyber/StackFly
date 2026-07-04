import ctypes
import ctypes.wintypes
import time
import json

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# --- DPI awareness ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI
except:
    pass

# Screen metrics
screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)

# Find Chrome RescueBudget
hwnds = []
def enum_cb(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if cls_buf.value == 'Chrome_WidgetWin_1' and 'RescueBudget' in buf.value:
                hwnds.append((hwnd, buf.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
cb = WNDENUMPROC(enum_cb)
user32.EnumWindows(cb, 0)

result = {
    "screen": f"{screen_w}x{screen_h}",
    "chrome_found": bool(hwnds),
}

if hwnds:
    hwnd = hwnds[0][0]
    user32.ShowWindow(hwnd, 3)
    time.sleep(0.3)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)

    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    crect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(crect))

    # Centre de la fenetre (coordonnees ecran)
    cx = rect.left + w // 2
    cy = rect.top + h // 2

    result["window"] = f"{rect.left},{rect.top} -> {rect.right},{rect.bottom}"
    result["window_size"] = f"{w}x{h}"
    result["client_size"] = f"{crect.right}x{crect.bottom}"
    result["center"] = f"{cx},{cy}"
    result["title"] = hwnds[0][1]

    # Chercher les DPI de la fenetre
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        result["dpi"] = dpi
        result["scale"] = round(dpi / 96.0, 2)
    except:
        result["dpi"] = "unknown"

output_path = r"C:\Users\vaudr\Claude\Projects\application budget\calibrate_result.json"
with open(output_path, "w") as f:
    json.dump(result, f, indent=2)

print("OK:", json.dumps(result, indent=2))
