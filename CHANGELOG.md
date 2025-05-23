# Değişiklik Günlüğü

Bu dosya, ZEKA projesindeki tüm önemli değişiklikleri belgelemektedir.

## [Yayınlanmamış]

### Eklenenler
- Python 3.13 uyumluluğu
- Temel paketler için sürüm kısıtlamaları optimize edildi
- Bağımlılık çakışmalarını önlemek için requirements.txt dosyası güncellendi

### Değişenler
- requirements.txt dosyası Python 3.13 ile uyumlu olacak şekilde yeniden düzenlendi
- Bazı gelişmiş özellikler için paketler opsiyonel hale getirildi
- README.md dosyası Python 3.13 uyumluluğu bilgisiyle güncellendi

### Düzeltilenler
- "resolution-too-deep" hatası çözüldü
- orjson paketi için belirli bir sürüm (3.9.15) belirtildi
- Tekrarlanan bağımlılıklar kaldırıldı
- İçe aktarma yolları düzeltildi (src.core -> core)
- Eksik paketler için yedek sınıflar eklendi (pvporcupine, pyautogui, vb.)

## [0.2.0] - 2024-XX-XX

### Eklenenler
- Masaüstü denetleyicisi entegrasyonu
- Ekran görüntüsü alma ve OCR ile metin tanıma
- Dosya gezgini entegrasyonu
- Pencere yönetimi
- Sistem bilgisi görüntüleme
- Uygulama kontrolü

### Değişenler
- Modüler mimari yeniden yapılandırması
- API rotaları yeniden düzenlendi
- Frontend bileşenleri güncellendi

### Düzeltilenler
- Asenkron işleme optimizasyonu
- Hata yönetimi iyileştirmesi
- Bellek sızıntıları giderildi

## [0.1.0] - 2024-XX-XX

### Eklenenler
- OpenRouter API entegrasyonu
- Vektör veritabanı entegrasyonu
- Semantik arama yetenekleri
- Çoklu dil modeli desteği
- Temel MCP entegrasyonu

### Değişenler
- Arayüz tasarımı güncellendi
- Performans iyileştirmeleri

### Düzeltilenler
- API isteklerinde zaman aşımı sorunları
- Bellek yönetimi sorunları
