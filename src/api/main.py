"""
ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
API Modülü
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Proje kök dizinini ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Modülleri içe aktar
from core.vector_database import VectorDatabase
from core.user_profile import UserProfile
from core.provider_manager import ProviderManager
from agents.conversation_agent import ConversationAgent
from config import PROFILES_PATH

# Rotaları içe aktar
from .auth_routes import router as auth_router
from .weather_routes import router as weather_router
from .voice_routes import router as voice_router
from .websocket_routes import router as websocket_router
from .proactive_routes import router as proactive_router
from .iot_routes import router as iot_router
from .routes.desktop import router as desktop_router
from .api_key_routes import router as api_key_router

# API uygulamasını oluştur
app = FastAPI(
    title="ZEKA API",
    description="Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı API",
    version="1.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm kaynaklara izin ver (geliştirme için)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket için CORS ayarları
# Starlette'in yeni sürümlerinde WebSocketRoute farklı bir şekilde ele alınıyor
# Bu nedenle basit bir CORS middleware kullanıyoruz

# Rotaları ekle
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(voice_router)
app.include_router(websocket_router, prefix="")
app.include_router(proactive_router)
app.include_router(iot_router)
app.include_router(desktop_router, prefix="/api")
app.include_router(api_key_router)

# Modelleri tanımla
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    language: str = "tr"
    style: str = "friendly"
    model: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    model: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ConversationHistoryResponse(BaseModel):
    messages: List[Message]

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str

class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    current_model: str

class SetModelRequest(BaseModel):
    model: str

class AddProviderRequest(BaseModel):
    provider_id: str
    name: str
    base_url: str
    api_key: Optional[str] = None
    description: str = ""
    models: List[str] = []
    auth_type: str = "bearer"
    metadata: Optional[Dict[str, Any]] = None

class SetModelResponse(BaseModel):
    success: bool
    model: str
    message: Optional[str] = None

class EmbeddingModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: Optional[str] = None

class EmbeddingModelListResponse(BaseModel):
    models: List[EmbeddingModelInfo]
    current_model: str
    current_function: str

class SetEmbeddingModelRequest(BaseModel):
    model: str

class SetEmbeddingModelResponse(BaseModel):
    success: bool
    model: str
    function: str
    message: Optional[str] = None

class UserModelPreferences(BaseModel):
    ai_model: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_function: Optional[str] = None
    voice_model: Optional[str] = None

class UserModelPreferencesResponse(BaseModel):
    success: bool
    preferences: UserModelPreferences
    message: Optional[str] = None

class SetUserModelPreferenceRequest(BaseModel):
    user_id: str
    model_type: str  # ai_model, embedding_model, embedding_function, voice_model
    model_value: str

# Global değişkenler
conversation_agent = None
provider_manager = None

@app.on_event("startup")
async def startup_event():
    global conversation_agent, provider_manager

    # Varsayılan kullanıcı profili
    user_id = "default_user"

    try:
        # Kullanıcı profilini yükle
        user_profile = UserProfile(user_id, storage_path=PROFILES_PATH)
        user_preferences = user_profile.get_all_model_preferences()

        # Kullanıcı tercihlerinden model ayarlarını al
        ai_model = user_preferences.get("ai_model") or "anthropic/claude-3-haiku"
        embedding_model = user_preferences.get("embedding_model") or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        embedding_function = user_preferences.get("embedding_function") or os.getenv("EMBEDDING_FUNCTION", "sentence_transformer")

        logging.info(f"Kullanıcı tercihleri yüklendi: AI Model={ai_model}, Embedding={embedding_function}/{embedding_model}")
    except Exception as e:
        logging.warning(f"Kullanıcı tercihleri yüklenemedi, varsayılan değerler kullanılıyor: {str(e)}")
        # Çevre değişkenlerinden embedding ayarlarını al
        embedding_function = os.getenv("EMBEDDING_FUNCTION", "sentence_transformer")
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        ai_model = "anthropic/claude-3-haiku"

    # Provider manager'ı başlat
    provider_manager = ProviderManager()

    # Varsayılan sağlayıcıyı belirle (OpenAI varsa onu, yoksa ilk uygun olanı)
    providers = provider_manager.list_providers()
    default_provider_id = "openai"

    if "openai" not in providers or not os.getenv("OPENAI_API_KEY"):
        # OpenAI yoksa diğer sağlayıcıları kontrol et
        for pid, pdata in providers.items():
            if not pdata.get("requires_api_key", True):
                default_provider_id = pid
                break
            elif os.getenv(pdata.get("env_key", f"{pid.upper()}_API_KEY")):
                default_provider_id = pid
                break

    # AI istemcisini oluştur
    openai_client = provider_manager.create_client(
        default_provider_id,
        ai_model if ai_model.startswith("gpt-") else None
    )

    if not openai_client:
        logging.error(f"AI istemcisi oluşturulamadı. Sağlayıcı: {default_provider_id}")
        # Fallback olarak demo client oluştur
        from core.openai_client import OpenAIClient
        openai_client = OpenAIClient(
            provider_name="demo",
            api_key="demo-key",
            base_url="http://localhost:8080/v1",
            default_model="gpt-3.5-turbo"
        )

    # Vektör veritabanını başlat
    vector_db = VectorDatabase.get_instance(
        embedding_function_name=embedding_function,
        embedding_model_name=embedding_model
    )

    # Sohbet ajanını başlat
    conversation_agent = ConversationAgent(
        language_model=openai_client,
        default_language="tr",
        default_style="friendly"
    )

    logging.info(f"API başlatıldı ve sohbet ajanı hazır. AI Model={ai_model}, Embedding: {embedding_function}/{embedding_model}")

@app.get("/api/health")
async def health_check():
    """Sağlık kontrolü endpoint'i"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Sohbet mesajı gönderme endpoint'i"""
    if not conversation_agent:
        raise HTTPException(status_code=503, detail="Sohbet ajanı henüz başlatılmadı")

    try:
        # Özel model belirtilmişse geçici olarak ayarla
        openrouter_client = conversation_agent.language_model
        original_model = openrouter_client.default_model
        used_model = original_model

        if request.model:
            try:
                # Geçici olarak modeli değiştir
                openrouter_client.default_model = request.model
                used_model = request.model
                logging.info(f"Geçici model değiştirildi: {original_model} -> {request.model}")
            except Exception as model_error:
                logging.error(f"Geçici model değiştirilemedi: {str(model_error)}")
                # Hata durumunda varsayılan modeli kullan

        try:
            # Sohbet ajanına mesajı gönder
            result = await conversation_agent.process_task(
                task_id=f"chat_{datetime.now().timestamp()}",
                description=request.message,
                metadata={
                    "action": "chat",
                    "language": request.language,
                    "style": request.style,
                    "user_id": request.user_id,
                    "model": used_model
                }
            )

            if result.get("success", False):
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id", ""),
                    "model": used_model
                }
            else:
                return {
                    "success": False,
                    "response": "",
                    "message": result.get("message", "Bilinmeyen hata"),
                    "model": used_model
                }
        finally:
            # İşlem bittikten sonra orijinal modele geri dön (eğer değiştirilmişse)
            if request.model:
                openrouter_client.default_model = original_model
                logging.info(f"Model orijinal değerine geri döndürüldü: {original_model}")
    except Exception as e:
        logging.error(f"Sohbet işleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sohbet işleme hatası: {str(e)}")

@app.get("/api/conversation-history", response_model=ConversationHistoryResponse)
async def get_conversation_history(limit: int = 10, user_id: str = "default_user"):
    """Sohbet geçmişini getirme endpoint'i"""
    if not conversation_agent:
        raise HTTPException(status_code=503, detail="Sohbet ajanı henüz başlatılmadı")

    try:
        # Sohbet geçmişini al
        history = conversation_agent.conversation_history[-limit:] if limit > 0 else []

        # Yanıt formatına dönüştür
        messages = []
        for entry in history:
            # Kullanıcı mesajı
            messages.append({
                "role": "user",
                "content": entry.get("user", ""),
                "timestamp": entry.get("timestamp", "")
            })

            # Asistan yanıtı
            messages.append({
                "role": "assistant",
                "content": entry.get("assistant", ""),
                "timestamp": entry.get("timestamp", "")
            })

        return {"messages": messages}
    except Exception as e:
        logging.error(f"Sohbet geçmişi getirme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sohbet geçmişi getirme hatası: {str(e)}")

