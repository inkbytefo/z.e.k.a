# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Şifre Politikası Modülü

import re
import os
import logging
from typing import Dict, Any, Optional, List, Tuple, Union

from ..logging_manager import get_logger

class PasswordPolicy:
    """Şifre politikası sınıfı.
    
    Bu sınıf, şifre güvenlik politikalarını uygular ve şifre
    güvenliğini değerlendirir.
    """
    
    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_numbers: bool = True,
        require_special: bool = True,
        min_unique_chars: int = 4,
        max_sequential_chars: int = 3,
        max_repeated_chars: int = 3,
        check_common_passwords: bool = True,
        common_passwords_file: Optional[str] = None
    ):
        """PasswordPolicy başlatıcısı.
        
        Args:
            min_length: Minimum şifre uzunluğu (varsayılan: 8)
            require_uppercase: Büyük harf gerekli mi (varsayılan: True)
            require_lowercase: Küçük harf gerekli mi (varsayılan: True)
            require_numbers: Rakam gerekli mi (varsayılan: True)
            require_special: Özel karakter gerekli mi (varsayılan: True)
            min_unique_chars: Minimum benzersiz karakter sayısı (varsayılan: 4)
            max_sequential_chars: Maksimum ardışık karakter sayısı (varsayılan: 3)
            max_repeated_chars: Maksimum tekrarlanan karakter sayısı (varsayılan: 3)
            check_common_passwords: Yaygın şifreleri kontrol et (varsayılan: True)
            common_passwords_file: Yaygın şifreler dosyası (opsiyonel)
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special = require_special
        self.min_unique_chars = min_unique_chars
        self.max_sequential_chars = max_sequential_chars
        self.max_repeated_chars = max_repeated_chars
        self.check_common_passwords = check_common_passwords
        
        self.logger = get_logger("password_policy")
        
        # Yaygın şifreler
        self.common_passwords = set()
        
        if check_common_passwords:
            self._load_common_passwords(common_passwords_file)
    
    def _load_common_passwords(self, common_passwords_file: Optional[str] = None) -> None:
        """Yaygın şifreleri yükler.
        
        Args:
            common_passwords_file: Yaygın şifreler dosyası (opsiyonel)
        """
        try:
            # Varsayılan dosya
            if not common_passwords_file:
                common_passwords_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "data",
                    "common_passwords.txt"
                )
            
            # Dosya var mı kontrol et
            if os.path.exists(common_passwords_file):
                with open(common_passwords_file, "r", encoding="utf-8") as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            self.common_passwords.add(password)
                
                self.logger.info(f"{len(self.common_passwords)} yaygın şifre yüklendi")
            else:
                self.logger.warning(f"Yaygın şifreler dosyası bulunamadı: {common_passwords_file}")
                
        except Exception as e:
            self.logger.error(f"Yaygın şifreler yüklenemedi: {str(e)}")
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Şifreyi doğrular.
        
        Args:
            password: Doğrulanacak şifre
            
        Returns:
            Tuple[bool, List[str]]: Doğrulama sonucu ve hata mesajları
        """
        errors = []
        
        # Uzunluk kontrolü
        if len(password) < self.min_length:
            errors.append(f"Şifre en az {self.min_length} karakter uzunluğunda olmalıdır")
        
        # Büyük harf kontrolü
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Şifre en az bir büyük harf içermelidir")
        
        # Küçük harf kontrolü
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Şifre en az bir küçük harf içermelidir")
        
        # Rakam kontrolü
        if self.require_numbers and not re.search(r"\d", password):
            errors.append("Şifre en az bir rakam içermelidir")
        
        # Özel karakter kontrolü
        if self.require_special and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            errors.append("Şifre en az bir özel karakter içermelidir")
        
        # Benzersiz karakter kontrolü
        unique_chars = set(password)
        if len(unique_chars) < self.min_unique_chars:
            errors.append(f"Şifre en az {self.min_unique_chars} farklı karakter içermelidir")
        
        # Ardışık karakter kontrolü
        for i in range(len(password) - self.max_sequential_chars + 1):
            substring = password[i:i + self.max_sequential_chars]
            
            # Ardışık sayılar
            if substring.isdigit():
                is_sequential = True
                for j in range(len(substring) - 1):
                    if int(substring[j + 1]) - int(substring[j]) != 1:
                        is_sequential = False
                        break
                
                if is_sequential:
                    errors.append(f"Şifre {self.max_sequential_chars} veya daha fazla ardışık sayı içermemelidir")
                    break
            
            # Ardışık harfler
            if substring.isalpha():
                is_sequential = True
                for j in range(len(substring) - 1):
                    if ord(substring[j + 1].lower()) - ord(substring[j].lower()) != 1:
                        is_sequential = False
                        break
                
                if is_sequential:
                    errors.append(f"Şifre {self.max_sequential_chars} veya daha fazla ardışık harf içermemelidir")
                    break
        
        # Tekrarlanan karakter kontrolü
        for i in range(len(password) - self.max_repeated_chars + 1):
            substring = password[i:i + self.max_repeated_chars]
            if len(set(substring)) == 1:
                errors.append(f"Şifre {self.max_repeated_chars} veya daha fazla tekrarlanan karakter içermemelidir")
                break
        
        # Yaygın şifre kontrolü
        if self.check_common_passwords and password.lower() in self.common_passwords:
            errors.append("Şifre yaygın olarak kullanılan bir şifre olmamalıdır")
        
        return len(errors) == 0, errors
    
    def get_password_strength(self, password: str) -> Tuple[int, str]:
        """Şifre gücünü hesaplar.
        
        Args:
            password: Şifre
            
        Returns:
            Tuple[int, str]: Şifre gücü (0-100) ve seviye (zayıf, orta, güçlü, çok güçlü)
        """
        score = 0
        max_score = 100
        
        # Uzunluk puanı (maksimum 30 puan)
        length_score = min(30, len(password) * 2)
        score += length_score
        
        # Karakter çeşitliliği puanı (maksimum 40 puan)
        char_diversity_score = 0
        
        # Büyük harf
        if re.search(r"[A-Z]", password):
            char_diversity_score += 10
        
        # Küçük harf
        if re.search(r"[a-z]", password):
            char_diversity_score += 10
        
        # Rakam
        if re.search(r"\d", password):
            char_diversity_score += 10
        
        # Özel karakter
        if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            char_diversity_score += 10
        
        score += char_diversity_score
        
        # Benzersiz karakter puanı (maksimum 15 puan)
        unique_chars = set(password)
        unique_chars_score = min(15, len(unique_chars) * 1.5)
        score += unique_chars_score
        
        # Karmaşıklık puanı (maksimum 15 puan)
        complexity_score = 15
        
        # Ardışık karakter cezası
        for i in range(len(password) - 2):
            substring = password[i:i + 3]
            
            # Ardışık sayılar
            if substring.isdigit():
                is_sequential = True
                for j in range(len(substring) - 1):
                    if int(substring[j + 1]) - int(substring[j]) != 1:
                        is_sequential = False
                        break
                
                if is_sequential:
                    complexity_score -= 5
            
            # Ardışık harfler
            if substring.isalpha():
                is_sequential = True
                for j in range(len(substring) - 1):
                    if ord(substring[j + 1].lower()) - ord(substring[j].lower()) != 1:
                        is_sequential = False
                        break
                
                if is_sequential:
                    complexity_score -= 5
        
        # Tekrarlanan karakter cezası
        for i in range(len(password) - 2):
            substring = password[i:i + 3]
            if len(set(substring)) == 1:
                complexity_score -= 5
        
        score += max(0, complexity_score)
        
        # Yaygın şifre cezası
        if self.check_common_passwords and password.lower() in self.common_passwords:
            score = min(30, score)  # Maksimum 30 puan
        
        # Şifre seviyesi
        if score < 40:
            level = "zayıf"
        elif score < 60:
            level = "orta"
        elif score < 80:
            level = "güçlü"
        else:
            level = "çok güçlü"
        
        return score, level
    
    def generate_password_requirements(self) -> str:
        """Şifre gereksinimlerini oluşturur.
        
        Returns:
            str: Şifre gereksinimleri
        """
        requirements = [
            f"- En az {self.min_length} karakter uzunluğunda olmalıdır"
        ]
        
        if self.require_uppercase:
            requirements.append("- En az bir büyük harf içermelidir")
        
        if self.require_lowercase:
            requirements.append("- En az bir küçük harf içermelidir")
        
        if self.require_numbers:
            requirements.append("- En az bir rakam içermelidir")
        
        if self.require_special:
            requirements.append("- En az bir özel karakter içermelidir")
        
        if self.min_unique_chars > 0:
            requirements.append(f"- En az {self.min_unique_chars} farklı karakter içermelidir")
        
        if self.max_sequential_chars > 0:
            requirements.append(f"- {self.max_sequential_chars} veya daha fazla ardışık karakter içermemelidir")
        
        if self.max_repeated_chars > 0:
            requirements.append(f"- {self.max_repeated_chars} veya daha fazla tekrarlanan karakter içermemelidir")
        
        if self.check_common_passwords:
            requirements.append("- Yaygın olarak kullanılan bir şifre olmamalıdır")
        
        return "\n".join(requirements)
