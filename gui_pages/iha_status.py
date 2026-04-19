from math import cos, sin, pi
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont


class GaugeCanvas(QWidget):
    def __init__(self, accent: str, min_value=0, max_value=100, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.min_value = min_value
        self.max_value = max_value
        self.value = None
        self.setMinimumSize(200, 200)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
            rect = self.rect().adjusted(14, 14, -14, -14)
            radius = min(rect.width(), rect.height()) / 2
            center = QPointF(rect.center())

            # Background ring (HUD style)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#050907'))
            painter.drawEllipse(center, radius, radius)

            # Base track ring
            track_pen = QPen(QColor('#1a3c28'), 4)
            track_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(track_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius - 8, radius - 8)

            # Value arc
            if self.value is not None and self.max_value != self.min_value:
                fraction = (float(self.value) - self.min_value) / float(self.max_value - self.min_value)
                fraction = max(0.0, min(1.0, fraction))
            else:
                fraction = 0.0

            arc_pen = QPen(QColor(self.accent), 4)
            arc_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(arc_pen)
            arc_rect = QRectF(center.x() - radius + 8, center.y() - radius + 8, 2 * (radius - 8), 2 * (radius - 8))
            start_angle = 90 * 16
            span_angle = -int(360 * 16 * fraction)
            painter.drawArc(arc_rect, start_angle, span_angle)

            # Tactical tick marks
            tick_pen = QPen(QColor('#1a3c28'), 2)
            painter.setPen(tick_pen)
            for i in range(12):
                angle = (360 / 12) * i
                rad = angle * pi / 180.0
                x1 = center.x() + (radius - 15) * cos(rad)
                y1 = center.y() + (radius - 15) * sin(rad)
                x2 = center.x() + (radius - 5) * cos(rad)
                y2 = center.y() + (radius - 5) * sin(rad)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        finally:
            painter.end()


class CircularGaugeCard(QFrame):
    def __init__(self, title: str, field: str, unit: str, accent: str, min_value=0, max_value=100):
        super().__init__()
        self.field = field
        self.canvas = GaugeCanvas(accent, min_value, max_value)
        self.setObjectName('gauge_card')
        self.setStyleSheet('border: 1px solid #1a3c28; background: #050907; border-radius: 0px;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #558b6e; font-size: 13px; font-weight: bold; border: none;')
        title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel('N/A')
        self.value_label.setStyleSheet(f'color: {accent}; font-size: 22px; font-weight: bold; font-family: Consolas; border: none;')
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setMinimumWidth(80) # Sabit genişlik ki büyüme yapmasın

        unit_label = QLabel(unit)
        unit_label.setStyleSheet('color: #558b6e; font-size: 11px; border: none;')
        unit_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.value_label)
        layout.addWidget(unit_label)

    def setValue(self, value):
        if value is None or value == 'N/A':
            self.value_label.setText('N/A')
            self.canvas.setValue(0)
            return

        try:
            numeric = float(value)
            self.value_label.setText(f'{numeric:.1f}')
            self.canvas.setValue(numeric)
        except (ValueError, TypeError):
            self.value_label.setText(str(value)[:6])
            self.canvas.setValue(0)


