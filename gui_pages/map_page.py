import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl

class MapPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.info_label = QLabel("🌍 Dinamik Harita Modülü")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.info_label)

        # QApplication kontrolü ile QWebEngineView oluştur
        if QApplication.instance() is not None:
            self.map_view = QWebEngineView()
            self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.map_view.page().profile().setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            self.map_view.loadFinished.connect(self.on_map_loaded)
            self.map_ready = False
            self.load_yandex_map()
        else:
            self.map_view = QLabel("Harita yüklenemedi: QApplication gerekli")
            self.map_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.map_view.setStyleSheet("font-size: 18px; color: red;")

        layout.addWidget(self.map_view, stretch=1)

        # Açıklama etiketi
        self.desc_label = QLabel("Yandex Maps tabanlı canlı harita. Drone konumu dinamik olarak güncellenecek.")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("font-size: 14px; color: #7f8c8d; margin-top: 10px;")
        layout.addWidget(self.desc_label)

    def load_yandex_map(self):
        lat, lon = 38.7312, 35.4787
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>EFES Yandex Harita</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <style>
                html, body {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
                #map {{
                    width: 100%;
                    height: 100%;
                }}
            </style>
            <script src="https://api-maps.yandex.ru/2.1/?lang=tr_TR"></script>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map;
                var dronePlacemark;
                function init() {{
                    map = new ymaps.Map('map', {{
                        center: [{lat}, {lon}],
                        zoom: 15,
                        controls: ['zoomControl', 'fullscreenControl']
                    }});
                    dronePlacemark = new ymaps.Placemark([
                        {lat}, {lon}
                    ], {{
                        balloonContent: '🦅 EFES Drone (Anlık Konum)'
                    }}, {{
                        preset: 'islands#redIcon'
                    }});
                    map.geoObjects.add(dronePlacemark);
                }}

                function updateDrone(lat, lon) {{
                    if (!map || !dronePlacemark) return;
                    dronePlacemark.geometry.setCoordinates([lat, lon]);
                    map.setCenter([lat, lon], 15, {{ duration: 300 }});
                }}

                ymaps.ready(init);
            </script>
        </body>
        </html>
        """
        self.map_view.setHtml(html_content, QUrl('https://yandex.com'))

    def on_map_loaded(self, ok):
        self.map_ready = ok

    def update_drone(self, lat, lon):
        if not getattr(self, 'map_ready', False):
            return
        js = f"updateDrone({lat}, {lon});"
        self.map_view.page().runJavaScript(js)
