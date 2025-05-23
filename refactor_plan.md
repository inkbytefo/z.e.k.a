# Z.E.K.A → JARVIS Dönüşüm Planı

## 1. Genel Bakış

Z.E.K.A (Zenginleştirilmiş Etkileşimli Kişisel Asistan) projesini, Tony Stark'ın JARVIS'i seviyesine yükseltmek için kapsamlı bir dönüşüm planı. Bu plan, mevcut Z.E.K.A altyapısını temel alarak, JARVIS'in temel özelliklerini aşamalı olarak entegre etmeyi amaçlamaktadır.

### JARVIS'in Temel Karakteristikleri

- **Proaktif Zeka**: Kullanıcının ihtiyaçlarını önceden tahmin etme
- **Omnipresent Erişim**: Her yerden, her cihazdan erişilebilirlik
- **Çoklu Görev Yönetimi**: Aynı anda onlarca görevi koordine etme
- **Duygusal Zeka**: Kullanıcının ruh halini anlayıp ona göre davranma
- **Teknik Maester**: Karmaşık teknik işlemleri otomatikleştirme
- **Güvenlik Odaklı**: Maksimum güvenlik ve gizlilik

### Mevcut Z.E.K.A Altyapısı Değerlendirmesi

**Güçlü Yönler:**
- Modüler ajan mimarisi
- OpenRouter entegrasyonu ile çoklu model desteği
- ChromaDB tabanlı vektör veritabanı
- Kısmen tamamlanmış MCP entegrasyonu
- Modern ve etkileşimli web arayüzü

**Geliştirilmesi Gereken Alanlar:**
- Ses işleme sistemi
- Proaktif zeka yetenekleri
- Sistem entegrasyonları
- Güvenlik katmanı
- Otonom problem çözme

## 2. Revize Edilmiş Stratejik Yaklaşım

Orijinal dört fazlı planın uygulanabilirlik değerlendirmesi:
- Faz 1: %70 uygulanabilir
- Faz 2: %60 uygulanabilir
- Faz 3: %50 uygulanabilir
- Faz 4: %40 uygulanabilir

Bu değerlendirme ışığında, daha pragmatik bir yaklaşım benimsiyoruz:

### Yeni Stratejik Yaklaşım

**Eski Plan**: Her fazı sıralı olarak tamamla
**Yeni Plan**: Core JARVIS features'ları önce, advanced features'lar sonra

```
Phase 1A: Voice + Basic Control (70% feasible)
Phase 1B: Proactive Intelligence (60% feasible)
Phase 1C: System Integration (50% feasible)
Phase 1D: Advanced AI Features (40% feasible)
```

## 3. Immediate MVP (0-2 Ay)

### 3.1 Ses Sistemi Upgrade'i ✅

#### Wake Word Detection Entegrasyonu ✅

```python
# TAMAMLANDI: src/core/wake_word_detector.py modülü oluşturuldu
# Picovoice Porcupine entegrasyonu yapıldı
# "Hey ZEKA" wake word desteği eklendi

from pvrecorder import PvRecorder
from porcupine import Porcupine

class WakeWordDetector:
    def __init__(self, config):
        self.access_key = config.get("porcupine_access_key")
        self.keywords = config.get("wake_words", ["hey zeka"])
        self.sensitivities = config.get("sensitivities", [0.7])
        # ...

    async def initialize(self):
        # Porcupine nesnesini oluştur
        self.porcupine = Porcupine(
            access_key=self.access_key,
            keywords=self.keywords,
            sensitivities=self.sensitivities
        )
        # ...
```

#### Sürekli Dinleme Modu ✅

```python
# TAMAMLANDI: src/core/voice_processor.py modülü güncellendi
# Sürekli dinleme modu eklendi
# WebRTC ve PyAudio entegrasyonu yapıldı

class VoiceProcessor:
    # ...

    async def start_listening(self, mode, callback):
        # Dinleme modunu başlat
        self.listening_mode = mode
        self.speech_callback = callback

        # Wake word detector başlat
        if mode == ListeningMode.WAKE_WORD:
            await self.wake_word_detector.initialize()
            await self.wake_word_detector.start()

        # Sürekli dinleme görevi başlat
        if mode == ListeningMode.CONTINUOUS:
            self.listening_task = asyncio.create_task(self._continuous_listening_loop())

        # ...

    async def _continuous_listening_loop(self):
        # Sürekli dinleme döngüsü
        # Konuşma algılama ve işleme
        # ...
```

