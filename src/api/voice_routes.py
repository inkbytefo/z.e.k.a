from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Literal
import logging
import io
import base64
import asyncio
import json
from datetime import datetime

from core.voice_processor import VoiceProcessor, ListeningMode
from core.voice_profile import VoiceProfile
from core.wake_word_detector import WakeWordDetector
from agents.voice_agent import VoiceAgent
from config import AGENT_CONFIG

# Router oluştur
router = APIRouter(
    prefix="/api/voice",
    tags=["voice"],
    responses={404: {"description": "Not found"}},
)

# Ses işleme nesnesi
voice_processor = None
voice_agent = None

# Modelleri tanımla
class TextToSpeechRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    rate: Optional[float] = 1.0
    pitch: Optional[float] = 1.0
    volume: Optional[float] = 1.0

class TextToSpeechResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None  # Base64 encoded audio
    error: Optional[str] = None

class SpeechToTextResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    command: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class ListeningModeRequest(BaseModel):
    mode: Literal["manual", "wake_word", "continuous"]
    wake_words: Optional[List[str]] = None
    sensitivity: Optional[float] = 0.7
    language: Optional[str] = None

class ListeningModeResponse(BaseModel):
    success: bool
    mode: Optional[str] = None
    error: Optional[str] = None

class WakeWordConfig(BaseModel):
    access_key: Optional[str] = None
    keywords: List[str]
    sensitivities: Optional[List[float]] = None
    device_index: Optional[int] = -1

class VoiceMessage(BaseModel):
    type: Literal["text", "command", "error", "status"]
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Ses işleme nesnelerini başlat
def initialize_voice_processor():
    global voice_processor, voice_agent

    if voice_processor is None:
        try:
            # Ses işleme yapılandırması
            voice_config = {
                # Temel ayarlar
                "default_language": "tr",
                "default_voice_id": "EXAVITQu4vr4xnSDxMaL",  # Varsayılan ElevenLabs ses ID'si
                "tts_model": "eleven_multilingual_v1",
                "cache_path": AGENT_CONFIG["voice_agent"]["cache_path"],
                "target_sample_rate": 44100,
                "target_db": -15,
                "chunk_size": 4096,

                # Whisper ayarları
                "whisper_model_size": "small",  # Whisper model boyutu (tiny, base, small, medium, large)
                "whisper_compute_type": "float16",  # Hesaplama tipi (int8, float16, float32)
                "whisper_device": "cpu",  # Cihaz (cpu, cuda, cuda:0, ...)
                "vad_filter": True,  # Ses aktivitesi algılama filtresi
                "vad_parameters": {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400
                },

                # Wake word ayarları
                "enable_wake_word": False,  # Wake word algılama aktif mi
                "wake_word_config": {
                    "keywords": ["hey zeka"],
                    "sensitivities": [0.7]
                },

                # VAD ayarları
                "enable_vad": True,  # Ses aktivitesi algılama aktif mi
                "vad_aggressiveness": 3,  # VAD agresiflik seviyesi (0-3)

                # Ses kaydı ayarları
                "audio_channels": 1,
                "audio_rate": 16000,
                "audio_chunk": 1024,
                "silence_threshold": 500,
                "silence_duration": 1.5,  # saniye
                "max_speech_duration": 10  # saniye
            }

            # Ses işleme nesnesi oluştur
            voice_processor = VoiceProcessor(voice_config)

            # Ses ajanı oluştur
            voice_agent = VoiceAgent(AGENT_CONFIG["voice_agent"])

            logging.info("Ses işleme modülü başlatıldı")
        except Exception as e:
            logging.error(f"Ses işleme modülü başlatılamadı: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ses işleme modülü başlatılamadı: {str(e)}"
            )

@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    timeout: Optional[int] = Form(10000)
):
    """Ses verisini metne dönüştürür.

    Args:
        audio: Ses dosyası
        language: Dil kodu (opsiyonel)
        timeout: Zaman aşımı süresi (ms)

    Returns:
        SpeechToTextResponse: Tanıma sonucu
    """
    # Ses işleme modülünü başlat
    initialize_voice_processor()

    try:
        # Ses verisini oku
        audio_data = await audio.read()

        # Ses ajanı ile işle
        task_id = f"stt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = await voice_agent.process_task(
            task_id=task_id,
            metadata={
                "type": "speech_to_text",
                "audio_data": audio_data,
                "language": language
            }
        )

        if result["status"] == "success":
            return {
                "success": True,
                "text": result["text"],
                "command": result.get("command"),
                "result": result.get("result")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Bilinmeyen hata")
            }

    except Exception as e:
        logging.error(f"Ses tanıma hatası: {str(e)}")
        return {
            "success": False,
            "error": f"Ses tanıma hatası: {str(e)}"
        }

