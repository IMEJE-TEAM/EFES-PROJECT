# 🛡️ SİPER: Dual-Model UAV Anti-Spoofing System

![EFES-2026](https://img.shields.io/badge/Project-EFES--2026-darkblue?style=for-the-badge)
![Defense-Tech](https://img.shields.io/badge/Field-Defense%20Tech-red?style=for-the-badge)
![AI-Powered](https://img.shields.io/badge/Focus-AI%20Powered-green?style=for-the-badge)

**SİPER**, insansız hava araçlarına (İHA) yönelik gerçekleştirilen GNSS spoofing saldırılarını milisaniyeler içinde tespit eden ve **BKZS-AURA** algoritması ile otonom müdahale sağlayan ileri seviye bir yapay zekâ platformudur.

---

## 🛰️ I. MİSYON VE STRATEJİK VİZYON
**SİPER**, gökyüzündeki egemenliğimizin dijital teminatıdır. Modern harp sahasında İHA sistemlerinin güvenliği, sadece uçuş kabiliyetine değil, verinin doğruluğuna bağlıdır. Projemiz, GNSS verilerini anlık analiz ederek sahte sinyalleri izole eder ve milli savunma teknolojilerinde dijital **"Siper"** görevini üstlenir.

---

## 🏗️ II. SİSTEM MİMARİSİ: ÇİFT KATMANLI KORUMA
SİPER, birbirini doğrulayan ve ardışık çalışan iki ana yapay zekâ katmanı üzerine inşa edilmiştir:

### 🔍 KATMAN 1: DETECTION MODEL (TEŞHİS)
* **Mimari:** 1D CNN + Transformer (CRNN) Hibrit Yapısı.
* **Analiz Kapasitesi:** Ham GNSS sinyalleri saniyede 30 kez denetlenir.
* **Doğruluk Oranı:** %98+ başarı ile anomali tespiti yapılır.

### 🧠 KATMAN 2: BKZS-AURA (MÜDAHALE VE ADAPTASYON)
**BKZS-AURA (Akıllı Uygulama ve Rotalama Algoritması)**, saldırı anında kontrolü devralan karar mekanizmasıdır.

* **Siber Tahkimat:** Saldırı tespit edildiği anda sahte veri izole edilir; navigasyon **IMU** ve **VIO (Görsel Odometri)** sistemine aktarılır.
* **Dinamik Rotalama:** **D* Lite** algoritması ile tehdit bölgeleri "yüksek maliyetli alan" tanımlanır ve otonom yeni rota çizilir.
* **Çevresel Entegrasyon:** Canlı Hava Durumu API verileriyle rüzgar/yağış limitlerine göre otomatik irtifa optimizasyonu yapılır.

---

## 🧬 III. VERİ STRATEJİSİ VE SİMÜLASYON
Fiziksel test kısıtlarını aşmak ve sistemi en zorlu koşullara hazırlamak için **Simulation-Based Validation** yöntemi kullanılmıştır:
* **Sentetik Veri Jeneratörü:** Milyonlarca farklı saldırı senaryosu ile eğitilmiş modeller.
* **Hibrit İzleme:** Siber saldırı (Spoofing) ve çevresel faktörlerin (Hava Durumu) eş zamanlı analizi.

---

## 👥 IV. İMEJE PROJE EKİBİ

| Üye İsmi | Ünvan | Uzmanlık Alanı |
| :--- | :--- | :--- |
| **Arda ÖZTÜRK** | **Team Captain** | System Architect & Strategic Planning |
| **Naim Furkan ŞAHİN** | **AI & Data Engineer** | AI Architecture & Project Communication |
| **Mehmet Akif YILDIRIMLI** | **AI Model Developer** | Deep Learning & Signal Processing |
| **Emirhan HARPUT** | **Data Scientist** | Synthetic Data Generation & Analytics |
| **Osman Fadıl ELİYATKIN** | **Integration Engineer** | Model-UI Deployment & Backend |

---

## 📅 V. STRATEJİK YOL HARİTASI (ROADMAP)
- [x] **Faz 1:** Kavramsal Mimari ve Veri Üretim Hattı Tasarımı
- [x] **Faz 2:** Detection Model v1.0 Eğitimi ve Sentetik Validasyon
- [ ] **Faz 3:** BKZS-AURA Algoritmik Entegrasyonu ve Stres Testleri (Simülasyon)
- [ ] **Faz 4:** EFES-2026 Teknik Sunum Dosyası ve Final Raporlama

---

## 📜 VI. LİSANS VE BİLGİLENDİRME
Bu proje, **Trabzon Üniversitesi Yapay Zekâ Mühendisliği** bünyesinde EFES-2026 Tatbikatı başvurusu kapsamında **İMEJE Takımı** tarafından geliştirilmiştir. Tüm hakları saklıdır.

---
<p align="center">
  <b>#EFES2026 #SİPER #SavunmaSanayii #MilliTeknolojiHamlesi #İmejeTeam</b>
</p>