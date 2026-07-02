@echo off
title Render Deploy v2
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === DEPLOY RENDER v2 ===
echo Fermeture fenetres + maximisation Chrome automatique
echo.
timeout /t 2 /nobreak >nul
python render_deploy2.py
if %errorlevel% neq 0 py render_deploy2.py
pause
