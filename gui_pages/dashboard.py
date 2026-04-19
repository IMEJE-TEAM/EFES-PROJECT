from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame, QLabel, QProgressBar
from PyQt5.QtCore import Qt

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
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setFixedWidth(340)
        info_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        info_panel = QFrame()
        info_panel.setObjectName("info_panel")
        
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(20)

        # 1. Canlı Özellik (Feature) Dağılımları
        feat_title = QLabel("CANLI ÖZELLİK DAĞILIMI")
        feat_title.setObjectName("feat_title")
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
        info_title = QLabel("MODEL NASIL ÇALIŞIR?")
        info_title.setObjectName("info_title")
        
        info_text = QLabel(
            "Bu sistem, GNSS/GPS alıcılarından alınan sinyal verilerini kullanarak CRNN-TRANSFORMER derin öğrenme mimarisi ile sahte sinyalleri (Spoofing) saptar.\n\n"
            "1️⃣ 1D-CNN (Uzamsal Özellik Çıkarımı): Sinyal kalitesi (C/N0), uydudan olan mesafe hataları (Pseudorange) gibi değerlerden anomali örüntülerini kısa bir sürede öğrenir.\n\n"
            "2️⃣ TRANSFORMER (Zamansal Bağlantı Analizi): Zaman serisi halindeki 30 ardışık verinin dünden bugüne olan hafızasını tutar, GPS kopmalarındaki / bozulmalarındaki gariplikleri analiz edip saldırıya karar verir."
        )
        info_text.setWordWrap(True)
        info_text.setObjectName("info_text")
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)

        info_layout.addStretch()
        info_scroll.setWidget(info_panel)
        page_layout.addWidget(info_scroll, stretch=1)
