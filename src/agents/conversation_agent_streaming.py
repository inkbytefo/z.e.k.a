"""
ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
Sohbet Ajanı Streaming Desteği
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from core.openrouter_client import OpenRouterClient
from agents.conversation_agent import ConversationAgent
from core.logging_manager import get_logger

class ConversationAgentStreaming(ConversationAgent):
    """Streaming desteği eklenmiş sohbet ajanı sınıfı."""

    def __init__(self, *args, **kwargs):
        """Streaming sohbet ajanı başlatıcısı."""
        super().__init__(*args, **kwargs)
        self.logger = get_logger("conversation_agent_streaming")

    async def process_task_streaming(
        self,
        task_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Bir görevi streaming modunda işler.

        Args:
            task_id: Görev ID'si
            description: Görev açıklaması
            metadata: Görev meta verileri

        Yields:
            str: Yanıt parçaları
        """
        # Performans ölçümü başlat
        start_time = datetime.now()
        self.metrics["total_interactions"] += 1
        self.metrics["last_interaction_time"] = start_time.isoformat()

        # Metadata'dan bilgileri çıkar
        action = metadata.get("action", "chat")
        language = metadata.get("language", self.current_language)
        style = metadata.get("style", self.current_style)
        user_id = metadata.get("user_id")

        # Dil ve stil ayarlarını güncelle (geçici olarak)
        temp_language = self.current_language
        temp_style = self.current_style

        if language in self.SUPPORTED_LANGUAGES:
            self.current_language = language

        if style in self.COMMUNICATION_STYLES:
            self.current_style = style

        try:
            # Model kontrolü
            if not self.is_initialized or not self.language_model:
                raise Exception("Dil modeli ayarlanmamış")

            # Kullanıcı tercihlerini ve belleği kontrol et
            preferences = {
                "language": self.current_language,
                "communication_style": self.current_style,
                "user_id": user_id
            }

            # Bellek yöneticisi varsa ilgili belleği getir
            relevant_memories = []
            if self.memory_access and description:
                try:
                    # Semantik arama yap
                    relevant_memories = await self.memory_access.retrieve(
                        query=description,
                        limit=5,
                        use_vector_search=True
                    )
                    self.logger.debug(f"{len(relevant_memories)} ilgili bellek öğesi bulundu")
                except Exception as e:
                    self.logger.warning(f"Bellek erişimi sırasında hata: {str(e)}")

            # İşlem türüne göre yönlendir
            if action == "chat":
                async for chunk in self._handle_chat_streaming(description, metadata, preferences):
                    yield chunk
            else:
                # Streaming desteklenmeyen işlemler için normal işlemi yap ve sonucu tek seferde döndür
                result = await self.process_task(task_id, description, metadata)
                yield result.get("response", "")

            # Sohbet geçmişini güncelle
            if action == "chat":
                # Kullanıcı mesajını ve asistan yanıtını kaydet
                self.conversation_history.append({
                    "user": description,
                    "assistant": "Streaming yanıt",  # Gerçek yanıt burada bilinmiyor
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "language": language,
                        "style": style,
                        "user_id": user_id
                    }
                })

                # Geçmiş boyutunu kontrol et
                if len(self.conversation_history) > self.max_history_length:
                    self.conversation_history = self.conversation_history[-self.max_history_length:]

        except Exception as e:
            # Hata durumunda
            self.logger.error(f"Streaming görev işleme hatası: {str(e)}", exc_info=True)
            yield f"İşlem sırasında bir hata oluştu: {str(e)}"

        finally:
            # Dil ve stil ayarlarını geri yükle
            self.current_language = temp_language
            self.current_style = temp_style

    async def _handle_chat_streaming(
        self,
        description: str,
        metadata: Dict[str, Any],  # pylint: disable=unused-argument
        preferences: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Sohbet isteğini streaming modunda işler.

        Args:
            description: Kullanıcı mesajı
            metadata: İstek meta verileri
            preferences: Kullanıcı tercihleri

        Yields:
            str: Yanıt parçaları
        """
        # Kullanıcı tercihlerini al
        communication_style = preferences.get("communication_style", self.current_style)
        language = preferences.get("language", self.current_language)
        user_id = preferences.get("user_id")

        # Sohbet geçmişini hazırla
        chat_history = []
        if len(self.conversation_history) > 0:
            # Son birkaç konuşmayı ekle
            history_limit = min(self.max_history_length, len(self.conversation_history))
            recent_history = self.conversation_history[-history_limit:]

            for entry in recent_history:
                chat_history.append({
                    "user": entry["user"],
                    "assistant": entry["assistant"],
                    "timestamp": entry["timestamp"]
                })

        # Sistem promptunu hazırla
        system_prompt = self._get_system_prompt(language, communication_style)

        try:
            # OpenRouter istemcisi mi kontrol et
            if hasattr(self.language_model, "generate_stream"):
                # OpenRouter API ile streaming yanıt oluştur (daha düşük sıcaklık değeri)
                async for chunk in self.language_model.generate_stream(
                    prompt=description,
                    system_prompt=system_prompt,
                    temperature=0.3,  # Daha düşük sıcaklık değeri (0.7 -> 0.3)
                    max_tokens=1000,
                    user_id=user_id
                ):
                    if "content" in chunk:
                        yield chunk["content"]
            else:
                # Streaming desteklenmeyen model için normal yanıt oluştur
                response = await self._generate_response(description, preferences, [])
                yield response.get("response", "")

        except Exception as e:
            self.logger.error(f"Streaming sohbet hatası: {str(e)}", exc_info=True)
            yield f"Yanıt oluşturulurken bir hata oluştu: {str(e)}"
