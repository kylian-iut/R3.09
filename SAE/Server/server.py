import socket
import threading
import os
import argparse

port=80
clients = []
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def session():
    global shutdown_event
    global clients
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
        if len(clients) == 0:
            print(f"\033[93mConnexion acceptée pour {address}\033[0m")
            clients.append(conn)
            t = threading.Thread(target=newclient, args=(conn, address))
            t.start()
        else:
            print(f"\033[93mConnexion refusé pour {address}\033[0m")
            reply = "occuped"
            conn.send(reply.encode())
            conn.close()

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
            data = conn.recv(1024).decode()
            if not data:
                break
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"\033[31mLa connexion avec {address} a été perdue.\033[0m")
            break
        except UnicodeDecodeError:
            reply = "err"
            conn.send(reply.encode())
            continue
        
        if data == "file":
            conn.send("ack".encode())
            print(f"Réception d'un fichier...")
            receive_file(conn, address)
        elif data == "bye":
            print(f"\033[93mFermeture de la connexion avec {address}\033[0m")
            conn.send("bye".encode())
            break
        else:  # 🟦 Traitement des messages texte
            print(f"Message reçu de {address} : \033[92m{data}\033[0m")
            broadcast(data, conn, address)
            conn.send("ack".encode())
            
    conn.close()
    clients.remove(conn)

def receive_file(conn, address): 
    try:
        file_name = conn.recv(1024).decode()
        conn.send("ack".encode())
        print(f"Réception du fichier '{file_name}' de {address}")

        file_size = int(conn.recv(1024).decode())
        conn.send("ack".encode())
        print(f"Taille du fichier : {file_size} octets")

        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as file:
            bytes_received = 0
            while bytes_received < file_size:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                file.write(chunk)
                bytes_received += len(chunk)
        
        print(f"\033[92mFichier '{file_name}' reçu avec succès ({bytes_received} octets).\033[0m")
        conn.send("fichier reçu".encode())
    except Exception as e:
        print(f"\033[31mErreur lors de la réception du fichier : {e}\033[0m")
        conn.send("erreur lors de la réception".encode())

def main():
    global port
    global shutdown_event
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--port',type=int,required=False,help="Spécifiez le port à utiliser.")
    args = parser.parse_args()
    if args.port != None:
        port = args.port
    while True:
        cond = input("Voulez-vous démarrer le serveur localhost ? y/n [yes]: ")
        if cond != 'n':
            shutdown_event = threading.Event()
            session()
        else:
            exit()


if __name__ == "__main__":
    main()