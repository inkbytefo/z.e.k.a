import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import json
from datetime import datetime
import base64

from core.openai_client import OpenAIClient
from core.voice_processor import VoiceProcessor
from agents.conversation_agent_streaming import ConversationAgentStreaming
from config import AGENT_CONFIG, ELEVENLABS_API_KEY

# Router oluştur
router = APIRouter(
    tags=["websocket"],
)

# Aktif bağlantıları takip et
active_connections: Dict[str, WebSocket] = {}

# Ses işleme nesnesi
voice_processor = None

# Sohbet ajanı
conversation_agent = None

# Modelleri tanımla
class StreamingChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    language: str = "tr"
    style: str = "friendly"
    model: Optional[str] = None

class VoiceRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: Optional[str] = None

# Ses işleme nesnelerini başlat
def initialize_voice_processor():
    global voice_processor

    if voice_processor is None:
        try:
            # Ses işleme yapılandırması
            voice_config = {
                "default_language": "tr",
                "default_voice_id": "EXAVITQu4vr4xnSDxMaL",  # Varsayılan ElevenLabs ses ID'si
                "tts_model": "eleven_multilingual_v1",
                "whisper_model_size": "base",  # Whisper model boyutu (tiny, base, small, medium, large)
                "cache_path": AGENT_CONFIG["voice_agent"]["cache_path"],
                "target_sample_rate": 44100,
                "target_db": -15,
                "chunk_size": 4096,
                "elevenlabs_api_key": ELEVENLABS_API_KEY
            }

            # Ses işleme nesnesi oluştur
            voice_processor = VoiceProcessor(voice_config)

            logging.info("Ses işleme modülü başlatıldı")
        except Exception as e:
            logging.error(f"Ses işleme modülü başlatılamadı: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ses işleme modülü başlatılamadı: {str(e)}"
            )

# Sohbet ajanını başlat
def initialize_conversation_agent():
    global conversation_agent

    if conversation_agent is None:
        try:
            # OpenAI istemcisini başlat
            openai_client = OpenAIClient(
                api_key=os.getenv("OPENAI_API_KEY"),
                default_model="gpt-4o-mini"
            )

            # Sohbet ajanını başlat
            conversation_agent = ConversationAgentStreaming(
                language_model=openai_client,
                default_language="tr",
                default_style="friendly"
            )

            logging.info("Sohbet ajanı başlatıldı")
        except Exception as e:
            logging.error(f"Sohbet ajanı başlatılamadı: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sohbet ajanı başlatılamadı: {str(e)}"
            )

