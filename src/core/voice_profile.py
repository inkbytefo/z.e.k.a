# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ses Profili Modülü

from dataclasses import dataclass
from typing import Optional

@dataclass
class VoiceProfile:
    """Ses profili veri sınıfı.
    
    Bu sınıf, bir kullanıcının ses tercihlerini ve
    ayarlarını tutar. ElevenLabs ve diğer ses servisleri
    için gerekli yapılandırmayı sağlar.
    """
    
    # Temel bilgiler
    voice_id: str
    name: str
    language: str
    accent: Optional[str] = None
    gender: Optional[str] = None
    
    # ElevenLabs ses ayarları
    stability: float = 0.71
    similarity_boost: float = 0.5
    style: float = 0.0
    use_speaker_boost: bool = True
    
    # Hız ve ton ayarları
    speaking_rate: float = 1.0
    pitch: float = 0.0
    
    # Ses aktivasyon ayarları
    wake_word: Optional[str] = None
    activation_threshold: float = 0.5
    
    def to_dict(self) -> dict:
        """Profili sözlük formatına dönüştürür.
        
        Returns:
            dict: Profil verisi
        """
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "language": self.language,
            "accent": self.accent,
            "gender": self.gender,
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "use_speaker_boost": self.use_speaker_boost,
            "speaking_rate": self.speaking_rate,
            "pitch": self.pitch,
            "wake_word": self.wake_word,
            "activation_threshold": self.activation_threshold
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        """Sözlük verisinden profil oluşturur.
        
        Args:
            data: Profil verisi
            
        Returns:
            VoiceProfile: Oluşturulan profil
        """
        return cls(**data)
        
    def update(self, **kwargs) -> None:
        """Profil ayarlarını günceller.
        
        Args:
            **kwargs: Güncellenecek alanlar
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def validate(self) -> bool:
        """Profil ayarlarının geçerliliğini kontrol eder.
        
        Returns:
            bool: Profil geçerli mi
        """
        # Gerekli alanların kontrolü
        if not self.voice_id or not self.name or not self.language:
            return False
            
        # Değer aralığı kontrolleri
        if not (0.0 <= self.stability <= 1.0):
            return False
        if not (0.0 <= self.similarity_boost <= 1.0):
            return False
        if not (0.0 <= self.style <= 1.0):
            return False
        if not (0.5 <= self.speaking_rate <= 2.0):
            return False
        if not (-1.0 <= self.pitch <= 1.0):
            return False
        if not (0.0 <= self.activation_threshold <= 1.0):
            return False
            
        return True
