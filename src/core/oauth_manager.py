# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# OAuth Yönetim Modülü

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import os
import json
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from O365 import Account, MSGraphProtocol

class OAuthManagerBase(ABC):
    """OAuth yönetimi için temel soyut sınıf."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """OAuth yöneticisini başlatır.
        
        Returns:
            bool: Başlatma başarılı ise True
        """
        pass
    
    @abstractmethod
    async def get_token(self, service: str) -> Dict[str, Any]:
        """Belirtilen servis için token bilgilerini getirir.
        
        Args:
            service: Servis adı
            
        Returns:
            Dict[str, Any]: Token bilgileri
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, service: str) -> Dict[str, Any]:
        """Belirtilen servis için token'ı yeniler.
        
        Args:
            service: Servis adı
            
        Returns:
            Dict[str, Any]: Yenilenen token bilgileri
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, service: str) -> bool:
        """Belirtilen servis için token'ı iptal eder.
        
        Args:
            service: Servis adı
            
        Returns:
            bool: İptal başarılı ise True
        """
        pass

class OAuthManager(OAuthManagerBase):
    """OAuth token yönetimi için ana sınıf."""
    
    def __init__(self, config: Dict[str, Any]):
        """OAuthManager başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.encryption_key = None
        self.fernet = None
        self.tokens = {}
        self.token_file = "oauth_tokens.enc"
    
    async def initialize(self) -> bool:
        """OAuth yöneticisini başlatır ve token'ları yükler."""
        try:
            # Şifreleme anahtarını al veya oluştur
            key_file = "oauth.key"
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(self.encryption_key)
            
            self.fernet = Fernet(self.encryption_key)
            
            # Kayıtlı token'ları yükle
            if os.path.exists(self.token_file):
                with open(self.token_file, "rb") as f:
                    encrypted_data = f.read()
                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    self.tokens = json.loads(decrypted_data)
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"OAuth başlatma hatası: {str(e)}")
    
    async def _save_tokens(self) -> None:
        """Token'ları şifreli olarak kaydeder."""
        try:
            encrypted_data = self.fernet.encrypt(
                json.dumps(self.tokens).encode()
            )
            with open(self.token_file, "wb") as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise RuntimeError(f"Token kaydetme hatası: {str(e)}")
    
    async def get_token(self, service: str) -> Dict[str, Any]:
        """Servis için geçerli token bilgilerini getirir."""
        if service not in self.tokens:
            await self._authenticate_service(service)
        
        token_info = self.tokens[service]
        
        # Token süresi dolmuşsa yenile
        if datetime.fromisoformat(token_info['expiry']) <= datetime.now():
            token_info = await self.refresh_token(service)
        
        return token_info
    
    async def _authenticate_service(self, service: str) -> None:
        """Belirtilen servis için kimlik doğrulaması yapar."""
        try:
            if service == "google":
                await self._authenticate_google()
            elif service == "microsoft":
                await self._authenticate_microsoft()
            else:
                raise ValueError(f"Desteklenmeyen servis: {service}")
                
        except Exception as e:
            raise RuntimeError(f"Kimlik doğrulama hatası: {str(e)}")
    
    async def _authenticate_google(self) -> None:
        """Google servisleri için OAuth kimlik doğrulaması."""
        try:
            scopes = self.config["google_scopes"]
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_credentials.json',
                scopes
            )
            creds = flow.run_local_server(port=0)
            
            self.tokens["google"] = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
                "expiry": creds.expiry.isoformat()
            }
            
            await self._save_tokens()
            
        except Exception as e:
            raise RuntimeError(f"Google kimlik doğrulama hatası: {str(e)}")
    
    async def _authenticate_microsoft(self) -> None:
        """Microsoft servisleri için OAuth kimlik doğrulaması."""
        try:
            credentials = (
                self.config["outlook_client_id"],
                self.config["outlook_client_secret"]
            )
            account = Account(
                credentials,
                auth_flow_type='credentials',
                tenant_id=self.config.get("outlook_tenant_id")
            )
            
            if account.authenticate():
                token = account.connection.token_backend.token
                self.tokens["microsoft"] = {
                    "token": token["access_token"],
                    "refresh_token": token.get("refresh_token"),
                    "token_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    "client_id": self.config["outlook_client_id"],
                    "client_secret": self.config["outlook_client_secret"],
                    "scopes": token["scope"].split(),
                    "expiry": (
                        datetime.now() + 
                        timedelta(seconds=token["expires_in"])
                    ).isoformat()
                }
                
                await self._save_tokens()
            else:
                raise RuntimeError("Microsoft kimlik doğrulama başarısız")
                
        except Exception as e:
            raise RuntimeError(f"Microsoft kimlik doğrulama hatası: {str(e)}")
    
    async def refresh_token(self, service: str) -> Dict[str, Any]:
        """Token'ı yeniler."""
        try:
            if service not in self.tokens:
                raise ValueError(f"Servis token'ı bulunamadı: {service}")
            
            token_info = self.tokens[service]
            
            if service == "google":
                creds = Credentials.from_authorized_user_info(token_info)
                
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    
                    self.tokens["google"].update({
                        "token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "expiry": creds.expiry.isoformat()
                    })
                    
            elif service == "microsoft":
                # Microsoft Graph token yenileme
                data = {
                    "client_id": token_info["client_id"],
                    "client_secret": token_info["client_secret"],
                    "refresh_token": token_info["refresh_token"],
                    "grant_type": "refresh_token"
                }
                
                response = requests.post(token_info["token_uri"], data=data)
                new_token = response.json()
                
                if "access_token" in new_token:
                    self.tokens["microsoft"].update({
                        "token": new_token["access_token"],
                        "refresh_token": new_token.get(
                            "refresh_token",
                            token_info["refresh_token"]
                        ),
                        "expiry": (
                            datetime.now() + 
                            timedelta(seconds=new_token["expires_in"])
                        ).isoformat()
                    })
                else:
                    raise RuntimeError("Token yenileme başarısız")
            
            await self._save_tokens()
            return self.tokens[service]
            
        except Exception as e:
            raise RuntimeError(f"Token yenileme hatası: {str(e)}")
    
    async def revoke_token(self, service: str) -> bool:
        """Token'ı iptal eder."""
        try:
            if service not in self.tokens:
                return False
            
            token_info = self.tokens[service]
            
            if service == "google":
                # Google token iptali
                requests.post(
                    "https://accounts.google.com/o/oauth2/revoke",
                    params={"token": token_info["token"]},
                    headers={"content-type": "application/x-www-form-urlencoded"}
                )
                
            elif service == "microsoft":
                # Microsoft token iptali
                headers = {
                    "Authorization": f"Bearer {token_info['token']}"
                }
                requests.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/logout",
                    headers=headers
                )
            
            del self.tokens[service]
            await self._save_tokens()
            return True
            
        except Exception as e:
            raise RuntimeError(f"Token iptal hatası: {str(e)}")
    
    def get_service_credentials(self, service: str) -> Any:
        """Servis için kimlik bilgilerini oluşturur."""
        if service not in self.tokens:
            return None
            
        token_info = self.tokens[service]
        
        if service == "google":
            return Credentials.from_authorized_user_info(token_info)
        elif service == "microsoft":
            return {
                "token": token_info["token"],
                "client_id": token_info["client_id"],
                "client_secret": token_info["client_secret"]
            }
        
        return None
