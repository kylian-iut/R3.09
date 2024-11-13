import socket

host='localhost'
port=80

client_socket = socket.socket()
client_socket.settimeout(5)

def echange():
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print(f"\033[31mLa connexion au serveur a été refusée!\033[0m")
        retr='yes'
        retr=input("Voulez-vous réessayer ? y/n [yes]: ")
        if retr == 'n':
            exit()
        else:
            echange()
            return
    except OSError:
        print(f"\033[31mSocket déjà instancié!\033[0m")
        return
    while True:
        try:
            reply = client_socket.recv(1024).decode()
            if reply == "ack":
                print("Le serveur a reçu le message")
            elif reply == "bye":
                client_socket.close()
                break
        except ConnectionResetError:
            print(f"\033[31mLa connexion au serveur a été perdue!\033[0m")
            retr='yes'
            retr=input("Voulez-vous reconnecter ? y/n [yes]: ")
            if retr == 'n':
                exit()
            else:
                echange()
                return
        except TimeoutError:
            print(f"\033[31mLa connexion au serveur a échoué!\033[0m")
            retr='yes'
            retr=input("Voulez-vous reconnecter ? y/n [yes]: ")
            if retr == 'n':
                exit()
            else:
                echange()
                return
        message=""
        while message=="":
            message=input("Entrez votre message: ")
        client_socket.send(message.encode())
echange()
