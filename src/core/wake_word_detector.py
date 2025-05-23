# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Wake Word Detection Modülü

import os
import asyncio
import numpy as np
import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
from pathlib import Path
try:
    from pvrecorder import PvRecorder
    from pvporcupine import PvPorcupine as Porcupine
except ImportError:
    # Eğer modüller bulunamazsa, sahte sınıflar oluştur
    logging.warning("PvRecorder veya PvPorcupine modülleri bulunamadı. Sahte sınıflar kullanılacak.")

    class PvRecorder:
        def __init__(self, frame_length=0, device_index=-1):
            self.frame_length = frame_length
            self.device_index = device_index

        def start(self):
            logging.warning("Sahte PvRecorder.start() çağrıldı")

        def read(self):
            return [0] * self.frame_length

        def stop(self):
            logging.warning("Sahte PvRecorder.stop() çağrıldı")

        def delete(self):
            logging.warning("Sahte PvRecorder.delete() çağrıldı")

    class Porcupine:
        def __init__(self, access_key=None, keywords=None, keyword_paths=None, sensitivities=None):
            self.frame_length = 512
            self.keywords = keywords or []
            self.keyword_paths = keyword_paths or []

        def process(self, pcm):
            return -1  # Hiçbir şey algılanmadı

        def delete(self):
            logging.warning("Sahte Porcupine.delete() çağrıldı")

class WakeWordState(Enum):
    """Wake word algılama durumları."""
    IDLE = 0
    LISTENING = 1
    DETECTED = 2
    PROCESSING = 3
    ERROR = 4

class WakeWordDetector:
    """Wake word algılama sınıfı.

    Bu sınıf, Picovoice Porcupine kütüphanesini kullanarak
    wake word algılama işlemini gerçekleştirir. "Hey ZEKA" gibi
    özel bir kelime veya ifade algılandığında belirtilen callback
    fonksiyonunu çağırır.
    """

    def __init__(self, config: Dict[str, Any]):
        """WakeWordDetector başlatıcısı.

        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.access_key = config.get("porcupine_access_key", os.getenv("PORCUPINE_ACCESS_KEY"))
        self.keywords = config.get("wake_words", ["hey zeka"])
        self.sensitivities = config.get("sensitivities", [0.7] * len(self.keywords))
        self.device_index = config.get("device_index", -1)  # -1: varsayılan mikrofon

        self.porcupine = None
        self.recorder = None
        self.state = WakeWordState.IDLE
        self.detection_callback = None
        self.running = False
        self._task = None

        # Hata durumunda yeniden deneme ayarları
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 5)  # saniye
        self.current_retry = 0

        # Özel wake word modeli
        self.custom_keyword_paths = config.get("custom_keyword_paths", None)

    async def initialize(self) -> bool:
        """Wake word algılama sistemini başlatır.

        Returns:
            bool: Başlatma başarılı ise True
        """
        try:
            # Porcupine nesnesini oluştur
            if self.custom_keyword_paths:
                self.porcupine = Porcupine(
                    access_key=self.access_key,
                    keyword_paths=self.custom_keyword_paths,
                    sensitivities=self.sensitivities
                )
            else:
                self.porcupine = Porcupine(
                    access_key=self.access_key,
                    keywords=self.keywords,
                    sensitivities=self.sensitivities
                )

            # Ses kaydediciyi oluştur
            self.recorder = PvRecorder(
                frame_length=self.porcupine.frame_length,
                device_index=self.device_index
            )

            self.state = WakeWordState.IDLE
            self.current_retry = 0
            return True

        except Exception as e:
            logging.error(f"Wake word algılama sistemi başlatılamadı: {str(e)}")
            self.state = WakeWordState.ERROR
            return False

    def set_detection_callback(self, callback: Callable[[int], None]) -> None:
        """Wake word algılama callback fonksiyonunu ayarlar.

        Args:
            callback: Algılama durumunda çağrılacak fonksiyon
        """
        self.detection_callback = callback

    async def start(self) -> bool:
        """Wake word algılama işlemini başlatır.

        Returns:
            bool: Başlatma başarılı ise True
        """
        if self.running:
            return True

        if not self.porcupine or not self.recorder:
            success = await self.initialize()
            if not success:
                return False

        try:
            self.recorder.start()
            self.running = True
            self.state = WakeWordState.LISTENING

            # Asenkron dinleme görevini başlat
            self._task = asyncio.create_task(self._listen_loop())

            logging.info(f"Wake word algılama başladı. Dinlenen kelimeler: {self.keywords}")
            return True

        except Exception as e:
            logging.error(f"Wake word algılama başlatılamadı: {str(e)}")
            self.state = WakeWordState.ERROR
            return False

    async def stop(self) -> None:
        """Wake word algılama işlemini durdurur."""
        self.running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self.recorder:
            self.recorder.stop()

        self.state = WakeWordState.IDLE
        logging.info("Wake word algılama durduruldu")

    async def _listen_loop(self) -> None:
        """Sürekli dinleme döngüsü."""
        try:
            while self.running:
                # Ses verisini oku
                pcm = self.recorder.read()

                # Wake word algılama
                result = self.porcupine.process(pcm)

                if result >= 0:  # Wake word algılandı
                    self.state = WakeWordState.DETECTED
                    logging.info(f"Wake word algılandı: {self.keywords[result]}")

                    # Callback fonksiyonunu çağır
                    if self.detection_callback:
                        self.detection_callback(result)

                    # Kısa bir süre bekle (yeni algılamaları önlemek için)
                    self.state = WakeWordState.PROCESSING
                    await asyncio.sleep(2)
                    self.state = WakeWordState.LISTENING

                # Diğer asenkron işlemlere fırsat ver
                await asyncio.sleep(0.01)

        except Exception as e:
            logging.error(f"Wake word dinleme hatası: {str(e)}")
            self.state = WakeWordState.ERROR

            # Yeniden deneme
            if self.current_retry < self.max_retries:
                self.current_retry += 1
                logging.info(f"Wake word algılama yeniden başlatılıyor ({self.current_retry}/{self.max_retries})...")
                await asyncio.sleep(self.retry_delay)
                await self.stop()
                await self.start()
            else:
                logging.error("Maksimum yeniden deneme sayısına ulaşıldı")

    def __del__(self):
        """Nesne yok edildiğinde kaynakları temizle."""
        if self.recorder:
            self.recorder.delete()
        if self.porcupine:
            self.porcupine.delete()
