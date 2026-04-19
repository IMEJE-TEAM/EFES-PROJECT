import os
import sys
import csv
import re
from engine import Engine
from gui_pages.dashboard import DashboardPage
from gui_pages.iha_status import IhaStatusPage
from gui_pages.model_analysis import ModelAnalysisPage
from gui_pages.logs import LogsPage
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap
from gui_pages.map_page import MapPage
from gui_pages.settings_page import SettingsPage






class MainWindow(QMainWindow, Engine):
    def __init__(self):
        super().__init__()
        super().setWindowTitle("SIPER Askeri")
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

        # Logo ekleme
        logo_label = QLabel()
        pixmap = QPixmap("graffiti_red.png")
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
            sidebar_layout.addWidget(logo_label)

        app_title = QLabel("SİPER TAKTİK\nKOMUTA KONTROL")
        app_title.setObjectName("app_title")
        app_title.setWordWrap(True)
        app_title.setFixedHeight(60)
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(app_title)

        self.btn_dashboard = QPushButton(" [01] TAKTİK EKRAN")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        
        self.btn_model = QPushButton(" [02] SİSTEM ANALİZİ")
        self.btn_model.setCheckable(True)

        self.btn_logs = QPushButton(" [03] SİSTEM LOGLARI")
        self.btn_logs.setCheckable(True)

        self.btn_iha = QPushButton(" [04] İHA TELEMETRİ")
        self.btn_iha.setCheckable(True)

        self.btn_auto = QPushButton(" [05] OTONOM NAVİGASYON")
        self.btn_auto.setCheckable(True)

        self.btn_config = QPushButton(" [06] KONFİGÜRASYON")
        self.btn_config.setCheckable(True)

        
        for btn in [self.btn_dashboard, self.btn_model, self.btn_logs, self.btn_iha, self.btn_auto, self.btn_config]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sidebar_layout.addWidget(btn)

       
        
        sidebar_layout.addStretch()

        self.btn_theme = QPushButton("OPTİK: GÜNDÜZ MODU")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setObjectName("btn_theme")
        sidebar_layout.addWidget(self.btn_theme)
        
        version_lbl = QLabel("AĞ: CRNN-LSTM AKTİF\nSÜRÜM: MIL-STD-1.0.3\nDURUM: GÜVENLİ")
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
        self.iha_page = IhaStatusPage()
        self.stacked_widget.addWidget(self.iha_page)
        self.map_page = MapPage(self)
        self.stacked_widget.addWidget(self.map_page)        
        self.stacked_widget.addWidget(SettingsPage(self))



        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_container)



        # Menü Sinyalleri
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.btn_model.clicked.connect(lambda: self.switch_page(1))
        self.btn_logs.clicked.connect(lambda: self.switch_page(2))
        self.btn_iha.clicked.connect(lambda: self.switch_page(3))
        self.btn_auto.clicked.connect(lambda: self.switch_page(4))   
        self.btn_config.clicked.connect(lambda: self.switch_page(5)) 





        # Thread Başlangıcı
        self.Thread()

    def create_header_panel(self):
        self.header_frame = QFrame()
        self.header_frame.setObjectName("header_frame")
        self.header_frame.setFixedHeight(90)
        header_layout = QHBoxLayout(self.header_frame)
        
        self.status_icon = QLabel("✓")
        self.status_icon.setStyleSheet("font-size: 36px; font-weight: bold; color: #39ff14;")
        
        self.status_label = QLabel("SİSTEM DURUMU: NOMİNAL")
        self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #39ff14; letter-spacing: 1px;")
        
        risk_layout = QVBoxLayout()
        risk_title = QLabel("TEHDİT SEVİYESİ / ELEKTRONİK HARP RİSKİ:")
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
        self.btn_theme.setText("OPTİK: GÜNDÜZ MODU" if self.is_dark else "OPTİK: GECE MODU")
        self.apply_theme(self.is_dark)

    def apply_theme(self, dark: bool):
        if dark:
            self.setStyleSheet("""
                QMainWindow { background-color: #050907; }
                QWidget { color: #39ff14; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; }
                #sidebar { background-color: #0a120e; border-right: 2px solid #1a3c28; }
                #sidebar QPushButton { background-color: transparent; color: #558b6e; border: 1px solid transparent; border-radius: 4px; padding: 12px 15px; text-align: left; font-weight: bold; font-size: 14px; letter-spacing: 1px; }
                #sidebar QPushButton:hover { background-color: #12241b; color: #39ff14; border: 1px solid #1a3c28; }
                #sidebar QPushButton:checked { background-color: #1a3c28; color: #ffffff; border-left: 4px solid #39ff14; border-right: 1px solid #39ff14; border-top: 1px solid #39ff14; border-bottom: 1px solid #39ff14; }
                #header_frame { background-color: #08100c; border: 2px solid #1a3c28; border-radius: 0px; padding: 10px; }
                QProgressBar { border: 1px solid #39ff14; border-radius: 0px; background-color: #050907; text-align: center; color: #39ff14; font-weight: bold; height: 18px; }
                QProgressBar::chunk { background-color: #39ff14; }
                QScrollArea { border: none; background-color: transparent; }
                QStackedWidget > QWidget { background-color: transparent; }
                QScrollBar:vertical { background: #050907; width: 12px; border: 1px solid #1a3c28; }
                QScrollBar::handle:vertical { background: #1a3c28; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #39ff14; }
                #info_panel { background-color: #0a120e; border: 1px solid #1a3c28; }
                
                #app_title { font-size: 18px; font-weight: bold; color: #39ff14; margin-bottom: 16px; letter-spacing: 2px; }
                #btn_theme { font-size: 12px; color: #558b6e; border: 1px solid #1a3c28; padding: 10px; border-radius: 0px; }
                #btn_theme:hover { background-color: #1a3c28; color: #39ff14; }
                #version_lbl { color: #558b6e; font-size: 11px; letter-spacing: 1px; }
                #risk_title { color: #39ff14; font-size: 12px; letter-spacing: 1px; font-weight: bold; }
                #info_title { font-size: 16px; font-weight: bold; color: #39ff14; text-transform: uppercase; }
                #info_text { color: #a2c4b0; font-size: 13px; line-height: 1.5; }
                #info_line { color: #1a3c28; }
                #feat_title { font-size: 16px; font-weight: bold; color: #39ff14; text-transform: uppercase; }
                
                #page_title { font-size: 22px; font-weight: bold; color: #39ff14; text-transform: uppercase; letter-spacing: 2px; }
                QLabel[class="img_title"] { font-size: 16px; color: #39ff14; font-weight: bold; margin-top: 10px; text-transform: uppercase; }
                
                QPushButton[class="log_btn"] { background-color: #0a120e; color: #39ff14; border: 1px solid #1a3c28; border-radius: 0px; padding: 8px 15px; font-weight: bold; text-transform: uppercase; }
                QPushButton[class="log_btn"]:hover { background-color: #1a3c28; border-color: #39ff14; }
                
                #log_text_box {
                    background-color: #050907; color: #39ff14; font-family: 'Consolas', monospace;
                    font-size: 13px; border: 1px solid #1a3c28; border-radius: 0px; padding: 15px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #e3e7d3; }
                QWidget { color: #2e3b32; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; }
                #sidebar { background-color: #d1d6c0; border-right: 2px solid #8d977a; }
                #sidebar QPushButton { background-color: transparent; color: #4a5c4d; border: 1px solid transparent; border-radius: 4px; padding: 12px 15px; text-align: left; font-weight: bold; font-size: 14px; letter-spacing: 1px; }
                #sidebar QPushButton:hover { background-color: #c0c7ad; color: #1e2922; border: 1px solid #8d977a; }
                #sidebar QPushButton:checked { background-color: #a8b092; color: #1e2922; border-left: 4px solid #1e2922; border-right: 1px solid #8d977a; border-top: 1px solid #8d977a; border-bottom: 1px solid #8d977a; }
                #header_frame { background-color: #d1d6c0; border: 2px solid #8d977a; border-radius: 0px; padding: 10px; }
                QProgressBar { border: 1px solid #4a5c4d; border-radius: 0px; background-color: #e3e7d3; text-align: center; color: #1e2922; font-weight: bold; height: 18px; }
                QProgressBar::chunk { background-color: #4a5c4d; }
                QScrollArea { border: none; background-color: transparent; }
                QStackedWidget > QWidget { background-color: transparent; }
                QScrollBar:vertical { background: #e3e7d3; width: 12px; border: 1px solid #8d977a; }
                QScrollBar::handle:vertical { background: #8d977a; min-height: 20px; }
                QScrollBar::handle:vertical:hover { background: #4a5c4d; }
                #info_panel { background-color: #d1d6c0; border: 1px solid #8d977a; }
                
                #app_title { font-size: 18px; font-weight: bold; color: #1e2922; margin-bottom: 16px; letter-spacing: 2px; }
                #btn_theme { font-size: 12px; color: #4a5c4d; border: 1px solid #8d977a; padding: 10px; border-radius: 0px; }
                #btn_theme:hover { background-color: #8d977a; color: #ffffff; }
                #version_lbl { color: #5a6b5d; font-size: 11px; letter-spacing: 1px; }
                #risk_title { color: #1e2922; font-size: 12px; letter-spacing: 1px; font-weight: bold; }
                #info_title { font-size: 16px; font-weight: bold; color: #1e2922; text-transform: uppercase; }
                #info_text { color: #2e3b32; font-size: 13px; line-height: 1.5; }
                #info_line { color: #8d977a; }
                #feat_title { font-size: 16px; font-weight: bold; color: #1e2922; text-transform: uppercase; }
                
                #page_title { font-size: 22px; font-weight: bold; color: #1e2922; text-transform: uppercase; letter-spacing: 2px; }
                QLabel[class="img_title"] { font-size: 16px; color: #1e2922; font-weight: bold; margin-top: 10px; text-transform: uppercase; }
                
                QPushButton[class="log_btn"] { background-color: #d1d6c0; color: #1e2922; border: 1px solid #8d977a; border-radius: 0px; padding: 8px 15px; font-weight: bold; text-transform: uppercase; }
                QPushButton[class="log_btn"]:hover { background-color: #a8b092; border-color: #4a5c4d; }
                
                #log_text_box {
                    background-color: #e3e7d3; color: #1e2922; font-family: 'Consolas', monospace;
                    font-size: 13px; border: 1px solid #8d977a; border-radius: 0px; padding: 15px;
                }
            """)
        
        # update PgGraph backgrounds
        if hasattr(self, 'graph_list'):
            for g in self.graph_list:
                g.set_theme(dark)

    def switch_page(self, index):
        page = self.stacked_widget.widget(index)
        opacity = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(opacity)
        animation = QPropertyAnimation(opacity, b"opacity")
        animation.setDuration(250)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.stacked_widget.setCurrentIndex(index)
        animation.start()
        self.page_animation = animation

        self.btn_dashboard.setChecked(index == 0)
        self.btn_model.setChecked(index == 1)
        self.btn_logs.setChecked(index == 2)
        self.btn_iha.setChecked(index == 3)
        self.btn_auto.setChecked(index == 4)
        self.btn_config.setChecked(index == 5)

    def update_map_position(self, lat, lon):
        if hasattr(self, 'map_page'):
            self.map_page.update_drone(lat, lon)
            
        if hasattr(self, 'iha_page'):
            import random
            telemetry = {
                'GPS_ground_speed': 15.2 + random.uniform(-1, 1),
                'GPS_altitude': 410.5 + random.uniform(-2, 2),
                'GPS_ground_course': (lon * 1000) % 360,
                'verticalSpeed': random.uniform(-0.5, 0.5),
                'GPS_hdop': random.uniform(0.8, 1.2),
                'GPS_numSat': int(14 + random.uniform(0, 3)),
                'navState': 'AUTO-NAV',
                'GPS_coord[0]': round(lat, 6),
                'GPS_coord[1]': round(lon, 6),
                'escTemperature': 42.0 + random.uniform(-1, 1),
                'vbat': 22.4 - random.uniform(0, 0.1),
                'rssi': -68 + int(random.uniform(-4, 4)),
                'activeWpNumber': 4,
                'navTgtPos[0]': round(1200 + random.uniform(-5, 5), 1),
                'navTgtPos[1]': round(800 + random.uniform(-5, 5), 1),
                'navTgtPos[2]': 400,
                'navVel[0]': round(10 + random.uniform(-0.5, 0.5), 2),
                'navVel[1]': round(10 + random.uniform(-0.5, 0.5), 2),
                'navVel[2]': round(random.uniform(-0.2, 0.2), 2),
                'accSmooth[0]': round(random.uniform(-0.1, 0.1), 3),
                'accSmooth[1]': round(random.uniform(-0.1, 0.1), 3),
                'accSmooth[2]': round(9.8 + random.uniform(-0.05, 0.05), 3),
                'gyroADC[0]': round(random.uniform(-0.5, 0.5), 2),
                'gyroADC[1]': round(random.uniform(-0.5, 0.5), 2),
                'gyroADC[2]': round(random.uniform(-0.5, 0.5), 2),
                'magADC[0]': int(random.uniform(100, 150)),
                'magADC[1]': int(random.uniform(100, 150)),
                'magADC[2]': int(random.uniform(100, 150)),
            }
            self.iha_page.update_telemetry(telemetry)

    def setWindowTitle(self, title):
        # Prevent actual window title from changing
        if title == "SIPER Askeri":
            super().setWindowTitle(title)
            
        if hasattr(self, 'header_frame'):
            match = re.search(r'\(%([0-9.]+)\)', title)
            if match:
                risk_val = float(match.group(1))
                self.risk_bar.setValue(int(risk_val))

            if "UYARI" in title or "SALDIRI" in title:
                self.status_icon.setText("⚠")
                self.status_icon.setStyleSheet("font-size: 36px; font-weight: bold; color: #ff003c;")
                self.status_label.setText("KRİTİK UYARI: TEHDİT TESPİT EDİLDİ!")
                self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ff003c; letter-spacing: 1px;")
                self.header_frame.setStyleSheet("#header_frame { background-color: #1a0505; border: 2px solid #ff003c; border-radius: 0px; }")
                self.risk_bar.setStyleSheet("""QProgressBar::chunk { background-color: #ff003c; } QProgressBar { border: 1px solid #ff003c; border-radius: 0px; }""")
            else:
                self.status_icon.setText("✓")
                self.status_icon.setStyleSheet("font-size: 36px; font-weight: bold; color: #39ff14;")
                self.status_label.setText("SİSTEM DURUMU: NOMİNAL")
                self.status_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #39ff14; letter-spacing: 1px;")
                self.header_frame.setStyleSheet("#header_frame { background-color: #08100c; border: 2px solid #1a3c28; border-radius: 0px; }")
                self.risk_bar.setStyleSheet("""QProgressBar::chunk { background-color: #39ff14; } QProgressBar { border: 1px solid #39ff14; border-radius: 0px; }""")

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
    app = QApplication(sys.argv) if QApplication.instance() is None else QApplication.instance()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
