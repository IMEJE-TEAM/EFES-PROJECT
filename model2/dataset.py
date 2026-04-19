import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import RobustScaler
import joblib

class UAVInertialDataset(Dataset):
    def __init__(self, csv_path, sequence_length=50, is_training=True, scaler_path="imu_scaler.pkl"):
        """
        sequence_length: Modelin karar vermek için bakacağı geçmiş veri adımı (Örn: 50 satır = ~0.5 saniye)
        """
        self.seq_len = sequence_length
        self.is_training = is_training
        
        # 1. Veriyi Yükle
        print(f"[SİSTEM] Veri yükleniyor: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # 2. Girdiler (X) ve Çıktılar (Y)
        # Girdiler: İvme, Jiroskop, Manyetometre, Barometre
        feature_cols = [
            'accSmooth[0]', 'accSmooth[1]', 'accSmooth[2]',
            'gyroADC[0]', 'gyroADC[1]', 'gyroADC[2]',
            'magADC[0]', 'magADC[1]', 'magADC[2]',
            'BaroAlt (cm)'
        ]
        # Çıktılar: Hız Vektörleri (Koordinat değil, hız tahmin ediyoruz ki integral alabilelim)
        target_cols = ['navVel[0]', 'navVel[1]', 'navVel[2]']
        
        X_raw = df[feature_cols].values
        Y_raw = df[target_cols].values
        
        # 3. Zırhlı Ölçeklendirme (Robust Scaling)
        # Sadece eğitim verisiyle fit ediyoruz, testte aynı ölçeği kullanıyoruz
        if self.is_training:
            self.scaler_X = RobustScaler()
            self.scaler_Y = RobustScaler()
            X_scaled = self.scaler_X.fit_transform(X_raw)
            Y_scaled = self.scaler_Y.fit_transform(Y_raw)
            # Uçuş anında kullanmak üzere scaler'ı kaydet
            joblib.dump((self.scaler_X, self.scaler_Y), scaler_path)
            print("[SİSTEM] RobustScaler başarıyla eğitildi ve kaydedildi.")
        else:
            self.scaler_X, self.scaler_Y = joblib.load(scaler_path)
            X_scaled = self.scaler_X.transform(X_raw)
            Y_scaled = self.scaler_Y.transform(Y_raw)

        # 4. Sliding Window (Kayan Pencere) Üretimi
        self.X, self.Y = self._create_sequences(X_scaled, Y_scaled)
        print(f"[BAŞARILI] {len(self.X)} adet zaman penceresi oluşturuldu.")

    def _create_sequences(self, data_X, data_Y):
        xs, ys = [], []
        # Veriyi seq_len kadar kaydırarak paketle
        for i in range(len(data_X) - self.seq_len):
            xs.append(data_X[i : (i + self.seq_len)])
            ys.append(data_Y[i + self.seq_len]) # Pencerenin bittiği anın hızını tahmin et
        return np.array(xs), np.array(ys)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        # PyTorch Tensor'larına çevir
        return torch.tensor(self.X[idx], dtype=torch.float32), \
               torch.tensor(self.Y[idx], dtype=torch.float32)

def get_dataloaders(csv_path, batch_size=64, seq_len=50, split_ratio=0.8):
    # Veri setini baştan sona oku (Kronolojik sıra bozulmamalı!)
    full_dataset = UAVInertialDataset(csv_path, sequence_length=seq_len, is_training=True)
    
    train_size = int(split_ratio * len(full_dataset))
    test_size = len(full_dataset) - train_size
    
    # DİKKAT: random_split KULLANMIYORUZ! Zaman serisinde gelecekten geçmişe veri sızamaz.
    train_dataset = torch.utils.data.Subset(full_dataset, range(0, train_size))
    test_dataset = torch.utils.data.Subset(full_dataset, range(train_size, len(full_dataset)))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, drop_last=True)
    
    return train_loader, test_loader