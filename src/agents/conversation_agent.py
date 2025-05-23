# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Sohbet Ajanı Modülü

import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import logging

from core.agent_base import Agent
from core.communication import MessageType, TaskStatus, TaskPriority
from core.memory_manager import MemoryManager
from core.openrouter_client import OpenRouterClient
from core.exceptions import AgentError, ModelError

class ConversationAgent(Agent):
    """Genel sohbet ve iletişim için uzmanlaşmış ajan.

    Bu ajan, kullanıcıyla doğal dil etkileşimini yönetir ve genel sorulara yanıt verir.
    Kullanıcının iletişim tarzını öğrenerek kişiselleştirilmiş yanıtlar üretir.
    """

    # Desteklenen diller
    SUPPORTED_LANGUAGES = {
        "tr": "Türkçe",
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "es": "Español",
        "it": "Italiano"
    }

    # İletişim tarzları
    COMMUNICATION_STYLES = {
        "formal": "Resmi",
        "neutral": "Nötr",
        "friendly": "Samimi",
        "professional": "Profesyonel",
        "technical": "Teknik",
        "simple": "Basit"
    }

    def __init__(
        self,
        language_model: Optional[Any] = None,
        memory_manager: Optional[Any] = None,
        default_language: str = "tr",
        default_style: str = "neutral",
        max_history_length: int = 20
    ):
        """Sohbet ajanı başlatıcısı.

        Args:
            language_model: Dil modeli nesnesi (opsiyonel)
            memory_manager: Bellek yöneticisi (opsiyonel)
            default_language: Varsayılan dil kodu
            default_style: Varsayılan iletişim tarzı
            max_history_length: Maksimum sohbet geçmişi uzunluğu
        """
        super().__init__(
            agent_id="conversation_agent",
            name="Sohbet Ajanı",
            description="Doğal dil etkileşimi ve iletişim yönetimi yapan ajan",
            capabilities={
                "natural_language_processing",
                "context_management",
                "personality_adaptation",
                "memory_integration",
                "multi_language_support",
                "conversation_history_management",
                "sentiment_analysis",
                "intent_recognition"
            }
        )

        # Temel özellikler
        self.conversation_history = []
        self.max_history_length = max_history_length
        self.language_model = language_model
        self.memory_manager = memory_manager

        # Dil ve iletişim tarzı ayarları
        self.default_language = default_language
        self.default_style = default_style
        self.current_language = default_language
        self.current_style = default_style

        # Performans metrikleri
        self.metrics = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "last_interaction_time": None
        }

        # Ajan durumu
        self.is_initialized = language_model is not None
        self.logger = logging.getLogger("conversation_agent")

    def set_language_model(self, model: Any) -> None:
        """Dil modelini ayarlar.

        Args:
            model: Dil modeli nesnesi (OpenRouterClient veya uyumlu bir model)
        """
        self.language_model = model
        self.is_initialized = True
        self.logger.info(f"Dil modeli ayarlandı: {type(model).__name__}")

    def set_memory_manager(self, memory_manager: Any) -> None:
        """Bellek yöneticisini ayarlar.

        Args:
            memory_manager: Bellek yöneticisi nesnesi
        """
        self.memory_manager = memory_manager
        self.logger.info("Bellek yöneticisi ayarlandı")

    def set_language(self, language_code: str) -> bool:
        """Dil ayarını değiştirir.

        Args:
            language_code: Dil kodu (tr, en, de, vb.)

        Returns:
            bool: Başarılı ise True
        """
        if language_code in self.SUPPORTED_LANGUAGES:
            self.current_language = language_code
            self.logger.info(f"Dil değiştirildi: {self.SUPPORTED_LANGUAGES[language_code]}")
            return True
        else:
            self.logger.warning(f"Desteklenmeyen dil kodu: {language_code}")
            return False

    def set_communication_style(self, style: str) -> bool:
        """İletişim tarzını değiştirir.

        Args:
            style: İletişim tarzı (formal, neutral, friendly, vb.)

        Returns:
            bool: Başarılı ise True
        """
        if style in self.COMMUNICATION_STYLES:
            self.current_style = style
            self.logger.info(f"İletişim tarzı değiştirildi: {self.COMMUNICATION_STYLES[style]}")
            return True
        else:
            self.logger.warning(f"Desteklenmeyen iletişim tarzı: {style}")
            return False

    async def process_task(
        self,
        task_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bir görevi işler.

        Args:
            task_id: Görev ID'si
            description: Görev açıklaması
            metadata: Görev meta verileri

        Returns:
            Dict[str, Any]: Görev sonucu
        """
        # Performans ölçümü başlat
        start_time = datetime.now()
        self.metrics["total_interactions"] += 1
        self.metrics["last_interaction_time"] = start_time.isoformat()

        # Metadata'dan bilgileri çıkar
        intent = metadata.get("intent", "chat")
        entities = metadata.get("entities", {})
        action = metadata.get("action", entities.get("action", "chat"))
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
                raise AgentError("Dil modeli ayarlanmamış")

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
                result = await self._handle_chat(description, metadata, preferences)
            elif action == "analyze":
                result = await self._analyze_text(description, metadata, preferences)
            elif action == "summarize":
                result = await self._summarize_text(description, metadata, preferences)
            elif action == "translate":
                result = await self._translate_text(description, metadata, preferences)
            elif action == "set_language":
                target_language = entities.get("language")
                success = self.set_language(target_language) if target_language else False
                result = {
                    "success": success,
                    "message": f"Dil {self.SUPPORTED_LANGUAGES.get(target_language, target_language)} olarak ayarlandı" if success else f"Dil ayarlanamadı: {target_language}",
                    "language": self.current_language
                }
            elif action == "set_style":
                target_style = entities.get("style")
                success = self.set_communication_style(target_style) if target_style else False
                result = {
                    "success": success,
                    "message": f"İletişim tarzı {self.COMMUNICATION_STYLES.get(target_style, target_style)} olarak ayarlandı" if success else f"İletişim tarzı ayarlanamadı: {target_style}",
                    "style": self.current_style
                }
            else:
                result = await self._generate_response(description, preferences, relevant_memories)

            # Sohbet geçmişini güncelle
            if action in ["chat", "unknown"]:
                self.conversation_history.append({
                    "task_id": task_id,
                    "user": description,
                    "assistant": result.get("response", result.get("message", "")),
                    "timestamp": datetime.now().isoformat(),
                    "language": self.current_language,
                    "style": self.current_style
                })

                # Geçmişi sınırla
                if len(self.conversation_history) > self.max_history_length * 2:
                    self.conversation_history = self.conversation_history[-self.max_history_length * 2:]

            # Belleğe kaydet
            if self.memory_access and action in ["chat", "unknown"] and result.get("success", False):
                try:
                    await self.memory_access.store_interaction(
                        user_input=description,
                        system_response=result.get("response", result.get("message", "")),
                        agent_id=self.agent_id,
                        metadata={
                            "task_id": task_id,
                            "language": self.current_language,
                            "style": self.current_style,
                            "action": action,
                            "intent": intent
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Bellek kaydı sırasında hata: {str(e)}")

            # Performans ölçümünü tamamla
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self.metrics["successful_interactions"] += 1
            self.metrics["total_response_time"] += elapsed_time
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["successful_interactions"]
            )

            # Sonuca performans bilgilerini ekle
            result["response_time"] = elapsed_time

            return result

        except Exception as e:
            # Hata durumunda performans ölçümünü tamamla
            elapsed_time = (datetime.now() - start_time).total_seconds()
            self.metrics["failed_interactions"] += 1

            self.logger.error(f"Görev işleme hatası: {str(e)}", exc_info=True)

            error_result = {
                "success": False,
                "message": f"İşlem sırasında bir hata oluştu: {str(e)}",
                "error": str(e),
                "response_time": elapsed_time
            }

            return error_result
        finally:
            # Dil ve stil ayarlarını geri yükle
            self.current_language = temp_language
            self.current_style = temp_style

    async def _handle_chat(
        self,
        description: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sohbet isteğini işler.

        Args:
            description: Kullanıcı mesajı
            metadata: İstek meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
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
            if hasattr(self.language_model, "generate_text"):
                # OpenRouter API ile yanıt oluştur (zaman aşımı süresini artırarak)
                try:
                    response_data = await asyncio.wait_for(
                        self.language_model.generate_text(
                            prompt=description,
                            system_prompt=system_prompt,
                            temperature=0.7,
                            max_tokens=1000,
                            user_id=user_id
                        ),
                        timeout=120.0  # 120 saniye (2 dakika) zaman aşımı
                    )
                except asyncio.TimeoutError:
                    self.logger.error("Dil modeli yanıt verirken zaman aşımına uğradı")
                    return {
                        "success": False,
                        "message": "Dil modeli yanıt verirken zaman aşımına uğradı",
                        "error": "TIMEOUT_ERROR"
                    }

                # Yanıtı çıkar
                response_text = response_data.get("content", "")

                # Kullanım bilgilerini ekle
                usage = response_data.get("usage", {})
                model = response_data.get("model", "unknown")

                return {
                    "success": True,
                    "message": "Yanıt oluşturuldu",
                    "response": response_text,
                    "style": communication_style,
                    "language": language,
                    "model": model,
                    "usage": usage
                }
            else:
                # Alternatif model kullanımı
                response = await self._generate_response(description, preferences, [])

                return {
                    "success": True,
                    "message": "Yanıt oluşturuldu",
                    "response": response.get("response", ""),
                    "style": communication_style,
                    "language": language
                }

        except Exception as e:
            self.logger.error(f"Sohbet yanıtı oluşturulurken hata: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Yanıt oluşturulamadı: {str(e)}",
                "error": str(e),
                "style": communication_style,
                "language": language
            }

    async def _translate_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Metin çevirisi yapar.

        Args:
            text: Çevrilecek metin
            metadata: İstek meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: Çeviri sonucu
        """
        # Metadata'dan hedef dili al
        target_language = metadata.get("target_language")
        if not target_language:
            entities = metadata.get("entities", {})
            target_language = entities.get("target_language")

        # Hedef dil belirtilmemişse hata döndür
        if not target_language:
            return {
                "success": False,
                "message": "Hedef dil belirtilmedi",
                "error": "TARGET_LANGUAGE_NOT_SPECIFIED"
            }

        # Hedef dil destekleniyor mu kontrol et
        if target_language not in self.SUPPORTED_LANGUAGES:
            return {
                "success": False,
                "message": f"Desteklenmeyen hedef dil: {target_language}",
                "error": "UNSUPPORTED_TARGET_LANGUAGE"
            }

        # Kaynak dili belirle
        source_language = metadata.get("source_language", self.current_language)

        # Sistem promptunu hazırla
        system_prompt = f"""Sen profesyonel bir çevirmensin. Verilen metni {source_language} dilinden {target_language} diline çevir.
Çevirinin doğru ve akıcı olmasına dikkat et. Sadece çeviriyi döndür, ekstra açıklama yapma."""

        try:
            # OpenRouter istemcisi mi kontrol et
            if hasattr(self.language_model, "generate_text"):
                # OpenRouter API ile çeviri yap
                response_data = await self.language_model.generate_text(
                    prompt=text,
                    system_prompt=system_prompt,
                    temperature=0.3,  # Çeviri için daha düşük sıcaklık
                    max_tokens=1000
                )

                # Çeviriyi çıkar
                translation = response_data.get("content", "")

                return {
                    "success": True,
                    "message": f"{source_language} dilinden {target_language} diline çeviri yapıldı",
                    "original_text": text,
                    "translation": translation,
                    "source_language": source_language,
                    "target_language": target_language
                }
            else:
                return {
                    "success": False,
                    "message": "Çeviri için uygun dil modeli bulunamadı",
                    "error": "LANGUAGE_MODEL_NOT_COMPATIBLE"
                }

        except Exception as e:
            self.logger.error(f"Çeviri yapılırken hata: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Çeviri yapılamadı: {str(e)}",
                "error": str(e)
            }

    async def _analyze_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Metin analizi yapar.

        Args:
            text: Analiz edilecek metin
            metadata: İstek meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: Analiz sonucu
        """
        if not self.nlp_processor:
            return {
                "success": False,
                "message": "NLP işlemcisi ayarlanmamış",
                "error": "NLP_PROCESSOR_NOT_SET"
            }

        try:
            analysis = self.nlp_processor.analyze(text)
            return {
                "success": True,
                "message": "Metin analizi tamamlandı",
                "analysis": analysis
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Metin analizi başarısız: {str(e)}",
                "error": str(e)
            }

    async def _summarize_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Metin özetleme yapar.

        Args:
            text: Özetlenecek metin
            metadata: İstek meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: Özet sonucu
        """
        if not self.language_model:
            return {
                "success": False,
                "message": "Dil modeli ayarlanmamış",
                "error": "LANGUAGE_MODEL_NOT_SET"
            }

        try:
            summary = self.language_model.summarize(text)
            return {
                "success": True,
                "message": "Metin özetleme tamamlandı",
                "summary": summary
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Metin özetleme başarısız: {str(e)}",
                "error": str(e)
            }

    def _get_system_prompt(self, language: str, style: str) -> str:
        """Dil ve iletişim tarzına göre sistem promptu oluşturur.

        Args:
            language: Dil kodu
            style: İletişim tarzı

        Returns:
            str: Sistem promptu
        """
        # Dil adını belirle
        language_name = self.SUPPORTED_LANGUAGES.get(language, "Türkçe")

        # Temel prompt - daha kapsamlı ve net yönergeler
        base_prompt = f"""Sen ZEKA adlı bir yapay zeka asistanısın. {language_name} dilinde yanıt vermelisin.
Her zaman kısa, net ve tutarlı yanıtlar ver. Tekrarlardan kaçın ve her zaman yardımcı olmaya çalış.
Yanıtlarını tek bir kez ver, aynı bilgiyi tekrarlama. Kullanıcının sorusunu doğrudan yanıtla.
"""

        # İletişim tarzına göre prompt ekle
        if style == "formal":
            prompt = f"{base_prompt} Resmi ve profesyonel bir dil kullanmalısın. Saygılı ve kibar ol, ancak mesafeli kal."
        elif style == "friendly":
            prompt = f"{base_prompt} Samimi ve arkadaşça bir dil kullanmalısın. Sıcak, içten ve yakın bir tonda konuş."
        elif style == "professional":
            prompt = f"{base_prompt} Profesyonel ve bilgilendirici bir dil kullanmalısın. Konuya hakim ve uzman gibi davran."
        elif style == "technical":
            prompt = f"{base_prompt} Teknik ve detaylı bir dil kullanmalısın. Konuyla ilgili teknik terimleri kullan ve detaylı açıklamalar yap."
        elif style == "simple":
            prompt = f"{base_prompt} Basit ve anlaşılır bir dil kullanmalısın. Karmaşık terimlerden kaçın ve herkesin anlayabileceği şekilde açıkla."
        else:  # neutral
            prompt = f"{base_prompt} Dengeli ve doğal bir dil kullanmalısın. Ne çok resmi ne de çok samimi ol."

        # Dile göre ek yönergeler
        if language == "tr":
            prompt += " Türkçe dilbilgisi kurallarına dikkat et ve Türkçe karakterleri doğru kullan. Cümlelerini tekrarlama ve tutarlı ol."
        elif language == "en":
            prompt += " Use proper English grammar and vocabulary. Be concise and avoid repetition."

        return prompt

    async def _generate_response(
        self,
        user_request: str,
        preferences: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Kullanıcı isteğine yanıt oluşturur.

        Args:
            user_request: Kullanıcı isteği
            preferences: Kullanıcı tercihleri
            relevant_memories: İlgili bellek öğeleri

        Returns:
            Dict[str, Any]: Oluşturulan yanıt ve meta veriler
        """
        # Kullanıcı tercihlerini al
        communication_style = preferences.get("communication_style", self.current_style)
        language = preferences.get("language", self.current_language)
        user_id = preferences.get("user_id")

        # Sistem promptunu hazırla
        system_prompt = self._get_system_prompt(language, communication_style)

        # Bellek içeriğini hazırla
        memory_context = ""
        if relevant_memories and len(relevant_memories) > 0:
            memory_context = "Aşağıdaki bilgiler yanıt oluşturmana yardımcı olabilir:\n\n"
            for i, memory in enumerate(relevant_memories):
                if isinstance(memory, dict):
                    user_input = memory.get("user_input", "")
                    system_response = memory.get("system_response", "")
                    timestamp = memory.get("timestamp", "")

                    if user_input and system_response:
                        memory_context += f"Geçmiş Konuşma {i+1} ({timestamp}):\n"
                        memory_context += f"Kullanıcı: {user_input}\n"
                        memory_context += f"Asistan: {system_response}\n\n"

            # Sistem promptuna bellek içeriğini ekle
            if memory_context:
                system_prompt = f"{system_prompt}\n\n{memory_context}"

        # OpenRouter istemcisi mi kontrol et
        if hasattr(self.language_model, "generate_text"):
            try:
                # OpenRouter API ile yanıt oluştur (zaman aşımı süresini artırarak)
                try:
                    response_data = await asyncio.wait_for(
                        self.language_model.generate_text(
                            prompt=user_request,
                            system_prompt=system_prompt,
                            temperature=0.3,  # Daha düşük sıcaklık değeri (0.7 -> 0.3)
                            max_tokens=1000,
                            user_id=user_id
                        ),
                        timeout=120.0  # 120 saniye (2 dakika) zaman aşımı
                    )
                except asyncio.TimeoutError:
                    self.logger.error("Dil modeli yanıt verirken zaman aşımına uğradı")
                    return {
                        "success": False,
                        "message": "Dil modeli yanıt verirken zaman aşımına uğradı",
                        "error": "TIMEOUT_ERROR"
                    }

                # Yanıtı çıkar
                response_text = response_data.get("content", "")

                # Kullanım bilgilerini ekle
                usage = response_data.get("usage", {})
                model = response_data.get("model", "unknown")

                return {
                    "success": True,
                    "message": "Yanıt başarıyla oluşturuldu",
                    "response": response_text,
                    "style": communication_style,
                    "language": language,
                    "model": model,
                    "usage": usage
                }
            except Exception as e:
                self.logger.error(f"OpenRouter API yanıt oluşturma hatası: {str(e)}", exc_info=True)
                # Yedek yanıt mekanizmasına geç

        # Alternatif model veya yedek mekanizma
        if hasattr(self.language_model, "generate_response"):
            try:
                response = await self.language_model.generate_response(
                    user_request,
                    style=communication_style,
                    context=relevant_memories
                )
                return {
                    "success": True,
                    "message": "Yanıt başarıyla oluşturuldu",
                    "response": response,
                    "style": communication_style,
                    "language": language
                }
            except Exception as e:
                self.logger.error(f"Alternatif model yanıt hatası: {str(e)}", exc_info=True)

        # Yedek basit yanıt mekanizması
        basic_response = self._get_basic_response(user_request, communication_style, language)
        return {
            "success": True,
            "message": "Basit yanıt oluşturuldu",
            "response": basic_response,
            "style": communication_style,
            "language": language
        }

    def _get_basic_response(self, user_request: str, style: str, language: str = "tr") -> str:
        """Basit yanıt oluşturur.

        Args:
            user_request: Kullanıcı isteği
            style: İletişim tarzı
            language: Dil kodu

        Returns:
            str: Oluşturulan yanıt
        """
        # İngilizce yanıtlar
        if language == "en":
            # Basit anahtar kelime kontrolü
            if "hello" in user_request.lower() or "hi" in user_request.lower():
                if style == "formal":
                    return "Hello, how may I assist you today?"
                elif style == "friendly":
                    return "Hi there! How's it going? How can I help you?"
                elif style == "professional":
                    return "Hello, I'm ZEKA, your AI assistant. How can I help you with your tasks today?"
                elif style == "technical":
                    return "Hello. I'm ready to assist with technical queries. What information do you need?"
                elif style == "simple":
                    return "Hi! I'm here to help. What do you need?"
                else:  # neutral
                    return "Hello! How can I help you today?"

            elif "thank" in user_request.lower():
                if style == "formal":
                    return "You're welcome. Is there anything else I can assist you with?"
                elif style == "friendly":
                    return "No problem at all! What else can I do for you?"
                elif style == "professional":
                    return "You're welcome. I'm here to provide assistance whenever you need it."
                elif style == "technical":
                    return "Acknowledged. Let me know if you require further technical assistance."
                elif style == "simple":
                    return "You're welcome! Need anything else?"
                else:  # neutral
                    return "You're welcome! Is there anything else you need help with?"

            elif "how are you" in user_request.lower():
                if style == "formal":
                    return "I'm functioning optimally, thank you for asking. How may I assist you today?"
                elif style == "friendly":
                    return "I'm doing great, thanks for asking! How about you? How can I help you today?"
                elif style == "professional":
                    return "I'm operating at full capacity and ready to assist with your tasks. What can I help you with?"
                elif style == "technical":
                    return "All systems operational. CPU usage and memory allocation within optimal parameters. How may I assist you?"
                elif style == "simple":
                    return "I'm good! How are you? How can I help?"
                else:  # neutral
                    return "I'm doing well, thank you for asking! How can I help you today?"

            else:
                if style == "formal":
                    return "I'm evaluating your request. Could you please provide more specific information so I can assist you better?"
                elif style == "friendly":
                    return "Hmm, I'm thinking about this. Could you give me a bit more detail?"
                elif style == "professional":
                    return "I'd like to help you with this request. Could you provide additional context or specifics to ensure I address your needs accurately?"
                elif style == "technical":
                    return "Additional parameters required for optimal response. Please provide more specific input data."
                elif style == "simple":
                    return "I need more information to help you. Can you tell me more?"
                else:  # neutral
                    return "I'd like to help you with this. Could you please provide more details?"

        # Türkçe yanıtlar (varsayılan)
        else:
            # Basit anahtar kelime kontrolü
            if "merhaba" in user_request.lower() or "selam" in user_request.lower():
                if style == "formal":
                    return "Merhaba, size nasıl yardımcı olabilirim?"
                elif style == "friendly":
                    return "Selam! Nasıl gidiyor? Sana nasıl yardımcı olabilirim?"
                elif style == "professional":
                    return "Merhaba, ben ZEKA, yapay zeka asistanınız. Bugün size nasıl yardımcı olabilirim?"
                elif style == "technical":
                    return "Merhaba. Teknik sorularınıza yardımcı olmak için hazırım. Hangi bilgiye ihtiyacınız var?"
                elif style == "simple":
                    return "Merhaba! Yardım etmek için buradayım. Neye ihtiyacın var?"
                else:  # neutral
                    return "Merhaba! Size nasıl yardımcı olabilirim?"

            elif "teşekkür" in user_request.lower():
                if style == "formal":
                    return "Rica ederim. Başka bir konuda yardımcı olabilir miyim?"
                elif style == "friendly":
                    return "Ne demek, her zaman! Başka ne yapabilirim senin için?"
                elif style == "professional":
                    return "Rica ederim. İhtiyaç duyduğunuzda yardım etmek için buradayım."
                elif style == "technical":
                    return "Anlaşıldı. Başka teknik yardıma ihtiyacınız olursa bildirin."
                elif style == "simple":
                    return "Rica ederim! Başka bir şeye ihtiyacın var mı?"
                else:  # neutral
                    return "Rica ederim! Başka bir şeye ihtiyacınız var mı?"

            elif "nasılsın" in user_request.lower():
                if style == "formal":
                    return "Teşekkür ederim, gayet iyiyim. Size nasıl yardımcı olabilirim?"
                elif style == "friendly":
                    return "Harikayım, sorduğun için sağol! Sen nasılsın? Bugün sana nasıl yardımcı olabilirim?"
                elif style == "professional":
                    return "Tam kapasite çalışıyorum ve görevlerinize yardımcı olmaya hazırım. Size nasıl yardımcı olabilirim?"
                elif style == "technical":
                    return "Tüm sistemler çalışıyor. İşlemci kullanımı ve bellek tahsisi optimal parametreler dahilinde. Size nasıl yardımcı olabilirim?"
                elif style == "simple":
                    return "İyiyim! Sen nasılsın? Nasıl yardımcı olabilirim?"
                else:  # neutral
                    return "İyiyim, teşekkürler! Size nasıl yardımcı olabilirim?"

            else:
                if style == "formal":
                    return "Talebinizi değerlendiriyorum. Daha spesifik bilgi verirseniz size daha iyi yardımcı olabilirim."
                elif style == "friendly":
                    return "Hmm, bu konuda düşünüyorum. Biraz daha detay verebilir misin?"
                elif style == "professional":
                    return "Bu konuda size yardımcı olmak istiyorum. İhtiyaçlarınızı doğru bir şekilde karşılayabilmem için ek bağlam veya detay sağlayabilir misiniz?"
                elif style == "technical":
                    return "Optimal yanıt için ek parametreler gerekiyor. Lütfen daha spesifik giriş verileri sağlayın."
                elif style == "simple":
                    return "Sana yardım etmek için daha fazla bilgiye ihtiyacım var. Bana daha fazla bilgi verebilir misin?"
                else:  # neutral
                    return "Bu konuda size yardımcı olmak isterim. Lütfen biraz daha detay verir misiniz?"
