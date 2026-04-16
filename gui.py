import sys
import pickle
import pandas as pd
import numpy as np
import pyqtgraph as pg
import itertools
import sklearn

from tensorflow.keras.models import load_model
from collections import deque
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Eğer TensorFlow hatası alıyorsan bunu da ekle:
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from PyQt6.QtCore import *
import pyqtgraph as pg
# Kimsenin bilgisayarını bozmayacak, dinamik yol bulucu
if sys.platform == 'win32':
    # Python'un kurulu olduğu ana dizini bulur (Anaconda veya düz Python fark etmez)
    base_path = os.path.dirname(sys.executable)
    dll_paths = [
        base_path,
        os.path.join(base_path, "Library", "bin"),
        os.path.join(base_path, "Scripts")
    ]
    for path in dll_paths:
        if os.path.exists(path):
            os.add_dll_directory(path)



class DataWorker(QObject):
    data_ready = pyqtSignal(float, list)
    def __init__(self, model, scaler, csv_path):
        super().__init__()
        self.model = model
        self.scaler = scaler
        self.data_buffer = deque(maxlen=30)
        df = pd.read_csv(csv_path)
        self.data_iterator = itertools.cycle(df.iloc[:, :8].values)

    @pyqtSlot()
    def process_data(self):
        new_row = next(self.data_iterator)
        self.data_buffer.append(new_row)
        if len(self.data_buffer) == 30:
            data_array = np.array(list(self.data_buffer))
            normalized_data = self.scaler.transform(data_array)
            normalized_tensor = normalized_data.reshape(1,30,8)
            prediction = self.model.predict(normalized_tensor, verbose = 0)
            score = float(prediction[0][0])

            self.data_ready.emit(score, list(new_row))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model")
        self.resize(800,600)
        
        self.load_model_scaler()
        
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()

        pg.setConfigOptions(antialias=True)
        self.graph = pg.PlotWidget()
        self.graph.setBackground('#1e1e2f')
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.graph.setLabel('left', 'Sensör Değeri')
        self.graph.setLabel('bottom', 'Zaman Çizelgesi')
        
        kalem = pg.mkPen(color=(0, 255, 255), width=3)
        self.starter_data = [0] * 1000
        self.cizgi = self.graph.plot(self.starter_data, pen=kalem)
        self.cizgi.setFillLevel(0)
        self.cizgi.setBrush(pg.mkBrush(color=(0, 255, 255, 50)))

        main_layout.addWidget(self.graph)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.Thread()

    def Thread(self):
        #Thread
        self.data_worker = DataWorker(model=self.ai_model, scaler=self.ai_scaler, csv_path="model\\test_senaryosu.csv")
        self.kanal = QThread()
        
        self.data_worker.moveToThread(self.kanal)
        self.timer = QTimer()
        self.timer.setInterval(1)
        self.timer.moveToThread(self.kanal)
        self.timer.timeout.connect(self.data_worker.process_data)

        self.data_worker.data_ready.connect(self.graph_update)

        self.kanal.started.connect(self.timer.start)
        self.kanal.start()

    def graph_update(self, oran, liste):
        self.starter_data.pop(0)
        self.starter_data.append(liste[0])
        self.cizgi.setData(self.starter_data)
        if oran > 0.5:
            self.setWindowTitle(f"UYARI: SALDIRI TESPİT EDİLDİ! (%{oran*100:.2f})")
        else:
            self.setWindowTitle(f"Durum Normal (%{oran*100:.2f})")

    def load_model_scaler(self):
        self.ai_model = load_model("model\\crnn_model.h5")
        with open("model\\crnn_scaler.pkl", "rb") as f:
            self.ai_scaler = pickle.load(f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

    #YAZILIMINI SİKTİĞİM
