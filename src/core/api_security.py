# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# API Güvenlik Modülü

import time
import hmac
import hashlib
import base64
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
from dataclasses import dataclass

@dataclass
class APIKey:
    """API anahtarı bilgileri için veri sınıfı."""
    
    key: str
    secret: str
    owner: str
    permissions: List[str]
    rate_limit: int  # requests per minute
    expires_at: Optional[datetime] = None
    is_active: bool = True

class RateLimiter:
    """İstek sınırlama için sınıf."""
    
    def __init__(self, redis_client: redis.Redis, window: int = 60):
        """RateLimiter başlatıcısı.
        
        Args:
            redis_client: Redis istemcisi
            window: Zaman penceresi (saniye)
        """
        self.redis = redis_client
        self.window = window
    
    async def check_rate_limit(
        self,
        api_key: str,
        limit: int
    ) -> Tuple[bool, int]:
        """İstek limitini kontrol eder.
        
        Args:
            api_key: API anahtarı
            limit: İzin verilen maksimum istek sayısı
            
        Returns:
            Tuple[bool, int]: Limit aşıldı mı, kalan istek sayısı
        """
        current = int(time.time())
        key = f"rate_limit:{api_key}:{current // self.window}"
        
        async with self.redis.pipeline() as pipe:
            try:
                # İstek sayısını artır ve son kullanım zamanını güncelle
                await pipe.watch(key)
                count = await self.redis.get(key) or 0
                count = int(count)
                
                if count >= limit:
                    return True, 0
                
                # Sayacı artır ve süreyi ayarla
                await pipe.multi()
                await pipe.incr(key)
                await pipe.expire(key, self.window)
                await pipe.execute()
                
                remaining = limit - (count + 1)
                return False, remaining
                
            except redis.WatchError:
                # İyimser kilitleme başarısız oldu, tekrar dene
                return await self.check_rate_limit(api_key, limit)

