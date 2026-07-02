@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === GIT BASH FIX ===
taskkill /f /im git.exe >nul 2>&1
timeout /t 2 >nul
"C:\Program Files\Git\bin\bash.exe" -c "cd '/c/Users/vaudr/Claude/Projects/application budget' && rm -f .git/index.lock .git/HEAD.lock .git/config.lock && git add CoachFinancier.html serve.js package.json && git commit -m 'Fix: restore serve.js + package.json + SW 5.0' && git push origin master && echo PUSH_OK"
echo.
echo === FIN ===
pause
