# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Yapılandırma Modülü

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.parent

# Kullanıcı kimliği
USER_ID = os.getenv("USER_ID", "default_user")

# Veri depolama yolları
STORAGE_PATH = os.getenv("STORAGE_PATH", str(PROJECT_ROOT / "data"))
MEMORY_PATH = os.path.join(STORAGE_PATH, "memory")
PROFILES_PATH = os.path.join(STORAGE_PATH, "profiles")
USERS_PATH = os.path.join(STORAGE_PATH, "users")
MODELS_PATH = os.path.join(STORAGE_PATH, "models")
LOGS_PATH = str(PROJECT_ROOT / "logs")

# API yapılandırmaları
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN")
HOME_ASSISTANT_HOST = os.getenv("HOME_ASSISTANT_HOST", "localhost")
HOME_ASSISTANT_PORT = int(os.getenv("HOME_ASSISTANT_PORT", "8123"))
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Uygulama yapılandırması
APP_CONFIG = {
    "max_history_length": 10,
    "default_communication_style": "neutral",
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "enable_voice": os.getenv("ENABLE_VOICE", "False").lower() == "true",
    "default_voice_id": os.getenv("DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),  # Default ElevenLabs ses
    "voice_activation": {
        "enabled": os.getenv("VOICE_ACTIVATION_ENABLED", "False").lower() == "true",
        "default_wake_word": os.getenv("WAKE_WORD", "hey zeka"),
        "activation_threshold": float(os.getenv("ACTIVATION_THRESHOLD", "0.5"))
    },
    "audio": {
        "input_device": os.getenv("AUDIO_INPUT_DEVICE", "default"),
        "output_device": os.getenv("AUDIO_OUTPUT_DEVICE", "default"),
        "sample_rate": int(os.getenv("AUDIO_SAMPLE_RATE", "44100")),
        "channels": int(os.getenv("AUDIO_CHANNELS", "1")),
        "chunk_size": int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
        "format": "float32"
    },
    "speech": {
        "language": os.getenv("SPEECH_LANGUAGE", "tr"),
        "tts_model": os.getenv("TTS_MODEL", "eleven_multilingual_v1"),
        "max_silence": float(os.getenv("MAX_SILENCE_SEC", "1.0")),
        "speech_timeout": float(os.getenv("SPEECH_TIMEOUT_SEC", "15.0"))
    }
}

# Ajan yapılandırmaları
AGENT_CONFIG = {
    "conversation_agent": {
        "name": "Sohbet Ajanı",
        "description": "Genel sohbet ve iletişim"
    },
    "calendar_agent": {
        "name": "Takvim Ajanı",
        "description": "Takvim yönetimi ve toplantı planlaması"
    },
    "email_agent": {
        "name": "E-posta Ajanı",
        "description": "E-posta yönetimi ve özetleme"
    },
    "research_agent": {
        "name": "Araştırma Ajanı",
        "description": "İnternet araştırması ve bilgi derleme"
    },
    "coding_agent": {
        "name": "Kodlama Ajanı",
        "description": "Kod yardımı ve hata ayıklama"
    },
    "voice_agent": {
        "name": "Ses Ajanı",
        "description": "Sesli iletişim ve ses işleme yönetimi",
        "voice_profiles_path": os.path.join(STORAGE_PATH, "voice_profiles"),
        "cache_path": os.path.join(STORAGE_PATH, "voice_cache")
    },
    "desktop_agent": {
        "name": "Masaüstü Ajanı",
        "description": "Masaüstü ortamı kontrolü ve otomasyonu",
        "tesseract_path": os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    }
}

# Ses önbellekleme ayarları
VOICE_CACHE_CONFIG = {
    "max_cache_size_mb": int(os.getenv("VOICE_CACHE_SIZE_MB", "512")),
    "max_cache_age_days": int(os.getenv("VOICE_CACHE_AGE_DAYS", "30")),
    "enable_cache": os.getenv("ENABLE_VOICE_CACHE", "True").lower() == "true"
}

# IoT yapılandırması
IOT_CONFIG = {
    "devices_file": os.path.join(STORAGE_PATH, "iot", "devices.json"),
    "home_assistant": {
        "host": HOME_ASSISTANT_HOST,
        "port": HOME_ASSISTANT_PORT,
        "token": HOME_ASSISTANT_TOKEN,
        "use_ssl": os.getenv("HOME_ASSISTANT_SSL", "False").lower() == "true"
    },
    "mqtt": {
        "broker_host": MQTT_BROKER_HOST,
        "broker_port": MQTT_BROKER_PORT,
        "username": MQTT_USERNAME,
        "password": MQTT_PASSWORD,
        "use_ssl": os.getenv("MQTT_SSL", "False").lower() == "true",
        "discovery_topic": os.getenv("MQTT_DISCOVERY_TOPIC", "homeassistant")
    }
}
