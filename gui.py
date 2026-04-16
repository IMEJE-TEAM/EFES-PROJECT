import sys
from engine import Engine

from PyQt6.QtWidgets import *
class MainWindow(QMainWindow, Engine):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model")
        self.resize(1920,1080)

        self.load_model_scaler()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_widget = QWidget()
        self.main_layout = QVBoxLayout()

        self.graph_create_add()

        main_widget.setLayout(self.main_layout)
        self.scroll_area.setWidget(main_widget)
        self.setCentralWidget(self.scroll_area)

        self.Thread()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
