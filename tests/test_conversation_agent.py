# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Sohbet Ajanı Test Modülü

import os
import sys
import asyncio
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.conversation_agent import ConversationAgent
from src.core.exceptions import AgentError, ModelError


class TestConversationAgent(unittest.TestCase):
    """Sohbet ajanı testleri."""
    
    def setUp(self):
        """Test öncesi hazırlık."""
        # Mock dil modeli
        self.mock_language_model = MagicMock()
        
        # Mock bellek yöneticisi
        self.mock_memory_manager = MagicMock()
        
        # Test verileri
        self.test_user_message = "Merhaba, nasılsın?"
        self.test_task_id = "test_task_123"
    
    def test_init(self):
        """Başlatma testi."""
        # Sohbet ajanını başlat
        agent = ConversationAgent(
            language_model=self.mock_language_model,
            memory_manager=self.mock_memory_manager,
            default_language="tr",
            default_style="friendly"
        )
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, "conversation_agent")
        self.assertEqual(agent.language_model, self.mock_language_model)
        self.assertEqual(agent.memory_manager, self.mock_memory_manager)
        self.assertEqual(agent.default_language, "tr")
        self.assertEqual(agent.default_style, "friendly")
        self.assertEqual(agent.current_language, "tr")
        self.assertEqual(agent.current_style, "friendly")
        self.assertTrue(agent.is_initialized)
    
    def test_set_language(self):
        """Dil ayarlama testi."""
        agent = ConversationAgent()
        
        # Geçerli dil
        result = agent.set_language("en")
        self.assertTrue(result)
        self.assertEqual(agent.current_language, "en")
        
        # Geçersiz dil
        result = agent.set_language("xyz")
        self.assertFalse(result)
        self.assertEqual(agent.current_language, "en")  # Değişmemeli
    
    def test_set_communication_style(self):
        """İletişim tarzı ayarlama testi."""
        agent = ConversationAgent()
        
        # Geçerli tarz
        result = agent.set_communication_style("formal")
        self.assertTrue(result)
        self.assertEqual(agent.current_style, "formal")
        
        # Geçersiz tarz
        result = agent.set_communication_style("xyz")
        self.assertFalse(result)
        self.assertEqual(agent.current_style, "formal")  # Değişmemeli
    
    def test_get_system_prompt(self):
        """Sistem promptu oluşturma testi."""
        agent = ConversationAgent()
        
        # Türkçe, resmi tarz
        prompt_tr_formal = agent._get_system_prompt("tr", "formal")
        self.assertIn("Türkçe", prompt_tr_formal)
        self.assertIn("Resmi ve profesyonel", prompt_tr_formal)
        
        # İngilizce, samimi tarz
        prompt_en_friendly = agent._get_system_prompt("en", "friendly")
        self.assertIn("English", prompt_en_friendly)
        self.assertIn("Samimi ve arkadaşça", prompt_en_friendly)
    
    def test_get_basic_response(self):
        """Basit yanıt oluşturma testi."""
        agent = ConversationAgent()
        
        # Türkçe selamlaşma, resmi tarz
        response_tr_formal = agent._get_basic_response("merhaba", "formal", "tr")
        self.assertIn("Merhaba", response_tr_formal)
        self.assertIn("size", response_tr_formal)
        
        # İngilizce selamlaşma, samimi tarz
        response_en_friendly = agent._get_basic_response("hello", "friendly", "en")
        self.assertIn("Hi there", response_en_friendly)
        self.assertIn("How's it going", response_en_friendly)
    
    async def async_test_process_task_chat(self):
        """Sohbet görevi işleme testi."""
        # Mock yanıt
        mock_response = {
            "content": "Merhaba! Size nasıl yardımcı olabilirim?",
            "model": "anthropic/claude-3-haiku",
            "usage": {"total_tokens": 100}
        }
        
        # Mock dil modeli
        mock_language_model = MagicMock()
        mock_language_model.generate_text = MagicMock(return_value=mock_response)
        
        # Sohbet ajanını başlat
        agent = ConversationAgent(language_model=mock_language_model)
        
        # Görevi işle
        result = await agent.process_task(
            task_id=self.test_task_id,
            description=self.test_user_message,
            metadata={"action": "chat", "language": "tr", "style": "neutral"}
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["response"], "Merhaba! Size nasıl yardımcı olabilirim?")
        self.assertEqual(result["language"], "tr")
        self.assertEqual(result["style"], "neutral")
        self.assertEqual(result["model"], "anthropic/claude-3-haiku")
        
        # Dil modelinin doğru şekilde çağrıldığını doğrula
        mock_language_model.generate_text.assert_called_once()
        
        # Sohbet geçmişinin güncellendiğini doğrula
        self.assertEqual(len(agent.conversation_history), 1)
        self.assertEqual(agent.conversation_history[0]["user"], self.test_user_message)
        self.assertEqual(agent.conversation_history[0]["assistant"], "Merhaba! Size nasıl yardımcı olabilirim?")
    
    async def async_test_process_task_translate(self):
        """Çeviri görevi işleme testi."""
        # Mock yanıt
        mock_response = {
            "content": "Hello, how are you?",
            "model": "anthropic/claude-3-haiku",
            "usage": {"total_tokens": 100}
        }
        
        # Mock dil modeli
        mock_language_model = MagicMock()
        mock_language_model.generate_text = MagicMock(return_value=mock_response)
        
        # Sohbet ajanını başlat
        agent = ConversationAgent(language_model=mock_language_model)
        
        # Görevi işle
        result = await agent.process_task(
            task_id=self.test_task_id,
            description=self.test_user_message,
            metadata={
                "action": "translate",
                "entities": {"target_language": "en"},
                "source_language": "tr"
            }
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["translation"], "Hello, how are you?")
        self.assertEqual(result["source_language"], "tr")
        self.assertEqual(result["target_language"], "en")
        
        # Dil modelinin doğru şekilde çağrıldığını doğrula
        mock_language_model.generate_text.assert_called_once()
    
    async def async_test_process_task_set_language(self):
        """Dil ayarlama görevi işleme testi."""
        # Sohbet ajanını başlat
        agent = ConversationAgent()
        
        # Görevi işle
        result = await agent.process_task(
            task_id=self.test_task_id,
            description="Dili İngilizce olarak ayarla",
            metadata={
                "action": "set_language",
                "entities": {"language": "en"}
            }
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(agent.current_language, "en")
    
    async def async_test_process_task_error(self):
        """Hata durumu testi."""
        # Mock dil modeli (hata fırlatan)
        mock_language_model = MagicMock()
        mock_language_model.generate_text = MagicMock(side_effect=Exception("Test hatası"))
        
        # Sohbet ajanını başlat
        agent = ConversationAgent(language_model=mock_language_model)
        
        # Görevi işle
        result = await agent.process_task(
            task_id=self.test_task_id,
            description=self.test_user_message,
            metadata={"action": "chat"}
        )
        
        self.assertFalse(result["success"])
        self.assertIn("hata", result["message"].lower())
        self.assertIn("Test hatası", result["error"])
    
    def test_all(self):
        """Tüm asenkron testleri çalıştır."""
        loop = asyncio.get_event_loop()
        
        # Tüm asenkron testleri çalıştır
        loop.run_until_complete(self.async_test_process_task_chat())
        loop.run_until_complete(self.async_test_process_task_translate())
        loop.run_until_complete(self.async_test_process_task_set_language())
        loop.run_until_complete(self.async_test_process_task_error())


if __name__ == "__main__":
    unittest.main()
