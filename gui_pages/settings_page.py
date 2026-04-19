from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QGridLayout
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush, QPolygon, QPainterPath

class ArtificialHorizon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.roll = 0.0
        self.pitch = 0.0

    def set_attitude(self, roll, pitch):
        self.roll = roll
        self.pitch = pitch
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPoint(width // 2, height // 2)
        radius = min(width, height) // 2 - 10

        # Maskeleyerek dairesel bir alan içine çizim yapmak
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        painter.setClipPath(path)

        # Ufuk çizgisini (Sky and Ground) Roll (Yatış) açısına göre döndür
        painter.translate(center)
        painter.rotate(-self.roll)

        # Pitch (Yunuslama) açısına göre gökyüzü-yer ayrımını yukarı/aşağı kaydır
        pitch_scale = radius / 45.0  # 45 derecelik pitch radius uzunluğuna denk gelir (görsellik için ideal)
        pitch_offset = self.pitch * pitch_scale

        sky_color = QColor(41, 128, 185)   # Gökyüzü Mavi
        ground_color = QColor(139, 69, 19) # Toprak Kahverengi

        # Gökyüzü Çokgeni
        sky_poly = QPolygon([
            QPoint(-radius * 2, -radius * 2),
            QPoint(radius * 2, -radius * 2),
            QPoint(radius * 2, int(pitch_offset)),
            QPoint(-radius * 2, int(pitch_offset))
        ])
        
        # Yer Çokgeni
        ground_poly = QPolygon([
            QPoint(-radius * 2, int(pitch_offset)),
            QPoint(radius * 2, int(pitch_offset)),
            QPoint(radius * 2, radius * 2),
            QPoint(-radius * 2, radius * 2)
        ])

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(sky_color))
        painter.drawPolygon(sky_poly)

        painter.setBrush(QBrush(ground_color))
        painter.drawPolygon(ground_poly)

        # Yunuslama (Pitch) çizgileri (10'ar derecelik aralıklarla)
        painter.setPen(QPen(Qt.white, 2))
        for p in range(-60, 61, 10):
            if p == 0:
                # Tam ufuk çizgisi
                painter.setPen(QPen(Qt.green, 2))
                y = pitch_offset
                painter.drawLine(int(-radius), int(y), int(radius), int(y))
                painter.setPen(QPen(Qt.white, 2))
            else:
                y = p * pitch_scale + pitch_offset
                # 20 derecelik ana çizgiler geniş, 10 derecelik ara çizgiler daha dar
                line_width = radius * 0.4 if p % 20 == 0 else radius * 0.2
                painter.drawLine(int(-line_width/2), int(y), int(line_width/2), int(y))

        painter.rotate(self.roll)
        painter.translate(-center)

        # Kokpitteki sabit referans İHA simgesi (Ortadaki artı/kanat şekli)
        painter.setPen(QPen(Qt.red, 4))
        # Sol kanat çizgisi
        painter.drawLine(center.x() - int(radius*0.6), center.y(), center.x() - int(radius*0.2), center.y())
        # Sağ kanat çizgisi
        painter.drawLine(center.x() + int(radius*0.2), center.y(), center.x() + int(radius*0.6), center.y())
        # Kuyruk dikey çizgi
        painter.drawLine(center.x(), center.y(), center.x(), center.y() - int(radius*0.1))
        # Merkez nokta
        painter.setBrush(QBrush(Qt.red))
        painter.drawEllipse(center, 4, 4)
        
        # Dış Bezel/Çerçeve için maskelemeyi kaldır
        painter.setClipping(False)
        
        # Kadranın dış siyah askeri çerçevesi
        painter.setPen(QPen(QColor(40, 40, 40), 10))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius, radius)

