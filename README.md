# ZEKA: Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı

ZEKA, kullanıcıların günlük görevlerini yönetmelerine yardımcı olan, kişiselleştirilmiş bir yapay zeka asistanıdır. Sesli komutları anlayabilir, metinleri okuyabilir, takvim yönetimi yapabilir, e-posta gönderebilir ve kod yazma konusunda yardımcı olabilir.

## 🎨 Yeni iOS 18 Tarzı Tasarım (v2.1.0)

ZEKA artık tamamen yenilenen iOS 18 tarzı arayüzü ile daha modern ve kullanıcı dostu bir deneyim sunuyor:

### ✨ Tasarım Özellikleri
- **iOS 18 Estetiği**: Glassmorphism efektleri, yumuşak köşeler ve subtle animasyonlar
- **Esnek Layout**: 3-sütunlu responsive tasarım (Sistem Durumu | Konuşma | Denetim Merkezi)
- **Denetim Merkezi**: iOS Control Center benzeri widget sistemi
- **Minimalist Voice Control**: TopBar'da Dynamic Island tarzı ses kontrolü
- **Şeffaf Chat Arka Planı**: Glassmorphism efektleri ile modern görünüm
- **Enhanced Background**: Daha görünür 3D arka plan animasyonları
- **Performance Optimized**: Lazy loading, React.memo ve code splitting

### 🏗️ Yeni Mimari
- **TopBar**: Navigation + minimized voice control
- **SystemStatusPanel**: iOS Settings tarzı real-time sistem durumu
- **ConversationPanel**: Messages app tarzı chat interface
- **ControlCenterPanel**: iOS Control Center tarzı widget grid

## Özellikler

- **Çoklu Ajan Mimarisi**: Farklı görevler için uzmanlaşmış ajanlar arasında işbirliği.
- **Sesli Etkileşim**: Kullanıcılar sesli komutlarla ZEKA ile etkileşime girebilir.
- **Görev Yönetimi**: Takvim entegrasyonu, hatırlatıcılar ve toplantı planlama.
- **E-posta Yönetimi**: E-posta okuma, yazma ve gönderme.
- **Kodlama Yardımı**: Kod analizi, hata düzeltme ve optimizasyon önerileri.
- **Vektör Bellek**: Semantik arama ve ilişkisel bellek yetenekleri.
- **Çoklu Dil Modeli Desteği**: OpenRouter API entegrasyonu ile Claude, Llama, Mistral ve Cohere gibi farklı dil modellerine erişim.
- **MCP Entegrasyonu**: Model Context Protocol desteği ile topluluk tarafından geliştirilen MCP sunucularına bağlanabilme.
- **Güvenlik**: API güvenliği, veri şifreleme ve anonimleştirme.
- **Masaüstü Denetleyicisi**: Dosya gezgini, ekran görüntüsü alma, OCR ile metin tanıma, pencere yönetimi ve sistem bilgisi görüntüleme.

## Kurulum

### Önkoşullar

