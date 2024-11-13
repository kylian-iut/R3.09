import socket
import threading

port = 80
clients = []

def session():
    global shutdown_event
    server_socket = socket.socket()
    try:
        server_socket.bind(('0.0.0.0', port))
    except OSError:
        print(f"\033[31mLe port {port} est déjà ouvert!\033[0m")
        server_socket.close()
        return
    server_socket.listen()
    print("Serveur démarré et en attente de connexions...")

    while not shutdown_event.is_set():
        conn, address = server_socket.accept()
        print(f"\033[93mConnexion acceptée pour {address}\033[0m")
        clients.append(conn)
        t = threading.Thread(target=newclient, args=(conn, address))
        t.start()

def broadcast(message, sender_conn, address=None):
    for client in clients:
        if client != sender_conn:
            try:
                if address != None:
                    message=f"Message reçu de {address} : {message}"
                client.send(message.encode())
            except BrokenPipeError:
                print("Impossible d'envoyer à un client déconnecté")

def newclient(conn, address):
    reply = "ack"
    conn.send(reply.encode())
    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"\033[31mLa connexion avec {address} a été perdue.\033[0m")
            break
        except UnicodeDecodeError:
            reply = "err"
            conn.send(reply.encode())
            continue

        print(f"Message reçu de {address} : \033[92m{message}\033[0m")

        if message == "bye":
            print(f"\033[93mFermeture de la connexion avec {address}\033[0m")
            conn.send("bye".encode())
            break
        elif message == "arret":
            print("\033[93mArrêt du serveur\033[0m")
            conn.send("bye".encode())
            broadcast("arret", conn)
            shutdown_event.set()
            break
        else:
            broadcast(message, conn, address)
            conn.send("ack".encode())

    conn.close()
    clients.remove(conn)

while True:
    cond = input("Voulez-vous démarrer le serveur localhost ? y/n [yes]: ")
    if cond != 'n':
        shutdown_event = threading.Event()
        session()
    else:
        exit()
