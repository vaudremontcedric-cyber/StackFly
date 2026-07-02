import ctypes, time
u = ctypes.windll.user32

def click(x, y):
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.3)
    u.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.15)
    u.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.5)

# Fermer popup eventuel
u.keybd_event(0x1B, 0, 0, 0)
time.sleep(0.05)
u.keybd_event(0x1B, 0, 0x0002, 0)
time.sleep(0.5)

# Clic sur "Manual Deploy" (bouton haut droite Render dashboard)
print("Clic Manual Deploy...")
click(1325, 282)
time.sleep(2.5)

# Screenshot pour voir le menu
import subprocess
subprocess.run(['powershell', '-Command',
    'Add-Type -AssemblyName System.Windows.Forms; $s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $b=New-Object System.Drawing.Bitmap($s.Width,$s.Height); $g=[System.Drawing.Graphics]::FromImage($b); $g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size); $b.Save(\'C:\\\\Users\\\\vaudr\\\\Claude\\\\Projects\\\\application budget\\\\click_step1.png\'); $g.Dispose(); $b.Dispose()'],
    capture_output=True, timeout=10)
print("Screenshot pris: click_step1.png")

# Clic "Deploy latest commit" (premier item du dropdown)
print("Clic Deploy latest commit...")
click(1325, 330)
time.sleep(3)

subprocess.run(['powershell', '-Command',
    'Add-Type -AssemblyName System.Windows.Forms; $s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $b=New-Object System.Drawing.Bitmap($s.Width,$s.Height); $g=[System.Drawing.Graphics]::FromImage($b); $g.CopyFromScreen($s.Location,[System.Drawing.Point]::Empty,$s.Size); $b.Save(\'C:\\\\Users\\\\vaudr\\\\Claude\\\\Projects\\\\application budget\\\\click_step2.png\'); $g.Dispose(); $b.Dispose()'],
    capture_output=True, timeout=10)
print("Screenshot pris: click_step2.png")
print("DONE")