#### Faster-Whisper Optimizasyonu ✅

```python
# TAMAMLANDI: src/core/optimized_whisper.py modülü oluşturuldu
# Daha hızlı ve verimli ses tanıma için optimizasyonlar eklendi
# Asenkron işleme ve önbellekleme yetenekleri eklendi

from faster_whisper import WhisperModel

class OptimizedWhisperTranscriber:
    def __init__(self, config):
        # Model ayarları
        self.model_size = config.get("whisper_model_size", "small")
        self.device = config.get("whisper_device", "cpu")
        self.compute_type = config.get("whisper_compute_type", "float16")

        # Modeli yükle
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )

    async def transcribe(self, audio_data, language=None):
        # Asenkron transcribe işlemi
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: self.model.transcribe(
                audio_data,
                language=language,
                beam_size=self.beam_size,
                vad_filter=self.vad_filter
            )
        )

        # Segmentleri birleştir
        text = " ".join([segment.text for segment in segments])
        return text
```

#### Gerçek Zamanlı Ses Sentezi ✅

```python
# TAMAMLANDI: src/core/voice_processor.py modülü güncellendi
# ElevenLabs entegrasyonu optimize edildi
# Gerçek zamanlı ses sentezi için WebSocket desteği eklendi

async def _stream_audio(self, text, voice_id, chunk_size):
    """Ses verisini stream modunda üretir."""
    try:
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=self.voice_settings
            ),
            model=self.config.get("tts_model", "eleven_multilingual_v1"),
            stream=True
        )

        buffer = b""
        for chunk in audio:
            buffer += chunk
            while len(buffer) >= chunk_size:
                yield buffer[:chunk_size]
                buffer = buffer[chunk_size:]
                await asyncio.sleep(0)  # Diğer asenkron işlemlere fırsat ver

        if buffer:
            yield buffer

    except Exception as e:
        raise RuntimeError(f"Ses stream hatası: {str(e)}")
```

#### WebRTC Entegrasyonu (Web Arayüzü İçin) ✅

```javascript
// TAMAMLANDI: WebSocket API endpoint'i eklendi
// Gerçek zamanlı ses iletişimi için API eklendi

// WebSocket bağlantısı örneği
const socket = new WebSocket('ws://localhost:8000/api/voice/ws');

socket.onopen = () => {
  console.log('WebSocket bağlantısı açıldı');
};

socket.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'command' && message.content === 'play_audio') {
    // Ses verisini çal
    const audio = new Audio('data:audio/wav;base64,' + message.metadata.audio_data);
    audio.play();
  }
};

// Dinleme modunu başlat
socket.send(JSON.stringify({
  type: 'command',
  content: 'start_listening',
  mode: 'continuous'  // veya 'wake_word'
}));
```
```

### 3.2 Proaktif Öneriler ✅

#### Kullanıcı Davranış Veri Toplama Sistemi ✅

```python
# TAMAMLANDI: src/core/behavior_tracker.py modülü oluşturuldu
# Kullanıcı etkileşimlerini kaydetme ve izleme sistemi eklendi

class UserBehaviorTracker:
    def __init__(self, user_id, vector_db):
        self.user_id = user_id
        self.vector_db = vector_db
        self.collection_name = f"user_behavior_{user_id}"
        self.logger = get_logger("behavior_tracker")

        # Disk önbelleği için dizin
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "behavior_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)

    async def initialize(self):
        # Kullanıcı davranış koleksiyonunu oluştur
        await self.vector_db.create_collection(self.collection_name)

        # Disk önbelleğini yükle
        await self._load_cache_from_disk()

    async def track_interaction(self, interaction_type, content, metadata=None):
        # Etkileşimi kaydet
        current_time = datetime.now()
        interaction_metadata = metadata or {}
        interaction_metadata.update({
            "user_id": self.user_id,
            "timestamp": current_time.isoformat(),
            "interaction_type": interaction_type,
            "day_of_week": current_time.strftime("%A"),
            "hour_of_day": current_time.hour,
            "date": current_time.strftime("%Y-%m-%d")
        })

        # Önbelleğe ekle
        async with self.lock:
            self._cache.append({
                "content": content,
                "metadata": interaction_metadata
            })
```

#### Basit Tahmin Algoritmaları ✅

```python
# TAMAMLANDI: src/core/proactive_assistant.py modülü oluşturuldu
# Zamana, bağlama ve davranış örüntülerine dayalı öneriler eklendi

