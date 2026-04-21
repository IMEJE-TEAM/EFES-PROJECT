import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, random_split
import math

# =====================================================================
# VERİ İŞLEME VE DELTA (FARK) MATEMATİĞİ
# =====================================================================

def prepare_telemetry_data(df):
    """
    Ham veriyi alır, GPS verilerini bir önceki saniyeye göre
    farklara (delta) dönüştürür ve sızıntı yapan etiketleri siler.
    """
    # 1. Delta (Yer Değiştirme) Hesabı
    df['delta_GPS_0'] = df['GPS_coord[0]'].diff().fillna(0)
    df['delta_GPS_1'] = df['GPS_coord[1]'].diff().fillna(0)
    df['delta_GPS_alt'] = df['GPS_altitude'].diff().fillna(0)
    
    # 2. Silinecek Çöp Veriler ve GPS Sızıntıları
    drop_columns = [
        'time (us)', 'escTemperature', 'vbat (V)', 'amperage (A)', 
        'Battery Remaining (%)', 'rssi', 'navTgtPos[0]', 'navTgtPos[1]', 
        'navTgtPos[2]', 'wind[0]', 'wind[1]', 'wind[2]', 'distance_to_wp (m)', 
        'distance_to_home (m)', 'GPS_numSat', 'GPS_hdop', 'GPS_ground_course', 
        'GPS_speed (m/s)'
    ]
    
    # Sızıntıları veri setinden tamamen uçur
    df = df.drop(columns=[col for col in drop_columns if col in df.columns], errors='ignore')
    return df

# =====================================================================
# ZAMAN PENCERELİ DATASET SINIFI (TRANSFORMER İÇİN)
# =====================================================================

class TelemetryDataset(Dataset):
    def __init__(self, dataframe, seq_len=50):
        self.seq_len = seq_len
        
        # Girdi (X): GPS kesinlikle gizli. Sadece IMU ve Barometre. (Toplam 16 Sütun)
        feature_columns = [
            'accSmooth[0]', 'accSmooth[1]', 'accSmooth[2]',
            'gyroADC[0]', 'gyroADC[1]', 'gyroADC[2]',
            'attitude[0]', 'attitude[1]', 'attitude[2]',
            'magADC[0]', 'magADC[1]', 'magADC[2]',
            'BaroAlt (cm)', 'navVel[0]', 'navVel[1]', 'navVel[2]'
        ]
        
        # Çıktı (y): Sadece pencerenin sonundaki yer değiştirme farkı (Delta)
        label_columns = ['delta_GPS_0', 'delta_GPS_1', 'delta_GPS_alt']
        
        self.X = torch.tensor(dataframe[feature_columns].values, dtype=torch.float32)
        self.y = torch.tensor(dataframe[label_columns].values, dtype=torch.float32)
        
    def __len__(self):
        # KRİTİK: Son pencerelerin taşmasını önlemek için seq_len kadar kısaltıyoruz
        return len(self.X) - self.seq_len
    
    def __getitem__(self, idx):
        # KRİTİK: Model artık tek bir anı değil, "seq_len" uzunluğunda bir geçmişi görüyor!
        x_window = self.X[idx : idx + self.seq_len]
        
        # Hedef: Pencerenin tam bittiği andaki değişim
        y_target = self.y[idx + self.seq_len]
        return x_window, y_target

# =====================================================================
# DATALOADER OLUŞTURUCU (TRAIN.PY İÇİN KUSURSUZ UYUM)
# =====================================================================

# model2/dataset.py içindeki ilgili yer:

def get_dataloaders(csv_path, batch_size, seq_len=50):
    df = pd.read_csv(csv_path, nrows=700000)
    df_processed = prepare_telemetry_data(df)
    dataset = TelemetryDataset(df_processed, seq_len=seq_len)
    
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
    
    # DİKKAT: num_workers ve pin_memory eklendi!
    # num_workers=8 -> Arka planda 8 ayrı işlemci çekirdeği veri taşır.
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        drop_last=True,
        num_workers=8,        # <--- İŞÇİ SAYISI BURADA
        pin_memory=True       # <--- Veriyi RAM'de hazır bekletir, hızlandırır
    )
    
    test_loader = DataLoader(
        test_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        drop_last=True,
        num_workers=8,        # <--- İŞÇİ SAYISI BURADA
        pin_memory=True
    )
    
    return train_loader, test_loader
# =====================================================================
# KALKAN (SPOOFING SHIELD) MANTIĞI - (Fizik Yasalarıyla Tam Uyumlu)
# =====================================================================

class SpoofingShield:
    def __init__(self, max_speed_mps=20.0, drift_threshold=15.0):
        self.max_speed_mps = max_speed_mps       # Işınlanma Hız Sınırı (20m/s) - Modelin öğrendiği sınır
        self.drift_threshold = drift_threshold   # Hata Payı Sınırı (15 metre)
        self.last_clean_gps = None               
        
    def update_clean_gps(self, real_gps_x, real_gps_y):
        self.last_clean_gps = (real_gps_x, real_gps_y)
        
    def check_for_attack(self, real_gps_x, real_gps_y, pred_gps_x, pred_gps_y, dt_seconds=1.0):
        distance_diff = math.sqrt((real_gps_x - pred_gps_x)**2 + (real_gps_y - pred_gps_y)**2)
        
        # 1. Işınlanma Kontrolü (Eğitimdeki ceza fonksiyonunun canlı hali)
        if (distance_diff / dt_seconds) > self.max_speed_mps:
            return True # Spoofed!
            
        # 2. 15 Metre Sınırı
        if distance_diff > self.drift_threshold:
            return True # Spoofed!
            
        if distance_diff < 5.0:
            self.update_clean_gps(real_gps_x, real_gps_y)
            
        return False