@router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(request: TextToSpeechRequest):
    """Metni ses verisine dönüştürür.

    Args:
        request: Ses sentezleme isteği

    Returns:
        TextToSpeechResponse: Sentezleme sonucu
    """
    # Ses işleme modülünü başlat
    initialize_voice_processor()

    try:
        # Ses ajanı ile işle
        task_id = f"tts_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = await voice_agent.process_task(
            task_id=task_id,
            metadata={
                "type": "text_to_speech",
                "text": request.text,
                "voice_id": request.voice_id,
                "rate": request.rate,
                "pitch": request.pitch,
                "volume": request.volume
            }
        )

        if result["status"] == "success":
            # Ses verisini Base64 ile kodla
            audio_base64 = base64.b64encode(result["audio_data"]).decode("utf-8")

            return {
                "success": True,
                "audio_data": audio_base64
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Bilinmeyen hata")
            }

    except Exception as e:
        logging.error(f"Ses sentezleme hatası: {str(e)}")
        return {
            "success": False,
            "error": f"Ses sentezleme hatası: {str(e)}"
        }

@router.get("/stream-speech")
async def stream_speech(text: str, voice_id: Optional[str] = None):
    """Metni ses olarak stream eder.

    Args:
        text: Sese dönüştürülecek metin
        voice_id: Ses profili ID'si (opsiyonel)

    Returns:
        StreamingResponse: Ses stream'i
    """
    # Ses işleme modülünü başlat
    initialize_voice_processor()

    try:
        # Ses verisini oluştur
        audio_data = await voice_processor.text_to_speech(text, voice_id=voice_id)

        # Stream olarak döndür
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav"
        )

    except Exception as e:
        logging.error(f"Ses stream hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ses stream hatası: {str(e)}"
        )

@router.post("/listening-mode", response_model=ListeningModeResponse)
async def set_listening_mode(request: ListeningModeRequest):
    """Dinleme modunu ayarlar.

    Args:
        request: Dinleme modu isteği

    Returns:
        ListeningModeResponse: İşlem sonucu
    """
    # Ses işleme modülünü başlat
    initialize_voice_processor()

    try:
        # Dinleme modunu belirle
        mode_map = {
            "manual": ListeningMode.MANUAL,
            "wake_word": ListeningMode.WAKE_WORD,
            "continuous": ListeningMode.CONTINUOUS
        }

        mode = mode_map.get(request.mode)
        if not mode:
            return {
                "success": False,
                "error": f"Geçersiz dinleme modu: {request.mode}"
            }

        # Wake word ayarlarını güncelle
        if mode == ListeningMode.WAKE_WORD and request.wake_words:
            voice_processor.config["enable_wake_word"] = True
            voice_processor.config["wake_word_config"]["keywords"] = request.wake_words

            if request.sensitivity:
                voice_processor.config["wake_word_config"]["sensitivities"] = [
                    request.sensitivity for _ in request.wake_words
                ]

            # Wake word detector'ı yeniden başlat
            if voice_processor.wake_word_detector:
                await voice_processor.wake_word_detector.stop()
                voice_processor.wake_word_detector = WakeWordDetector(
                    voice_processor.config["wake_word_config"]
                )

        # Dil ayarını güncelle
        if request.language:
            voice_processor.config["default_language"] = request.language

        # Dinleme modunu başlat
        success = await voice_processor.start_listening(
            mode=mode,
            callback=lambda text: voice_agent.process_command(text)
        )

        if success:
            return {
                "success": True,
                "mode": request.mode
            }
        else:
            return {
                "success": False,
                "error": "Dinleme modu başlatılamadı"
            }

    except Exception as e:
        logging.error(f"Dinleme modu ayarlama hatası: {str(e)}")
        return {
            "success": False,
            "error": f"Dinleme modu ayarlama hatası: {str(e)}"
        }