class ProactiveAssistant:
    def __init__(self, user_id, vector_db, user_profile=None, behavior_tracker=None):
        self.user_id = user_id
        self.vector_db = vector_db
        self.user_profile = user_profile
        self.behavior_tracker = behavior_tracker or UserBehaviorTracker(user_id, vector_db)
        self.collection_name = f"user_behavior_{user_id}"
        self.logger = get_logger("proactive_assistant")

    async def get_suggestions_by_time(self, top_n=3):
        # Günün bu saatinde genellikle ne yapıldığını bul
        current_time = datetime.now()
        current_hour = current_time.hour
        current_day = current_time.strftime("%A")

        # Filtreleme koşulları
        where = {
            "user_id": self.user_id,
            "hour_of_day": {"$gte": current_hour - 1, "$lte": current_hour + 1}
        }

        # Haftanın günü filtresi
        if day_filter:
            where["day_of_week"] = current_day

        # Vektör veritabanından sorgula
        results = await self.vector_db.search(
            collection_name=self.collection_name,
            query="",  # Boş sorgu, sadece filtreleme yapılacak
            n_results=top_n * 2,  # Daha fazla sonuç al, sonra filtreleme yap
            where=where
        )

        return results

    async def suggest_next_action(self, context=None):
        # Kullanıcının bir sonraki olası eylemini öner
        suggestions = []

        # Zamana dayalı öneriler
        time_suggestions = await self.get_suggestions_by_time()
        suggestions.extend(time_suggestions)

        # Bağlama dayalı öneriler (eğer bağlam varsa)
        if context:
            context_suggestions = await self.get_suggestions_by_context(context=context)
            suggestions.extend(context_suggestions)

        # Davranış örüntüsüne dayalı öneriler
        pattern_suggestions = await self.get_suggestions_by_pattern()
        suggestions.extend(pattern_suggestions)

        # En iyi öneriyi seç (güven skoruna göre)
        best_suggestion = max(suggestions, key=lambda x: x["confidence"])

        return best_suggestion
```

#### API Entegrasyonu ✅

```python
# TAMAMLANDI: src/api/proactive_routes.py modülü oluşturuldu
# Proaktif öneriler için API endpoint'leri eklendi

@router.post("/next-action", response_model=NextActionResponse)
async def suggest_next_action(request: NextActionRequest):
    """Kullanıcının bir sonraki olası eylemini önerir."""
    try:
        # Proaktif asistanı al
        assistant = await get_proactive_assistant(request.user_id)

        # Bir sonraki eylemi öner
        suggestion = await assistant.suggest_next_action(context=request.context)

        if suggestion:
            return {
                "success": True,
                "suggestion": suggestion,
                "message": "Bir sonraki eylem önerisi bulundu"
            }
        else:
            return {
                "success": False,
                "suggestion": None,
                "message": "Bir sonraki eylem önerisi bulunamadı"
            }
    except Exception as e:
        logging.error(f"Bir sonraki eylem önerilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bir sonraki eylem önerilemedi: {str(e)}"
        )
```

### 3.3 Temel IoT Entegrasyonu ✅

#### HomeAssistant Bridge ✅

```python
# TAMAMLANDI: src/core/iot/home_assistant.py modülü oluşturuldu
# Home Assistant API entegrasyonu eklendi

class HomeAssistantBridge:
    def __init__(self, host, token, port=8123, use_ssl=False):
        protocol = "https" if use_ssl else "http"
        self.base_url = f"{protocol}://{host}:{port}/api"
        self.websocket_url = f"{'wss' if use_ssl else 'ws'}://{host}:{port}/api/websocket"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.logger = get_logger("home_assistant")

    async def get_states(self, use_cache=True):
        # Tüm cihaz durumlarını getirir
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/states",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")

                    states = await response.json()
                    return states
        except Exception as e:
            self.logger.error(f"Cihaz durumları alınamadı: {str(e)}")
            raise

    async def call_service(self, domain, service, entity_id=None, data=None):
        # Bir servisi çağırır (ışık açma, termostat ayarlama vb.)
        try:
            payload = data or {}
            if entity_id:
                payload["entity_id"] = entity_id

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/services/{domain}/{service}",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")

                    result = await response.json()
                    return result
        except Exception as e:
            self.logger.error(f"Servis çağrılamadı: {str(e)}")
            raise
