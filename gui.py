import os
import sys
import csv
import re
from engine import Engine
from gui_pages.dashboard import DashboardPage
from gui_pages.model_analysis import ModelAnalysisPage
from gui_pages.logs import LogsPage
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from gui_pages.map_page import MapPage
from gui_pages.settings_page import SettingsPage






class MainWindow(QMainWindow, Engine):
    def __init__(self):
        super().__init__()
        super().setWindowTitle("Proje arayüzü")
        self.resize(1366, 768)

        self.is_dark = True
        self.apply_theme(self.is_dark)

        self.load_model_scaler()

        # Ana Yatay Yerleşim (Sidebar + İçerik)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. SOL MENÜ (SIDEBAR)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 20)
        sidebar_layout.setSpacing(10)

        app_title = QLabel("🛡️ EFES\nSaldırı Tespit Sistemi")
        app_title.setObjectName("app_title")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(app_title)

        self.btn_dashboard = QPushButton("📊 Canlı İzleme (Dashboard)")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        
        self.btn_model = QPushButton("📈 Model Başarı Analizleri")
        self.btn_model.setCheckable(True)

        self.btn_logs = QPushButton("📂 Log Yönetimi")
        self.btn_logs.setCheckable(True)

        self.btn_auto = QPushButton("🌍 Otonom Uçuş & Harita")
        self.btn_auto.setCheckable(True)

        self.btn_config = QPushButton("⚙️ Görev & Yapılandırma")
        self.btn_config.setCheckable(True)

        
        for btn in [self.btn_dashboard, self.btn_model, self.btn_logs, self.btn_auto, self.btn_config]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sidebar_layout.addWidget(btn)

       
        
        sidebar_layout.addStretch()

        self.btn_theme = QPushButton("☀️ Gündüz Moda Geç")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setObjectName("btn_theme")
        sidebar_layout.addWidget(self.btn_theme)
        
        version_lbl = QLabel("Model: CRNN-LSTM\nVersiyon: 1.0.3")
        version_lbl.setObjectName("version_lbl")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_lbl)

        main_layout.addWidget(self.sidebar)

        
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(25, 20, 25, 20)
        content_layout.setSpacing(20)

        self.create_header_panel()
        content_layout.addWidget(self.header_frame)

       # Stacked Widget (Sayfalar)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(DashboardPage(self))
        self.stacked_widget.addWidget(ModelAnalysisPage())
        self.stacked_widget.addWidget(LogsPage(self))
        self.stacked_widget.addWidget(MapPage(self))        
        self.stacked_widget.addWidget(SettingsPage(self))



        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_container)



        # Menü Sinyalleri
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.btn_model.clicked.connect(lambda: self.switch_page(1))
        self.btn_logs.clicked.connect(lambda: self.switch_page(2))
        self.btn_auto.clicked.connect(lambda: self.switch_page(3))   
        self.btn_config.clicked.connect(lambda: self.switch_page(4)) 





        # Thread Başlangıcı
        self.Thread()

    def create_header_panel(self):
        self.header_frame = QFrame()
        self.header_frame.setObjectName("header_frame")
        self.header_frame.setFixedHeight(90)
        header_layout = QHBoxLayout(self.header_frame)
        
        self.status_icon = QLabel("✓")
        self.status_icon.setStyleSheet("font-size: 36px; font-weight: bold; color: #00ff00;")
        
        self.status_label = QLabel("Sistem Güvende (Analiz Devam Ediyor)")
        self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ff00;")
        
        risk_layout = QVBoxLayout()
        risk_title = QLabel("Anlık Spoofing / Tehdit Olasılığı:")
        risk_title.setObjectName("risk_title")
        
        self.risk_bar = QProgressBar()
        self.risk_bar.setRange(0, 100)
        self.risk_bar.setValue(0)
        self.risk_bar.setFormat("%v%")
        self.risk_bar.setFixedWidth(300)
        
        risk_layout.addWidget(risk_title)
        risk_layout.addWidget(self.risk_bar)
        risk_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(self.status_icon)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addLayout(risk_layout)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.btn_theme.setText("☀️ Gündüz Moda Geç" if self.is_dark else "🌙 Gece Moda Geç")
        self.apply_theme(self.is_dark)

    def apply_theme(self, dark: bool):
        if dark:
            self.setStyleSheet("""
                QMainWindow { background-color: #0d0d16; }
                QWidget { color: #d1d1e0; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 14px; }
                #sidebar { background-color: #161623; border-right: 1px solid #232336; }
                #sidebar QPushButton { background-color: transparent; color: #8b8bad; border: none; border-radius: 8px; padding: 12px 15px; text-align: left; font-weight: 600; font-size: 15px; }
                #sidebar QPushButton:hover { background-color: #232336; color: #ffffff; }
                #sidebar QPushButton:checked { background-color: #2a2a44; color: #00ffff; border-left: 4px solid #00ffff; }
                #header_frame { background-color: #1a251f; border: 1px solid #00ff00; border-radius: 12px; padding: 10px; }
                QProgressBar { border: 1px solid #232336; border-radius: 6px; background-color: #161623; text-align: center; color: white; font-weight: bold; height: 20px; }
                QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00ffff, stop:1 #0055ff); border-radius: 5px; }
                QScrollArea { border: none; background-color: transparent; }
                QStackedWidget > QWidget { background-color: transparent; }
                QScrollBar:vertical { background: #0d0d16; width: 10px; border-radius: 5px; }
                QScrollBar::handle:vertical { background: #3c3c54; border-radius: 5px; }
                QScrollBar::handle:vertical:hover { background: #5a5a7a; }
                #info_panel { background-color: #161623; border: 1px solid #232336; border-radius: 10px; }
                
                #app_title { font-size: 22px; font-weight: 800; color: white; margin-bottom: 20px; }
                #btn_theme { font-size: 13px; color: #a0a0c0; border: 1px solid #3c3c54; padding: 10px; border-radius: 6px; }
                #btn_theme:hover { background-color: #232336; color: #ffffff; }
                #version_lbl { color: #666680; font-size: 11px; }
                #risk_title { color: #a0a0c0; font-size: 12px; }
                #info_title { font-size: 14px; font-weight: bold; color: #00ffff; }
                #info_text { color: #d1d1e0; font-size: 13px; line-height: 1.5; }
                #info_line { color: #232336; }
                #feat_title { font-size: 14px; font-weight: bold; color: #00ffff; }
                
                #page_title { font-size: 20px; font-weight: bold; color: white; }
                QLabel[class="img_title"] { font-size: 16px; color: #00ffff; font-weight: bold; margin-top: 10px; }
                
                QPushButton[class="log_btn"] { background-color: #2b2b40; color: #fff; border: 1px solid #3c3c54; border-radius: 6px; padding: 8px 15px;}
                QPushButton[class="log_btn"]:hover { background-color: #3b3b55; }
                
                #log_text_box {
                    background-color: #12121e; color: #00ff00; font-family: 'Consolas', monospace;
                    font-size: 14px; border: 1px solid #3c3c54; border-radius: 8px; padding: 15px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #f5f6fa; }
                QWidget { color: #2d3436; font-family: 'Segoe UI', -apple-system, sans-serif; font-size: 14px; }
                #sidebar { background-color: #ffffff; border-right: 1px solid #dcdde1; }
                #sidebar QPushButton { background-color: transparent; color: #718093; border: none; border-radius: 8px; padding: 12px 15px; text-align: left; font-weight: 600; font-size: 15px; }
                #sidebar QPushButton:hover { background-color: #f1f2f6; color: #2f3640; }
                #sidebar QPushButton:checked { background-color: #e8f3fe; color: #007bff; border-left: 4px solid #007bff; }
                #header_frame { background-color: #ecfdf5; border: 1px solid #10b981; border-radius: 12px; padding: 10px; }
                QProgressBar { border: 1px solid #dcdde1; border-radius: 6px; background-color: #f5f6fa; text-align: center; color: #2d3436; font-weight: bold; height: 20px; }
                QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007bff, stop:1 #00d2ff); border-radius: 5px; }
                QScrollArea { border: none; background-color: transparent; }
                QStackedWidget > QWidget { background-color: transparent; }
                QScrollBar:vertical { background: #f5f6fa; width: 10px; border-radius: 5px; }
                QScrollBar::handle:vertical { background: #dcdde1; border-radius: 5px; }
                QScrollBar::handle:vertical:hover { background: #b2bec3; }
                #info_panel { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 10px; }
                
                #app_title { font-size: 22px; font-weight: 800; color: #2d3436; margin-bottom: 20px; }
                #btn_theme { font-size: 13px; color: #718093; border: 1px solid #dcdde1; padding: 10px; border-radius: 6px; }
                #btn_theme:hover { background-color: #f1f2f6; color: #2d3436; }
                #version_lbl { color: #8395a7; font-size: 11px; }
                #risk_title { color: #718093; font-size: 12px; }
                #info_title { font-size: 14px; font-weight: bold; color: #007bff; }
                #info_text { color: #2d3436; font-size: 13px; line-height: 1.5; }
                #info_line { color: #dcdde1; }
                #feat_title { font-size: 14px; font-weight: bold; color: #007bff; }
                
                #page_title { font-size: 20px; font-weight: bold; color: #2d3436; }
                QLabel[class="img_title"] { font-size: 16px; color: #007bff; font-weight: bold; margin-top: 10px; }
                
                QPushButton[class="log_btn"] { background-color: #ffffff; color: #2d3436; border: 1px solid #dcdde1; border-radius: 6px; padding: 8px 15px;}
                QPushButton[class="log_btn"]:hover { background-color: #f1f2f6; }
                
                #log_text_box {
                    background-color: #ffffff; color: #27ae60; font-family: 'Consolas', monospace;
                    font-size: 14px; border: 1px solid #dcdde1; border-radius: 8px; padding: 15px;
                }
            """)
        
        # update PgGraph backgrounds
        if hasattr(self, 'graph_list'):
            for g in self.graph_list:
                g.set_theme(dark)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_model.setChecked(index == 1)
        self.btn_logs.setChecked(index == 2)
        self.btn_auto.setChecked(index == 3)
        self.btn_config.setChecked(index == 4)

    def setWindowTitle(self, title):
        # Prevent actual window title from changing
        if title == "Proje arayüzü":
            super().setWindowTitle(title)
            
        if hasattr(self, 'header_frame'):
            match = re.search(r'\(%([0-9.]+)\)', title)
            if match:
                risk_val = float(match.group(1))
                self.risk_bar.setValue(int(risk_val))

            if "UYARI" in title or "SALDIRI" in title:
                self.status_icon.setText("⚠")
                self.status_icon.setStyleSheet("font-size: 36px; font-weight: bold; color: #ff3333;")
                self.status_label.setText("UYARI: GNSS Spoofing Saldırısı Tespit Edildi!")
                self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff3333;")
                self.header_frame.setStyleSheet("#header_frame { background-color: #2a1114; border: 1px solid #ff3333; border-radius: 12px; }")
                self.risk_bar.setStyleSheet("""QProgressBar::chunk { background-color: #ff3333; border-radius: 5px; }""")
            else:
                self.status_icon.setText("✓")
                self.status_icon.setStyleSheet("font-size: 36px; font-weight: bold; color: #00ff00;")
                self.status_label.setText("Sistem Güvende (Normal Akış)")
                self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ff00;")
                self.header_frame.setStyleSheet("#header_frame { background-color: #112a1c; border: 1px solid #00ff00; border-radius: 12px; }")
                self.risk_bar.setStyleSheet("""QProgressBar::chunk { background-color: #00ffff; border-radius: 5px; }""")

    def graph_update(self, oran, vektor):
        # 1. Engine.py içindeki asıl grafik güncellemesini çalıştır
        super().graph_update(oran, vektor)
        
        # SAĞ PANEL CANLI VERİ GÜNCELLEMESİ (Feature Dağılımlarının Gösterimi)
        if hasattr(self, 'live_feat_bars'):
            # Her bir özellik için kabaca min-max sınırları (Görsel % oran için)
            limits = [
                (20, 60),   # Ort C/N0 
                (0, 10),    # Std C/N0
                (-50, 50),  # Ort prRes  
                (0, 20),    # Std prRes
                (0, 100),   # Max prRes
                (0, 30),    # Kull Uydu
                (0, 30),    # Gör Uydu
                (0.5, 3.0)  # Açı Oranı
            ]
            for i, val in enumerate(vektor):
                if i < len(self.live_feat_bars):
                    bar, lbl = self.live_feat_bars[i]
                    lbl.setText(f"{val:.1f}")
                    
                    min_v, max_v = limits[i]
                    perc = ((val - min_v) / (max_v - min_v)) * 100
                    perc = max(0, min(100, perc))
                    bar.setValue(int(perc))

        # 2. CSV formatında arka planda verileri depola
        if not hasattr(self, 'log_data'):
            # İlk satır: Header / Başlıklar
            self.log_data = [["Tarih_Saat", "Risk_Scoru", "Durum", "Mean_cno", "std_cno", "mean_prRes", "std_prRes", "max_prRes", "num_used", "num_visible", "cno_elev_ratio"]]
            
        import datetime
        zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        durum = "SPOOFING" if oran > 0.5 else "NORMAL"
        
        # Değerleri ve skoru string'e çevirip bir liste yapısı yaratıyoruz
        satir = [zaman, f"{oran:.4f}", durum] + [f"{v:.4f}" for v in vektor]
        self.log_data.append(satir)
        
        # 3. Arayüz sekmesindeki ekrana "log_text" içine virgülle ayrılmış (CSV) tarzda bas
        if hasattr(self, 'log_text'):
            csv_mensei = ",".join(satir)
            # Sadece SPOOFING anlarını veya isterseniz her şeyi text'e yazdırabilirsiniz. 
            # Ekranda bilgisayarı kastırmaması adına log yönetiminde anlık uarıları yakalamak daha stabildir
            # Ama veri analisti görsün diyorsanız direkt ekliyoruz:
            if durum == "SPOOFING":
                self.log_text.append(f"[ALARM] {csv_mensei}")

    # Sekme 1: Dashboard
    def page1(self):
        from gui_pages.dashboard import DashboardPage
        page = QWidget()
        page.setObjectName("dashboard_page")
        layout = QVBoxLayout(page)
        self.dashboard_widget = DashboardPage(self)
        layout.addWidget(self.dashboard_widget)
        return page

    # Sekme 2: Model Analizi
    def page2(self):
        from gui_pages.model_analysis import ModelAnalysisPage
        page = QWidget()
        page.setObjectName("model_analysis_page")
        layout = QVBoxLayout(page)
        self.analysis_widget = ModelAnalysisPage(self)
        layout.addWidget(self.analysis_widget)
        return page

    # Sekme 3: Loglar (Canlı Akış)
    def page3(self):
        from gui_pages.logs import LogsPage
        page = QWidget()
        page.setObjectName("logs_page")
        layout = QVBoxLayout(page)
        self.logs_widget = LogsPage(self)
        layout.addWidget(self.logs_widget)
        return page
        
    def save_log_file(self):
        from gui_pages.log_manager import LogManager
        LogManager.save_log_file(self)
        
    def load_log_file(self):
        from gui_pages.log_manager import LogManager
        LogManager.load_log_file(self)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
