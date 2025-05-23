# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Takvim Ajanı Modülü

from typing import Dict, Any, Set, Optional
from datetime import datetime, timedelta
import asyncio
import json

from ..core.agent_base import Agent
from ..core.communication import MessageType, TaskStatus, TaskPriority

class CalendarAgent(Agent):
    """Takvim ve toplantı yönetimi için uzmanlaşmış ajan.

    Bu ajan, kullanıcının takvim etkinliklerini yönetir, toplantıları planlar,
    hatırlatıcılar oluşturur ve takvim çakışmalarını çözer.
    """

    def __init__(self, agent_id="calendar_agent", name="Takvim Ajanı", description="Takvim ve toplantı yönetimi yapan ajan"):
        """Takvim ajanı başlatıcısı.

        Args:
            agent_id: Ajan ID'si
            name: Ajan adı
            description: Ajan açıklaması
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities={"calendar_management", "scheduling", "reminder_setting"}
        )
        self.calendar_provider = None
        self.default_reminder_minutes = 15
        self.busy_times = {}  # Çakışma kontrolü için

    def set_calendar_provider(self, provider: str, credentials: Optional[Dict[str, Any]] = None) -> None:
        """Takvim sağlayıcısını ayarlar.

        Args:
            provider: Sağlayıcı adı (google, outlook, vb.)
            credentials: Kimlik bilgileri
        """
        self.calendar_provider = provider
        # Burada sağlayıcıya özgü kimlik doğrulama ve bağlantı kurma işlemleri yapılacak
        print(f"{provider} takvim sağlayıcısı ayarlandı.")

    async def process_task(
        self,
        task_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bir görevi işler.

        Args:
            task_id: Görev ID'si
            description: Görev açıklaması
            metadata: Görev meta verileri

        Returns:
            Dict[str, Any]: Görev sonucu
        """
        intent = metadata.get("intent")
        entities = metadata.get("entities", {})
        action = entities.get("action", "unknown")

        try:
            # Bellek ve kullanıcı tercihlerini kontrol et
            preferences = self.get_user_preferences("calendar")
            relevant_memory = self.get_relevant_memory(description)

            # İşlem türüne göre yönlendir
            if action == "create":
                result = await self._create_event(description, metadata, preferences)
            elif action == "check":
                result = await self._list_events(description, metadata, preferences)
            elif action == "update":
                result = await self._update_event(description, metadata, preferences)
            elif action == "delete":
                result = await self._delete_event(description, metadata, preferences)
            elif action == "remind":
                result = await self._set_reminder(description, metadata, preferences)
            else:
                result = {
                    "success": False,
                    "message": "Anlaşılamayan takvim işlemi. Lütfen daha açık bir ifade kullanın.",
                    "action_needed": "clarification"
                }

            return result

        except Exception as e:
            return {
                "success": False,
                "message": f"İşlem sırasında bir hata oluştu: {str(e)}",
                "error": str(e)
            }

    async def _create_event(
        self,
        description: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Yeni bir takvim etkinliği oluşturur.

        Args:
            description: Görev açıklaması
            metadata: Görev meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        # Etkinlik detaylarını çıkar
        event_details = await self._extract_event_details(description)

        # Çakışma kontrolü
        conflicts = await self._check_conflicts(
            event_details["start_time"],
            event_details["end_time"]
        )

        if conflicts:
            return {
                "success": False,
                "message": "Bu zaman diliminde çakışan etkinlikler var.",
                "conflicts": conflicts,
                "action_needed": "resolve_conflicts"
            }

        # Etkinliği oluştur
        # Burada gerçek takvim API'si kullanılacak
        event = {
            "title": event_details["title"],
            "start_time": event_details["start_time"],
            "end_time": event_details["end_time"],
            "description": event_details.get("description", ""),
            "location": event_details.get("location"),
            "attendees": event_details.get("attendees", []),
            "reminder": event_details.get("reminder", self.default_reminder_minutes)
        }

        # Meşgul zamanları güncelle
        self.busy_times[event["start_time"]] = event

        return {
            "success": True,
            "message": "Etkinlik başarıyla oluşturuldu.",
            "event": event
        }

    async def _list_events(
        self,
        description: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Takvim etkinliklerini listeler.

        Args:
            description: Görev açıklaması
            metadata: Görev meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        # Zaman aralığını belirle
        time_range = await self._extract_time_range(description)

        # Etkinlikleri getir
        # Burada gerçek takvim API'si kullanılacak
        events = [
            event for start_time, event in self.busy_times.items()
            if time_range["start"] <= start_time <= time_range["end"]
        ]

        return {
            "success": True,
            "message": f"{len(events)} etkinlik bulundu.",
            "events": events,
            "time_range": time_range
        }

    async def _update_event(
        self,
        description: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mevcut bir etkinliği günceller.

        Args:
            description: Görev açıklaması
            metadata: Görev meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        # Güncellenecek etkinliği bul
        event_details = await self._extract_event_details(description)

        # Etkinliği güncelle
        # Burada gerçek takvim API'si kullanılacak

        return {
            "success": True,
            "message": "Etkinlik başarıyla güncellendi.",
            "updated_event": event_details
        }

    async def _delete_event(
        self,
        description: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bir etkinliği siler.

        Args:
            description: Görev açıklaması
            metadata: Görev meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        # Silinecek etkinliği bul
        event_details = await self._extract_event_details(description)

        # Etkinliği sil
        # Burada gerçek takvim API'si kullanılacak

        # Meşgul zamanlardan kaldır
        if event_details.get("start_time") in self.busy_times:
            del self.busy_times[event_details["start_time"]]

        return {
            "success": True,
            "message": "Etkinlik başarıyla silindi.",
            "deleted_event": event_details
        }

    async def _set_reminder(
        self,
        description: str,
        metadata: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Hatırlatıcı ayarlar.

        Args:
            description: Görev açıklaması
            metadata: Görev meta verileri
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        # Hatırlatıcı detaylarını çıkar
        reminder_details = await self._extract_reminder_details(description)

        # Hatırlatıcıyı ayarla
        # Burada gerçek takvim API'si kullanılacak

        return {
            "success": True,
            "message": "Hatırlatıcı başarıyla ayarlandı.",
            "reminder": reminder_details
        }

    async def _extract_event_details(self, description: str) -> Dict[str, Any]:
        """Açıklamadan etkinlik detaylarını çıkarır.

        Args:
            description: Etkinlik açıklaması

        Returns:
            Dict[str, Any]: Etkinlik detayları
        """
        # Gelecekte NLP ile geliştirilecek
        # Şimdilik basit bir örnek:
        return {
            "title": "Örnek Etkinlik",
            "start_time": datetime.now() + timedelta(hours=1),
            "end_time": datetime.now() + timedelta(hours=2),
            "description": description,
            "location": None,
            "attendees": []
        }

    async def _extract_time_range(self, description: str) -> Dict[str, datetime]:
        """Açıklamadan zaman aralığını çıkarır.

        Args:
            description: Açıklama metni

        Returns:
            Dict[str, datetime]: Başlangıç ve bitiş zamanları
        """
        # Gelecekte NLP ile geliştirilecek
        # Şimdilik bugünü döndür
        now = datetime.now()
        return {
            "start": now.replace(hour=0, minute=0, second=0),
            "end": now.replace(hour=23, minute=59, second=59)
        }

    async def _extract_reminder_details(self, description: str) -> Dict[str, Any]:
        """Açıklamadan hatırlatıcı detaylarını çıkarır.

        Args:
            description: Açıklama metni

        Returns:
            Dict[str, Any]: Hatırlatıcı detayları
        """
        # Gelecekte NLP ile geliştirilecek
        return {
            "event_id": "sample_event_id",
            "minutes_before": self.default_reminder_minutes,
            "notification_type": "email"
        }

    async def _check_conflicts(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> list:
        """Zaman aralığındaki çakışmaları kontrol eder.

        Args:
            start_time: Başlangıç zamanı
            end_time: Bitiş zamanı

        Returns:
            list: Çakışan etkinlikler listesi
        """
        conflicts = []

        for event_time, event in self.busy_times.items():
            if (start_time <= event_time <= end_time or
                start_time <= event["end_time"] <= end_time):
                conflicts.append(event)

        return conflicts
