import socket
import threading
import os
import argparse
import signal
import subprocess

port=8000
max_client=2
clients = {}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
shutdown_event = threading.Event()

def execute(file, conn):
    """
        Fonction qui permet de détecter le langage du script, puis de l'executer et d'envoyer le résultat
    """
    ext = os.path.splitext(file)[-1]
    status=None
    try:
        if ext == ".py":
            print(f"\033[93mScript python va être executé\033[0m")
            result = subprocess.run(["python", file], capture_output=True, text=True, check=True)
        elif ext == ".c":
            print(f"\033[93mScript C va être executé\033[0m")
            executable = os.path.splitext(file)[0]
            subprocess.run(["gcc", file, "-o", executable], capture_output=True, text=True, check=True)
            if os.name == "nt":  # Si sous Windows
                executable += ".exe"
            print(executable)
            result = subprocess.run([executable], capture_output=True, text=True, check=True)
        elif ext == ".cpp":
            print(f"\033[93mScript C++ va être executé\033[0m")
            executable = os.path.splitext(file)[0]
            subprocess.run(["g++", file, "-o", executable], capture_output=True, text=True, check=True)
            if os.name == "nt":  # Si sous Windows
                executable += ".exe"
            result = subprocess.run([executable], capture_output=True, text=True, check=True)
        elif ext == ".java":
            print(f"\033[93mScript Java va être executé\033[0m")
            classname = os.path.basename(file).replace(".java", "")
            subprocess.run(["javac", file], capture_output=True, text=True, check=True)
            result = subprocess.run(["java", "-cp", os.path.dirname(file), classname], capture_output=True, text=True, check=True)
        else:
            print(f"\033[93mScript ne peut pas être executé\033[0m")
            status = "err:lang"
    except subprocess.CalledProcessError as err:
        error_details=f"{err.stderr}"
        print(error_details)
        conn.send('stderr'.encode())
        conn.send(error_details.encode('utf-8'))

    except Exception as err:
        error_details=f"Erreur inattendue : {err}"
        print(error_details)
        conn.send('othererr'.encode())
        conn.send(error_details.encode())
    else:
        if not status:
            print("Sortie standard :")
            print(result.stdout)
            conn.send('stdout'.encode())
            conn.send(result.stdout.encode())
    finally:
        if not status:
            print(f"\033[92mExecution de '{os.path.basename(file)}' terminée avec succès.\033[0m")
            return
        else:
            return status

def handle_sigint(signal, frame):
    """
        Méthode qui permet d'arrêter le serveur avec le signal lié à CTRL+C
    """
    print(f"\033[31mLe serveur s'arrête.\033[0m")
    shutdown_event.set()

def session():
    """
        Méthode qui établie la connexion avec le Client
    """
    global clients
    global max_client
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
                if len(clients) < max_client:
                    print(f"\033[93mConnexion acceptée pour {address}\033[0m")
                    clients[conn]=[]
                    print(clients)
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
    """
        Méthode de nettoyage qui supprime les fichiers uploadés avant l'arrêt
    """   
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
    """
        Méthode qui traite les commandes du client
    """
    global clients
    try:
        conn.send("ack".encode())
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
                conn.send("ack".encode())
            elif data == "ok":
                if len(clients[conn]) > 0:
                    file=clients[conn][0]
                    state=execute(os.path.join(UPLOAD_DIR, file),conn)
                    try:
                        result = conn.recv(1024).decode()
                    except ConnectionResetError:
                        print(f"\033[31mLa connexion au client a été perdue!\033[0m")
                        return
                    if result == 'ack':
                        if not state:
                            try:
                                conn.send("bye".encode())
                                print(f"\033[93mFermeture de la connexion avec {address}\033[0m")
                            except ConnectionResetError:
                                print(f"\033[31mLa connexion au client a été perdue!\033[0m")
                                return
                        else:
                            print(state)
                            conn.send(state.encode())
                else:
                    conn.send("ack".encode())
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
            del clients[conn]

def receive_file(conn, address):
    """
        Méthode qui permet de réceptionner le contenu d'un script puis de le sauvegarder dans un fichier dans le dossier uploads
    """
    global clients
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
        clients[conn].append(file_name)
        conn.send("fichier reçu".encode())
    except Exception as e:
        print(f"\033[31mErreur lors de la réception du fichier : {e}\033[0m")
        conn.send("erreur lors de la réception".encode())

def main():
    """
        Méthode qui permet d'obtenir les instructions nécéssaire à l'initialisation du serveur
    """
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