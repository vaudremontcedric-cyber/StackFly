"""
Ouvre CoachFinancier.html dans Chrome via Windows start
"""
import subprocess
import time

# Windows "start" command ouvre le fichier dans le navigateur par defaut
url = "file:///C:/Users/vaudr/Claude/Projects/application%20budget/CoachFinancier.html"
subprocess.Popen(['cmd', '/c', 'start', '', url])
time.sleep(4)
print("=== Fichier ouvert ===")
