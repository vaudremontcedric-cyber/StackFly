@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === SUPPRESSION TOUS LES LOCKS ===
taskkill /f /im git.exe >nul 2>&1
timeout /t 2 >nul
del /f /q ".git\index.lock" 2>nul
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\config.lock" 2>nul
del /f /q ".git\packed-refs.lock" 2>nul
for /f "delims=" %%i in ('dir /b /s ".git\*.lock" 2^>nul') do del /f /q "%%i" 2>nul
echo Locks supprimes.
echo.
echo === COMMIT ===
git add CoachFinancier.html serve.js package.json
git commit -m "Fix: restore serve.js + package.json + SW 5.0"
echo.
echo === PUSH ===
git push origin master
if %errorlevel% neq 0 git push origin HEAD:main
echo.
echo === DONE ===
pause
