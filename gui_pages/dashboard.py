from math import cos, sin, pi
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen

class RadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(40)
        self.setMinimumSize(220, 220)

    def rotate(self):
        self.angle = (self.angle + 3) % 360
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
            rect = self.rect().adjusted(10, 10, -10, -10)
            center = QPointF(rect.center())
            radius = min(rect.width(), rect.height()) / 2 - 10

            painter.setBrush(QColor('#081011'))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius + 10, radius + 10)

            grid_pen = QPen(QColor('#1f354c'), 2)
            painter.setPen(grid_pen)
            painter.setBrush(Qt.NoBrush)
            for ring in range(1, 5):
                painter.drawEllipse(center, radius / 5 * ring, radius / 5 * ring)
            painter.drawLine(QPointF(center.x() - radius, center.y()), QPointF(center.x() + radius, center.y()))
            painter.drawLine(QPointF(center.x(), center.y() - radius), QPointF(center.x(), center.y() + radius))

            painter.setPen(QPen(QColor('#224362'), 1))
            for i in range(0, 360, 30):
                angle = i * pi / 180.0
                x = center.x() + radius * 0.96 * cos(angle)
                y = center.y() + radius * 0.96 * sin(angle)
                painter.drawLine(center, QPointF(x, y))

            sweep_pen = QPen(QColor('#26f7a4'))
            sweep_pen.setWidth(3)
            painter.setPen(sweep_pen)
            painter.setBrush(QColor(38, 247, 164, 60))
            painter.drawPie(rect, int((90 - self.angle - 30) * 16), int(60 * 16))

            line_pen = QPen(QColor('#26f7a4'))
            line_pen.setWidth(2)
            painter.setPen(line_pen)
            painter.drawLine(center, QPointF(
                center.x() + radius * cos(self.angle * pi / 180.0),
                center.y() - radius * sin(self.angle * pi / 180.0)
            ))

            painter.setPen(QColor('#95e8d5'))
            painter.drawText(QPointF(center.x() - 24, center.y() + 6), 'RADAR')
        finally:
            painter.end()


class DashboardPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        page_layout = QHBoxLayout(self) # Yatay düzeye geçtik (Sol: Grafikler, Sağ: Bilgi Paneli)

        # SOL TARAF: Grafikler
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QWidget { background-color: transparent; }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.main_window.main_layout = QVBoxLayout(scroll_content)
        self.main_window.graph_create_add()

        scroll_area.setWidget(scroll_content)
        page_layout.addWidget(scroll_area, stretch=3) # Grafikler yatayda daha geniş yer kaplasın

        # SAĞ TARAF: Canlı Bilgi & Model Anlatım Paneli
        info_panel = QFrame()
        info_panel.setObjectName("info_panel")
        info_panel.setFixedWidth(280)
        
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(12)

        # 1. Canlı Özellik (Feature) Dağılımları
        feat_title = QLabel("CANLI ÖZELLİK DAĞILIMI")
        feat_title.setObjectName("feat_title")
        feat_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #39ff14;")
        info_layout.addWidget(feat_title)

        self.main_window.live_feat_bars = []
        
        features = ["Ort C/N0", "Std C/N0", "Ort prRes", "Std prRes", "Max prRes", "Kull Uydu", "Gör Uydu", "Açı Oranı"]
        for feat in features:
            r_layout = QHBoxLayout()
            
            lbl_name = QLabel(feat)
            lbl_name.setFixedWidth(80)
            lbl_name.setStyleSheet("font-size: 12px; font-weight: bold; color: #c4c4c4;")
            
            bar = QProgressBar()
            bar.setFixedHeight(12)
            bar.setTextVisible(False)
            bar.setRange(0, 100)
            bar.setStyleSheet("QProgressBar { background: #121212; border: 1px solid #2c2c2c; border-radius: 6px; } QProgressBar::chunk { background: #db2508; border-radius: 6px; }")
            
            val_lbl = QLabel("0.0")
            val_lbl.setFixedWidth(40)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #c4c4c4;")
            
            r_layout.addWidget(lbl_name)
            r_layout.addWidget(bar)
            r_layout.addWidget(val_lbl)
            
            info_layout.addLayout(r_layout)
            self.main_window.live_feat_bars.append((bar, val_lbl))

        # Araya ince bir stil çizgisi ekle
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("info_line")
        info_layout.addWidget(line)

        # 2. Model Çalışma Mantığı ve Özellikler
        info_title = QLabel("SİSTEM ÇALIŞMA MANTIĞI")
        info_title.setObjectName("info_title")
        
        info_text = QLabel(
            "SİPER TAKTİK KONTROL - EH TESPİT SİSTEMİ\n\n"
            "[+] 1D-CNN (SİNYAL İŞLEME): GNSS alıcısından alınan ham verilerdeki (C/N0, Pseudorange Residual) anlık sinyal bozulumlarını ve uzamsal anomalileri tespit eder.\n\n"
            "[+] TRANSFORMER (ZAMANSAL İZLEME): Ardışık zaman adımlarındaki telemetri matrisini analiz ederek, doğal olmayan sinyal sıçramalarını ve elektronik harp (Spoofing) saldırılarını yüksek hassasiyetle sınıflandırır."
        )
        info_text.setWordWrap(True)
        info_text.setObjectName("info_text")
        info_text.setStyleSheet("font-size: 11px;")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)

        radar_card = QFrame()
        radar_card.setStyleSheet('background: #0f1218; border: 1px solid #23282f; border-radius: 16px;')
        radar_layout = QVBoxLayout(radar_card)
        radar_layout.setContentsMargins(12, 12, 12, 12)
        radar_layout.setSpacing(12)

        radar_label = QLabel('RADAR GÖRÜNTÜSÜ')
        radar_label.setStyleSheet('color: #8afe8a; font-size: 14px; font-weight: bold;')
        radar_layout.addWidget(radar_label)
        radar_layout.addWidget(RadarWidget())

        info_layout.addWidget(radar_card)
        info_layout.addStretch()
        page_layout.addWidget(info_panel, alignment=Qt.AlignmentFlag.AlignTop)
