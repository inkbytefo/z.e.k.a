# OpenRouter API Streaming Entegrasyonu

Bu belge, Z.E.K.A projesinde OpenRouter API ile streaming işlevselliğinin nasıl kullanılacağını açıklar.

## Genel Bakış

OpenRouter API, çeşitli dil modellerine (Claude, GPT-4, Llama, Mistral vb.) tek bir API üzerinden erişim sağlar. Bu entegrasyon, OpenAI SDK kullanarak OpenRouter API'ye erişim sağlar ve streaming desteği ile gerçek zamanlı yanıt akışı sunar.

## Yapılan Değişiklikler

1. `openrouter_client.py` dosyası, OpenAI SDK'nın en son sürümüne uygun olarak güncellendi.
2. Streaming işlevselliği, OpenAI SDK'nın AsyncOpenAI sınıfı kullanılarak yeniden yazıldı.
3. Kullanıcıların kendi API endpoint URL'lerini ekleyebilecekleri bir yapı oluşturuldu.
4. Streaming yanıtların düzgün çalışması sağlandı.

## Kullanım

### OpenRouterClient Başlatma

```python
from src.core.openrouter_client import OpenRouterClient

# Varsayılan ayarlarla başlat
client = OpenRouterClient()

# Özel ayarlarla başlat
client = OpenRouterClient(
    api_key="your-api-key",
    default_model="anthropic/claude-3-opus",
    site_url="https://your-site.com",
    site_name="Your Site Name",
    timeout=120.0,
    max_retries=5,
    retry_delay=2.0,
    api_base="https://openrouter.ai/api/v1"  # Özel API endpoint URL'si
)
```

### Metin Üretme

```python
response = await client.generate_text(
    prompt="Yapay zeka nedir?",
    model="anthropic/claude-3-opus",  # Opsiyonel, varsayılan model kullanılabilir
    max_tokens=1000,
    temperature=0.7,
    system_prompt="Türkçe yanıt ver ve örnekler kullan."
)

print(response["content"])  # Üretilen metin
```

### Streaming Metin Üretme

```python
async for chunk in client.generate_stream(
    prompt="Yapay zeka teknolojisinin geleceği nasıl olacak?",
    model="anthropic/claude-3-opus",  # Opsiyonel, varsayılan model kullanılabilir
    max_tokens=300,
    temperature=0.7,
    system_prompt="Türkçe yanıt ver ve kısa tut."
):
    if "content" in chunk and chunk["content"]:
        print(chunk["content"], end="", flush=True)  # Parçaları gerçek zamanlı göster
    
    if "is_last_chunk" in chunk and chunk["is_last_chunk"]:
        print("\nStreaming tamamlandı.")
        print(f"Toplam karakter: {len(chunk['complete_text'])}")
        print(f"Yanıt süresi: {chunk['response_time']:.2f} saniye")
```

### Araç Çağrıları (Function Calling)

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Belirli bir konum için hava durumu bilgisi alır",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Şehir adı, örn. 'İstanbul'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Sıcaklık birimi"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = await client.execute_tool_call(
    prompt="İstanbul'da hava durumu nasıl?",
    tools=tools,
    model="anthropic/claude-3-opus",
    max_tokens=1000,
    temperature=0.7,
    system_prompt="Sen bir hava durumu asistanısın."
)

if response["tool_calls"]:
    for tool_call in response["tool_calls"]:
        print(f"Araç: {tool_call['function']['name']}")
        print(f"Argümanlar: {tool_call['function']['arguments']}")
```

## Hata Ayıklama

Streaming işlevselliğinde bir sorun yaşarsanız, aşağıdaki adımları izleyin:

1. OpenAI SDK'nın en son sürümünün yüklü olduğundan emin olun: `pip install openai --upgrade`
2. API anahtarınızın doğru olduğunu kontrol edin.
3. Bağlantı sorunları için ağ ayarlarınızı kontrol edin.
4. Hata mesajlarını inceleyerek sorunun kaynağını belirlemeye çalışın.

## Test

OpenRouter API istemcisini test etmek için `test_openrouter_client.py` betiğini kullanabilirsiniz:

```bash
python test_openrouter_client.py
```

Bu betik, hem normal metin üretme hem de streaming işlevselliğini test eder.

## Notlar

- OpenRouter API, farklı modellere erişim sağlar, ancak her modelin kendi özellikleri ve sınırlamaları vardır.
- Streaming işlevselliği, tüm modeller tarafından desteklenmeyebilir.
- API kullanımı, OpenRouter hesabınızdaki kredi miktarına göre sınırlıdır.
