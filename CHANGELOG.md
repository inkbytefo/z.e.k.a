# Değişiklik Günlüğü

Bu dosya, ZEKA projesindeki tüm önemli değişiklikleri belgelemektedir.

## [2.1.0] - 2024-12-19 🎨 iOS 18 Tasarım Güncellemesi

### 🎨 Büyük UI/UX Yeniden Tasarımı - iOS 18 Stili

#### Eklenenler
- **Tam iOS 18 Tasarım Sistemi**
  - Glassmorphism efektleri ve backdrop blur
  - iOS 18 renk paleti ve tipografi (SF Pro font ailesi)
  - Tutarlı spacing, border radius ve shadow sistemi
  - iOS benzeri easing curve'leri ile smooth animasyonlar

- **Yeni Layout Mimarisi**
  - 3-sütunlu responsive grid layout
  - Dynamic Island tarzı voice control ile TopBar
  - SystemStatusPanel (sol) - iOS Settings stili
  - ConversationPanel (orta) - Messages app stili
  - ControlCenterPanel (sağ) - iOS Control Center stili

- **Gelişmiş Widget Sistemi**
  - iOS Control Center'dan ilham alan widget grid
  - Provider göstergeleri ile ModelSelectorWidget
  - Güvenli anahtar yönetimi ile APIKeysWidget
  - Saatlik tahmin ile WeatherWidget
  - Daha iyi performans için React.Suspense ile lazy loading

- **Gelişmiş Ses Entegrasyonu**
  - Web Speech API ile real-time konuşma tanıma
  - Asistan yanıtları için konuşma sentezi
  - Görsel ses aktivite göstergeleri
  - Sorunsuz voice-to-text input

- **Performans Optimizasyonları**
  - Component memoization için React.memo
  - Widget bileşenlerinin lazy loading'i
  - Daha iyi bundle boyutu için code splitting
  - Custom properties ile optimize edilmiş CSS
  - iOS benzeri görünümde smooth scrollbar'lar

#### Değişenler
- **Tam Frontend Yeniden Yazımı**
  - Cyber/futuristik temadan iOS 18 estetiğine geçiş
  - Katı layout'tan esnek responsive grid'e geçiş
  - Background animasyon görünürlüğü artırıldı (opacity: 0.6)
  - Typing animasyonları ile geliştirilmiş chat arayüzü

- **Kullanıcı Deneyimi İyileştirmeleri**
  - Top bar'da minimize edilmiş voice control
  - Daha iyi kontrast ile şeffaf chat arka planı
  - Hover efektleri ve micro-interaction'lar
  - Daha iyi görsel hiyerarşi ve bilgi yoğunluğu

#### Kaldırılanlar
- **Legacy Bileşenler**
  - ZEKA Avatar bileşeni (talep üzerine)
  - UI'daki küçük pulse efektleri
  - Eski cyber-style tasarım elementleri
  - Katı widget container sistemi

## [Yayınlanmamış] - Python 3.13 Uyumluluk

### Eklenenler
- Python 3.13 uyumluluğu
- Temel paketler için sürüm kısıtlamaları optimize edildi
- Bağımlılık çakışmalarını önlemek için requirements.txt dosyası güncellendi

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