class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # Başlık
        title = QLabel("SİSTEM PANELİ - İHA DONANIM VE UÇUŞ DURUMU")
        title.setObjectName("page_title")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Üç Sütunlu Yapı: Sol(İHA Görseli ve Motor/Batarya), Orta(Yapay Ufuk), Sağ(MFD Verileri)
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        self.indicators = {}

        def create_bar_indicator(parent_layout, label_text, bar_max=100, bar_color="#39ff14"):
            lbl_title = QLabel(label_text)
            lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #558b6e; margin-top: 10px;")
            parent_layout.addWidget(lbl_title)

            bar = QProgressBar()
            bar.setRange(0, bar_max)
            bar.setValue(0)
            bar.setTextVisible(True)
            bar.setStyleSheet(f"""
                QProgressBar {{ border: 1px solid {bar_color}; border-radius: 0px; background-color: #050907; color: {bar_color}; font-weight: bold; height: 18px; text-align: center; }}
                QProgressBar::chunk {{ background-color: {bar_color}; }}
            """)
            parent_layout.addWidget(bar)
            return bar

        def create_text_indicator(row, col, grid_layout, label_text):
            lbl_title = QLabel(label_text)
            lbl_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #558b6e;")
            grid_layout.addWidget(lbl_title, row, col)

            lbl_val = QLabel("N/A")
            lbl_val.setStyleSheet("font-size: 16px; font-weight: bold; color: #39ff14;")
            grid_layout.addWidget(lbl_val, row + 1, col)
            return lbl_val

        # --- SOL PANEL: İHA Görseli ve Temel Barlar ---
        left_panel = QFrame()
        left_panel.setObjectName("info_panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        
        self.drone_visual = QLabel()
        pixmap = QPixmap("ihossk.png")
        if not pixmap.isNull():
            # Resmi boyutlandırıp daha kibar hale getirdik
            self.drone_visual.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.drone_visual.setText("GÖRSEL BULUNAMADI\n(ihossk.png)")
            self.drone_visual.setStyleSheet("color: #ff003c; font-size: 14px; border: 1px dashed #ff003c; padding: 20px;")
        self.drone_visual.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.drone_visual)

        self.flight_mode_lbl = QLabel("UÇUŞ MODU: BİLİNMİYOR")
        self.flight_mode_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #39ff14; margin-top: 15px;")
        self.flight_mode_lbl.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.flight_mode_lbl)

        self.time_lbl = QLabel("GÖREV SÜRESİ: 00:00:00")
        self.time_lbl.setStyleSheet("font-size: 14px; color: #a2c4b0; margin-bottom: 15px;")
        self.time_lbl.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.time_lbl)

        self.indicators['battery'] = create_bar_indicator(left_layout, "BATARYA DURUMU", bar_max=100, bar_color="#ff003c")
        self.indicators['motor'] = create_bar_indicator(left_layout, "ANA MOTOR GÜCÜ", bar_max=1000, bar_color="#39ff14")
        
        left_layout.addStretch()
        content_layout.addWidget(left_panel, stretch=1)

        # --- ORTA PANEL: Yapay Ufuk (Attitude Indicator) ---
        center_panel = QFrame()
        center_panel.setObjectName("info_panel")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setAlignment(Qt.AlignCenter)
        
        center_title = QLabel("ATTITUDE INDICATOR\n(YAPAY UFUK)")
        center_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #558b6e; margin-bottom: 10px;")
        center_title.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(center_title)
        
        # 3D hissi verecek custom çizimli yapay ufuk widget'ımızı ekliyoruz
        self.horizon = ArtificialHorizon()
        center_layout.addWidget(self.horizon)
        
        content_layout.addWidget(center_panel, stretch=1)

        # --- SAĞ PANEL: Telemetri MFD Ekranı ---
        right_panel = QFrame()
        right_panel.setObjectName("info_panel")
        right_layout = QVBoxLayout(right_panel)

        mfd_title = QLabel("MULTIFUNCTION DISPLAY (MFD)")
        mfd_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #558b6e; margin-bottom: 15px;")
        mfd_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(mfd_title)

        grid = QGridLayout()
        grid.setSpacing(15)

        # Enerji
        self.indicators['amperage'] = create_text_indicator(0, 0, grid, "ANLIK AKIM (A)")
        self.indicators['energy'] = create_text_indicator(0, 1, grid, "TÜKETİM (mAh)")

        # Servolar
        self.indicators['servo0'] = create_text_indicator(2, 0, grid, "AİLERON (S0)")
        self.indicators['servo1'] = create_text_indicator(2, 1, grid, "ELEVATÖR (S1)")

        # Yönelim Açıları
        self.indicators['roll'] = create_text_indicator(4, 0, grid, "ROLL (°)")
        self.indicators['pitch'] = create_text_indicator(4, 1, grid, "PITCH (°)")
        self.indicators['yaw'] = create_text_indicator(6, 0, grid, "YAW (°)")

        # Çevre / Mesafe
        self.indicators['baro_alt'] = create_text_indicator(6, 1, grid, "BARO İRTİFA (cm)")
        self.indicators['dist_home'] = create_text_indicator(8, 0, grid, "EVE UZAKLIK (m)")
        self.indicators['dist_wp'] = create_text_indicator(8, 1, grid, "HEDEFE UZAK (m)")

        # Rüzgar
        self.indicators['wind_x'] = create_text_indicator(10, 0, grid, "RÜZGAR (X)")
        self.indicators['wind_y'] = create_text_indicator(10, 1, grid, "RÜZGAR (Y)")

        right_layout.addLayout(grid)
        right_layout.addStretch()

        content_layout.addWidget(right_panel, stretch=1)

    def update_sys_telemetry(self, data):
        # Zaman (Mikrosaniye -> Saniye dönüştür)
        try:
            sec = int(data.get('time (us)', 0) / 1e6)
            mins, secs = divmod(sec, 60)
            hours, mins = divmod(mins, 60)
            self.time_lbl.setText(f"GÖREV SÜRESİ: {hours:02d}:{mins:02d}:{secs:02d}")
        except:
            pass

        mode = data.get('Flight Mode', 'BİLİNMİYOR')
        self.flight_mode_lbl.setText(f"UÇUŞ MODU: {mode}")

        bat = float(data.get('Battery Remaining (%)', 0))
        self.indicators['battery'].setValue(int(bat))
        self.indicators['battery'].setFormat(f"%v%")

        self.indicators['amperage'].setText(f"{float(data.get('amperage (A)', 0)):.2f} A")
        self.indicators['energy'].setText(f"{int(data.get('energyCumulative (mAh)', 0))} mAh")

        motor_val = float(data.get('motor[0]', 0))
        self.indicators['motor'].setValue(int(motor_val))
        self.indicators['motor'].setFormat(f"%v PWM")

        self.indicators['servo0'].setText(f"{float(data.get('servo[0]', 0)):.1f}°")
        self.indicators['servo1'].setText(f"{float(data.get('servo[1]', 0)):.1f}°")

        roll = float(data.get('attitude[0]', 0))
        pitch = float(data.get('attitude[1]', 0))
        yaw = float(data.get('attitude[2]', 0))

        self.indicators['roll'].setText(f"{roll:.2f}°")
        self.indicators['pitch'].setText(f"{pitch:.2f}°")
        self.indicators['yaw'].setText(f"{yaw:.2f}°")

        # Yapay ufku (Artificial Horizon) güncelle
        self.horizon.set_attitude(roll, pitch)

        self.indicators['dist_home'].setText(f"{float(data.get('distance_to_home (m)', 0)):.1f} m")
        self.indicators['dist_wp'].setText(f"{float(data.get('distance_to_wp (m)', 0)):.1f} m")
        self.indicators['baro_alt'].setText(f"{float(data.get('BaroAlt (cm)', 0)):.1f} cm")

        self.indicators['wind_x'].setText(f"{float(data.get('wind[0]', 0)):.2f}")
        self.indicators['wind_y'].setText(f"{float(data.get('wind[1]', 0)):.2f}")