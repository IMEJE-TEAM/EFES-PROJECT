import os
import sys
import pickle
import pandas as pd
import numpy as np
import math
import itertools
import warnings

import PyQt5.QtWidgets 
import pyqtgraph as pg
pg.setConfigOptions(useOpenGL=False, antialias=True) 

from collections import deque
from PyQt5.QtCore import *

# TensorFlow Uyarılarını ve Loglarını Kapat
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
from tensorflow.keras.models import load_model

# ==========================================
# 1. TELEMETRİ OKUYUCU (DATAS.CSV)
# ==========================================
class TelemetryWorker(QThread):
    telemetry_ready = pyqtSignal(dict)

    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path
        self.is_running = True

    def run(self):
        try:
            # Tıpkı istediğin gibi, arayüzü besleyecek olan ana veri datas.csv'den okunuyor!
            df = pd.read_csv(self.csv_path)
            for index, row in df.iterrows():
                if not self.is_running:
                    break
                self.telemetry_ready.emit(row.to_dict())
                self.msleep(30) # ~30 FPS Akıcılığı
        except Exception as e:
            print(f"[HATA] CSV Okuma Hatası: {e}")

    def stop(self):
        self.is_running = False
        self.wait()

# ==========================================
# 2. ARAYÜZ GRAFİK SINIFI (KIRMIZI SÜTUN DESTEKLİ)
# ==========================================
class PgGraph(pg.PlotWidget):
    def __init__(self, left_name:str, bottom_name:str, c_rgb=(57,255,20)):
        from PyQt5.QtWidgets import QApplication
        if QApplication.instance() is None:
            raise RuntimeError("QApplication must be created before PgGraph")
        super().__init__()
        self.setMinimumHeight(170)
        self.setBackground('#050907')
        self.getPlotItem().getViewBox().setBackgroundColor('#050907')
        self.showGrid(x=True, y=True, alpha=0.08)
        self.setLabel('left', left_name)
        self.setLabel('bottom', bottom_name)

        # Fare ile grafiği çekiştirmeyi kilitler
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

        self.data_points = 250 
        self.data = np.zeros(self.data_points) 
        self.first_run = True

        self.line_color = c_rgb
        self.kalem = pg.mkPen(color=self.line_color, width=2.5)
        self.baseline = self.plot(np.zeros(self.data_points), pen=pg.mkPen(None))
        self.cizgi = self.plot(self.data, pen=self.kalem)

        # Normal Dolgu
        r, g, b = self.line_color
        self.normal_fill = pg.FillBetweenItem(self.cizgi, self.baseline, brush=(r, g, b, 25))
        self.getPlotItem().addItem(self.normal_fill)

        # ========================================================
        # SİBER SALDIRI (SPOOFING) KIRMIZI SÜTUNLARI
        # ========================================================
        self.spoof_mask = np.zeros(self.data_points, dtype=bool)
        
        self.y0_array = np.full(self.data_points, -9999.0)
        self.danger_bars = pg.BarGraphItem(
            x=np.arange(self.data_points), 
            y0=self.y0_array, 
            height=np.zeros(self.data_points), 
            width=1.0, 
            brush=(255, 0, 50, 90), 
            pen=None
        )
        self.getPlotItem().addItem(self.danger_bars)

    def set_theme(self, is_dark: bool):
        pass

    def update_value(self, new_val, is_spoofing=False, alpha=0.15):
        if self.first_run:
            self.data.fill(new_val)
            self.first_run = False

        smoothed_val = (self.data[-1] * (1 - alpha)) + (new_val * alpha)

        self.data = np.roll(self.data, -1)
        self.data[-1] = smoothed_val

        self.spoof_mask = np.roll(self.spoof_mask, -1)
        self.spoof_mask[-1] = is_spoofing

        self.cizgi.setData(self.data)

        min_y = np.min(self.data)
        max_y = np.max(self.data)
        if min_y == max_y:
            pad = 1.0
        else:
            pad = (max_y - min_y) * 0.2
        self.getPlotItem().setYRange(min_y - pad, max_y + pad)

        heights = np.where(self.spoof_mask, 19999.0, 0.0)
        self.danger_bars.setOpts(height=heights)

