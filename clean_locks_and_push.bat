@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"
echo === Suppression TOUS les locks git ===
del /f ".git\index.lock" 2>nul
del /f ".git\HEAD.lock" 2>nul
del /f ".git\COMMIT_EDITMSG.lock" 2>nul
del /f ".git\refs\heads\master.lock" 2>nul
del /f ".git\refs\heads\main.lock" 2>nul
echo Locks supprimes.
echo === Git status ===
git status
echo === Git add + commit ===
git add "coach-financier\CoachFinancier.html"
git commit -m "v5.2: Firebase cloud sync + fix receiptModal + multi-device"
echo === Push GitHub ===
git push origin master
if %errorlevel% neq 0 git push origin HEAD:main
echo.
echo === DONE ===
pause
