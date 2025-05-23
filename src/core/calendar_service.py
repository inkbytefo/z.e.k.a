# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Takvim Servisi Modülü

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from O365 import Account, MSGraphProtocol

class CalendarServiceBase(ABC):
    """Takvim servisleri için temel soyut sınıf.
    
    Bu sınıf, farklı takvim servisleri (Google Calendar, Outlook)
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
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """Kullanıcının takvimlerini listeler.
        
        Returns:
            List[Dict[str, Any]]: Takvim listesi
        """
        pass
    
    @abstractmethod
    async def list_events(
        self,
        calendar_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Belirtilen tarih aralığındaki etkinlikleri listeler.
        
        Args:
            calendar_id: Takvim ID'si
            start_time: Başlangıç zamanı
            end_time: Bitiş zamanı (opsiyonel)
            
        Returns:
            List[Dict[str, Any]]: Etkinlik listesi
        """
        pass
    
    @abstractmethod
    async def create_event(
        self,
        calendar_id: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Yeni bir etkinlik oluşturur.
        
        Args:
            calendar_id: Takvim ID'si
            event_data: Etkinlik verileri
            
        Returns:
            Dict[str, Any]: Oluşturulan etkinlik
        """
        pass

class GoogleCalendarService(CalendarServiceBase):
    """Google Calendar servisi implementasyonu."""
    
    # OAuth 2.0 için gerekli izinler
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, config: Dict[str, Any]):
        """GoogleCalendarService başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.creds = None
        self.service = None
        
    async def authenticate(self) -> bool:
        """Google Calendar için OAuth 2.0 kimlik doğrulaması yapar."""
        try:
            # Token dosyası varsa yükle
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
            
            # Geçerli kimlik bilgisi yoksa veya yenilenebilir değilse
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Yeni kimlik doğrulama akışı
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json',
                        self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Token'ı kaydet
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())
            
            # Calendar API servisini oluştur
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
            
        except Exception as e:
            raise RuntimeError(f"Google Calendar kimlik doğrulama hatası: {str(e)}")
    
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """Kullanıcının Google takvimlerini listeler."""
        try:
            if not self.service:
                await self.authenticate()
                
            calendars = []
            page_token = None
            
            while True:
                # Takvimleri al
                calendar_list = self.service.calendarList().list(
                    pageToken=page_token
                ).execute()
                
                for calendar in calendar_list['items']:
                    calendars.append({
                        'id': calendar['id'],
                        'name': calendar['summary'],
                        'description': calendar.get('description', ''),
                        'timezone': calendar['timeZone']
                    })
                
                page_token = calendar_list.get('nextPageToken')
                if not page_token:
                    break
                    
            return calendars
            
        except HttpError as e:
            raise RuntimeError(f"Takvim listesi alınamadı: {str(e)}")
    
    async def list_events(
        self,
        calendar_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Belirtilen tarih aralığındaki Google Calendar etkinliklerini listeler."""
        try:
            if not self.service:
                await self.authenticate()
                
            if not end_time:
                end_time = start_time + timedelta(days=7)
                
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                events.append({
                    'id': event['id'],
                    'title': event['summary'],
                    'description': event.get('description', ''),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location', ''),
                    'attendees': [
                        {'email': a['email'], 'name': a.get('displayName', '')}
                        for a in event.get('attendees', [])
                    ]
                })
                
            return events
            
        except HttpError as e:
            raise RuntimeError(f"Etkinlik listesi alınamadı: {str(e)}")
    
    async def create_event(
        self,
        calendar_id: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Google Calendar'da yeni bir etkinlik oluşturur."""
        try:
            if not self.service:
                await self.authenticate()
                
            event = {
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start'].isoformat(),
                    'timeZone': event_data.get('timezone', 'UTC'),
                },
                'end': {
                    'dateTime': event_data['end'].isoformat(),
                    'timeZone': event_data.get('timezone', 'UTC'),
                },
                'location': event_data.get('location', ''),
                'attendees': [
                    {'email': a['email']} for a in event_data.get('attendees', [])
                ]
            }
            
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return {
                'id': created_event['id'],
                'title': created_event['summary'],
                'description': created_event.get('description', ''),
                'start': created_event['start'].get('dateTime'),
                'end': created_event['end'].get('dateTime'),
                'location': created_event.get('location', ''),
                'attendees': [
                    {'email': a['email'], 'name': a.get('displayName', '')}
                    for a in created_event.get('attendees', [])
                ]
            }
            
        except HttpError as e:
            raise RuntimeError(f"Etkinlik oluşturulamadı: {str(e)}")

