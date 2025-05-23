# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# MQTT Entegrasyon Modülü

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from enum import Enum
import paho.mqtt.client as mqtt
from datetime import datetime

from ..logging_manager import get_logger

class MQTTQoS(Enum):
    """MQTT QoS (Quality of Service) seviyeleri."""
    AT_MOST_ONCE = 0  # En fazla bir kez (fire and forget)
    AT_LEAST_ONCE = 1  # En az bir kez (onay gerektirir)
    EXACTLY_ONCE = 2  # Tam olarak bir kez (en güvenilir, en yavaş)

class MQTTClient:
    """MQTT protokolü ile IoT cihazlarına bağlanmak için kullanılan sınıf.
    
    Bu sınıf, MQTT broker'ına bağlanarak IoT cihazlarıyla iletişim kurar.
    Mesaj gönderme, alma ve belirli konulara abone olma işlemlerini sağlar.
    """
    
    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        client_id: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False
    ):
        """MQTTClient başlatıcısı.
        
        Args:
            broker_host: MQTT broker adresi
            broker_port: MQTT broker portu (varsayılan: 1883)
            client_id: MQTT istemci ID'si (opsiyonel)
            username: MQTT kullanıcı adı (opsiyonel)
            password: MQTT şifresi (opsiyonel)
            use_ssl: SSL kullanılsın mı (varsayılan: False)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"zeka_mqtt_{os.getpid()}_{datetime.now().timestamp():.0f}"
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        
        self.logger = get_logger("mqtt_client")
        
        # MQTT istemcisi
        self.client = mqtt.Client(client_id=self.client_id)
        
        # Callback'ler
        self.topic_callbacks: Dict[str, List[Callable]] = {}
        self.wildcard_callbacks: Dict[str, List[Callable]] = {}
        
        # Bağlantı durumu
        self.connected = False
        self.connecting = False
        self.connection_error = None
        
        # Asenkron işlemler için event loop
        self.loop = None
        self.future = None
        
        # MQTT callback'lerini ayarla
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        
        # Kimlik bilgilerini ayarla
        if username and password:
            self.client.username_pw_set(username, password)
        
        # SSL ayarları
        if use_ssl:
            self.client.tls_set()
    
    async def connect(self) -> bool:
        """MQTT broker'ına bağlanır.
        
        Returns:
            bool: Bağlantı başarılı ise True
        """
        if self.connected:
            return True
        
        if self.connecting:
            # Bağlantı zaten devam ediyor, tamamlanmasını bekle
            while self.connecting:
                await asyncio.sleep(0.1)
            return self.connected
        
        self.connecting = True
        self.connection_error = None
        
        try:
            # Bağlantı için future oluştur
            self.loop = asyncio.get_event_loop()
            self.future = self.loop.create_future()
            
            # Bağlantıyı başlat
            self.client.connect_async(self.broker_host, self.broker_port)
            
            # MQTT loop'unu başlat
            self.client.loop_start()
            
            # Bağlantının tamamlanmasını bekle
            try:
                await asyncio.wait_for(self.future, timeout=10.0)
                self.logger.info(f"MQTT broker'a bağlandı: {self.broker_host}:{self.broker_port}")
                return True
            except asyncio.TimeoutError:
                self.logger.error("MQTT bağlantı zaman aşımı")
                self.client.loop_stop()
                return False
            
        except Exception as e:
            self.connection_error = str(e)
            self.logger.error(f"MQTT bağlantı hatası: {str(e)}")
            return False
        finally:
            self.connecting = False
    
    async def disconnect(self) -> None:
        """MQTT broker'ından bağlantıyı keser."""
        if self.connected:
            self.client.disconnect()
            self.client.loop_stop()
            self.connected = False
            self.logger.info("MQTT broker'dan bağlantı kesildi")
    
    async def publish(
        self,
        topic: str,
        payload: Union[str, Dict[str, Any], bytes],
        qos: Union[MQTTQoS, int] = MQTTQoS.AT_LEAST_ONCE,
        retain: bool = False
    ) -> bool:
        """Bir konuya mesaj yayınlar.
        
        Args:
            topic: Mesajın yayınlanacağı konu
            payload: Mesaj içeriği (string, dict veya bytes)
            qos: Mesaj QoS seviyesi (varsayılan: AT_LEAST_ONCE)
            retain: Mesaj broker'da tutulsun mu (varsayılan: False)
            
        Returns:
            bool: Yayınlama başarılı ise True
        """
        if not self.connected:
            success = await self.connect()
            if not success:
                return False
        
        try:
            # QoS değerini ayarla
            if isinstance(qos, MQTTQoS):
                qos = qos.value
            
            # Payload'ı hazırla
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            # Mesajı yayınla
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            # Sonucu kontrol et
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"MQTT yayınlama hatası: {mqtt.error_string(result.rc)}")
                return False
            
            self.logger.debug(f"MQTT mesajı yayınlandı: {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"MQTT yayınlama hatası: {str(e)}")
            return False
    
    async def subscribe(
        self,
        topic: str,
        callback: Callable[[str, bytes], None],
        qos: Union[MQTTQoS, int] = MQTTQoS.AT_LEAST_ONCE
    ) -> bool:
        """Bir konuya abone olur.
        
        Args:
            topic: Abone olunacak konu
            callback: Mesaj alındığında çağrılacak fonksiyon
            qos: Abone QoS seviyesi (varsayılan: AT_LEAST_ONCE)
            
        Returns:
            bool: Abonelik başarılı ise True
        """
        if not self.connected:
            success = await self.connect()
            if not success:
                return False
        
        try:
            # QoS değerini ayarla
            if isinstance(qos, MQTTQoS):
                qos = qos.value
            
            # Callback'i kaydet
            if '#' in topic or '+' in topic:
                # Wildcard konu
                if topic not in self.wildcard_callbacks:
                    self.wildcard_callbacks[topic] = []
                self.wildcard_callbacks[topic].append(callback)
            else:
                # Normal konu
                if topic not in self.topic_callbacks:
                    self.topic_callbacks[topic] = []
                self.topic_callbacks[topic].append(callback)
            
            # Konuya abone ol
            result = self.client.subscribe(topic, qos=qos)
            
            # Sonucu kontrol et
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"MQTT abonelik hatası: {mqtt.error_string(result[0])}")
                return False
            
            self.logger.info(f"MQTT konusuna abone olundu: {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"MQTT abonelik hatası: {str(e)}")
            return False
    
    async def unsubscribe(self, topic: str) -> bool:
        """Bir konudan aboneliği kaldırır.
        
        Args:
            topic: Aboneliği kaldırılacak konu
            
        Returns:
            bool: Abonelik kaldırma başarılı ise True
        """
        if not self.connected:
            return False
        
        try:
            # Konudan aboneliği kaldır
            result = self.client.unsubscribe(topic)
            
            # Sonucu kontrol et
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(f"MQTT abonelik kaldırma hatası: {mqtt.error_string(result[0])}")
                return False
            
            # Callback'leri temizle
            if topic in self.topic_callbacks:
                del self.topic_callbacks[topic]
            
            if topic in self.wildcard_callbacks:
                del self.wildcard_callbacks[topic]
            
            self.logger.info(f"MQTT konusundan abonelik kaldırıldı: {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"MQTT abonelik kaldırma hatası: {str(e)}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT bağlantı callback'i."""
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.connected = True
            self.connecting = False
            if self.future and not self.future.done():
                self.future.set_result(True)
            self.logger.info("MQTT broker'a bağlandı")
        else:
            self.connected = False
            self.connecting = False
            self.connection_error = mqtt.error_string(rc)
            if self.future and not self.future.done():
                self.future.set_exception(Exception(f"MQTT bağlantı hatası: {mqtt.error_string(rc)}"))
            self.logger.error(f"MQTT bağlantı hatası: {mqtt.error_string(rc)}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT bağlantı kesme callback'i."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"MQTT beklenmeyen bağlantı kesilmesi: {mqtt.error_string(rc)}")
        else:
            self.logger.info("MQTT broker'dan bağlantı kesildi")
    
    def _on_message(self, client, userdata, msg):
        """MQTT mesaj alma callback'i."""
        topic = msg.topic
        payload = msg.payload
        
        # Doğrudan konu callback'leri
        if topic in self.topic_callbacks:
            for callback in self.topic_callbacks[topic]:
                try:
                    callback(topic, payload)
                except Exception as e:
                    self.logger.error(f"MQTT callback hatası: {str(e)}")
        
        # Wildcard konu callback'leri
        for pattern, callbacks in self.wildcard_callbacks.items():
            if self._topic_matches_pattern(topic, pattern):
                for callback in callbacks:
                    try:
                        callback(topic, payload)
                    except Exception as e:
                        self.logger.error(f"MQTT wildcard callback hatası: {str(e)}")
    
    def _on_publish(self, client, userdata, mid):
        """MQTT yayınlama callback'i."""
        self.logger.debug(f"MQTT mesajı yayınlandı: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """MQTT abonelik callback'i."""
        self.logger.debug(f"MQTT aboneliği tamamlandı: {mid}")
    
    def _on_unsubscribe(self, client, userdata, mid):
        """MQTT abonelik kaldırma callback'i."""
        self.logger.debug(f"MQTT aboneliği kaldırıldı: {mid}")
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Bir konunun wildcard desenine uyup uymadığını kontrol eder.
        
        Args:
            topic: Kontrol edilecek konu
            pattern: Wildcard deseni
            
        Returns:
            bool: Konu desene uyuyorsa True
        """
        if pattern == topic:
            return True
        
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) > len(topic_parts):
            return False
        
        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == '#':
                return True
            
            if pattern_part != '+' and pattern_part != topic_parts[i]:
                return False
            
            if i == len(pattern_parts) - 1 and i < len(topic_parts) - 1:
                return False
        
        return True
