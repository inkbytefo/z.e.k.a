# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Veri Güvenliği Modülü

import os
import re
import asyncio
import base64
import hashlib
import hmac
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime, timedelta

class EncryptionManager:
    """Şifreleme işlemleri için yönetici sınıf."""
    
    def __init__(self, config: Dict[str, Any]):
        """EncryptionManager başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.key_dir = config.get("key_dir", "keys")
        self.salt = os.urandom(16)
        
        # Anahtar dizinini oluştur
        os.makedirs(self.key_dir, exist_ok=True)
        
        # Master anahtarı yükle veya oluştur
        self.master_key = self._load_or_create_master_key()
        
        # Simetrik şifreleme için Fernet
        self.fernet = Fernet(self.master_key)
        
        # Asimetrik anahtar çifti
        self.private_key, self.public_key = self._load_or_create_key_pair()
        
        # AESGCM için anahtar
        self.aes_key = AESGCM.generate_key(bit_length=256)
    
    def _load_or_create_master_key(self) -> bytes:
        """Master anahtarı yükler veya oluşturur."""
        key_path = os.path.join(self.key_dir, "master.key")
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        
        # Yeni anahtar oluştur
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
        
        # Anahtarı kaydet
        with open(key_path, "wb") as f:
            f.write(key)
        
        return key
    
    def _load_or_create_key_pair(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """RSA anahtar çiftini yükler veya oluşturur."""
        private_path = os.path.join(self.key_dir, "private.pem")
        public_path = os.path.join(self.key_dir, "public.pem")
        
        if os.path.exists(private_path) and os.path.exists(public_path):
            # Mevcut anahtarları yükle
            with open(private_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            
            with open(public_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())
            
            return private_key, public_key
        
        # Yeni anahtar çifti oluştur
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Anahtarları kaydet
        with open(private_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        with open(public_path, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        return private_key, public_key
    
    def encrypt_symmetric(self, data: Union[str, bytes]) -> bytes:
        """Simetrik şifreleme yapar.
        
        Args:
            data: Şifrelenecek veri
            
        Returns:
            bytes: Şifrelenmiş veri
        """
        if isinstance(data, str):
            data = data.encode()
        return self.fernet.encrypt(data)
    
    def decrypt_symmetric(self, encrypted_data: bytes) -> bytes:
        """Simetrik şifre çözme yapar.
        
        Args:
            encrypted_data: Şifreli veri
            
        Returns:
            bytes: Çözülmüş veri
        """
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_asymmetric(self, data: Union[str, bytes]) -> bytes:
        """Asimetrik şifreleme yapar.
        
        Args:
            data: Şifrelenecek veri
            
        Returns:
            bytes: Şifrelenmiş veri
        """
        if isinstance(data, str):
            data = data.encode()
        
        return self.public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_asymmetric(self, encrypted_data: bytes) -> bytes:
        """Asimetrik şifre çözme yapar.
        
        Args:
            encrypted_data: Şifreli veri
            
        Returns:
            bytes: Çözülmüş veri
        """
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def aes_encrypt(self, data: Union[str, bytes], aad: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """AESGCM ile şifreleme yapar.
        
        Args:
            data: Şifrelenecek veri
            aad: Ek doğrulama verisi
            
        Returns:
            Tuple[bytes, bytes]: Nonce ve şifreli veri
        """
        if isinstance(data, str):
            data = data.encode()
        
        aesgcm = AESGCM(self.aes_key)
        nonce = os.urandom(12)
        
        encrypted_data = aesgcm.encrypt(nonce, data, aad)
        return nonce, encrypted_data
    
    def aes_decrypt(
        self,
        nonce: bytes,
        encrypted_data: bytes,
        aad: Optional[bytes] = None
    ) -> bytes:
        """AESGCM ile şifre çözme yapar.
        
        Args:
            nonce: Şifreleme nonce'u
            encrypted_data: Şifreli veri
            aad: Ek doğrulama verisi
            
        Returns:
            bytes: Çözülmüş veri
        """
        aesgcm = AESGCM(self.aes_key)
        return aesgcm.decrypt(nonce, encrypted_data, aad)

class SessionManager:
    """Oturum yönetimi için sınıf."""
    
    def __init__(self, config: Dict[str, Any]):
        """SessionManager başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = config.get("session_timeout", 3600)  # 1 saat
        
        # Otomatik temizlik için task
        self._cleanup_task = None
    
    def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Yeni oturum oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            metadata: Ek meta veriler
            
        Returns:
            str: Oturum ID'si
        """
        session_id = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_access": datetime.now(),
            "metadata": metadata or {}
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Oturum geçerliliğini kontrol eder.
        
        Args:
            session_id: Oturum ID'si
            
        Returns:
            bool: Oturum geçerli ise True
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Zaman aşımı kontrolü
        if (datetime.now() - session["last_access"]).total_seconds() > self.session_timeout:
            del self.sessions[session_id]
            return False
        
        # Son erişim zamanını güncelle
        session["last_access"] = datetime.now()
        return True
    
    def end_session(self, session_id: str) -> bool:
        """Oturumu sonlandırır.
        
        Args:
            session_id: Oturum ID'si
            
        Returns:
            bool: İşlem başarılı ise True
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def _cleanup_expired_sessions(self) -> None:
        """Süresi dolmuş oturumları temizler."""
        while True:
            current_time = datetime.now()
            expired_sessions = [
                sid for sid, session in self.sessions.items()
                if (current_time - session["last_access"]).total_seconds() > self.session_timeout
            ]
            
            for sid in expired_sessions:
                del self.sessions[sid]
            
            await asyncio.sleep(60)  # Her dakika kontrol et

