import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication, QSizePolicy, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl

class MapPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # HARİTA KONTEYNERI
        map_container = QFrame()
        map_container.setStyleSheet('border: 2px solid #1a3c28; background: #050907; border-radius: 0px;')
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(2, 2, 2, 2)
        map_layout.setSpacing(0)

        header_label = QLabel("SİPER TAKTİK HARİTA (AI-SENSÖR FÜZYONU)")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #39ff14; font-family: Consolas; padding: 10px; border-bottom: 1px solid #1a3c28;")
        map_layout.addWidget(header_label)

        self.map_view = QWebEngineView()
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.map_view.loadFinished.connect(self.on_map_loaded)
        self.map_ready = False
        self.load_yandex_map()

        map_layout.addWidget(self.map_view, stretch=1)
        main_layout.addWidget(map_container, stretch=4)

        # SAĞ TAKTİK PANEL
        self.panel = QFrame()
        self.panel.setFixedWidth(320)
        self.panel.setStyleSheet('border: 2px solid #1a3c28; background: #050907; border-radius: 0px;')
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        panel_layout.setSpacing(20)

        panel_title = QLabel("NAVİGASYON KIYASLAMA")
        panel_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #39ff14; border-bottom: 1px solid #1a3c28; padding-bottom: 5px;")
        panel_layout.addWidget(panel_title)

        # GPS Verisi (Ham)
        gps_frame = QFrame()
        gps_frame.setStyleSheet('border: 1px solid #ff003c; background: #1a0505;')
        gps_layout = QVBoxLayout(gps_frame)
        gps_layout.addWidget(QLabel("📡 UYDU GPS (HAM)"))
        self.lbl_real_coord = QLabel("N/A, N/A")
        self.lbl_real_coord.setStyleSheet("color: #ff003c; font-weight: bold;")
        gps_layout.addWidget(self.lbl_real_coord)
        panel_layout.addWidget(gps_frame)

        # AI Verisi (Güvenli)
        ai_frame = QFrame()
        ai_frame.setStyleSheet('border: 1px solid #00aaff; background: #050a1a;')
        ai_layout = QVBoxLayout(ai_frame)
        ai_layout.addWidget(QLabel("🛡️ SİPER AI (HAYALET)"))
        self.lbl_ai_coord = QLabel("N/A, N/A")
        self.lbl_ai_coord.setStyleSheet("color: #00aaff; font-weight: bold;")
        ai_layout.addWidget(self.lbl_ai_coord)
        panel_layout.addWidget(ai_frame)

        panel_layout.addStretch()
        main_layout.addWidget(self.panel)

    def load_yandex_map(self):
        lat, lon = 38.7312, 35.4787
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <script src="https://api-maps.yandex.ru/2.1/?lang=tr_TR"></script>
            <style>
                html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; background: #050907; }}
                #map {{ filter: brightness(0.7) contrast(1.2) saturate(0.5); }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map, realDrone, ghostDrone;
                function init() {{
                    map = new ymaps.Map('map', {{
                        center: [{lat}, {lon}], zoom: 17,
                        controls: []
                    }});
                    map.setType('yandex#hybrid');

                    // Gerçek GPS İkonu (Kırmızı)
                    realDrone = new ymaps.Placemark([{lat}, {lon}], {{
                        hintContent: 'UYDU GPS'
                    }}, {{ preset: 'islands#redCircleDotIcon' }});

                    // AI Hayalet İkonu (Mavi)
                    ghostDrone = new ymaps.Placemark([{lat}, {lon}], {{
                        hintContent: 'SİPER HAYALET'
                    }}, {{ preset: 'islands#blueCircleDotIcon' }});

                    map.geoObjects.add(realDrone).add(ghostDrone);
                }}

                function updatePositions(rLat, rLon, gLat, gLon) {{
                    if (!map) return;
                    realDrone.geometry.setCoordinates([rLat, rLon]);
                    ghostDrone.geometry.setCoordinates([gLat, gLon]);
                    map.setCenter([gLat, gLon], map.getZoom(), {{ duration: 300 }});
                }}
                ymaps.ready(init);
            </script>
        </body>
        </html>
        """
        self.map_view.setHtml(html_content, QUrl('https://yandex.com'))

    def on_map_loaded(self, ok):
        self.map_ready = ok

    def update_drone_comparison(self, rLat, rLon, gLat, gLon):
        self.lbl_real_coord.setText(f"{rLat:.6f}\n{rLon:.6f}")
        self.lbl_ai_coord.setText(f"{gLat:.6f}\n{gLon:.6f}")
        
        if self.map_ready:
            self.map_view.page().runJavaScript(f"updatePositions({rLat}, {rLon}, {gLat}, {gLon});")