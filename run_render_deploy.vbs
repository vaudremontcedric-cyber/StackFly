Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Users\vaudr\Claude\Projects\application budget\trigger_render_deploy.ps1""", 0, False
