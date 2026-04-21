import os
import numpy as np
from math import cos, sin, pi
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QApplication, QGridLayout, QFrame, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush

import pyqtgraph as pg

# ========================================================
# YENİ TRANSFORMER ATTENTION (DİKKAT) MATRİSİ SİMÜLASYONU
# ========================================================
class AttentionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        
        # Animasyon için Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_matrix)
        self.timer.start(100) # 10 FPS
        
        # 8 Dikkat Başlığı (Multi-Head) temsili
        self.grid_size = 8 
        self.weights = np.random.rand(self.grid_size, self.grid_size)

    def update_matrix(self):
        # Yumuşak geçişli matris animasyonu (Attention değerlerinin değişimi)
        noise = (np.random.rand(self.grid_size, self.grid_size) - 0.5) * 0.15
        self.weights = np.clip(self.weights + noise, 0.1, 1.0)
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing)
            rect = self.rect().adjusted(10, 10, -10, -10)
            
            # Siyah/Koyu yeşil arka plan
            painter.setBrush(QColor('#081011'))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 10, 10)

            # İç Grid (Attention Matrisi) Çizimi
            cell_w = rect.width() / self.grid_size
            cell_h = rect.height() / self.grid_size

            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    val = self.weights[i, j]
                    
                    # Transformer'a özel siber-neon renk skalası
                    r = int(57 * val)
                    g = int(255 * val)
                    b = int(20 * val + 150 * (1 - val)) 
                    
                    painter.setBrush(QColor(r, g, b, int(80 + 175 * val)))
                    painter.setPen(QPen(QColor('#1a3c28'), 1))
                    
                    x = rect.left() + j * cell_w
                    y = rect.top() + i * cell_h
                    
                    cell_rect = QRectF(x + 2, y + 2, cell_w - 4, cell_h - 4)
                    painter.drawRoundedRect(cell_rect, 4, 4)
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

        # SAYFA BAŞLIK VE AÇIKLAMASI GÜNCELLENDİ
        title = QLabel('🧠 SİPER AI (Model-2): UAV Inertial Transformer Mimarisi & Başarı Analizi')
        title.setObjectName('page_title')
        title.setStyleSheet('font-size: 22px; color: #8afe8a; font-weight: bold;')
        content_layout.addWidget(title)

        subtitle = QLabel('GNSS verilerini baypas edip doğrudan fiziksel sensör füzyonu (IMU, Baro) ile anomali tespiti yapan Multi-Head Attention tabanlı yapay zeka modelinin analiz paneli.')
        subtitle.setStyleSheet('color: #9aa2b1; font-size: 13px;')
        content_layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(18)

        # Çizilecek interaktif grafiklerin tipleri ve başlıkları (AYNEN KORUNDU)
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

        # ========================================================
        # YENİ ATTENTION MATRİSİ VE AÇIKLAMA PANELİ
        # ========================================================
        attention_card = QFrame()
        attention_card.setStyleSheet('background: #0f1218; border: 1px solid #23282f; border-radius: 18px;')
        attention_layout = QHBoxLayout(attention_card)
        attention_layout.setContentsMargins(18, 18, 18, 18)
        attention_layout.setSpacing(18)

        # Matris Görseli
        matrix_panel = QFrame()
        matrix_panel.setStyleSheet('background: #081011; border: 1px solid #1f2937; border-radius: 18px;')
        matrix_panel.setFixedSize(380, 380)
        matrix_panel_layout = QVBoxLayout(matrix_panel)
        matrix_panel_layout.setContentsMargins(12, 12, 12, 12)
        matrix_panel_layout.addWidget(AttentionWidget())

        # Metin Paneli
        text_panel = QFrame()
        text_panel.setStyleSheet('background: transparent; border: none;')
        text_layout = QVBoxLayout(text_panel)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(10)

        attention_title = QLabel("Aktif 'Attention' (Dikkat) Matrisi")
        attention_title.setStyleSheet('color: #8afe8a; font-size: 16px; font-weight: bold;')
        text_layout.addWidget(attention_title)

        attention_desc = QLabel(
            "Bu matris, SİPER AI'nın 'Multi-Head Attention' mekanizmasının canlı bir simülasyonudur. "
            "Modelin son 30 saniyelik uçuş verisinde hangi sensör noktalarına ve zaman dilimlerine "
            "ağırlık verdiğini (odaklandığını) görselleştirir.\n\n"
            "Neon yeşil alanlar, modelin analiz ettiği kritik fiziksel hareketleri (örneğin ani ivmelenme veya irtifa kaybı) "
            "temsil eder. Siber bir Spoofing saldırısı anında, GNSS'ten gelen sahte sinyaller İHA'nın fiziksel "
            "gerçekliği ile uyuşmayacağı için, yapay zekanın bu matristeki odak noktaları anında "
            "şekil değiştirerek anomaliyi saniyeler içinde deşifre eder."
        )
        attention_desc.setWordWrap(True)
        attention_desc.setStyleSheet('color: #9aa2b1; font-size: 13px; line-height: 1.5;')
        
        text_layout.addWidget(attention_desc)
        text_layout.addStretch()

        attention_layout.addWidget(matrix_panel)
        attention_layout.addWidget(text_panel)

        content_layout.addWidget(attention_card)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)