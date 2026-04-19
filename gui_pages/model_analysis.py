import os
from math import cos, sin, pi
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QApplication, QGridLayout, QFrame, QDialog, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen


class RadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0.0
        self.setMinimumSize(360, 360)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(40)

    def rotate(self):
        self.angle = (self.angle + 2.5) % 360
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
            rect = self.rect().adjusted(10, 10, -10, -10)
            center = rect.center()
            radius = min(rect.width(), rect.height()) / 2 - 10

            painter.setBrush(QColor('#081011'))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius + 10, radius + 10)

            grid_pen = QPen(QColor('#1f354c'), 2)
            painter.setPen(grid_pen)
            painter.setBrush(Qt.NoBrush)
            for ring in range(1, 5):
                painter.drawEllipse(center, radius / 5 * ring, radius / 5 * ring)
            painter.drawLine(center.x() - radius, center.y(), center.x() + radius, center.y())
            painter.drawLine(center.x(), center.y() - radius, center.x(), center.y() + radius)

            painter.setPen(QPen(QColor('#224362'), 1))
            for i in range(0, 360, 30):
                angle = i * pi / 180.0
                x = center.x() + radius * 0.96 * cos(angle)
                y = center.y() + radius * 0.96 * sin(angle)
                painter.drawLine(center, QPointF(x, y))

            sweep_pen = QPen(QColor('#26f7a4'))
            sweep_pen.setWidth(3)
            painter.setPen(sweep_pen)
            painter.setBrush(QColor(38, 247, 164, 80))
            painter.drawPie(rect, int((90 - self.angle - 40) * 16), int(80 * 16))

            line_pen = QPen(QColor('#26f7a4'))
            line_pen.setWidth(2)
            painter.setPen(line_pen)
            painter.drawLine(center, QPointF(
                center.x() + radius * cos(self.angle * pi / 180.0),
                center.y() - radius * sin(self.angle * pi / 180.0)
            ))

            painter.setPen(QPen(QColor('#95e8d5')))
            painter.setFont(self.font())
            painter.drawText(center.x() - 30, center.y() + 6, 'RADAR')
        finally:
            painter.end()


class ImageModal(QDialog):
    def __init__(self, title: str, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setStyleSheet(
            'QDialog { background: #050608; border: 2px solid #2d2d33; border-radius: 16px; }'
            'QLabel { color: #e2e8f0; }'
            'QPushButton { background: #1f2937; color: #f8fafc; border: 1px solid #334155; border-radius: 10px; padding: 10px 18px; }'
            'QPushButton:hover { background: #334155; }'
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        layout.addWidget(title_label)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not pixmap.isNull():
            enlarged = pixmap.scaledToWidth(1000, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(enlarged)
        else:
            image_label.setText('Görsel yüklenemedi.')
            image_label.setStyleSheet('color: #ff6b6b;')
        layout.addWidget(image_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_button = QPushButton('Kapat')
        close_button.clicked.connect(self.close)
        btn_layout.addWidget(close_button)
        layout.addLayout(btn_layout)

        self.resize(1080, 760)


class ImageCard(QFrame):
    def __init__(self, title: str, path: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.path = path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            'QFrame { background: #0f1218; border: 1px solid #23282f; border-radius: 16px; }'
            'QFrame:hover { border: 1px solid #48b0ff; background: #13171f; }'
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #c7d2e0; font-size: 14px; font-weight: bold;')
        layout.addWidget(title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(260)
        self.image_label.setStyleSheet('background: #0b1118; border-radius: 12px;')

        if os.path.exists(path) and QApplication.instance() is not None:
            pixmap = QPixmap(path)
            pixmap = pixmap.scaledToWidth(460, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.pixmap = pixmap
        else:
            self.image_label.setText('Görsel bulunamadı')
            self.image_label.setStyleSheet('color: #ff6b6b;')
            self.pixmap = QPixmap()

        layout.addWidget(self.image_label)

        footer = QLabel('Büyütmek için tıkla')
        footer.setStyleSheet('color: #94a3b8; font-size: 11px;')
        layout.addWidget(footer)

    def mousePressEvent(self, event):
        if self.pixmap and not self.pixmap.isNull():
            modal = ImageModal(self.title, self.pixmap, self)
            modal.exec_()
        super().mousePressEvent(event)


class ModelAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { background: transparent; border: none; }')

        content = QWidget()
        content.setStyleSheet('background: #050608;')
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(18)

        title = QLabel('📈 Model Eğitim & Başarı Grafikleri')
        title.setObjectName('page_title')
        title.setStyleSheet('font-size: 22px; color: #8afe8a; font-weight: bold;')
        content_layout.addWidget(title)

        subtitle = QLabel('Tüm model grafikleriyle, daha kompakt ve profesyonel sunum.')
        subtitle.setStyleSheet('color: #9aa2b1; font-size: 13px;')
        content_layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(18)

        img_list = [
            ('Karmaşıklık Matrisi', 'model/confusion_matrix.png'),
            ('ROC Eğrisi', 'model/roc_curve.png'),
            ('Eğitim & Kayıp', 'model/egitim_grafikleri.png'),
            ('Precision / Recall', 'model/precision_recall_curve.png'),
            ('Özellik Dağılımı', 'model/feature_dagilimi.png'),
            ('Tahmin Dağılımı', 'model/tahmin_dagilimi.png'),
            ('Hata Analizi', 'model/hata_analizi.png'),
            ('Bölgesel Analiz', 'model/bolgesel_analiz.png')
        ]

        for index, (img_title, img_path) in enumerate(img_list):
            card = ImageCard(img_title, img_path, parent=self)
            grid.addWidget(card, index // 2, index % 2)

        content_layout.addLayout(grid)

        radar_card = QFrame()
        radar_card.setStyleSheet('background: #0f1218; border: 1px solid #23282f; border-radius: 18px;')
        radar_layout = QHBoxLayout(radar_card)
        radar_layout.setContentsMargins(18, 18, 18, 18)
        radar_layout.setSpacing(18)

        radar_panel = QFrame()
        radar_panel.setStyleSheet('background: #081011; border: 1px solid #1f2937; border-radius: 18px;')
        radar_panel.setFixedSize(380, 380)
        radar_panel_layout = QVBoxLayout(radar_panel)
        radar_panel_layout.setContentsMargins(12, 12, 12, 12)
        radar_panel_layout.addWidget(RadarWidget())

        text_panel = QFrame()
        text_panel.setStyleSheet('background: transparent; border: none;')
        text_layout = QVBoxLayout(text_panel)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(10)

        radar_title = QLabel('Model Radar Sistemi')
        radar_title.setStyleSheet('color: #8afe8a; font-size: 16px; font-weight: bold;')
        text_layout.addWidget(radar_title)

        radar_desc = QLabel(
            'Sistem durumu tespitini model analizi ile birlikte görselleştirir. '
            'Bu radar göstergesi yalnızca arayüzsel bir animasyondur ve kokpit tarzında panel etkisi verir.'
        )
        radar_desc.setWordWrap(True)
        radar_desc.setStyleSheet('color: #9aa2b1; font-size: 13px; line-height: 1.4;')
        text_layout.addWidget(radar_desc)
        text_layout.addStretch()

        radar_layout.addWidget(radar_panel)
        radar_layout.addWidget(text_panel)

        content_layout.addWidget(radar_card)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)
