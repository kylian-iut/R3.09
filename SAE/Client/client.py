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
    QFileDialog,
    QTextEdit,
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

class RenameWindow(QWidget):
    def __init__(self, file_name, parent=None):
        super().__init__()
        
        self.old_name = file_name
        self.parent = parent
        
        self.setWindowTitle(f"Renommer {self.old_name}")
        self.resize(300, 150)
        
        layout = QGridLayout()

        self.new_name_input = QLineEdit()
        self.new_name_input.setText(self.old_name)
        layout.addWidget(self.new_name_input, 0, 0, 1, 2)

        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self.enregistrer)
        layout.addWidget(self.save_button, 1, 0)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.close)
        layout.addWidget(self.cancel_button, 1, 1)

        self.setLayout(layout)

    def enregistrer(self):
        new_name = self.new_name_input.text().strip()

        if not new_name:
            self.parent.show_error("Le nouveau nom ne peut pas être vide.")
            return

        if new_name in self.parent.files:
            self.parent.show_error(f"Le fichier '{new_name}' existe déjà.")
            return

        self.parent.files[new_name] = self.parent.files.pop(self.old_name)

        self.parent.listWidget.clear()
        self.parent.listWidget.addItems(self.parent.files.keys())
        self.close()

class EditorWindow(QWidget):
    def __init__(self, file_name, parent=None):
        super().__init__()
        
        self.file_name = file_name
        self.parent = parent
        self.setWindowTitle(f"Édition de {file_name}")

        layout = QGridLayout()

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit,0,0,1,2)
        if file_name in self.parent.files:
            self.text_edit.setPlainText(self.parent.files[file_name])

        save_button = QPushButton("Enregistrer")
        save_button.clicked.connect(self.enregistrer)
        layout.addWidget(save_button,1,0)

        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button,1,1)

        self.setLayout(layout)

    def enregistrer(self):
        new_data = self.text_edit.toPlainText()
        self.parent.files[self.file_name] = new_data
        self.close()

class CreateWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.parent=parent
        self.setWindowTitle("Nouveau fichier")
        self.resize(300, 200)

        layout = QGridLayout()

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit, 0, 0, 1, 3)

        self.file_name_input = QLineEdit()
        self.file_name_input.setPlaceholderText("Nom du fichier")
        layout.addWidget(self.file_name_input, 1, 0)

        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self.enregistrer)
        layout.addWidget(self.save_button, 1, 1)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.close)
        layout.addWidget(self.cancel_button, 1, 2)

        self.setLayout(layout)
    
    def enregistrer(self):
        file_name = self.file_name_input.text().strip()

        if not file_name:
            self.parent.show_error("Le nom du fichier ne peut pas être vide.")
            return

        if file_name in self.parent.files:
            self.parent.show_error(f"Le fichier '{file_name}' existe déjà.")
            return
        
        self.parent.files[file_name] = self.text_edit.toPlainText()
        newItem = QListWidgetItem()
        newItem.setText(file_name)
        self.parent.listWidget.insertItem(-1, newItem)
        self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Client SAE3.02")
        self.setFixedSize(550, 330)
        layout = QGridLayout()
        
        self.stacklayout = QStackedLayout()

        self.listWidget = QListWidget(self)
        self.listWidget.resize(700, 700)
        self.listWidget.setStyleSheet("QListWidget { font-size: 18px; }")
        self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.listWidget,0,0,10,4)
        self.files = {}
        
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
        # Ouvre l'explorateur natif pour sélectionner des fichiers
        selected_files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner un ou plusieurs fichiers",
            "",
            "Python (*.py);;;Tous les fichiers (*)"
        )

        if selected_files:
            # Ajouter les fichiers sélectionnés à la liste
            for file in selected_files:
                file_name = os.path.basename(file)

                if file_name in self.files:
                    self.show_error(f"Le fichier '{file_name}' existe déjà.")
                    return

                try:
                    with open(file, 'r') as f:
                        self.files[file_name]=f.read()
                except FileNotFoundError:
                    self.show_error(f"Le fichier '{file_name}' n'a pas été trouvé.")
                    return
                except UnicodeDecodeError:
                    self.show_error(f"Le fichier '{file_name}' n'est pas compatible.")
                    return
                else:
                    newItem = QListWidgetItem()
                    newItem.setText(file_name)
                    self.listWidget.insertItem(-1, newItem)
                

    def edit(self):
        selected_items = self.listWidget.selectedItems()
        if len(selected_items) == 1:
            file_name=selected_items[0].text()
            self.editor_window = EditorWindow(file_name, self)
            self.editor_window.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.editor_window.show()
    
    def new(self):
        self.create_window = CreateWindow(self)
        self.create_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.create_window.show()
    
    def rename(self):
        selected_items = self.listWidget.selectedItems()
        if len(selected_items) == 1:
            file_name=selected_items[0].text()
            self.rename_window = RenameWindow(file_name, self)
            self.rename_window.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.rename_window.show()
    
    def suppr(self):
        selected_items = self.listWidget.selectedItems()
        if len(selected_items) == 1:
            self.listWidget.takeItem(self.listWidget.row(selected_items[0]))
            self.files.pop(selected_items[0].text())
        elif len(selected_items) != 0:
            confirmation_dialog = QMessageBox()
            confirmation_dialog.setIcon(QMessageBox.Icon.Warning)
            confirmation_dialog.setWindowTitle("Confirmer la suppression")
            confirmation_dialog.setText(f"Êtes-vous sûr de vouloir supprimer {len(selected_items)} fichiers ?")
            confirmation_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if confirmation_dialog.exec() == QMessageBox.StandardButton.Yes:
                for item in selected_items:
                    self.files.pop(item.text())
                    self.listWidget.takeItem(self.listWidget.row(item))

    
    def upload(self):
        return
    
    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
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