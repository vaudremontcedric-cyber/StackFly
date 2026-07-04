"""
Ouvre CoachFinancier.html via os.startfile (plus fiable sur Windows)
"""
import os
import time

path = r"C:\Users\vaudr\Claude\Projects\application budget\CoachFinancier.html"
print(f"Ouverture: {path}")
os.startfile(path)
time.sleep(4)
print("=== Done ===")