```

#### MQTT Entegrasyonu ✅

```python
# TAMAMLANDI: src/core/iot/mqtt_client.py modülü oluşturuldu
# MQTT protokolü entegrasyonu eklendi

class MQTTClient:
    def __init__(self, broker_host, broker_port=1883, client_id=None, username=None, password=None, use_ssl=False):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"zeka_mqtt_{os.getpid()}_{datetime.now().timestamp():.0f}"
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

        self.logger = get_logger("mqtt_client")

        # MQTT istemcisi
        self.client = mqtt.Client(client_id=self.client_id)

        # Kimlik bilgilerini ayarla
        if username and password:
            self.client.username_pw_set(username, password)

        # SSL ayarları
        if use_ssl:
            self.client.tls_set()

    async def publish(self, topic, payload, qos=MQTTQoS.AT_LEAST_ONCE, retain=False):
        # Bir konuya mesaj yayınlar
        if not self.connected:
            success = await self.connect()
            if not success:
                return False

        try:
            # QoS değerini ayarla
            if isinstance(qos, MQTTQoS):
                qos = qos.value

            # Payload'ı hazırla
            if isinstance(payload, dict):
                payload = json.dumps(payload)

            if isinstance(payload, str):
                payload = payload.encode('utf-8')

            # Mesajı yayınla
            result = self.client.publish(topic, payload, qos=qos, retain=retain)

            # Sonucu kontrol et
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"MQTT yayınlama hatası: {mqtt.error_string(result.rc)}")
                return False

            self.logger.debug(f"MQTT mesajı yayınlandı: {topic}")
            return True
        except Exception as e:
            self.logger.error(f"MQTT yayınlama hatası: {str(e)}")
            return False
```

#### IoT Cihaz Yönetimi ✅

```python
# TAMAMLANDI: src/core/iot/device_manager.py modülü oluşturuldu
# Farklı platformlardaki IoT cihazlarını yönetmek için ortak bir arayüz eklendi

class IoTDeviceManager:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger("iot_device_manager")

        # Cihaz listesi
        self.devices = {}

        # Platform bağlantıları
        self.home_assistant = None
        self.mqtt_client = None

    async def initialize(self):
        # IoT cihaz yöneticisini başlatır
        try:
            # Home Assistant bağlantısı
            if "home_assistant" in self.config:
                ha_config = self.config["home_assistant"]
                self.home_assistant = HomeAssistantBridge(
                    host=ha_config.get("host", "localhost"),
                    token=ha_config.get("token"),
                    port=ha_config.get("port", 8123),
                    use_ssl=ha_config.get("use_ssl", False)
                )

                # Home Assistant'ı başlat
                ha_success = await self.home_assistant.initialize()
                if ha_success:
                    # Home Assistant cihazlarını keşfet
                    await self._discover_home_assistant_devices()

            # MQTT bağlantısı
            if "mqtt" in self.config:
                mqtt_config = self.config["mqtt"]
                self.mqtt_client = MQTTClient(
                    broker_host=mqtt_config.get("broker_host", "localhost"),
                    broker_port=mqtt_config.get("broker_port", 1883),
                    client_id=mqtt_config.get("client_id"),
                    username=mqtt_config.get("username"),
                    password=mqtt_config.get("password"),
                    use_ssl=mqtt_config.get("use_ssl", False)
                )

                # MQTT'yi başlat
                mqtt_success = await self.mqtt_client.connect()
                if mqtt_success and "discovery_topic" in mqtt_config:
                    # MQTT cihazlarını keşfet
                    await self._discover_mqtt_devices(mqtt_config["discovery_topic"])

            return True
        except Exception as e:
            self.logger.error(f"IoT cihaz yöneticisi başlatılamadı: {str(e)}")
            return False

    async def control_device(self, device_id, command, params=None):
        # Bir cihazı kontrol eder
        device = await self.get_device(device_id)
        if not device:
            return False

        # Cihaz platformuna göre kontrol et
        if device.platform == DevicePlatform.HOME_ASSISTANT and self.home_assistant:
            entity_id = device.platform_data.get("entity_id")
            domain = entity_id.split('.')[0]
            await self.home_assistant.call_service(domain, command, entity_id, params)
            return True
        elif device.platform == DevicePlatform.MQTT and self.mqtt_client:
            topic = device.platform_data.get("command_topic")
            payload = {"command": command, **(params or {})}
            return await self.mqtt_client.publish(topic, payload)

        return False