@app.get("/api/models", response_model=ModelListResponse)
async def get_models():
    """Kullanılabilir modelleri listeler ve mevcut modeli döndürür"""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Sağlayıcı yöneticisi henüz başlatılmadı")

    try:
        # Tüm sağlayıcılardan modelleri topla
        models = []
        providers = provider_manager.list_providers()

        for provider_id, provider_data in providers.items():
            provider_models = provider_data.get("models", [])
            for model_id in provider_models:
                models.append({
                    "id": f"{provider_id}/{model_id}" if provider_id != "openai" else model_id,
                    "name": model_id,
                    "provider": provider_data.get("name", provider_id)
                })

        # Mevcut modeli al
        current_model = "gpt-4o-mini"  # Varsayılan
        if conversation_agent and conversation_agent.language_model:
            current_model = conversation_agent.language_model.default_model

        return {"models": models, "current_model": current_model}
    except Exception as e:
        logging.error(f"Model listesi alınırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model listesi alınamadı: {str(e)}")

@app.post("/api/models/set", response_model=SetModelResponse)
async def set_model(request: SetModelRequest, user_id: str = "default_user"):
    """Kullanılacak modeli değiştirir"""
    if not conversation_agent or not conversation_agent.language_model:
        raise HTTPException(status_code=503, detail="Dil modeli henüz başlatılmadı")

    try:
        # OpenAI istemcisini al
        openai_client = conversation_agent.language_model

        # Modeli değiştir
        old_model = openai_client.default_model
        openai_client.default_model = request.model

        # Kullanıcı profilini güncelle
        try:
            user_profile = UserProfile(user_id, storage_path=PROFILES_PATH)
            user_profile.set_model_preference("ai_model", request.model)
            logging.info(f"Kullanıcı model tercihi kaydedildi: {user_id} -> {request.model}")
        except Exception as profile_error:
            logging.error(f"Kullanıcı profili güncellenirken hata: {str(profile_error)}")

        logging.info(f"Model değiştirildi: {old_model} -> {request.model}")

        return {
            "success": True,
            "model": request.model,
            "message": f"Model başarıyla değiştirildi: {request.model}"
        }
    except Exception as e:
        logging.error(f"Model değiştirilirken hata: {str(e)}")
        return {
            "success": False,
            "model": conversation_agent.language_model.default_model if conversation_agent and conversation_agent.language_model else "gpt-4o-mini",
            "message": f"Model değiştirilemedi: {str(e)}"
        }

