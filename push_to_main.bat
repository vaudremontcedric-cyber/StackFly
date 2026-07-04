@echo off
cd /d "C:\Users\vaudr\Claude\Projects\application budget\coach-financier"

echo === Suppression des locks git ===
del /f "..\\.git\\index.lock" 2>nul
del /f "..\\.git\\HEAD.lock" 2>nul

echo === Commit v5.5 ===
git add -A
git commit -m "v5.6 - modal confirm/prompt natifs remplacés + bouton supprimer items 50/30/20 + modal versement objectif + fix saveActif + fix calcul epargne"

echo === Push vers master ===
git push origin master

echo === Push vers main (pour Render) ===
git push origin master:main

echo.
echo === DONE — ouvre Render et clique Manual Deploy ===
pause
