# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# IoT Cihaz Yönetim Modülü

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from enum import Enum
from datetime import datetime

from ..logging_manager import get_logger
from .home_assistant import HomeAssistantBridge, EntityType
from .mqtt_client import MQTTClient, MQTTQoS

class DeviceType(Enum):
    """IoT cihaz tipleri."""
    LIGHT = "light"
    SWITCH = "switch"
    SENSOR = "sensor"
    THERMOSTAT = "thermostat"
    CAMERA = "camera"
    LOCK = "lock"
    SPEAKER = "speaker"
    TV = "tv"
    VACUUM = "vacuum"
    FAN = "fan"
    BLIND = "blind"
    OUTLET = "outlet"
    UNKNOWN = "unknown"

class DevicePlatform(Enum):
    """IoT cihaz platformları."""
    HOME_ASSISTANT = "home_assistant"
    MQTT = "mqtt"
    TUYA = "tuya"
    WEMO = "wemo"
    TP_LINK = "tp_link"
    CUSTOM = "custom"
    UNKNOWN = "unknown"

class DeviceCapability(Enum):
    """IoT cihaz yetenekleri."""
    POWER = "power"  # Açma/kapama
    BRIGHTNESS = "brightness"  # Parlaklık
    COLOR = "color"  # Renk
    TEMPERATURE = "temperature"  # Sıcaklık
    HUMIDITY = "humidity"  # Nem
    MOTION = "motion"  # Hareket
    DOOR = "door"  # Kapı durumu
    BATTERY = "battery"  # Pil durumu
    VOLUME = "volume"  # Ses seviyesi
    CHANNEL = "channel"  # Kanal
    LOCK = "lock"  # Kilit
    FAN_SPEED = "fan_speed"  # Fan hızı
    MODE = "mode"  # Mod
    POSITION = "position"  # Konum (perde, panjur vb.)

