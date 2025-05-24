"""
Z.E.K.A OpenAI API İstemcisi

Bu modül, OpenAI API ile doğrudan iletişim kurmak için kullanılır.
Sohbet tamamlama, streaming yanıtlar ve model yönetimi sağlar.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from core.logging_manager import get_logger


class OpenAIAPIError(Exception):
    """OpenAI API hataları için özel exception sınıfı"""
    pass


class OpenAIClient:
    """OpenAI API istemcisi.

    Bu sınıf, OpenAI API üzerinden GPT modellerine erişim sağlar.
    Sohbet tamamlama, streaming yanıtlar ve model yönetimi destekler.
    """

    # Desteklenen OpenAI modelleri
    SUPPORTED_MODELS = {
        "gpt-4": {
            "name": "GPT-4",
            "provider": "openai",
            "description": "En gelişmiş GPT modeli",
            "max_tokens": 8192,
            "supports_streaming": True
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "provider": "openai",
            "description": "Hızlı ve güçlü GPT-4 varyantı",
            "max_tokens": 128000,
            "supports_streaming": True
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "provider": "openai",
            "description": "Optimize edilmiş GPT-4 modeli",
            "max_tokens": 128000,
            "supports_streaming": True
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "provider": "openai",
            "description": "Hızlı ve ekonomik GPT-4o varyantı",
            "max_tokens": 128000,
            "supports_streaming": True
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "provider": "openai",
            "description": "Hızlı ve ekonomik model",
            "max_tokens": 16385,
            "supports_streaming": True
        }
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        timeout: float = 120.0,
        max_retries: int = 3,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        base_url: Optional[str] = None,
        provider_name: str = "openai"
    ):
        """OpenAI uyumlu API istemcisi başlatıcısı.

        Args:
            api_key: API anahtarı. None ise çevre değişkenlerinden alınır.
            default_model: Varsayılan model ID'si.
            timeout: İstek zaman aşımı (saniye).
            max_retries: Maksimum yeniden deneme sayısı.
            organization: OpenAI organizasyon ID'si (opsiyonel).
            project: OpenAI proje ID'si (opsiyonel).
            base_url: Özel API endpoint URL'si (opsiyonel).
            provider_name: Sağlayıcı adı (openai, ollama, localai, vb.).
        """
        # Loglama
        self.logger = get_logger("openai_client")

        # Sağlayıcı bilgileri
        self.provider_name = provider_name
        self.base_url = base_url

        # API anahtarı - sağlayıcıya göre farklı çevre değişkenleri kontrol et
        if not api_key:
            if provider_name == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider_name == "ollama":
                api_key = os.getenv("OLLAMA_API_KEY", "ollama")  # Ollama genelde API key gerektirmez
            elif provider_name == "localai":
                api_key = os.getenv("LOCALAI_API_KEY", "localai")
            elif provider_name == "groq":
                api_key = os.getenv("GROQ_API_KEY")
            elif provider_name == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            else:
                api_key = os.getenv(f"{provider_name.upper()}_API_KEY")

        self.api_key = api_key
        if not self.api_key:
            self.logger.error(f"{provider_name} API anahtarı bulunamadı")
            raise OpenAIAPIError(f"{provider_name} API anahtarı bulunamadı. İlgili çevre değişkenini ayarlayın.")

        # Konfigürasyon
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.organization = organization
        self.project = project

        # Base URL'yi belirle
        if not self.base_url:
            if provider_name == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif provider_name == "ollama":
                self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            elif provider_name == "localai":
                self.base_url = os.getenv("LOCALAI_BASE_URL", "http://localhost:8080/v1")
            elif provider_name == "groq":
                self.base_url = "https://api.groq.com/openai/v1"
            elif provider_name == "anthropic":
                self.base_url = "https://api.anthropic.com/v1"
            else:
                self.base_url = os.getenv(f"{provider_name.upper()}_BASE_URL", "http://localhost:8080/v1")

        # Model doğrulama - sadece OpenAI için katı kontrol
        if provider_name == "openai" and default_model not in self.SUPPORTED_MODELS:
            self.logger.warning(f"Desteklenmeyen OpenAI model: {default_model}. Varsayılan model kullanılacak.")
            self.default_model = "gpt-4o-mini"

        try:
            # Senkron OpenAI uyumlu istemcisi
            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "timeout": timeout,
                "max_retries": max_retries,
            }

            # OpenAI spesifik parametreler
            if provider_name == "openai":
                if organization:
                    client_kwargs["organization"] = organization
                if project:
                    client_kwargs["project"] = project

            self.client = OpenAI(**client_kwargs)

            # Asenkron OpenAI uyumlu istemcisi (streaming için)
            self.async_client = AsyncOpenAI(**client_kwargs)

            self.logger.info(f"{provider_name} istemcisi başlatıldı. Base URL: {self.base_url}, Model: {default_model}")
        except Exception as e:
            self.logger.error(f"{provider_name} istemcisi başlatılırken hata: {str(e)}", exc_info=True)
            raise OpenAIAPIError(f"{provider_name} istemcisi başlatılamadı: {str(e)}")

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Metin üretir.

        Args:
            prompt: Kullanıcı mesajı
            model: Kullanılacak model (opsiyonel)
            max_tokens: Maksimum token sayısı
            temperature: Yaratıcılık seviyesi (0.0-2.0)
            system_prompt: Sistem mesajı (opsiyonel)
            user_id: Kullanıcı ID'si (opsiyonel)

        Returns:
            Dict: Yanıt verisi
        """
        model = model or self.default_model

        # Mesajları hazırla
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                user=user_id
            )

            return {
                "response": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            self.logger.error(f"Metin üretme hatası: {str(e)}", exc_info=True)
            raise OpenAIAPIError(f"Metin üretilemedi: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming metin üretir.

        Args:
            prompt: Kullanıcı mesajı
            model: Kullanılacak model (opsiyonel)
            max_tokens: Maksimum token sayısı
            temperature: Yaratıcılık seviyesi (0.0-2.0)
            system_prompt: Sistem mesajı (opsiyonel)
            user_id: Kullanıcı ID'si (opsiyonel)

        Yields:
            Dict: Streaming yanıt parçası
        """
        model = model or self.default_model

        # Mesajları hazırla
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                user=user_id,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model": chunk.model,
                        "finish_reason": chunk.choices[0].finish_reason
                    }

        except Exception as e:
            self.logger.error(f"Streaming metin üretme hatası: {str(e)}", exc_info=True)
            raise OpenAIAPIError(f"Streaming metin üretilemedi: {str(e)}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sohbet tamamlama yapar.

        Args:
            messages: Sohbet mesajları listesi
            model: Kullanılacak model (opsiyonel)
            max_tokens: Maksimum token sayısı
            temperature: Yaratıcılık seviyesi (0.0-2.0)
            user_id: Kullanıcı ID'si (opsiyonel)

        Returns:
            Dict: Yanıt verisi
        """
        model = model or self.default_model

        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                user=user_id
            )

            return {
                "response": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            self.logger.error(f"Sohbet tamamlama hatası: {str(e)}", exc_info=True)
            raise OpenAIAPIError(f"Sohbet tamamlanamadı: {str(e)}")

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """Kullanılabilir modelleri listeler.

        Returns:
            List: Model listesi
        """
        try:
            models = []
            for model_id, model_info in self.SUPPORTED_MODELS.items():
                models.append({
                    "id": model_id,
                    "name": model_info["name"],
                    "provider": model_info["provider"],
                    "description": model_info.get("description", ""),
                    "max_tokens": model_info.get("max_tokens", 4096),
                    "supports_streaming": model_info.get("supports_streaming", True)
                })

            return models

        except Exception as e:
            self.logger.error(f"Model listesi alınırken hata: {str(e)}", exc_info=True)
            raise OpenAIAPIError(f"Model listesi alınamadı: {str(e)}")

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Belirli bir model hakkında bilgi getirir.

        Args:
            model_id: Model ID'si

        Returns:
            Dict: Model bilgisi veya None
        """
        return self.SUPPORTED_MODELS.get(model_id)

    def is_model_supported(self, model_id: str) -> bool:
        """Modelin desteklenip desteklenmediğini kontrol eder.

        Args:
            model_id: Model ID'si

        Returns:
            bool: Destekleniyorsa True
        """
        return model_id in self.SUPPORTED_MODELS
