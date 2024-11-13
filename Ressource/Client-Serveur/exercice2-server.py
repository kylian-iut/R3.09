import socket
import threading
port=8000
stay=True

def ecoute(conn,server_socket):
    global stay
    while True:
        try:
            message = conn.recv(1024).decode()
        except ConnectionResetError:
            print(f"\033[31mLe client a fermé la connexion!\033[0m")
            conn.close() 
            return
        except ConnectionAbortedError:
            conn.close() 
            return
        else:
            print(f"\033[92m{message}\033[0m")
            if message == "bye":
                print("\033[93mLe client ferme la connexion\033[0m")
                reply = "bye"
                conn.send(reply.encode())
                conn.close() 
                server_socket.close()
                return
            elif message == "arret":
                print("\033[93mLe client a arrêté le serveur\033[0m")
                reply = "arret"
                conn.send(reply.encode())
                conn.close() 
                server_socket.close()
                stay=False
                return
            else:
                reply = ""
                try:
                    conn.send(reply.encode())
                except OSError:
                    return True

def envoie(conn,server_socket):
    while True:
        try:
            message = input()
        except EOFError:
            return
        if message == "bye":
            print("\033[93mJe ferme la connexion\033[0m")
            reply = "bye"
            conn.send(reply.encode())
            conn.close() 
            server_socket.close()
            break
        elif message == "arret":
            print("\033[93mJ'arrête le serveur\033[0m")
            reply = "arret"
            conn.send(reply.encode())
            conn.close() 
            server_socket.close()
            return
        else:
            try:
                conn.send(message.encode())
            except OSError:
                return


def session():
    global stay
    while stay:
        server_socket = socket.socket()
        try:
            server_socket.bind(('0.0.0.0', port))
        except OSError:
            print(f"\033[31mLe port {port} est déjà ouvert!\033[0m")
            server_socket.close()
            return
        server_socket.listen(1)
        print("J'attend une conenxion...")
        conn, address = server_socket.accept()
        print(f"\033[93mConnexion acceptée pour {address}\033[0m")
        reply = "ack"
        conn.send(reply.encode())
        t1 = threading.Thread(target=ecoute, args=[conn,server_socket])
        t2 = threading.Thread(target=envoie, args=[conn,server_socket])
        t1.start()
        t2.start()
        t1.join()

while True:
    cond="yes"
    print("")
    cond=input("Voulez-vous vous démarrer le serveur localhost ? y/n [yes]: ")
    if cond != 'n':
        session()
    else:
        exit()