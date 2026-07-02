@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget"

echo === Configuration Git ===
git init
git config user.email "vaudremontcedric@gmail.com"
git config user.name "vaudremontcedric-cyber"
git add CoachFinancier.html serve.js package.json
git commit -m "Fix: bottom sheet 3 options + Gemini 2.5 Flash + SW v3"
git remote remove origin 2>nul
git remote add origin https://github.com/vaudremontcedric-cyber/StackFly.git
echo.
echo === Push vers GitHub ===
echo (GitHub va demander ton nom d'utilisateur et mot de passe / token)
git push --force origin HEAD:main
echo.
echo === Termine ! Render redeploie dans 1-2 minutes ===
pause