# ==========================================
# 3. ANA MOTOR (KERAS MODEL VE ÇİFT VERİ AKIŞI)
# ==========================================
class Engine():
    def Thread(self):
        self.data_buffer = deque(maxlen=30)
        self.buffer_filled = False

        # 1. YAPAY ZEKA VERİSİ (Sadece grafikleri ve modeli besler)
        try:
            df_keras = pd.read_csv("model/test_senaryosu.csv")
            if 'Label' in df_keras.columns:
                df_keras = df_keras.drop(columns=['Label'])
            self.keras_iterator = itertools.cycle(df_keras.values)
        except Exception as e:
            print(f"[UYARI] test_senaryosu.csv bulunamadı: {e}")
            self.keras_iterator = itertools.cycle([np.zeros(8)])

        # 2. ARAYÜZ (GUI) VERİSİ (Senin istediğin model2/datas.csv)
        self.worker = TelemetryWorker(csv_path="model2/datas.csv")
        self.worker.telemetry_ready.connect(self.process_telemetry)
        self.worker.start()

    def load_model_scaler(self):
        print("[SİSTEM] Keras CRNN Modeli Yükleniyor...")
        self.ai_model = load_model("model/crnn_model.h5")
        with open("model/crnn_scaler.pkl", "rb") as f:
            self.ai_scaler = pickle.load(f)
        print("[BAŞARILI] SİPER AI Beyni Yüklendi ve Aktif!")

    def process_telemetry(self, telemetry_data):
        # A) YAPAY ZEKA HESAPLAMASI İÇİN KERAS VERİSİNİ AL (test_senaryosu.csv)
        keras_features = next(self.keras_iterator).tolist()

        if not self.buffer_filled:
            for _ in range(30):
                self.data_buffer.append(keras_features)
            self.buffer_filled = True
        
        self.data_buffer.append(keras_features)

        # Kalkan: Doğrudan TensorFlow Tensor kullanarak hızlandırılmış tahmin
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            data_array = np.array(list(self.data_buffer))
            scaled_data = self.ai_scaler.transform(data_array)
            
            tensor = tf.convert_to_tensor(scaled_data.reshape(1, 30, 8), dtype=tf.float32)
            oran = float(self.ai_model(tensor, training=False)[0][0])

        # B) ARAYÜZ İÇİN GERÇEK TELEMETRİYİ AL (model2/datas.csv)
        # Haritadaki kırmızı ikon tamamen bu koordinatları izleyecek!
        lat = float(telemetry_data.get('GPS_coord[0]', 38.7312))
        lon = float(telemetry_data.get('GPS_coord[1]', 35.4787))

        # Haritayı güncelle (4 parametre istiyordu, hepsini gerçek veriden verdik)
        self.update_map_position(lat, lon, lat, lon)

        # Grafik Vektörü (8'i Keras'tan, 2'si Çıktıdan)
        vektor = [
            float(keras_features[0]), # Mean_cno
            float(keras_features[1]), # Std_cno
            float(keras_features[2]), # Mean_prRes
            float(keras_features[3]), # Std_prRes
            float(keras_features[4]), # Max_prRes
            float(keras_features[5]), # Num_used
            float(keras_features[6]), # Num_visible
            float(keras_features[7]), # Cno_elev_ratio
            float(oran * 50),         # Model Sapması
            float(oran * 100)         # SİPER RİSK ORANI (%)
        ]
        
        self.graph_update(oran, vektor)

        # C) İHA TELEMETRİ VE SİSTEM PANELİ İÇİN GERÇEK VERİ SÖZLÜĞÜ (datas.csv)
        formatted_telemetry = {
            'GPS_ground_speed': float(telemetry_data.get('GPS_speed (m/s)', 0.0)),
            'GPS_altitude': float(telemetry_data.get('GPS_altitude', 1200.0)),
            'GPS_ground_course': float(telemetry_data.get('GPS_ground_course', 0.0)),
            'verticalSpeed': float(telemetry_data.get('navVel[2]', 0.0)),
            'GPS_hdop': float(telemetry_data.get('GPS_hdop', 1.0)),
            'GPS_numSat': int(telemetry_data.get('GPS_numSat', 12)),
            'navState': 'AUTO-NAV' if oran < 0.5 else 'SİBER MÜDAHALE',
            'GPS_coord[0]': lat,
            'GPS_coord[1]': lon,
            'escTemperature': float(telemetry_data.get('escTemperature', 35.0)),
            'vbat': float(telemetry_data.get('vbat (V)', 24.2)),
            'rssi': float(telemetry_data.get('rssi', 99.0)),
            'activeWpNumber': int(telemetry_data.get('activeWpNumber', 1)),
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

        # İki sekmeyi de datas.csv'den gelen taze veriyle güncelliyoruz!
        if hasattr(self, 'settings_page'):
            self.settings_page.update_sys_telemetry(formatted_telemetry)
        if hasattr(self, 'iha_page'):
            self.iha_page.update_telemetry(formatted_telemetry)

    def graph_create_add(self):
        from PyQt5.QtWidgets import QLabel
        graph_details = [
            ("Mean_cno", "Ortalama C/N0 (Sinyal Gücü)", '#00e5ff', (0, 229, 255)),
            ("std_cno", "C/N0 Standart Sapması", '#00e5ff', (0, 229, 255)),
            ("mean_prRes", "Pseudorange Residual (Ortalama)", '#bc8cff', (188, 140, 255)),
            ("std_prRes", "Pseudorange Residual (Sapma)", '#bc8cff', (188, 140, 255)),
            ("max_prRes", "Maksimum Pseudorange Hatası", '#bc8cff', (188, 140, 255)),
            ("num_used", "Kullanılan Uydu Sayısı", '#f8b229', (248, 178, 41)),
            ("num_visible", "Görünür Uydu Sayısı", '#f8b229', (248, 178, 41)),
            ("cno_elev_ratio", "Sinyal / Yükseklik Oranı", '#f8b229', (248, 178, 41)),
            ("MODEL_SAPMASI", "SİPER AI - Tahmini Konum Sapması", '#ff9100', (255, 145, 0)),
            ("SPOOF_RISK", "SİPER AI - Siber Saldırı Olasılığı (%) [KRİTİK]", '#ff003c', (255, 0, 60))
        ]
        
        self.graph_list = []
        for name, desc, c_hex, c_rgb in graph_details:
            lbl = QLabel(f"📍 {name} | {desc}")
            lbl.setStyleSheet(f"color: {c_hex}; font-size: 13px; font-weight: bold; margin-top: 15px; margin-bottom: 2px;")
            self.main_layout.addWidget(lbl)
            
            graph = PgGraph(name, "Zaman", c_rgb=c_rgb)
            self.graph_list.append(graph)
            self.main_layout.addWidget(graph)

    def graph_update(self, oran, vektor):
        is_attack = oran > 0.5 

        if hasattr(self, 'graph_list'):
            for i, value in enumerate(vektor):
                if i < len(self.graph_list):
                    self.graph_list[i].update_value(value, is_spoofing=is_attack, alpha=0.2)
        
        if is_attack:
            self.setWindowTitle(f"UYARI: SALDIRI TESPİT EDİLDİ! (%{oran*100:.2f})")
        else:
            self.setWindowTitle(f"Durum Normal (%{oran*100:.2f})")