class IhaStatusPage(QWidget):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.gauges = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        header = QLabel('TAKTİK UÇUŞ VE SENSÖR TELEMETRİSİ (UAV-HUD)')
        header.setObjectName('page_title')
        header.setStyleSheet('font-size: 20px; color: #39ff14; font-weight: bold; font-family: Consolas; letter-spacing: 2px;')
        main_layout.addWidget(header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('QScrollArea { background-color: transparent; border: none; } QWidget { background-color: transparent; }')

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(0, 0, 0, 0)

        container_layout.addWidget(self.create_instruments_panel(), 2)
        container_layout.addWidget(self.create_system_panel(), 3)

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    def create_instruments_panel(self):
        panel = QFrame()
        panel.setObjectName('info_panel')
        panel.setStyleSheet('border: 2px solid #1a3c28; background: #050907; border-radius: 0px;')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        title = QLabel('PRİMER UÇUŞ GÖSTERGELERİ (PFD)')
        title.setStyleSheet('color: #39ff14; font-size: 15px; font-weight: bold; border: none; border-bottom: 1px solid #1a3c28; padding-bottom: 5px;')
        layout.addWidget(title)

        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(10)
        gauge_row.addWidget(self.create_gauge_card('YER HIZI (GS)', 'GPS_ground_speed', 'm/s', '#39ff14', min_value=0, max_value=90))
        gauge_row.addWidget(self.create_gauge_card('İRTİFA (ALT)', 'GPS_altitude', 'm', '#39ff14', min_value=0, max_value=1500))
        layout.addLayout(gauge_row)

        gauge_row_2 = QHBoxLayout()
        gauge_row_2.setSpacing(10)
        gauge_row_2.addWidget(self.create_gauge_card('ROTA (HDG)', 'GPS_ground_course', '°', '#39ff14', min_value=0, max_value=360))
        gauge_row_2.addWidget(self.create_gauge_card('DİKEY HIZ (VS)', 'verticalSpeed', 'm/s', '#39ff14', min_value=-20, max_value=20))
        layout.addLayout(gauge_row_2)

        return panel

    def create_system_panel(self):
        panel = QFrame()
        panel.setObjectName('info_panel')
        panel.setStyleSheet('border: 2px solid #1a3c28; background: #050907; border-radius: 0px;')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        title = QLabel('SİSTEM TELEMETRİSİ (EICAS)')
        title.setStyleSheet('color: #39ff14; font-size: 15px; font-weight: bold; border: none; border-bottom: 1px solid #1a3c28; padding-bottom: 5px;')
        layout.addWidget(title)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.addWidget(self.create_status_card('GPS HDOP', 'GPS_hdop', '---', '#39ff14'))
        top_row.addWidget(self.create_status_card('UYDU SAYISI', 'GPS_numSat', 'ADET', '#39ff14'))
        top_row.addWidget(self.create_status_card('UÇUŞ MODU', 'navState', '', '#ff003c'))
        top_row.addWidget(self.create_status_card('AKTİF WP', 'activeWpNumber', '', '#39ff14'))
        layout.addLayout(top_row)

        nav_panel = QFrame()
        nav_panel.setStyleSheet('border: 1px solid #1a3c28; background: #08100c; border-radius: 0px;')
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(10)

        nav_title = QLabel('NAVİGASYON VE GÜÇ BİLGİLERİ')
        nav_title.setStyleSheet('color: #558b6e; font-size: 13px; font-weight: bold; border: none;')
        nav_layout.addWidget(nav_title)

        nav_grid = QGridLayout()
        nav_grid.setSpacing(10)
        nav_grid.addWidget(self.create_status_card('KOORDİNAT X', 'GPS_coord[0]', '°', '#39ff14'), 0, 0)
        nav_grid.addWidget(self.create_status_card('KOORDİNAT Y', 'GPS_coord[1]', '°', '#39ff14'), 0, 1)
        nav_grid.addWidget(self.create_status_card('BATARYA', 'vbat', 'V', '#39ff14'), 0, 2)
        
        nav_grid.addWidget(self.create_status_card('HEDEF X', 'navTgtPos[0]', 'm', '#39ff14'), 1, 0)
        nav_grid.addWidget(self.create_status_card('HEDEF Y', 'navTgtPos[1]', 'm', '#39ff14'), 1, 1)
        nav_grid.addWidget(self.create_status_card('ESC ISI', 'escTemperature', '°C', '#f8b229'), 1, 2)
        nav_layout.addLayout(nav_grid)

        layout.addWidget(nav_panel)

        sensor_panel = QFrame()
        sensor_panel.setStyleSheet('border: 1px solid #1a3c28; background: #08100c; border-radius: 0px;')
        sensor_layout = QVBoxLayout(sensor_panel)
        sensor_layout.setContentsMargins(12, 12, 12, 12)
        sensor_layout.setSpacing(10)

        sensor_title = QLabel('SENSÖR OKUMALARI (IMU / MAG)')
        sensor_title.setStyleSheet('color: #558b6e; font-size: 13px; font-weight: bold; border: none;')
        sensor_layout.addWidget(sensor_title)

        sensor_grid = QGridLayout()
        sensor_grid.setSpacing(10)
        sensors = [
            ('accSmooth[0]', 'İVME X', '#39ff14'),
            ('accSmooth[1]', 'İVME Y', '#39ff14'),
            ('accSmooth[2]', 'İVME Z', '#39ff14'),
            ('gyroADC[0]', 'GYRO X', '#39ff14'),
            ('gyroADC[1]', 'GYRO Y', '#39ff14'),
            ('gyroADC[2]', 'GYRO Z', '#39ff14'),
            ('magADC[0]', 'MAG X', '#39ff14'),
            ('magADC[1]', 'MAG Y', '#39ff14'),
            ('magADC[2]', 'MAG Z', '#39ff14')
        ]

        for i, (field, title_text, color) in enumerate(sensors):
            card = self.create_status_card(title_text, field, '', color)
            sensor_grid.addWidget(card, i // 3, i % 3)

        sensor_layout.addLayout(sensor_grid)
        layout.addWidget(sensor_panel)

        return panel

    def create_gauge_card(self, title, field, unit, accent, min_value=0, max_value=100):
        card = CircularGaugeCard(title, field, unit, accent, min_value=min_value, max_value=max_value)
        self.values[field] = card.value_label
        self.gauges[field] = card
        return card

    def create_status_card(self, title, field, unit, accent):
        card = QFrame()
        card.setObjectName('status_card')
        card.setStyleSheet('border: 1px solid #1a3c28; background: #050907; border-radius: 0px;')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #558b6e; font-size: 11px; border: none;')
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel('N/A')
        value_label.setObjectName(f'value_{field}')
        value_label.setStyleSheet(f'color: {accent}; font-size: 16px; font-weight: bold; font-family: Consolas; border: none;')
        value_label.setAlignment(Qt.AlignCenter)
        # Layout kaymasını engellemek için minimum width ayarlıyoruz
        value_label.setMinimumWidth(80) 

        unit_label = QLabel(unit)
        unit_label.setStyleSheet('color: #558b6e; font-size: 10px; border: none;')
        unit_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        # Sadece birim varsa ekle (Arayüzde boşluk kaplamasın)
        if unit:
            layout.addWidget(unit_label)
            
        self.values[field] = value_label
        return card

    def update_telemetry(self, telemetry: dict):
        for field, label in self.values.items():
            if field in self.gauges:
                if field in telemetry:
                    self.gauges[field].setValue(telemetry.get(field))
                else:
                    self.gauges[field].setValue(None)

            if field in telemetry:
                val = telemetry.get(field)
                if isinstance(val, float):
                    label.setText(f"{val:.2f}")
                else:
                    label.setText(str(val))
            else:
                label.setText('N/A')
