@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"

echo ========================================
echo   DEPLOIEMENT RESCUEBUDGET v5.0
echo ========================================
echo.

echo Suppression du verrou git si present...
if exist ".git\index.lock" (
    del /f ".git\index.lock"
    echo Verrou supprime.
) else (
    echo Aucun verrou.
)
echo.

echo [1/3] Ajout du fichier...
git add CoachFinancier.html
if %errorlevel% neq 0 ( echo ERREUR git add & pause & exit )

echo [2/3] Commit...
git commit -m "Fix: renderScore null guard scoreLabel + SW 5.0"
if %errorlevel% neq 0 ( echo ERREUR git commit & pause & exit )

echo [3/3] Push vers GitHub...
git push origin master
if %errorlevel% neq 0 (
  echo Essai avec HEAD:main...
  git push origin HEAD:main
)

echo.
echo ========================================
echo   SUCCES ! Render redeploie dans 1-2min
echo   Ensuite : Ctrl+Shift+R sur le site
echo ========================================
pause
