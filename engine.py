import os
import sys
import pickle
import pandas as pd
import numpy as np
import math
import PyQt5.QtWidgets 
import pyqtgraph as pg
pg.setConfigOptions(useOpenGL=False) 
import itertools

from collections import deque
from PyQt5.QtCore import *

import torch
# Yeni eğittiğimiz Transformer modelini projeye dahil ediyoruz
sys.path.append(os.getcwd())
from model2.uav_transformer import UAVInertialTransformer

# ==========================================
# 1. TELEMETRİ OKUYUCU (DRONE SİMÜLATÖRÜ)
# ==========================================
class TelemetryWorker(QThread):
    telemetry_ready = pyqtSignal(dict)

    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path
        self.is_running = True

    def run(self):
        try:
            df = pd.read_csv(self.csv_path)
            for index, row in df.iterrows():
                if not self.is_running:
                    break
                self.telemetry_ready.emit(row.to_dict())
                self.msleep(20) # 50 FPS Hızında Akıcı Veri
        except Exception as e:
            print(f"Telemetri Hatası: {e}")

    def stop(self):
        self.is_running = False
        self.wait()

# ==========================================
# 2. ARAYÜZ GRAFİK SINIFI (BTC / TRADINGVIEW STİLİ)
# ==========================================
class PgGraph(pg.PlotWidget):
    def __init__(self, left_name:str, bottom_name:str, c_hex='#39ff14', c_rgb=(57,255,20)):
        from PyQt5.QtWidgets import QApplication
        if QApplication.instance() is None:
            raise RuntimeError("QApplication must be created before PgGraph")
        super().__init__()
        self.setMinimumHeight(160)
        self.setBackground('#050907')
        self.getPlotItem().getViewBox().setBackgroundColor('#050907')
        self.showGrid(x=True, y=True, alpha=0.1)
        self.setLabel('left', left_name)
        self.setLabel('bottom', bottom_name)

        # GRAFİĞİ TAMAMEN KİLİTLE (Fareyle Bozulmayı Engeller)
        self.getPlotItem().setMouseEnabled(x=False, y=False)
        self.getPlotItem().hideButtons()
        self.getPlotItem().setMenuEnabled(False)
        self.getPlotItem().showAxis('top', False)
        self.getPlotItem().showAxis('right', False)

        axis_pen = pg.mkPen('#1a3c28')
        text_pen = pg.mkPen('#558b6e')
        self.getPlotItem().getAxis('left').setPen(axis_pen)
        self.getPlotItem().getAxis('left').setTextPen(text_pen)
        self.getPlotItem().getAxis('bottom').setPen(axis_pen)
        self.getPlotItem().getAxis('bottom').setTextPen(text_pen)

        # ÇİZGİ VE ALAN DOLGUSU (Antialias ile pürüzsüzleştirildi)
        self.kalem = pg.mkPen(color=c_rgb, width=2.5, antialias=True)
        self.data_points = 200 # BTC grafiği gibi uzun hafıza
        self.data = np.full(self.data_points, np.nan) # Boşluklar sıfır olmasın, NaN olsun

        self.baseline = self.plot(np.zeros(self.data_points), pen=pg.mkPen(None))
        self.cizgi = self.plot(self.data, pen=self.kalem, connect='finite')

        # Gradyan Dolgu
        r, g, b = c_rgb
        self.fill = pg.FillBetweenItem(self.cizgi, self.baseline, brush=(r, g, b, 40))
        self.getPlotItem().addItem(self.fill)

    def set_theme(self, is_dark: bool):
        pass # Tema artık sabit koyu askeri borsa stili

    def update_value(self, new_val, alpha=0.15):
        # ÜSTEL YUMUŞATMA (EMA) - Testere görüntülerini yok eder, süzülme hissi verir
        if np.isnan(self.data[-1]):
            smoothed_val = new_val
        else:
            smoothed_val = (self.data[-1] * (1 - alpha)) + (new_val * alpha)

        self.data = np.roll(self.data, -1)
        self.data[-1] = smoothed_val
        self.cizgi.setData(self.data)

        # DİNAMİK Y EKSENİ (Grafik hiçbir zaman dışarı taşmaz veya çok küçük kalmaz)
        valid_data = self.data[~np.isnan(self.data)]
        if len(valid_data) > 0:
            min_y = np.min(valid_data)
            max_y = np.max(valid_data)
            padding = max((max_y - min_y) * 0.15, 0.5)
            self.getPlotItem().setYRange(min_y - padding, max_y + padding)
            
