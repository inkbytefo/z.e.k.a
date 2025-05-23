#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenRouter API Test Betiği (Bağımsız)
Bu betik, OpenRouter API istemcisini doğrudan test etmek için kullanılır.
"""

import os
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from dotenv import load_dotenv

# OpenAI SDK kullan
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionChunk, ChatCompletion

# Çevre değişkenlerini yükle
load_dotenv()

class OpenRouterAPIError(Exception):
    """OpenRouter API istekleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "OpenRouter API isteği sırasında bir hata oluştu", code: str = "OPENROUTER_API_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code}] {self.message}"

class OpenRouterClient:
    """OpenRouter API istemcisi.

    Bu sınıf, OpenRouter API üzerinden çeşitli dil modellerine erişim sağlar.
    Claude, Llama, Mistral ve Cohere gibi modelleri destekler.
    """

    # Model sağlayıcıları
    PROVIDERS = {
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2"],
        "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        "google": ["gemini-pro", "gemini-1.5-pro"],
        "meta": ["llama-3", "llama-2"],
        "mistral": ["mistral-large", "mistral-medium", "mistral-small"],
        "cohere": ["command", "command-r", "command-r-plus"],
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "anthropic/claude-3-opus",
        site_url: str = "https://zeka-assistant.com",
        site_name: str = "ZEKA Assistant",
        timeout: float = 120.0,
        max_retries: int = 5,
        retry_delay: float = 2.0,
        api_base: Optional[str] = None
    ):
        """OpenRouter istemcisi başlatıcısı."""
        # API anahtarı
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            print("OpenRouter API anahtarı bulunamadı")
            raise OpenRouterAPIError("OpenRouter API anahtarı bulunamadı")

        # Yapılandırma
        self.default_model = default_model
        self.site_url = site_url
        self.site_name = site_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.api_base = api_base or "https://openrouter.ai/api/v1"

        # Model önbelleği
        self.models_cache = {}
        self.models_cache_time = 0
        self.models_cache_ttl = 3600  # 1 saat

        # İstek metrikleri
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "last_request_time": None,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }

        try:
            # Senkron OpenAI istemcisi
            self.client = OpenAI(
                base_url=self.api_base,
                api_key=self.api_key,
                timeout=timeout,
                max_retries=max_retries,
                default_headers={
                    "HTTP-Referer": site_url,
                    "X-Title": site_name
                }
            )
            
            # Asenkron OpenAI istemcisi (streaming için)
            self.async_client = AsyncOpenAI(
                base_url=self.api_base,
                api_key=self.api_key,
                timeout=timeout,
                max_retries=max_retries,
                default_headers={
                    "HTTP-Referer": site_url,
                    "X-Title": site_name
                }
            )
            
            print("OpenAI SDK kullanılıyor")
            print(f"OpenRouter istemcisi başlatıldı. Varsayılan model: {default_model}")
        except Exception as e:
            print(f"OpenRouter istemcisi başlatılırken hata: {str(e)}")
            raise OpenRouterAPIError(f"OpenRouter istemcisi başlatılamadı: {str(e)}")

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Yeniden deneme mekanizması ile fonksiyon çağırır."""
        max_retries = self.max_retries
        retry_delay = self.retry_delay

        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    print(f"Maksimum yeniden deneme sayısına ulaşıldı: {str(e)}")
                    raise

                # Hata türüne göre yeniden deneme kararı
                if "rate_limit" in str(e).lower() or "timeout" in str(e).lower() or "503" in str(e):
                    wait_time = retry_delay * (2 ** attempt)  # Üstel geri çekilme
                    print(f"API hatası, {wait_time:.2f} saniye sonra yeniden deneniyor: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    # Diğer hata türleri için yeniden deneme yapma
                    print(f"Yeniden denenemeyen hata: {str(e)}")
                    raise

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """OpenRouter API üzerinden metin üretir."""
        start_time = time.time()
        self.metrics["total_requests"] += 1
        self.metrics["last_request_time"] = datetime.now().isoformat()

        try:
            # Mesajları oluştur
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # İstek parametreleri
            params = {
                "model": model or self.default_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            # Opsiyonel parametreler
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            if response_format:
                params["response_format"] = response_format

            if user_id:
                params["user"] = user_id

            # İstek gönder (yeniden deneme mekanizması ile)
            async def _make_request():
                # Asenkron OpenAI istemcisi kullan
                return await self.async_client.chat.completions.create(**params)

            print(f"OpenRouter API isteği gönderiliyor: {model or self.default_model}")
            response = await self._retry_with_backoff(_make_request)

            # Metrikleri güncelle
            elapsed_time = time.time() - start_time
            self.metrics["successful_requests"] += 1
            self.metrics["total_response_time"] += elapsed_time
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["successful_requests"]
            )

            # Token kullanımını ve maliyeti güncelle
            if hasattr(response, "usage") and response.usage:
                self.metrics["total_tokens"] += response.usage.total_tokens

                # Maliyet hesaplama (OpenRouter API'den dönen fiyatlandırma bilgisine göre)
                if hasattr(response, "cost") and response.cost:
                    self.metrics["total_cost"] += response.cost

            # Yanıtı hazırla
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "created": response.created,
                "response_time": elapsed_time,
                "finish_reason": response.choices[0].finish_reason
            }

            # Kullanım bilgilerini ekle
            if hasattr(response, "usage") and response.usage:
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }

            # Araç çağrıları varsa ekle
            if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls:
                result["tool_calls"] = response.choices[0].message.tool_calls

            print(f"Metin üretildi: {len(result['content'])} karakter ({elapsed_time:.2f}s)")
            return result

        except Exception as e:
            # Metrikleri güncelle
            self.metrics["failed_requests"] += 1
            elapsed_time = time.time() - start_time

            print(f"OpenRouter API hatası: {str(e)}")
            raise OpenRouterAPIError(f"Metin üretilemedi: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """OpenRouter API üzerinden akış halinde metin üretir."""
        start_time = time.time()
        self.metrics["total_requests"] += 1
        self.metrics["last_request_time"] = datetime.now().isoformat()

        full_response = ""
        chunk_count = 0

        try:
            # Mesajları oluştur
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # İstek parametreleri
            params = {
                "model": model or self.default_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True
            }

            # Opsiyonel parametreler
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            if response_format:
                params["response_format"] = response_format

            if user_id:
                params["user"] = user_id

            print(f"OpenRouter API akış isteği gönderiliyor: {model or self.default_model}")
            
            # Doğrudan asenkron istemci ile stream oluştur
            stream = await self.async_client.chat.completions.create(**params)
            
            # Stream nesnesini doğrudan kullan (artık __aiter__ metodu var)
            async for chunk in stream:
                chunk_count += 1

                # Delta içeriğini kontrol et
                if chunk.choices and hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

                    # Parça bilgilerini döndür
                    yield {
                        "content": content,
                        "chunk_index": chunk_count,
                        "finish_reason": chunk.choices[0].finish_reason,
                        "model": getattr(chunk, "model", model or self.default_model)
                    }

            # Metrikleri güncelle
            elapsed_time = time.time() - start_time
            self.metrics["successful_requests"] += 1
            self.metrics["total_response_time"] += elapsed_time
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["successful_requests"]
            )

            # Son parçayı döndür (meta verilerle)
            yield {
                "content": "",  # Boş içerik, akışın bittiğini belirtir
                "chunk_index": chunk_count,
                "finish_reason": "stop",
                "model": model or self.default_model,
                "complete_text": full_response,
                "response_time": elapsed_time,
                "is_last_chunk": True
            }

            print(f"Akış tamamlandı: {len(full_response)} karakter, {chunk_count} parça ({elapsed_time:.2f}s)")

        except Exception as e:
            # Metrikleri güncelle
            self.metrics["failed_requests"] += 1
            elapsed_time = time.time() - start_time

            print(f"OpenRouter API akış hatası: {str(e)}")

            # Hata bilgisini döndür
            yield {
                "error": str(e),
                "chunk_index": chunk_count,
                "finish_reason": "error",
                "response_time": elapsed_time,
                "is_last_chunk": True
            }

            raise OpenRouterAPIError(f"Akış üretilemedi: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """API kullanım metriklerini döndürür."""
        return self.metrics

async def test_openrouter():
    """OpenRouter istemcisini test eder."""
    try:
        print("OpenRouter API testi başlatılıyor...")

        # İstemciyi başlat
        client = OpenRouterClient()

        # Metin üret
        print("\nMetin üretiliyor...")
        response = await client.generate_text(
            prompt="Yapay zeka nedir ve günlük hayatta nasıl kullanılır?",
            max_tokens=500,
            temperature=0.7,
            system_prompt="Türkçe yanıt ver ve örnekler kullan."
        )

        print(f"\nYanıt ({response['model']}):")
        print(response["content"])

        # Kullanım bilgilerini göster
        if "usage" in response:
            print(f"\nToken kullanımı: {response['usage']['total_tokens']} token")
            print(f"Yanıt süresi: {response['response_time']:.2f} saniye")

        # Streaming testi
        print("\nStreaming testi yapılıyor...")
        print("Yanıt parçaları:")
        full_text = ""
        async for chunk in client.generate_stream(
            prompt="Yapay zeka teknolojisinin geleceği nasıl olacak?",
            max_tokens=300,
            temperature=0.7,
            system_prompt="Türkçe yanıt ver ve kısa tut."
        ):
            if "content" in chunk and chunk["content"]:
                print(chunk["content"], end="", flush=True)
                full_text += chunk["content"]
            
            if "is_last_chunk" in chunk and chunk["is_last_chunk"]:
                print("\n\nStreaming tamamlandı.")
                print(f"Toplam karakter: {len(full_text)}")
                print(f"Yanıt süresi: {chunk['response_time']:.2f} saniye")

        # Metrikleri göster
        metrics = client.get_metrics()
        print("\nAPI metrikleri:")
        print(f"  Toplam istek sayısı: {metrics['total_requests']}")
        print(f"  Başarılı istek sayısı: {metrics['successful_requests']}")
        print(f"  Başarısız istek sayısı: {metrics['failed_requests']}")
        print(f"  Toplam token sayısı: {metrics['total_tokens']}")
        print(f"  Ortalama yanıt süresi: {metrics['average_response_time']:.2f} saniye")

        print("\nOpenRouter API testi başarıyla tamamlandı")
    except Exception as e:
        print(f"Test sırasında hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test fonksiyonunu çalıştır
    asyncio.run(test_openrouter())