class OutlookCalendarService(CalendarServiceBase):
    """Outlook Calendar servisi implementasyonu."""
    
    def __init__(self, config: Dict[str, Any]):
        """OutlookCalendarService başlatıcısı.
        
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
        """Outlook Calendar için OAuth kimlik doğrulaması yapar."""
        try:
            credentials = (self.client_id, self.client_secret)
            self.account = Account(credentials, auth_flow_type='credentials', tenant_id=self.tenant_id)
            return self.account.authenticate()
            
        except Exception as e:
            raise RuntimeError(f"Outlook Calendar kimlik doğrulama hatası: {str(e)}")
    
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """Kullanıcının Outlook takvimlerini listeler."""
        try:
            if not self.account:
                await self.authenticate()
                
            schedule = self.account.schedule()
            calendars = []
            
            for calendar in schedule.list_calendars():
                calendars.append({
                    'id': calendar.calendar_id,
                    'name': calendar.name,
                    'description': getattr(calendar, 'description', ''),
                    'timezone': getattr(calendar, 'timezone', 'UTC')
                })
                
            return calendars
            
        except Exception as e:
            raise RuntimeError(f"Takvim listesi alınamadı: {str(e)}")
    
    async def list_events(
        self,
        calendar_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Belirtilen tarih aralığındaki Outlook Calendar etkinliklerini listeler."""
        try:
            if not self.account:
                await self.authenticate()
                
            if not end_time:
                end_time = start_time + timedelta(days=7)
                
            schedule = self.account.schedule()
            calendar = schedule.get_calendar(calendar_id)
            q = calendar.new_query('start').greater_equal(start_time)
            q.chain('and').on_attribute('end').less_equal(end_time)
            
            events = []
            for event in calendar.get_events(query=q, include_recurring=True):
                events.append({
                    'id': event.object_id,
                    'title': event.subject,
                    'description': event.body,
                    'start': event.start.isoformat(),
                    'end': event.end.isoformat(),
                    'location': event.location or '',
                    'attendees': [
                        {'email': a.address, 'name': a.name}
                        for a in event.attendees
                    ]
                })
                
            return events
            
        except Exception as e:
            raise RuntimeError(f"Etkinlik listesi alınamadı: {str(e)}")
    
    async def create_event(
        self,
        calendar_id: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Outlook Calendar'da yeni bir etkinlik oluşturur."""
        try:
            if not self.account:
                await self.authenticate()
                
            schedule = self.account.schedule()
            calendar = schedule.get_calendar(calendar_id)
            
            # Yeni etkinlik oluştur
            event = calendar.new_event()
            event.subject = event_data['title']
            event.body = event_data.get('description', '')
            event.start = event_data['start']
            event.end = event_data['end']
            event.location = event_data.get('location', '')
            
            # Katılımcıları ekle
            for attendee in event_data.get('attendees', []):
                event.attendees.add(attendee['email'])
            
            # Etkinliği kaydet
            event.save()
            
            return {
                'id': event.object_id,
                'title': event.subject,
                'description': event.body,
                'start': event.start.isoformat(),
                'end': event.end.isoformat(),
                'location': event.location or '',
                'attendees': [
                    {'email': a.address, 'name': a.name}
                    for a in event.attendees
                ]
            }
            
        except Exception as e:
            raise RuntimeError(f"Etkinlik oluşturulamadı: {str(e)}")