@app.get("/api/embedding-models", response_model=EmbeddingModelListResponse)
async def get_embedding_models():
    """Kullanılabilir embedding modellerini listeler ve mevcut modeli döndürür"""
    try:
        # Desteklenen embedding modellerini tanımla
        models = [
            {
                "id": "sentence-transformers/all-MiniLM-L6-v2",
                "name": "all-MiniLM-L6-v2",
                "provider": "sentence-transformers",
                "description": "Genel amaçlı, hızlı ve hafif embedding modeli"
            },
            {
                "id": "sentence-transformers/multi-qa-mpnet-base-dot-v1",
                "name": "multi-qa-mpnet-base-dot-v1",
                "provider": "sentence-transformers",
                "description": "Soru-cevap için optimize edilmiş model"
            },
            {
                "id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "name": "paraphrase-multilingual-MiniLM-L12-v2",
                "provider": "sentence-transformers",
                "description": "Çok dilli embedding modeli"
            },
            {
                "id": "huggingface/sentence-transformers/all-mpnet-base-v2",
                "name": "all-mpnet-base-v2",
                "provider": "huggingface",
                "description": "Yüksek kaliteli, daha büyük embedding modeli"
            },
            {
                "id": "openai/text-embedding-ada-002",
                "name": "text-embedding-ada-002",
                "provider": "openai",
                "description": "OpenAI'nin genel amaçlı embedding modeli"
            },
            {
                "id": "cohere/embed-english-v2.0",
                "name": "embed-english-v2.0",
                "provider": "cohere",
                "description": "Cohere'in İngilizce embedding modeli"
            }
        ]

        # Mevcut modeli al
        current_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        current_function = os.getenv("EMBEDDING_FUNCTION", "sentence_transformer")

        return {
            "models": models,
            "current_model": current_model,
            "current_function": current_function
        }
    except Exception as e:
        logging.error(f"Embedding model listesi alınırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding model listesi alınamadı: {str(e)}")

