import pickle
import pandas as pd
import numpy as np
import math
import PyQt5.QtWidgets  # Force PyQt5 for pyqtgraph
import pyqtgraph as pg
pg.setConfigOptions(useOpenGL=False)  # Disable OpenGL for compatibility
import itertools
import sklearn

from tensorflow.keras.models import load_model
from collections import deque
from PyQt5.QtCore import *

class DataWorker(QObject):
    data_ready = pyqtSignal(float, np.ndarray)
    gps_ready = pyqtSignal(float, float)

    def __init__(self, model, scaler, csv_path):
        super().__init__()
        self.model = model
        self.scaler = scaler
        self.data_buffer = deque(maxlen=30)
        df = pd.read_csv(csv_path)
        self.data_iterator = itertools.cycle(df.iloc[:, :8].values)
        self.gps_path = self._create_gps_path()
        self.gps_index = 0

    def _create_gps_path(self):
        base_lat, base_lon = 38.7312, 35.4787
        path = []
        for i in range(1000):
            path.append(
                (
                    base_lat + 0.00018 * math.sin(i / 25.0),
                    base_lon + 0.00024 * math.cos(i / 30.0)
                )
            )
        return path

    @pyqtSlot()
    def process_data(self):
        new_row = next(self.data_iterator)
        self.data_buffer.append(new_row)
        if len(self.data_buffer) == 30:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                data_array = np.array(list(self.data_buffer))
                normalized_data = self.scaler.transform(data_array)
            normalized_tensor = normalized_data.reshape(1,30,8)
            prediction = self.model.predict(normalized_tensor, verbose = 0)
            score = float(prediction[0][0])

            self.data_ready.emit(score, new_row)

            lat, lon = self.gps_path[self.gps_index]
            self.gps_ready.emit(lat, lon)
            self.gps_index = (self.gps_index + 1) % len(self.gps_path)

class TelemetryWorker(QThread):
    telemetry_ready = pyqtSignal(dict)

    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path
        self.is_running = True

    def run(self):
        try:
            for chunk in pd.read_csv(self.csv_path, chunksize=1000):
                if not self.is_running:
                    break
                for index, row in chunk.iterrows():
                    if not self.is_running:
                        break
                    self.telemetry_ready.emit(row.to_dict())
                    self.msleep(100)
        except Exception as e:
            print(f"Hata: {e}")

    def stop(self):
        self.is_running = False
        self.wait()

class PgGraph(pg.PlotWidget):
    def __init__(self, left_name:str, bottom_name:str):
        from PyQt5.QtWidgets import QApplication
        if QApplication.instance() is None:
            raise RuntimeError("QApplication must be created before PgGraph")
        super().__init__()
        self.setMinimumHeight(150)
        self.setBackground('#000000')
        self.getPlotItem().getViewBox().setBackgroundColor('#000000')
        self.showGrid(x=True, y=True, alpha=0.18)
        self.setLabel('left', left_name)
        self.setLabel('bottom', bottom_name)
        self.getPlotItem().hideButtons()
        self.getPlotItem().setMenuEnabled(False)
        self.getPlotItem().showAxis('top', False)
        self.getPlotItem().showAxis('right', False)
        axis_pen = pg.mkPen('#5c5f66')
        text_pen = pg.mkPen('#8e929b')
        self.getPlotItem().getAxis('left').setPen(axis_pen)
        self.getPlotItem().getAxis('left').setTextPen(text_pen)
        self.getPlotItem().getAxis('bottom').setPen(axis_pen)
        self.getPlotItem().getAxis('bottom').setTextPen(text_pen)

        # Kırmızı çizgi rengi (askeri tema için)
        self.kalem = pg.mkPen(color=(219, 37, 8), width=2)
        self.data = np.zeros(1000)
        self.baseline = self.plot(np.zeros(1000), pen=pg.mkPen(None))
        self.cizgi = self.plot(self.data, pen=self.kalem)
        self.fill = pg.FillBetweenItem(self.cizgi, self.baseline, brush=(219, 37, 8, 40))
        self.getPlotItem().addItem(self.fill)
        self.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False)

    def set_theme(self, is_dark: bool):
        if is_dark:
            self.setBackground('#000000')  # Tam siyah askeri arka plan
            self.getPlotItem().getViewBox().setBackgroundColor('#000000')
            self.showGrid(x=True, y=True, alpha=0.18)
            self.kalem.setColor(pg.mkColor(219, 37, 8))
        else:
            self.setBackground('#1f1f1f')  # Açık modda koyu gri
            self.getPlotItem().getViewBox().setBackgroundColor('#1f1f1f')
            self.showGrid(x=True, y=True, alpha=0.18)
            self.kalem.setColor(pg.mkColor(219, 37, 8))
        self.cizgi.setPen(self.kalem)
            
