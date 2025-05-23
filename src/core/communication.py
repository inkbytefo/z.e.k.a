# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# İletişim Protokolü Modülü

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any
import asyncio
import json
import uuid
from datetime import datetime

class MessageType(Enum):
    """İletişim mesajlarının türlerini tanımlar."""
    TASK_REQUEST = auto()      # Görev isteği
    TASK_RESPONSE = auto()     # Görev yanıtı
    SUBTASK_REQUEST = auto()   # Alt görev isteği
    SUBTASK_RESPONSE = auto()  # Alt görev yanıtı
    COLLABORATION = auto()     # İşbirliği mesajı
    STATUS_UPDATE = auto()     # Durum güncelleme
    ERROR = auto()             # Hata bildirimi

class TaskPriority(Enum):
    """Görev öncelik seviyeleri."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

class TaskStatus(Enum):
    """Görev durumu."""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class Message:
    """Ajanlar arası iletişim için standart mesaj formatı."""
    id: str
    type: MessageType
    sender_id: str
    receiver_id: str
    content: Dict[str, Any]
    priority: TaskPriority
    timestamp: datetime
    parent_task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CommunicationManager:
    """Ajanlar arası iletişimi yöneten merkezi sınıf."""
    
    def __init__(self):
        """İletişim yöneticisi başlatıcısı."""
        self.message_queue = asyncio.Queue()
        self.active_tasks: Dict[str, Dict] = {}
        self.subscribers: Dict[str, List[callable]] = {}
        self.task_histories: Dict[str, List[Message]] = {}
    
    def create_message(
        self,
        msg_type: MessageType,
        sender_id: str,
        receiver_id: str,
        content: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Yeni bir mesaj oluşturur.
        
        Args:
            msg_type: Mesaj türü
            sender_id: Gönderen ajan ID'si
            receiver_id: Alıcı ajan ID'si
            content: Mesaj içeriği
            priority: Görev önceliği
            parent_task_id: Üst görev ID'si (varsa)
            metadata: Ek meta veriler
            
        Returns:
            Message: Oluşturulan mesaj nesnesi
        """
        return Message(
            id=str(uuid.uuid4()),
            type=msg_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            priority=priority,
            timestamp=datetime.now(),
            parent_task_id=parent_task_id,
            metadata=metadata or {}
        )
    
    async def send_message(self, message: Message) -> None:
        """Mesajı gönderir ve kuyruğa ekler.
        
        Args:
            message: Gönderilecek mesaj
        """
        await self.message_queue.put(message)
        self._update_task_history(message)
        await self._notify_subscribers(message)
    
    async def get_message(self) -> Message:
        """Kuyruktan bir mesaj alır.
        
        Returns:
            Message: Alınan mesaj
        """
        return await self.message_queue.get()
    
    def subscribe(self, agent_id: str, callback: callable) -> None:
        """Bir ajanı mesaj almak üzere abone yapar.
        
        Args:
            agent_id: Abone olacak ajanın ID'si
            callback: Mesaj alındığında çağrılacak fonksiyon
        """
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
    
    def unsubscribe(self, agent_id: str, callback: callable) -> None:
        """Bir ajanın aboneliğini kaldırır.
        
        Args:
            agent_id: Aboneliği kaldırılacak ajanın ID'si
            callback: Kaldırılacak callback fonksiyonu
        """
        if agent_id in self.subscribers and callback in self.subscribers[agent_id]:
            self.subscribers[agent_id].remove(callback)
    
    async def _notify_subscribers(self, message: Message) -> None:
        """İlgili abonelere mesajı bildirir.
        
        Args:
            message: Bildirilecek mesaj
        """
        if message.receiver_id in self.subscribers:
            for callback in self.subscribers[message.receiver_id]:
                try:
                    await callback(message)
                except Exception as e:
                    print(f"Callback hatası {e}")
    
    def _update_task_history(self, message: Message) -> None:
        """Görev geçmişini günceller.
        
        Args:
            message: Kaydedilecek mesaj
        """
        task_id = message.parent_task_id or message.id
        if task_id not in self.task_histories:
            self.task_histories[task_id] = []
        self.task_histories[task_id].append(message)
    
    def get_task_history(self, task_id: str) -> List[Message]:
        """Bir görevin mesaj geçmişini getirir.
        
        Args:
            task_id: Görev ID'si
            
        Returns:
            List[Message]: Görev mesajları listesi
        """
        return self.task_histories.get(task_id, [])
    
    def analyze_task_flow(self, task_id: str) -> Dict[str, Any]:
        """Görev akışını analiz eder.
        
        Args:
            task_id: Görev ID'si
            
        Returns:
            Dict[str, Any]: Analiz sonuçları
        """
        history = self.get_task_history(task_id)
        if not history:
            return {"error": "Görev geçmişi bulunamadı"}
            
        analysis = {
            "task_id": task_id,
            "start_time": history[0].timestamp,
            "end_time": history[-1].timestamp if history else None,
            "total_messages": len(history),
            "participating_agents": list(set(msg.sender_id for msg in history)),
            "status": self._determine_task_status(history),
            "error_count": sum(1 for msg in history if msg.type == MessageType.ERROR)
        }
        
        return analysis
    
    def _determine_task_status(self, history: List[Message]) -> TaskStatus:
        """Mesaj geçmişinden görev durumunu belirler.
        
        Args:
            history: Mesaj geçmişi
            
        Returns:
            TaskStatus: Belirlenen görev durumu
        """
        if not history:
            return TaskStatus.PENDING
            
        last_message = history[-1]
        
        if last_message.type == MessageType.ERROR:
            return TaskStatus.FAILED
        elif last_message.type == MessageType.TASK_RESPONSE:
            return TaskStatus.COMPLETED
        elif any(msg.type == MessageType.TASK_REQUEST for msg in history):
            return TaskStatus.IN_PROGRESS
            
        return TaskStatus.PENDING