@app.post("/api/embedding-models/set", response_model=SetEmbeddingModelResponse)
async def set_embedding_model(request: SetEmbeddingModelRequest, user_id: str = "default_user"):
    """Kullanılacak embedding modelini değiştirir"""
    try:
        # Vektör veritabanını al
        vector_db = VectorDatabase.get_instance()

        # Modeli değiştir
        old_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        old_function = os.getenv("EMBEDDING_FUNCTION", "sentence_transformer")

        # Yeni model ve fonksiyon adını ayarla
        model_parts = request.model.split('/')
        if len(model_parts) >= 2:
            provider = model_parts[0]
            model_name = model_parts[-1]

            # Provider'a göre fonksiyon adını belirle
            function_name = "sentence_transformer"
            if provider == "huggingface":
                function_name = "huggingface"
            elif provider == "openai":
                function_name = "openai"
            elif provider == "cohere":
                function_name = "cohere"
        else:
            model_name = request.model
            function_name = old_function

        # Vektör veritabanını yeni model ile güncelle
        await vector_db.update_embedding_function(function_name, model_name)

        # Çevre değişkenlerini güncelle
        os.environ["EMBEDDING_MODEL"] = model_name
        os.environ["EMBEDDING_FUNCTION"] = function_name

        # Kullanıcı profilini güncelle
        try:
            user_profile = UserProfile(user_id, storage_path=PROFILES_PATH)
            user_profile.set_model_preference("embedding_model", model_name)
            user_profile.set_model_preference("embedding_function", function_name)
            logging.info(f"Kullanıcı embedding model tercihi kaydedildi: {user_id} -> {model_name}")
        except Exception as profile_error:
            logging.error(f"Kullanıcı profili güncellenirken hata: {str(profile_error)}")

        logging.info(f"Embedding modeli değiştirildi: {old_model} -> {model_name}")

        return {
            "success": True,
            "model": model_name,
            "function": function_name,
            "message": f"Embedding modeli başarıyla değiştirildi: {model_name}"
        }
    except Exception as e:
        logging.error(f"Embedding modeli değiştirilirken hata: {str(e)}")
        return {
            "success": False,
            "model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            "function": os.getenv("EMBEDDING_FUNCTION", "sentence_transformer"),
            "message": f"Embedding modeli değiştirilemedi: {str(e)}"
        }

@app.get("/api/user/model-preferences", response_model=UserModelPreferencesResponse)
async def get_user_model_preferences(user_id: str = "default_user"):
    """Kullanıcının model tercihlerini getirir"""
    try:
        # Kullanıcı profilini al
        user_profile = UserProfile(user_id, storage_path=PROFILES_PATH)
        model_preferences = user_profile.get_all_model_preferences()

        # Yanıt oluştur
        return {
            "success": True,
            "preferences": model_preferences,
            "message": "Model tercihleri başarıyla getirildi"
        }
    except Exception as e:
        logging.error(f"Kullanıcı model tercihleri getirilirken hata: {str(e)}")
        return {
            "success": False,
            "preferences": {
                "ai_model": None,
                "embedding_model": None,
                "embedding_function": None,
                "voice_model": None
            },
            "message": f"Model tercihleri getirilemedi: {str(e)}"
        }

@app.post("/api/user/model-preferences/set", response_model=UserModelPreferencesResponse)
async def set_user_model_preference(request: SetUserModelPreferenceRequest):
    """Kullanıcının model tercihini ayarlar"""
    try:
        # Kullanıcı profilini al
        user_profile = UserProfile(request.user_id, storage_path=PROFILES_PATH)

        # Model tercihini ayarla
        user_profile.set_model_preference(request.model_type, request.model_value)

        # Güncellenmiş tercihleri al
        model_preferences = user_profile.get_all_model_preferences()

        logging.info(f"Kullanıcı model tercihi ayarlandı: {request.user_id} -> {request.model_type}={request.model_value}")

        return {
            "success": True,
            "preferences": model_preferences,
            "message": f"Model tercihi başarıyla ayarlandı: {request.model_type}={request.model_value}"
        }
    except ValueError as ve:
        logging.error(f"Geçersiz model türü: {str(ve)}")
        return {
            "success": False,
            "preferences": UserProfile(request.user_id, storage_path=PROFILES_PATH).get_all_model_preferences(),
            "message": str(ve)
        }
    except Exception as e:
        logging.error(f"Kullanıcı model tercihi ayarlanırken hata: {str(e)}")
        return {
            "success": False,
            "preferences": {
                "ai_model": None,
                "embedding_model": None,
                "embedding_function": None,
                "voice_model": None
            },
            "message": f"Model tercihi ayarlanamadı: {str(e)}"
        }


