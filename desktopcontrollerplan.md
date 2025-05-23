# Z.E.K.A. Masaüstü Denetleyicisi Geliştirme Planı

## 1. Genel Bakış

Bu belge, Z.E.K.A. projesini JARVIS seviyesine taşıyacak masaüstü denetleyicisi (Desktop Controller) geliştirme planını içermektedir. Mevcut `SystemController` sınıfını temel alarak, kullanıcının masaüstü ortamıyla doğal dil, ses ve niyet üzerinden etkileşim kurmasını sağlayan, uygulamaları derinlemesine kontrol edebilen, iş akışlarını otomatikleştiren, bağlamsal olarak farkında ve proaktif bir masaüstü denetim sistemi oluşturmayı hedefliyoruz.

## 2. Mevcut Durum Analizi

### 2.1 Mevcut Bileşenler

- **SystemController**: Temel sistem komutları çalıştırma ve uygulama açma yetenekleri
- **Ses Sistemi**: Wake word detection, sürekli dinleme modu, Faster-Whisper entegrasyonu
- **Proaktif Öneriler**: Kullanıcı davranış izleme ve basit öneriler
- **IoT Entegrasyonu**: HomeAssistant ve MQTT entegrasyonu

### 2.2 Eksik Bileşenler

- **Gelişmiş Dosya/Klasör İşlemleri**: Dosya oluşturma, silme, taşıma, arama ✅
- **Pencere Yönetimi**: Aktif pencereyi bulma, pencere kontrolü ✅
- **Uygulama İçi Etkileşim**: Uygulamalarda buton tıklama, metin girme ✅
- **Ekran Algılama**: Ekran görüntüsü alma, OCR ile metin tanıma ✅
- **Bağlam Yönetimi**: Masaüstü etkileşimlerini belleğe kaydetme
- **İş Akışı Motoru**: Çok adımlı görevleri otomatikleştirme
- **Güvenlik Katmanı**: Yetkilendirme ve izin yönetimi ✅

## 3. Mimari Tasarım

```
+-----------------------------------+
|      Z.E.K.A. Çekirdeği (LLM)     |  <-- Doğal Dil Anlama, Karar Verme
+-----------------------------------+
             ^          |
             | (Komutlar)| (Geri Bildirim)
             v          |
+-----------------------------------+
|  Desktop Interaction Layer (DIL)  |  <-- Ana Geliştirme Odağı
+-----------------------------------+
    |         |         |         |
    v         v         v         v
+---------+ +---------+ +---------+ +-----------------+
| OS      | | App     | | Screen  | | Workflow        |
| Abstrct.| | Control | | Percpt. | | Engine          |
+---------+ +---------+ +---------+ +-----------------+
             ^          ^         ^
             |          |         |
+-----------------------------------+
|      İşletim Sistemi (OS)         |
+-----------------------------------+
|         Uygulamalar               |
+-----------------------------------+
```

### 3.1 Bileşenler

1. **OS Abstraction Layer (OSAL)**: İşletim sistemi soyutlama katmanı
2. **Application Control Module (ACM)**: Uygulama kontrol modülü
3. **Screen Perception Module (SPM)**: Ekran algılama modülü
4. **Context Manager**: Bağlam yöneticisi
5. **Workflow Engine**: İş akışı motoru
6. **Security & Permissions Manager**: Güvenlik ve izin yöneticisi

## 4. Geliştirme Aşamaları

### Faz 1: Temel Masaüstü Kontrolü ve Farkındalık (1-2 Ay)

#### 1.1 OSAL Geliştirmesi ✅

```python
# src/core/desktop/os_abstraction.py
class OSAbstractionLayer:
    def __init__(self):
        self.os_type = platform.system()
        self.system_controller = SystemController()

    async def execute_command(self, command):
        return await self.system_controller.execute_command(command)

    async def open_application(self, app_name):
        return await self.system_controller.open_application(app_name)

    async def create_directory(self, path):
        # Dizin oluşturma işlemi
        try:
            os.makedirs(path, exist_ok=True)
            return True, f"Dizin oluşturuldu: {path}"
        except Exception as e:
            return False, f"Dizin oluşturma hatası: {str(e)}"

    async def list_directory(self, path):
        # Dizin içeriğini listeleme
        try:
            items = os.listdir(path)
            result = []
            for item in items:
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                result.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "path": item_path
                })
            return True, result
        except Exception as e:
            return False, f"Dizin listeleme hatası: {str(e)}"

    # Diğer dosya/klasör işlemleri...

    async def get_active_window(self):
        # İşletim sistemine göre aktif pencere bilgisini al
        if self.os_type == "Windows":
            # pywin32 kullanarak aktif pencere bilgisini al
            pass
        elif self.os_type == "Darwin":  # macOS
            # osascript kullanarak aktif pencere bilgisini al
            pass
        else:  # Linux
            # xlib kullanarak aktif pencere bilgisini al
            pass
```

#### 1.2 Basit Ekran Algılama ✅

