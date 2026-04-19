import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        # Zaman serilerindeki ardışıklığı (hangi veri önce geldi) modele öğretmek için
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.pe = pe.unsqueeze(0) # Şekil: (1, max_len, d_model)

    def forward(self, x):
        # x şekli: (batch_size, sequence_length, d_model)
        x = x + self.pe[:, :x.size(1), :].to(x.device)
        return x

class UAVInertialTransformer(nn.Module):
    def __init__(self, input_dim, d_model=128, nhead=8, num_layers=4, dropout=0.1):
        """
        input_dim: Kaç adet sensör verisi veriyoruz? (Örn: acc[3] + gyro[3] + mag[3] + baro[1] = 10)
        d_model: Transformer'ın iç gömme (embedding) boyutu
        nhead: Attention (Dikkat) kafa sayısı
        num_layers: Transformer Encoder katman sayısı
        """
        super(UAVInertialTransformer, self).__init__()
        
        # 1. Sensör verilerini Transformer'ın anlayacağı geniş boyuta eşle (Linear Embedding)
        self.feature_embedding = nn.Linear(input_dim, d_model)
        
        # 2. Zaman bilgisini ekle
        self.pos_encoder = PositionalEncoding(d_model)
        
        # 3. Transformer Encoder (Kalp)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 4. Çıktı Katmanı (3 boyutlu hız vektörü tahmini: navVel_X, navVel_Y, navVel_Z)
        self.decoder = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, 3) # Çıktı boyutu: 3
        )

    def forward(self, src):
        # src şekli: (batch_size, sequence_length, input_dim) -> (Örn: 32, 50, 10)
        x = self.feature_embedding(src)
        x = self.pos_encoder(x)
        
        # Veriyi dikkat mekanizmasından geçir
        encoded = self.transformer_encoder(x)
        
        # Sadece zaman penceresinin en sonundaki (t anındaki) birikimli bilgiyi al
        last_time_step = encoded[:, -1, :] 
        
        # Çıktıya dönüştür (3 boyutlu hız)
        out = self.decoder(last_time_step)
        
        return out