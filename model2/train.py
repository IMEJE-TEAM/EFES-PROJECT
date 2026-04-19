import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import time

# (Bir önceki mesajda yazdığımız UAVInertialTransformer sınıfının burada olduğunu varsayıyoruz)
from model import UAVInertialTransformer
from dataset import get_dataloaders

def train_model(csv_path):
    # 1. Hiperparametreler ve Cihaz Ayarları
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SİSTEM] Eğitim şu cihazda başlıyor: {DEVICE.type.upper()}")
    
    SEQ_LEN = 50
    INPUT_DIM = 10 # 3 Acc + 3 Gyro + 3 Mag + 1 Baro
    BATCH_SIZE = 128
    EPOCHS = 100
    LEARNING_RATE = 1e-4

    # 2. DataLoader ve Model Başlatma
    train_loader, test_loader = get_dataloaders(csv_path, batch_size=BATCH_SIZE, seq_len=SEQ_LEN)
    
    model = UAVInertialTransformer(input_dim=INPUT_DIM, d_model=128, nhead=8, num_layers=4, dropout=0.15)
    model.to(DEVICE)
    
    # 3. Savunma Sanayii Standartlarında Optimizasyon
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4) # AdamW ile L2 regülarizasyonu
    criterion = nn.SmoothL1Loss() # Huber Loss: Sensör gürültüsüne karşı zırh
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True) # Tıkanınca öğrenmeyi yavaşlat
    
    best_val_loss = float('inf')
    
    # 4. Eğitim Döngüsü
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0
        start_time = time.time()
        
        for batch_idx, (x, y) in enumerate(train_loader):
            x, y = x.to(DEVICE), y.to(DEVICE)
            
            optimizer.zero_grad()
            predictions = model(x)
            
            loss = criterion(predictions, y)
            loss.backward()
            
            # Gradyan Patlamasını Önle (Kusursuzluk detayı)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            epoch_loss += loss.item()
            
        avg_train_loss = epoch_loss / len(train_loader)
        
        # 5. Validasyon (Test) Döngüsü
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in test_loader:
                x, y = x.to(DEVICE), y.to(DEVICE)
                preds = model(x)
                loss = criterion(preds, y)
                val_loss += loss.item()
                
        avg_val_loss = val_loss / len(test_loader)
        scheduler.step(avg_val_loss) # Öğrenme oranını güncelle
        
        epoch_time = time.time() - start_time
        print(f"Epoch {epoch+1:03d}/{EPOCHS} | Süre: {epoch_time:.1f}s | Train Loss: {avg_train_loss:.6f} | Val Loss: {avg_val_loss:.6f}")
        
        # 6. En İyi Modeli Kaydet (Checkpointing)
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': best_val_loss,
            }, "uav_transformer_best.pth")
            print(f" -> [KAYDEDİLDİ] Yeni en iyi model! Loss: {best_val_loss:.6f}")

if __name__ == "__main__":
    train_model("datas.csv")