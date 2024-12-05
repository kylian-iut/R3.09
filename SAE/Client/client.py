import socket
import sys
import threading
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QWidget,
    QComboBox,
    QGridLayout,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)

host = 'localhost'
port = 80

files=["file1.py","main.py","file2.py","file2.py","file2.py","file2.py","file2.py","file2.py","file2.py","file2.py","file2.py","file2.py"]

def ecoute(client_socket):
    try:
        reply = client_socket.recv(1024).decode()
        if not reply:
            return
        print(f"\033[92m{reply}\033[0m")
        
        if reply == "bye":
            print("\033[93mConnexion avec le serveur terminée\033[0m")
            client_socket.close()
            return "bye"
        elif reply == "arret":
            print("\033[93mLe serveur va s'arrêter\033[0m")
            reply = "bye"
            try:
                client_socket.send(reply.encode())
            except OSError:
                return
        elif reply == "occuped":
            print("\033[93mLe serveur est occupé\033[0m")
            client_socket.close()
            return "occuped"
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
    if not os.path.isfile(file_path):
        print(f"\033[31mLa cible {file_path} n'est pas un fichier.\033[0m")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    print(f"{file_name} : {file_size} octets")

    try:
        client_socket.send("file".encode())
        client_socket.recv(1024)

        client_socket.send(file_name.encode())
        client_socket.recv(1024)

        client_socket.send(str(file_size).encode()) 
        client_socket.recv(1024)
        print("Téléversement...")
        with open(file_path, "rb") as file:
            while chunk := file.read(1024):
                client_socket.send(chunk)
        print("\033[92mFichier envoyé avec succès.\033[0m")
        client_socket.recv(1024)
    except Exception as err:
        print(f"\033[31mErreur lors de l'envoi du fichier : {err}\033[0m")

def envoie(client_socket):
    if ecoute(client_socket) == 'occuped':
        return
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
                if ecoute(client_socket) == 'bye':
                    return
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
        try:
            print(f"\033[31mServeur injoignable!\033[0m")
            client_socket.close()
            return
        except KeyboardInterrupt:
            print(f"\033[31mConnexion annulée!\033[0m")
            client_socket.close()
            return
    else:
        t1 = threading.Thread(target=envoie, args=[client_socket])
        t1.start()
        try:
            t1.join()
        except KeyboardInterrupt:
            client_socket.send("bye".encode())
            ecoute(client_socket)
            client_socket.close()
            return

class MainWindow(QMainWindow):
    def __init__(self):
        global files
        super().__init__()
        self.setWindowTitle("Client SAE3.02")
        self.setFixedSize(550, 330)
        layout = QGridLayout()
        
        self.stacklayout = QStackedLayout()

        self.listWidget = QListWidget(self)
        self.listWidget.resize(700, 700)
        self.listWidget.setStyleSheet("QListWidget { font-size: 18px; }")
        self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for file in files:
            newItem = QListWidgetItem()
            newItem.setText(file)
            self.listWidget.insertItem(-1, newItem)
        layout.addWidget(self.listWidget,0,0,10,4)
        
        label = QLabel("Serveur")
        layout.addWidget(label,10,0)

        self.serv = QLineEdit()
        layout.addWidget(self.serv,10,1)

        self.T1label = QLabel("Port")
        layout.addWidget(self.T1label,10,2)
        
        self.port = QLineEdit()
        layout.addWidget(self.port,10,3,1,2)
        
        btn_help = QPushButton("?")
        btn_help.pressed.connect(self.help)
        layout.addWidget(btn_help,10,5)

        btn_quit = QPushButton("Quitter")
        btn_quit.pressed.connect(self.close)
        layout.addWidget(btn_quit,0,4,1,2)
        
        btn_import = QPushButton("Importer")
        btn_import.pressed.connect(self.importe)
        layout.addWidget(btn_import,1,4,1,2)

        btn_edit = QPushButton("Editer")
        btn_edit.pressed.connect(self.edit)
        layout.addWidget(btn_edit,2,4,1,2)

        btn_new = QPushButton("Nouveau")
        btn_new.pressed.connect(self.new)
        layout.addWidget(btn_new,3,4,1,2)

        btn_rename = QPushButton("Renommer")
        btn_rename.pressed.connect(self.rename)
        layout.addWidget(btn_rename,4,4,1,2)

        btn_suppr = QPushButton("Supprimer")
        btn_suppr.pressed.connect(self.suppr)
        layout.addWidget(btn_suppr,5,4,1,2)

        btn_upload = QPushButton("Téléverser")
        btn_upload.pressed.connect(self.upload)
        btn_upload.setFixedHeight(btn_upload.sizeHint().height() * 4)
        layout.addWidget(btn_upload,6,4,4,2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def importe(self):
        return
    
    def importe(self):
        return
    
    def edit(self):
        return
    
    def new(self):
        return
    
    def rename(self):
        return
    
    def suppr(self):
        return
    
    def upload(self):
        return
    
    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("Erreur")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
    def help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Aide")
        msg.setText("Importez des fichiers, puis sélectionnez le fichier ciblé pour effectuer une action dessus sur la droite. Si vous choisissez Téléverser, le fichier sélectionné sera le script principal")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()