# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ses İşleme Araçları

import threading
import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
from typing import Optional, Tuple, Callable
from pathlib import Path
import wave
import pyaudio
from ..config import APP_CONFIG

class AudioRecorder:
    """Ses kaydı için araç sınıfı."""
    
    def __init__(self, config: dict = None):
        """AudioRecorder başlatıcısı.
        
        Args:
            config: Ses kaydı yapılandırması
        """
        self.config = config or APP_CONFIG["audio"]
        self.recording = False
        self.audio_queue = queue.Queue()
        self.callback: Optional[Callable] = None
        
    def start_recording(self, callback: Optional[Callable] = None) -> None:
        """Ses kaydını başlatır.
        
        Args:
            callback: Her ses parçası için çağrılacak fonksiyon
        """
        self.recording = True
        self.callback = callback
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Ses kaydı durumu: {status}")
            if self.recording:
                self.audio_queue.put(indata.copy())
                if self.callback:
                    self.callback(indata.copy())
                    
        self.stream = sd.InputStream(
            samplerate=self.config["sample_rate"],
            channels=self.config["channels"],
            dtype=np.float32,
            blocksize=self.config["chunk_size"],
            callback=audio_callback
        )
        self.stream.start()
        
    def stop_recording(self) -> np.ndarray:
        """Ses kaydını durdurur ve kaydı döndürür.
        
        Returns:
            np.ndarray: Kaydedilen ses verisi
        """
        self.recording = False
        self.stream.stop()
        self.stream.close()
        
        # Kuyruktaki tüm ses verilerini birleştir
        chunks = []
        while not self.audio_queue.empty():
            chunks.append(self.audio_queue.get())
            
        return np.concatenate(chunks) if chunks else np.array([])
        
class AudioPlayer:
    """Ses çalma için araç sınıfı."""
    
    def __init__(self, config: dict = None):
        """AudioPlayer başlatıcısı.
        
        Args:
            config: Ses çalma yapılandırması
        """
        self.config = config or APP_CONFIG["audio"]
        self._audio = pyaudio.PyAudio()
        
    def play_audio(self, audio_data: np.ndarray) -> None:
        """Ses verisini çalar.
        
        Args:
            audio_data: Çalınacak ses verisi
        """
        stream = self._audio.open(
            format=pyaudio.paFloat32,
            channels=self.config["channels"],
            rate=self.config["sample_rate"],
            output=True
        )
        
        try:
            stream.write(audio_data.tobytes())
        finally:
            stream.stop_stream()
            stream.close()
            
    def play_file(self, file_path: str) -> None:
        """Ses dosyasını çalar.
        
        Args:
            file_path: Çalınacak ses dosyası yolu
        """
        audio_data, _ = sf.read(file_path)
        self.play_audio(audio_data)
        
    def __del__(self):
        """PyAudio nesnesini temizle."""
        self._audio.terminate()
        
class AudioProcessor:
    """Ses işleme için yardımcı araç sınıfı."""
    
    @staticmethod
    def save_audio(audio_data: np.ndarray, file_path: str, config: dict = None) -> None:
        """Ses verisini dosyaya kaydeder.
        
        Args:
            audio_data: Kaydedilecek ses verisi
            file_path: Hedef dosya yolu
            config: Ses yapılandırması
        """
        config = config or APP_CONFIG["audio"]
        
        # Dizini oluştur
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Ses verisini kaydet
        sf.write(
            file_path,
            audio_data,
            config["sample_rate"],
            subtype="FLOAT"
        )
        
    @staticmethod
    def load_audio(file_path: str) -> Tuple[np.ndarray, int]:
        """Ses dosyasını yükler.
        
        Args:
            file_path: Yüklenecek ses dosyası yolu
            
        Returns:
            Tuple[np.ndarray, int]: Ses verisi ve örnekleme hızı
        """
        return sf.read(file_path)
        
    @staticmethod
    def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
        """Ses seviyesini normalize eder.
        
        Args:
            audio_data: Normalize edilecek ses verisi
            
        Returns:
            np.ndarray: Normalize edilmiş ses verisi
        """
        return audio_data / np.max(np.abs(audio_data))
        
    @staticmethod
    def detect_silence(
        audio_data: np.ndarray,
        threshold: float = 0.02,
        min_duration: float = 0.3,
        sample_rate: int = 44100
    ) -> bool:
        """Ses verisinde sessizliği tespit eder.
        
        Args:
            audio_data: Kontrol edilecek ses verisi
            threshold: Sessizlik eşiği
            min_duration: Minimum sessizlik süresi (saniye)
            sample_rate: Örnekleme hızı
            
        Returns:
            bool: Sessizlik tespit edildi mi
        """
        # RMS enerji hesapla
        window_size = int(min_duration * sample_rate)
        if len(audio_data) < window_size:
            return True
            
        rms = np.sqrt(np.mean(audio_data**2))
        return rms < threshold
