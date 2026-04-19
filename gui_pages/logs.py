import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox

class LogsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title = QLabel("📂 Sistem Güvenlik ve Uyarı Logları")
        title.setObjectName("page_title")
        
        btn_save_log = QPushButton("💾 Log Kaydet")
        btn_load_log = QPushButton("📂 Log Yükle")
        btn_save_log.setProperty("class", "log_btn")
        btn_load_log.setProperty("class", "log_btn")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_save_log)
        header_layout.addWidget(btn_load_log)
        layout.addLayout(header_layout)
        
        self.main_window.log_text = QTextEdit()
        self.main_window.log_text.setReadOnly(True)
        self.main_window.log_text.setObjectName("log_text_box")
        
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.main_window.log_text.append(f"[{dt}] [SİSTEM] Arayüz ve Yapay Zeka Motoru başlatıldı.")
        
        layout.addWidget(self.main_window.log_text)
        
        from gui_pages.log_manager import LogManager
        btn_save_log.clicked.connect(lambda: LogManager.save_log_file(self.main_window))
        btn_load_log.clicked.connect(lambda: LogManager.load_log_file(self.main_window))