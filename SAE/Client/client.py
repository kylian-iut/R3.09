import socket
import threading
import os
import re
import time

from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer, QTime
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QWidget,
    QGridLayout,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QFileDialog,
    QTextEdit,
    QRadioButton,
    QButtonGroup,
    QSpacerItem,
    QSizePolicy,
)

host = 'localhost'
port = '8000'

class WorkerThread(QThread):
    error_signal = pyqtSignal(str)

    def __init__(self, host, port, files, main, console_window):
        super().__init__()

        self.host=host
        self.port=port
        self.files=files
        self.main=main
        self.console_window=console_window
    
    def run(self):
        self.echange(self.host,self.port,self.files,self.main,self.console_window)

    def ecoute(self, client_socket):
        """
            Méthode qui permet d'obtenir et de traiter un réponse du serveur
        """
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
            elif reply.startswith("err:lang"):
                client_socket.close()
                return "err:lang"
            else:
                reply = ""
                try:
                    client_socket.send(reply.encode())
                except OSError:
                    return
        except ConnectionResetError:
            print(f"\033[31mLa connexion au serveur a été perdue!\033[0m")
            client_socket.close()
            return
        except TimeoutError:
            print(f"\033[31mLa connexion au serveur a échoué!\033[0m")
            client_socket.close()
            return
        except OSError:
            print(f"\033[31mLa connexion au serveur a été perdue!\033[0m")
            client_socket.close()
            return

    def envoie_fichier(self, client_socket, file_name, data):
        """
            Méthode qui permet l'envoie d'un script au serveur
        """
        file_size = len(data)
        print(f"{file_name} : {file_size} octets")

        try:
            client_socket.send("file".encode())
            client_socket.recv(1024)

            client_socket.send(file_name.encode())
            client_socket.recv(1024)

            client_socket.send(str(file_size).encode())
            client_socket.recv(1024)

            print("Téléversement...")
            client_socket.sendall(data.encode("utf-8"))
            client_socket.recv(1024)
            print("\033[92mFichier envoyé avec succès.\033[0m")
        except Exception as err:
            print(f"\033[31mErreur lors de l'envoi du fichier : {err}\033[0m")

    def envoie(self, client_socket, message, data=None):
        """
            Méthode qui gère l'envoie de commandes au serveur
        """
        server_status = self.ecoute(client_socket)
        if server_status == 'occuped':
            self.error_signal.emit(f"Serveur occupé!")
            return
        elif server_status == "err:lang":
            self.error_signal.emit(f"Serveur ne peut pas executer!")
            return
        if message.startswith("fichier:"):
            file_name = message.split(":", 1)[1].strip()
            self.envoie_fichier(client_socket, file_name, data)
        else:
            try:
                client_socket.send(message.encode())
                if self.ecoute(client_socket) == 'bye':
                    return
            except (ConnectionResetError, OSError):
                window.show_error(f"Le serveur a fermé la connexion!")
                client_socket.close()
                return

    def echange(self, host, port,files,main, console_window):
        """
            Méthode qui initialise la connexion avec le serveur et le déroulement des actions à lui faire traiter
        """
        file_names = list(files.keys())
        client_socket = socket.socket()
        client_socket.settimeout(1)
        try:
            client_socket.connect((host, int(port)))
        except ConnectionRefusedError:
            client_socket.close()
            self.error_signal.emit(f"La connexion au serveur a été refusée!")
            return
        except OSError:
            try:
                client_socket.close()
                self.error_signal.emit(f"Serveur injoignable!")
                return
            except KeyboardInterrupt:
                client_socket.close()
                self.error_signal.emit(f"Connexion annulée!")
                return
        else:
            print("\033[93mConnexion au serveur établie\033[0m")
            file_names = [main] + [item for item in file_names if item != main]
            print(file_names)
            for file_name in file_names:
                print(file_name)
                data=files[file_name]
                t1 = threading.Thread(target=self.envoie, args=[client_socket, "fichier:" + file_name, data])
                t1.start()
                try:
                    t1.join()
                except KeyboardInterrupt:
                    client_socket.send("bye".encode())
                    self.ecoute(client_socket)
                    client_socket.close()
                    return
            client_socket.send("ok".encode())
            client_socket.settimeout(None)
            start_status=client_socket.recv(1024).decode()
            if start_status == "ack":
                end_status=client_socket.recv(1024).decode()
                if end_status == "stderr":
                    console_window.text_color(QColor(255, 0, 0))
                elif end_status == "othererr":
                    console_window.text_color(QColor(255, 165, 0))
                else:
                    console_window.text_color(QColor(255, 255, 255))
                out=client_socket.recv(1024).decode()
                console_window.print_message(f"{out} \n")
                print("\033[92mRésultat de l'execution reçu avec succès.\033[0m")
                client_socket.send("ack".encode())
                client_socket.settimeout(1)
                self.ecoute(client_socket)

