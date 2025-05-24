"""
Z.E.K.A AI Sağlayıcı Yöneticisi

Bu modül, farklı AI sağlayıcılarını yönetmek için kullanılır.
OpenAI-compatible API'leri destekler.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from core.logging_manager import get_logger
from core.openai_client import OpenAIClient, OpenAIAPIError


class ProviderManager:
    """AI sağlayıcılarını yöneten sınıf"""
    
    # Önceden tanımlanmış sağlayıcılar
    PREDEFINED_PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "description": "OpenAI GPT modelleri",
            "base_url": "https://api.openai.com/v1",
            "auth_type": "bearer",
            "requires_api_key": True,
            "env_key": "OPENAI_API_KEY",
            "models": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "supports_streaming": True,
            "logo_url": "https://openai.com/favicon.ico"
        },
        "ollama": {
            "name": "Ollama",
            "description": "Yerel Ollama modelleri",
            "base_url": "http://localhost:11434/v1",
            "auth_type": "none",
            "requires_api_key": False,
            "env_key": "OLLAMA_API_KEY",
            "models": [],  # Dinamik olarak keşfedilecek
            "supports_streaming": True,
            "logo_url": "https://ollama.ai/favicon.ico"
        },
        "localai": {
            "name": "LocalAI",
            "description": "Yerel LocalAI modelleri",
            "base_url": "http://localhost:8080/v1",
            "auth_type": "bearer",
            "requires_api_key": False,
            "env_key": "LOCALAI_API_KEY",
            "models": [],  # Dinamik olarak keşfedilecek
            "supports_streaming": True,
            "logo_url": "https://localai.io/favicon.ico"
        },
        "groq": {
            "name": "Groq",
            "description": "Groq hızlı AI modelleri",
            "base_url": "https://api.groq.com/openai/v1",
            "auth_type": "bearer",
            "requires_api_key": True,
            "env_key": "GROQ_API_KEY",
            "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
            "supports_streaming": True,
            "logo_url": "https://groq.com/favicon.ico"
        },
        "anthropic": {
            "name": "Anthropic (via OpenAI format)",
            "description": "Anthropic Claude modelleri OpenAI formatında",
            "base_url": "https://api.anthropic.com/v1",
            "auth_type": "bearer",
            "requires_api_key": True,
            "env_key": "ANTHROPIC_API_KEY",
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "supports_streaming": True,
            "logo_url": "https://anthropic.com/favicon.ico"
        }
    }
    
    def __init__(self, storage_path: str = "data/providers"):
        """Sağlayıcı yöneticisi başlatıcısı
        
        Args:
            storage_path: Sağlayıcı verilerinin saklanacağı dizin
        """
        self.logger = get_logger("provider_manager")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.providers_file = self.storage_path / "providers.json"
        self.active_providers = {}
        self.load_providers()
    
    def load_providers(self):
        """Kayıtlı sağlayıcıları yükler"""
        try:
            if self.providers_file.exists():
                with open(self.providers_file, 'r', encoding='utf-8') as f:
                    saved_providers = json.load(f)
                
                # Önceden tanımlanmış sağlayıcıları güncelle
                for provider_id, provider_data in self.PREDEFINED_PROVIDERS.items():
                    if provider_id in saved_providers:
                        # Kayıtlı verilerle güncelle
                        provider_data.update(saved_providers[provider_id])
                    self.active_providers[provider_id] = provider_data
                
                # Özel sağlayıcıları ekle
                for provider_id, provider_data in saved_providers.items():
                    if provider_id not in self.PREDEFINED_PROVIDERS:
                        self.active_providers[provider_id] = provider_data
            else:
                # İlk kez çalışıyorsa önceden tanımlanmış sağlayıcıları kullan
                self.active_providers = self.PREDEFINED_PROVIDERS.copy()
                self.save_providers()
            
            self.logger.info(f"{len(self.active_providers)} sağlayıcı yüklendi")
        except Exception as e:
            self.logger.error(f"Sağlayıcılar yüklenirken hata: {str(e)}")
            self.active_providers = self.PREDEFINED_PROVIDERS.copy()
    
    def save_providers(self):
        """Sağlayıcıları dosyaya kaydeder"""
        try:
            with open(self.providers_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_providers, f, ensure_ascii=False, indent=2)
            self.logger.debug("Sağlayıcılar kaydedildi")
        except Exception as e:
            self.logger.error(f"Sağlayıcılar kaydedilirken hata: {str(e)}")
    
    def add_provider(
        self,
        provider_id: str,
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
        description: str = "",
        models: List[str] = None,
        auth_type: str = "bearer",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Yeni sağlayıcı ekler
        
        Args:
            provider_id: Sağlayıcı ID'si
            name: Sağlayıcı adı
            base_url: API base URL'si
            api_key: API anahtarı (opsiyonel)
            description: Açıklama
            models: Desteklenen modeller
            auth_type: Kimlik doğrulama türü
            metadata: Ek meta veriler
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            provider_data = {
                "name": name,
                "description": description,
                "base_url": base_url,
                "auth_type": auth_type,
                "requires_api_key": api_key is not None,
                "models": models or [],
                "supports_streaming": True,  # Varsayılan olarak streaming destekli
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "custom": True  # Özel sağlayıcı işareti
            }
            
            if metadata:
                provider_data.update(metadata)
            
            self.active_providers[provider_id] = provider_data
            self.save_providers()
            
            self.logger.info(f"Sağlayıcı eklendi: {provider_id} ({name})")
            return True
        except Exception as e:
            self.logger.error(f"Sağlayıcı eklenirken hata: {str(e)}")
            return False
    
    def remove_provider(self, provider_id: str) -> bool:
        """Sağlayıcıyı kaldırır
        
        Args:
            provider_id: Sağlayıcı ID'si
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            if provider_id in self.active_providers:
                # Önceden tanımlanmış sağlayıcıları silme, sadece devre dışı bırak
                if provider_id in self.PREDEFINED_PROVIDERS:
                    self.active_providers[provider_id]["enabled"] = False
                else:
                    del self.active_providers[provider_id]
                
                self.save_providers()
                self.logger.info(f"Sağlayıcı kaldırıldı: {provider_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Sağlayıcı kaldırılırken hata: {str(e)}")
            return False
    
    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Sağlayıcı bilgilerini getirir
        
        Args:
            provider_id: Sağlayıcı ID'si
            
        Returns:
            Dict: Sağlayıcı bilgileri veya None
        """
        return self.active_providers.get(provider_id)
    
    def list_providers(self, enabled_only: bool = True) -> Dict[str, Dict[str, Any]]:
        """Sağlayıcıları listeler
        
        Args:
            enabled_only: Sadece etkin sağlayıcıları listele
            
        Returns:
            Dict: Sağlayıcı listesi
        """
        if enabled_only:
            return {
                pid: pdata for pid, pdata in self.active_providers.items()
                if pdata.get("enabled", True)
            }
        return self.active_providers.copy()
    
    async def discover_models(self, provider_id: str) -> List[str]:
        """Sağlayıcının modellerini keşfeder
        
        Args:
            provider_id: Sağlayıcı ID'si
            
        Returns:
            List: Bulunan modeller
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return []
        
        try:
            # OpenAI uyumlu client oluştur
            client = OpenAIClient(
                provider_name=provider_id,
                base_url=provider["base_url"],
                api_key=os.getenv(provider.get("env_key", f"{provider_id.upper()}_API_KEY"), "dummy")
            )
            
            # /models endpoint'ini çağır
            response = await client.async_client.models.list()
            models = [model.id for model in response.data]
            
            # Bulunan modelleri kaydet
            provider["models"] = models
            provider["last_model_discovery"] = datetime.now().isoformat()
            self.save_providers()
            
            self.logger.info(f"{provider_id} için {len(models)} model keşfedildi")
            return models
            
        except Exception as e:
            self.logger.warning(f"{provider_id} model keşfi başarısız: {str(e)}")
            return provider.get("models", [])
    
    def create_client(self, provider_id: str, model: str = None) -> Optional[OpenAIClient]:
        """Sağlayıcı için client oluşturur
        
        Args:
            provider_id: Sağlayıcı ID'si
            model: Kullanılacak model
            
        Returns:
            OpenAIClient: Oluşturulan client veya None
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        
        try:
            api_key = None
            if provider.get("requires_api_key", True):
                api_key = os.getenv(provider.get("env_key", f"{provider_id.upper()}_API_KEY"))
                if not api_key:
                    self.logger.error(f"{provider_id} için API anahtarı bulunamadı")
                    return None
            
            client = OpenAIClient(
                provider_name=provider_id,
                base_url=provider["base_url"],
                api_key=api_key or "dummy",
                default_model=model or provider.get("models", ["gpt-3.5-turbo"])[0]
            )
            
            return client
            
        except Exception as e:
            self.logger.error(f"{provider_id} client oluşturulurken hata: {str(e)}")
            return None
