# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kimlik Doğrulama API Modelleri

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    """Token yanıt modeli."""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """Token veri modeli."""
    username: Optional[str] = None

class UserBase(BaseModel):
    """Kullanıcı temel modeli."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    """Kullanıcı oluşturma modeli."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Kullanıcı güncelleme modeli."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Kullanıcı yanıt modeli."""
    created_at: str
    last_login: Optional[str] = None
    last_updated: str
    is_admin: bool = False

class LoginRequest(BaseModel):
    """Giriş isteği modeli."""
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    """Token yenileme isteği modeli."""
    refresh_token: str
