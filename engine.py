import pickle
import pandas as pd
import numpy as np
import pyqtgraph as pg
import itertools
import sklearn

from tensorflow.keras.models import load_model
from collections import deque
from PyQt6.QtCore import *

class DataWorker(QObject):
    data_ready = pyqtSignal(float, np.ndarray)
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

            self.data_ready.emit(score, new_row)

class PgGraph(pg.PlotWidget):
    def __init__(self, left_name:str, bottom_name:str):
        super().__init__()
        self.setMinimumHeight(150)
        self.setBackground('#1e1e2f')
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel('left', left_name)
        self.setLabel('bottom', bottom_name)

        kalem = pg.mkPen(color=(0, 255, 255), width=3)
        self.data = np.zeros(1000)
        self.cizgi = self.plot(self.data, pen=kalem)
        self.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False)
class Engine():
    def Thread(self):
        #Thread
        self.data_worker = DataWorker(model=self.ai_model, scaler=self.ai_scaler, csv_path="model\\test_senaryosu.csv")
        self.kanal = QThread()
            
        self.data_worker.moveToThread(self.kanal)
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.moveToThread(self.kanal)
        self.timer.timeout.connect(self.data_worker.process_data)

        self.data_worker.data_ready.connect(self.graph_update)

        self.kanal.started.connect(self.timer.start)
        self.kanal.start()

    def graph_create_add(self):
        graph_name = ["Mean_cno","std_cno","mean_prRes","std_prRes","max_prRes","num_used","num_visible","cno_elev_ratio"]
        self.graph_list = []
        for name in graph_name:
            self.graph_list.append(PgGraph(name, "Zaman"))
        for graph in self.graph_list:
            self.main_layout.addWidget(graph)

    def graph_update(self, oran, vektor):
        for i, value in enumerate(vektor):
            self.graph_list[i].data = np.roll(self.graph_list[i].data, -1)
            self.graph_list[i].data[-1] = value
            self.graph_list[i].cizgi.setData(self.graph_list[i].data)
        if oran > 0.5:
            self.setWindowTitle(f"UYARI: SALDIRI TESPİT EDİLDİ! (%{oran*100:.2f})")
        else:
            self.setWindowTitle(f"Durum Normal (%{oran*100:.2f})")

    def load_model_scaler(self):
        self.ai_model = load_model("model\\crnn_model.h5")
        with open("model\\crnn_scaler.pkl", "rb") as f:
            self.ai_scaler = pickle.load(f)