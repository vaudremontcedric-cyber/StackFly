Set-Location "C:\Users\vaudr\Claude\Projects\application budget"
Write-Host "=== SUPPRESSION LOCKS ==="
Stop-Process -Name "git" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-ChildItem ".git" -Filter "*.lock" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "Locks supprimes."
Write-Host ""
Write-Host "=== COMMIT ==="
git add CoachFinancier.html serve.js package.json
git commit -m "Fix: restore serve.js + package.json + SW 5.0"
Write-Host ""
Write-Host "=== PUSH ==="
git push origin master
Write-Host ""
Write-Host "=== DONE ==="
Read-Host "Appuie sur Entree pour fermer"
