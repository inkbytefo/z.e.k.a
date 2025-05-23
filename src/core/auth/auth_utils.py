# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kimlik Doğrulama Yardımcı Fonksiyonları

import os
import time
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Union, Set

from jose import jwt, JWTError
from passlib.context import CryptContext

# Şifreleme bağlamı
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT ayarları
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "zeka_jwt_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Token güvenlik ayarları
TOKEN_BLACKLIST = set()  # Geçersiz kılınan token'lar
MAX_TOKENS_PER_USER = 5  # Kullanıcı başına maksimum token sayısı
USER_TOKENS = {}  # Kullanıcı token'ları

def get_password_hash(password: str) -> str:
    """Şifreyi hashler.

    Args:
        password: Hashlenecek şifre

    Returns:
        str: Hashlenmiş şifre
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifreyi doğrular.

    Args:
        plain_password: Düz metin şifre
        hashed_password: Hashlenmiş şifre

    Returns:
        bool: Şifre doğruysa True
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """JWT erişim token'ı oluşturur.

    Args:
        data: Token içeriği
        expires_delta: Token geçerlilik süresi

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    # Token ID ekle
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})

    # Kullanıcı token'larını takip et
    username = data.get("sub")
    if username:
        if username not in USER_TOKENS:
            USER_TOKENS[username] = []

        # Maksimum token sayısını kontrol et
        if len(USER_TOKENS[username]) >= MAX_TOKENS_PER_USER:
            # En eski token'ı geçersiz kıl
            old_token_jti = USER_TOKENS[username].pop(0)
            TOKEN_BLACKLIST.add(old_token_jti)

        # Yeni token'ı ekle
        USER_TOKENS[username].append(jti)

    # Son kullanma tarihini ayarla
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # Token oluşturma zamanı
        "type": "access"  # Token tipi
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """JWT yenileme token'ı oluşturur.

    Args:
        data: Token içeriği
        expires_delta: Token geçerlilik süresi

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    # Token ID ekle
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})

    # Son kullanma tarihini ayarla
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # Token oluşturma zamanı
        "type": "refresh"  # Token tipi
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """JWT token'ı çözer.

    Args:
        token: JWT token

    Returns:
        Dict[str, Any]: Token içeriği

    Raises:
        JWTError: Token geçersizse
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """JWT token'ı doğrular.

    Args:
        token: JWT token

    Returns:
        Optional[Dict[str, Any]]: Token geçerliyse içeriği, değilse None
    """
    try:
        # Token'ı çöz
        payload = decode_token(token)

        # Token ID'sini kontrol et
        jti = payload.get("jti")
        if not jti:
            return None

        # Kara listeyi kontrol et
        if jti in TOKEN_BLACKLIST:
            return None

        # Token tipini kontrol et
        token_type = payload.get("type")
        if not token_type:
            return None

        return payload
    except JWTError:
        return None

def invalidate_token(token: str) -> bool:
    """Token'ı geçersiz kılar.

    Args:
        token: JWT token

    Returns:
        bool: Geçersiz kılma başarılı ise True
    """
    try:
        # Token'ı çöz
        payload = decode_token(token)

        # Token ID'sini al
        jti = payload.get("jti")
        if not jti:
            return False

        # Kara listeye ekle
        TOKEN_BLACKLIST.add(jti)

        # Kullanıcı token'larından çıkar
        username = payload.get("sub")
        if username and username in USER_TOKENS and jti in USER_TOKENS[username]:
            USER_TOKENS[username].remove(jti)

        return True
    except JWTError:
        return False

def invalidate_all_user_tokens(username: str) -> bool:
    """Kullanıcının tüm token'larını geçersiz kılar.

    Args:
        username: Kullanıcı adı

    Returns:
        bool: Geçersiz kılma başarılı ise True
    """
    if username not in USER_TOKENS:
        return False

    # Tüm token'ları kara listeye ekle
    for jti in USER_TOKENS[username]:
        TOKEN_BLACKLIST.add(jti)

    # Kullanıcı token'larını temizle
    USER_TOKENS[username] = []

    return True

def clean_token_blacklist() -> int:
    """Süresi dolmuş token'ları kara listeden temizler.

    Returns:
        int: Temizlenen token sayısı
    """
    # Temizlenen token sayısı
    cleaned_count = 0

    # Kara listedeki token'ları kontrol et
    for jti in list(TOKEN_BLACKLIST):
        # Token'ı kullanıcı listesinde ara
        found = False
        for username, tokens in USER_TOKENS.items():
            if jti in tokens:
                found = True
                break

        # Token kullanıcı listesinde yoksa kara listeden çıkar
        if not found:
            TOKEN_BLACKLIST.remove(jti)
            cleaned_count += 1

    return cleaned_count
