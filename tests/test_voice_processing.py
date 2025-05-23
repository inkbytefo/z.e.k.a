# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ses İşleme Testleri

import os
import unittest
import asyncio
import numpy as np
from unittest.mock import MagicMock, patch
from ..src.core.voice_processor import VoiceProcessor
from ..src.core.voice_profile import VoiceProfile

class TestVoiceProcessor(unittest.TestCase):
    """VoiceProcessor sınıfı için test senaryoları."""
    
    def setUp(self):
        """Her test öncesi çalışacak hazırlık fonksiyonu."""
        self.config = {
            "openai_api_key": "test_key",
            "elevenlabs_api_key": "test_key",
            "target_sample_rate": 44100,
            "target_db": -15,
            "chunk_size": 1024 * 16,
            "max_pool_size": 100
        }
        self.processor = VoiceProcessor(self.config)
        
        # Test ses verisi oluştur
        duration = 1  # 1 saniye
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        self.test_audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sinüs dalgası
        
    def test_preprocess_audio(self):
        """Ses önişleme fonksiyonunu test eder."""
        # Test ses verisini bytes formatına dönüştür
        audio_bytes = self.processor._audio_to_bytes(self.test_audio, 44100)
        
        # Önişleme yap
        processed = self.processor.preprocess_audio(audio_bytes)
        
        # Sonuçları kontrol et
        processed_array, sr = self.processor._bytes_to_audio(processed)
        self.assertEqual(sr, 44100)
        self.assertTrue(np.max(np.abs(processed_array)) <= 1.0)
        
    def test_postprocess_audio(self):
        """Ses sonişleme fonksiyonunu test eder."""
        # Test ses verisini bytes formatına dönüştür
        audio_bytes = self.processor._audio_to_bytes(self.test_audio, 44100)
        
        # Sonişleme yap
        processed = self.processor.postprocess_audio(audio_bytes)
        
        # Sonuçları kontrol et
        processed_array, sr = self.processor._bytes_to_audio(processed)
        
        # Örnekleme hızı kontrolü
        self.assertEqual(sr, self.config["target_sample_rate"])
        
        # Ses seviyesi kontrolü
        current_db = 20 * np.log10(np.max(np.abs(processed_array)))
        self.assertGreaterEqual(current_db, self.config["target_db"])
    
    @patch("openai.Audio.atranscribe")
    async def test_speech_to_text(self, mock_transcribe):
        """Ses tanıma fonksiyonunu test eder."""
        # Mock yanıtı ayarla
        mock_transcribe.return_value = {"text": "test metni"}
        
        # Test ses verisi oluştur
        audio_bytes = self.processor._audio_to_bytes(self.test_audio, 44100)
        
        # Ses tanıma yap
        text = await self.processor.speech_to_text(audio_bytes)
        
        # Sonucu kontrol et
        self.assertEqual(text, "test metni")
        
        # API çağrısını kontrol et
        mock_transcribe.assert_called_once()
    
    @patch("elevenlabs.generate")
    async def test_text_to_speech(self, mock_generate):
        """Metin okuma fonksiyonunu test eder."""
        # Mock yanıtı ayarla
        mock_generate.return_value = b"test_audio_data"
        
        # Test profili ayarla
        self.processor.voice_profile = VoiceProfile(
            voice_id="test_voice",
            language="tr",
            stability=0.7,
            similarity_boost=0.5,
            style=0.0,
            use_speaker_boost=True
        )
        
        # Metin okuma yap
        audio = await self.processor.text_to_speech("test metni")
        
        # Sonucu kontrol et
        self.assertEqual(audio, b"test_audio_data")
        
        # API çağrısını kontrol et
        mock_generate.assert_called_once()
    
    def test_voice_profile_update(self):
        """Ses profili güncelleme fonksiyonunu test eder."""
        profile = VoiceProfile(
            voice_id="test_voice",
            language="tr",
            stability=0.7,
            similarity_boost=0.5,
            style=0.0,
            use_speaker_boost=True
        )
        
        self.processor.update_profile(profile)
        
        # Profil güncellemesini kontrol et
        self.assertEqual(self.processor.voice_profile, profile)
        self.assertEqual(self.processor.voice_settings.stability, profile.stability)
        self.assertEqual(self.processor.voice_settings.similarity_boost, profile.similarity_boost)
        self.assertEqual(self.processor.voice_settings.style, profile.style)
        self.assertEqual(self.processor.voice_settings.use_speaker_boost, profile.use_speaker_boost)

def async_test(f):
    """Asenkron test fonksiyonları için dekoratör."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(f(*args, **kwargs))
    return wrapper

if __name__ == "__main__":
    unittest.main()