```

#### API Entegrasyonu ✅

```python
# TAMAMLANDI: src/api/iot_routes.py modülü oluşturuldu
# IoT cihazlarını kontrol etmek için API endpoint'leri eklendi

@router.get("/devices", response_model=DevicesResponse)
async def get_devices(device_type=None, platform=None, capability=None):
    """Cihazları listeler."""
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()

        # Cihazları getir
        devices = await dm.get_devices(device_type, platform, capability)

        # Yanıt oluştur
        response_devices = []
        for device in devices:
            response_devices.append(DeviceResponse(
                device_id=device.device_id,
                name=device.name,
                device_type=device.device_type.value,
                platform=device.platform.value,
                capabilities=[cap.value for cap in device.capabilities],
                state=device.state,
                last_updated=device.last_updated.isoformat() if device.last_updated else None,
                available=device.available
            ))

        return {"devices": response_devices}
    except Exception as e:
        logging.error(f"Cihazlar listelenirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cihazlar listelenirken hata: {str(e)}"
        )

@router.post("/devices/{device_id}/control", response_model=DeviceControlResponse)
async def control_device(device_id: str, request: DeviceControlRequest):
    """Bir cihazı kontrol eder."""
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()

        # Cihazı kontrol et
        success = await dm.control_device(device_id, request.command, request.params)

        if success:
            return {
                "success": True,
                "device_id": device_id,
                "message": f"Cihaz başarıyla kontrol edildi: {request.command}"
            }
        else:
            return {
                "success": False,
                "device_id": device_id,
                "message": f"Cihaz kontrol edilemedi: {request.command}"
            }
    except Exception as e:
        logging.error(f"Cihaz kontrol edilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cihaz kontrol edilirken hata: {str(e)}"
        )
```

### 3.4 Temel Güvenlik İyileştirmeleri ✅

#### API Key Encryption ✅

```python
# TAMAMLANDI: src/core/security/api_key_manager.py modülü oluşturuldu
# API anahtarlarını güvenli bir şekilde yönetmek için bir sınıf eklendi

class APIKeyManager:
    def __init__(self, storage_path, encryption_key=None, salt=None, user_id="default"):
        self.storage_path = storage_path
        self.user_id = user_id
        self.logger = get_logger("api_key_manager")

        # Depolama dizinini oluştur
        os.makedirs(storage_path, exist_ok=True)

        # Kullanıcı dizinini oluştur
        self.user_path = os.path.join(storage_path, user_id)
        os.makedirs(self.user_path, exist_ok=True)

        # Şifreleme anahtarını ayarla
        self.encryption_key = self._setup_encryption_key(encryption_key)

        # Şifreleme tuzu
        self.salt = salt or os.urandom(16)

        # Fernet şifreleme nesnesi
        self.cipher = Fernet(self.encryption_key)

    def encrypt_key(self, api_key):
        # API anahtarını şifrele
        encrypted_key = self.cipher.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted_key).decode()

    def decrypt_key(self, encrypted_key):
        # Şifrelenmiş API anahtarını çöz
        encrypted_data = base64.urlsafe_b64decode(encrypted_key)
        decrypted_key = self.cipher.decrypt(encrypted_data)
        return decrypted_key.decode()

    def save_key(self, service_name, api_key, metadata=None):
        # API anahtarını güvenli bir şekilde kaydet
        encrypted_key = self.encrypt_key(api_key)

        # Meta verileri hazırla
        metadata = metadata or {}
        metadata.update({
            "service": service_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })

        # Anahtar verilerini hazırla
        key_data = {
            "encrypted_key": encrypted_key,
            "metadata": metadata
        }

        # Anahtar dosyasını kaydet
        key_file = os.path.join(self.user_path, f"{service_name}.json")
        with open(key_file, "w", encoding="utf-8") as f:
            json.dump(key_data, f, ensure_ascii=False, indent=2)

        # Dosya izinlerini ayarla (sadece sahibi okuyabilir)
        os.chmod(key_file, 0o600)
```

#### Güvenli Yapılandırma Yönetimi ✅

```python
# TAMAMLANDI: src/core/security/secure_config.py modülü oluşturuldu
# Hassas yapılandırma verilerini güvenli bir şekilde saklamak için bir sınıf eklendi