@router.post("/stop-listening", response_model=ListeningModeResponse)
async def stop_listening():
    """Dinleme modunu durdurur.

    Returns:
        ListeningModeResponse: İşlem sonucu
    """
    # Ses işleme modülünü başlat
    initialize_voice_processor()

    try:
        # Dinleme modunu durdur
        await voice_processor.stop_listening()

        return {
            "success": True,
            "mode": "manual"
        }

    except Exception as e:
        logging.error(f"Dinleme durdurma hatası: {str(e)}")
        return {
            "success": False,
            "error": f"Dinleme durdurma hatası: {str(e)}"
        }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint'i.

    Bu endpoint, gerçek zamanlı ses iletişimi için kullanılır.
    """
    await websocket.accept()

    # Ses işleme modülünü başlat
    initialize_voice_processor()

    # WebSocket bağlantısı için callback
    async def on_speech_detected(text: str):
        """Konuşma algılandığında çağrılır."""
        try:
            # Yanıt oluştur
            message = VoiceMessage(
                type="text",
                content=text,
                timestamp=datetime.now().isoformat(),
                metadata={"source": "user"}
            )

            # WebSocket üzerinden gönder
            await websocket.send_text(json.dumps(message.dict()))

            # Ajanı kullanarak yanıt oluştur
            result = await voice_agent.process_command(text)

            if result["status"] == "success":
                # Yanıt mesajı
                response_message = VoiceMessage(
                    type="text",
                    content=result.get("result", {}).get("response", "Anlaşıldı"),
                    timestamp=datetime.now().isoformat(),
                    metadata={"source": "assistant"}
                )

                # WebSocket üzerinden gönder
                await websocket.send_text(json.dumps(response_message.dict()))

                # Ses yanıtı oluştur
                audio_data = await voice_processor.text_to_speech(response_message.content)

                # Base64 ile kodla
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")

                # Ses mesajı
                audio_message = VoiceMessage(
                    type="command",
                    content="play_audio",
                    timestamp=datetime.now().isoformat(),
                    metadata={"audio_data": audio_base64}
                )

                # WebSocket üzerinden gönder
                await websocket.send_text(json.dumps(audio_message.dict()))
            else:
                # Hata mesajı
                error_message = VoiceMessage(
                    type="error",
                    content=result.get("error", "Bir hata oluştu"),
                    timestamp=datetime.now().isoformat()
                )

                # WebSocket üzerinden gönder
                await websocket.send_text(json.dumps(error_message.dict()))

        except Exception as e:
            logging.error(f"WebSocket yanıt hatası: {str(e)}")

            # Hata mesajı
            error_message = VoiceMessage(
                type="error",
                content=f"İşlem hatası: {str(e)}",
                timestamp=datetime.now().isoformat()
            )

            # WebSocket üzerinden gönder
            await websocket.send_text(json.dumps(error_message.dict()))

    # Callback'i ayarla
    voice_processor.speech_callback = on_speech_detected

    try:
        # Bağlantı durumu mesajı
        status_message = VoiceMessage(
            type="status",
            content="connected",
            timestamp=datetime.now().isoformat()
        )

        # WebSocket üzerinden gönder
        await websocket.send_text(json.dumps(status_message.dict()))

        # Mesajları dinle
        while True:
            data = await websocket.receive_text()

            try:
                # JSON verisini ayrıştır
                message_data = json.loads(data)

                # Komut tipini kontrol et
                if message_data.get("type") == "command":
                    command = message_data.get("content")

                    if command == "start_listening":
                        # Dinleme modunu başlat
                        mode = ListeningMode.CONTINUOUS
                        if message_data.get("mode") == "wake_word":
                            mode = ListeningMode.WAKE_WORD

                        success = await voice_processor.start_listening(
                            mode=mode,
                            callback=on_speech_detected
                        )

                        # Durum mesajı
                        status_message = VoiceMessage(
                            type="status",
                            content="listening_started" if success else "listening_failed",
                            timestamp=datetime.now().isoformat(),
                            metadata={"mode": mode.name}
                        )

                        # WebSocket üzerinden gönder
                        await websocket.send_text(json.dumps(status_message.dict()))

                    elif command == "stop_listening":
                        # Dinleme modunu durdur
                        await voice_processor.stop_listening()

                        # Durum mesajı
                        status_message = VoiceMessage(
                            type="status",
                            content="listening_stopped",
                            timestamp=datetime.now().isoformat()
                        )

                        # WebSocket üzerinden gönder
                        await websocket.send_text(json.dumps(status_message.dict()))

                    elif command == "process_audio":
                        # Ses verisini işle
                        audio_base64 = message_data.get("audio_data")
                        if audio_base64:
                            # Base64'ten çöz
                            audio_data = base64.b64decode(audio_base64)

                            # Metne dönüştür
                            text = await voice_processor.speech_to_text(audio_data)

                            # Callback'i çağır
                            await on_speech_detected(text)

            except json.JSONDecodeError:
                logging.error("Geçersiz JSON verisi")

            except Exception as e:
                logging.error(f"WebSocket mesaj işleme hatası: {str(e)}")

    except WebSocketDisconnect:
        logging.info("WebSocket bağlantısı kapatıldı")

        # Dinleme modunu durdur
        await voice_processor.stop_listening()

    except Exception as e:
        logging.error(f"WebSocket hatası: {str(e)}")

        # Dinleme modunu durdur
        await voice_processor.stop_listening()
