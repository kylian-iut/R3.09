import socket
import threading
import os
import argparse
import signal
import time

port=80
clients = []
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
shutdown_event = threading.Event()

def handle_sigint(signal, frame):
    print(f"\033[31mLe serveur s'arrête.\033[0m")
    shutdown_event.set()

def session():
    global clients
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind(('0.0.0.0', port))
    except OSError:
        print(f"\033[31mLe port {port} est déjà ouvert!\033[0m")
        server_socket.close()
        return
    server_socket.listen()
    server_socket.settimeout(1)
    print("Serveur démarré et en attente de connexions...")

    try:
        while not shutdown_event.is_set():
            try:
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
            except socket.timeout:
                continue
    finally:
        server_socket.close()
        for client in clients:
            client.close()
        print("\033[92mServeur arrêté proprement.\033[0m")
        cleanup_files()
 
def cleanup_files():   
    try:
        files = os.listdir(UPLOAD_DIR)
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("Tous les fichiers ont été supprimés avec succès.")
    except OSError as err:
        print(f"Erreur lors de la suppression des fichiers : {err}")

def newclient(conn, address):
    try:
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
            except KeyboardInterrupt:
                print(f"\033[31mLe serveur s'arrête.\033[0m")
            
            if data == "file":
                receive_file(conn, address)
            elif data == "bye":
                print(f"\033[93mFermeture de la connexion avec {address}\033[0m")
                conn.send("bye".encode())
                break
            else:
                print(f"Instruction inconnue reçu de {address} : \033[92m{data}\033[0m")
                conn.send("instruction inconnue".encode())
    finally:
        conn.close()
        if conn in clients:
            clients.remove(conn)

def receive_file(conn, address): 
    try:
        conn.send("ack".encode())
        print(f"Réception d'un fichier...")
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--port',type=int,required=False,help="Spécifiez le port à utiliser.")
    args = parser.parse_args()
    if args.port != None:
        port = args.port
    
    signal.signal(signal.SIGINT, handle_sigint)
    
    session()


if __name__ == "__main__":
    main()