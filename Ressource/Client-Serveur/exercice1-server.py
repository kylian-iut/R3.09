import socket

port=80


def ecoute():
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)
    print("J'attend une conenxion...")
    conn, address = server_socket.accept()
    print(f"\033[93mConnexion acceptée pour {address}\033[0m")
    reply = "ack"
    conn.send(reply.encode())
    while True:
        print("J'attend le client...")
        message = conn.recv(1024).decode()
        print(f"Le message reçu est: \033[92m {message} \033[0m")
        print("Je confirme la réception")
        if message == "bye":
            print("\033[93mJe ferme la connexion\033[0m")
            reply = "bye"
            conn.send(reply.encode())
            conn.close() 
            server_socket.close()
            break
        else:
            reply = "ack"
            conn.send(reply.encode())

while True:
    ecoute()