import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.mainLayout = QVBoxLayout(self)

        self.weatherPanel= QHBoxLayout()
        self.weatherinfo = QLabel("Hava Durumu ☀️: ")
        self.weathertemperature = QLabel("Hava Sıcaklığı 🌡️: ")
        self.location = QLabel("Konum Bilgisi [x: y: z:]")

        self.weatherPanel.addWidget(self.weatherinfo)
        self.weatherPanel.addWidget(self.weathertemperature)
        self.weatherPanel.addWidget(self.location)

        self.mainLayout.addLayout(self.weatherPanel)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800,600)
    window.setWindowTitle("EFES Project GUI")
    window.show()

    sys.exit(app.exec())