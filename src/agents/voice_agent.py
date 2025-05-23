# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ses Ajanı Modülü

from typing import Dict, Any, Optional
from core.agent_base import Agent
from core.voice_processor import VoiceProcessor
from core.voice_profile import VoiceProfile

class VoiceCommand:
    """Ses komutları için veri sınıfı."""

    def __init__(
        self,
        command: str,
        description: str,
        handler: callable,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.command = command
        self.description = description
        self.handler = handler
        self.metadata = metadata or {}
        self.usage_count = 0

class VoiceAgent(Agent):
    """Ses işleme ve yönetimi için ajan sınıfı."""

    def __init__(self, config: Dict[str, Any]):
        """VoiceAgent başlatıcısı.

        Args:
            config: Yapılandırma ayarları
        """
        super().__init__(
            agent_id="voice_agent",
            name="Ses Asistanı",
            description="Ses komutları ve ses işleme yetenekleri için ajan",
            capabilities={"STT", "TTS", "VOICE_COMMANDS"}
        )

        self.config = config
        self.voice_processor = VoiceProcessor(config)
        self.voice_profile = None
        self.command_registry: Dict[str, VoiceCommand] = {}
        self.default_language = config.get("default_language", "tr")

    def update_voice_profile(self, profile: VoiceProfile) -> None:
        """Ses profilini günceller.

        Args:
            profile: Yeni ses profili
        """
        self.voice_profile = profile
        self.voice_processor.update_profile(profile)

    def register_command(
        self,
        command: str,
        description: str,
        handler: callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Yeni bir ses komutu kaydeder.

        Args:
            command: Komut metni
            description: Komut açıklaması
            handler: Komut işleyici fonksiyon
            metadata: Ek meta veriler
        """
        self.command_registry[command] = VoiceCommand(
            command=command,
            description=description,
            handler=handler,
            metadata=metadata
        )

    def find_matching_command(self, text: str) -> Optional[VoiceCommand]:
        """Metin içinde eşleşen komutu bulur.

        Args:
            text: Aranacak metin

        Returns:
            Optional[VoiceCommand]: Eşleşen komut veya None
        """
        normalized_text = text.lower().strip()

        # Tam eşleşme kontrolü
        if normalized_text in self.command_registry:
            return self.command_registry[normalized_text]

        # Bulanık eşleşme kontrolü
        for command in self.command_registry.values():
            if command.command.lower() in normalized_text:
                return command

        return None

    async def process_task(
        self,
        task_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verilen görevi işler.

        Args:
            task_id: Görev ID'si
            description: Görev açıklaması
            metadata: Görev meta verileri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        try:
            task_type = metadata.get("type", "speech_to_text")

            if task_type == "speech_to_text":
                audio_data = metadata.get("audio_data")
                if not audio_data:
                    raise ValueError("Ses verisi bulunamadı")

                # Ses verisini metne dönüştür
                text = await self.voice_processor.speech_to_text(audio_data)

                # Komut kontrolü
                command = self.find_matching_command(text)
                if command:
                    command.usage_count += 1
                    result = await command.handler(text, metadata)
                    return {
                        "task_id": task_id,
                        "status": "success",
                        "text": text,
                        "command": command.command,
                        "result": result
                    }

                return {
                    "task_id": task_id,
                    "status": "success",
                    "text": text
                }

            elif task_type == "text_to_speech":
                text = metadata.get("text")
                if not text:
                    raise ValueError("Metin bulunamadı")

                # Metni sese dönüştür
                audio_data = await self.voice_processor.text_to_speech(
                    text,
                    chunk_size=metadata.get("chunk_size")
                )

                return {
                    "task_id": task_id,
                    "status": "success",
                    "audio_data": audio_data
                }

            else:
                raise ValueError(f"Desteklenmeyen görev tipi: {task_type}")

        except Exception as e:
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    async def process_command(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Komut metnini işler.

        Args:
            text: Komut metni
            metadata: Ek meta veriler

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        command = self.find_matching_command(text)
        if not command:
            return {
                "status": "error",
                "error": "Komut bulunamadı",
                "text": text
            }

        try:
            command.usage_count += 1
            result = await command.handler(text, metadata or {})

            return {
                "status": "success",
                "command": command.command,
                "result": result,
                "text": text
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "command": command.command,
                "text": text
            }

    def get_command_stats(self) -> Dict[str, Any]:
        """Komut kullanım istatistiklerini döndürür.

        Returns:
            Dict[str, Any]: İstatistikler
        """
        total_usage = sum(cmd.usage_count for cmd in self.command_registry.values())

        return {
            "total_commands": len(self.command_registry),
            "total_usage": total_usage,
            "commands": [
                {
                    "command": cmd.command,
                    "description": cmd.description,
                    "usage_count": cmd.usage_count,
                    "usage_percentage": cmd.usage_count / total_usage * 100 if total_usage > 0 else 0
                }
                for cmd in sorted(
                    self.command_registry.values(),
                    key=lambda x: x.usage_count,
                    reverse=True
                )
            ]
        }
