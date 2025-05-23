# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Güvenli Yapılandırma Yönetim Modülü

import os
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Set
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..logging_manager import get_logger
from .api_key_manager import APIKeyManager

class SecureConfig:
    """Güvenli yapılandırma yönetimi sınıfı.
    
    Bu sınıf, hassas yapılandırma verilerini güvenli bir şekilde saklar
    ve gerektiğinde çözerek kullanıma sunar.
    """
    
    def __init__(
        self,
        config_path: str,
        encryption_key: Optional[str] = None,
        user_id: str = "default"
    ):
        """SecureConfig başlatıcısı.
        
        Args:
            config_path: Yapılandırma dosyasının yolu
            encryption_key: Şifreleme anahtarı (opsiyonel)
            user_id: Kullanıcı ID'si (varsayılan: "default")
        """
        self.config_path = config_path
        self.user_id = user_id
        self.logger = get_logger("secure_config")
        
        # Yapılandırma dizinini oluştur
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # API anahtarı yöneticisi
        self.api_key_manager = APIKeyManager(
            storage_path=os.path.join(os.path.dirname(config_path), "api_keys"),
            encryption_key=encryption_key,
            user_id=user_id
        )
        
        # Yapılandırma verisi
        self.config: Dict[str, Any] = {}
        
        # Hassas alanlar
        self.sensitive_fields: Set[str] = set()
        
        # Yapılandırmayı yükle
        self._load_config()
    
    def _load_config(self) -> None:
        """Yapılandırmayı yükler."""
        try:
            # Yapılandırma dosyası var mı kontrol et
            if os.path.exists(self.config_path):
                # Yapılandırmayı yükle
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                
                # Hassas alanları belirle
                self.sensitive_fields = set(self.config.get("_sensitive_fields", []))
                
                # Hassas alanları çöz
                for field in self.sensitive_fields:
                    if field in self.config and self.config[field].startswith("encrypted:"):
                        encrypted_value = self.config[field].replace("encrypted:", "", 1)
                        try:
                            self.config[field] = self.api_key_manager.decrypt_key(encrypted_value)
                        except Exception as e:
                            self.logger.error(f"Hassas alan çözme hatası: {field} - {str(e)}")
                
                self.logger.info(f"Yapılandırma yüklendi: {self.config_path}")
            else:
                # Varsayılan yapılandırma
                self.config = {
                    "_sensitive_fields": []
                }
                
                # Yapılandırmayı kaydet
                self._save_config()
                
                self.logger.info(f"Varsayılan yapılandırma oluşturuldu: {self.config_path}")
                
        except Exception as e:
            self.logger.error(f"Yapılandırma yükleme hatası: {str(e)}")
            
            # Varsayılan yapılandırma
            self.config = {
                "_sensitive_fields": []
            }
    
    def _save_config(self) -> bool:
        """Yapılandırmayı kaydeder.
        
        Returns:
            bool: Kaydetme başarılı ise True
        """
        try:
            # Hassas alanları şifrele
            config_to_save = self.config.copy()
            
            # Hassas alanları güncelle
            config_to_save["_sensitive_fields"] = list(self.sensitive_fields)
            
            # Hassas alanları şifrele
            for field in self.sensitive_fields:
                if field in config_to_save and not config_to_save[field].startswith("encrypted:"):
                    try:
                        encrypted_value = self.api_key_manager.encrypt_key(config_to_save[field])
                        config_to_save[field] = f"encrypted:{encrypted_value}"
                    except Exception as e:
                        self.logger.error(f"Hassas alan şifreleme hatası: {field} - {str(e)}")
            
            # Yapılandırmayı kaydet
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            
            # Dosya izinlerini ayarla (sadece sahibi okuyabilir)
            os.chmod(self.config_path, 0o600)
            
            self.logger.info(f"Yapılandırma kaydedildi: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Yapılandırma kaydetme hatası: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Yapılandırma değerini getirir.
        
        Args:
            key: Yapılandırma anahtarı
            default: Varsayılan değer (opsiyonel)
            
        Returns:
            Any: Yapılandırma değeri
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, sensitive: bool = False) -> bool:
        """Yapılandırma değerini ayarlar.
        
        Args:
            key: Yapılandırma anahtarı
            value: Yapılandırma değeri
            sensitive: Hassas alan mı (varsayılan: False)
            
        Returns:
            bool: Ayarlama başarılı ise True
        """
        try:
            # Değeri ayarla
            self.config[key] = value
            
            # Hassas alan ise işaretle
            if sensitive and key != "_sensitive_fields":
                self.sensitive_fields.add(key)
            elif not sensitive and key in self.sensitive_fields:
                self.sensitive_fields.remove(key)
            
            # Yapılandırmayı kaydet
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Yapılandırma değeri ayarlama hatası: {key} - {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Yapılandırma değerini siler.
        
        Args:
            key: Yapılandırma anahtarı
            
        Returns:
            bool: Silme başarılı ise True
        """
        try:
            # Değeri sil
            if key in self.config:
                del self.config[key]
            
            # Hassas alan ise işareti kaldır
            if key in self.sensitive_fields:
                self.sensitive_fields.remove(key)
            
            # Yapılandırmayı kaydet
            return self._save_config()
            
        except Exception as e:
            self.logger.error(f"Yapılandırma değeri silme hatası: {key} - {str(e)}")
            return False
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """API anahtarını getirir.
        
        Args:
            service_name: Servis adı
            
        Returns:
            Optional[str]: API anahtarı, yoksa None
        """
        return self.api_key_manager.get_key(service_name)
    
    def set_api_key(self, service_name: str, api_key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """API anahtarını ayarlar.
        
        Args:
            service_name: Servis adı
            api_key: API anahtarı
            metadata: Ek meta veriler (opsiyonel)
            
        Returns:
            bool: Ayarlama başarılı ise True
        """
        return self.api_key_manager.save_key(service_name, api_key, metadata)
    
    def delete_api_key(self, service_name: str) -> bool:
        """API anahtarını siler.
        
        Args:
            service_name: Servis adı
            
        Returns:
            bool: Silme başarılı ise True
        """
        return self.api_key_manager.delete_key(service_name)
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """Kayıtlı API anahtarlarını listeler.
        
        Returns:
            List[Dict[str, Any]]: API anahtarı meta verileri listesi
        """
        return self.api_key_manager.list_keys()
    
    def get_all(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Tüm yapılandırma değerlerini getirir.
        
        Args:
            include_sensitive: Hassas alanları dahil et (varsayılan: False)
            
        Returns:
            Dict[str, Any]: Yapılandırma değerleri
        """
        if include_sensitive:
            return self.config.copy()
        else:
            # Hassas alanları hariç tut
            return {k: v for k, v in self.config.items() if k != "_sensitive_fields" and k not in self.sensitive_fields}
    
    def is_sensitive(self, key: str) -> bool:
        """Alanın hassas olup olmadığını kontrol eder.
        
        Args:
            key: Yapılandırma anahtarı
            
        Returns:
            bool: Hassas alan ise True
        """
        return key in self.sensitive_fields