```python
# src/core/desktop/screen_perception.py
class ScreenPerception:
    def __init__(self):
        # OCR için Tesseract yolunu ayarla
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows için

    async def capture_screen(self, region=None):
        # Ekran görüntüsü al
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            return True, screenshot
        except Exception as e:
            return False, f"Ekran görüntüsü alma hatası: {str(e)}"

    async def extract_text(self, image):
        # Görüntüden metin çıkar
        try:
            text = pytesseract.image_to_string(image, lang='tur+eng')
            return True, text
        except Exception as e:
            return False, f"Metin çıkarma hatası: {str(e)}"
```

#### 1.3 LLM Entegrasyonu ✅

```python
# src/agents/desktop_agent.py
class DesktopAgent(AgentBase):
    def __init__(self, agent_id, name, description):
        super().__init__(agent_id, name, description)
        self.osal = OSAbstractionLayer()
        self.screen_perception = ScreenPerception()

    async def process_request(self, user_request, intent, entities):
        # Masaüstü ile ilgili istekleri işle
        if intent == "open_application":
            app_name = entities.get("app_name")
            if app_name:
                result = await self.osal.open_application(app_name)
                return f"{app_name} uygulaması açıldı."

        elif intent == "read_screen":
            success, screenshot = await self.screen_perception.capture_screen()
            if success:
                success, text = await self.screen_perception.extract_text(screenshot)
                if success:
                    return f"Ekranda şunlar yazıyor: {text}"

        # Diğer masaüstü istekleri...
```

### Faz 2: Uygulama İçi Etkileşim (2-3 Ay)

#### 2.1 Klavye Kısayolu Simülasyonu ✅

```python
# src/core/desktop/keyboard_control.py
class KeyboardControl:
    def __init__(self):
        pass

    async def send_shortcut(self, shortcut):
        # Klavye kısayolu gönder
        try:
            pyautogui.hotkey(*shortcut.split('+'))
            return True, f"Kısayol gönderildi: {shortcut}"
        except Exception as e:
            return False, f"Kısayol gönderme hatası: {str(e)}"
```

#### 2.2 Hedeflenmiş Uygulama Kontrolü ✅

```python
# src/core/desktop/app_control.py
class ApplicationControl:
    def __init__(self):
        self.os_type = platform.system()

    async def find_window(self, app_name):
        # Uygulama penceresini bul
        if self.os_type == "Windows":
            # pywinauto kullanarak pencereyi bul
            pass
        # Diğer işletim sistemleri için...

    async def click_button(self, window, button_text):
        # Penceredeki butona tıkla
        if self.os_type == "Windows":
            # pywinauto kullanarak butona tıkla
            pass
        # Diğer işletim sistemleri için...

    async def enter_text(self, window, text_field, text):
        # Metin kutusuna yazı yaz
        if self.os_type == "Windows":
            # pywinauto kullanarak metin gir
            pass
        # Diğer işletim sistemleri için...
```

#### 2.3 Tarayıcı Otomasyonu ✅

```python
# src/core/desktop/browser_control.py
class BrowserControl:
    def __init__(self):
        pass

    async def open_url(self, url, browser="default"):
        # URL'yi tarayıcıda aç
        try:
            if browser == "default":
                webbrowser.open(url)
            else:
                # Belirli bir tarayıcıyı aç
                pass
            return True, f"URL açıldı: {url}"
        except Exception as e:
            return False, f"URL açma hatası: {str(e)}"

    async def search_web(self, query, search_engine="google"):
        # Web'de arama yap
        try:
            if search_engine == "google":
                url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            elif search_engine == "bing":
                url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            # Diğer arama motorları...

            return await self.open_url(url)
        except Exception as e:
            return False, f"Web arama hatası: {str(e)}"
```

### Faz 3 ve 4 için Planlanan Modüller

- **Context Manager**: Masaüstü etkileşimlerini belleğe kaydetme
- **Workflow Engine**: Çok adımlı görevleri otomatikleştirme
- **Security Manager**: Güvenlik ve izin yönetimi
- **Gelişmiş SPM**: Erişilebilirlik API'leri ile UI elemanlarını tanıma
- **Proaktif Öneriler**: Kullanıcı davranışlarına göre öneriler sunma

## 5. Teknoloji Yığını

### 5.1 Temel Kütüphaneler

- **Sistem İşlemleri**: `os`, `subprocess`, `asyncio`, `psutil`
- **Dosya İşlemleri**: `shutil`, `aiofiles`, `pathlib`
- **UI Otomasyonu**: `pyautogui`, `pywinauto` (Windows), `pyobjc` (macOS), `python-xlib` (Linux)
- **Ekran Algılama**: `Pillow`, `pytesseract`, `EasyOCR`
- **Tarayıcı Otomasyonu**: `selenium`, `playwright`

### 5.2 Bağımlılıklar

```
# Ek bağımlılıklar
pyautogui==0.9.54
pytesseract==0.3.10
psutil==5.9.5
pywinauto==0.6.8  # Windows için
pyobjc==9.2  # macOS için
python-xlib==0.33  # Linux için
selenium==4.10.0
playwright==1.36.0
easyocr==1.7.0
```

