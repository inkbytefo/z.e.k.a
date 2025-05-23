# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# E-posta Servisi Modülü

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from O365 import Account, Message, MSGraphProtocol

class EmailServiceBase(ABC):
    """E-posta servisleri için temel soyut sınıf.
    
    Bu sınıf, farklı e-posta servisleri (Gmail, Outlook)
    için ortak arayüzü tanımlar.
    """
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Servis için kimlik doğrulama yapar.
        
        Returns:
            bool: Kimlik doğrulama başarılı ise True
        """
        pass
    
    @abstractmethod
    async def list_messages(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """E-postaları listeler.
        
        Args:
            folder: Klasör adı
            limit: Maksimum e-posta sayısı
            query: Arama sorgusu
            
        Returns:
            List[Dict[str, Any]]: E-posta listesi
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """E-posta gönderir.
        
        Args:
            to: Alıcı e-posta adresleri
            subject: Konu
            body: İçerik
            cc: CC alıcıları
            bcc: BCC alıcıları
            
        Returns:
            Dict[str, Any]: Gönderilen e-posta bilgileri
        """
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Belirli bir e-postayı getirir.
        
        Args:
            message_id: E-posta ID'si
            
        Returns:
            Dict[str, Any]: E-posta detayları
        """
        pass

class GmailService(EmailServiceBase):
    """Gmail servisi implementasyonu."""
    
    # OAuth 2.0 için gerekli izinler
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """GmailService başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.creds = None
        self.service = None
    
    async def authenticate(self) -> bool:
        """Gmail için OAuth 2.0 kimlik doğrulaması yapar."""
        try:
            # Token dosyası varsa yükle
            if os.path.exists('gmail_token.json'):
                self.creds = Credentials.from_authorized_user_file('gmail_token.json', self.SCOPES)
            
            # Geçerli kimlik bilgisi yoksa veya yenilenebilir değilse
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Yeni kimlik doğrulama akışı
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'gmail_credentials.json',
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Token'ı kaydet
                with open('gmail_token.json', 'w') as token:
                    token.write(self.creds.to_json())
            
            # Gmail API servisini oluştur
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
            
        except Exception as e:
            raise RuntimeError(f"Gmail kimlik doğrulama hatası: {str(e)}")
    
    async def list_messages(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Gmail mesajlarını listeler."""
        try:
            if not self.service:
                await self.authenticate()
            
            # Mesajları al
            messages = []
            request = self.service.users().messages().list(
                userId='me',
                labelIds=[folder],
                maxResults=limit,
                q=query
            )
            
            while request and len(messages) < limit:
                response = request.execute()
                message_list = response.get('messages', [])
                
                for msg in message_list:
                    # Her mesajın detaylarını al
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Mesaj bilgilerini düzenle
                    headers = {
                        header['name']: header['value']
                        for header in message['payload']['headers']
                    }
                    
                    messages.append({
                        'id': message['id'],
                        'subject': headers.get('Subject', ''),
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'date': headers.get('Date', ''),
                        'snippet': message.get('snippet', '')
                    })
                    
                    if len(messages) >= limit:
                        break
                
                request = self.service.users().messages().list_next(request, response)
            
            return messages
            
        except HttpError as e:
            raise RuntimeError(f"Gmail mesaj listesi alınamadı: {str(e)}")
    
    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Gmail üzerinden e-posta gönderir."""
        try:
            if not self.service:
                await self.authenticate()
            
            # MIME mesajını oluştur
            message = MIMEMultipart()
            message['to'] = ', '.join(to)
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            # HTML içeriği ekle
            mime_text = MIMEText(body, 'html')
            message.attach(mime_text)
            
            # Mesajı gönder
            raw_message = {'raw': base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')}
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body=raw_message
            ).execute()
            
            return {
                'id': sent_message['id'],
                'subject': subject,
                'to': to,
                'cc': cc or [],
                'bcc': bcc or [],
                'status': 'sent'
            }
            
        except HttpError as e:
            raise RuntimeError(f"Gmail mesaj gönderilemedi: {str(e)}")
    
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Gmail'den belirli bir mesajı getirir."""
        try:
            if not self.service:
                await self.authenticate()
            
            # Mesaj detaylarını al
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Başlık bilgilerini düzenle
            headers = {
                header['name']: header['value']
                for header in message['payload']['headers']
            }
            
            # İçeriği al
            parts = []
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        text = base64.urlsafe_b64decode(data).decode('utf-8')
                        parts.append(text)
            
            return {
                'id': message['id'],
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'cc': headers.get('Cc', ''),
                'date': headers.get('Date', ''),
                'body': '\n'.join(parts),
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as e:
            raise RuntimeError(f"Gmail mesaj detayları alınamadı: {str(e)}")

class OutlookEmailService(EmailServiceBase):
    """Outlook e-posta servisi implementasyonu."""
    
    def __init__(self, config: Dict[str, Any]):
        """OutlookEmailService başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.account = None
        
        # Microsoft Graph protokolü
        self.protocol = MSGraphProtocol()
        
        # OAuth için kimlik bilgileri
        self.client_id = config["outlook_client_id"]
        self.client_secret = config["outlook_client_secret"]
        self.tenant_id = config.get("outlook_tenant_id")
    
    async def authenticate(self) -> bool:
        """Outlook için OAuth kimlik doğrulaması yapar."""
        try:
            credentials = (self.client_id, self.client_secret)
            self.account = Account(credentials, auth_flow_type='credentials', tenant_id=self.tenant_id)
            return self.account.authenticate()
            
        except Exception as e:
            raise RuntimeError(f"Outlook kimlik doğrulama hatası: {str(e)}")
    
    async def list_messages(
        self,
        folder: str = "Inbox",
        limit: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Outlook mesajlarını listeler."""
        try:
            if not self.account:
                await self.authenticate()
            
            mailbox = self.account.mailbox()
            folder_obj = mailbox.get_folder(folder)
            
            # Arama sorgusu oluştur
            q = folder_obj.new_query()
            if query:
                q.search(query)
            
            messages = []
            for msg in folder_obj.get_messages(limit=limit, query=q):
                messages.append({
                    'id': msg.object_id,
                    'subject': msg.subject,
                    'from': msg.sender.address,
                    'to': [r.address for r in msg.recipients],
                    'date': msg.received.isoformat(),
                    'snippet': msg.body_preview
                })
            
            return messages
            
        except Exception as e:
            raise RuntimeError(f"Outlook mesaj listesi alınamadı: {str(e)}")
    
    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Outlook üzerinden e-posta gönderir."""
        try:
            if not self.account:
                await self.authenticate()
            
            # Yeni mesaj oluştur
            message = Message(parent=self.account)
            message.subject = subject
            message.body = body
            
            # Alıcıları ekle
            for recipient in to:
                message.to.add(recipient)
            
            if cc:
                for recipient in cc:
                    message.cc.add(recipient)
            
            if bcc:
                for recipient in bcc:
                    message.bcc.add(recipient)
            
            # Mesajı gönder
            message.send()
            
            return {
                'id': message.object_id,
                'subject': subject,
                'to': to,
                'cc': cc or [],
                'bcc': bcc or [],
                'status': 'sent'
            }
            
        except Exception as e:
            raise RuntimeError(f"Outlook mesaj gönderilemedi: {str(e)}")
    
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Outlook'tan belirli bir mesajı getirir."""
        try:
            if not self.account:
                await self.authenticate()
            
            mailbox = self.account.mailbox()
            message = mailbox.get_message(message_id)
            
            return {
                'id': message.object_id,
                'subject': message.subject,
                'from': message.sender.address,
                'to': [r.address for r in message.recipients],
                'cc': [r.address for r in message.cc_recipients],
                'date': message.received.isoformat(),
                'body': message.body,
                'snippet': message.body_preview
            }
            
        except Exception as e:
            raise RuntimeError(f"Outlook mesaj detayları alınamadı: {str(e)}")