class SecureConfig:
    def __init__(self, config_path, encryption_key=None, user_id="default"):
        self.config_path = config_path
        self.user_id = user_id
        self.logger = get_logger("secure_config")

        # Yapılandırma dizinini oluştur
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # API anahtarı yöneticisi
        self.api_key_manager = APIKeyManager(
            storage_path=os.path.join(os.path.dirname(config_path), "api_keys"),
            encryption_key=encryption_key,
            user_id=user_id
        )

        # Yapılandırma verisi
        self.config = {}

        # Hassas alanlar
        self.sensitive_fields = set()

        # Yapılandırmayı yükle
        self._load_config()

    def get(self, key, default=None):
        # Yapılandırma değerini getirir
        return self.config.get(key, default)

    def set(self, key, value, sensitive=False):
        # Yapılandırma değerini ayarlar
        self.config[key] = value

        # Hassas alan ise işaretle
        if sensitive and key != "_sensitive_fields":
            self.sensitive_fields.add(key)
        elif not sensitive and key in self.sensitive_fields:
            self.sensitive_fields.remove(key)

        # Yapılandırmayı kaydet
        return self._save_config()
```

#### Şifre Politikası ✅

```python
# TAMAMLANDI: src/core/security/password_policy.py modülü oluşturuldu
# Şifre güvenlik politikalarını uygulamak için bir sınıf eklendi

class PasswordPolicy:
    def __init__(
        self,
        min_length=8,
        require_uppercase=True,
        require_lowercase=True,
        require_numbers=True,
        require_special=True,
        min_unique_chars=4,
        max_sequential_chars=3,
        max_repeated_chars=3,
        check_common_passwords=True,
        common_passwords_file=None
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special = require_special
        self.min_unique_chars = min_unique_chars
        self.max_sequential_chars = max_sequential_chars
        self.max_repeated_chars = max_repeated_chars
        self.check_common_passwords = check_common_passwords

        # Yaygın şifreler
        self.common_passwords = set()

        if check_common_passwords:
            self._load_common_passwords(common_passwords_file)

    def validate_password(self, password):
        # Şifreyi doğrular
        errors = []

        # Uzunluk kontrolü
        if len(password) < self.min_length:
            errors.append(f"Şifre en az {self.min_length} karakter uzunluğunda olmalıdır")

        # Büyük harf kontrolü
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Şifre en az bir büyük harf içermelidir")

        # Küçük harf kontrolü
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Şifre en az bir küçük harf içermelidir")

        # Rakam kontrolü
        if self.require_numbers and not re.search(r"\d", password):
            errors.append("Şifre en az bir rakam içermelidir")

        # Özel karakter kontrolü
        if self.require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            errors.append("Şifre en az bir özel karakter içermelidir")

        return len(errors) == 0, errors
```

#### JWT Token Güvenliği ✅

```python
# TAMAMLANDI: src/core/auth/auth_utils.py modülü güncellendi
# JWT token güvenliği iyileştirildi

# Token güvenlik ayarları
TOKEN_BLACKLIST = set()  # Geçersiz kılınan token'lar
MAX_TOKENS_PER_USER = 5  # Kullanıcı başına maksimum token sayısı
USER_TOKENS = {}  # Kullanıcı token'ları

def create_access_token(data, expires_delta=None):
    # JWT erişim token'ı oluşturur
    to_encode = data.copy()

    # Token ID ekle
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})

    # Kullanıcı token'larını takip et
    username = data.get("sub")
    if username:
        if username not in USER_TOKENS:
            USER_TOKENS[username] = []

        # Maksimum token sayısını kontrol et
        if len(USER_TOKENS[username]) >= MAX_TOKENS_PER_USER:
            # En eski token'ı geçersiz kıl
            old_token_jti = USER_TOKENS[username].pop(0)
            TOKEN_BLACKLIST.add(old_token_jti)

        # Yeni token'ı ekle
        USER_TOKENS[username].append(jti)

    # Son kullanma tarihini ayarla
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # Token oluşturma zamanı
        "type": "access"  # Token tipi
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def verify_token(token):
    # JWT token'ı doğrular
    try:
        # Token'ı çöz
        payload = decode_token(token)

        # Token ID'sini kontrol et
        jti = payload.get("jti")
        if not jti:
            return None

        # Kara listeyi kontrol et
        if jti in TOKEN_BLACKLIST:
            return None

        # Token tipini kontrol et
        token_type = payload.get("type")
        if not token_type:
            return None

        return payload
    except JWTError:
        return None

