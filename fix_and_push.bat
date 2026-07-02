@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === FIX LOCK + PUSH SW 5.0 ===

echo Arret des processus git en cours...
taskkill /f /im git.exe >nul 2>&1
timeout /t 1 >nul

echo Suppression du verrou...
if exist ".git\index.lock" (
    del /f /q ".git\index.lock"
    echo Verrou supprime.
) else (
    echo Aucun verrou.
)

echo Commit + Push...
git add CoachFinancier.html
git commit -m "Fix: renderScore null guard scoreLabel + SW 5.0"
git push origin master
if %errorlevel% neq 0 (
    git push origin HEAD:main
)

echo.
echo === SUCCES - Attends 2min puis Ctrl+Shift+R ===
pause
