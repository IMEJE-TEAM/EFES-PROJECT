from math import cos, sin, pi
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QScrollArea
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont


class GaugeCanvas(QWidget):
    def __init__(self, accent: str, min_value=0, max_value=100, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.min_value = min_value
        self.max_value = max_value
        self.value = None
        self.setMinimumSize(240, 240)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        rect = self.rect().adjusted(14, 14, -14, -14)
        radius = min(rect.width(), rect.height()) / 2
        center = QPointF(rect.center())

        # Background ring
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#121418'))
        painter.drawEllipse(center, radius, radius)

        # Base track ring
        track_pen = QPen(QColor('#2e3540'), 12)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius - 8, radius - 8)

        # Value arc
        if self.value is not None and self.max_value != self.min_value:
            fraction = (float(self.value) - self.min_value) / float(self.max_value - self.min_value)
            fraction = max(0.0, min(1.0, fraction))
        else:
            fraction = 0.0

        arc_pen = QPen(QColor(self.accent), 12)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)
        arc_rect = QRectF(center.x() - radius + 8, center.y() - radius + 8, 2 * (radius - 8), 2 * (radius - 8))
        start_angle = 90 * 16
        span_angle = -int(360 * 16 * fraction)
        painter.drawArc(arc_rect, start_angle, span_angle)

        # Center guide lines
        guide_pen = QPen(QColor('#4a5566'), 1)
        painter.setPen(guide_pen)
        for i in range(8):
            angle = (360 / 8) * i
            rad = angle * pi / 180.0
            x1 = center.x() + (radius - 20) * 0.88 * cos(rad)
            y1 = center.y() + (radius - 20) * 0.88 * sin(rad)
            x2 = center.x() + (radius - 20) * cos(rad)
            y2 = center.y() + (radius - 20) * sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class CircularGaugeCard(QFrame):
    def __init__(self, title: str, field: str, unit: str, accent: str, min_value=0, max_value=100):
        super().__init__()
        self.field = field
        self.canvas = GaugeCanvas(accent, min_value, max_value)
        self.setObjectName('gauge_card')
        self.setStyleSheet('border: 1px solid #4a0f12; background: #0d1014; border-radius: 18px;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #9aa2b1; font-size: 13px; font-weight: bold;')
        title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel('N/A')
        self.value_label.setStyleSheet('color: #f0f0f0; font-size: 24px; font-weight: bold;')
        self.value_label.setAlignment(Qt.AlignCenter)

        unit_label = QLabel(unit)
        unit_label.setStyleSheet('color: #6b6f76; font-size: 11px;')
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
            self.value_label.setText(str(value))
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
        main_layout.setSpacing(18)

        header = QLabel('İHA DURUM PANELİ')
        header.setObjectName('page_title')
        header.setStyleSheet('font-size: 24px; color: #8afe8a; font-weight: bold;')
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
        panel.setStyleSheet('border: 1px solid #4a0f12; background: #121212; border-radius: 18px;')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        title = QLabel('KOKPİT GÖSTERGELERİ')
        title.setStyleSheet('color: #8afe8a; font-size: 16px; font-weight: bold;')
        layout.addWidget(title)

        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(16)
        gauge_row.addWidget(self.create_gauge_card('Hız', 'GPS_ground_speed', 'm/s', '#8afe8a', min_value=0, max_value=90))
        gauge_row.addWidget(self.create_gauge_card('İrtifa', 'GPS_altitude', 'm', '#f8b229', min_value=0, max_value=1500))
        layout.addLayout(gauge_row)

        gauge_row_2 = QHBoxLayout()
        gauge_row_2.setSpacing(16)
        gauge_row_2.addWidget(self.create_gauge_card('Yön', 'GPS_ground_course', '°', '#db2508', min_value=0, max_value=360))
        gauge_row_2.addWidget(self.create_gauge_card('Dikey Hız', 'verticalSpeed', 'm/s', '#20d3a5', min_value=-20, max_value=20))
        layout.addLayout(gauge_row_2)

        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        status_row.addWidget(self.create_status_card('GPS HDOP', 'GPS_hdop', '---', '#8afe8a'))
        status_row.addWidget(self.create_status_card('Uydu Sayısı', 'GPS_numSat', 'adet', '#f8b229'))
        status_row.addWidget(self.create_status_card('Nav Durumu', 'navState', '', '#db2508'))
        layout.addLayout(status_row)

        coord_row = QHBoxLayout()
        coord_row.setSpacing(12)
        coord_row.addWidget(self.create_status_card('Koordinat X', 'GPS_coord[0]', '°', '#8b8fff'))
        coord_row.addWidget(self.create_status_card('Koordinat Y', 'GPS_coord[1]', '°', '#8b8fff'))
        layout.addLayout(coord_row)

        return panel

    def create_system_panel(self):
        panel = QFrame()
        panel.setObjectName('info_panel')
        panel.setStyleSheet('border: 1px solid #4a0f12; background: #121212; border-radius: 18px;')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        title = QLabel('SİSTEM DURUMU')
        title.setStyleSheet('color: #8afe8a; font-size: 16px; font-weight: bold;')
        layout.addWidget(title)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self.create_status_card('ESC Sıcaklık', 'escTemperature', '°C', '#f8b229'))
        top_row.addWidget(self.create_status_card('Batarya', 'vbat', 'V', '#18b6ff'))
        top_row.addWidget(self.create_status_card('Sinyal', 'rssi', 'dBm', '#db2508'))
        top_row.addWidget(self.create_status_card('Waypoint', 'activeWpNumber', '', '#8afe8a'))
        layout.addLayout(top_row)

        nav_panel = QFrame()
        nav_panel.setStyleSheet('border: 1px solid #23282f; background: #0f1218; border-radius: 16px;')
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(16, 16, 16, 16)
        nav_layout.setSpacing(10)

        nav_title = QLabel('HAREKET & NAVİGASYON')
        nav_title.setStyleSheet('color: #8afe8a; font-size: 14px; font-weight: bold;')
        nav_layout.addWidget(nav_title)

        nav_grid = QGridLayout()
        nav_grid.setSpacing(12)
        nav_grid.addWidget(self.create_status_card('Hedef X', 'navTgtPos[0]', 'm', '#db2508'), 0, 0)
        nav_grid.addWidget(self.create_status_card('Hedef Y', 'navTgtPos[1]', 'm', '#db2508'), 0, 1)
        nav_grid.addWidget(self.create_status_card('Hedef Z', 'navTgtPos[2]', 'm', '#db2508'), 0, 2)
        nav_grid.addWidget(self.create_status_card('Hız X', 'navVel[0]', 'm/s', '#8b8fff'), 1, 0)
        nav_grid.addWidget(self.create_status_card('Hız Y', 'navVel[1]', 'm/s', '#8b8fff'), 1, 1)
        nav_grid.addWidget(self.create_status_card('Hız Z', 'navVel[2]', 'm/s', '#8b8fff'), 1, 2)
        nav_layout.addLayout(nav_grid)

        layout.addWidget(nav_panel)

        sensor_panel = QFrame()
        sensor_panel.setStyleSheet('border: 1px solid #23282f; background: #0f1218; border-radius: 16px;')
        sensor_layout = QVBoxLayout(sensor_panel)
        sensor_layout.setContentsMargins(16, 16, 16, 16)
        sensor_layout.setSpacing(12)

        sensor_title = QLabel('SENSÖR TELEMETRİSİ')
        sensor_title.setStyleSheet('color: #8afe8a; font-size: 14px; font-weight: bold;')
        sensor_layout.addWidget(sensor_title)

        sensor_grid = QGridLayout()
        sensor_grid.setSpacing(12)
        sensors = [
            ('accSmooth[0]', 'İvme X', '#db2508'),
            ('accSmooth[1]', 'İvme Y', '#db2508'),
            ('accSmooth[2]', 'İvme Z', '#db2508'),
            ('gyroADC[0]', 'Jiroskop X', '#8b8fff'),
            ('gyroADC[1]', 'Jiroskop Y', '#8b8fff'),
            ('gyroADC[2]', 'Jiroskop Z', '#8b8fff'),
            ('magADC[0]', 'Manyetik X', '#20d3a5'),
            ('magADC[1]', 'Manyetik Y', '#20d3a5'),
            ('magADC[2]', 'Manyetik Z', '#20d3a5')
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
        card.setStyleSheet('border: 1px solid #2a3038; background: #0d1014; border-radius: 14px;')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #9aa2b1; font-size: 12px;')
        value_label = QLabel('N/A')
        value_label.setObjectName(f'value_{field}')
        value_label.setStyleSheet(f'color: {accent}; font-size: 20px; font-weight: bold;')
        unit_label = QLabel(unit)
        unit_label.setStyleSheet('color: #6b6f76; font-size: 11px;')

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(unit_label)
        self.values[field] = value_label
        return card

    def create_value_meter(self, title, field, accent):
        card = QFrame()
        card.setObjectName('meter_card')
        card.setStyleSheet('border: 1px solid #272a30; background: #0f1218; border-radius: 12px;')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #7f8b99; font-size: 11px;')
        value_label = QLabel('N/A')
        value_label.setObjectName(f'value_{field}')
        value_label.setStyleSheet(f'color: {accent}; font-size: 18px; font-weight: bold;')
        bar = QFrame()
        bar.setFixedHeight(8)
        bar.setStyleSheet('background: #15181f; border-radius: 4px;')
        fill = QFrame(bar)
        fill.setGeometry(0, 0, 0, 8)
        fill.setStyleSheet(f'background: {accent}; border-radius: 4px;')

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(bar)
        self.values[field] = value_label
        return card

    def create_horizon_card(self):
        card = QFrame()
        card.setObjectName('horizon_card')
        card.setStyleSheet('border: 1px solid #4a0f12; background: #0d1014; border-radius: 14px;')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title_label = QLabel('YAPAY UFUK')
        title_label.setStyleSheet('color: #9aa2b1; font-size: 12px;')
        indicator = QFrame()
        indicator.setFixedHeight(140)
        indicator.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1d252f, stop:1 #0d1014); border: 1px solid #3f5361; border-radius: 12px;')
        horizon = QLabel("<div style='width:100%;height:100%;position:relative;'>"
                         "<div style='position:absolute;top:10%;left:0;width:100%;height:1px;background:#2f7c42;'></div>"
                         "<div style='position:absolute;top:40%;left:0;width:100%;height:1px;background:#2f7c42;'></div>"
                         "<div style='position:absolute;top:60%;left:0;width:100%;height:1px;background:#2f7c42;'></div>"
                         "<div style='position:absolute;top:90%;left:0;width:100%;height:1px;background:#2f7c42;'></div>"
                         "<div style='position:absolute;left:50%;top:45%;width:90px;height:2px;background:#db2508;transform:translateX(-50%);'></div>"
                         "</div>")
        horizon.setTextFormat(Qt.RichText)
        horizon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator_layout = QVBoxLayout(indicator)
        indicator_layout.setContentsMargins(6, 6, 6, 6)
        indicator_layout.addWidget(horizon)

        roll_label = QLabel('Roll: N/A')
        pitch_label = QLabel('Pitch: N/A')
        roll_label.setStyleSheet('color: #c4c4c4; font-size: 12px;')
        pitch_label.setStyleSheet('color: #c4c4c4; font-size: 12px;')

        layout.addWidget(title_label)
        layout.addWidget(indicator)
        layout.addWidget(roll_label)
        layout.addWidget(pitch_label)
        return card

    def update_telemetry(self, telemetry: dict):
        for field, label in self.values.items():
            if field in self.gauges:
                if field in telemetry:
                    self.gauges[field].setValue(telemetry.get(field))
                else:
                    self.gauges[field].setValue(None)

            if field in telemetry:
                label.setText(str(telemetry.get(field, 'N/A')))
            else:
                label.setText('N/A')