def invalidate_token(token):
    # Token'ı geçersiz kılar
    try:
        # Token'ı çöz
        payload = decode_token(token)

        # Token ID'sini al
        jti = payload.get("jti")
        if not jti:
            return False

        # Kara listeye ekle
        TOKEN_BLACKLIST.add(jti)

        # Kullanıcı token'larından çıkar
        username = payload.get("sub")
        if username and username in USER_TOKENS and jti in USER_TOKENS[username]:
            USER_TOKENS[username].remove(jti)

        return True
    except JWTError:
        return False
```

#### Kullanıcı Kimlik Doğrulama Güvenliği ✅

```python
# TAMAMLANDI: src/core/auth/user_auth.py modülü güncellendi
# Kullanıcı kimlik doğrulama güvenliği iyileştirildi

def authenticate_user(self, username, password, ip_address=None, user_agent=None):
    # Kullanıcıyı doğrular
    if not self.user_exists(username):
        return None

    # Kullanıcı verilerini yükle
    user_path = self.get_user_path(username)
    with open(user_path, "r", encoding="utf-8") as f:
        user_data = json.load(f)

    # Hesap kilitli mi kontrol et
    if user_data.get("account_locked_until"):
        locked_until = datetime.fromisoformat(user_data["account_locked_until"])
        if locked_until > datetime.now(timezone.utc):
            self.logger.warning(f"Kilitli hesaba giriş denemesi: {username}")
            return None
        else:
            # Kilit süresini geçmiş, kilidi kaldır
            user_data["account_locked_until"] = None
            user_data["failed_login_attempts"] = 0

    # Şifreyi doğrula
    if not verify_password(password, user_data["hashed_password"]):
        # Başarısız giriş denemesi
        user_data["failed_login_attempts"] = user_data.get("failed_login_attempts", 0) + 1
        user_data["last_failed_login"] = datetime.now(timezone.utc).isoformat()

        # Maksimum başarısız giriş denemesi kontrolü
        max_attempts = 5
        if user_data["failed_login_attempts"] >= max_attempts:
            # Hesabı kilitle (30 dakika)
            lock_duration_minutes = 30
            user_data["account_locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=lock_duration_minutes)).isoformat()
            self.logger.warning(f"Hesap kilitlendi: {username} (çok fazla başarısız giriş denemesi)")

            # Tüm token'ları geçersiz kıl
            invalidate_all_user_tokens(username)

        # Kullanıcı verilerini güncelle
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

        return None

    # Kullanıcı aktif değilse
    if not user_data.get("is_active", True):
        self.logger.warning(f"Pasif hesaba giriş denemesi: {username}")
        return None

    # Başarılı giriş, başarısız giriş sayacını sıfırla
    user_data["failed_login_attempts"] = 0

    # Son giriş zamanını ve bilgilerini güncelle
    now = datetime.now(timezone.utc)
    user_data["last_login"] = now.isoformat()

    # IP ve kullanıcı ajanı bilgilerini güncelle
    if ip_address:
        user_data["last_ip"] = ip_address

        # Bilinen IP'ler listesine ekle
        known_ips = user_data.get("known_ips", [])
        if ip_address not in known_ips:
            known_ips.append(ip_address)
            user_data["known_ips"] = known_ips

    if user_agent:
        user_data["user_agent"] = user_agent

    # Giriş geçmişine ekle
    login_history = user_data.get("login_history", [])
    login_history.append({
        "timestamp": now.isoformat(),
        "ip": ip_address,
        "user_agent": user_agent
    })

    # Giriş geçmişini son 10 girişle sınırla
    user_data["login_history"] = login_history[-10:]

    # Kullanıcı verilerini güncelle
    with open(user_path, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

    # Hassas verileri temizle
    user_data.pop("hashed_password", None)
    user_data.pop("password_history", None)
    user_data.pop("two_factor_secret", None)
    user_data.pop("recovery_codes", None)

    self.logger.info(f"Kullanıcı girişi başarılı: {username}")
    return user_data
```

## 4. Quick Wins (2-4 Ay)

### 4.1 Desktop Control

```python
import subprocess
import platform
import asyncio

class SystemController:
    def __init__(self):
        self.os_type = platform.system()

    async def execute_command(self, command):
        # Sistem komutunu çalıştır
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Komut çalıştırma hatası: {stderr.decode()}")

        return stdout.decode()

    async def open_application(self, app_name):
        # İşletim sistemine göre uygulama aç
        if self.os_type == "Windows":
            return await self.execute_command(f"start {app_name}")
        elif self.os_type == "Darwin":  # macOS
            return await self.execute_command(f"open -a '{app_name}'")
        else:  # Linux
            return await self.execute_command(f"{app_name} &")
```

### 4.2 Context Memory Optimizasyonu

```python
class EnhancedMemoryManager:
    def __init__(self, vector_db, user_id):
        self.vector_db = vector_db
        self.user_id = user_id
        self.conversation_collection = f"conversation_history_{user_id}"

    async def initialize(self):
        # Konuşma geçmişi koleksiyonunu oluştur
        await self.vector_db.create_collection(self.conversation_collection)

    async def add_conversation_entry(self, role, content, context=None):
        # Konuşma girdisini ekle
        metadata = {
            "user_id": self.user_id,
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "context": context or {}
        }

        # Vektör veritabanına ekle
        await self.vector_db.add_texts(
            collection_name=self.conversation_collection,
            texts=[content],
            metadatas=[metadata]
        )

    async def get_relevant_history(self, query, limit=5):
        # Sorguyla ilgili geçmiş konuşmaları getir
        results = await self.vector_db.search(
            collection_name=self.conversation_collection,
            query=query,
            n_results=limit
        )

        return results
```

### 4.3 Mobile Companion (PWA)

```javascript
// next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
});

