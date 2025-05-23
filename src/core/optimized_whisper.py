# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Optimize Edilmiş Whisper Modülü

import os
import asyncio
import tempfile
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from faster_whisper import WhisperModel

class OptimizedWhisperTranscriber:
    """Optimize edilmiş Whisper ses tanıma sınıfı.
    
    Bu sınıf, Faster-Whisper kütüphanesini kullanarak
    ses tanıma işlemlerini optimize edilmiş şekilde gerçekleştirir.
    Asenkron işleme, önbellekleme ve model optimizasyonları içerir.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """OptimizedWhisperTranscriber başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        
        # Model ayarları
        self.model_size = config.get("whisper_model_size", "small")
        self.device = config.get("whisper_device", "cpu")
        self.compute_type = config.get("whisper_compute_type", "float16")
        
        # Performans ayarları
        self.beam_size = config.get("beam_size", 5)
        self.vad_filter = config.get("vad_filter", True)
        self.vad_parameters = config.get("vad_parameters", {
            "min_silence_duration_ms": 500,
            "speech_pad_ms": 400
        })
        
        # Dil ayarları
        self.language = config.get("default_language", "tr")
        self.translate = config.get("translate", False)
        
        # Model yükleme
        self._load_model()
        
        # İşleme kilidi
        self._processing_lock = asyncio.Lock()
        
        # Önbellek
        self._cache: Dict[str, str] = {}
        self.max_cache_size = config.get("max_cache_size", 100)
        
    def _load_model(self) -> None:
        """Whisper modelini yükler."""
        try:
            logging.info(f"Whisper modeli yükleniyor: {self.model_size} ({self.device}, {self.compute_type})")
            
            # Modeli yükle
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=self.config.get("model_path", None)
            )
            
            logging.info("Whisper modeli başarıyla yüklendi")
            
        except Exception as e:
            logging.error(f"Whisper modeli yüklenemedi: {str(e)}")
            raise RuntimeError(f"Whisper modeli yüklenemedi: {str(e)}")
    
    def _generate_cache_key(self, audio_data: bytes) -> str:
        """Önbellek anahtarı oluşturur.
        
        Args:
            audio_data: Ses verisi
            
        Returns:
            str: Önbellek anahtarı
        """
        import hashlib
        return hashlib.md5(audio_data).hexdigest()
    
    def _add_to_cache(self, key: str, text: str) -> None:
        """Sonucu önbelleğe ekler.
        
        Args:
            key: Önbellek anahtarı
            text: Tanınan metin
        """
        # Önbellek boyutu kontrolü
        if len(self._cache) >= self.max_cache_size:
            # En eski anahtarı sil
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        # Önbelleğe ekle
        self._cache[key] = text
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        task: Optional[str] = None
    ) -> str:
        """Ses verisini metne dönüştürür.
        
        Args:
            audio_data: Ses verisi
            language: Dil kodu (opsiyonel)
            task: Görev tipi (transcribe veya translate)
            
        Returns:
            str: Tanınan metin
        """
        try:
            # Önbellekte ara
            cache_key = self._generate_cache_key(audio_data)
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            async with self._processing_lock:
                # Geçici dosya oluştur
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(audio_data)
                
                try:
                    # Dil ve görev ayarlarını belirle
                    lang = language or self.language
                    task_type = task or ("translate" if self.translate else "transcribe")
                    
                    # Asenkron transcribe işlemi
                    loop = asyncio.get_event_loop()
                    segments, info = await loop.run_in_executor(
                        None,
                        lambda: self.model.transcribe(
                            temp_path,
                            language=lang,
                            task=task_type,
                            beam_size=self.beam_size,
                            vad_filter=self.vad_filter,
                            vad_parameters=self.vad_parameters
                        )
                    )
                    
                    # Segmentleri birleştir
                    text = " ".join([segment.text for segment in segments])
                    
                    # Önbelleğe ekle
                    self._add_to_cache(cache_key, text)
                    
                    return text.strip()
                    
                finally:
                    # Geçici dosyayı temizle
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        except Exception as e:
            logging.error(f"Ses tanıma hatası: {str(e)}")
            raise RuntimeError(f"Ses tanıma hatası: {str(e)}")
    
    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Ses verisini zaman damgalı olarak metne dönüştürür.
        
        Args:
            audio_data: Ses verisi
            language: Dil kodu (opsiyonel)
            
        Returns:
            List[Dict[str, Any]]: Zaman damgalı segmentler
        """
        try:
            async with self._processing_lock:
                # Geçici dosya oluştur
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(audio_data)
                
                try:
                    # Dil ayarını belirle
                    lang = language or self.language
                    
                    # Asenkron transcribe işlemi
                    loop = asyncio.get_event_loop()
                    segments, info = await loop.run_in_executor(
                        None,
                        lambda: self.model.transcribe(
                            temp_path,
                            language=lang,
                            beam_size=self.beam_size,
                            word_timestamps=True,
                            vad_filter=self.vad_filter,
                            vad_parameters=self.vad_parameters
                        )
                    )
                    
                    # Segmentleri işle
                    result = []
                    for segment in segments:
                        result.append({
                            "text": segment.text,
                            "start": segment.start,
                            "end": segment.end,
                            "words": [
                                {
                                    "word": word.word,
                                    "start": word.start,
                                    "end": word.end,
                                    "probability": word.probability
                                }
                                for word in segment.words
                            ] if segment.words else []
                        })
                    
                    return result
                    
                finally:
                    # Geçici dosyayı temizle
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        except Exception as e:
            logging.error(f"Zaman damgalı ses tanıma hatası: {str(e)}")
            raise RuntimeError(f"Zaman damgalı ses tanıma hatası: {str(e)}")
