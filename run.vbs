Set WshShell = CreateObject("WScript.Shell")
' Etape 1: Push GitHub
WshShell.Run "cmd /c ""C:\Users\vaudr\Claude\Projects\application budget\push_only.bat""", 1, True
' Etape 2: Deploy Render (minimise Cowork d'abord)
WshShell.Run "python ""C:\Users\vaudr\Claude\Projects\application budget\render_deploy6.py""", 1, True
