@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === PUSH UNIQUEMENT (commit deja pret) ===
git log --oneline -2
echo.
git push origin master
if %errorlevel% neq 0 (
    git push origin HEAD:main
)
echo.
echo === SUCCES - Attends 2min puis Ctrl+Shift+R ===
pause
