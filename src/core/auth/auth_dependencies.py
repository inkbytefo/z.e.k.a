# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kimlik Doğrulama Bağımlılıkları

import os
import logging
from typing import Dict, Any, Optional, List, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .auth_utils import verify_token
from .user_auth import UserAuth

# OAuth2 şema
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Kullanıcı kimlik doğrulama yöneticisi
user_auth = UserAuth(storage_path=os.getenv("USERS_PATH", "./data/users"))

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Mevcut kullanıcıyı getirir.
    
    Args:
        token: JWT token
        
    Returns:
        Dict[str, Any]: Kullanıcı verileri
        
    Raises:
        HTTPException: Kimlik doğrulama başarısızsa
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz kimlik bilgileri",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Token'ı doğrula
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Kullanıcıyı getir
    user = user_auth.get_user(username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Mevcut aktif kullanıcıyı getirir.
    
    Args:
        current_user: Mevcut kullanıcı
        
    Returns:
        Dict[str, Any]: Kullanıcı verileri
        
    Raises:
        HTTPException: Kullanıcı aktif değilse
    """
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Devre dışı bırakılmış kullanıcı")
    return current_user

async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Mevcut admin kullanıcıyı getirir.
    
    Args:
        current_user: Mevcut kullanıcı
        
    Returns:
        Dict[str, Any]: Kullanıcı verileri
        
    Raises:
        HTTPException: Kullanıcı admin değilse
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yeterli izne sahip değilsiniz"
        )
    return current_user
