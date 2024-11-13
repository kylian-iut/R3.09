import sys

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversion de Température")
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


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()