- Python 3.10 veya üzeri (Python 3.13 desteği eklenmiştir)
- [Poetry](https://python-poetry.org/) (bağımlılık yönetimi için) veya pip
- OpenRouter API anahtarı (opsiyonel, farklı dil modelleri için)
- Tesseract OCR (masaüstü denetleyicisi için, opsiyonel)

#### Python 3.13 Uyumluluğu

Python 3.13 ile uyumlu temel paketler requirements.txt dosyasında belirtilmiştir. Bazı gelişmiş özellikler için ek paketlerin manuel olarak kurulması gerekebilir:

- **Vektör Veritabanı**: chromadb, sentence-transformers, hnswlib, annoy
- **LLM Entegrasyonları**: langchain, langchain-openai, langchain-community
- **Veri İşleme**: numpy, pandas, scipy
- **Ajan Mimarisi**: autogen, crewai
- **Gelişmiş Ses İşleme**: faster-whisper, elevenlabs, librosa
- **Masaüstü Otomasyonu**: pyautogui, pytesseract, pywinauto

### Adımlar

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/kullanici/zeka.git
   cd zeka
   ```

2. Bağımlılıkları yükleyin:

   Poetry ile:
   ```bash
   poetry install
   ```

   veya pip ile:
   ```bash
   pip install -r requirements.txt
   ```

3. Çevre değişkenlerini ayarlayın:
   - `.env.example` dosyasını kopyalayıp `.env` olarak adlandırın.
   - Gerekli API anahtarlarını ve ayarları doldurun:
     ```
     OPENAI_API_KEY=your_openai_api_key
     OPENROUTER_API_KEY=your_openrouter_api_key
     ```

4. Vektör veritabanı dizinini oluşturun:
   ```bash
   mkdir -p data/vector_db
   ```

5. Uygulamayı başlatın:

   Windows için:
   ```bash
   start_zeka.bat
   ```

   Linux/macOS için:
   ```bash
   ./start_zeka.sh
   ```

   veya manuel olarak:
   ```bash
   # Backend'i başlat
   cd src
   python -m api.main

   # Yeni bir terminal penceresinde frontend'i başlat
   cd src/ui/frontend
   npm run dev
   ```

6. Testleri çalıştırın:
   ```bash
   python -m unittest discover tests
   ```

## Kullanım

ZEKA'ya sesli komutlar vererek veya metin girişi yaparak etkileşime geçebilirsiniz. Örnek komutlar:

### Genel Komutlar
- "Merhaba, nasılsın?"
- "Bugün hava nasıl?"
- "Yapay zeka nedir?"

### Dil ve İletişim Tarzı Ayarları
- "Dili İngilizce olarak ayarla."
- "Resmi iletişim tarzını kullan."
- "Samimi bir şekilde konuş."

### Çeviri İşlemleri
- "Bu metni İngilizce'ye çevir: Merhaba dünya."
- "Fransızca'dan Türkçe'ye çevir: Bonjour le monde."

### Bellek ve Semantik Arama
- "Daha önce yapay zeka hakkında ne konuşmuştuk?"
- "Geçmiş konuşmalarımızda Python ile ilgili ne vardı?"

### OpenRouter API Kullanımı
- "Claude modeli ile yanıt ver: Kuantum bilgisayarlar nasıl çalışır?"
- "Llama modeli kullanarak bir hikaye yaz."

### Masaüstü Denetleyicisi Komutları
- "Ekran görüntüsü al ve metni oku."
- "C:\Users\kullanici\Belgeler dizinini listele."
- "Sistem bilgilerini göster."
- "Açık pencereleri listele."
- "Notepad uygulamasını aç."
- "Bu komutu çalıştır: ipconfig"

## Geliştirme Planı

Projenin geliştirme planı [plan.md](plan.md) dosyasında detaylandırılmıştır. Şu ana kadar tamamlanan aşamalar:

- ✅ Asenkron işleme optimizasyonu
- ✅ Hata yönetimi iyileştirmesi
- ✅ Modüler mimari yeniden yapılandırması
- ✅ OpenRouter API entegrasyonu
- ✅ Vektör veritabanı entegrasyonu
- ✅ Masaüstü denetleyicisi entegrasyonu
- ✅ Python 3.13 uyumluluğu
- 🔄 MCP entegrasyonu (kısmen tamamlandı)

## Proje Yapısı

```
zeka/
├── data/                  # Veri dosyaları
│   ├── vector_db/         # Vektör veritabanı dosyaları
│   └── screenshots/       # Ekran görüntüleri
├── logs/                  # Log dosyaları
├── src/                   # Kaynak kodlar
│   ├── agents/            # Ajan modülleri
│   │   ├── conversation_agent.py
│   │   ├── desktop_agent.py
│   │   └── ...
│   ├── core/              # Çekirdek modüller
│   │   ├── agent_base.py
│   │   ├── communication.py
│   │   ├── desktop/       # Masaüstü denetleyicisi modülleri
│   │   │   ├── os_abstraction.py
│   │   │   ├── screen_perception.py
│   │   │   ├── keyboard_control.py
│   │   │   ├── app_control.py
│   │   │   ├── browser_control.py
│   │   │   └── ...
│   │   ├── exceptions.py
│   │   ├── logging_manager.py
│   │   ├── memory_manager.py
│   │   ├── openrouter_client.py
│   │   ├── vector_database.py
│   │   └── ...
│   ├── api/               # API rotaları
│   │   ├── routes/        # API alt rotaları
│   │   │   ├── desktop.py # Masaüstü denetleyicisi API rotaları
│   │   │   └── ...
│   │   └── main.py        # API ana uygulaması
│   ├── services/          # Servis modülleri
│   ├── ui/                # Kullanıcı arayüzü
│   │   ├── frontend/      # Frontend bileşenleri
│   │   │   ├── components/
│   │   │   │   ├── desktop-controller.tsx
│   │   │   │   └── ...
│   │   │   ├── lib/
│   │   │   │   ├── desktop-api.ts
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── main.py            # Ana uygulama
├── tests/                 # Test dosyaları
│   ├── test_conversation_agent.py
│   ├── test_openrouter_client.py
│   ├── test_vector_database.py
│   └── ...
├── .env.example           # Örnek çevre değişkenleri
├── requirements.txt       # Bağımlılıklar
├── README.md              # Bu dosya
├── plan.md                # Geliştirme planı
└── desktopcontrollerplan.md # Masaüstü denetleyicisi planı
```

## Katkıda Bulunma

Katkıda bulunmak için lütfen [CONTRIBUTING.md](CONTRIBUTING.md) dosyasını okuyun. Özellikle şu alanlarda katkılarınızı bekliyoruz:

- MCP entegrasyonunun tamamlanması
- Güvenlik katmanının geliştirilmesi
- Yeni ajanların eklenmesi
- Test kapsamının genişletilmesi
- Dokümantasyonun iyileştirilmesi
- Masaüstü denetleyicisi yeteneklerinin genişletilmesi
- Çoklu işletim sistemi desteğinin iyileştirilmesi

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
