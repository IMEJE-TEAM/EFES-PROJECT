import os
import numpy as np
from math import cos, sin, pi
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QApplication, QGridLayout, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush

import pyqtgraph as pg

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


class GraphCard(QFrame):
    def __init__(self, title: str, plot_type: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet(
            'QFrame { background: #0f1218; border: 1px solid #23282f; border-radius: 16px; }'
            'QFrame:hover { border: 1px solid #48b0ff; background: #13171f; }'
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet('color: #c7d2e0; font-size: 14px; font-weight: bold; border: none; background: transparent;')
        layout.addWidget(title_label)

        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#0b1118')
        self.plot_widget.setFixedHeight(260)
        self.plot_widget.getPlotItem().hideButtons()
        self.plot_widget.getPlotItem().setMenuEnabled(False)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        self.plot_widget.setStyleSheet('border: none; border-radius: 12px;')
        
        # Eksen Stilleri
        axis_pen = pg.mkPen('#334155')
        text_pen = pg.mkPen('#94a3b8')
        for axis_name in ['left', 'bottom']:
            axis = self.plot_widget.getPlotItem().getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen(text_pen)

        layout.addWidget(self.plot_widget)
        self.generate_mock_data(plot_type)

    def generate_mock_data(self, p_type):
        if p_type == 'cm':
            # Karmaşıklık Matrisi (Heatmap - ImageItem)
            # Gerçek veri simülasyonu: [[TP, FN], [FP, TN]]
            data = np.array([[850, 45], [30, 920]])
            img = pg.ImageItem()
            img.setImage(data)
            
            # Renk Haritası
            colormap = pg.colormap.get('plasma')
            img.setLookupTable(colormap.getLookupTable())
            
            self.plot_widget.addItem(img)
            self.plot_widget.setLabel('left', 'Gerçek (True)')
            self.plot_widget.setLabel('bottom', 'Tahmin (Predicted)')
            self.plot_widget.getPlotItem().invertY(True)

        elif p_type == 'roc':
            # ROC Eğrisi
            fpr = np.linspace(0, 1, 100)
            tpr = 1 - np.exp(-6 * fpr)
            self.plot_widget.plot(fpr, tpr, pen=pg.mkPen('#39ff14', width=2), fillLevel=0, fillBrush=(57, 255, 20, 40))
            self.plot_widget.plot([0, 1], [0, 1], pen=pg.mkPen('#ff003c', width=2, style=Qt.DashLine))
            self.plot_widget.setLabel('left', 'True Positive Rate')
            self.plot_widget.setLabel('bottom', 'False Positive Rate')

        elif p_type == 'loss':
            # Eğitim & Kayıp
            epochs = np.arange(1, 51)
            loss = 0.7 * np.exp(-0.12 * epochs) + np.random.normal(0, 0.015, 50)
            val_loss = 0.7 * np.exp(-0.09 * epochs) + 0.04 + np.random.normal(0, 0.02, 50)
            self.plot_widget.plot(epochs, loss, pen=pg.mkPen('#39ff14', width=2), name="Eğitim")
            self.plot_widget.plot(epochs, val_loss, pen=pg.mkPen('#48b0ff', width=2), name="Doğrulama")
            self.plot_widget.setLabel('left', 'Kayıp (Loss)')
            self.plot_widget.setLabel('bottom', 'Epok (Epoch)')

        elif p_type == 'pr':
            # Precision / Recall
            recall = np.linspace(0, 1, 100)
            precision = 1 - 0.4 * recall**4
            self.plot_widget.plot(recall, precision, pen=pg.mkPen('#eab308', width=2), fillLevel=0, fillBrush=(234, 179, 8, 40))
            self.plot_widget.setLabel('left', 'Precision')
            self.plot_widget.setLabel('bottom', 'Recall')

        elif p_type == 'feature':
            # Özellik Dağılımı (Çift Eğri)
            x = np.linspace(-4, 4, 200)
            normal = np.exp(-0.5 * ((x + 1) / 0.8)**2)
            spoof = 0.7 * np.exp(-0.5 * ((x - 1.5) / 1.0)**2)
            self.plot_widget.plot(x, normal, pen=pg.mkPen('#39ff14', width=2), fillLevel=0, fillBrush=(57, 255, 20, 60))
            self.plot_widget.plot(x, spoof, pen=pg.mkPen('#ff003c', width=2), fillLevel=0, fillBrush=(255, 0, 60, 60))
            self.plot_widget.setLabel('left', 'Yoğunluk')
            self.plot_widget.setLabel('bottom', 'C/N0 Özellik Değeri')

        elif p_type == 'predict':
            # Tahmin Dağılımı (Bar Graph)
            x = np.arange(0, 1.05, 0.05)
            y = np.array([800, 120, 50, 30, 20, 10, 5, 5, 8, 15, 25, 40, 60, 90, 150, 200, 300, 500, 750, 850, 950])
            bg = pg.BarGraphItem(x=x, height=y, width=0.04, brush='#48b0ff')
            self.plot_widget.addItem(bg)
            self.plot_widget.setLabel('left', 'Örnek Sayısı')
            self.plot_widget.setLabel('bottom', 'Spoofing Olasılığı (%)')

        elif p_type == 'error':
            # Hata Analizi (Scatter Plot)
            x = np.random.normal(0, 1, 250)
            y = np.random.normal(0, 1, 250)
            errors = (x**2 + y**2 > 2.5)
            
            scatter_correct = pg.ScatterPlotItem(x=x[~errors], y=y[~errors], size=5, pen=pg.mkPen(None), brush=pg.mkBrush('#39ff14'))
            scatter_error = pg.ScatterPlotItem(x=x[errors], y=y[errors], size=8, pen=pg.mkPen(None), brush=pg.mkBrush('#ff003c'))
            self.plot_widget.addItem(scatter_correct)
            self.plot_widget.addItem(scatter_error)
            self.plot_widget.setLabel('left', 'prRes Sapması')
            self.plot_widget.setLabel('bottom', 'C/N0 Ortalama')

        elif p_type == 'regional':
            # Bölgesel Analiz (Zaman Serisi)
            x = np.arange(150)
            for i, color in enumerate(['#39ff14', '#48b0ff', '#eab308', '#ff003c']):
                y = np.cumsum(np.random.normal(0, 1, 150)) + i * 20
                self.plot_widget.plot(x, y, pen=pg.mkPen(color, width=2))
            self.plot_widget.setLabel('left', 'GNSS Sapma Oranı')
            self.plot_widget.setLabel('bottom', 'Zaman / Sektör')


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

        title = QLabel('📈 Model Eğitim & Başarı Grafikleri (Canlı Çizim)')
        title.setObjectName('page_title')
        title.setStyleSheet('font-size: 22px; color: #8afe8a; font-weight: bold;')
        content_layout.addWidget(title)

        subtitle = QLabel('Eski statik resimler yerine doğrudan kütüphane kullanılarak oluşturulmuş interaktif, profesyonel model analiz grafikleri.')
        subtitle.setStyleSheet('color: #9aa2b1; font-size: 13px;')
        content_layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(18)

        # Çizilecek interaktif grafiklerin tipleri ve başlıkları
        plot_list = [
            ('Karmaşıklık Matrisi (Confusion Matrix)', 'cm'),
            ('ROC Eğrisi', 'roc'),
            ('Eğitim & Kayıp Değerleri', 'loss'),
            ('Precision / Recall Eğrisi', 'pr'),
            ('Özellik Dağılımı (Normal / Spoofed)', 'feature'),
            ('Tahmin Dağılımı Histogramı', 'predict'),
            ('Hata Analizi (Scatter)', 'error'),
            ('Bölgesel Sapma Analizi', 'regional')
        ]

        for index, (p_title, p_type) in enumerate(plot_list):
            card = GraphCard(p_title, p_type, parent=self)
            grid.addWidget(card, index // 2, index % 2)

        content_layout.addLayout(grid)

        # RADAR PANELİ
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