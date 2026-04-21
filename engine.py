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
            # Gerçek zamanlı uçuşu simüle etmek için satır satır okuyup gecikme veriyoruz
            df = pd.read_csv(self.csv_path)
            for index, row in df.iterrows():
                if not self.is_running:
                    break
                self.telemetry_ready.emit(row.to_dict())
                self.msleep(100) # 100ms = 10Hz Yayın Hızı
        except Exception as e:
            print(f"Telemetri Hatası: {e}")

    def stop(self):
        self.is_running = False
        self.wait()

# ==========================================
# 2. ARAYÜZ GRAFİK SINIFI
# ==========================================
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

        self.kalem = pg.mkPen(color=(219, 37, 8), width=2)
        self.data = np.zeros(1000)
        self.baseline = self.plot(np.zeros(1000), pen=pg.mkPen(None))
        self.cizgi = self.plot(self.data, pen=self.kalem)
        self.fill = pg.FillBetweenItem(self.cizgi, self.baseline, brush=(219, 37, 8, 40))
        self.getPlotItem().addItem(self.fill)
        self.getPlotItem().getViewBox().setMouseEnabled(x=False, y=False)

    def set_theme(self, is_dark: bool):
        if is_dark:
            self.setBackground('#000000') 
            self.getPlotItem().getViewBox().setBackgroundColor('#000000')
            self.showGrid(x=True, y=True, alpha=0.18)
            self.kalem.setColor(pg.mkColor(219, 37, 8))
        else:
            self.setBackground('#1f1f1f') 
            self.getPlotItem().getViewBox().setBackgroundColor('#1f1f1f')
            self.showGrid(x=True, y=True, alpha=0.18)
            self.kalem.setColor(pg.mkColor(219, 37, 8))
        self.cizgi.setPen(self.kalem)
            
