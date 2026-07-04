# Minimize Cowork first, then navigate Chrome to Render dashboard
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
}
"@

$RENDER_URL = "https://dashboard.render.com/web/srv-d8qnpbvavr4c73djols0"

# Find all top-level windows
$windows = @()
$callback = [Win32+EnumWindowsProc]{
    param($hwnd, $lParam)
    if ([Win32]::IsWindowVisible($hwnd)) {
        $titleBuf = New-Object System.Text.StringBuilder 256
        [Win32]::GetWindowText($hwnd, $titleBuf, 256) | Out-Null
        $title = $titleBuf.ToString()
        $classBuf = New-Object System.Text.StringBuilder 256
        [Win32]::GetClassName($hwnd, $classBuf, 256) | Out-Null
        $class = $classBuf.ToString()
        if ($title.Length -gt 0) {
            $script:windows += [PSCustomObject]@{ HWND = $hwnd; Title = $title; Class = $class }
        }
    }
    return $true
}
[Win32]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

Write-Host "Found windows:"
$windows | ForEach-Object { Write-Host "  [$($_.Class)] $($_.Title)" }

# Find Cowork/Claude window and minimize it
$coworkWin = $windows | Where-Object { $_.Title -match "Claude|Cowork" -and $_.Class -ne "Chrome_WidgetWin_1" } | Select-Object -First 1
if ($coworkWin) {
    Write-Host "Minimizing Cowork: $($coworkWin.Title)"
    [Win32]::ShowWindow($coworkWin.HWND, 6) | Out-Null  # SW_MINIMIZE
    Start-Sleep -Milliseconds 500
}

# Open Render URL in Chrome
Write-Host "Opening Render dashboard..."
Start-Process "chrome.exe" "--new-tab $RENDER_URL"
Start-Sleep -Seconds 3

# Find Chrome window
$chromeWin = $windows | Where-Object { $_.Class -eq "Chrome_WidgetWin_1" } | Select-Object -First 1
if ($chromeWin) {
    Write-Host "Focusing Chrome: $($chromeWin.Title)"
    [Win32]::ShowWindow($chromeWin.HWND, 9) | Out-Null  # SW_RESTORE
    Start-Sleep -Milliseconds 300
    [Win32]::SetForegroundWindow($chromeWin.HWND) | Out-Null
    Start-Sleep -Milliseconds 500

    # Use SendKeys to type in address bar
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait("^l")
    Start-Sleep -Milliseconds 400
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    Start-Sleep -Milliseconds 200

    # Set clipboard and paste
    [System.Windows.Forms.Clipboard]::SetText($RENDER_URL)
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Write-Host "Navigated to Render dashboard."
} else {
    Write-Host "Chrome not found!"
}

Write-Host "Done. Please click 'Manual Deploy' button on the Render dashboard."