## 6. Uygulama Planı

### 6.1 Faz 1 (1-2 Ay) ✅

1. **Hafta 1-2**: OSAL temel yapısı ve dosya/klasör işlemleri ✅
2. **Hafta 3-4**: Basit ekran algılama ve OCR entegrasyonu ✅
3. **Hafta 5-6**: LLM entegrasyonu ve temel masaüstü ajanı ✅
4. **Hafta 7-8**: Test ve iyileştirmeler ✅

### 6.2 Faz 2 (2-3 Ay) ✅

1. **Hafta 1-2**: Klavye kontrolü ve kısayol simülasyonu ✅
2. **Hafta 3-5**: Uygulama kontrolü (Windows öncelikli) ✅
3. **Hafta 6-8**: Tarayıcı otomasyonu ✅
4. **Hafta 9-10**: LLM entegrasyonu ve test ✅

### 6.3 Faz 3 (3-4 Ay)

1. **Hafta 1-3**: Bağlam yöneticisi
2. **Hafta 4-6**: Basit iş akışı motoru
3. **Hafta 7-10**: LLM entegrasyonu ve test

### 6.4 Faz 4 (4-6 Ay)

1. **Hafta 1-4**: Gelişmiş ekran algılama
2. **Hafta 5-8**: Gelişmiş uygulama kontrolü
3. **Hafta 9-12**: Proaktif öneriler
4. **Hafta 13-16**: Karmaşık iş akışları
5. **Hafta 17-20**: Güvenlik katmanı ve test

## 7. Başarı Kriterleri

- Kullanıcı doğal dil komutlarıyla masaüstü görevlerini gerçekleştirebilmeli ✅
- Sistem, kullanıcının niyetini anlayabilmeli ✅
- Proaktif öneriler sunabilmeli
- Çok adımlı görevleri otomatikleştirebilmeli
- Güvenli ve güvenilir bir şekilde çalışmalı ✅

## 7.1 Tamamlanan Özellikler

- **Dosya Gezgini**: Dosya ve klasör listeleme, oluşturma, silme işlemleri ✅
- **Ekran Görüntüsü**: Ekran görüntüsü alma ve OCR ile metin tanıma ✅
- **Pencere Yönetimi**: Açık pencereleri listeleme, pencere etkinleştirme, işlem sonlandırma ✅
- **Sistem Bilgileri**: CPU, bellek ve disk kullanımı gibi sistem bilgilerini görüntüleme ✅
- **Terminal Entegrasyonu**: Sistem komutlarını çalıştırma ve sonuçları görüntüleme ✅
- **Kullanıcı Arayüzü**: Web tabanlı kullanıcı arayüzü ile masaüstü denetleyicisi yeteneklerine erişim ✅
- **Güvenlik Kontrolleri**: Dosya yolu güvenlik kontrolleri, tehlikeli sistem dizinlerine erişim engelleme ✅

## 8. Riskler ve Azaltma Stratejileri

- **Platform Bağımlılığı**: OSAL katmanı ile soyutlama
- **UI Değişiklikleri**: Erişilebilirlik API'leri kullanma
- **Güvenlik Riskleri**: Güvenlik katmanı ve kullanıcı onayı
- **Performans Sorunları**: Asenkron işlemler ve optimizasyon
- **Hata Yönetimi**: Sağlam hata yakalama ve raporlama

## 9. Sonuç

Bu plan, Z.E.K.A. projesini JARVIS seviyesine taşıyacak masaüstü denetleyicisinin geliştirilmesi için kapsamlı bir yol haritası sunmaktadır. Aşamalı yaklaşım, her adımda sistemi daha yetenekli hale getirirken, modüler mimari gelecekteki genişletmelere olanak tanıyacaktır.

## 10. İlerleme Durumu (Güncel)

### 10.1 Tamamlanan Fazlar
- **Faz 1**: Temel Masaüstü Kontrolü ve Farkındalık ✅
- **Faz 2**: Uygulama İçi Etkileşim ✅

### 10.2 Sonraki Adımlar
- **Faz 3**: Bağlam Yönetimi ve İş Akışı Motoru
- **Faz 4**: Gelişmiş Algılama ve Proaktif Öneriler

### 10.3 Gelecek Geliştirmeler
1. **Gelişmiş Dosya İşlemleri**: Dosya taşıma, kopyalama ve yeniden adlandırma işlevleri
2. **Dosya İçeriği Görüntüleme**: Metin dosyalarının içeriğini görüntüleme ve düzenleme
3. **Gelişmiş Pencere Yönetimi**: Pencere boyutlandırma, taşıma ve düzenleme işlevleri
4. **Güvenlik İyileştirmeleri**: Daha kapsamlı güvenlik kontrolleri ve kullanıcı izinleri
5. **Performans Optimizasyonu**: Büyük dizinler için sayfalama ve önbelleğe alma