class APIKeyManager:
    """API anahtarı yönetimi için sınıf."""
    
    def __init__(self, redis_client: redis.Redis):
        """APIKeyManager başlatıcısı.
        
        Args:
            redis_client: Redis istemcisi
        """
        self.redis = redis_client
    
    def generate_key_pair(self) -> Tuple[str, str]:
        """Yeni API anahtar çifti oluşturur.
        
        Returns:
            Tuple[str, str]: API anahtarı ve gizli anahtar
        """
        key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        secret = base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8')
        return key, secret
    
    async def create_api_key(
        self,
        owner: str,
        permissions: List[str],
        rate_limit: int,
        expires_in: Optional[int] = None
    ) -> APIKey:
        """Yeni API anahtarı oluşturur.
        
        Args:
            owner: Anahtar sahibi
            permissions: İzinler listesi
            rate_limit: İstek limiti
            expires_in: Geçerlilik süresi (saniye)
            
        Returns:
            APIKey: Oluşturulan anahtar
        """
        key, secret = self.generate_key_pair()
        expires_at = (
            datetime.now() + timedelta(seconds=expires_in)
            if expires_in else None
        )
        
        api_key = APIKey(
            key=key,
            secret=secret,
            owner=owner,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        # Redis'e kaydet
        await self.redis.hset(
            f"api_key:{key}",
            mapping={
                "secret": secret,
                "owner": owner,
                "permissions": json.dumps(permissions),
                "rate_limit": rate_limit,
                "expires_at": expires_at.isoformat() if expires_at else "",
                "is_active": "1"
            }
        )
        
        return api_key
    
    async def get_api_key(self, key: str) -> Optional[APIKey]:
        """API anahtarı bilgilerini getirir.
        
        Args:
            key: API anahtarı
            
        Returns:
            Optional[APIKey]: Anahtar bilgileri veya None
        """
        data = await self.redis.hgetall(f"api_key:{key}")
        if not data:
            return None
            
        return APIKey(
            key=key,
            secret=data[b"secret"].decode(),
            owner=data[b"owner"].decode(),
            permissions=json.loads(data[b"permissions"].decode()),
            rate_limit=int(data[b"rate_limit"]),
            expires_at=datetime.fromisoformat(data[b"expires_at"].decode())
            if data[b"expires_at"] else None,
            is_active=data[b"is_active"].decode() == "1"
        )
    
    async def deactivate_api_key(self, key: str) -> bool:
        """API anahtarını devre dışı bırakır.
        
        Args:
            key: API anahtarı
            
        Returns:
            bool: İşlem başarılı ise True
        """
        return await self.redis.hset(f"api_key:{key}", "is_active", "0") > 0
    
    async def rotate_api_key(self, key: str) -> Optional[APIKey]:
        """API anahtarını yeniler.
        
        Args:
            key: Mevcut API anahtarı
            
        Returns:
            Optional[APIKey]: Yeni anahtar bilgileri veya None
        """
        old_key = await self.get_api_key(key)
        if not old_key or not old_key.is_active:
            return None
        
        # Yeni anahtar oluştur
        new_key = await self.create_api_key(
            owner=old_key.owner,
            permissions=old_key.permissions,
            rate_limit=old_key.rate_limit,
            expires_in=(
                int((old_key.expires_at - datetime.now()).total_seconds())
                if old_key.expires_at else None
            )
        )
        
        # Eski anahtarı devre dışı bırak
        await self.deactivate_api_key(key)
        
        return new_key

class RequestValidator:
    """API istek doğrulama için sınıf."""
    
    def __init__(self, timestamp_tolerance: int = 300):
        """RequestValidator başlatıcısı.
        
        Args:
            timestamp_tolerance: Zaman damgası toleransı (saniye)
        """
        self.timestamp_tolerance = timestamp_tolerance
    
    def generate_signature(
        self,
        secret: str,
        method: str,
        path: str,
        params: Dict[str, Any],
        timestamp: int
    ) -> str:
        """İmza oluşturur.
        
        Args:
            secret: API gizli anahtarı
            method: HTTP metodu
            path: İstek yolu
            params: İstek parametreleri
            timestamp: Zaman damgası
            
        Returns:
            str: İmza
        """
        # İmzalanacak string
        string_to_sign = f"{method}\n{path}\n{json.dumps(params, sort_keys=True)}\n{timestamp}"
        
        # HMAC-SHA256 ile imzala
        signature = hmac.new(
            secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(
        self,
        signature: str,
        secret: str,
        method: str,
        path: str,
        params: Dict[str, Any],
        timestamp: int
    ) -> bool:
        """İmzayı doğrular.
        
        Args:
            signature: Gelen imza
            secret: API gizli anahtarı
            method: HTTP metodu
            path: İstek yolu
            params: İstek parametreleri
            timestamp: Zaman damgası
            
        Returns:
            bool: İmza geçerli ise True
        """
        # Zaman damgası kontrolü
        current_time = int(time.time())
        if abs(current_time - timestamp) > self.timestamp_tolerance:
            return False
        
        # İmza kontrolü
        expected_signature = self.generate_signature(
            secret,
            method,
            path,
            params,
            timestamp
        )
        
        return hmac.compare_digest(signature, expected_signature)

class APISecurityManager:
    """API güvenlik yönetimi için ana sınıf."""
    
    def __init__(self, config: Dict[str, Any]):
        """APISecurityManager başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        
        # Redis bağlantısı
        self.redis = redis.Redis(
            host=config.get("redis_host", "localhost"),
            port=config.get("redis_port", 6379),
            db=config.get("redis_db", 0)
        )
        
        # Alt bileşenler
        self.key_manager = APIKeyManager(self.redis)
        self.rate_limiter = RateLimiter(
            self.redis,
            window=config.get("rate_limit_window", 60)
        )
        self.validator = RequestValidator(
            timestamp_tolerance=config.get("timestamp_tolerance", 300)
        )
    
    async def verify_request(
        self,
        api_key: str,
        signature: str,
        method: str,
        path: str,
        params: Dict[str, Any],
        timestamp: int
    ) -> Tuple[bool, Optional[str]]:
        """API isteğini doğrular.
        
        Args:
            api_key: API anahtarı
            signature: İstek imzası
            method: HTTP metodu
            path: İstek yolu
            params: İstek parametreleri
            timestamp: Zaman damgası
            
        Returns:
            Tuple[bool, Optional[str]]: Doğrulama sonucu ve hata mesajı
        """
        # API anahtarını kontrol et
        key_data = await self.key_manager.get_api_key(api_key)
        if not key_data:
            return False, "Geçersiz API anahtarı"
        
        if not key_data.is_active:
            return False, "Devre dışı bırakılmış API anahtarı"
        
        if key_data.expires_at and datetime.now() > key_data.expires_at:
            return False, "Süresi dolmuş API anahtarı"
        
        # Rate limit kontrolü
        is_limited, remaining = await self.rate_limiter.check_rate_limit(
            api_key,
            key_data.rate_limit
        )
        if is_limited:
            return False, "Rate limit aşıldı"
        
        # İmza doğrulama
        if not self.validator.verify_signature(
            signature,
            key_data.secret,
            method,
            path,
            params,
            timestamp
        ):
            return False, "Geçersiz imza"
        
        return True, None
