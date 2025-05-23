# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# API Anahtarı Yönetim Modülü

import os
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..logging_manager import get_logger

class APIKeyManager:
    """API anahtarlarını güvenli bir şekilde yöneten sınıf.
    
    Bu sınıf, API anahtarlarını şifreleyerek güvenli bir şekilde saklar
    ve gerektiğinde çözerek kullanıma sunar.
    """
    
    def __init__(
        self,
        storage_path: str,
        encryption_key: Optional[str] = None,
        salt: Optional[bytes] = None,
        user_id: str = "default"
    ):
        """APIKeyManager başlatıcısı.
        
        Args:
            storage_path: API anahtarlarının saklanacağı dizin
            encryption_key: Şifreleme anahtarı (opsiyonel)
            salt: Şifreleme tuzu (opsiyonel)
            user_id: Kullanıcı ID'si (varsayılan: "default")
        """
        self.storage_path = storage_path
        self.user_id = user_id
        self.logger = get_logger("api_key_manager")
        
        # Depolama dizinini oluştur
        os.makedirs(storage_path, exist_ok=True)
        
        # Kullanıcı dizinini oluştur
        self.user_path = os.path.join(storage_path, user_id)
        os.makedirs(self.user_path, exist_ok=True)
        
        # Şifreleme anahtarını ayarla
        self.encryption_key = self._setup_encryption_key(encryption_key)
        
        # Şifreleme tuzu
        self.salt = salt or os.urandom(16)
        
        # Fernet şifreleme nesnesi
        self.cipher = Fernet(self.encryption_key)
        
        # Anahtar önbelleği
        self._key_cache: Dict[str, str] = {}
    
    def _setup_encryption_key(self, encryption_key: Optional[str] = None) -> bytes:
        """Şifreleme anahtarını ayarlar.
        
        Args:
            encryption_key: Şifreleme anahtarı (opsiyonel)
            
        Returns:
            bytes: Şifreleme anahtarı
        """
        # Çevre değişkeninden al
        env_key = os.getenv("ENCRYPTION_KEY")
        
        if encryption_key:
            # Verilen anahtarı kullan
            key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        elif env_key:
            # Çevre değişkenindeki anahtarı kullan
            key = env_key.encode()
        else:
            # Anahtar dosyasını kontrol et
            key_file = os.path.join(self.storage_path, ".encryption_key")
            
            if os.path.exists(key_file):
                # Anahtar dosyasından oku
                with open(key_file, "rb") as f:
                    key = f.read().strip()
            else:
                # Yeni anahtar oluştur
                key = Fernet.generate_key()
                
                # Anahtar dosyasına kaydet
                with open(key_file, "wb") as f:
                    f.write(key)
                
                # Dosya izinlerini ayarla (sadece sahibi okuyabilir)
                os.chmod(key_file, 0o600)
        
        # Anahtar formatını kontrol et
        try:
            # Base64 formatında mı?
            if len(key) != 32 and len(base64.urlsafe_b64decode(key + b"=" * (-len(key) % 4))) == 32:
                return key
            
            # PBKDF2 ile anahtar türet
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key))
            return derived_key
            
        except Exception:
            # Geçersiz anahtar, yeni oluştur
            self.logger.warning("Geçersiz şifreleme anahtarı, yeni anahtar oluşturuluyor")
            return Fernet.generate_key()
    
    def encrypt_key(self, api_key: str) -> str:
        """API anahtarını şifreler.
        
        Args:
            api_key: Şifrelenecek API anahtarı
            
        Returns:
            str: Şifrelenmiş API anahtarı
        """
        try:
            # API anahtarını şifrele
            encrypted_key = self.cipher.encrypt(api_key.encode())
            
            # Base64 formatına dönüştür
            return base64.urlsafe_b64encode(encrypted_key).decode()
            
        except Exception as e:
            self.logger.error(f"API anahtarı şifreleme hatası: {str(e)}")
            raise
    
    def decrypt_key(self, encrypted_key: str) -> str:
        """Şifrelenmiş API anahtarını çözer.
        
        Args:
            encrypted_key: Şifrelenmiş API anahtarı
            
        Returns:
            str: Çözülmüş API anahtarı
        """
        try:
            # Base64 formatından dönüştür
            encrypted_data = base64.urlsafe_b64decode(encrypted_key)
            
            # API anahtarını çöz
            decrypted_key = self.cipher.decrypt(encrypted_data)
            
            return decrypted_key.decode()
            
        except Exception as e:
            self.logger.error(f"API anahtarı çözme hatası: {str(e)}")
            raise
    
    def save_key(self, service_name: str, api_key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """API anahtarını kaydeder.
        
        Args:
            service_name: Servis adı
            api_key: API anahtarı
            metadata: Ek meta veriler (opsiyonel)
            
        Returns:
            bool: Kaydetme başarılı ise True
        """
        try:
            # API anahtarını şifrele
            encrypted_key = self.encrypt_key(api_key)
            
            # Meta verileri hazırla
            metadata = metadata or {}
            metadata.update({
                "service": service_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
            # Anahtar verilerini hazırla
            key_data = {
                "encrypted_key": encrypted_key,
                "metadata": metadata
            }
            
            # Anahtar dosyasını kaydet
            key_file = os.path.join(self.user_path, f"{service_name}.json")
            with open(key_file, "w", encoding="utf-8") as f:
                json.dump(key_data, f, ensure_ascii=False, indent=2)
            
            # Dosya izinlerini ayarla (sadece sahibi okuyabilir)
            os.chmod(key_file, 0o600)
            
            # Önbelleğe ekle
            self._key_cache[service_name] = api_key
            
            self.logger.info(f"API anahtarı kaydedildi: {service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"API anahtarı kaydetme hatası: {str(e)}")
            return False
    
    def get_key(self, service_name: str) -> Optional[str]:
        """API anahtarını getirir.
        
        Args:
            service_name: Servis adı
            
        Returns:
            Optional[str]: API anahtarı, yoksa None
        """
        # Önbellekte var mı kontrol et
        if service_name in self._key_cache:
            return self._key_cache[service_name]
        
        try:
            # Anahtar dosyasını kontrol et
            key_file = os.path.join(self.user_path, f"{service_name}.json")
            
            if not os.path.exists(key_file):
                return None
            
            # Anahtar verilerini yükle
            with open(key_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            
            # API anahtarını çöz
            encrypted_key = key_data["encrypted_key"]
            api_key = self.decrypt_key(encrypted_key)
            
            # Önbelleğe ekle
            self._key_cache[service_name] = api_key
            
            return api_key
            
        except Exception as e:
            self.logger.error(f"API anahtarı getirme hatası: {str(e)}")
            return None
    
    def delete_key(self, service_name: str) -> bool:
        """API anahtarını siler.
        
        Args:
            service_name: Servis adı
            
        Returns:
            bool: Silme başarılı ise True
        """
        try:
            # Anahtar dosyasını kontrol et
            key_file = os.path.join(self.user_path, f"{service_name}.json")
            
            if not os.path.exists(key_file):
                return False
            
            # Anahtar dosyasını sil
            os.remove(key_file)
            
            # Önbellekten çıkar
            if service_name in self._key_cache:
                del self._key_cache[service_name]
            
            self.logger.info(f"API anahtarı silindi: {service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"API anahtarı silme hatası: {str(e)}")
            return False
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """Kayıtlı API anahtarlarını listeler.
        
        Returns:
            List[Dict[str, Any]]: API anahtarı meta verileri listesi
        """
        try:
            # Anahtar dosyalarını bul
            key_files = [f for f in os.listdir(self.user_path) if f.endswith(".json")]
            
            # Meta verileri topla
            keys_metadata = []
            
            for key_file in key_files:
                try:
                    # Anahtar verilerini yükle
                    with open(os.path.join(self.user_path, key_file), "r", encoding="utf-8") as f:
                        key_data = json.load(f)
                    
                    # Servis adını al
                    service_name = key_file.replace(".json", "")
                    
                    # Meta verileri ekle
                    metadata = key_data.get("metadata", {})
                    metadata["service"] = service_name
                    
                    keys_metadata.append(metadata)
                    
                except Exception as e:
                    self.logger.error(f"Anahtar meta verisi yükleme hatası: {key_file} - {str(e)}")
            
            return keys_metadata
            
        except Exception as e:
            self.logger.error(f"API anahtarları listeleme hatası: {str(e)}")
            return []
    
    def update_key(self, service_name: str, api_key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """API anahtarını günceller.
        
        Args:
            service_name: Servis adı
            api_key: Yeni API anahtarı
            metadata: Ek meta veriler (opsiyonel)
            
        Returns:
            bool: Güncelleme başarılı ise True
        """
        try:
            # Anahtar dosyasını kontrol et
            key_file = os.path.join(self.user_path, f"{service_name}.json")
            
            if not os.path.exists(key_file):
                # Anahtar yoksa yeni oluştur
                return self.save_key(service_name, api_key, metadata)
            
            # Mevcut meta verileri yükle
            with open(key_file, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            
            # API anahtarını şifrele
            encrypted_key = self.encrypt_key(api_key)
            
            # Meta verileri güncelle
            current_metadata = key_data.get("metadata", {})
            if metadata:
                current_metadata.update(metadata)
            
            current_metadata["updated_at"] = datetime.now().isoformat()
            
            # Anahtar verilerini güncelle
            key_data["encrypted_key"] = encrypted_key
            key_data["metadata"] = current_metadata
            
            # Anahtar dosyasını kaydet
            with open(key_file, "w", encoding="utf-8") as f:
                json.dump(key_data, f, ensure_ascii=False, indent=2)
            
            # Önbelleği güncelle
            self._key_cache[service_name] = api_key
            
            self.logger.info(f"API anahtarı güncellendi: {service_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"API anahtarı güncelleme hatası: {str(e)}")
            return False
