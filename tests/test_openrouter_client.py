# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# OpenRouter API İstemci Test Modülü

import os
import sys
import asyncio
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.openrouter_client import OpenRouterClient
from src.core.exceptions import OpenRouterAPIError


class TestOpenRouterClient(unittest.TestCase):
    """OpenRouter API istemci testleri."""
    
    def setUp(self):
        """Test öncesi hazırlık."""
        # Test API anahtarı
        self.api_key = os.getenv("OPENROUTER_API_KEY", "test_api_key")
        
        # Test verileri
        self.test_prompt = "Yapay zeka nedir ve günlük hayatta nasıl kullanılır?"
        self.test_system_prompt = "Türkçe yanıt ver ve örnekler kullan."
        self.test_model = "anthropic/claude-3-haiku"
    
    @patch("openai.OpenAI")
    def test_init(self, mock_openai):
        """Başlatma testi."""
        # Mock OpenAI istemcisi
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # OpenRouter istemcisini başlat
        client = OpenRouterClient(
            api_key=self.api_key,
            default_model=self.test_model,
            site_url="https://test.com",
            site_name="Test App"
        )
        
        self.assertIsNotNone(client)
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.default_model, self.test_model)
        self.assertEqual(client.site_url, "https://test.com")
        self.assertEqual(client.site_name, "Test App")
        
        # OpenAI istemcisinin doğru parametrelerle çağrıldığını doğrula
        mock_openai.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            timeout=60.0,
            max_retries=3,
            default_headers={
                "HTTP-Referer": "https://test.com",
                "X-Title": "Test App"
            }
        )
    
    @patch("openai.OpenAI")
    async def async_test_generate_text(self, mock_openai):
        """Metin üretme testi."""
        # Mock yanıt
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Yapay zeka (AI), insan zekasını simüle eden bilgisayar sistemleridir."
        mock_response.model = self.test_model
        mock_response.created = 1234567890
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 150
        
        # Mock istemci
        mock_client = MagicMock()
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # OpenRouter istemcisini başlat
        client = OpenRouterClient(api_key=self.api_key)
        
        # Metin üret
        response = await client.generate_text(
            prompt=self.test_prompt,
            model=self.test_model,
            system_prompt=self.test_system_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        self.assertIsNotNone(response)
        self.assertEqual(response["content"], "Yapay zeka (AI), insan zekasını simüle eden bilgisayar sistemleridir.")
        self.assertEqual(response["model"], self.test_model)
        self.assertEqual(response["usage"]["total_tokens"], 150)
        
        # İstemcinin doğru parametrelerle çağrıldığını doğrula
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], self.test_model)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["max_tokens"], 1000)
        self.assertEqual(len(kwargs["messages"]), 2)
        self.assertEqual(kwargs["messages"][0]["role"], "system")
        self.assertEqual(kwargs["messages"][0]["content"], self.test_system_prompt)
        self.assertEqual(kwargs["messages"][1]["role"], "user")
        self.assertEqual(kwargs["messages"][1]["content"], self.test_prompt)
    
    @patch("openai.OpenAI")
    async def async_test_generate_stream(self, mock_openai):
        """Akış halinde metin üretme testi."""
        # Mock yanıt parçaları
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Yapay "
        chunk1.choices[0].finish_reason = None
        
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "zeka "
        chunk2.choices[0].finish_reason = None
        
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = "nedir?"
        chunk3.choices[0].finish_reason = "stop"
        
        # Mock akış
        mock_stream = [chunk1, chunk2, chunk3]
        
        # Mock istemci
        mock_client = MagicMock()
        mock_client.chat.completions.create = MagicMock(return_value=mock_stream)
        mock_openai.return_value = mock_client
        
        # OpenRouter istemcisini başlat
        client = OpenRouterClient(api_key=self.api_key)
        
        # Akış halinde metin üret
        chunks = []
        async for chunk in client.generate_stream(
            prompt=self.test_prompt,
            model=self.test_model,
            system_prompt=self.test_system_prompt,
            temperature=0.7,
            max_tokens=1000
        ):
            chunks.append(chunk)
        
        self.assertEqual(len(chunks), 4)  # 3 içerik parçası + 1 son parça
        self.assertEqual(chunks[0]["content"], "Yapay ")
        self.assertEqual(chunks[1]["content"], "zeka ")
        self.assertEqual(chunks[2]["content"], "nedir?")
        self.assertTrue(chunks[3]["is_last_chunk"])
        
        # İstemcinin doğru parametrelerle çağrıldığını doğrula
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs["model"], self.test_model)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["max_tokens"], 1000)
        self.assertTrue(kwargs["stream"])
    
    @patch("openai.OpenAI")
    async def async_test_list_available_models(self, mock_openai):
        """Kullanılabilir modelleri listeleme testi."""
        # Mock yanıt
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(id="anthropic/claude-3-opus"),
            MagicMock(id="anthropic/claude-3-sonnet"),
            MagicMock(id="openai/gpt-4")
        ]
        
        # Mock istemci
        mock_client = MagicMock()
        mock_client.models.list = MagicMock(return_value=mock_response)
        mock_openai.return_value = mock_client
        
        # OpenRouter istemcisini başlat
        client = OpenRouterClient(api_key=self.api_key)
        
        # Modelleri listele
        models = await client.list_available_models()
        
        self.assertEqual(len(models), 3)
        self.assertEqual(models[0]["id"], "anthropic/claude-3-opus")
        self.assertEqual(models[0]["provider"], "anthropic")
        self.assertEqual(models[0]["name"], "claude-3-opus")
        
        # İstemcinin doğru şekilde çağrıldığını doğrula
        mock_client.models.list.assert_called_once()
    
    def test_all(self):
        """Tüm asenkron testleri çalıştır."""
        loop = asyncio.get_event_loop()
        
        # Tüm asenkron testleri çalıştır
        loop.run_until_complete(self.async_test_generate_text())
        loop.run_until_complete(self.async_test_generate_stream())
        loop.run_until_complete(self.async_test_list_available_models())


if __name__ == "__main__":
    unittest.main()
