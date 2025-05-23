# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# MCP (Model Context Protocol) Yönetim Modülü

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import aiohttp
import websockets
import jsonschema
from datetime import datetime

# MCP istemci kütüphanesini içe aktar (varsayımsal)
try:
    import mcp_client
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    logging.warning("MCP istemci kütüphanesi bulunamadı. MCP özellikleri sınırlı olacak.")

class MCPServer:
    """MCP sunucusu bilgilerini tutan sınıf."""

    def __init__(
        self,
        server_id: str,
        name: str,
        url: str,
        api_key: Optional[str] = None,
        description: str = "",
        is_official: bool = False,
        models: Optional[List[Dict[str, Any]]] = None,
        capabilities: Optional[List[Dict[str, Any]]] = None,
        status: str = "disconnected"
    ):
        """MCP sunucusu başlatıcısı.

        Args:
            server_id: Sunucu benzersiz tanımlayıcısı
            name: Sunucu adı
            url: Sunucu URL'si
            api_key: API anahtarı (opsiyonel)
            description: Sunucu açıklaması
            is_official: Resmi sunucu mu?
            models: Sunucunun desteklediği modeller listesi
            capabilities: Sunucunun desteklediği yetenekler listesi
            status: Sunucu durumu (connected, disconnected, error)
        """
        self.server_id = server_id
        self.name = name
        self.url = url
        self.api_key = api_key
        self.description = description
        self.is_official = is_official
        self.models = models or []
        self.capabilities = capabilities or []
        self.status = status
        self.last_connected = None
        self.connection = None

    def to_dict(self) -> Dict[str, Any]:
        """Sunucu bilgilerini sözlük olarak döndürür."""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "is_official": self.is_official,
            "models": self.models,
            "capabilities": self.capabilities,
            "status": self.status,
            "last_connected": self.last_connected
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServer':
        """Sözlükten MCP sunucusu oluşturur."""
        return cls(
            server_id=data.get("server_id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            api_key=data.get("api_key"),
            description=data.get("description", ""),
            is_official=data.get("is_official", False),
            models=data.get("models", []),
            capabilities=data.get("capabilities", []),
            status=data.get("status", "disconnected")
        )

class MCPManager:
    """MCP (Model Context Protocol) entegrasyonlarını yöneten sınıf.

    Bu sınıf, Model Context Protocol sunucularını yönetir ve
    farklı yapay zeka modellerini, yeteneklerini ve eklentilerini
    sisteme entegre etmek için kullanılır.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """MCP yöneticisi başlatıcısı.

        Args:
            storage_path: MCP yapılandırma dosyalarının saklanacağı yol
        """
        # Eski yapılar (geriye uyumluluk için)
        self.models = {}
        self.capabilities = {}
        self.plugins = {}

        # MCP sunucuları ve yapılandırma
        self.servers: Dict[str, MCPServer] = {}
        self.active_connections: Dict[str, Any] = {}
        self.default_server_id: Optional[str] = None

        # Yapılandırma dosyası yolu
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "mcp"
        )

        # Depolama dizinini oluştur
        os.makedirs(self.storage_path, exist_ok=True)

        # Yapılandırmayı yükle
        self._load_configuration()

    def _load_configuration(self) -> None:
        """MCP yapılandırmasını dosyadan yükler."""
        config_file = os.path.join(self.storage_path, "mcp_config.json")

        if not os.path.exists(config_file):
            # Varsayılan yapılandırmayı oluştur
            self._create_default_configuration()
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Sunucuları yükle
            for server_data in config.get("servers", []):
                server = MCPServer.from_dict(server_data)
                self.servers[server.server_id] = server

            # Varsayılan sunucuyu ayarla
            self.default_server_id = config.get("default_server_id")

            logging.info(f"{len(self.servers)} MCP sunucusu yüklendi.")

            # Sunucu keşfini başlat
            asyncio.create_task(self._discover_servers())

        except Exception as e:
            logging.error(f"MCP yapılandırması yüklenirken hata oluştu: {e}")
            # Hata durumunda varsayılan yapılandırmayı oluştur
            self._create_default_configuration()

    async def _discover_servers(self) -> None:
        """MCP sunucularını keşfeder."""
        try:
            # Keşif URL'sinden sunucuları al
            discovery_url = "https://mcp.so/discovery"

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(discovery_url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Sunucuları işle
                            for server_data in data.get("servers", []):
                                server = MCPServer(
                                    server_id=server_data["id"],
                                    name=server_data["name"],
                                    url=server_data["url"],
                                    description=server_data.get("description", ""),
                                    is_official=server_data.get("is_official", False)
                                )
                                self.servers[server.server_id] = server

                            logging.info(f"{len(data.get('servers', []))} MCP sunucusu keşfedildi.")
                        else:
                            logging.warning(f"MCP sunucu keşfi başarısız: {response.status}")
                except aiohttp.ClientConnectorError as e:
                    logging.warning(f"MCP sunucusuna bağlanılamadı: {str(e)}")
                    # Varsayılan yapılandırmayı kullan
                    self._create_default_configuration()

        except Exception as e:
            logging.error(f"MCP sunucu keşfi sırasında hata: {str(e)}", exc_info=True)
            # Hata durumunda varsayılan yapılandırmayı kullan
            self._create_default_configuration()

    def _create_default_configuration(self) -> None:
        """Varsayılan MCP yapılandırmasını oluşturur."""
        # Resmi MCP sunucusunu ekle
        official_server = MCPServer(
            server_id="official",
            name="MCP.so Sunucusu",
            url="https://mcp.so",
            description="ZEKA projesi için resmi MCP sunucusu",
            is_official=True
        )

        self.servers[official_server.server_id] = official_server
        self.default_server_id = official_server.server_id

        # Yapılandırmayı kaydet
        self._save_configuration()

        logging.info("Varsayılan MCP yapılandırması oluşturuldu.")

    def _save_configuration(self) -> None:
        """MCP yapılandırmasını dosyaya kaydeder."""
        config_file = os.path.join(self.storage_path, "mcp_config.json")

        config = {
            "servers": [server.to_dict() for server in self.servers.values()],
            "default_server_id": self.default_server_id
        }

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logging.info("MCP yapılandırması kaydedildi.")

        except Exception as e:
            logging.error(f"MCP yapılandırması kaydedilirken hata oluştu: {e}")

    # MCP Sunucu Yönetimi

    def add_server(
        self,
        name: str,
        url: str,
        api_key: Optional[str] = None,
        description: str = "",
        is_official: bool = False,
        set_as_default: bool = False
    ) -> str:
        """Yeni bir MCP sunucusu ekler.

        Args:
            name: Sunucu adı
            url: Sunucu URL'si
            api_key: API anahtarı (opsiyonel)
            description: Sunucu açıklaması
            is_official: Resmi sunucu mu?
            set_as_default: Varsayılan sunucu olarak ayarla

        Returns:
            str: Eklenen sunucunun ID'si
        """
        import uuid
        server_id = str(uuid.uuid4())

        server = MCPServer(
            server_id=server_id,
            name=name,
            url=url,
            api_key=api_key,
            description=description,
            is_official=is_official
        )

        self.servers[server_id] = server

        if set_as_default or not self.default_server_id:
            self.default_server_id = server_id

        # Yapılandırmayı kaydet
        self._save_configuration()

        logging.info(f"MCP sunucusu eklendi: {name} ({server_id})")
        return server_id

    def remove_server(self, server_id: str) -> bool:
        """Bir MCP sunucusunu kaldırır.

        Args:
            server_id: Kaldırılacak sunucunun ID'si

        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if server_id not in self.servers:
            logging.warning(f"Kaldırılacak MCP sunucusu bulunamadı: {server_id}")
            return False

        # Aktif bağlantıyı kapat
        if server_id in self.active_connections:
            self.disconnect_server(server_id)

        # Sunucuyu kaldır
        server = self.servers.pop(server_id)

        # Varsayılan sunucu ise başka bir sunucuyu varsayılan yap
        if self.default_server_id == server_id:
            if self.servers:
                self.default_server_id = next(iter(self.servers.keys()))
            else:
                self.default_server_id = None

        # Yapılandırmayı kaydet
        self._save_configuration()

        logging.info(f"MCP sunucusu kaldırıldı: {server.name} ({server_id})")
        return True

    def update_server(
        self,
        server_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        description: Optional[str] = None,
        is_official: Optional[bool] = None
    ) -> bool:
        """Bir MCP sunucusunu günceller.

        Args:
            server_id: Güncellenecek sunucunun ID'si
            name: Yeni sunucu adı
            url: Yeni sunucu URL'si
            api_key: Yeni API anahtarı
            description: Yeni sunucu açıklaması
            is_official: Yeni resmi sunucu durumu

        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if server_id not in self.servers:
            logging.warning(f"Güncellenecek MCP sunucusu bulunamadı: {server_id}")
            return False

        server = self.servers[server_id]

        # Değerleri güncelle
        if name is not None:
            server.name = name
        if url is not None:
            server.url = url
        if api_key is not None:
            server.api_key = api_key
        if description is not None:
            server.description = description
        if is_official is not None:
            server.is_official = is_official

        # Yapılandırmayı kaydet
        self._save_configuration()

        logging.info(f"MCP sunucusu güncellendi: {server.name} ({server_id})")
        return True

    def set_default_server(self, server_id: str) -> bool:
        """Varsayılan MCP sunucusunu ayarlar.

        Args:
            server_id: Varsayılan yapılacak sunucunun ID'si

        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        if server_id not in self.servers:
            logging.warning(f"Varsayılan yapılacak MCP sunucusu bulunamadı: {server_id}")
            return False

        self.default_server_id = server_id

        # Yapılandırmayı kaydet
        self._save_configuration()

        logging.info(f"Varsayılan MCP sunucusu ayarlandı: {self.servers[server_id].name} ({server_id})")
        return True

    def get_server(self, server_id: Optional[str] = None) -> Optional[MCPServer]:
        """Belirtilen MCP sunucusunu getirir.

        Args:
            server_id: Getirilecek sunucunun ID'si. None ise varsayılan sunucu getirilir.

        Returns:
            Optional[MCPServer]: Sunucu nesnesi veya None
        """
        if server_id is None:
            server_id = self.default_server_id

        if not server_id or server_id not in self.servers:
            return None

        return self.servers[server_id]

    def list_servers(self) -> List[Dict[str, Any]]:
        """Tüm MCP sunucularının listesini döndürür.

        Returns:
            List[Dict[str, Any]]: Sunucu bilgileri listesi
        """
        return [
            {
                "server_id": server.server_id,
                "name": server.name,
                "url": server.url,
                "description": server.description,
                "is_official": server.is_official,
                "status": server.status,
                "is_default": server.server_id == self.default_server_id
            }
            for server in self.servers.values()
        ]

    # MCP Sunucu Bağlantı Yönetimi

    async def connect_server(self, server_id: Optional[str] = None) -> bool:
        """Belirtilen MCP sunucusuna bağlanır.

        Args:
            server_id: Bağlanılacak sunucunun ID'si. None ise varsayılan sunucu kullanılır.

        Returns:
            bool: Bağlantı başarılı ise True, değilse False
        """
        server = self.get_server(server_id)
        if not server:
            logging.warning("Bağlanılacak MCP sunucusu bulunamadı.")
            return False

        # Zaten bağlı ise
        if server.status == "connected":
            return True

        try:
            # MCP istemci kütüphanesi kullanılabilir ise
            if MCP_CLIENT_AVAILABLE:
                connection = await mcp_client.connect(
                    url=server.url,
                    api_key=server.api_key
                )

                # Sunucu bilgilerini güncelle
                server.status = "connected"
                server.last_connected = datetime.now()
                server.connection = connection

                # Aktif bağlantıları güncelle
                self.active_connections[server.server_id] = connection

                # Sunucu yeteneklerini ve modellerini al
                await self._fetch_server_capabilities(server)

                logging.info(f"MCP sunucusuna bağlanıldı: {server.name} ({server.server_id})")
                return True
            else:
                # MCP istemci kütüphanesi yoksa manuel bağlantı
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{server.url}/info",
                        headers={"Authorization": f"Bearer {server.api_key}"} if server.api_key else {}
                    ) as response:
                        if response.status == 200:
                            info = await response.json()

                            # Sunucu bilgilerini güncelle
                            server.status = "connected"
                            server.last_connected = datetime.now()
                            server.models = info.get("models", [])
                            server.capabilities = info.get("capabilities", [])

                            logging.info(f"MCP sunucusuna bağlanıldı: {server.name} ({server.server_id})")
                            return True
                        else:
                            error = await response.text()
                            logging.error(f"MCP sunucusuna bağlanırken hata: {error}")
                            server.status = "error"
                            return False

        except Exception as e:
            logging.error(f"MCP sunucusuna bağlanırken hata: {e}")
            server.status = "error"
            return False

    async def disconnect_server(self, server_id: Optional[str] = None) -> bool:
        """Belirtilen MCP sunucusu ile bağlantıyı keser.

        Args:
            server_id: Bağlantısı kesilecek sunucunun ID'si. None ise varsayılan sunucu kullanılır.

        Returns:
            bool: İşlem başarılı ise True, değilse False
        """
        server = self.get_server(server_id)
        if not server:
            logging.warning("Bağlantısı kesilecek MCP sunucusu bulunamadı.")
            return False

        # Zaten bağlı değilse
        if server.status != "connected":
            return True

        try:
            # MCP istemci kütüphanesi kullanılabilir ise
            if server.server_id in self.active_connections:
                connection = self.active_connections[server.server_id]
                await connection.close()
                del self.active_connections[server.server_id]

            # Sunucu durumunu güncelle
            server.status = "disconnected"
            server.connection = None

            logging.info(f"MCP sunucusu ile bağlantı kesildi: {server.name} ({server.server_id})")
            return True

        except Exception as e:
            logging.error(f"MCP sunucusu ile bağlantı kesilirken hata: {e}")
            server.status = "error"
            return False

    async def _fetch_server_capabilities(self, server: MCPServer) -> None:
        """Sunucunun yeteneklerini ve modellerini alır.

        Args:
            server: MCP sunucusu
        """
        if not server.connection:
            return

        try:
            # MCP istemci kütüphanesi kullanılabilir ise
            if MCP_CLIENT_AVAILABLE:
                info = await server.connection.get_info()
                server.models = info.get("models", [])
                server.capabilities = info.get("capabilities", [])
            else:
                # MCP istemci kütüphanesi yoksa manuel istek
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{server.url}/info",
                        headers={"Authorization": f"Bearer {server.api_key}"} if server.api_key else {}
                    ) as response:
                        if response.status == 200:
                            info = await response.json()
                            server.models = info.get("models", [])
                            server.capabilities = info.get("capabilities", [])

        except Exception as e:
            logging.error(f"Sunucu yetenekleri alınırken hata: {e}")

    # MCP İstek Yönetimi

    async def send_request(
        self,
        request_type: str,
        data: Dict[str, Any],
        server_id: Optional[str] = None,
        timeout: float = 60.0  # Zaman aşımı süresini ekledik
    ) -> Dict[str, Any]:
        """MCP sunucusuna istek gönderir.

        Args:
            request_type: İstek türü (generate, embed, vb.)
            data: İstek verileri
            server_id: İsteğin gönderileceği sunucunun ID'si. None ise varsayılan sunucu kullanılır.
            timeout: İstek zaman aşımı süresi (saniye)

        Returns:
            Dict[str, Any]: Sunucu yanıtı veya None (hata durumunda)
        """
        try:
            server = self.get_server(server_id)
            if not server:
                # Sunucu bulunamadıysa, yerel işleme geçmek için None döndür
                logging.warning(f"MCP sunucusu bulunamadı, yerel işleme geçiliyor")
                return None

            # Sunucu bağlı değilse bağlan
            if server.status != "connected":
                connected = await self.connect_server(server.server_id)
                if not connected:
                    logging.warning(f"MCP sunucusuna bağlanılamadı: {server.name}, yerel işleme geçiliyor")
                    return None
        except Exception as e:
            logging.warning(f"MCP sunucu hazırlığı sırasında hata: {str(e)}, yerel işleme geçiliyor")
            return None

        try:
            # MCP istemci kütüphanesi kullanılabilir ise
            if MCP_CLIENT_AVAILABLE and server.connection:
                if request_type == "generate":
                    response = await server.connection.generate(data)
                elif request_type == "embed":
                    response = await server.connection.embed(data)
                elif request_type == "chat":
                    response = await server.connection.chat(data)
                else:
                    response = await server.connection.custom_request(request_type, data)

                return response
            else:
                # MCP istemci kütüphanesi yoksa manuel istek
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{server.url}/{request_type}",
                        json=data,
                        headers={"Authorization": f"Bearer {server.api_key}"} if server.api_key else {}
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error = await response.text()
                            raise Exception(f"MCP isteği başarısız: {error}")

        except Exception as e:
            logging.error(f"MCP isteği gönderilirken hata: {e}")
            raise

    # Geriye uyumluluk için eski metodlar

    def register_model(self, model_id, model_instance, model_config=None):
        """Yeni bir yapay zeka modelini sisteme kaydeder.

        Args:
            model_id (str): Model tanımlayıcısı
            model_instance: Model nesnesi
            model_config (dict, optional): Model yapılandırması
        """
        if model_config is None:
            model_config = {}

        self.models[model_id] = {
            "instance": model_instance,
            "config": model_config
        }
        logging.info(f"{model_id} modeli başarıyla kaydedildi.")

    def register_capability(self, capability_id, capability_instance, capability_config=None):
        """Yeni bir yetenek modülünü sisteme kaydeder.

        Args:
            capability_id (str): Yetenek tanımlayıcısı
            capability_instance: Yetenek nesnesi
            capability_config (dict, optional): Yetenek yapılandırması
        """
        if capability_config is None:
            capability_config = {}

        self.capabilities[capability_id] = {
            "instance": capability_instance,
            "config": capability_config
        }
        logging.info(f"{capability_id} yeteneği başarıyla kaydedildi.")

    def register_plugin(self, plugin_id, plugin_instance, plugin_config=None):
        """Yeni bir eklentiyi sisteme kaydeder.

        Args:
            plugin_id (str): Eklenti tanımlayıcısı
            plugin_instance: Eklenti nesnesi
            plugin_config (dict, optional): Eklenti yapılandırması
        """
        if plugin_config is None:
            plugin_config = {}

        self.plugins[plugin_id] = {
            "instance": plugin_instance,
            "config": plugin_config
        }
        logging.info(f"{plugin_id} eklentisi başarıyla kaydedildi.")

    def get_model(self, model_id):
        """Belirtilen modeli getirir.

        Args:
            model_id (str): Model tanımlayıcısı

        Returns:
            object: Model nesnesi veya None
        """
        if model_id in self.models:
            return self.models[model_id]["instance"]
        return None

    def get_capability(self, capability_id):
        """Belirtilen yeteneği getirir.

        Args:
            capability_id (str): Yetenek tanımlayıcısı

        Returns:
            object: Yetenek nesnesi veya None
        """
        if capability_id in self.capabilities:
            return self.capabilities[capability_id]["instance"]
        return None

    def get_plugin(self, plugin_id):
        """Belirtilen eklentiyi getirir.

        Args:
            plugin_id (str): Eklenti tanımlayıcısı

        Returns:
            object: Eklenti nesnesi veya None
        """
        if plugin_id in self.plugins:
            return self.plugins[plugin_id]["instance"]
        return None

    def list_available_models(self):
        """Kullanılabilir modellerin listesini döndürür.

        Returns:
            list: Model tanımlayıcıları listesi
        """
        # Eski modeller + MCP sunucularından gelen modeller
        models = list(self.models.keys())

        # MCP sunucularından modelleri ekle
        for server in self.servers.values():
            if server.status == "connected" and server.models:
                for model in server.models:
                    model_id = f"mcp:{server.server_id}:{model.get('id', '')}"
                    if model_id not in models:
                        models.append(model_id)

        return models

    def list_available_capabilities(self):
        """Kullanılabilir yeteneklerin listesini döndürür.

        Returns:
            list: Yetenek tanımlayıcıları listesi
        """
        # Eski yetenekler + MCP sunucularından gelen yetenekler
        capabilities = list(self.capabilities.keys())

        # MCP sunucularından yetenekleri ekle
        for server in self.servers.values():
            if server.status == "connected" and server.capabilities:
                for capability in server.capabilities:
                    capability_id = f"mcp:{server.server_id}:{capability.get('id', '')}"
                    if capability_id not in capabilities:
                        capabilities.append(capability_id)

        return capabilities

    def list_available_plugins(self):
        """Kullanılabilir eklentilerin listesini döndürür.

        Returns:
            list: Eklenti tanımlayıcıları listesi
        """
        return list(self.plugins.keys())

    def update_model_config(self, model_id, config_updates):
        """Model yapılandırmasını günceller.

        Args:
            model_id (str): Model tanımlayıcısı
            config_updates (dict): Güncellenecek yapılandırma değerleri

        Returns:
            bool: Güncelleme başarılı ise True, değilse False
        """
        if model_id in self.models:
            self.models[model_id]["config"].update(config_updates)
            return True
        return False

    def update_capability_config(self, capability_id, config_updates):
        """Yetenek yapılandırmasını günceller.

        Args:
            capability_id (str): Yetenek tanımlayıcısı
            config_updates (dict): Güncellenecek yapılandırma değerleri

        Returns:
            bool: Güncelleme başarılı ise True, değilse False
        """
        if capability_id in self.capabilities:
            self.capabilities[capability_id]["config"].update(config_updates)
            return True
        return False

    def update_plugin_config(self, plugin_id, config_updates):
        """Eklenti yapılandırmasını günceller.

        Args:
            plugin_id (str): Eklenti tanımlayıcısı
            config_updates (dict): Güncellenecek yapılandırma değerleri

        Returns:
            bool: Güncelleme başarılı ise True, değilse False
        """
        if plugin_id in self.plugins:
            self.plugins[plugin_id]["config"].update(config_updates)
            return True
        return False