# ==========================================
# 3. ANA MOTOR (SİPER YAPAY ZEKA MERKEZİ)
# ==========================================
class Engine():
    def Thread(self):
        self.imu_buffer = deque(maxlen=30)
        self.first_gps_lock = False
        
        self.model_gps_x = 0.0
        self.model_gps_y = 0.0

        # ESKİ CSV'Yİ GÖRSELLİK İÇİN YÜKLE (test_senaryosu.csv)
        try:
            df_grafik = pd.read_csv("model/test_senaryosu.csv")
            self.grafik_iterator = itertools.cycle(df_grafik.values)
        except Exception as e:
            print(f"[UYARI] Grafik CSV'si bulunamadı: {e}")
            self.grafik_iterator = itertools.cycle([np.zeros(9)])

        self.telemetry_worker = TelemetryWorker(csv_path="model2/datas.csv")
        self.telemetry_worker.telemetry_ready.connect(self.process_telemetry)
        self.telemetry_worker.start()

    def load_model_scaler(self):
        self.device = torch.device("cpu")
        self.ai_model = UAVInertialTransformer(input_dim=16, d_model=128, nhead=8, num_layers=4, dropout=0.15)
        model_path = "uav_transformer_best.pth"
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            self.ai_model.load_state_dict(checkpoint['model_state_dict'])
        self.ai_model.to(self.device)
        self.ai_model.eval()

    def process_telemetry(self, telemetry_data):
        real_lat = float(telemetry_data.get('GPS_coord[0]', 38.7312))
        real_lon = float(telemetry_data.get('GPS_coord[1]', 35.4787))

        features = [
            float(telemetry_data.get('accSmooth[0]', 0.0)), float(telemetry_data.get('accSmooth[1]', 0.0)), float(telemetry_data.get('accSmooth[2]', 0.0)),
            float(telemetry_data.get('gyroADC[0]', 0.0)), float(telemetry_data.get('gyroADC[1]', 0.0)), float(telemetry_data.get('gyroADC[2]', 0.0)),
            float(telemetry_data.get('attitude[0]', 0.0)), float(telemetry_data.get('attitude[1]', 0.0)), float(telemetry_data.get('attitude[2]', 0.0)),
            float(telemetry_data.get('magADC[0]', 0.0)), float(telemetry_data.get('magADC[1]', 0.0)), float(telemetry_data.get('magADC[2]', 0.0)),
            float(telemetry_data.get('BaroAlt (cm)', 0.0)), float(telemetry_data.get('navVel[0]', 0.0)), float(telemetry_data.get('navVel[1]', 0.0)), float(telemetry_data.get('navVel[2]', 0.0))
        ]

        if not self.first_gps_lock:
            self.model_gps_x = real_lat
            self.model_gps_y = real_lon
            self.first_gps_lock = True
            for _ in range(29):
                self.imu_buffer.append(features)

        self.imu_buffer.append(features)

        oran = 0.0
        model_drift = 0.0
        
        if len(self.imu_buffer) == 30:
            with torch.no_grad():
                input_tensor = torch.tensor([list(self.imu_buffer)], dtype=torch.float32).to(self.device)
                predictions = self.ai_model(input_tensor)
                
                raw_lat = predictions[0][0].item()
                raw_lon = predictions[0][1].item()
                
                HIZ_CARPANI = 0.000005 
                self.model_gps_x += (raw_lat * HIZ_CARPANI)
                self.model_gps_y += (raw_lon * HIZ_CARPANI)

                diff_lat = abs(real_lat - self.model_gps_x)
                diff_lon = abs(real_lon - self.model_gps_y)
                model_drift = math.sqrt(diff_lat**2 + diff_lon**2) * 111000 

                if model_drift > 20.0: 
                    oran = min(1.0, model_drift / 100.0)
                else:
                    self.model_gps_x = self.model_gps_x * 0.90 + real_lat * 0.10
                    self.model_gps_y = self.model_gps_y * 0.90 + real_lon * 0.10

        # ==========================================================
        # GRAFİK VE VERİ FÜZYONU
        # ==========================================================
        # test_senaryosu.csv'den bir satır alıyoruz
        eski_grafik = next(self.grafik_iterator) 
        
        # Karma Veri Vektörü (İlk 6'sı test_senaryosu'ndan, son 2'si datas.csv'deki modelden hesaplanan)
        vektor = [
            float(eski_grafik[0]),  # 1. mean_cno
            float(eski_grafik[1]),  # 2. std_cno
            float(eski_grafik[2]),  # 3. mean_prRes
            float(eski_grafik[3]),  # 4. std_prRes
            float(eski_grafik[4]),  # 5. max_prRes
            float(eski_grafik[5]),  # 6. num_used
            float(model_drift),     # 7. SİPER MODEL SAPMASI (datas.csv)
            float(oran * 100)       # 8. SİPER RİSK ORANI (datas.csv)
        ]
        
        self.graph_update(oran, vektor)
        self.update_map_position(real_lat, real_lon, self.model_gps_x, self.model_gps_y)
        
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
                'GPS_coord[0]': real_lat,
                'GPS_coord[1]': real_lon,
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
        # Grafikleri isimleri ve özel Neon renkleriyle tanımlıyoruz
        graph_details = [
            ("Mean_cno", "Ort. Sinyal Gücü (test_senaryosu)", '#00e5ff', (0, 229, 255)),
            ("std_cno", "Sinyal Kararsızlığı (test_senaryosu)", '#00e5ff', (0, 229, 255)),
            ("mean_prRes", "Pseudorange Hatası (test_senaryosu)", '#bc8cff', (188, 140, 255)),
            ("std_prRes", "Hata Sapması (test_senaryosu)", '#bc8cff', (188, 140, 255)),
            ("max_prRes", "Anomali Piki (test_senaryosu)", '#bc8cff', (188, 140, 255)),
            ("num_used", "Kullanılan Uydu (test_senaryosu)", '#f8b229', (248, 178, 41)),
            ("MODEL_SAPMASI", "SİPER AI - Tahmini Konum Sapması (Metre) [KRİTİK]", '#ff9100', (255, 145, 0)),
            ("SPOOF_RISK", "SİPER AI - Siber Saldırı Olasılığı (%) [KRİTİK]", '#ff003c', (255, 0, 60))
        ]
        
        self.graph_list = []
        for name, desc, c_hex, c_rgb in graph_details:
            lbl = QLabel(f"📍 {name} | {desc}")
            lbl.setStyleSheet(f"color: {c_hex}; font-size: 13px; font-weight: bold; margin-top: 15px; margin-bottom: 2px;")
            self.main_layout.addWidget(lbl)
            
            graph = PgGraph(name, "Zaman", c_hex=c_hex, c_rgb=c_rgb)
            self.graph_list.append(graph)
            self.main_layout.addWidget(graph)

    def graph_update(self, oran, vektor):
        if hasattr(self, 'graph_list'):
            for i, value in enumerate(vektor):
                if i < len(self.graph_list):
                    # Direct data set yerine yumuşatma fonksiyonunu çağırıyoruz
                    self.graph_list[i].update_value(value, alpha=0.2)
        
        if oran > 0.5:
            self.setWindowTitle(f"UYARI: SALDIRI TESPİT EDİLDİ! (%{oran*100:.2f})")
        else:
            self.setWindowTitle(f"Durum Normal (%{oran*100:.2f})")