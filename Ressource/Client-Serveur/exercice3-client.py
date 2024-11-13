import socket
import threading

host='localhost'
port=80

def ecoute(client_socket):
    while True:
        try:
            reply = client_socket.recv(1024).decode()
            print(f"\033[92m{reply}\033[0m")
            if reply == "bye":
                print("\033[93mLe serveur ferme la connexion\033[0m")
                client_socket.close()
                break
            elif reply == "arret":
                print("\033[93mLe serveur s'arrête\033[0m")
                client_socket.close()
                break
            else:
                reply = ""
                try:
                    client_socket.send(reply.encode())
                except OSError:
                    return
        except ConnectionResetError:
            print(f"\033[31mLa connexion au serveur a été perdue!\033[0m")
            retr='yes'
            retr=input("Voulez-vous reconnecter ? y/n [yes]: ")
            if retr == 'n':
                client_socket.close()
                return
            else:
                echange()
                return
        except TimeoutError:
            print(f"\033[31mLa connexion au serveur a échoué!\033[0m")
            retr='yes'
            retr=input("Voulez-vous reconnecter ? y/n [yes]: ")
            if retr == 'n':
                client_socket.close()
                return
            else:
                echange()
                return

def envoie(client_socket):
    while True:
        message=""
        while message=="":
            try:
                message=input()
            except EOFError:
                return
        try:
            client_socket.send(message.encode())
        except ConnectionResetError:
            print(f"\033[31mLe serveur a fermé la connexion!\033[0m")
            client_socket.close()
            return
        except OSError:
            return

def echange():
    client_socket = socket.socket()
    client_socket.settimeout(300)
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print(f"\033[31mLa connexion au serveur a été refusée!\033[0m")
        retr='yes'
        retr=input("Voulez-vous réessayer ? y/n [yes]: ")
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
        t1 = threading.Thread(target=ecoute, args=[client_socket])
        t2 = threading.Thread(target=envoie, args=[client_socket])
        t1.start()
        t2.start()
        t1.join()

while True:
    cond="yes"
    print("")
    cond=input("Voulez-vous vous connecter au serveur localhost ? y/n [yes]: ")
    if cond != 'n':
        echange()
    else:
        exit()