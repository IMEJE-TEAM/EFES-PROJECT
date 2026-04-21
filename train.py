import sys
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import matplotlib.pyplot as plt

# Yolları düzelt
sys.path.append(os.getcwd())
from model2.uav_transformer import UAVInertialTransformer
from model2.dataset import get_dataloaders
import torch
import multiprocessing

# Ryzen 9'un çekirdeklerini sonuna kadar kullanmaya zorla!
# Sistemindeki fiziksel ve sanal çekirdek sayısını otomatik bulur ve PyTorch'a atar.
core_count = multiprocessing.cpu_count()
torch.set_num_threads(core_count)
print(f"[BİLGİ] PyTorch matris işlemleri için {core_count} adet thread kullanacak!")
# =====================================================================
# 1. KESİN VE ZORUNLU CİHAZ SEÇİMİ (SADECE CPU)
# =====================================================================
# CUDA aramalarını ve denemelerini tamamen kaldırdık. 
# Sistem direkt olarak işlemciye (CPU) yönlendirildi.
DEVICE = torch.device("cpu")
print("[SİSTEM] Eğitim doğrudan işlemci (CPU) üzerinde başlıyor!")

# =====================================================================
# 2. FİZİK YASALARI (Fizik Temelli Ceza Fonksiyonu)
# =====================================================================
def physics_informed_loss(predictions, targets, dt=1.0, max_speed=20.0):
    """
    Fiziksel Kısıtlama: Dronun tahmin edilen hızı 20m/s'yi geçerse (ışınlanma)
    modele devasa bir hata puanı (ceza) verir.
    """
    pred_speed = torch.sqrt(predictions[:, 0]**2 + predictions[:, 1]**2) / dt
    penalty = torch.relu(pred_speed - max_speed) ** 2
    return penalty.mean()

# =====================================================================
# 3. ANA EĞİTİM FONKSİYONU
# =====================================================================
def train_model(csv_path):
    SEQ_LEN = 30
    INPUT_DIM = 16 # 3 Acc + 3 Gyro + 3 Att + 3 Mag + 1 Baro + 3 NavVel
    BATCH_SIZE = 512 # CPU'da bellek şişmesin diye 32 ideal
    EPOCHS = 10     # İsteğin üzerine 10 Epoch'a düşürüldü
    LEARNING_RATE = 1e-4

    print("[SİSTEM] Dataloader'lar hazırlanıyor...")
    train_loader, test_loader = get_dataloaders(csv_path, batch_size=BATCH_SIZE, seq_len=SEQ_LEN)
    
    print("[SİSTEM] Model mimarisi oluşturuluyor ve işlemciye gönderiliyor...")
    model = UAVInertialTransformer(input_dim=INPUT_DIM, d_model=128, nhead=8, num_layers=4, dropout=0.15)
    model = model.to(DEVICE)
    
    # Optimizasyon ve Öğrenme Oranı Ayarları
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    criterion = nn.SmoothL1Loss()
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_loss = float('inf')
    total_batches = len(train_loader)

    # Grafik verilerini tutacak listeler
    history_train_loss = []
    history_val_loss = []
    history_lr = []
    
    print("\n[SİSTEM] Eğitim Motorları Ateşlendi!\n" + "="*50)
    
    # Eğitim Döngüsü
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0
        start_time = time.time()
        
        for batch_idx, (x, y) in enumerate(train_loader):
            x, y = x.to(DEVICE), y.to(DEVICE)
            
            optimizer.zero_grad()
            predictions = model(x)
            
            # 1. Standart İstatistiksel Hata
            base_loss = criterion(predictions, y)
            
            # 2. Fiziksel Ceza
            phys_penalty = physics_informed_loss(predictions, y)
            
            # 3. Toplam Hata (Ceza katsayısı 0.5)
            loss = base_loss + (0.5 * phys_penalty)
            
            loss.backward()
            
            # Gradyan Patlamasını Önle
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            epoch_loss += loss.item()

            # Terminal Animasyonu
            percent = 100. * (batch_idx + 1) / total_batches
            print(f"\r[Epoch {epoch+1}/{EPOCHS}] İlerleme: [%{percent:.1f}] Batch: {batch_idx+1}/{total_batches} | Anlık Hata: {loss.item():.6f}", end="")
            
        avg_train_loss = epoch_loss / total_batches
        print() 
        
        # Validasyon (Test) Döngüsü
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in test_loader:
                x, y = x.to(DEVICE), y.to(DEVICE)
                preds = model(x)
                
                # Test aşamasında sadece base_loss bakılır
                loss = criterion(preds, y) 
                val_loss += loss.item()
                
        avg_val_loss = val_loss / len(test_loader)
        scheduler.step(avg_val_loss)
        
        # Grafik için verileri kaydet
        history_train_loss.append(avg_train_loss)
        history_val_loss.append(avg_val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        history_lr.append(current_lr)

        epoch_time = time.time() - start_time
        print(f"Epoch {epoch+1:03d}/{EPOCHS} | Süre: {epoch_time:.1f}s | Train Loss: {avg_train_loss:.6f} | Val Loss: {avg_val_loss:.6f} | LR: {current_lr:.6f}")
        
        # En İyi Modeli Kaydet
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': best_val_loss,
            }, "uav_transformer_best.pth")
            print(f" -> [KAYDEDİLDİ] Yeni en iyi model! Loss: {best_val_loss:.6f}")
            
        print("-" * 65)

    # =====================================================================
    # 4. GRAFİKLERİ ÇİZ VE KAYDET
    # =====================================================================
    print("\n[SİSTEM] Eğitim tamamlandı! Grafikler çiziliyor...")
    
    output_dir = "model2"
    os.makedirs(output_dir, exist_ok=True)
    
    # Loss Grafiği
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, EPOCHS+1), history_train_loss, label='Train Loss', color='blue', linewidth=2)
    plt.plot(range(1, EPOCHS+1), history_val_loss, label='Validation Loss', color='red', linewidth=2)
    plt.title('Aura-Med V2 - Eğitim ve Doğrulama Hatası Değişimi')
    plt.xlabel('Epoch')
    plt.ylabel('Loss (SmoothL1Loss + Physics Penalty)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    loss_path = os.path.join(output_dir, "loss_grafigi.png")
    plt.savefig(loss_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Learning Rate Grafiği
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, EPOCHS+1), history_lr, label='Learning Rate', color='green', linewidth=2)
    plt.title('Aura-Med V2 - Öğrenme Oranı (LR) Düşüş Eğrisi')
    plt.xlabel('Epoch')
    plt.ylabel('Learning Rate')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    lr_path = os.path.join(output_dir, "learning_rate_grafigi.png")
    plt.savefig(lr_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[BAŞARILI] Tüm eğitim grafikleri '{output_dir}' klasörünün içine kaydedildi!")

if __name__ == "__main__":
    train_model("model2/datas.csv")