@echo off
title Render Deploy v4
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
timeout /t 2 /nobreak >nul
python render_deploy4.py
if %errorlevel% neq 0 py render_deploy4.py
pause
