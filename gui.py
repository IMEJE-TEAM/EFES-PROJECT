import sys
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QPainter

class MapMotor(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.toplam_zoom = 1.0
        self.sahne = QGraphicsScene(self)
        

        self.setScene(self.sahne)

        self.map_image = QPixmap("map.png")

        self.harita_ogesi = QGraphicsPixmapItem(self.map_image)
        self.sahne.addItem(self.harita_ogesi)
        self.fitInView(self.harita_ogesi, Qt.KeepAspectRatio)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
    
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            if self.toplam_zoom < 8:
               self.toplam_zoom *= 1.15
               self.scale(1.15, 1.15)
        else:
            if self.toplam_zoom > 1.3:
                self.toplam_zoom *= 0.85
                self.scale(0.85, 0.85)
        
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.mapMotor = MapMotor()
        self.mainLayout = QVBoxLayout(self)

        self.weatherPanel= QHBoxLayout()
        self.weatherinfo = QLabel("Hava Durumu ☀️: ")
        self.weathertemperature = QLabel("Hava Sıcaklığı 🌡️: ")
        self.location = QLabel("Konum Bilgisi [x: y: z:]")

        self.weatherPanel.addWidget(self.weatherinfo)
        self.weatherPanel.addWidget(self.weathertemperature)
        self.weatherPanel.addWidget(self.location)
    
        self.mainLayout.addLayout(self.weatherPanel)
        self.mainLayout.addWidget(self.mapMotor)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800,600)
    window.setWindowTitle("EFES Project GUI")
    window.show()

    sys.exit(app.exec())