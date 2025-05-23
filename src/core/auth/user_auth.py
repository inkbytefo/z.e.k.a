# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kullanıcı Kimlik Doğrulama Modülü

import os
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple

from .auth_utils import get_password_hash, verify_password, invalidate_all_user_tokens
from ..security.password_policy import PasswordPolicy

class UserAuth:
    """Kullanıcı kimlik doğrulama yöneticisi.

    Bu sınıf, kullanıcı hesaplarını yönetir ve kimlik doğrulama işlemlerini gerçekleştirir.
    """

    def __init__(self, storage_path: str = "./data/users"):
        """Kullanıcı kimlik doğrulama yöneticisi başlatıcısı.

        Args:
            storage_path: Kullanıcı verilerinin depolanacağı dizin yolu
        """
        self.storage_path = storage_path
        self.ensure_storage_exists()
        self.logger = logging.getLogger("user_auth")

        # Şifre politikası
        self.password_policy = PasswordPolicy(
            min_length=10,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special=True,
            min_unique_chars=5,
            max_sequential_chars=3,
            max_repeated_chars=3,
            check_common_passwords=True
        )

    def ensure_storage_exists(self):
        """Depolama dizininin var olduğundan emin olur."""
        os.makedirs(self.storage_path, exist_ok=True)

    def get_user_path(self, username: str) -> str:
        """Kullanıcı dosyası yolunu döndürür.

        Args:
            username: Kullanıcı adı

        Returns:
            str: Kullanıcı dosyası yolu
        """
        return os.path.join(self.storage_path, f"{username}.json")

    def user_exists(self, username: str) -> bool:
        """Kullanıcının var olup olmadığını kontrol eder.

        Args:
            username: Kullanıcı adı

        Returns:
            bool: Kullanıcı varsa True
        """
        user_path = self.get_user_path(username)
        return os.path.exists(user_path)

    def create_user(self, username: str, password: str, email: str, full_name: str = "") -> Tuple[bool, Optional[List[str]]]:
        """Yeni kullanıcı oluşturur.

        Args:
            username: Kullanıcı adı
            password: Şifre
            email: E-posta adresi
            full_name: Tam ad (opsiyonel)

        Returns:
            Tuple[bool, Optional[List[str]]]: (Başarılıysa True, Hata mesajları)

        Raises:
            ValueError: Kullanıcı zaten varsa
        """
        if self.user_exists(username):
            raise ValueError(f"Kullanıcı zaten var: {username}")

        # Kullanıcı adı geçerliliğini kontrol et
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            return False, ["Kullanıcı adı 3-20 karakter uzunluğunda olmalı ve sadece harf, rakam ve alt çizgi içermelidir"]

        # E-posta geçerliliğini kontrol et
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return False, ["Geçerli bir e-posta adresi giriniz"]

        # Şifre politikasını kontrol et
        is_valid, errors = self.password_policy.validate_password(password)
        if not is_valid:
            return False, errors

        # Şifreyi hashle
        hashed_password = get_password_hash(password)

        # Kullanıcı verilerini oluştur
        user_data = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "failed_login_attempts": 0,
            "last_failed_login": None,
            "account_locked_until": None,
            "password_last_changed": datetime.now(timezone.utc).isoformat(),
            "password_history": [],  # Önceki şifrelerin hash'leri
            "security_questions": [],  # Güvenlik soruları ve cevapları
            "two_factor_enabled": False,  # İki faktörlü kimlik doğrulama
            "two_factor_method": None,  # İki faktörlü kimlik doğrulama yöntemi
            "two_factor_secret": None,  # İki faktörlü kimlik doğrulama sırrı
            "recovery_codes": [],  # Kurtarma kodları
            "last_ip": None,  # Son giriş IP adresi
            "known_ips": [],  # Bilinen IP adresleri
            "user_agent": None,  # Son giriş kullanıcı ajanı
            "login_history": []  # Giriş geçmişi
        }

        # Kullanıcı verilerini kaydet
        user_path = self.get_user_path(username)
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

        # Dosya izinlerini ayarla (sadece sahibi okuyabilir)
        os.chmod(user_path, 0o600)

        self.logger.info(f"Yeni kullanıcı oluşturuldu: {username}")
        return True, None

    def authenticate_user(self, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Kullanıcıyı doğrular.

        Args:
            username: Kullanıcı adı
            password: Şifre
            ip_address: IP adresi (opsiyonel)
            user_agent: Kullanıcı ajanı (opsiyonel)

        Returns:
            Optional[Dict[str, Any]]: Doğrulama başarılıysa kullanıcı verileri, değilse None
        """
        if not self.user_exists(username):
            return None

        # Kullanıcı verilerini yükle
        user_path = self.get_user_path(username)
        with open(user_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)

        # Hesap kilitli mi kontrol et
        if user_data.get("account_locked_until"):
            locked_until = datetime.fromisoformat(user_data["account_locked_until"])
            if locked_until > datetime.now(timezone.utc):
                self.logger.warning(f"Kilitli hesaba giriş denemesi: {username}")
                return None
            else:
                # Kilit süresini geçmiş, kilidi kaldır
                user_data["account_locked_until"] = None
                user_data["failed_login_attempts"] = 0

        # Şifreyi doğrula
        if not verify_password(password, user_data["hashed_password"]):
            # Başarısız giriş denemesi
            user_data["failed_login_attempts"] = user_data.get("failed_login_attempts", 0) + 1
            user_data["last_failed_login"] = datetime.now(timezone.utc).isoformat()

            # Maksimum başarısız giriş denemesi kontrolü
            max_attempts = 5
            if user_data["failed_login_attempts"] >= max_attempts:
                # Hesabı kilitle (30 dakika)
                lock_duration_minutes = 30
                user_data["account_locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=lock_duration_minutes)).isoformat()
                self.logger.warning(f"Hesap kilitlendi: {username} (çok fazla başarısız giriş denemesi)")

                # Tüm token'ları geçersiz kıl
                invalidate_all_user_tokens(username)

            # Kullanıcı verilerini güncelle
            with open(user_path, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            return None

        # Kullanıcı aktif değilse
        if not user_data.get("is_active", True):
            self.logger.warning(f"Pasif hesaba giriş denemesi: {username}")
            return None

        # Başarılı giriş, başarısız giriş sayacını sıfırla
        user_data["failed_login_attempts"] = 0

        # Son giriş zamanını ve bilgilerini güncelle
        now = datetime.now(timezone.utc)
        user_data["last_login"] = now.isoformat()

        # IP ve kullanıcı ajanı bilgilerini güncelle
        if ip_address:
            user_data["last_ip"] = ip_address

            # Bilinen IP'ler listesine ekle
            known_ips = user_data.get("known_ips", [])
            if ip_address not in known_ips:
                known_ips.append(ip_address)
                user_data["known_ips"] = known_ips

        if user_agent:
            user_data["user_agent"] = user_agent

        # Giriş geçmişine ekle
        login_history = user_data.get("login_history", [])
        login_history.append({
            "timestamp": now.isoformat(),
            "ip": ip_address,
            "user_agent": user_agent
        })

        # Giriş geçmişini son 10 girişle sınırla
        user_data["login_history"] = login_history[-10:]

        # Kullanıcı verilerini güncelle
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

        # Hassas verileri temizle
        user_data.pop("hashed_password", None)
        user_data.pop("password_history", None)
        user_data.pop("two_factor_secret", None)
        user_data.pop("recovery_codes", None)

        self.logger.info(f"Kullanıcı girişi başarılı: {username}")
        return user_data

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı verilerini getirir.

        Args:
            username: Kullanıcı adı

        Returns:
            Optional[Dict[str, Any]]: Kullanıcı verileri, kullanıcı yoksa None
        """
        if not self.user_exists(username):
            return None

        # Kullanıcı verilerini yükle
        user_path = self.get_user_path(username)
        with open(user_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)

        # Hassas verileri temizle
        user_data.pop("hashed_password", None)

        return user_data

    def update_user(self, username: str, data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """Kullanıcı verilerini günceller.

        Args:
            username: Kullanıcı adı
            data: Güncellenecek veriler

        Returns:
            Tuple[bool, Optional[List[str]]]: (Başarılıysa True, Hata mesajları)

        Raises:
            ValueError: Kullanıcı yoksa
        """
        if not self.user_exists(username):
            raise ValueError(f"Kullanıcı bulunamadı: {username}")

        # Kullanıcı verilerini yükle
        user_path = self.get_user_path(username)
        with open(user_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)

        # Güncellenmemesi gereken alanları koru
        protected_fields = [
            "username", "created_at", "hashed_password", "is_admin",
            "failed_login_attempts", "last_failed_login", "account_locked_until",
            "password_history", "two_factor_secret", "recovery_codes"
        ]

        # Şifre güncellemesi kontrolü
        if "password" in data:
            # Şifre politikasını kontrol et
            is_valid, errors = self.password_policy.validate_password(data["password"])
            if not is_valid:
                return False, errors

            # Önceki şifreleri kontrol et (son 5 şifre tekrar kullanılamaz)
            password_history = user_data.get("password_history", [])
            for old_hash in password_history[-5:]:
                if verify_password(data["password"], old_hash):
                    return False, ["Bu şifre yakın zamanda kullanılmış. Lütfen farklı bir şifre seçin."]

            # Yeni şifreyi hashle
            new_hash = get_password_hash(data["password"])

            # Şifre geçmişine ekle
            password_history.append(user_data["hashed_password"])
            user_data["password_history"] = password_history[-10:]  # Son 10 şifreyi sakla

            # Şifreyi güncelle
            user_data["hashed_password"] = new_hash
            user_data["password_last_changed"] = datetime.now(timezone.utc).isoformat()

            # Tüm token'ları geçersiz kıl (şifre değiştiğinde)
            invalidate_all_user_tokens(username)

            # Şifre alanını kaldır
            del data["password"]

        # E-posta güncellemesi kontrolü
        if "email" in data and data["email"] != user_data.get("email"):
            # E-posta geçerliliğini kontrol et
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", data["email"]):
                return False, ["Geçerli bir e-posta adresi giriniz"]

        # Verileri güncelle
        for key, value in data.items():
            if key not in protected_fields:
                user_data[key] = value

        # Son güncelleme zamanını güncelle
        user_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Kullanıcı verilerini kaydet
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Kullanıcı güncellendi: {username}")
        return True, None

    def delete_user(self, username: str) -> bool:
        """Kullanıcıyı siler.

        Args:
            username: Kullanıcı adı

        Returns:
            bool: Başarılıysa True

        Raises:
            ValueError: Kullanıcı yoksa
        """
        if not self.user_exists(username):
            raise ValueError(f"Kullanıcı bulunamadı: {username}")

        try:
            # Tüm token'ları geçersiz kıl
            invalidate_all_user_tokens(username)

            # Kullanıcı dosyasını sil
            user_path = self.get_user_path(username)
            os.remove(user_path)

            self.logger.info(f"Kullanıcı silindi: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Kullanıcı silme hatası: {str(e)}")
            return False

    def lock_user_account(self, username: str, duration_minutes: int = 30) -> bool:
        """Kullanıcı hesabını kilitler.

        Args:
            username: Kullanıcı adı
            duration_minutes: Kilit süresi (dakika)

        Returns:
            bool: Başarılıysa True
        """
        if not self.user_exists(username):
            return False

        try:
            # Kullanıcı verilerini yükle
            user_path = self.get_user_path(username)
            with open(user_path, "r", encoding="utf-8") as f:
                user_data = json.load(f)

            # Hesabı kilitle
            user_data["account_locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat()

            # Tüm token'ları geçersiz kıl
            invalidate_all_user_tokens(username)

            # Kullanıcı verilerini güncelle
            with open(user_path, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Kullanıcı hesabı kilitlendi: {username} ({duration_minutes} dakika)")
            return True
        except Exception as e:
            self.logger.error(f"Kullanıcı hesabı kilitleme hatası: {str(e)}")
            return False

    def unlock_user_account(self, username: str) -> bool:
        """Kullanıcı hesabının kilidini açar.

        Args:
            username: Kullanıcı adı

        Returns:
            bool: Başarılıysa True
        """
        if not self.user_exists(username):
            return False

        try:
            # Kullanıcı verilerini yükle
            user_path = self.get_user_path(username)
            with open(user_path, "r", encoding="utf-8") as f:
                user_data = json.load(f)

            # Hesap kilidini kaldır
            user_data["account_locked_until"] = None
            user_data["failed_login_attempts"] = 0

            # Kullanıcı verilerini güncelle
            with open(user_path, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Kullanıcı hesabının kilidi açıldı: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Kullanıcı hesabı kilit açma hatası: {str(e)}")
            return False