# ==========================================
# 3. ANA MOTOR (SİPER YAPAY ZEKA MERKEZİ)
# ==========================================
class Engine():
    def Thread(self):
        # SİPER AI İçin Hafıza Tanımlamaları
        self.imu_buffer = deque(maxlen=30) # 30 Adımlık geçmişi tutar (SEQ_LEN)
        self.first_gps_lock = False
        
        # Hayalet İkon (Mavi - Model) ve Gerçek İkon (Yeşil - GPS) koordinatları
        self.model_gps_x = 0.0
        self.model_gps_y = 0.0

        # Tek bir Telemetri Worker'ı ile hem UI hem AI besleniyor
        self.telemetry_worker = TelemetryWorker(csv_path="model2/datas.csv")
        self.telemetry_worker.telemetry_ready.connect(self.process_telemetry)
        self.telemetry_worker.start()

    def load_model_scaler(self):
        # Eski Keras kodlarını sildik, PyTorch modelini cihaz hafızasına alıyoruz.
        self.device = torch.device("cpu")
        print("[SİSTEM] PyTorch SİPER AI Modeli CPU üzerinde başlatılıyor...")
        
        # Model mimarisi train.py'deki ile BİREBİR aynı olmalı
        self.ai_model = UAVInertialTransformer(input_dim=16, d_model=128, nhead=8, num_layers=4, dropout=0.15)
        
        model_path = "uav_transformer_best.pth"
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            self.ai_model.load_state_dict(checkpoint['model_state_dict'])
            print("[BAŞARILI] SİPER AI Beyni Yüklendi ve Aktif!")
        else:
            print("[KRİTİK HATA] Model ağırlıkları bulunamadı! Lütfen .pth dosyasını ana klasöre koyun.")
            
        self.ai_model.to(self.device)
        self.ai_model.eval()

    def process_telemetry(self, telemetry_data):
        # 1. Gerçek GPS (Uydudan gelen potansiyel tehlikeli veri)
        real_lat = float(telemetry_data.get('GPS_coord[0]', 38.7312))
        real_lon = float(telemetry_data.get('GPS_coord[1]', 35.4787))

        if not self.first_gps_lock:
            self.model_gps_x = real_lat
            self.model_gps_y = real_lon
            self.first_gps_lock = True

        # 2. Model için 16 Sütunluk Fiziksel Veriyi Çekiyoruz (GPS YOK!)
        features = [
            float(telemetry_data.get('accSmooth[0]', 0.0)), float(telemetry_data.get('accSmooth[1]', 0.0)), float(telemetry_data.get('accSmooth[2]', 0.0)),
            float(telemetry_data.get('gyroADC[0]', 0.0)), float(telemetry_data.get('gyroADC[1]', 0.0)), float(telemetry_data.get('gyroADC[2]', 0.0)),
            float(telemetry_data.get('attitude[0]', 0.0)), float(telemetry_data.get('attitude[1]', 0.0)), float(telemetry_data.get('attitude[2]', 0.0)),
            float(telemetry_data.get('magADC[0]', 0.0)), float(telemetry_data.get('magADC[1]', 0.0)), float(telemetry_data.get('magADC[2]', 0.0)),
            float(telemetry_data.get('BaroAlt (cm)', 0.0)), float(telemetry_data.get('navVel[0]', 0.0)), float(telemetry_data.get('navVel[1]', 0.0)), float(telemetry_data.get('navVel[2]', 0.0))
        ]
        self.imu_buffer.append(features)

        # ==========================================================
        # SİPER KALKANI - YAPAY ZEKA KONTROLÜ
        # ==========================================================
        oran = 0.0
        model_drift = 0.0
        
        # Eğer buffer dolduysa (30 satır) yapay zeka tahmine başlar
        if len(self.imu_buffer) == 30:
            with torch.no_grad():
                # Veriyi Tensöre çevir ve boyutunu [1, 30, 16] yap
                input_tensor = torch.tensor([list(self.imu_buffer)], dtype=torch.float32).to(self.device)
                
                # Model Çıktısı (Delta: saniyedeki tahmini yer değiştirme)
                predictions = self.ai_model(input_tensor)
                delta_lat = predictions[0][0].item()
                delta_lon = predictions[0][1].item()
                
                # Modelin hesapladığı Güvenli "Hayalet" Koordinat
                self.model_gps_x += delta_lat
                self.model_gps_y += delta_lon

                # MANTIK TESTİ: Gerçek GPS ile Modelin Tahmini arasındaki mesafeyi ölç
                diff_lat = abs(real_lat - self.model_gps_x)
                diff_lon = abs(real_lon - self.model_gps_y)
                
                # Matematiksel sapma oranını "Metre" tarzı okunabilir bir formata çekiyoruz
                model_drift = math.sqrt(diff_lat**2 + diff_lon**2) * 50000 

                # KALKAN KURALI: Eğer fark çok açıldıysa SPOOFING ilan et
                if model_drift > 15.0: # 15 birimlik/metrelik sapma tespiti
                    oran = min(1.0, model_drift / 50.0) # Tehlike Skoru (0.0 ile 1.0 arası)
                else:
                    # Rüzgar gibi doğal kaymaları önlemek için eğer saldırı yoksa 
                    # modelin konumunu ara sıra gerçeğe bağlayarak sıfırla.
                    self.model_gps_x = real_lat
                    self.model_gps_y = real_lon

        # ==========================================================
        # UI VE GRAFİK GÜNCELLEMELERİ
        # ==========================================================
        # Arayüzdeki 8'li grafik için özellikleri ayarlıyoruz (Eski sinyal özelliklerini simüle veya by-pass ediyoruz)
        vektor = [
            float(telemetry_data.get('GPS_numSat', 12) * 3), # Mean_cno (Mock)
            float(telemetry_data.get('GPS_hdop', 1.0)),      # std_cno
            float(model_drift),                              # Model Sapma Değeri (ÇOK ÖNEMLİ)
            float(model_drift * 0.2),                        # Sapma Standartı
            float(model_drift * 1.5),                        # Maksimum Sapma
            float(telemetry_data.get('GPS_numSat', 12)),
            float(telemetry_data.get('GPS_numSat', 12) + 2),
            float(1.5 + (oran * 2))                          # Saldırı anında fırlayan oran
        ]
        self.graph_update(oran, vektor)

        # Haritayı İKİ FARKLI NOKTA ile besle (Hem Gerçek Hem Hayalet)
        self.update_map_position(real_lat, real_lon, self.model_gps_x, self.model_gps_y)
        
        # Yan Panelleri Güncelle
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
        
        # Grafik isimleri ve açıklamaları
        graph_details = [
            ("Mean_cno", "Ortalama Sinyal Gücü - Sentetik Veri"),
            ("std_cno", "HDOP Dalgalanması - Konum Hassasiyeti"),
            ("MODEL_SAPMASI", "SİPER AI - Tahmini Konum ile GPS Arasındaki Mesafe Sapması (KRİTİK)"),
            ("std_prRes", "Hesaplama Hata Payı - Standart Sapma"),
            ("max_prRes", "Maksimum Fiziksel Anomaliler - Saldırı Anında Pik Yapar"),
            ("num_used", "Kullanılan Uydu Sayısı (Gerçek Zamanlı)"),
            ("num_visible", "Görünür Uydu Sayısı (Gerçek Zamanlı)"),
            ("SPOOF_RISK", "Yapay Zeka Anomali Katsayısı - Doğal Olmayan Haraket Oranı")
        ]
        
        self.graph_list = []
        for name, desc in graph_details:
            lbl = QLabel(f"📍 {name} | {desc}")
            lbl.setStyleSheet("color: #a0a0c0; font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
            self.main_layout.addWidget(lbl)
            
            graph = PgGraph(name, "Zaman")
            self.graph_list.append(graph)
            self.main_layout.addWidget(graph)


    def graph_update(self, oran, vektor):
        # Eğer grafik listesi arayüzde oluşturulduysa verileri kaydırarak ekle
        if hasattr(self, 'graph_list'):
            for i, value in enumerate(vektor):
                if i < len(self.graph_list):
                    self.graph_list[i].data = np.roll(self.graph_list[i].data, -1)
                    self.graph_list[i].data[-1] = value
                    self.graph_list[i].cizgi.setData(self.graph_list[i].data)
        
        # Pencere başlığını ve tehlike durumunu güncelle
        if oran > 0.5:
            self.setWindowTitle(f"UYARI: SALDIRI TESPİT EDİLDİ! (%{oran*100:.2f})")
        else:
            self.setWindowTitle(f"Durum Normal (%{oran*100:.2f})")