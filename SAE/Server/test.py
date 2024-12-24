import os
import subprocess

# Vérifie si gcc est accessible
try:
    result = subprocess.run(["gcc", "--version"], capture_output=True, text=True, check=True)
    print("GCC version:", result.stdout)
except FileNotFoundError:
    print("gcc n'est pas trouvé.")
except subprocess.CalledProcessError as e:
    print(f"Erreur d'exécution : {e}")
