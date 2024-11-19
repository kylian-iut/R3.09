import socket
import threading
import os

host = 'localhost'
port = 80

def ecoute(client_socket):
    try:
        reply = client_socket.recv(1024).decode()
        if not reply:
            return
        print(f"\033[92m{reply}\033[0m")
        
        if reply == "bye":
            print("\033[93mLe serveur ferme la connexion\033[0m")
            client_socket.close()
            return "bye"
        elif reply == "arret":
            print("\033[93mLe serveur va s'arrêter\033[0m")
            reply = "bye"
            try:
                client_socket.send(reply.encode())
            except OSError:
                return
        else:
            reply = ""
            try:
                client_socket.send(reply.encode())
            except OSError:
                return
    except ConnectionResetError:
        print(f"\033[31mLa connexion au serveur a été perdue!\033[0m")
        retr = input("Voulez-vous reconnecter ? y/n [yes]: ").strip().lower()
        if retr == 'n':
            client_socket.close()
            return
        else:
            echange()
            return
    except TimeoutError:
        print(f"\033[31mLa connexion au serveur a échoué!\033[0m")
        retr = input("Voulez-vous reconnecter ? y/n [yes]: ").strip().lower()
        if retr == 'n':
            client_socket.close()
            return
        else:
            echange()
            return

def envoie_fichier(client_socket, file_path):
    if not os.path.exists(file_path):
        print(f"\033[31mLe fichier {file_path} n'existe pas.\033[0m")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    print(f"{file_name} : {file_size}")

    try:
        client_socket.send("file".encode())
        print("j'attend réponse fichier")
        client_socket.recv(1024)

        client_socket.send(file_name.encode())
        print("j'attend réponse nom fichier")
        client_socket.recv(1024)

        client_socket.send(str(file_size).encode()) 
        print("j'attend réponse taille fichier")
        client_socket.recv(1024)
        print("on commence le transfert du fichier")
        with open(file_path, "rb") as file:
            while chunk := file.read(1024):
                client_socket.send(chunk)

        print("\033[92mFichier envoyé avec succès.\033[0m")
    except Exception as err:
        print(f"\033[31mErreur lors de l'envoi du fichier : {err}\033[0m")

def envoie(client_socket):
    while True:
        message = ""
        while message == "":
            try:
                message = input()
            except EOFError:
                return
        if message.startswith("fichier:"):
            file_path = message.split(":", 1)[1].strip()
            envoie_fichier(client_socket, file_path)
        else:
            try:
                client_socket.send(message.encode())
                ecoute(client_socket)
            except (ConnectionResetError, OSError):
                print(f"\033[31mLe serveur a fermé la connexion!\033[0m")
                client_socket.close()
                return

def echange():
    client_socket = socket.socket()
    client_socket.settimeout(1)
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print(f"\033[31mLa connexion au serveur a été refusée!\033[0m")
        retr = input("Voulez-vous réessayer ? y/n [yes]: ").strip().lower()
        if retr == 'n':
            client_socket.close()
            return
        else:
            echange()
            return
    except OSError:
        print(f"\033[31mSocket déjà instancié!\033[0m")
        client_socket.close()
        return
    else:
        t1 = threading.Thread(target=envoie, args=[client_socket])
        t1.start()
        t1.join()

while True:
    cond = input("Voulez-vous vous connecter au serveur localhost ? y/n [yes]: ")
    if cond != 'n':
        echange()
    else:
        exit()