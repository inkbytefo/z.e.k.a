# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ses İşleme Modülü

import asyncio
import numpy as np
import soundfile as sf
import tempfile
import os
import io
import logging
import webrtcvad
import pyaudio
import wave
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, AsyncGenerator, Callable
from .voice_profile import VoiceProfile
from .voice_cache import VoiceCache
from .wake_word_detector import WakeWordDetector, WakeWordState
from .optimized_whisper import OptimizedWhisperTranscriber
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from scipy import signal

class ListeningMode(Enum):
    """Dinleme modları."""
    MANUAL = 0  # Manuel tetikleme (API çağrısı ile)
    WAKE_WORD = 1  # Wake word ile tetikleme
    CONTINUOUS = 2  # Sürekli dinleme

class VoiceProcessor:
    """Ses işleme fonksiyonlarını sağlayan temel sınıf.

    Bu sınıf, konuşma tanıma (STT) ve metin okuma (TTS)
    işlemlerini gerçekleştirir. Faster Whisper ve ElevenLabs
    servislerini kullanır. Ayrıca wake word detection ve
    sürekli dinleme modlarını destekler.
    """

    def __init__(self, config: Dict[str, Any]):
        """VoiceProcessor başlatıcısı.

        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.voice_profile = None
        self.cache = VoiceCache(config)
        self._audio_pool: Dict[str, np.ndarray] = {}
        self._processing_lock = asyncio.Lock()

        # Dinleme modu ayarları
        self.listening_mode = ListeningMode.MANUAL
        self.is_listening = False
        self.listening_task = None
        self.speech_callback = None

        # Wake word detector
        self.wake_word_detector = None
        if config.get("enable_wake_word", False):
            self.wake_word_detector = WakeWordDetector(config.get("wake_word_config", {}))

        # VAD (Voice Activity Detection)
        self.vad = None
        if config.get("enable_vad", False):
            self.vad = webrtcvad.Vad(config.get("vad_aggressiveness", 3))

        # PyAudio için ayarlar
        self.audio_format = pyaudio.paInt16
        self.channels = config.get("audio_channels", 1)
        self.rate = config.get("audio_rate", 16000)
        self.chunk = config.get("audio_chunk", 1024)
        self.pyaudio_instance = None

        # Performans ayarları
        self.chunk_size = config.get("chunk_size", 1024 * 16)  # 16KB chunks
        self.max_pool_size = config.get("max_pool_size", 100)  # Max 100 audio in memory

        # API anahtarlarını ayarla
        elevenlabs_api_key = config.get("elevenlabs_api_key")
        if elevenlabs_api_key:
            set_api_key(elevenlabs_api_key)
        else:
            logging.warning("ElevenLabs API anahtarı bulunamadı. Lütfen .env dosyasında ELEVENLABS_API_KEY değişkenini ayarlayın.")

        # Optimize edilmiş Whisper modelini yükle
        self.whisper_transcriber = OptimizedWhisperTranscriber(config)

        # Ses ayarları
        self.voice_settings = VoiceSettings(
            stability=0.71,
            similarity_boost=0.5,
            style=0.0,
            use_speaker_boost=True
        )

    def update_profile(self, profile: VoiceProfile) -> None:
        """Ses profilini günceller.

        Args:
            profile: Yeni ses profili
        """
        self.voice_profile = profile

        # ElevenLabs ses ayarlarını güncelle
        self.voice_settings = VoiceSettings(
            stability=profile.stability,
            similarity_boost=profile.similarity_boost,
            style=profile.style,
            use_speaker_boost=profile.use_speaker_boost
        )

    def _add_to_pool(self, key: str, audio_array: np.ndarray) -> None:
        """Ses verisini bellek havuzuna ekler.

        Args:
            key: Önbellek anahtarı
            audio_array: Ses verisi
        """
        if len(self._audio_pool) >= self.max_pool_size:
            # En eski veriyi sil
            oldest_key = next(iter(self._audio_pool))
            del self._audio_pool[oldest_key]

        self._audio_pool[key] = audio_array

    async def _process_chunks(self, audio_data: bytes) -> np.ndarray:
        """Ses verisini parçalar halinde işler.

        Args:
            audio_data: İşlenecek ses verisi

        Returns:
            np.ndarray: İşlenmiş ses verisi
        """
        audio_array, sample_rate = self._bytes_to_audio(audio_data)
        chunk_samples = int(self.chunk_size * sample_rate / 1000)  # ms to samples
        chunks = []

        for i in range(0, len(audio_array), chunk_samples):
            chunk = audio_array[i:i + chunk_samples]
            # Asenkron işleme simülasyonu
            await asyncio.sleep(0)
            chunks.append(chunk)

        return np.concatenate(chunks)

    async def speech_to_text(self, audio_data: bytes) -> str:
        """Ses verisini metne dönüştürür.

        Args:
            audio_data: İşlenecek ses verisi

        Returns:
            str: Dönüştürülen metin
        """
        try:
            # Ses verisini ön işle
            processed_audio = self.preprocess_audio(audio_data)

            # Dil ayarını belirle
            language = self.voice_profile.language if self.voice_profile else None

            # Optimize edilmiş Whisper ile ses tanıma
            text = await self.whisper_transcriber.transcribe(processed_audio, language)

            logging.info(f"Ses tanıma tamamlandı: {len(text)} karakter")
            return text.strip()

        except Exception as e:
            logging.error(f"Ses tanıma hatası: {str(e)}")
            raise RuntimeError(f"Ses tanıma hatası: {str(e)}")

    async def text_to_speech(self, text: str, chunk_size: Optional[int] = None) -> bytes:
        """Metni ses verisine dönüştürür.

        Args:
            text: Sese dönüştürülecek metin
            chunk_size: Parça boyutu (byte)

        Returns:
            bytes: Üretilen ses verisi
        """
        try:
            # Ses profili ayarlarını al
            voice_id = (
                self.voice_profile.voice_id
                if self.voice_profile
                else self.config.get("default_voice_id")
            )

            async with self._processing_lock:
                # Önbellekte ara
                cached_audio, metadata = self.cache.get(text, voice_id)
                if cached_audio:
                    return cached_audio

                # Cache miss - bellek havuzunda ara
                cache_key = self.cache._generate_key(text, voice_id)
                if cache_key in self._audio_pool:
                    return self._audio_to_bytes(self._audio_pool[cache_key], self.config.get("target_sample_rate", 44100))

            # ElevenLabs ile ses üret (chunk_size belirtilmişse stream modunda)
            chunk_size = chunk_size or self.chunk_size
            audio_chunks = []

            async for chunk in self._stream_audio(
                text=text,
                voice_id=voice_id,
                chunk_size=chunk_size
            ):
                audio_chunks.append(chunk)

            audio = b"".join(audio_chunks)

            # Ses verisini numpy dizisine dönüştür
            audio_array, _ = self._bytes_to_audio(audio)

            # Bellek havuzuna ve önbelleğe kaydet
            self._add_to_pool(cache_key, audio_array)
            self.cache.put(
                text,
                audio,
                voice_id,
                {
                    "model": self.config.get("tts_model", "eleven_multilingual_v1"),
                    "settings": self.voice_settings.__dict__
                }
            )

            return audio

        except Exception as e:
            raise RuntimeError(f"Ses üretme hatası: {str(e)}")

    async def _stream_audio(
        self,
        text: str,
        voice_id: str,
        chunk_size: int
    ) -> AsyncGenerator[bytes, None]:
        """Ses verisini stream modunda üretir.

        Args:
            text: Sese dönüştürülecek metin
            voice_id: Ses profili ID'si
            chunk_size: Parça boyutu (byte)

        Yields:
            bytes: Ses verisi parçası
        """
        try:
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=self.voice_settings
                ),
                model=self.config.get("tts_model", "eleven_multilingual_v1"),
                stream=True
            )

            buffer = b""
            for chunk in audio:
                buffer += chunk
                while len(buffer) >= chunk_size:
                    yield buffer[:chunk_size]
                    buffer = buffer[chunk_size:]
                    await asyncio.sleep(0)  # Diğer asenkron işlemlere fırsat ver

            if buffer:
                yield buffer

        except Exception as e:
            raise RuntimeError(f"Ses stream hatası: {str(e)}")

    def _bytes_to_audio(self, audio_data: bytes) -> Tuple[np.ndarray, int]:
        """Bytes formatındaki ses verisini numpy dizisine dönüştürür.

        Args:
            audio_data: Bytes formatında ses verisi

        Returns:
            Tuple[np.ndarray, int]: Ses verisi ve örnekleme hızı
        """
        import io
        try:
            # Geçici dosya kullanarak ses verisini oku
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_data)

            # Geçici dosyadan ses verisini oku
            audio_array, sample_rate = sf.read(temp_path)

            # Geçici dosyayı temizle
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            return audio_array, sample_rate
        except Exception as e:
            # Hata durumunda orijinal yöntemi dene
            try:
                with io.BytesIO(audio_data) as buf:
                    audio_array, sample_rate = sf.read(buf)
                    return audio_array, sample_rate
            except Exception as inner_e:
                raise RuntimeError(f"Ses verisi okunamadı: {str(e)}, İç hata: {str(inner_e)}")

    def _audio_to_bytes(self, audio_array: np.ndarray, sample_rate: int) -> bytes:
        """Numpy dizisini bytes formatına dönüştürür.

        Args:
            audio_array: Ses verisi dizisi
            sample_rate: Örnekleme hızı

        Returns:
            bytes: Bytes formatında ses verisi
        """
        import io
        buf = io.BytesIO()
        sf.write(buf, audio_array, sample_rate, format='WAV')
        return buf.getvalue()

    def _reduce_noise(self, audio_array: np.ndarray, sample_rate: int) -> np.ndarray:
        """Ses verisindeki gürültüyü azaltır.

        Args:
            audio_array: Ses verisi
            sample_rate: Örnekleme hızı

        Returns:
            np.ndarray: Gürültüsü azaltılmış ses verisi
        """
        # Spektral gürültü azaltma
        noise_reduction = 0.1
        freq_threshold = 100

        # FFT uygula
        fft = np.fft.fft(audio_array)
        freqs = np.fft.fftfreq(len(audio_array), 1/sample_rate)

        # Düşük frekanslı gürültüyü azalt
        fft[np.abs(freqs) < freq_threshold] *= (1 - noise_reduction)

        # Ters FFT ile zaman uzayına dön
        return np.real(np.fft.ifft(fft))

    def _normalize_audio(self, audio_array: np.ndarray) -> np.ndarray:
        """Ses verisini normalize eder.

        Args:
            audio_array: Ses verisi

        Returns:
            np.ndarray: Normalize edilmiş ses verisi
        """
        # Peak normalizasyon
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            return audio_array / max_val
        return audio_array

    def preprocess_audio(self, audio_data: bytes) -> bytes:
        """Ses verisini ön işler.

        Şu işlemleri gerçekleştirir:
        1. Gürültü azaltma
        2. Sinyal normalizasyonu
        3. Kalite iyileştirme

        Args:
            audio_data: İşlenecek ses verisi

        Returns:
            bytes: İşlenmiş ses verisi
        """
        try:
            # Bytes -> numpy array dönüşümü
            audio_array, sample_rate = self._bytes_to_audio(audio_data)

            # Gürültü azaltma
            audio_array = self._reduce_noise(audio_array, sample_rate)

            # Normalizasyon
            audio_array = self._normalize_audio(audio_array)

            # Numpy array -> bytes dönüşümü
            return self._audio_to_bytes(audio_array, sample_rate)

        except Exception as e:
            raise RuntimeError(f"Ses ön işleme hatası: {str(e)}")

    def postprocess_audio(self, audio_data: bytes) -> bytes:
        """Üretilen ses verisini son işler.

        Şu işlemleri gerçekleştirir:
        1. Format optimizasyonu
        2. Ses seviyesi ayarlama
        3. Çıktı kalitesi iyileştirme

        Args:
            audio_data: İşlenecek ses verisi

        Returns:
            bytes: İşlenmiş ses verisi
        """
        try:
            # Bytes -> numpy array dönüşümü
            audio_array, sample_rate = self._bytes_to_audio(audio_data)

            # Resample işlemi (eğer gerekirse)
            target_rate = self.config.get("target_sample_rate", 44100)
            if sample_rate != target_rate:
                audio_array = signal.resample(
                    audio_array,
                    int(len(audio_array) * target_rate / sample_rate)
                )
                sample_rate = target_rate

            # Ses seviyesi optimizasyonu
            target_db = self.config.get("target_db", -15)
            current_db = 20 * np.log10(np.max(np.abs(audio_array)))
            if current_db < target_db:
                gain = 10**((target_db - current_db) / 20)
                audio_array *= gain

            # Numpy array -> bytes dönüşümü
            return self._audio_to_bytes(audio_array, sample_rate)

        except Exception as e:
            raise RuntimeError(f"Ses son işleme hatası: {str(e)}")

    async def start_listening(
        self,
        mode: ListeningMode,
        callback: Callable[[str], None]
    ) -> bool:
        """Dinleme modunu başlatır.

        Args:
            mode: Dinleme modu
            callback: Konuşma algılandığında çağrılacak fonksiyon

        Returns:
            bool: Başlatma başarılı ise True
        """
        if self.is_listening:
            logging.warning("Dinleme zaten aktif")
            return False

        self.listening_mode = mode
        self.speech_callback = callback

        try:
            # PyAudio başlat
            if not self.pyaudio_instance:
                self.pyaudio_instance = pyaudio.PyAudio()

            # Wake word detector başlat
            if mode == ListeningMode.WAKE_WORD and self.wake_word_detector:
                await self.wake_word_detector.initialize()
                self.wake_word_detector.set_detection_callback(self._on_wake_word_detected)
                await self.wake_word_detector.start()

            # Sürekli dinleme görevi başlat
            if mode == ListeningMode.CONTINUOUS:
                self.listening_task = asyncio.create_task(self._continuous_listening_loop())

            self.is_listening = True
            logging.info(f"Dinleme başladı: {mode.name}")
            return True

        except Exception as e:
            logging.error(f"Dinleme başlatma hatası: {str(e)}")
            return False

    async def stop_listening(self) -> None:
        """Dinleme modunu durdurur."""
        if not self.is_listening:
            return

        try:
            # Wake word detector durdur
            if self.wake_word_detector:
                await self.wake_word_detector.stop()

            # Dinleme görevini iptal et
            if self.listening_task:
                self.listening_task.cancel()
                try:
                    await self.listening_task
                except asyncio.CancelledError:
                    pass
                self.listening_task = None

            # PyAudio kapat
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None

            self.is_listening = False
            logging.info("Dinleme durduruldu")

        except Exception as e:
            logging.error(f"Dinleme durdurma hatası: {str(e)}")

    def _on_wake_word_detected(self, keyword_index: int) -> None:
        """Wake word algılandığında çağrılır.

        Args:
            keyword_index: Algılanan anahtar kelime indeksi
        """
        logging.info(f"Wake word algılandı: {keyword_index}")

        # Konuşma kaydını başlat
        asyncio.create_task(self._record_after_wake_word())

    async def _record_after_wake_word(self) -> None:
        """Wake word algılandıktan sonra konuşmayı kaydeder."""
        try:
            # Ses kaydı için stream aç
            stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            frames = []
            silence_threshold = self.config.get("silence_threshold", 500)
            silence_duration = self.config.get("silence_duration", 1.5)  # saniye
            max_duration = self.config.get("max_speech_duration", 10)  # saniye

            silence_frames = 0
            max_frames = int(max_duration * self.rate / self.chunk)
            silence_limit = int(silence_duration * self.rate / self.chunk)

            logging.info("Konuşma kaydı başladı")

            # Konuşma bitene kadar kaydet
            for _ in range(max_frames):
                data = stream.read(self.chunk)
                frames.append(data)

                # Sessizlik kontrolü
                if self._is_silence(data, silence_threshold):
                    silence_frames += 1
                    if silence_frames >= silence_limit:
                        logging.info("Sessizlik algılandı, kayıt durduruluyor")
                        break
                else:
                    silence_frames = 0

                await asyncio.sleep(0.01)

            # Stream kapat
            stream.stop_stream()
            stream.close()

            # Ses verisini işle
            if frames:
                audio_data = self._frames_to_audio(frames)

                # Metne dönüştür
                text = await self.speech_to_text(audio_data)

                # Callback fonksiyonunu çağır
                if self.speech_callback and text.strip():
                    self.speech_callback(text)

        except Exception as e:
            logging.error(f"Konuşma kayıt hatası: {str(e)}")

    async def _continuous_listening_loop(self) -> None:
        """Sürekli dinleme döngüsü."""
        try:
            # Ses kaydı için stream aç
            stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            frames = []
            is_speech = False
            silence_threshold = self.config.get("silence_threshold", 500)
            silence_duration = self.config.get("silence_duration", 1.5)  # saniye
            max_duration = self.config.get("max_speech_duration", 10)  # saniye

            silence_frames = 0
            max_frames = int(max_duration * self.rate / self.chunk)
            silence_limit = int(silence_duration * self.rate / self.chunk)

            logging.info("Sürekli dinleme başladı")

            while self.is_listening:
                data = stream.read(self.chunk)

                # Konuşma algılama
                if not is_speech:
                    if not self._is_silence(data, silence_threshold):
                        is_speech = True
                        frames = [data]
                        logging.info("Konuşma başladı")

                # Konuşma kaydı
                elif is_speech:
                    frames.append(data)

                    # Sessizlik kontrolü
                    if self._is_silence(data, silence_threshold):
                        silence_frames += 1
                        if silence_frames >= silence_limit:
                            logging.info("Konuşma bitti")

                            # Ses verisini işle
                            audio_data = self._frames_to_audio(frames)

                            # Metne dönüştür
                            text = await self.speech_to_text(audio_data)

                            # Callback fonksiyonunu çağır
                            if self.speech_callback and text.strip():
                                self.speech_callback(text)

                            # Değişkenleri sıfırla
                            frames = []
                            is_speech = False
                            silence_frames = 0
                    else:
                        silence_frames = 0

                    # Maksimum süre kontrolü
                    if len(frames) >= max_frames:
                        logging.info("Maksimum konuşma süresi aşıldı")

                        # Ses verisini işle
                        audio_data = self._frames_to_audio(frames)

                        # Metne dönüştür
                        text = await self.speech_to_text(audio_data)

                        # Callback fonksiyonunu çağır
                        if self.speech_callback and text.strip():
                            self.speech_callback(text)

                        # Değişkenleri sıfırla
                        frames = []
                        is_speech = False
                        silence_frames = 0

                await asyncio.sleep(0.01)

            # Stream kapat
            stream.stop_stream()
            stream.close()

        except Exception as e:
            logging.error(f"Sürekli dinleme hatası: {str(e)}")
            self.is_listening = False

    def _is_silence(self, audio_data: bytes, threshold: int) -> bool:
        """Ses verisinin sessizlik olup olmadığını kontrol eder.

        Args:
            audio_data: Ses verisi
            threshold: Sessizlik eşiği

        Returns:
            bool: Sessizlik ise True
        """
        # WebRTC VAD kullanılıyorsa
        if self.vad:
            try:
                return not self.vad.is_speech(audio_data, self.rate)
            except:
                pass

        # Basit genlik kontrolü
        try:
            # Bytes -> int16 array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # RMS (Root Mean Square) hesapla
            rms = np.sqrt(np.mean(np.square(audio_array)))

            return rms < threshold
        except:
            return False

    def _frames_to_audio(self, frames: List[bytes]) -> bytes:
        """Ses karelerini birleştirir.

        Args:
            frames: Ses kareleri

        Returns:
            bytes: Birleştirilmiş ses verisi
        """
        # Geçici WAV dosyası oluştur
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

            # WAV dosyasına yaz
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.audio_format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))

            # Dosyayı oku
            with open(temp_path, 'rb') as f:
                audio_data = f.read()

            # Geçici dosyayı sil
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            return audio_data
