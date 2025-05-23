# ZEKA - Kurulum Talimatları

Bu belge, ZEKA (Zenginleştirilmiş Etkileşimli Kişisel Asistan) projesinin kurulum adımlarını içermektedir.

## Gereksinimler

- Python 3.9 veya daha yeni bir sürüm
- pip (Python paket yöneticisi)
- Git (isteğe bağlı, kaynak kodunu klonlamak için)

## Kurulum Adımları

### 1. Kaynak Kodunu Edinin

Projeyi doğrudan indirin veya Git kullanarak klonlayın:

```bash
git clone <repo-url>
cd zeka-assistant
```

### 2. Sanal Ortam Oluşturun (İsteğe Bağlı ama Önerilir)

Python sanal ortamı oluşturmak, projenin bağımlılıklarını izole etmenize yardımcı olur:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

Gerekli tüm kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
```

### 4. Yapılandırma

Projenin kök dizininde `.env` dosyası oluşturun ve gerekli yapılandırma değerlerini ekleyin:

```
# .env dosyası örneği
USER_ID=default_user
STORAGE_PATH=./data

# API Anahtarları (ilerleyen aşamalarda kullanılacak)
# OPENAI_API_KEY=your_openai_api_key
# ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 5. Veri Dizinlerini Oluşturun

Uygulama ilk çalıştırıldığında otomatik olarak oluşturulacak olsa da, manuel olarak da oluşturabilirsiniz:

```bash
mkdir -p data/memory data/profiles data/models logs
```

## Çalıştırma

Uygulamayı başlatmak için:

```bash
python src/main.py
```

## Geliştirme

### Yeni Ajan Ekleme

Yeni bir ajan eklemek için:

1. `src/agents/` dizininde yeni bir Python dosyası oluşturun
2. `Agent` sınıfından türetilen bir sınıf tanımlayın
3. `process_task` metodunu uygulayın
4. `src/main.py` dosyasındaki `_register_agents` metodunda ajanınızı kaydedin

### Yeni MCP (Model, Yetenek, Eklenti) Ekleme

Yeni bir MCP eklemek için:

1. İlgili modeli/yeteneği/eklentiyi uygulayın
2. `MCPManager` sınıfını kullanarak sisteme kaydedin

## Sorun Giderme

- **Bağımlılık Hataları**: Tüm bağımlılıkların doğru sürümlerle yüklendiğinden emin olun
- **Dizin Hataları**: Gerekli veri dizinlerinin mevcut olduğundan emin olun
- **API Hataları**: API anahtarlarının doğru şekilde yapılandırıldığından emin olun

## İleri Aşamalar

Projenin ilerleyen aşamalarında eklenecek özellikler:

- Gelişmiş LLM entegrasyonu
- Vektör veritabanı implementasyonu
- Sesli etkileşim yetenekleri
- Web arayüzü
- Daha fazla uzmanlaşmış ajan