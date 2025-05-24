# Z.E.K.A OpenAI Entegrasyonu

Bu dokümantasyon, Z.E.K.A projesindeki OpenAI API entegrasyonunu açıklar.

## Genel Bakış

Z.E.K.A artık OpenAI API'sini doğrudan kullanarak GPT modellerine erişim sağlar. Bu entegrasyon şunları destekler:

- **Sohbet Tamamlama**: GPT modelleri ile doğal dil işleme
- **Streaming Yanıtlar**: Gerçek zamanlı yanıt akışı
- **Model Yönetimi**: Farklı GPT modelleri arasında geçiş
- **Kullanıcı Tercihleri**: Model tercihlerinin kaydedilmesi

## Desteklenen Modeller

### GPT-4 Serisi
- **gpt-4**: En gelişmiş GPT modeli (8K token)
- **gpt-4-turbo**: Hızlı ve güçlü GPT-4 varyantı (128K token)
- **gpt-4o**: Optimize edilmiş GPT-4 modeli (128K token)
- **gpt-4o-mini**: Hızlı ve ekonomik GPT-4o varyantı (128K token)

### GPT-3.5 Serisi
- **gpt-3.5-turbo**: Hızlı ve ekonomik model (16K token)

## Konfigürasyon

### Çevre Değişkenleri

`.env` dosyasında aşağıdaki değişkenleri ayarlayın:

```env
# OpenAI API Anahtarı
OPENAI_API_KEY="your-openai-api-key-here"

# Varsayılan Model
DEFAULT_MODEL="gpt-4o-mini"

# Model Ayarları
DEFAULT_TEMPERATURE="0.7"
DEFAULT_MAX_TOKENS="1000"
```

### API Anahtarı Alma

1. [OpenAI Platform](https://platform.openai.com/) hesabınıza giriş yapın
2. API Keys bölümüne gidin
3. Yeni bir API anahtarı oluşturun
4. Anahtarı `.env` dosyasına ekleyin

## Kullanım

### OpenAI İstemcisi Başlatma

```python
from src.core.openai_client import OpenAIClient

# Varsayılan ayarlarla başlat
client = OpenAIClient()

# Özel ayarlarla başlat
client = OpenAIClient(
    api_key="your-api-key",
    default_model="gpt-4o",
    timeout=120.0,
    max_retries=3,
    organization="your-org-id",  # Opsiyonel
    project="your-project-id"    # Opsiyonel
)
```

### Metin Üretme

```python
response = await client.generate_text(
    prompt="Yapay zeka nedir?",
    model="gpt-4o",  # Opsiyonel, varsayılan model kullanılabilir
    max_tokens=1000,
    temperature=0.7,
    system_prompt="Türkçe yanıt ver ve örnekler kullan.",
    user_id="user123"  # Opsiyonel
)

print(response["response"])
print(f"Kullanılan model: {response['model']}")
print(f"Token kullanımı: {response['usage']}")
```

### Streaming Yanıtlar

```python
async for chunk in client.generate_stream(
    prompt="Uzun bir hikaye anlat",
    model="gpt-4o-mini",
    temperature=0.8,
    max_tokens=2000
):
    if chunk.get("content"):
        print(chunk["content"], end="", flush=True)
```

### Sohbet Tamamlama

```python
messages = [
    {"role": "system", "content": "Sen yardımcı bir asistansın."},
    {"role": "user", "content": "Merhaba!"},
    {"role": "assistant", "content": "Merhaba! Size nasıl yardımcı olabilirim?"},
    {"role": "user", "content": "Python hakkında bilgi ver."}
]

response = await client.chat_completion(
    messages=messages,
    model="gpt-4o",
    temperature=0.7
)

print(response["response"])
```

### Model Listesi

```python
models = await client.list_available_models()
for model in models:
    print(f"ID: {model['id']}")
    print(f"Ad: {model['name']}")
    print(f"Sağlayıcı: {model['provider']}")
    print(f"Açıklama: {model['description']}")
    print(f"Max Token: {model['max_tokens']}")
    print(f"Streaming: {model['supports_streaming']}")
    print("---")
```

## API Endpoint'leri

### Model Yönetimi

#### Kullanılabilir Modelleri Listele
```http
GET /api/models
```

Yanıt:
```json
{
  "models": [
    {
      "id": "gpt-4o-mini",
      "name": "GPT-4o Mini",
      "provider": "openai"
    }
  ],
  "current_model": "gpt-4o-mini"
}
```

#### Model Değiştir
```http
POST /api/models/set
Content-Type: application/json

{
  "model": "gpt-4o"
}
```

### Sohbet

#### Mesaj Gönder
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Merhaba!",
  "user_id": "default_user",
  "language": "tr",
  "style": "friendly",
  "model": "gpt-4o-mini"
}
```

## Hata Yönetimi

### Yaygın Hatalar

1. **API Anahtarı Hatası**
   ```
   OpenAI API anahtarı bulunamadı. OPENAI_API_KEY çevre değişkenini ayarlayın.
   ```
   Çözüm: `.env` dosyasında `OPENAI_API_KEY` değişkenini ayarlayın.

2. **Model Bulunamadı**
   ```
   Desteklenmeyen model: invalid-model. Varsayılan model kullanılacak.
   ```
   Çözüm: Desteklenen model listesinden bir model seçin.

3. **Rate Limit**
   ```
   Rate limit exceeded. Please try again later.
   ```
   Çözüm: İstek sıklığını azaltın veya daha yüksek limitli bir plan kullanın.

### Hata Yakalama

```python
from src.core.openai_client import OpenAIAPIError

try:
    response = await client.generate_text("Test mesajı")
except OpenAIAPIError as e:
    print(f"OpenAI API hatası: {e}")
except Exception as e:
    print(f"Genel hata: {e}")
```

## Performans İpuçları

1. **Model Seçimi**: Basit görevler için `gpt-3.5-turbo` veya `gpt-4o-mini` kullanın
2. **Token Limiti**: Gereksiz uzun yanıtları önlemek için `max_tokens` ayarlayın
3. **Sıcaklık**: Tutarlı yanıtlar için düşük (0.1-0.3), yaratıcı yanıtlar için yüksek (0.7-1.0) değer kullanın
4. **Streaming**: Uzun yanıtlar için streaming kullanarak kullanıcı deneyimini iyileştirin

## Güvenlik

1. **API Anahtarı**: API anahtarınızı asla kod içinde sabit olarak yazmayın
2. **Çevre Değişkenleri**: `.env` dosyasını versiyon kontrolüne eklemeyin
3. **Rate Limiting**: Aşırı kullanımı önlemek için rate limiting uygulayın
4. **Kullanıcı Girişi**: Kullanıcı girdilerini doğrulayın ve temizleyin

## Sorun Giderme

### Debug Modu

Detaylı log çıktısı için log seviyesini DEBUG olarak ayarlayın:

```python
import logging
logging.getLogger("openai_client").setLevel(logging.DEBUG)
```

### Bağlantı Testi

```python
try:
    models = await client.list_available_models()
    print("OpenAI bağlantısı başarılı!")
    print(f"Kullanılabilir model sayısı: {len(models)}")
except Exception as e:
    print(f"Bağlantı hatası: {e}")
```
