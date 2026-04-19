import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class ModelAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(30)
        
        title = QLabel("📈 Model Eğitim & Başarı Grafikleri")
        title.setObjectName("page_title")
        content_layout.addWidget(title)
        
        # Ekrana basılması istenen resimler
        img_list = [
            ("Karmaşıklık Matrisi (Confusion Matrix)", "model/confusion_matrix.png"),
            ("ROC Eğrisi (Model Tahmin Analizi)", "model/roc_curve.png"),
            ("Eğitim ve Kayıp (Loss / Accuracy)", "model/egitim_grafikleri.png"),
            ("Hassasiyet / Duyarlılık (Precision - Recall)", "model/precision_recall_curve.png")
        ]
        
        for img_title, img_path in img_list:
            lbl_title = QLabel(img_title)
            lbl_title.setProperty("class", "img_title")
            content_layout.addWidget(lbl_title)
            
            img_lbl = QLabel()
            if os.path.exists(img_path):
                if QApplication.instance() is not None:
                    pixmap = QPixmap(img_path)
                    # Standart bir genişlikte yeniden boyutlandırarak arayüze sığdır
                    pixmap = pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation)
                    img_lbl.setPixmap(pixmap)
                else:
                    img_lbl.setText("QApplication gerekli")
            else:
                img_lbl.setText("Görsel bulunamadı: " + img_path)
                
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(img_lbl)
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
