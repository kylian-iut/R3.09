import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton
from PyQt6.QtCore import Qt

class SecondaryWindow(QMainWindow):
    def __init__(self, text):
        super().__init__()
        self.setWindowTitle("Fenêtre Secondaire")
        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)
        self.resize(200, 100)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fenêtre Principale")
        self.resize(300, 150)

        # Bouton pour ouvrir la première fenêtre secondaire
        self.button1 = QPushButton("Ouvrir Fenêtre 1", self)
        self.button1.clicked.connect(self.open_window1)
        self.button1.move(50, 50)

        # Bouton pour ouvrir la deuxième fenêtre secondaire
        self.button2 = QPushButton("Ouvrir Fenêtre 2", self)
        self.button2.clicked.connect(self.open_window2)
        self.button2.move(150, 50)

        self.window1 = None
        self.window2 = None

    def open_window1(self):
        if not self.window1 or not self.window1.isVisible():
            self.window1 = SecondaryWindow("Bonjour de la première fenêtre !")
            self.window1.show()

    def open_window2(self):
        if not self.window2 or not self.window2.isVisible():
            self.window2 = SecondaryWindow("Bonjour de la deuxième fenêtre !")
            self.window2.show()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()