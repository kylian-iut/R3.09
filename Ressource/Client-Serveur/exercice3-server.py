import socket
import threading

port=80
shutdown_event = threading.Event()

def ecoute():
    global shutdown_event
    server_socket = socket.socket()
    try:
        server_socket.bind(('0.0.0.0', port))
    except OSError:
        print(f"\033[31mLe port {port} est déjà ouvert!\033[0m")
        server_socket.close()
        return
    server_socket.listen(1)
    while not shutdown_event.is_set():  # Le serveur continue tant que l'Event n'est pas déclenché
        print("J'attend une conenxion...")
        conn, address = server_socket.accept()
        t1 = threading.Thread(target=newclient, args=[conn, address, server_socket])
        t1.start()

def newclient(conn, address, server_socket):
    print(f"\033[93mConnexion acceptée pour {address}\033[0m")
    reply = "ack"
    conn.send(reply.encode())
    while True:
        print("J'attend le client...")
        try:
            message = conn.recv(1024).decode()
        except ConnectionResetError:
            print(f"\033[31mLe client a fermé la connexion!\033[0m")
            conn.close() 
            return
        except ConnectionAbortedError:
            print(f"\033[31mLa communication du client a été interrompu!\033[0m")
            conn.close() 
            return
        except UnicodeDecodeError:
            print(f"\033[93mLe client a envoyé des caractères non UTF-8!\033[0m")
            reply = "err"
            conn.send(reply.encode())
        else:
            print(f"Le message reçu est: \033[92m {message} \033[0m")
            print("Je confirme la réception")
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
                shutdown_event.set()
                return
            else:
                reply = "ack"
                conn.send(reply.encode())

while True:
    cond="yes"
    print("")
    cond=input("Voulez-vous vous démarrer le serveur localhost ? y/n [yes]: ")
    if cond != 'n':
        ecoute()
    else:
        exit()