module.exports = withPWA({
  // Next.js config
});

// manifest.json
{
  "name": "ZEKA Assistant",
  "short_name": "ZEKA",
  "description": "Zenginleştirilmiş Etkileşimli Kişisel Asistan",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#000000",
  "theme_color": "#0099cc",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 4.4 JARVIS-Style UI Themes

```javascript
// theme.js
export const jarvisTheme = {
  colors: {
    primary: '#00ccff',
    secondary: '#0066cc',
    background: '#000000',
    surface: '#111111',
    text: '#ffffff',
    accent: '#ff3300',
    success: '#00ff99',
    warning: '#ffcc00',
    error: '#ff3300'
  },
  fonts: {
    main: '"Rajdhani", sans-serif',
    mono: '"JetBrains Mono", monospace'
  },
  animations: {
    pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    fadeIn: 'fadeIn 0.5s ease-in',
    slideIn: 'slideIn 0.3s ease-out'
  },
  shadows: {
    glow: '0 0 10px rgba(0, 204, 255, 0.5), 0 0 20px rgba(0, 204, 255, 0.3)'
  }
};
```

## 5. Uzun Vadeli Yol Haritası (4+ Ay)

### 5.1 Proaktif Zeka Geliştirme
- Gelişmiş kullanıcı davranış analizi
- Makine öğrenimi modelleri ile tahmin
- Bağlamsal farkındalık
- Kişiselleştirilmiş öneriler

### 5.2 Sistem Entegrasyonları
- Gelişmiş IoT entegrasyonu
- Çoklu cihaz senkronizasyonu
- API entegrasyonları (e-posta, takvim, görevler)
- Bulut servisleri entegrasyonu

### 5.3 Duygusal Zeka
- Ses tonu analizi
- Duygu tanıma
- Kişiselleştirilmiş yanıtlar
- Kullanıcı ruh hali takibi

### 5.4 Teknik Maester Yetenekleri
- Kod geliştirme asistanı
- Proje yönetimi
- Araştırma ve analiz
- 3D görselleştirme ve AR/VR

## 6. Teknik Altyapı Gereksinimleri

### Backend
- FastAPI (async/await)
- Redis (caching)
- PostgreSQL (structured data)
- ChromaDB (vector storage)
- Celery (task queue)
- Docker containers

### AI/ML
- TensorFlow/PyTorch
- Transformers library
- OpenCV
- Speech recognition
- Computer vision models
- Custom fine-tuned models

### Frontend
- Next.js/React
- Three.js
- WebRTC
- WebGL
- Progressive Web App
- Electron (desktop)

## 7. Başarı Kriterleri

### JARVIS-Level Achievement
- Proaktif intelligence
- Natural conversation
- Multi-system control
- Predictive capabilities
- Emotional awareness
- Security excellence

### Success Indicators
- User dependency rate > 80%
- Task automation > 70%
- User satisfaction > 9/10
- System reliability > 99%
- Response accuracy > 95%

---

*"Sometimes you gotta run before you can walk." - Tony Stark*