# Provider yönetimi endpoint'leri

@app.get("/api/providers")
async def get_providers():
    """Kullanılabilir AI sağlayıcılarını listeler"""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Sağlayıcı yöneticisi henüz başlatılmadı")

    try:
        providers = provider_manager.list_providers()
        provider_list = []

        for provider_id, provider_data in providers.items():
            provider_list.append({
                "id": provider_id,
                "name": provider_data.get("name", provider_id),
                "description": provider_data.get("description", ""),
                "base_url": provider_data.get("base_url", ""),
                "auth_type": provider_data.get("auth_type", "bearer"),
                "requires_api_key": provider_data.get("requires_api_key", True),
                "models": provider_data.get("models", []),
                "supports_streaming": provider_data.get("supports_streaming", True),
                "enabled": provider_data.get("enabled", True),
                "custom": provider_data.get("custom", False)
            })

        return {"providers": provider_list}
    except Exception as e:
        logging.error(f"Sağlayıcı listesi alınırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sağlayıcı listesi alınamadı: {str(e)}")


@app.post("/api/providers/add")
async def add_provider(request: AddProviderRequest):
    """Yeni AI sağlayıcısı ekler"""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Sağlayıcı yöneticisi henüz başlatılmadı")

    try:
        success = provider_manager.add_provider(
            provider_id=request.provider_id,
            name=request.name,
            base_url=request.base_url,
            api_key=request.api_key,
            description=request.description,
            models=request.models,
            auth_type=request.auth_type,
            metadata=request.metadata
        )

        if success:
            return {"success": True, "message": f"Sağlayıcı başarıyla eklendi: {request.name}"}
        else:
            raise HTTPException(status_code=400, detail="Sağlayıcı eklenemedi")

    except Exception as e:
        logging.error(f"Sağlayıcı eklenirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sağlayıcı eklenemedi: {str(e)}")


@app.delete("/api/providers/{provider_id}")
async def remove_provider(provider_id: str):
    """AI sağlayıcısını kaldırır"""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Sağlayıcı yöneticisi henüz başlatılmadı")

    try:
        success = provider_manager.remove_provider(provider_id)

        if success:
            return {"success": True, "message": f"Sağlayıcı başarıyla kaldırıldı: {provider_id}"}
        else:
            raise HTTPException(status_code=404, detail="Sağlayıcı bulunamadı")

    except Exception as e:
        logging.error(f"Sağlayıcı kaldırılırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sağlayıcı kaldırılamadı: {str(e)}")


@app.post("/api/providers/{provider_id}/discover-models")
async def discover_provider_models(provider_id: str):
    """Sağlayıcının modellerini keşfeder"""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Sağlayıcı yöneticisi henüz başlatılmadı")

    try:
        models = await provider_manager.discover_models(provider_id)
        return {"success": True, "models": models, "count": len(models)}

    except Exception as e:
        logging.error(f"Model keşfi sırasında hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model keşfi başarısız: {str(e)}")


@app.get("/api/providers/{provider_id}")
async def get_provider_details(provider_id: str):
    """Belirli bir sağlayıcının detaylarını getirir"""
    if not provider_manager:
        raise HTTPException(status_code=503, detail="Sağlayıcı yöneticisi henüz başlatılmadı")

    try:
        provider = provider_manager.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Sağlayıcı bulunamadı")

        return {
            "id": provider_id,
            "name": provider.get("name", provider_id),
            "description": provider.get("description", ""),
            "base_url": provider.get("base_url", ""),
            "auth_type": provider.get("auth_type", "bearer"),
            "requires_api_key": provider.get("requires_api_key", True),
            "models": provider.get("models", []),
            "supports_streaming": provider.get("supports_streaming", True),
            "enabled": provider.get("enabled", True),
            "custom": provider.get("custom", False),
            "created_at": provider.get("created_at"),
            "updated_at": provider.get("updated_at"),
            "last_model_discovery": provider.get("last_model_discovery")
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Sağlayıcı detayları alınırken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sağlayıcı detayları alınamadı: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Port 8001'e güncellendi
