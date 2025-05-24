# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# API Anahtarı Yönetim Rotaları

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from pydantic import BaseModel, Field

from core.security.secure_config import SecureConfig
from core.user_profile import UserProfile
from config import PROFILES_PATH, USERS_PATH

# Router oluştur
router = APIRouter(
    prefix="/api/api-keys",
    tags=["api-keys"],
    responses={404: {"description": "Not found"}},
)

# Modeller
class APIKeyRequest(BaseModel):
    service_name: str
    api_key: str
    metadata: Optional[Dict[str, Any]] = None

class APIKeyResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class APIKeyListItem(BaseModel):
    service_name: str
    masked_key: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str

class APIKeyListResponse(BaseModel):
    keys: List[APIKeyListItem]

class APIProviderInfo(BaseModel):
    id: str
    name: str
    description: str
    url: str
    auth_type: str = "api_key"
    auth_key_name: str = "api_key"
    logo_url: Optional[str] = None
    models_endpoint: Optional[str] = None
    requires_auth: bool = True

class APIProviderListResponse(BaseModel):
    providers: List[APIProviderInfo]

# Desteklenen API sağlayıcıları
SUPPORTED_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "description": "OpenAI API (GPT-3.5, GPT-4, vb.)",
        "url": "https://platform.openai.com",
        "auth_type": "api_key",
        "auth_key_name": "api_key",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/1024px-ChatGPT_logo.svg.png",
        "models_endpoint": "https://api.openai.com/v1/models",
        "requires_auth": True
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "description": "Anthropic API (Claude modelleri)",
        "url": "https://console.anthropic.com",
        "auth_type": "api_key",
        "auth_key_name": "api_key",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Anthropic_logo.svg/1200px-Anthropic_logo.svg.png",
        "models_endpoint": None,
        "requires_auth": True
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "description": "OpenRouter API (Çeşitli AI modelleri)",
        "url": "https://openrouter.ai",
        "auth_type": "api_key",
        "auth_key_name": "api_key",
        "logo_url": "https://avatars.githubusercontent.com/u/139895814",
        "models_endpoint": "https://openrouter.ai/api/v1/models",
        "requires_auth": True
    },
    {
        "id": "cohere",
        "name": "Cohere",
        "description": "Cohere API (Command modelleri)",
        "url": "https://dashboard.cohere.com",
        "auth_type": "api_key",
        "auth_key_name": "api_key",
        "logo_url": "https://assets-global.website-files.com/64f6f2c0e3f4c5a91c1e823a/654693d569494a7d8055f6d2_cohere_logo.svg",
        "models_endpoint": None,
        "requires_auth": True
    },
    {
        "id": "google",
        "name": "Google AI",
        "description": "Google AI API (Gemini modelleri)",
        "url": "https://ai.google.dev",
        "auth_type": "api_key",
        "auth_key_name": "api_key",
        "logo_url": "https://lh3.googleusercontent.com/COxitqgJr1sJnIDe8-jiKhxDx1FrYbtRHKJ9z_hELisAlapwE9LUPh6fcXIfb5vwpbMl4xl9H9TRFPc5NOO8Sb3VSgIBrfRYvW6cUA",
        "models_endpoint": None,
        "requires_auth": True
    }
]

# API anahtarı yönetim fonksiyonları
@router.post("/set", response_model=APIKeyResponse)
async def set_api_key(request: APIKeyRequest, user_id: str = "default_user"):
    """API anahtarını ayarlar"""
    try:
        # Güvenli yapılandırma yöneticisini başlat
        secure_config = SecureConfig(user_id=user_id, storage_path=USERS_PATH)

        # API anahtarını ayarla
        success = secure_config.set_api_key(
            service_name=request.service_name,
            api_key=request.api_key,
            metadata=request.metadata
        )

        if success:
            logging.info(f"API anahtarı başarıyla ayarlandı: {request.service_name}")
            return {
                "success": True,
                "message": f"API anahtarı başarıyla ayarlandı: {request.service_name}"
            }
        else:
            logging.error(f"API anahtarı ayarlanamadı: {request.service_name}")
            return {
                "success": False,
                "message": f"API anahtarı ayarlanamadı: {request.service_name}"
            }
    except Exception as e:
        logging.error(f"API anahtarı ayarlanırken hata: {str(e)}")
        return {
            "success": False,
            "message": f"API anahtarı ayarlanamadı: {str(e)}"
        }

@router.delete("/delete/{service_name}", response_model=APIKeyResponse)
async def delete_api_key(service_name: str, user_id: str = "default_user"):
    """API anahtarını siler"""
    try:
        # Güvenli yapılandırma yöneticisini başlat
        secure_config = SecureConfig(user_id=user_id, storage_path=USERS_PATH)

        # API anahtarını sil
        success = secure_config.delete_api_key(service_name)

        if success:
            logging.info(f"API anahtarı başarıyla silindi: {service_name}")
            return {
                "success": True,
                "message": f"API anahtarı başarıyla silindi: {service_name}"
            }
        else:
            logging.error(f"API anahtarı silinemedi: {service_name}")
            return {
                "success": False,
                "message": f"API anahtarı silinemedi: {service_name}"
            }
    except Exception as e:
        logging.error(f"API anahtarı silinirken hata: {str(e)}")
        return {
            "success": False,
            "message": f"API anahtarı silinemedi: {str(e)}"
        }

@router.get("/list", response_model=APIKeyListResponse)
async def list_api_keys(user_id: str = "default_user"):
    """Kayıtlı API anahtarlarını listeler"""
    try:
        # Güvenli yapılandırma yöneticisini başlat
        secure_config = SecureConfig(user_id=user_id, storage_path=USERS_PATH)

        # API anahtarlarını listele
        keys = secure_config.list_api_keys()

        # Yanıt formatına dönüştür
        key_list = []
        for key in keys:
            # API anahtarını maskele (ilk 4 ve son 4 karakter hariç)
            service_name = key.get("service", "")
            api_key = secure_config.get_api_key(service_name)
            masked_key = ""
            if api_key:
                if len(api_key) > 8:
                    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                else:
                    masked_key = "*" * len(api_key)

            key_list.append({
                "service_name": service_name,
                "masked_key": masked_key,
                "metadata": key.get("metadata", {}),
                "created_at": key.get("created_at", ""),
                "updated_at": key.get("updated_at", "")
            })

        return {"keys": key_list}
    except Exception as e:
        logging.error(f"API anahtarları listelenirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API anahtarları listelenirken hata: {str(e)}"
        )

@router.get("/providers", response_model=APIProviderListResponse)
async def list_providers():
    """Desteklenen API sağlayıcılarını listeler"""
    return {"providers": SUPPORTED_PROVIDERS}