class DataAnonymizer:
    """Veri anonimleştirme için sınıf."""
    
    def __init__(self, config: Dict[str, Any]):
        """DataAnonymizer başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.patterns = config.get("anonymization_patterns", {})
    
    def detect_sensitive_data(self, data: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Hassas verileri tespit eder.
        
        Args:
            data: İncelenecek veri
            
        Returns:
            List[Dict[str, Any]]: Tespit edilen hassas veriler
        """
        findings = []
        
        if isinstance(data, str):
            text = data
        else:
            text = json.dumps(data)
        
        for pattern_name, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    "type": pattern_name,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return findings
    
    def anonymize_data(
        self,
        data: Union[str, Dict[str, Any]],
        mask_char: str = "*"
    ) -> Union[str, Dict[str, Any]]:
        """Hassas verileri anonimleştirir.
        
        Args:
            data: Anonimleştirilecek veri
            mask_char: Maskeleme karakteri
            
        Returns:
            Union[str, Dict[str, Any]]: Anonimleştirilmiş veri
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result[key] = self.anonymize_data(value, mask_char)
                else:
                    result[key] = self._mask_sensitive_data(str(value), mask_char)
            return result
            
        elif isinstance(data, list):
            return [self.anonymize_data(item, mask_char) for item in data]
            
        else:
            return self._mask_sensitive_data(str(data), mask_char)
    
    def _mask_sensitive_data(self, text: str, mask_char: str) -> str:
        """Hassas verileri maskeler.
        
        Args:
            text: Maskelenecek metin
            mask_char: Maskeleme karakteri
            
        Returns:
            str: Maskelenmiş metin
        """
        findings = self.detect_sensitive_data(text)
        
        # Sondan başa doğru değiştir (indeks kayması olmasın)
        for finding in reversed(findings):
            mask_length = finding["end"] - finding["start"]
            text = (
                text[:finding["start"]] +
                mask_char * mask_length +
                text[finding["end"]:]
            )
        
        return text

class DataSecurityManager:
    """Veri güvenliği yönetimi için ana sınıf."""
    
    def __init__(self, config: Dict[str, Any]):
        """DataSecurityManager başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        
        # Alt bileşenler
        self.encryption = EncryptionManager(config)
        self.session = SessionManager(config)
        self.anonymizer = DataAnonymizer(config)
    
    def secure_data(
        self,
        data: Union[str, Dict[str, Any]],
        encryption_type: str = "symmetric",
        anonymize: bool = True
    ) -> Dict[str, Any]:
        """Veriyi güvenli hale getirir.
        
        Args:
            data: Güvenli hale getirilecek veri
            encryption_type: Şifreleme tipi
            anonymize: Anonimleştirme yapılsın mı
            
        Returns:
            Dict[str, Any]: Güvenli veri
        """
        # Önce anonimleştir
        if anonymize:
            data = self.anonymizer.anonymize_data(data)
        
        # Sonra şifrele
        if encryption_type == "symmetric":
            encrypted = self.encryption.encrypt_symmetric(
                json.dumps(data) if isinstance(data, dict) else data
            )
        elif encryption_type == "asymmetric":
            encrypted = self.encryption.encrypt_asymmetric(
                json.dumps(data) if isinstance(data, dict) else data
            )
        elif encryption_type == "aes":
            nonce, encrypted = self.encryption.aes_encrypt(
                json.dumps(data) if isinstance(data, dict) else data
            )
            return {
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "encrypted_data": base64.b64encode(encrypted).decode('utf-8'),
                "encryption_type": encryption_type
            }
        else:
            raise ValueError(f"Desteklenmeyen şifreleme tipi: {encryption_type}")
        
        return {
            "encrypted_data": base64.b64encode(encrypted).decode('utf-8'),
            "encryption_type": encryption_type
        }
    
    def restore_data(
        self,
        secure_data: Dict[str, Any],
        as_json: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """Güvenli veriyi geri yükler.
        
        Args:
            secure_data: Güvenli veri
            as_json: JSON olarak parse edilsin mi
            
        Returns:
            Union[str, Dict[str, Any]]: Geri yüklenmiş veri
        """
        encryption_type = secure_data["encryption_type"]
        encrypted = base64.b64decode(secure_data["encrypted_data"])
        
        if encryption_type == "symmetric":
            decrypted = self.encryption.decrypt_symmetric(encrypted)
        elif encryption_type == "asymmetric":
            decrypted = self.encryption.decrypt_asymmetric(encrypted)
        elif encryption_type == "aes":
            nonce = base64.b64decode(secure_data["nonce"])
            decrypted = self.encryption.aes_decrypt(nonce, encrypted)
        else:
            raise ValueError(f"Desteklenmeyen şifreleme tipi: {encryption_type}")
        
        if as_json:
            try:
                return json.loads(decrypted)
            except:
                pass
        
        return decrypted.decode() if isinstance(decrypted, bytes) else decrypted
