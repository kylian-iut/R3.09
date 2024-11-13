import sys

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Une première fenêtre")
        self.resize(280, 150)
        self.nom=""
        pagelayout = QVBoxLayout()
        element_layout = QVBoxLayout()
        
        self.stacklayout = QStackedLayout()

        pagelayout.addLayout(element_layout)
        pagelayout.addLayout(self.stacklayout)

        label = QLabel("Saisir votre nom")
        element_layout.addWidget(label)

        self.champ = QLineEdit()
        self.champ.returnPressed.connect(self.activate_tab_1)
        self.champ.setMaxLength(30)
        element_layout.addWidget(self.champ)

        btn = QPushButton("Ok")
        btn.pressed.connect(self.activate_tab_1)
        element_layout.addWidget(btn)

        self.label_bonjour = QLabel()
        element_layout.addWidget(self.label_bonjour)

        btn = QPushButton("Quitter")
        btn.pressed.connect(self.activate_tab_2)
        element_layout.addWidget(btn)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)

    def activate_tab_1(self):
        self.nom=self.champ.text()
        self.label_bonjour.setText(f"Bonjour {self.nom}")
        window.show()

    def activate_tab_2(self):
        self.close()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()