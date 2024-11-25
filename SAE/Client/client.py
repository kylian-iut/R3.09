import socket
import sys
import threading
import os

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
)

host = 'localhost'
port = 80

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
        super().__init__()
        self.setWindowTitle("Client SAE3.02")
        self.resize(350, 150)
        layout = QGridLayout()
        
        self.stacklayout = QStackedLayout()

        label = QLabel("Température")
        layout.addWidget(label,0,0)

        self.champ = QLineEdit()
        layout.addWidget(self.champ,0,1)

        self.T1label = QLabel("°C")
        layout.addWidget(self.T1label,0,2)

        btn = QPushButton("Convertir")
        btn.pressed.connect(self.convert_temperature)
        layout.addWidget(btn,1,1)
        
        self.combobox = QComboBox(self)
        self.combobox.addItem("°C -> K")
        self.combobox.addItem("K -> °C")
        self.combobox.currentIndexChanged.connect(self.update_labels)
        layout.addWidget(self.combobox,1,2)

        label = QLabel("Conversion")
        layout.addWidget(label,2,0)

        self.sortie = QLineEdit()
        self.sortie.setReadOnly(True)
        layout.addWidget(self.sortie,2,1)
        
        self.T2label = QLabel("K")
        layout.addWidget(self.T2label,2,2)
        
        btn = QPushButton("?")
        btn.pressed.connect(self.help)
        layout.addWidget(btn,4,2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def convert_temperature(self):
        try:
            temp = float(self.champ.text())
            if self.combobox.currentText() == "°C -> K":
                if temp < -273.15:
                    self.show_error("Valeur incorrect : inférieur à 0 K")
                    return
                converted_temp = temp + 273.15
            else:
                if temp < 0:
                    self.show_error("Valeur incorrect : inférieur à 0 K")
                    return
                converted_temp = temp - 273.15

            self.sortie.setText(f"{converted_temp:.2f}")

        except ValueError:
            self.show_error("Valeur incorrect : caractère incompatible")
    
    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("Erreur")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
    def help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Aide")
        msg.setText("Permet de convertir une température soit de Kelvin en Celsius, soit de Celsius vers Kelvin")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def update_labels(self):
        if self.combobox.currentText() == "°C -> K":
            self.T1label.setText("°C")
            self.T2label.setText("K")
        else:
            self.T1label.setText("K")
            self.T2label.setText("°C")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
    echange()