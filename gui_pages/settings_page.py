from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("⚙️ Sistem Ayarları (Yapım Aşamasında)")
        title.setObjectName("page_title")
        layout.addWidget(title)
        layout.addStretch()