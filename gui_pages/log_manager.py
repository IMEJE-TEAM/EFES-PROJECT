import csv
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class LogManager:
    @staticmethod
    def save_log_file(main_window):
        if not hasattr(main_window, 'log_data') or len(main_window.log_data) == 0:
            QMessageBox.warning(main_window, "Uyarı", "Kaydedilecek log verisi bulunamadı!")
            return
            
        yol, _ = QFileDialog.getSaveFileName(main_window, "Logları Kaydet", "", "CSV Dosyaları (*.csv)")
        if yol:
            try:
                with open(yol, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(main_window.log_data)
                
                QMessageBox.information(main_window, "Başarılı", f"Loglar başarıyla kaydedildi:\n{yol}")
            except Exception as e:
                QMessageBox.critical(main_window, "Hata", f"Log kaydedilirken bir hata oluştu:\n{e}")

    @staticmethod
    def load_log_file(main_window):
        yol, _ = QFileDialog.getOpenFileName(main_window, "Log Yükle", "", "CSV Dosyaları (*.csv)")
        if yol:
            try:
                main_window.log_text.clear()
                main_window.log_text.append(f"--- YÜKLENEN LOG: {yol} ---\n")
                with open(yol, mode='r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    header = next(reader, None)
                    if header:
                        main_window.log_text.append(f"[BAŞLIK] {','.join(header)}")
                    for row in reader:
                        main_window.log_text.append(",".join(row))
            except Exception as e:
                QMessageBox.critical(main_window, "Hata", f"Log yüklenirken bir hata oluştu:\n{e}")