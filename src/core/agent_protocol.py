# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ajan İletişim Protokolü Modülü

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import uuid
import logging

@dataclass
class Message:
    """Ajanlar arası mesaj sınıfı."""
    
    id: str
    sender: str
    receiver: str
    type: str
    content: Dict[str, Any]
    priority: int
    timestamp: datetime
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expires_at: Optional[datetime] = None

class MessageQueue:
    """Asenkron mesaj kuyruğu sınıfı."""
    
    def __init__(self, max_size: int = 1000):
        """MessageQueue başlatıcısı.
        
        Args:
            max_size: Maksimum kuyruk boyutu
        """
        self.queue = asyncio.PriorityQueue(maxsize=max_size)
        self._consumers: List[Callable] = []
        self._running = False
    
    async def put(self, message: Message) -> None:
        """Kuyruğa mesaj ekler.
        
        Args:
            message: Eklenecek mesaj
        """
        await self.queue.put((message.priority, message))
    
    async def get(self) -> Optional[Message]:
        """Kuyruktan mesaj alır.
        
        Returns:
            Optional[Message]: Mesaj veya None
        """
        try:
            _, message = await self.queue.get()
            return message
        except asyncio.QueueEmpty:
            return None
    
    def register_consumer(self, callback: Callable) -> None:
        """Mesaj tüketici kaydeder.
        
        Args:
            callback: Mesaj işleyici fonksiyon
        """
        self._consumers.append(callback)
    
    def unregister_consumer(self, callback: Callable) -> None:
        """Mesaj tüketici kaydını siler.
        
        Args:
            callback: Silinecek işleyici fonksiyon
        """
        if callback in self._consumers:
            self._consumers.remove(callback)
    
    async def start(self) -> None:
        """Mesaj işlemeyi başlatır."""
        self._running = True
        while self._running:
            message = await self.get()
            if message:
                for consumer in self._consumers:
                    try:
                        await consumer(message)
                    except Exception as e:
                        logging.error(f"Mesaj işleme hatası: {str(e)}")
    
    def stop(self) -> None:
        """Mesaj işlemeyi durdurur."""
        self._running = False

class AgentProtocol:
    """Ajan iletişim protokolü sınıfı."""
    
    def __init__(self, config: Dict[str, Any]):
        """AgentProtocol başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.queues: Dict[str, MessageQueue] = {}
        self.handlers: Dict[str, Callable] = {}
        self._correlation_map: Dict[str, asyncio.Future] = {}
        self._message_timeout = config.get("message_timeout", 30)  # saniye
        self._retry_limit = config.get("retry_limit", 3)
        self._cleanup_interval = config.get("cleanup_interval", 60)  # saniye
        
        # Otomatik temizlik için task
        asyncio.create_task(self._cleanup_expired_messages())
    
    def create_queue(self, name: str, max_size: int = 1000) -> MessageQueue:
        """Yeni mesaj kuyruğu oluşturur.
        
        Args:
            name: Kuyruk adı
            max_size: Maksimum kuyruk boyutu
            
        Returns:
            MessageQueue: Oluşturulan kuyruk
        """
        queue = MessageQueue(max_size=max_size)
        self.queues[name] = queue
        return queue
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Mesaj işleyici kaydeder.
        
        Args:
            message_type: Mesaj tipi
            handler: İşleyici fonksiyon
        """
        self.handlers[message_type] = handler
    
    async def send_message(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        content: Dict[str, Any],
        priority: int = 0,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Optional[Message]:
        """Mesaj gönderir.
        
        Args:
            sender: Gönderici ID'si
            receiver: Alıcı ID'si
            message_type: Mesaj tipi
            content: Mesaj içeriği
            priority: Mesaj önceliği
            correlation_id: İlişki ID'si
            reply_to: Yanıt mesaj ID'si
            timeout: Zaman aşımı süresi
            
        Returns:
            Optional[Message]: Yanıt mesajı veya None
        """
        message = Message(
            id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            type=message_type,
            content=content,
            priority=priority,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            reply_to=reply_to,
            expires_at=datetime.now().timestamp() + (timeout or self._message_timeout)
            if timeout is not None or self._message_timeout is not None
            else None
        )
        
        # Yanıt bekliyorsa future oluştur
        if correlation_id:
            future = asyncio.Future()
            self._correlation_map[correlation_id] = future
        
        # Kuyruğa ekle
        if receiver in self.queues:
            await self.queues[receiver].put(message)
            
            # Yanıt bekle
            if correlation_id:
                try:
                    response = await asyncio.wait_for(
                        future,
                        timeout=timeout or self._message_timeout
                    )
                    return response
                except asyncio.TimeoutError:
                    del self._correlation_map[correlation_id]
                    return None
        
        return None
    
    async def handle_message(self, message: Message) -> None:
        """Mesajı işler.
        
        Args:
            message: İşlenecek mesaj
        """
        try:
            # Zaman aşımı kontrolü
            if message.expires_at and datetime.now().timestamp() > message.expires_at:
                logging.warning(f"Mesaj zaman aşımına uğradı: {message.id}")
                return
            
            # İlgili işleyiciyi bul ve çalıştır
            if message.type in self.handlers:
                handler = self.handlers[message.type]
                response = await handler(message)
                
                # Yanıt verilecekse gönder
                if message.correlation_id and response:
                    await self.send_message(
                        sender=message.receiver,
                        receiver=message.sender,
                        message_type=f"{message.type}_response",
                        content=response,
                        correlation_id=message.correlation_id,
                        reply_to=message.id
                    )
            else:
                logging.warning(f"İşleyici bulunamadı: {message.type}")
                
        except Exception as e:
            logging.error(f"Mesaj işleme hatası: {str(e)}")
            
            # Hata yanıtı gönder
            if message.correlation_id:
                await self.send_message(
                    sender=message.receiver,
                    receiver=message.sender,
                    message_type=f"{message.type}_error",
                    content={"error": str(e)},
                    correlation_id=message.correlation_id,
                    reply_to=message.id
                )
    
    async def _cleanup_expired_messages(self) -> None:
        """Zamanı geçmiş mesajları temizler."""
        while True:
            now = datetime.now().timestamp()
            
            # Zamanı geçmiş correlation ID'leri temizle
            expired_correlations = [
                cid for cid, future in self._correlation_map.items()
                if not future.done() and future.get_loop().time() + self._message_timeout < now
            ]
            
            for cid in expired_correlations:
                if cid in self._correlation_map:
                    self._correlation_map[cid].cancel()
                    del self._correlation_map[cid]
            
            await asyncio.sleep(self._cleanup_interval)
    
    def start_all_queues(self) -> None:
        """Tüm kuyrukları başlatır."""
        for queue in self.queues.values():
            asyncio.create_task(queue.start())
    
    def stop_all_queues(self) -> None:
        """Tüm kuyrukları durdurur."""
        for queue in self.queues.values():
            queue.stop()