class Worker(QObject):
    # Signal pour envoyer un message d'erreur
    error_signal = pyqtSignal(str)

    def run(self):
        """
            Méthode qui empêche de traiter le script d'un langage non supporté
        """
        # Simule une tâche en arrière-plan
        self.error_signal.emit("Script ne peut pas être exécuté")

class ConsoleWindow(QMainWindow):
    def __init__(self, host, port, files, main):
        super().__init__()

        self.setWindowTitle("Console")
        self.resize(600, 400)

        layout = QGridLayout()

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        font = QFont("Courier", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        layout.addWidget(self.text_edit, 0, 0, 1, 4)

        self.clear_button = QPushButton("Effacer", self)
        self.clear_button.clicked.connect(self.clear)
        layout.addWidget(self.clear_button, 1, 0)

        """ self.toggle_button = QPushButton("Démarrer", self)
        self.toggle_button.setStyleSheet("background-color: green; color: white;")
        self.toggle_button.clicked.connect(self.toggle_color)
        layout.addWidget(self.toggle_button, 1, 0)

        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("Entrez un message")
        self.line_edit.setReadOnly(True)
        self.line_edit.returnPressed.connect(self.send_message)
        layout.addWidget(self.line_edit, 1, 1)

        self.send_button = QPushButton("Envoyer", self)
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button, 1, 2) """

        self.quit_button = QPushButton("Quitter", self)
        self.quit_button.clicked.connect(self.close)
        layout.addWidget(self.quit_button, 1, 3)

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer, 1, 2)  # Placer l'espacement entre les deux bouton

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)      
        self.time_elapsed = QTime(0, 0)  # Temps initial
        self.time_label = QTextEdit(self)
        self.time_label.setReadOnly(True)
        self.time_label.setFont(font)
        self.time_label.setFixedSize(120, 30)
        layout.addWidget(self.time_label, 1, 1, 1, 2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.worker_thread = WorkerThread(host,port,files,main,self)
        self.worker_thread.error_signal.connect(self.handle_server_error)
        self.start_timer()
        self.worker_thread.start()
        self.worker_thread.finished.connect(self.stop_timer)

    def handle_server_error(self, error_message):
        """ Gérer l'erreur de serveur : arrêter le chronomètre et afficher un pop-up. """
        self.stop_timer()  # Arrêter le chronomètre
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Erreur")
        msg.setText(error_message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        self.close()
    
    def start_timer(self):
        """ Démarre ou redémarre le chronomètre. """
        self.time_elapsed = QTime(0, 0)  # Réinitialiser le temps
        self.timer.start(10)  # Démarrer le timer (actualise toutes les 10 ms)
        self.time_label.setPlainText(f"{self.time_elapsed.toString('hh:mm:ss')}.{self.time_elapsed.msec():03d}")

    def stop_timer(self):
        self.timer.stop()

    def toggle_color(self):
        current_color = self.toggle_button.styleSheet()
        if "green" in current_color:
            self.toggle_button.setStyleSheet("background-color: red; color: white;")
            self.toggle_button.setText("Arrêter")
            self.text_edit.clear()
            self.line_edit.setReadOnly(False)
            self.print_message("Hello World !")
        else:
            self.toggle_button.setStyleSheet("background-color: green; color: white;")
            self.toggle_button.setText("Démarrer")
            self.line_edit.setReadOnly(True)
            self.line_edit.clear()

    def send_message(self):
        message = self.line_edit.text()
        if message:
            self.text_edit.append(f"> {message}")
            self.line_edit.clear()

    def update_timer(self):
        """ Met à jour le temps écoulé toutes les secondes. """
        self.time_elapsed = self.time_elapsed.addMSecs(10)
        self.time_label.setPlainText(f"{self.time_elapsed.toString('hh:mm:ss')}.{self.time_elapsed.msec():03d}")

    def text_color(self, color):
        self.text_edit.setTextColor(color)

    def print_message(self, message):
        self.text_edit.append(f"{message}")
    
    def clear(self):
        self.text_edit.clear()

class LanguageWindow(QWidget):
    def __init__(self, files, file_name, parent=None):
        super().__init__()
        self.file_name=file_name
        self.FILES=files
        self.parent=parent

        self.setWindowTitle("Choisir le langage d'exécution")
        self.setFixedSize(350, 200)

        grid_layout = QGridLayout()

        self.text_label = QLabel(f"Comment voulez-vous exécuter {file_name} ?")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setMaximumHeight(40)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.text_label, 0, 0, 2, 3)

        self.button_group = QButtonGroup()

        self.radio_python = QRadioButton("Python")
        self.button_group.addButton(self.radio_python)
        grid_layout.addWidget(self.radio_python, 2, 1, 1, 2)

        self.radio_java = QRadioButton("Java")
        self.button_group.addButton(self.radio_java)
        grid_layout.addWidget(self.radio_java, 3, 1, 1, 2)

        self.radio_c = QRadioButton("C")
        grid_layout.addWidget(self.radio_c, 4, 1, 1, 2)
        self.button_group.addButton(self.radio_c)

        self.radio_cpp = QRadioButton("C++")
        self.button_group.addButton(self.radio_cpp)        
        grid_layout.addWidget(self.radio_cpp, 5, 1, 1, 2)        

        self.button_enregistrer = QPushButton("Enregistrer")
        self.button_enregistrer.clicked.connect(self.enregistrer)
        grid_layout.addWidget(self.button_enregistrer, 6, 0, 1, 2)

        self.button_annuler = QPushButton("Annuler")
        self.button_annuler.clicked.connect(self.annuler)
        grid_layout.addWidget(self.button_annuler, 6, 2)

        self.setLayout(grid_layout)
    
    def annuler(self):
        self.close()

    def enregistrer(self):
        selected_language = None
        old_name=self.file_name
        tempfiles=self.FILES.copy() # cette manière permet de contourner la façon dont Python gère les objets mutables. Puisque avec seulement =, les deux variables pointent vers le même objet en mémoire
        if self.radio_python.isChecked():
            selected_language = "Python"
            self.file_name=old_name.split('.')[0]+".py"
        elif self.radio_java.isChecked():
            selected_language = "Java"
            self.file_name=old_name.split('.')[0]+".java"
        elif self.radio_c.isChecked():
            selected_language = "C"
            self.file_name=old_name.split('.')[0]+".c"
        elif self.radio_cpp.isChecked():
            selected_language = "C++"
            self.file_name=old_name.split('.')[0]+".cpp"
        if selected_language:
            tempfiles[self.file_name] = tempfiles.pop(old_name)
            self.parent.start_console(tempfiles, self.file_name)
            self.close()

class RenameWindow(QWidget):
    def __init__(self, file_name, parent=None):
        super().__init__()
        
        self.old_name = file_name
        self.parent = parent
        
        self.setWindowTitle(f"Renommer {self.old_name}")
        self.setFixedSize(300, 80)
        
        layout = QGridLayout()

        self.new_name_input = QLineEdit()
        self.new_name_input.setText(self.old_name)
        self.new_name_input.returnPressed.connect(self.enregistrer)
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
        
        self.resize(550, 330)
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
        self.resize(550, 330)

        layout = QGridLayout()

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit, 0, 0, 1, 3)

        self.file_name_input = QLineEdit()
        self.file_name_input.setPlaceholderText("Nom du fichier")
        self.file_name_input.returnPressed.connect(self.enregistrer)
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
        global port
        global host
        self.setWindowTitle("Client SAE3.02")
        self.setFixedSize(550, 330)
        self.console_window = None
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
        self.serv.setText(host)
        layout.addWidget(self.serv,10,1)

        self.T1label = QLabel("Port")
        layout.addWidget(self.T1label,10,2)
        
        self.port = QLineEdit()
        self.port.setText(port)
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
            "Tous les fichiers supportés (*.py *.c *.cpp *.cc *.java *.txt);;Python (*.py);;C (*.c);;C++ (*.cpp *.cc);;Java (*.java);;Texte (*.txt)"
        )

        if selected_files:
            # Ajouter les fichiers sélectionnés à la liste
            for file in selected_files:
                file_name = os.path.basename(file)

                if file_name in self.files:
                    self.show_error(f"Le fichier '{file_name}' existe déjà.")
                    return

                try:
                    with open(file, 'r', encoding="utf-8") as f:
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
        selected_items = self.listWidget.selectedItems() # Le fichier sélectionné sera main
        # Regex pour IPv4, IPv6, Hostname et Port réseau
        ipv4_regex = r'^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}$'
        ipv6_regex = r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9])?[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9])?[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9])?[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9])?[0-9]))$'
        hostname_regex = r'^(localhost|(?=.{1,253}$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(\.[a-zA-Z]{2,})*)$'
        port_regex = r'^(6553[0-5]|655[0-2][0-9]|65[0-4][0-9]{2}|6[0-4][0-9]{3}|[1-5][0-9]{4}|[1-9][0-9]{0,3}|0)$'

        if len(selected_items) == 1:
            if bool(re.match(ipv4_regex, self.serv.text()) or re.match(ipv6_regex, self.serv.text()) or re.match(hostname_regex, self.serv.text())):
                if bool(re.match(port_regex, self.port.text())):
                    if selected_items[0].text().split('.')[-1] not in ["py","java", "c", "cpp"]:
                        self.language_window = LanguageWindow(self.files, selected_items[0].text(), self)
                        self.language_window.setWindowModality(Qt.WindowModality.ApplicationModal)
                        self.language_window.show()
                    else:
                        self.start_console(self.files, selected_items[0].text())
                else:
                    self.show_error("Numéro du port incorrect !")
            else:
                self.show_error("Adresse du serveur incorrect !")
    
    def start_console(self, files, file_name):
        self.console_window = ConsoleWindow(self.serv.text(),self.port.text(),files,file_name)
        self.console_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.console_window.clear()
        self.console_window.show()

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
    app = QApplication([])

    window = MainWindow()

    worker_thread = QThread()
    worker = Worker()
    worker.moveToThread(worker_thread)

    worker_thread.started.connect(worker.run)
    worker_thread.start()

    window.show()
    app.exec()