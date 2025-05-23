# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kullanıcı Profil Yönetim Modülü

import json
import os
from datetime import datetime

class UserProfile:
    """Kullanıcı profilini ve tercihlerini yöneten sınıf.

    Bu sınıf, kullanıcının kişisel bilgilerini, tercihlerini ve davranış modellerini
    depolar ve yönetir. Asistanın kişiselleştirilmesinde kullanılır.
    """

    def __init__(self, user_id, storage_path="./data/profiles"):
        """Kullanıcı profil yöneticisi başlatıcısı.

        Args:
            user_id (str): Kullanıcının benzersiz tanımlayıcısı
            storage_path (str): Profil verilerinin depolanacağı dizin yolu
        """
        self.user_id = user_id
        self.storage_path = storage_path
        self.profile_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "preferences": {},
            "interests": [],
            "communication_style": "neutral",
            "learned_behaviors": {},
            "model_preferences": {
                "ai_model": None,
                "embedding_model": None,
                "embedding_function": None,
                "voice_model": None
            }
        }
        self.ensure_storage_exists()
        self.load_profile()

    def ensure_storage_exists(self):
        """Depolama dizininin var olduğundan emin olur."""
        os.makedirs(self.storage_path, exist_ok=True)

    def load_profile(self):
        """Kullanıcı profilini yükler. Profil yoksa yeni bir profil oluşturur."""
        profile_path = os.path.join(self.storage_path, f"{self.user_id}.json")

        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                self.profile_data = json.load(f)
        else:
            # Yeni profil oluştur ve kaydet
            self.save_profile()

    def save_profile(self):
        """Kullanıcı profilini kaydeder."""
        self.profile_data["last_updated"] = datetime.now().isoformat()
        profile_path = os.path.join(self.storage_path, f"{self.user_id}.json")

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(self.profile_data, f, ensure_ascii=False, indent=2)

    def set_preference(self, preference_type, preference_value):
        """Kullanıcı tercihini ayarlar.

        Args:
            preference_type (str): Tercih türü
            preference_value: Tercih değeri
        """
        self.profile_data["preferences"][preference_type] = preference_value
        self.save_profile()

    def get_preference(self, preference_type, default=None):
        """Kullanıcı tercihini getirir.

        Args:
            preference_type (str): Tercih türü
            default: Tercih bulunamazsa dönecek varsayılan değer

        Returns:
            any: Tercih değeri veya varsayılan değer
        """
        return self.profile_data["preferences"].get(preference_type, default)

    def get_all_preferences(self):
        """Tüm kullanıcı tercihlerini getirir.

        Returns:
            dict: Tüm tercihler
        """
        return self.profile_data["preferences"]

    def add_interest(self, interest):
        """Kullanıcı ilgi alanı ekler.

        Args:
            interest (str): İlgi alanı
        """
        if interest not in self.profile_data["interests"]:
            self.profile_data["interests"].append(interest)
            self.save_profile()

    def remove_interest(self, interest):
        """Kullanıcı ilgi alanını kaldırır.

        Args:
            interest (str): İlgi alanı
        """
        if interest in self.profile_data["interests"]:
            self.profile_data["interests"].remove(interest)
            self.save_profile()

    def get_interests(self):
        """Kullanıcı ilgi alanlarını getirir.

        Returns:
            list: İlgi alanları listesi
        """
        return self.profile_data["interests"]

    def set_communication_style(self, style):
        """İletişim tarzını ayarlar.

        Args:
            style (str): İletişim tarzı (örn. "formal", "casual", "friendly")
        """
        self.profile_data["communication_style"] = style
        self.save_profile()

    def get_communication_style(self):
        """İletişim tarzını getirir.

        Returns:
            str: İletişim tarzı
        """
        return self.profile_data["communication_style"]

    def update_learned_behavior(self, behavior_key, behavior_data):
        """Öğrenilen davranış modelini günceller.

        Args:
            behavior_key (str): Davranış anahtarı
            behavior_data: Davranış verisi
        """
        self.profile_data["learned_behaviors"][behavior_key] = behavior_data
        self.save_profile()

    def get_learned_behavior(self, behavior_key, default=None):
        """Öğrenilen davranış modelini getirir.

        Args:
            behavior_key (str): Davranış anahtarı
            default: Davranış bulunamazsa dönecek varsayılan değer

        Returns:
            any: Davranış verisi veya varsayılan değer
        """
        return self.profile_data["learned_behaviors"].get(behavior_key, default)

    def get_profile_summary(self):
        """Kullanıcı profili özeti oluşturur.

        Returns:
            dict: Profil özeti
        """
        return {
            "user_id": self.user_id,
            "interests_count": len(self.profile_data["interests"]),
            "preferences_count": len(self.profile_data["preferences"]),
            "communication_style": self.profile_data["communication_style"],
            "learned_behaviors_count": len(self.profile_data["learned_behaviors"]),
            "last_updated": self.profile_data["last_updated"]
        }

    def set_model_preference(self, model_type, model_value):
        """Model tercihini ayarlar.

        Args:
            model_type (str): Model türü (ai_model, embedding_model, embedding_function, voice_model)
            model_value (str): Model değeri
        """
        if model_type in self.profile_data["model_preferences"]:
            self.profile_data["model_preferences"][model_type] = model_value
            self.save_profile()
        else:
            raise ValueError(f"Geçersiz model türü: {model_type}")

    def get_model_preference(self, model_type, default=None):
        """Model tercihini getirir.

        Args:
            model_type (str): Model türü (ai_model, embedding_model, embedding_function, voice_model)
            default: Tercih bulunamazsa dönecek varsayılan değer

        Returns:
            str: Model değeri veya varsayılan değer
        """
        if model_type in self.profile_data["model_preferences"]:
            return self.profile_data["model_preferences"].get(model_type, default)
        else:
            raise ValueError(f"Geçersiz model türü: {model_type}")

    def get_all_model_preferences(self):
        """Tüm model tercihlerini getirir.

        Returns:
            dict: Tüm model tercihleri
        """
        return self.profile_data["model_preferences"]

    def get_access_interface(self):
        """Kullanıcı profili erişim arayüzünü döndürür.

        Returns:
            UserProfile: Kullanıcı profili erişim arayüzü
        """
        return self