@router.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Gerçek zamanlı sohbet için WebSocket endpoint'i"""
    # Bağlantıyı kabul et
    await websocket.accept()

    # Bağlantı ID'si oluştur
    connection_id = f"chat_{datetime.now().timestamp()}"
    active_connections[connection_id] = websocket

    # Log ekle
    logging.info(f"Yeni WebSocket bağlantısı: {connection_id} - {websocket.client.host}:{websocket.client.port}")

    # Sohbet ajanını başlat
    try:
        initialize_conversation_agent()
    except Exception as e:
        logging.error(f"Sohbet ajanı başlatılamadı: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Sohbet ajanı başlatılamadı: {str(e)}"
        })
        await websocket.close(code=1011)
        return

    # Hoş geldin mesajı gönder
    await websocket.send_json({
        "type": "connected",
        "message": "WebSocket bağlantısı kuruldu",
        "connection_id": connection_id
    })

    try:
        # Mesajları dinle
        while True:
            # Mesaj al
            data = await websocket.receive_text()
            request_data = json.loads(data)

            # Mesaj tipini kontrol et
            if request_data.get("type") == "chat":
                # Sohbet mesajı
                message = request_data.get("message", "")
                user_id = request_data.get("user_id", "default_user")
                language = request_data.get("language", "tr")
                style = request_data.get("style", "friendly")
                model = request_data.get("model")

                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Mesaj içeriği gereklidir"
                    })
                    continue

                # Kullanıcı mesajını gönder
                await websocket.send_json({
                    "type": "user_message",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })

                # Özel model belirtilmişse geçici olarak ayarla
                openrouter_client = conversation_agent.language_model
                original_model = openrouter_client.default_model
                used_model = original_model

                if model:
                    try:
                        # Geçici olarak modeli değiştir
                        openrouter_client.default_model = model
                        used_model = model
                        logging.info(f"Geçici model değiştirildi: {original_model} -> {model}")
                    except Exception as model_error:
                        logging.error(f"Geçici model değiştirilemedi: {str(model_error)}")

                try:
                    # Streaming yanıt için görev oluştur
                    task_id = f"chat_{datetime.now().timestamp()}"

                    # Yanıt üretmeye başla
                    await websocket.send_json({
                        "type": "assistant_message_start",
                        "timestamp": datetime.now().isoformat(),
                        "model": used_model
                    })

                    # Streaming yanıt al
                    async for chunk in conversation_agent.process_task_streaming(
                        task_id=task_id,
                        description=message,
                        metadata={
                            "action": "chat",
                            "language": language,
                            "style": style,
                            "user_id": user_id,
                            "model": used_model
                        }
                    ):
                        # Yanıt parçasını gönder
                        await websocket.send_json({
                            "type": "assistant_message_chunk",
                            "chunk": chunk,
                            "timestamp": datetime.now().isoformat()
                        })

                    # Yanıt tamamlandı
                    await websocket.send_json({
                        "type": "assistant_message_end",
                        "timestamp": datetime.now().isoformat()
                    })

                finally:
                    # İşlem bittikten sonra orijinal modele geri dön (eğer değiştirilmişse)
                    if model:
                        openrouter_client.default_model = original_model
                        logging.info(f"Model orijinal değerine geri döndürüldü: {original_model}")

            elif request_data.get("type") == "voice":
                try:
                    # Ses işleme modülünü başlat
                    initialize_voice_processor()

                    # Ses verisi
                    audio_data_base64 = request_data.get("audio_data", "")
                    language = request_data.get("language")
                except Exception as e:
                    logging.error(f"Ses işleme modülü başlatılamadı: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Ses işleme modülü başlatılamadı: {str(e)}"
                    })
                    continue

                if not audio_data_base64:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Ses verisi gereklidir"
                    })
                    continue

                try:
                    # Base64 verisini çöz
                    audio_data = base64.b64decode(audio_data_base64)
                    logging.info(f"Ses verisi alındı, boyut: {len(audio_data)} bytes")

                    # Ses tanıma başladı bilgisi gönder
                    await websocket.send_json({
                        "type": "speech_recognition_start",
                        "timestamp": datetime.now().isoformat()
                    })

                    try:
                        # Ses verisini metne dönüştür
                        text = await voice_processor.speech_to_text(audio_data)
                        logging.info(f"Ses tanıma başarılı: '{text}'")

                        # Tanıma sonucunu gönder
                        await websocket.send_json({
                            "type": "speech_recognition_result",
                            "text": text,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as speech_error:
                        logging.error(f"Ses tanıma hatası (iç): {str(speech_error)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Ses tanıma hatası: {str(speech_error)}"
                        })

                except Exception as e:
                    logging.error(f"Ses tanıma hatası: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Ses tanıma hatası: {str(e)}"
                    })

            else:
                # Bilinmeyen mesaj tipi
                await websocket.send_json({
                    "type": "error",
                    "message": "Bilinmeyen mesaj tipi"
                })

    except WebSocketDisconnect:
        # Bağlantı koptu
        logging.info(f"WebSocket bağlantısı koptu: {connection_id}")
    except Exception as e:
        # Hata oluştu
        logging.error(f"WebSocket hatası: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Sunucu hatası: {str(e)}"
            })
        except:
            pass
    finally:
        # Bağlantıyı kaldır
        if connection_id in active_connections:
            del active_connections[connection_id]