class Engine():
    def Thread(self):
        # 1. Eski Simülasyon Worker'ı (Grafikler ve Loglar İçin)
        self.data_worker = DataWorker(model=self.ai_model, scaler=self.ai_scaler, csv_path="model\\test_senaryosu.csv")
        self.kanal = QThread()
            
        self.data_worker.moveToThread(self.kanal)
        self.timer = QTimer()
        self.timer.setInterval(1)
        self.timer.moveToThread(self.kanal)
        self.timer.timeout.connect(self.data_worker.process_data)

        self.data_worker.data_ready.connect(self.graph_update)
        # gps_ready sinyalini haritaya bağlamıyoruz, çünkü artık TelemetryWorker'dan besleniyor

        self.kanal.started.connect(self.timer.start)
        self.kanal.start()

        # 2. Yeni Telemetri Worker'ı (İHA Telemetri ve Harita İçin)
        self.telemetry_worker = TelemetryWorker(csv_path="model2\\datas.csv")
        self.telemetry_worker.telemetry_ready.connect(self.process_telemetry)
        self.telemetry_worker.start()

    def process_telemetry(self, telemetry_data):
        # CSV'deki "GPS_coord[0]" ve "GPS_coord[1]" sütunlarından harita koordinatlarını çekiyoruz
        lat = float(telemetry_data.get('GPS_coord[0]', 38.7312))
        lon = float(telemetry_data.get('GPS_coord[1]', 35.4787))
        self.update_map_position(lat, lon)
        
        if hasattr(self, 'settings_page'):
            self.settings_page.update_sys_telemetry(telemetry_data)

        if hasattr(self, 'iha_page'):
            formatted_telemetry = {
                'GPS_ground_speed': float(telemetry_data.get('GPS_speed (m/s)', 0.0)),
                'GPS_altitude': float(telemetry_data.get('GPS_altitude', 0.0)),
                'GPS_ground_course': float(telemetry_data.get('GPS_ground_course', 0.0)),
                'verticalSpeed': float(telemetry_data.get('navVel[2]', 0.0)),
                'GPS_hdop': float(telemetry_data.get('GPS_hdop', 0.0)),
                'GPS_numSat': int(telemetry_data.get('GPS_numSat', 0)),
                'navState': str(telemetry_data.get('Nav State', 'AUTO-NAV')),
                'GPS_coord[0]': lat,
                'GPS_coord[1]': lon,
                'escTemperature': float(telemetry_data.get('escTemperature', 0.0)),
                'vbat': float(telemetry_data.get('vbat (V)', 0.0)),
                'rssi': float(telemetry_data.get('rssi', 0.0)),
                'activeWpNumber': int(telemetry_data.get('activeWpNumber', 0)),
                'navTgtPos[0]': float(telemetry_data.get('navTgtPos[0]', 0.0)),
                'navTgtPos[1]': float(telemetry_data.get('navTgtPos[1]', 0.0)),
                'navTgtPos[2]': float(telemetry_data.get('navTgtPos[2]', 0.0)),
                'navVel[0]': float(telemetry_data.get('navVel[0]', 0.0)),
                'navVel[1]': float(telemetry_data.get('navVel[1]', 0.0)),
                'navVel[2]': float(telemetry_data.get('navVel[2]', 0.0)),
                'accSmooth[0]': float(telemetry_data.get('accSmooth[0]', 0.0)),
                'accSmooth[1]': float(telemetry_data.get('accSmooth[1]', 0.0)),
                'accSmooth[2]': float(telemetry_data.get('accSmooth[2]', 0.0)),
                'gyroADC[0]': float(telemetry_data.get('gyroADC[0]', 0.0)),
                'gyroADC[1]': float(telemetry_data.get('gyroADC[1]', 0.0)),
                'gyroADC[2]': float(telemetry_data.get('gyroADC[2]', 0.0)),
                'magADC[0]': float(telemetry_data.get('magADC[0]', 0.0)),
                'magADC[1]': float(telemetry_data.get('magADC[1]', 0.0)),
                'magADC[2]': float(telemetry_data.get('magADC[2]', 0.0)),
            }
            self.iha_page.update_telemetry(formatted_telemetry)

    def graph_create_add(self):
        from PyQt5.QtWidgets import QLabel
        
        # Grafik isimleri ve açıklamaları
        graph_details = [
            ("Mean_cno", "Ortalama C/N0 (Sinyal Gücü) - Spoofing anında sert düşüşler yaşanabilir"),
            ("std_cno", "C/N0 Standart Sapması - Sinyal kalite kararsızlığını ve dalgalanmasını gösterir"),
            ("mean_prRes", "Pseudorange Residual (Ortalama) - Uydu mesafe hesaplamasındaki uyumsuzlukları saptar"),
            ("std_prRes", "Pseudorange Residual (Sapma) - Hesaplama hatalarının veya sahte sinyallerin tespiti"),
            ("max_prRes", "Maksimum Pseudorange Hatası - Konumdaki ani zıplamalarda ve saldırılarda pik yapar"),
            ("num_used", "Kullanılan Uydu Sayısı - Saldırı esnasında alıcının uydu kaybetmesi durumunu izler"),
            ("num_visible", "Gökyüzünde Görünür Uydu Sayısı - Cihazın gördüğü toplam sinyal kaynağı"),
            ("cno_elev_ratio", "Sinyal / Yükseklik Oranı - Doğal olmayan (ör. yerden gelen) sinyalleri ayırt eder")
        ]
        
        self.graph_list = []
        for name, desc in graph_details:
            # Her grafikten önce arayüze açıklama metni ekliyoruz
            lbl = QLabel(f"📍 {name} | {desc}")
            lbl.setStyleSheet("color: #a0a0c0; font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
            self.main_layout.addWidget(lbl)
            
            # Grafiği oluşturup ekliyoruz
            graph = PgGraph(name, "Zaman")
            self.graph_list.append(graph)
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