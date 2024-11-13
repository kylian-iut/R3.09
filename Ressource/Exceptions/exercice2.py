file = "texte.txt"

try:
    with open(file, 'r') as fichier:
        lignes = fichier.readlines()
    lignes = [ligne.strip() for ligne in lignes]
except FileNotFoundError or FileExistsError:
    print("Le fichier spécifié est introuvable!")
except PermissionError or IOError:
    print("Vous n'avez pas la permission d'ouvrir le fichier spécifié!")
else:
    print(lignes)
finally:
    print("Le programme est terminé.")
