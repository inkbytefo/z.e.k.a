# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ses Önbellekleme Modülü

from typing import Dict, Any, Optional, Tuple, List
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
import numpy as np
import soundfile as sf
from pathlib import Path

class VoiceCache:
    """Ses verilerinin önbelleklenmesi için sınıf.
    
    Bu sınıf, sık kullanılan ses komutları ve yanıtlarının
    önbelleklenmesini sağlar. Önbellek yönetimi ve temizleme
    stratejilerini içerir.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """VoiceCache başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.cache_dir = Path(config.get("cache_dir", "voice_cache"))
        self.max_cache_size = config.get("max_cache_size", 1024 * 1024 * 1024)  # 1GB
        self.max_entry_age = config.get("max_entry_age", 7 * 24 * 60 * 60)  # 7 gün
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata: Dict[str, Any] = {}
        
        # Önbellek dizinini oluştur
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata dosyasını yükle
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Önbellek metadata dosyasını yükler."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
        except Exception as e:
            print(f"Metadata yükleme hatası: {str(e)}")
            self.metadata = {}
    
    def _save_metadata(self) -> None:
        """Önbellek metadata dosyasını kaydeder."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Metadata kaydetme hatası: {str(e)}")
    
    def _generate_key(self, text: str, voice_id: Optional[str] = None) -> str:
        """Önbellek anahtarı oluşturur.
        
        Args:
            text: Ses verisinin metni
            voice_id: Ses profili ID'si
            
        Returns:
            str: Önbellek anahtarı
        """
        key_data = text
        if voice_id:
            key_data += voice_id
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Önbellek dosya yolunu döndürür.
        
        Args:
            key: Önbellek anahtarı
            
        Returns:
            Path: Dosya yolu
        """
        return self.cache_dir / f"{key}.wav"
    
    def _get_total_cache_size(self) -> int:
        """Toplam önbellek boyutunu hesaplar.
        
        Returns:
            int: Toplam boyut (byte)
        """
        total_size = 0
        for entry in self.metadata.values():
            cache_path = self._get_cache_path(entry["key"])
            if cache_path.exists():
                total_size += cache_path.stat().st_size
        return total_size
    
    def _clean_cache(self, required_space: int = 0) -> None:
        """Önbelleği temizler.
        
        Args:
            required_space: Gerekli boş alan (byte)
        """
        # Eski girişleri temizle
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.metadata.items()
            if current_time - entry["last_access"] > self.max_entry_age
        ]
        
        for key in expired_keys:
            self.remove(key)
        
        # Boyut limitini aşıyorsa en az kullanılanları sil
        if required_space > 0:
            total_size = self._get_total_cache_size()
            if total_size + required_space > self.max_cache_size:
                # En az kullanılan girişleri bul
                entries = [
                    (key, entry) for key, entry in self.metadata.items()
                ]
                entries.sort(key=lambda x: (
                    x[1]["access_count"],
                    x[1]["last_access"]
                ))
                
                # Gerekli alan açılana kadar sil
                freed_space = 0
                for key, entry in entries:
                    cache_path = self._get_cache_path(entry["key"])
                    if cache_path.exists():
                        freed_space += cache_path.stat().st_size
                        self.remove(key)
                    
                    if freed_space >= required_space:
                        break
    
    def put(
        self,
        text: str,
        audio_data: bytes,
        voice_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Ses verisini önbelleğe ekler.
        
        Args:
            text: Ses verisinin metni
            audio_data: Ses verisi
            voice_id: Ses profili ID'si
            metadata: Ek metadata
            
        Returns:
            str: Önbellek anahtarı
        """
        key = self._generate_key(text, voice_id)
        cache_path = self._get_cache_path(key)
        
        try:
            # Dosya boyutunu kontrol et ve gerekirse temizlik yap
            audio_size = len(audio_data)
            self._clean_cache(audio_size)
            
            # Ses verisini kaydet
            with open(cache_path, "wb") as f:
                f.write(audio_data)
            
            # Metadata güncelle
            self.metadata[key] = {
                "key": key,
                "text": text,
                "voice_id": voice_id,
                "created_at": time.time(),
                "last_access": time.time(),
                "access_count": 0,
                "size": audio_size,
                "custom_metadata": metadata or {}
            }
            
            self._save_metadata()
            return key
            
        except Exception as e:
            print(f"Önbelleğe ekleme hatası: {str(e)}")
            if cache_path.exists():
                cache_path.unlink()
            return ""
    
    def get(
        self,
        text: str,
        voice_id: Optional[str] = None
    ) -> Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
        """Ses verisini önbellekten alır.
        
        Args:
            text: Ses verisinin metni
            voice_id: Ses profili ID'si
            
        Returns:
            Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
            Ses verisi ve metadata
        """
        key = self._generate_key(text, voice_id)
        cache_path = self._get_cache_path(key)
        
        if key in self.metadata and cache_path.exists():
            try:
                # Ses verisini oku
                with open(cache_path, "rb") as f:
                    audio_data = f.read()
                
                # Metadata güncelle
                self.metadata[key].update({
                    "last_access": time.time(),
                    "access_count": self.metadata[key]["access_count"] + 1
                })
                
                self._save_metadata()
                return audio_data, self.metadata[key]
                
            except Exception as e:
                print(f"Önbellekten okuma hatası: {str(e)}")
        
        return None, None
    
    def remove(self, key: str) -> bool:
        """Önbellekten veri siler.
        
        Args:
            key: Önbellek anahtarı
            
        Returns:
            bool: Silme başarılı ise True
        """
        if key in self.metadata:
            cache_path = self._get_cache_path(key)
            
            try:
                if cache_path.exists():
                    cache_path.unlink()
                
                del self.metadata[key]
                self._save_metadata()
                return True
                
            except Exception as e:
                print(f"Önbellekten silme hatası: {str(e)}")
        
        return False
    
    def clear(self) -> bool:
        """Tüm önbelleği temizler.
        
        Returns:
            bool: Temizleme başarılı ise True
        """
        try:
            # Tüm önbellek dosyalarını sil
            for cache_file in self.cache_dir.glob("*.wav"):
                cache_file.unlink()
            
            # Metadata'yı sıfırla
            self.metadata = {}
            self._save_metadata()
            return True
            
        except Exception as e:
            print(f"Önbellek temizleme hatası: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Önbellek istatistiklerini döndürür.
        
        Returns:
            Dict[str, Any]: İstatistikler
        """
        total_size = self._get_total_cache_size()
        entry_count = len(self.metadata)
        
        # Yaş dağılımı
        current_time = time.time()
        age_distribution = {
            "1_day": 0,
            "7_days": 0,
            "30_days": 0,
            "older": 0
        }
        
        for entry in self.metadata.values():
            age = current_time - entry["created_at"]
            if age < 24 * 60 * 60:
                age_distribution["1_day"] += 1
            elif age < 7 * 24 * 60 * 60:
                age_distribution["7_days"] += 1
            elif age < 30 * 24 * 60 * 60:
                age_distribution["30_days"] += 1
            else:
                age_distribution["older"] += 1
        
        # Kullanım dağılımı
        usage_counts = [
            entry["access_count"]
            for entry in self.metadata.values()
        ]
        
        return {
            "total_size": total_size,
            "entry_count": entry_count,
            "age_distribution": age_distribution,
            "avg_access_count": np.mean(usage_counts) if usage_counts else 0,
            "max_access_count": max(usage_counts) if usage_counts else 0
        }
