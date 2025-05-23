# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Home Assistant Entegrasyon Modülü

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import aiohttp
from datetime import datetime

from ..logging_manager import get_logger

class EntityType(Enum):
    """Home Assistant varlık tipleri."""
    LIGHT = "light"
    SWITCH = "switch"
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    CLIMATE = "climate"
    MEDIA_PLAYER = "media_player"
    CAMERA = "camera"
    COVER = "cover"
    FAN = "fan"
    LOCK = "lock"
    VACUUM = "vacuum"
    SCENE = "scene"
    SCRIPT = "script"
    AUTOMATION = "automation"
    WEATHER = "weather"
    PERSON = "person"
    ZONE = "zone"
    OTHER = "other"

class HomeAssistantBridge:
    """Home Assistant ile entegrasyon sağlayan sınıf.
    
    Bu sınıf, Home Assistant API'si üzerinden cihazları kontrol etmek,
    durumlarını almak ve otomasyonları çalıştırmak için kullanılır.
    """
    
    def __init__(
        self,
        host: str,
        token: str,
        port: int = 8123,
        use_ssl: bool = False
    ):
        """HomeAssistantBridge başlatıcısı.
        
        Args:
            host: Home Assistant sunucu adresi
            token: Home Assistant API token'ı (Long-Lived Access Token)
            port: Home Assistant sunucu portu (varsayılan: 8123)
            use_ssl: SSL kullanılsın mı (varsayılan: False)
        """
        protocol = "https" if use_ssl else "http"
        self.base_url = f"{protocol}://{host}:{port}/api"
        self.websocket_url = f"{'wss' if use_ssl else 'ws'}://{host}:{port}/api/websocket"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.logger = get_logger("home_assistant")
        
        # WebSocket bağlantısı
        self.ws_connection = None
        self.ws_task = None
        self.ws_id = 1
        self.ws_callbacks = {}
        self.ws_connected = False
        
        # Önbellek
        self.states_cache = {}
        self.entities_cache = {}
        self.last_cache_update = None
        self.cache_ttl = 60  # saniye
    
    async def initialize(self) -> bool:
        """Home Assistant bağlantısını başlatır.
        
        Returns:
            bool: Başlatma başarılı ise True
        """
        try:
            # API bağlantısını test et
            await self.get_states()
            
            # WebSocket bağlantısını başlat
            self.ws_task = asyncio.create_task(self._websocket_listener())
            
            self.logger.info("Home Assistant bağlantısı başlatıldı")
            return True
        except Exception as e:
            self.logger.error(f"Home Assistant bağlantısı başlatılamadı: {str(e)}")
            return False
    
    async def get_states(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Tüm cihaz durumlarını getirir.
        
        Args:
            use_cache: Önbellek kullanılsın mı
            
        Returns:
            List[Dict[str, Any]]: Cihaz durumları listesi
        """
        # Önbellek kontrolü
        if use_cache and self.last_cache_update:
            cache_age = (datetime.now() - self.last_cache_update).total_seconds()
            if cache_age < self.cache_ttl and self.states_cache:
                return self.states_cache
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/states",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")
                    
                    states = await response.json()
                    
                    # Önbelleğe ekle
                    self.states_cache = states
                    self.last_cache_update = datetime.now()
                    
                    # Varlık önbelleğini güncelle
                    self._update_entities_cache(states)
                    
                    return states
        except Exception as e:
            self.logger.error(f"Cihaz durumları alınamadı: {str(e)}")
            raise
    
    async def get_state(self, entity_id: str) -> Dict[str, Any]:
        """Belirli bir cihazın durumunu getirir.
        
        Args:
            entity_id: Cihaz ID'si
            
        Returns:
            Dict[str, Any]: Cihaz durumu
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/states/{entity_id}",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")
                    
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Cihaz durumu alınamadı: {str(e)}")
            raise
    
    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Bir servisi çağırır.
        
        Args:
            domain: Servis domain'i (light, switch, vb.)
            service: Servis adı (turn_on, turn_off, vb.)
            entity_id: Cihaz ID'si (opsiyonel)
            data: Servis verileri (opsiyonel)
            
        Returns:
            List[Dict[str, Any]]: Servis çağrısı sonucu
        """
        try:
            payload = data or {}
            if entity_id:
                payload["entity_id"] = entity_id
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/services/{domain}/{service}",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")
                    
                    result = await response.json()
                    
                    # Önbelleği güncelle
                    self.last_cache_update = None
                    
                    return result
        except Exception as e:
            self.logger.error(f"Servis çağrılamadı: {str(e)}")
            raise
    
    async def get_entities_by_type(self, entity_type: Union[EntityType, str]) -> List[Dict[str, Any]]:
        """Belirli tipteki cihazları getirir.
        
        Args:
            entity_type: Cihaz tipi
            
        Returns:
            List[Dict[str, Any]]: Cihaz listesi
        """
        if isinstance(entity_type, EntityType):
            entity_type = entity_type.value
        
        try:
            # Tüm durumları al
            states = await self.get_states()
            
            # Belirli tipteki cihazları filtrele
            entities = []
            for state in states:
                if state["entity_id"].startswith(f"{entity_type}."):
                    entities.append(state)
            
            return entities
        except Exception as e:
            self.logger.error(f"Cihazlar getirilemedi: {str(e)}")
            raise
    
    async def get_config(self) -> Dict[str, Any]:
        """Home Assistant yapılandırmasını getirir.
        
        Returns:
            Dict[str, Any]: Yapılandırma
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/config",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")
                    
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Yapılandırma alınamadı: {str(e)}")
            raise
    
    async def get_history(
        self,
        entity_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """Cihaz geçmişini getirir.
        
        Args:
            entity_id: Cihaz ID'si
            start_time: Başlangıç zamanı (ISO 8601 formatında)
            end_time: Bitiş zamanı (ISO 8601 formatında)
            
        Returns:
            List[List[Dict[str, Any]]]: Geçmiş listesi
        """
        try:
            url = f"{self.base_url}/history/period"
            if start_time:
                url += f"/{start_time}"
            
            params = {"filter_entity_id": entity_id}
            if end_time:
                params["end_time"] = end_time
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Home Assistant API hatası: {response.status} - {error_text}")
                        raise Exception(f"Home Assistant API hatası: {response.status}")
                    
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Geçmiş alınamadı: {str(e)}")
            raise
    
    async def _websocket_listener(self) -> None:
        """WebSocket dinleyici görevi."""
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.websocket_url) as ws:
                        self.ws_connection = ws
                        self.logger.info("Home Assistant WebSocket bağlantısı kuruldu")
                        
                        # Kimlik doğrulama
                        auth_msg = await ws.receive_json()
                        if auth_msg["type"] == "auth_required":
                            await ws.send_json({
                                "type": "auth",
                                "access_token": self.headers["Authorization"].split(" ")[1]
                            })
                            
                            auth_result = await ws.receive_json()
                            if auth_result["type"] != "auth_ok":
                                self.logger.error(f"WebSocket kimlik doğrulama hatası: {auth_result}")
                                break
                            
                            self.ws_connected = True
                            self.logger.info("WebSocket kimlik doğrulama başarılı")
                        
                        # Olay aboneliği
                        await self._subscribe_to_events(ws)
                        
                        # Mesajları dinle
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                await self._handle_websocket_message(data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                self.logger.error(f"WebSocket hatası: {ws.exception()}")
                                break
                        
                        self.ws_connected = False
                        self.logger.info("Home Assistant WebSocket bağlantısı kapatıldı")
            
            except Exception as e:
                self.ws_connected = False
                self.logger.error(f"WebSocket bağlantı hatası: {str(e)}")
                await asyncio.sleep(5)  # Yeniden bağlanmadan önce bekle
    
    async def _subscribe_to_events(self, ws) -> None:
        """Olaylara abone ol.
        
        Args:
            ws: WebSocket bağlantısı
        """
        # Durum değişikliklerine abone ol
        await ws.send_json({
            "id": self.ws_id,
            "type": "subscribe_events",
            "event_type": "state_changed"
        })
        self.ws_id += 1
        
        # Diğer olaylara abone ol
        event_types = ["automation_triggered", "script_started", "service_executed"]
        for event_type in event_types:
            await ws.send_json({
                "id": self.ws_id,
                "type": "subscribe_events",
                "event_type": event_type
            })
            self.ws_id += 1
    
    async def _handle_websocket_message(self, data: Dict[str, Any]) -> None:
        """WebSocket mesajını işle.
        
        Args:
            data: Mesaj verisi
        """
        if data.get("type") == "event" and data.get("event", {}).get("event_type") == "state_changed":
            # Durum değişikliği olayı
            event_data = data["event"]["data"]
            entity_id = event_data["entity_id"]
            new_state = event_data["new_state"]
            
            # Önbelleği güncelle
            if self.states_cache:
                for i, state in enumerate(self.states_cache):
                    if state["entity_id"] == entity_id:
                        self.states_cache[i] = new_state
                        break
            
            # Varlık önbelleğini güncelle
            if entity_id in self.entities_cache:
                self.entities_cache[entity_id] = new_state
            
            self.logger.debug(f"Durum değişikliği: {entity_id} = {new_state.get('state')}")
        
        # Callback'leri çağır
        if "id" in data and data["id"] in self.ws_callbacks:
            callback, args, kwargs = self.ws_callbacks[data["id"]]
            try:
                await callback(data, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"WebSocket callback hatası: {str(e)}")
            
            # Tek seferlik callback'i temizle
            del self.ws_callbacks[data["id"]]
    
    def _update_entities_cache(self, states: List[Dict[str, Any]]) -> None:
        """Varlık önbelleğini güncelle.
        
        Args:
            states: Cihaz durumları listesi
        """
        for state in states:
            entity_id = state["entity_id"]
            self.entities_cache[entity_id] = state
    
    async def close(self) -> None:
        """Bağlantıyı kapat."""
        if self.ws_task:
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                pass
            self.ws_task = None
        
        if self.ws_connection:
            await self.ws_connection.close()
            self.ws_connection = None
        
        self.ws_connected = False
        self.logger.info("Home Assistant bağlantısı kapatıldı")
