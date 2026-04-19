import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication, QSizePolicy, QFrame, QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl

class MapPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        # Ana yatay düzen (Sol: Harita, Sağ: Taktik Panel)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # ==========================================
        # SOL TARAF: HARİTA MODÜLÜ
        # ==========================================
        map_container = QFrame()
        map_container.setStyleSheet('border: 2px solid #1a3c28; background: #050907; border-radius: 0px;')
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(2, 2, 2, 2)
        map_layout.setSpacing(0)

        header_label = QLabel("TAKTİK UYDU GÖRÜNTÜSÜ (SAT-NAV)")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #39ff14; font-family: Consolas; padding: 10px; border-bottom: 1px solid #1a3c28;")
        map_layout.addWidget(header_label)

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
            self.map_view = QLabel("Harita motoru başlatılamadı.")
            self.map_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.map_view.setStyleSheet("font-size: 16px; color: #ff003c; font-family: Consolas;")

        map_layout.addWidget(self.map_view, stretch=1)
        main_layout.addWidget(map_container, stretch=4) # Harita ekranın %75-80'ini kaplasın

        # ==========================================
        # SAĞ TARAF: TAKTİK BİLGİ PANELİ
        # ==========================================
        self.panel = QFrame()
        self.panel.setFixedWidth(320)
        self.panel.setStyleSheet('border: 2px solid #1a3c28; background: #050907; border-radius: 0px;')
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        panel_layout.setSpacing(20)

        panel_title = QLabel("SİHA NAVİGASYON VERİSİ")
        panel_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #39ff14; font-family: Consolas; border: none; border-bottom: 1px solid #1a3c28; padding-bottom: 5px;")
        panel_layout.addWidget(panel_title)

        # Koordinat Kartı
        coord_frame = QFrame()
        coord_frame.setStyleSheet('border: 1px solid #1a3c28; background: #08100c;')
        coord_layout = QVBoxLayout(coord_frame)
        coord_layout.setContentsMargins(12, 12, 12, 12)
        coord_layout.setSpacing(8)

        lbl_coord_title = QLabel("ANLIK KOORDİNATLAR")
        lbl_coord_title.setStyleSheet("color: #558b6e; font-size: 12px; font-weight: bold; border: none;")
        coord_layout.addWidget(lbl_coord_title)

        self.lbl_lat = QLabel("ENLEM : N/A")
        self.lbl_lon = QLabel("BOYLAM: N/A")
        self.lbl_lat.setStyleSheet("color: #39ff14; font-size: 14px; font-weight: bold; font-family: Consolas; border: none;")
        self.lbl_lon.setStyleSheet("color: #39ff14; font-size: 14px; font-weight: bold; font-family: Consolas; border: none;")
        coord_layout.addWidget(self.lbl_lat)
        coord_layout.addWidget(self.lbl_lon)

        panel_layout.addWidget(coord_frame)

        # Uçuş Durumu Kartı
        status_frame = QFrame()
        status_frame.setStyleSheet('border: 1px solid #1a3c28; background: #08100c;')
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(8)

        lbl_status_title = QLabel("GÖREV DURUMU")
        lbl_status_title.setStyleSheet("color: #558b6e; font-size: 12px; font-weight: bold; border: none;")
        status_layout.addWidget(lbl_status_title)

        self.lbl_mode = QLabel("MOD: OTONOM UÇUŞ")
        self.lbl_link = QLabel("VERİ BAĞI: AKTİF")
        self.lbl_gps = QLabel("GPS: KİLİTLENDİ (3D FIX)")
        
        for lbl in [self.lbl_mode, self.lbl_link, self.lbl_gps]:
            lbl.setStyleSheet("color: #39ff14; font-size: 13px; font-weight: bold; font-family: Consolas; border: none;")
            status_layout.addWidget(lbl)

        panel_layout.addWidget(status_frame)

        # Modüler Genişleme Alanı (Gelecekte arkadaşınızın ekleme yapabileceği yer)
        expansion_frame = QFrame()
        expansion_frame.setStyleSheet('border: 1px dashed #1a3c28; background: transparent;')
        expansion_layout = QVBoxLayout(expansion_frame)
        expansion_layout.setContentsMargins(12, 12, 12, 12)
        
        lbl_exp = QLabel("[ BOŞ SLOT ]\n\nBu alana eklenecek yeni modüller,\nhedef tespit sistemi, kamera\nakışı veya silah yönetim\npaneli için ayrılmıştır.")
        lbl_exp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_exp.setStyleSheet("color: #2b543b; font-size: 11px; font-weight: bold; font-family: Consolas; border: none;")
        expansion_layout.addWidget(lbl_exp)

        panel_layout.addWidget(expansion_frame, stretch=1)

        main_layout.addWidget(self.panel)


    def load_yandex_map(self):
        lat, lon = 38.7312, 35.4787
        # Karanlık askeri tema ve custom marker eklenmiş HTML yapısı
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
                    background-color: #050907;
                }}
                #map {{
                    width: 100%;
                    height: 100%;
                    /* Ufak bir yeşilimsi askeri filtre filtresi katabiliriz: */
                    filter: sepia(0.2) hue-rotate(90deg) saturate(1.5) contrast(1.2) brightness(0.8);
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
                        zoom: 16,
                        controls: ['zoomControl', 'typeSelector', 'fullscreenControl']
                    }});
                    
                    // Harita tipini uydu (hybrid) yapalım ki daha askeri dursun
                    map.setType('yandex#hybrid');

                    dronePlacemark = new ymaps.Placemark([
                        {lat}, {lon}
                    ], {{
                        balloonContent: '<b>⚔️ SİPER T-SİHA</b><br>Durum: Havadar'
                    }}, {{
                        preset: 'islands#redIcon'
                    }});
                    map.geoObjects.add(dronePlacemark);
                }}

                function updateDrone(lat, lon) {{
                    if (!map || !dronePlacemark) return;
                    dronePlacemark.geometry.setCoordinates([lat, lon]);
                    map.setCenter([lat, lon], 16, {{ duration: 300 }});
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
        # Arayüz panelindeki koordinatları güncelle
        self.lbl_lat.setText(f"ENLEM : {lat:.6f}")
        self.lbl_lon.setText(f"BOYLAM: {lon:.6f}")

        # Haritadaki imleci güncelle
        if not getattr(self, 'map_ready', False):
            return
        js = f"updateDrone({lat}, {lon});"
        self.map_view.page().runJavaScript(js)