class IoTDevice:
    """IoT cihazı temsil eden sınıf.
    
    Bu sınıf, farklı platformlardaki IoT cihazlarını temsil eder
    ve ortak bir arayüz sağlar.
    """
    
    def __init__(
        self,
        device_id: str,
        name: str,
        device_type: Union[DeviceType, str],
        platform: Union[DevicePlatform, str],
        capabilities: List[Union[DeviceCapability, str]],
        platform_data: Dict[str, Any]
    ):
        """IoTDevice başlatıcısı.
        
        Args:
            device_id: Cihaz ID'si
            name: Cihaz adı
            device_type: Cihaz tipi
            platform: Cihaz platformu
            capabilities: Cihaz yetenekleri
            platform_data: Platform özel veriler
        """
        self.device_id = device_id
        self.name = name
        
        # Enum dönüşümleri
        self.device_type = device_type if isinstance(device_type, DeviceType) else DeviceType(device_type)
        self.platform = platform if isinstance(platform, DevicePlatform) else DevicePlatform(platform)
        self.capabilities = []
        for cap in capabilities:
            if isinstance(cap, DeviceCapability):
                self.capabilities.append(cap)
            else:
                self.capabilities.append(DeviceCapability(cap))
        
        self.platform_data = platform_data
        self.state = {}
        self.last_updated = None
        self.available = False
    
    def update_state(self, state: Dict[str, Any]) -> None:
        """Cihaz durumunu günceller.
        
        Args:
            state: Yeni durum
        """
        self.state = state
        self.last_updated = datetime.now()
        self.available = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Cihazı sözlük olarak döndürür.
        
        Returns:
            Dict[str, Any]: Cihaz bilgileri
        """
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.device_type.value,
            "platform": self.platform.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "state": self.state,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "available": self.available
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IoTDevice':
        """Sözlükten cihaz oluşturur.
        
        Args:
            data: Cihaz bilgileri
            
        Returns:
            IoTDevice: Oluşturulan cihaz
        """
        device = cls(
            device_id=data["device_id"],
            name=data["name"],
            device_type=data["device_type"],
            platform=data["platform"],
            capabilities=data["capabilities"],
            platform_data=data.get("platform_data", {})
        )
        
        if "state" in data:
            device.state = data["state"]
        
        if "last_updated" in data and data["last_updated"]:
            device.last_updated = datetime.fromisoformat(data["last_updated"])
        
        if "available" in data:
            device.available = data["available"]
        
        return device

class IoTDeviceManager:
    """IoT cihazlarını yöneten sınıf.
    
    Bu sınıf, farklı platformlardaki IoT cihazlarını yönetir,
    durumlarını takip eder ve kontrol eder.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """IoTDeviceManager başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.logger = get_logger("iot_device_manager")
        
        # Cihaz listesi
        self.devices: Dict[str, IoTDevice] = {}
        
        # Platform bağlantıları
        self.home_assistant = None
        self.mqtt_client = None
        
        # Durum takibi için kilit
        self.lock = asyncio.Lock()
        
        # Cihaz durumu değişikliği callback'leri
        self.state_change_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
    
    async def initialize(self) -> bool:
        """IoT cihaz yöneticisini başlatır.
        
        Returns:
            bool: Başlatma başarılı ise True
        """
        try:
            # Home Assistant bağlantısı
            if "home_assistant" in self.config:
                ha_config = self.config["home_assistant"]
                self.home_assistant = HomeAssistantBridge(
                    host=ha_config.get("host", "localhost"),
                    token=ha_config.get("token"),
                    port=ha_config.get("port", 8123),
                    use_ssl=ha_config.get("use_ssl", False)
                )
                
                # Home Assistant'ı başlat
                ha_success = await self.home_assistant.initialize()
                if not ha_success:
                    self.logger.warning("Home Assistant bağlantısı başlatılamadı")
                else:
                    self.logger.info("Home Assistant bağlantısı başlatıldı")
                    
                    # Home Assistant cihazlarını keşfet
                    await self._discover_home_assistant_devices()
            
            # MQTT bağlantısı
            if "mqtt" in self.config:
                mqtt_config = self.config["mqtt"]
                self.mqtt_client = MQTTClient(
                    broker_host=mqtt_config.get("broker_host", "localhost"),
                    broker_port=mqtt_config.get("broker_port", 1883),
                    client_id=mqtt_config.get("client_id"),
                    username=mqtt_config.get("username"),
                    password=mqtt_config.get("password"),
                    use_ssl=mqtt_config.get("use_ssl", False)
                )
                
                # MQTT'yi başlat
                mqtt_success = await self.mqtt_client.connect()
                if not mqtt_success:
                    self.logger.warning("MQTT bağlantısı başlatılamadı")
                else:
                    self.logger.info("MQTT bağlantısı başlatıldı")
                    
                    # MQTT cihazlarını keşfet
                    if "discovery_topic" in mqtt_config:
                        await self._discover_mqtt_devices(mqtt_config["discovery_topic"])
            
            # Cihaz listesini yükle
            await self._load_devices()
            
            self.logger.info(f"IoT cihaz yöneticisi başlatıldı, {len(self.devices)} cihaz bulundu")
            return True
            
        except Exception as e:
            self.logger.error(f"IoT cihaz yöneticisi başlatılamadı: {str(e)}")
            return False
    
    async def get_devices(
        self,
        device_type: Optional[Union[DeviceType, str]] = None,
        platform: Optional[Union[DevicePlatform, str]] = None,
        capability: Optional[Union[DeviceCapability, str]] = None
    ) -> List[IoTDevice]:
        """Cihazları getirir.
        
        Args:
            device_type: Cihaz tipi filtresi (opsiyonel)
            platform: Platform filtresi (opsiyonel)
            capability: Yetenek filtresi (opsiyonel)
            
        Returns:
            List[IoTDevice]: Cihaz listesi
        """
        # Enum dönüşümleri
        if device_type and not isinstance(device_type, DeviceType):
            device_type = DeviceType(device_type)
        
        if platform and not isinstance(platform, DevicePlatform):
            platform = DevicePlatform(platform)
        
        if capability and not isinstance(capability, DeviceCapability):
            capability = DeviceCapability(capability)
        
        # Filtreleme
        filtered_devices = []
        for device in self.devices.values():
            # Cihaz tipi filtresi
            if device_type and device.device_type != device_type:
                continue
            
            # Platform filtresi
            if platform and device.platform != platform:
                continue
            
            # Yetenek filtresi
            if capability and capability not in device.capabilities:
                continue
            
            filtered_devices.append(device)
        
        return filtered_devices
    
    async def get_device(self, device_id: str) -> Optional[IoTDevice]:
        """Belirli bir cihazı getirir.
        
        Args:
            device_id: Cihaz ID'si
            
        Returns:
            Optional[IoTDevice]: Cihaz veya None
        """
        return self.devices.get(device_id)
    
    async def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Belirli bir cihazın durumunu getirir.
        
        Args:
            device_id: Cihaz ID'si
            
        Returns:
            Optional[Dict[str, Any]]: Cihaz durumu veya None
        """
        device = await self.get_device(device_id)
        if not device:
            return None
        
        # Cihaz platformuna göre durumu güncelle
        if device.platform == DevicePlatform.HOME_ASSISTANT and self.home_assistant:
            try:
                entity_id = device.platform_data.get("entity_id")
                if entity_id:
                    state = await self.home_assistant.get_state(entity_id)
                    device.update_state(state)
            except Exception as e:
                self.logger.error(f"Home Assistant cihaz durumu alınamadı: {str(e)}")
        
        return device.state
    
    async def control_device(
        self,
        device_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Bir cihazı kontrol eder.
        
        Args:
            device_id: Cihaz ID'si
            command: Komut
            params: Komut parametreleri (opsiyonel)
            
        Returns:
            bool: Kontrol başarılı ise True
        """
        device = await self.get_device(device_id)
        if not device:
            self.logger.error(f"Cihaz bulunamadı: {device_id}")
            return False
        
        params = params or {}
        
        try:
            # Cihaz platformuna göre kontrol et
            if device.platform == DevicePlatform.HOME_ASSISTANT and self.home_assistant:
                entity_id = device.platform_data.get("entity_id")
                if not entity_id:
                    self.logger.error(f"Home Assistant entity_id bulunamadı: {device_id}")
                    return False
                
                # Cihaz tipine göre domain belirle
                domain = entity_id.split('.')[0]
                
                # Komutu çağır
                await self.home_assistant.call_service(domain, command, entity_id, params)
                
                # Durumu güncelle
                state = await self.home_assistant.get_state(entity_id)
                device.update_state(state)
                
                return True
                
            elif device.platform == DevicePlatform.MQTT and self.mqtt_client:
                topic = device.platform_data.get("command_topic")
                if not topic:
                    self.logger.error(f"MQTT command_topic bulunamadı: {device_id}")
                    return False
                
                # Payload hazırla
                payload = {
                    "command": command
                }
                payload.update(params)
                
                # Mesajı yayınla
                success = await self.mqtt_client.publish(topic, payload)
                
                return success
                
            else:
                self.logger.error(f"Desteklenmeyen platform: {device.platform.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Cihaz kontrol hatası: {str(e)}")
            return False
    
    async def register_state_change_callback(
        self,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """Durum değişikliği callback'i kaydeder.
        
        Args:
            callback: Durum değiştiğinde çağrılacak fonksiyon
        """
        self.state_change_callbacks.append(callback)
    
    async def _discover_home_assistant_devices(self) -> None:
        """Home Assistant cihazlarını keşfeder."""
        if not self.home_assistant:
            return
        
        try:
            # Tüm durumları al
            states = await self.home_assistant.get_states()
            
            # Cihazları oluştur
            async with self.lock:
                for state in states:
                    entity_id = state["entity_id"]
                    domain = entity_id.split('.')[0]
                    
                    # Cihaz tipini belirle
                    device_type = DeviceType.UNKNOWN
                    if domain == "light":
                        device_type = DeviceType.LIGHT
                    elif domain == "switch":
                        device_type = DeviceType.SWITCH
                    elif domain == "sensor":
                        device_type = DeviceType.SENSOR
                    elif domain == "climate":
                        device_type = DeviceType.THERMOSTAT
                    elif domain == "camera":
                        device_type = DeviceType.CAMERA
                    elif domain == "lock":
                        device_type = DeviceType.LOCK
                    elif domain == "media_player":
                        if "tv" in entity_id:
                            device_type = DeviceType.TV
                        else:
                            device_type = DeviceType.SPEAKER
                    elif domain == "vacuum":
                        device_type = DeviceType.VACUUM
                    elif domain == "fan":
                        device_type = DeviceType.FAN
                    elif domain == "cover":
                        device_type = DeviceType.BLIND
                    
                    # Yetenekleri belirle
                    capabilities = []
                    if "state" in state["attributes"]:
                        capabilities.append(DeviceCapability.POWER)
                    
                    if "brightness" in state["attributes"]:
                        capabilities.append(DeviceCapability.BRIGHTNESS)
                    
                    if "rgb_color" in state["attributes"] or "color_temp" in state["attributes"]:
                        capabilities.append(DeviceCapability.COLOR)
                    
                    if "temperature" in state["attributes"] or "current_temperature" in state["attributes"]:
                        capabilities.append(DeviceCapability.TEMPERATURE)
                    
                    if "humidity" in state["attributes"]:
                        capabilities.append(DeviceCapability.HUMIDITY)
                    
                    if "motion" in entity_id or "motion" in state["attributes"]:
                        capabilities.append(DeviceCapability.MOTION)
                    
                    if "door" in entity_id or "door" in state["attributes"]:
                        capabilities.append(DeviceCapability.DOOR)
                    
                    if "battery" in state["attributes"]:
                        capabilities.append(DeviceCapability.BATTERY)
                    
                    if "volume_level" in state["attributes"]:
                        capabilities.append(DeviceCapability.VOLUME)
                    
                    if "source" in state["attributes"]:
                        capabilities.append(DeviceCapability.CHANNEL)
                    
                    if domain == "lock":
                        capabilities.append(DeviceCapability.LOCK)
                    
                    if "speed" in state["attributes"] or "percentage" in state["attributes"]:
                        capabilities.append(DeviceCapability.FAN_SPEED)
                    
                    if "mode" in state["attributes"] or "hvac_mode" in state["attributes"]:
                        capabilities.append(DeviceCapability.MODE)
                    
                    if "position" in state["attributes"] or "current_position" in state["attributes"]:
                        capabilities.append(DeviceCapability.POSITION)
                    
                    # Cihazı oluştur
                    device = IoTDevice(
                        device_id=f"ha_{entity_id}",
                        name=state["attributes"].get("friendly_name", entity_id),
                        device_type=device_type,
                        platform=DevicePlatform.HOME_ASSISTANT,
                        capabilities=capabilities,
                        platform_data={
                            "entity_id": entity_id,
                            "domain": domain
                        }
                    )
                    
                    # Durumu ayarla
                    device.update_state(state)
                    
                    # Cihazı ekle
                    self.devices[device.device_id] = device
            
            self.logger.info(f"{len(states)} Home Assistant cihazı keşfedildi")
            
        except Exception as e:
            self.logger.error(f"Home Assistant cihaz keşfi hatası: {str(e)}")
    
    async def _discover_mqtt_devices(self, discovery_topic: str) -> None:
        """MQTT cihazlarını keşfeder.
        
        Args:
            discovery_topic: Keşif konusu
        """
        if not self.mqtt_client:
            return
        
        try:
            # Keşif konusuna abone ol
            await self.mqtt_client.subscribe(
                f"{discovery_topic}/#",
                self._handle_mqtt_discovery
            )
            
            self.logger.info(f"MQTT cihaz keşfi başlatıldı: {discovery_topic}/#")
            
        except Exception as e:
            self.logger.error(f"MQTT cihaz keşfi hatası: {str(e)}")
    
    def _handle_mqtt_discovery(self, topic: str, payload: bytes) -> None:
        """MQTT keşif mesajını işler.
        
        Args:
            topic: Mesaj konusu
            payload: Mesaj içeriği
        """
        try:
            # Payload'ı ayrıştır
            payload_str = payload.decode('utf-8')
            payload_data = json.loads(payload_str)
            
            # Konu parçalarını ayrıştır
            topic_parts = topic.split('/')
            if len(topic_parts) < 4:
                return
            
            component = topic_parts[1]
            node_id = topic_parts[2]
            object_id = topic_parts[3]
            
            # Cihaz ID'si oluştur
            device_id = f"mqtt_{node_id}_{object_id}"
            
            # Cihaz tipini belirle
            device_type = DeviceType.UNKNOWN
            if component == "light":
                device_type = DeviceType.LIGHT
            elif component == "switch":
                device_type = DeviceType.SWITCH
            elif component == "sensor":
                device_type = DeviceType.SENSOR
            elif component == "climate":
                device_type = DeviceType.THERMOSTAT
            elif component == "camera":
                device_type = DeviceType.CAMERA
            elif component == "lock":
                device_type = DeviceType.LOCK
            elif component == "media_player":
                device_type = DeviceType.SPEAKER
            elif component == "vacuum":
                device_type = DeviceType.VACUUM
            elif component == "fan":
                device_type = DeviceType.FAN
            elif component == "cover":
                device_type = DeviceType.BLIND
            
            # Yetenekleri belirle
            capabilities = []
            if "state_topic" in payload_data:
                capabilities.append(DeviceCapability.POWER)
            
            if "brightness" in payload_data or "brightness_state_topic" in payload_data:
                capabilities.append(DeviceCapability.BRIGHTNESS)
            
            if "rgb" in payload_data or "color_temp" in payload_data:
                capabilities.append(DeviceCapability.COLOR)
            
            if "temperature" in payload_data or "current_temperature_topic" in payload_data:
                capabilities.append(DeviceCapability.TEMPERATURE)
            
            if "humidity" in payload_data:
                capabilities.append(DeviceCapability.HUMIDITY)
            
            if "motion" in object_id:
                capabilities.append(DeviceCapability.MOTION)
            
            if "door" in object_id:
                capabilities.append(DeviceCapability.DOOR)
            
            if "battery" in payload_data:
                capabilities.append(DeviceCapability.BATTERY)
            
            if "volume" in payload_data:
                capabilities.append(DeviceCapability.VOLUME)
            
            if "source" in payload_data:
                capabilities.append(DeviceCapability.CHANNEL)
            
            if component == "lock":
                capabilities.append(DeviceCapability.LOCK)
            
            if "speed" in payload_data or "percentage" in payload_data:
                capabilities.append(DeviceCapability.FAN_SPEED)
            
            if "mode" in payload_data:
                capabilities.append(DeviceCapability.MODE)
            
            if "position" in payload_data:
                capabilities.append(DeviceCapability.POSITION)
            
            # Cihazı oluştur
            device = IoTDevice(
                device_id=device_id,
                name=payload_data.get("name", object_id),
                device_type=device_type,
                platform=DevicePlatform.MQTT,
                capabilities=capabilities,
                platform_data={
                    "state_topic": payload_data.get("state_topic"),
                    "command_topic": payload_data.get("command_topic"),
                    "discovery_data": payload_data
                }
            )
            
            # Cihazı ekle
            asyncio.create_task(self._add_mqtt_device(device))
            
        except Exception as e:
            self.logger.error(f"MQTT keşif mesajı işleme hatası: {str(e)}")
    
    async def _add_mqtt_device(self, device: IoTDevice) -> None:
        """MQTT cihazını ekler.
        
        Args:
            device: Eklenecek cihaz
        """
        async with self.lock:
            self.devices[device.device_id] = device
            
            # Durum konusuna abone ol
            state_topic = device.platform_data.get("state_topic")
            if state_topic and self.mqtt_client:
                await self.mqtt_client.subscribe(
                    state_topic,
                    lambda topic, payload: self._handle_mqtt_state(device.device_id, topic, payload)
                )
            
            self.logger.info(f"MQTT cihazı eklendi: {device.name} ({device.device_id})")
    
    def _handle_mqtt_state(self, device_id: str, topic: str, payload: bytes) -> None:
        """MQTT durum mesajını işler.
        
        Args:
            device_id: Cihaz ID'si
            topic: Mesaj konusu
            payload: Mesaj içeriği
        """
        try:
            # Cihazı bul
            device = self.devices.get(device_id)
            if not device:
                return
            
            # Payload'ı ayrıştır
            try:
                payload_str = payload.decode('utf-8')
                payload_data = json.loads(payload_str)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # JSON değilse düz metin olarak kullan
                payload_data = {"state": payload.decode('utf-8', errors='ignore')}
            
            # Durumu güncelle
            device.update_state(payload_data)
            
            # Callback'leri çağır
            for callback in self.state_change_callbacks:
                try:
                    callback(device_id, payload_data)
                except Exception as e:
                    self.logger.error(f"Durum değişikliği callback hatası: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"MQTT durum mesajı işleme hatası: {str(e)}")
    
    async def _load_devices(self) -> None:
        """Cihaz listesini yükler."""
        # Cihaz listesi dosyası
        devices_file = self.config.get("devices_file")
        if not devices_file or not os.path.exists(devices_file):
            return
        
        try:
            with open(devices_file, 'r', encoding='utf-8') as f:
                devices_data = json.load(f)
            
            # Cihazları yükle
            async with self.lock:
                for device_data in devices_data:
                    device = IoTDevice.from_dict(device_data)
                    self.devices[device.device_id] = device
            
            self.logger.info(f"{len(devices_data)} cihaz yüklendi")
            
        except Exception as e:
            self.logger.error(f"Cihaz listesi yükleme hatası: {str(e)}")
    
    async def _save_devices(self) -> None:
        """Cihaz listesini kaydeder."""
        # Cihaz listesi dosyası
        devices_file = self.config.get("devices_file")
        if not devices_file:
            return
        
        try:
            # Cihazları dönüştür
            devices_data = []
            for device in self.devices.values():
                devices_data.append(device.to_dict())
            
            # Dosyaya kaydet
            with open(devices_file, 'w', encoding='utf-8') as f:
                json.dump(devices_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"{len(devices_data)} cihaz kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Cihaz listesi kaydetme hatası: {str(e)}")
    
    async def close(self) -> None:
        """Bağlantıları kapatır."""
        # Cihazları kaydet
        await self._save_devices()
        
        # Home Assistant bağlantısını kapat
        if self.home_assistant:
            await self.home_assistant.close()
        
        # MQTT bağlantısını kapat
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
        
        self.logger.info("IoT cihaz yöneticisi kapatıldı")
