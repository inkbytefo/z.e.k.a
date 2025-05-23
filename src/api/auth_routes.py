# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kimlik Doğrulama API Rotaları

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from core.auth.user_auth import UserAuth
from core.auth.auth_utils import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from core.auth.auth_dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user
)

from .auth_models import (
    Token,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    RefreshTokenRequest
)

# Router oluştur
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Kullanıcı kimlik doğrulama yöneticisi
user_auth = UserAuth(storage_path=os.getenv("USERS_PATH", "./data/users"))

# Loglama
logger = logging.getLogger("auth_routes")

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 uyumlu token endpoint'i.
    
    Args:
        form_data: OAuth2 form verileri
        
    Returns:
        Token: Erişim ve yenileme token'ları
        
    Raises:
        HTTPException: Kimlik doğrulama başarısızsa
    """
    user = user_auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token'ları oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user["username"]},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Kullanıcı girişi endpoint'i.
    
    Args:
        login_data: Giriş verileri
        
    Returns:
        Token: Erişim ve yenileme token'ları
        
    Raises:
        HTTPException: Kimlik doğrulama başarısızsa
    """
    user = user_auth.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token'ları oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user["username"]},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Token yenileme endpoint'i.
    
    Args:
        refresh_data: Yenileme token'ı
        
    Returns:
        Token: Yeni erişim ve yenileme token'ları
        
    Raises:
        HTTPException: Token geçersizse
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz yenileme token'ı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Token'ı doğrula
    payload = verify_token(refresh_data.refresh_token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Kullanıcıyı getir
    user = user_auth.get_user(username)
    if user is None:
        raise credentials_exception
    
    # Yeni token'ları oluştur
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": username},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Kullanıcı kaydı endpoint'i.
    
    Args:
        user_data: Kullanıcı verileri
        
    Returns:
        UserResponse: Oluşturulan kullanıcı
        
    Raises:
        HTTPException: Kullanıcı zaten varsa
    """
    try:
        # Kullanıcıyı oluştur
        user_auth.create_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            full_name=user_data.full_name or ""
        )
        
        # Kullanıcı verilerini getir
        user = user_auth.get_user(user_data.username)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """Mevcut kullanıcı bilgilerini getirir.
    
    Args:
        current_user: Mevcut kullanıcı
        
    Returns:
        UserResponse: Kullanıcı bilgileri
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Mevcut kullanıcı bilgilerini günceller.
    
    Args:
        user_data: Güncellenecek veriler
        current_user: Mevcut kullanıcı
        
    Returns:
        UserResponse: Güncellenmiş kullanıcı bilgileri
        
    Raises:
        HTTPException: Güncelleme başarısızsa
    """
    try:
        # Kullanıcıyı güncelle
        user_auth.update_user(
            username=current_user["username"],
            data=user_data.dict(exclude_unset=True)
        )
        
        # Güncellenmiş kullanıcı verilerini getir
        updated_user = user_auth.get_user(current_user["username"])
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
