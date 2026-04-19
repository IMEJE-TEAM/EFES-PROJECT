import os
import webbrowser
import folium
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

class MapPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)

        self.info_label = QLabel("🌍 Dinamik Harita Modülü")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")

        self.desc_label = QLabel("Sistem kararlılığı (DLL güvenliği) için canlı harita \nharici tarayıcıda sekme olarak açılacaktır.")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-bottom: 20px;")

        self.btn_open_map = QPushButton("🗺️ Canlı Haritayı Başlat")
        self.btn_open_map.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white; 
                font-size: 18px; font-weight: bold; 
                padding: 15px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        self.btn_open_map.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Butona tıklanınca haritayı üreten fonksiyonu çalıştır
        self.btn_open_map.clicked.connect(self.open_live_map)

        layout.addStretch()
        layout.addWidget(self.info_label)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.btn_open_map)
        layout.addStretch()

    def open_live_map(self):
        # Şimdilik başlangıç noktası olarak Kayseri merkez koordinatlarını verdim.
        # İleride burayı engine.py'den gelen drone'un canlı GPS verisiyle değiştireceğiz.
        current_lat = 38.7312
        current_lon = 35.4787

        # Folium ile dinamik haritayı oluştur
        m = folium.Map(location=[current_lat, current_lon], zoom_start=15, control_scale=True)
        
        # Drone'u temsil eden kırmızı işaretçiyi ekle
        folium.Marker(
            [current_lat, current_lon],
            popup="🦅 EFES Drone (Anlık Konum)",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

        # Haritayı HTML dosyası olarak kaydet ve tarayıcıda aç
        map_path = os.path.abspath("drone_map.html")
        m.save(map_path)
        webbrowser.open(f"file://{map_path}")