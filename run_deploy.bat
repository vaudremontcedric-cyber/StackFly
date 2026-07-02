@echo off
title Render Deploy Automation
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === LANCEMENT DU DEPLOY RENDER ===
echo.
echo Ce script va automatiquement cliquer dans Chrome pour declencher
echo le deploy de la v5.0 sur Render.com
echo.
echo IMPORTANT: Ne touche pas la souris pendant l'execution !
echo.
timeout /t 3 /nobreak >nul
python render_deploy.py
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Python n'est pas accessible. Essai avec py...
    py render_deploy.py
)
pause
