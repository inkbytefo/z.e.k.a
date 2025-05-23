# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# MCP (Model Context Protocol) Entegrasyon Modülü

import os
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncIterator, Union, Tuple, Set
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context
from mcp.client import MCPClient
from mcp.server.fastmcp.prompts import base
from mcp.server.fastmcp.resources import ResourceProvider
from mcp.server.fastmcp.tools import ToolProvider

from .logging_manager import get_logger
from .exceptions import MCPError
from .vector_database import VectorDatabase

class MCPIntegration:
    """Model Context Protocol (MCP) entegrasyonu.

    Bu sınıf, MCP sunucusu ve istemcisi oluşturarak
    LLM'lere veri ve işlevsellik sağlar.
    """

    # MCP sunucu türleri
    SERVER_TYPES = {
        "local": "Yerel MCP sunucusu",
        "remote": "Uzak MCP sunucusu",
        "community": "Topluluk MCP sunucusu"
    }

    def __init__(
        self,
        server_name: str = "ZEKA MCP Server",
        storage_path: Optional[str] = None,
        vector_db: Optional[Any] = None,
        dependencies: Optional[List[str]] = None,
        enable_telemetry: bool = False
    ):
        """MCP entegrasyonu başlatıcısı.

        Args:
            server_name: MCP sunucusu adı.
            storage_path: MCP yapılandırma dosyalarının saklanacağı yol.
            vector_db: Vektör veritabanı nesnesi (opsiyonel).
            dependencies: Ek bağımlılıklar (opsiyonel).
            enable_telemetry: Telemetri etkinleştirme durumu.
        """
        # Loglama
        self.logger = get_logger("mcp_integration")

        # Depolama yolu
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "mcp"
        )
        os.makedirs(self.storage_path, exist_ok=True)

        # Vektör veritabanı
        self.vector_db = vector_db

        # Bağımlılıklar
        self.dependencies = dependencies or ["pandas", "numpy", "requests"]

        # Telemetri
        self.enable_telemetry = enable_telemetry

        # MCP sunucusu oluştur
        try:
            self.server = FastMCP(
                server_name,
                dependencies=self.dependencies,
                lifespan=self._app_lifespan,
                enable_telemetry=self.enable_telemetry
            )
            self.client = None
            self.is_server_running = False

            # Sunucu yapılandırması
            self.initialize_server()

            # Bağlı sunucular
            self.connected_servers = {}

            # Metrikler
            self.metrics = {
                "server_start_time": None,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tool_calls": 0,
                "total_resource_requests": 0,
                "average_response_time": 0.0,
                "total_response_time": 0.0
            }

            self.logger.info(f"MCP entegrasyonu başlatıldı: {server_name}")
        except Exception as e:
            self.logger.error(f"MCP entegrasyonu başlatılırken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP entegrasyonu başlatılamadı: {str(e)}")

    @asynccontextmanager
    async def _app_lifespan(self, server_instance: FastMCP) -> AsyncIterator[Dict[str, Any]]:
        """Uygulama yaşam döngüsünü yönetir.

        Args:
            server_instance: MCP sunucusu.

        Yields:
            Dict[str, Any]: Yaşam döngüsü bağlamı.
        """
        # Başlangıç işlemleri
        self.logger.info("MCP sunucusu başlatılıyor...")

        # Sunucu başlangıç zamanını kaydet
        start_time = asyncio.get_event_loop().time()
        self.metrics["server_start_time"] = start_time

        # Bağlam oluştur
        context = {
            "start_time": start_time,
            "resources": {},
            "tools": {},
            "vector_db": self.vector_db
        }

        try:
            # Bağlamı döndür
            yield context
            self.logger.info("MCP sunucusu normal şekilde kapatılıyor...")
        except Exception as e:
            self.logger.error(f"MCP sunucusu çalışırken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP sunucusu çalışırken hata: {str(e)}")
        finally:
            # Temizleme işlemleri
            self.logger.info("MCP sunucusu kapatılıyor...")

            # Çalışma süresini hesapla
            end_time = asyncio.get_event_loop().time()
            uptime = end_time - start_time
            self.logger.info(f"MCP sunucusu çalışma süresi: {uptime:.2f} saniye")

    def initialize_server(self) -> None:
        """MCP sunucusunu yapılandırır ve kaynakları/araçları ekler."""
        try:
            # Kaynaklar ekle
            self._add_resources()

            # Araçlar ekle
            self._add_tools()

            # Promptlar ekle
            self._add_prompts()

            self.logger.info("MCP sunucusu yapılandırıldı.")
        except Exception as e:
            self.logger.error(f"MCP sunucusu yapılandırılırken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP sunucusu yapılandırılamadı: {str(e)}")

    def _add_resources(self) -> None:
        """MCP sunucusuna kaynaklar ekler."""
        # Kullanıcı profili kaynağı
        @self.server.resource("user://{user_id}/profile")
        def get_user_profile(user_id: str) -> str:
            """Kullanıcı profili bilgilerini getirir.

            Args:
                user_id: Kullanıcı ID'si.

            Returns:
                str: Kullanıcı profili bilgileri.
            """
            # Gerçek implementasyonda veritabanından alınacak
            return f"Kullanıcı profili: {user_id}"

        # Bellek kaynağı
        @self.server.resource("memory://{query}")
        def get_memory(query: str) -> str:
            """Bellek verilerini getirir.

            Args:
                query: Arama sorgusu.

            Returns:
                str: İlgili bellek verileri.
            """
            # Gerçek implementasyonda vektör veritabanından alınacak
            return f"Bellek sonuçları: {query}"

        # Takvim kaynağı
        @self.server.resource("calendar://{date}")
        def get_calendar(date: str) -> str:
            """Takvim verilerini getirir.

            Args:
                date: Tarih.

            Returns:
                str: Takvim verileri.
            """
            # Gerçek implementasyonda takvim API'sinden alınacak
            return f"Takvim etkinlikleri: {date}"

        # E-posta kaynağı
        @self.server.resource("email://{folder}")
        def get_emails(folder: str) -> str:
            """E-posta verilerini getirir.

            Args:
                folder: E-posta klasörü.

            Returns:
                str: E-posta verileri.
            """
            # Gerçek implementasyonda e-posta API'sinden alınacak
            return f"E-postalar: {folder}"

    def _add_tools(self) -> None:
        """MCP sunucusuna araçlar ekler."""
        # Web arama aracı
        @self.server.tool()
        def search_web(query: str, ctx: Context) -> str:
            """Web'de arama yapar.

            Args:
                query: Arama sorgusu.
                ctx: MCP bağlamı.

            Returns:
                str: Arama sonuçları.
            """
            # Gerçek implementasyonda arama API'si kullanılacak
            ctx.info(f"Web'de aranıyor: {query}")
            return f"Arama sonuçları: {query}"

        # Takvim oluşturma aracı
        @self.server.tool()
        def create_calendar_event(
            title: str,
            start_time: str,
            end_time: str,
            description: Optional[str] = None,
            ctx: Context = None
        ) -> str:
            """Takvim etkinliği oluşturur.

            Args:
                title: Etkinlik başlığı.
                start_time: Başlangıç zamanı.
                end_time: Bitiş zamanı.
                description: Etkinlik açıklaması.
                ctx: MCP bağlamı.

            Returns:
                str: Oluşturma sonucu.
            """
            # Gerçek implementasyonda takvim API'si kullanılacak
            if ctx:
                ctx.info(f"Takvim etkinliği oluşturuluyor: {title}")
            return f"Etkinlik oluşturuldu: {title} ({start_time} - {end_time})"

        # E-posta gönderme aracı
        @self.server.tool()
        def send_email(
            to: str,
            subject: str,
            body: str,
            ctx: Context = None
        ) -> str:
            """E-posta gönderir.

            Args:
                to: Alıcı e-posta adresi.
                subject: E-posta konusu.
                body: E-posta içeriği.
                ctx: MCP bağlamı.

            Returns:
                str: Gönderim sonucu.
            """
            # Gerçek implementasyonda e-posta API'si kullanılacak
            if ctx:
                ctx.info(f"E-posta gönderiliyor: {subject}")
            return f"E-posta gönderildi: {to} - {subject}"

    def _add_prompts(self) -> None:
        """MCP sunucusuna promptlar ekler."""
        # Kod inceleme promptu
        @self.server.prompt()
        def review_code(code: str) -> str:
            """Kod inceleme promptu.

            Args:
                code: İncelenecek kod.

            Returns:
                str: Prompt metni.
            """
            return f"Lütfen aşağıdaki kodu inceleyin ve iyileştirme önerileri sunun:\n\n{code}"

        # Hata ayıklama promptu
        @self.server.prompt()
        def debug_error(error: str) -> List[base.Message]:
            """Hata ayıklama promptu.

            Args:
                error: Hata mesajı.

            Returns:
                List[base.Message]: Mesaj listesi.
            """
            return [
                base.UserMessage("Şu hatayı alıyorum:"),
                base.UserMessage(error),
                base.AssistantMessage("Bu hatayı çözmek için yardımcı olacağım. Hatanın bağlamı hakkında daha fazla bilgi verebilir misiniz?"),
            ]

    async def start_server(
        self,
        host: str = "localhost",
        port: int = 8000,
        timeout: float = 30.0
    ) -> asyncio.Task:
        """MCP sunucusunu başlatır.

        Args:
            host: Sunucu host adresi.
            port: Sunucu port numarası.
            timeout: Başlatma zaman aşımı (saniye).

        Returns:
            asyncio.Task: Sunucu görevi.

        Raises:
            MCPError: Sunucu başlatılamazsa.
        """
        if self.is_server_running:
            self.logger.warning("MCP sunucusu zaten çalışıyor.")
            return

        try:
            # Sunucuyu asenkron olarak başlat
            start_time = time.time()
            server_task = asyncio.create_task(
                self.server.run(host=host, port=port)
            )
            self.is_server_running = True

            # Sunucunun başlamasını bekle
            try:
                await asyncio.wait_for(
                    asyncio.shield(asyncio.create_task(self._wait_for_server_ready(host, port))),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"MCP sunucusu başlatma zaman aşımı ({timeout}s)")

            elapsed_time = time.time() - start_time
            self.logger.info(f"MCP sunucusu başlatıldı: {host}:{port} ({elapsed_time:.2f}s)")

            # Sunucu görevini döndür
            return server_task
        except Exception as e:
            self.is_server_running = False
            self.logger.error(f"MCP sunucusu başlatılırken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP sunucusu başlatılamadı: {str(e)}")

    async def _wait_for_server_ready(self, host: str, port: int) -> None:
        """Sunucunun hazır olmasını bekler.

        Args:
            host: Sunucu host adresi.
            port: Sunucu port numarası.
        """
        import socket
        import asyncio

        max_attempts = 10
        delay = 0.5

        for attempt in range(max_attempts):
            try:
                # Soket bağlantısı dene
                reader, writer = await asyncio.open_connection(host, port)
                writer.close()
                await writer.wait_closed()
                self.logger.debug(f"MCP sunucusu hazır: {host}:{port}")
                return
            except (ConnectionRefusedError, socket.gaierror, OSError):
                await asyncio.sleep(delay)

        self.logger.warning(f"MCP sunucusu hazır olma kontrolü başarısız: {host}:{port}")

    async def connect_to_server(
        self,
        server_url: str,
        server_name: Optional[str] = None,
        server_type: str = "remote",
        timeout: float = 10.0
    ) -> bool:
        """MCP sunucusuna bağlanır.

        Args:
            server_url: MCP sunucusu URL'si.
            server_name: MCP sunucusu adı (opsiyonel).
            server_type: Sunucu türü (local, remote, community).
            timeout: Bağlantı zaman aşımı (saniye).

        Returns:
            bool: Bağlantı başarılı ise True.

        Raises:
            MCPError: Bağlantı kurulamazsa.
        """
        # Sunucu adını belirle
        server_name = server_name or f"MCP Server ({server_url})"

        # Sunucu türünü doğrula
        if server_type not in self.SERVER_TYPES:
            server_type = "remote"

        try:
            # Bağlantı başlangıç zamanı
            start_time = time.time()

            # MCP istemcisi oluştur ve bağlan
            self.client = MCPClient(server_url)

            # Zaman aşımı ile bağlan
            await asyncio.wait_for(
                self.client.connect(),
                timeout=timeout
            )

            # Bağlantı süresini hesapla
            elapsed_time = time.time() - start_time

            # Bağlı sunucular listesine ekle
            self.connected_servers[server_url] = {
                "name": server_name,
                "type": server_type,
                "connected_at": datetime.now().isoformat(),
                "connection_time": elapsed_time
            }

            self.logger.info(f"MCP sunucusuna bağlanıldı: {server_name} ({server_url}) - {elapsed_time:.2f}s")
            return True
        except asyncio.TimeoutError:
            self.logger.error(f"MCP sunucusuna bağlanırken zaman aşımı: {server_url} ({timeout}s)")
            raise MCPError(f"MCP sunucusuna bağlanırken zaman aşımı: {server_url}")
        except Exception as e:
            self.logger.error(f"MCP sunucusuna bağlanırken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP sunucusuna bağlanılamadı: {str(e)}")

    async def execute_tool(
        self,
        tool_name: str,
        timeout: float = 30.0,
        **params
    ) -> Any:
        """MCP aracını çalıştırır.

        Args:
            tool_name: Araç adı.
            timeout: İşlem zaman aşımı (saniye).
            **params: Araç parametreleri.

        Returns:
            Any: Araç çalıştırma sonucu.

        Raises:
            MCPError: Araç çalıştırılamazsa.
        """
        if not self.client:
            raise MCPError("MCP istemcisi bağlı değil. Önce connect_to_server() çağırın.")

        try:
            # Metrik güncelle
            self.metrics["total_tool_calls"] += 1

            # İşlem başlangıç zamanı
            start_time = time.time()

            # Aracı zaman aşımı ile çalıştır
            result = await asyncio.wait_for(
                self.client.execute_tool(tool_name, **params),
                timeout=timeout
            )

            # İşlem süresini hesapla
            elapsed_time = time.time() - start_time

            self.logger.info(f"MCP aracı çalıştırıldı: {tool_name} ({elapsed_time:.2f}s)")
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"MCP aracı çalıştırılırken zaman aşımı: {tool_name} ({timeout}s)")
            raise MCPError(f"MCP aracı çalıştırılırken zaman aşımı: {tool_name}")
        except Exception as e:
            self.logger.error(f"MCP aracı çalıştırılırken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP aracı çalıştırılamadı: {str(e)}")

    async def get_resource(
        self,
        resource_uri: str,
        timeout: float = 10.0
    ) -> str:
        """MCP kaynağını getirir.

        Args:
            resource_uri: Kaynak URI'si.
            timeout: İşlem zaman aşımı (saniye).

        Returns:
            str: Kaynak içeriği.

        Raises:
            MCPError: Kaynak getirilemezse.
        """
        if not self.client:
            raise MCPError("MCP istemcisi bağlı değil. Önce connect_to_server() çağırın.")

        try:
            # Metrik güncelle
            self.metrics["total_resource_requests"] += 1

            # İşlem başlangıç zamanı
            start_time = time.time()

            # Kaynağı zaman aşımı ile getir
            content = await asyncio.wait_for(
                self.client.get_resource(resource_uri),
                timeout=timeout
            )

            # İşlem süresini hesapla
            elapsed_time = time.time() - start_time

            self.logger.info(f"MCP kaynağı getirildi: {resource_uri} ({elapsed_time:.2f}s)")
            return content
        except asyncio.TimeoutError:
            self.logger.error(f"MCP kaynağı getirilirken zaman aşımı: {resource_uri} ({timeout}s)")
            raise MCPError(f"MCP kaynağı getirilirken zaman aşımı: {resource_uri}")
        except Exception as e:
            self.logger.error(f"MCP kaynağı getirilirken hata: {str(e)}", exc_info=True)
            raise MCPError(f"MCP kaynağı getirilemedi: {str(e)}")

    async def discover_and_connect_to_servers(
        self,
        max_servers: int = 5,
        server_types: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        timeout: float = 15.0
    ) -> List[Dict[str, Any]]:
        """MCP.so üzerinden sunucuları keşfeder ve bağlanır.

        Args:
            max_servers: Bağlanılacak maksimum sunucu sayısı.
            server_types: Bağlanılacak sunucu türleri (None ise tümü).
            capabilities: Gerekli yetenekler (None ise tümü).
            timeout: İşlem zaman aşımı (saniye).

        Returns:
            List[Dict[str, Any]]: Bağlanılan sunucuların bilgileri.
        """
        # Varsayılan sunucu türleri
        if server_types is None:
            server_types = ["community", "official"]

        # Varsayılan yetenekler
        if capabilities is None:
            capabilities = ["text_generation", "embeddings"]

        self.logger.info(f"MCP sunucuları keşfediliyor ve bağlanılıyor (max: {max_servers})")

        try:
            # Sunucuları keşfet
            all_servers = await discover_mcp_servers(timeout=timeout)

            # Sunucuları filtrele
            filtered_servers = []
            for server in all_servers:
                # Sunucu türünü kontrol et
                if server.get("type") not in server_types:
                    continue

                # Sunucu durumunu kontrol et
                if server.get("status") != "online":
                    continue

                # Yetenekleri kontrol et
                server_capabilities = server.get("capabilities", [])
                if not all(cap in server_capabilities for cap in capabilities):
                    continue

                filtered_servers.append(server)

            # Maksimum sunucu sayısına göre sınırla
            filtered_servers = filtered_servers[:max_servers]

            self.logger.info(f"{len(filtered_servers)} uygun MCP sunucusu bulundu")

            # Bağlanılan sunucuların bilgilerini tut
            connected_servers = []

            # Sunuculara bağlan
            for server in filtered_servers:
                server_url = server.get("url")
                server_name = server.get("name")
                server_type = server.get("type")

                if not server_url:
                    continue

                try:
                    # Sunucuya bağlan
                    success = await self.connect_to_server(
                        server_url=server_url,
                        server_name=server_name,
                        server_type=server_type,
                        timeout=timeout / len(filtered_servers)  # Her sunucu için zaman aşımını böl
                    )

                    if success:
                        connected_servers.append(server)
                except Exception as e:
                    self.logger.warning(f"MCP sunucusuna bağlanılamadı: {server_url} - {str(e)}")

            self.logger.info(f"{len(connected_servers)} MCP sunucusuna başarıyla bağlanıldı")
            return connected_servers
        except Exception as e:
            self.logger.error(f"MCP sunucuları keşfedilirken ve bağlanılırken hata: {str(e)}", exc_info=True)
            return []

# Yardımcı fonksiyonlar
async def discover_mcp_servers(
    discovery_url: str = "https://mcp.so/api/servers",
    timeout: float = 10.0
) -> List[Dict[str, Any]]:
    """Kullanılabilir MCP sunucularını keşfeder.

    Args:
        discovery_url: Keşif URL'si. Varsayılan olarak resmi MCP kayıt merkezi kullanılır.
        timeout: İşlem zaman aşımı (saniye).

    Returns:
        List[Dict[str, Any]]: Sunucu bilgileri listesi.
    """
    import aiohttp

    logger = get_logger("mcp_discovery")
    servers = []

    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"MCP sunucuları keşfediliyor: {discovery_url}")

            async with session.get(discovery_url, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()

                    # MCP.so API yanıt formatına göre işle
                    if "servers" in data:
                        servers = data["servers"]
                    else:
                        # API doğrudan sunucu listesi döndürüyorsa
                        servers = data if isinstance(data, list) else []

                    logger.info(f"{len(servers)} MCP sunucusu keşfedildi")

                    # Sunucu bilgilerini standart formata dönüştür
                    standardized_servers = []
                    for server in servers:
                        # MCP.so API formatına göre uyarla
                        standardized_server = {
                            "url": server.get("url") or server.get("endpoint"),
                            "name": server.get("name") or server.get("title", "Unknown Server"),
                            "type": server.get("type") or "community",
                            "description": server.get("description", ""),
                            "provider": server.get("provider", ""),
                            "capabilities": server.get("capabilities", []),
                            "status": server.get("status", "online")
                        }
                        standardized_servers.append(standardized_server)

                    return standardized_servers
                else:
                    logger.warning(f"MCP sunucuları keşfedilemedi: HTTP {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"MCP sunucuları keşfedilirken ağ hatası: {str(e)}", exc_info=True)
    except asyncio.TimeoutError:
        logger.error(f"MCP sunucuları keşfedilirken zaman aşımı: {timeout}s")
    except Exception as e:
        logger.error(f"MCP sunucuları keşfedilirken beklenmeyen hata: {str(e)}", exc_info=True)

    return servers

async def register_mcp_server(
    server_url: str,
    server_name: str,
    server_type: str = "community",
    server_description: str = "",
    capabilities: Optional[List[str]] = None,
    registry_url: str = "https://mcp.so/api/servers/register",
    timeout: float = 10.0
) -> bool:
    """MCP sunucusunu kayıt eder.

    Args:
        server_url: Sunucu URL'si.
        server_name: Sunucu adı.
        server_type: Sunucu türü.
        server_description: Sunucu açıklaması.
        capabilities: Sunucu yetenekleri.
        registry_url: Kayıt URL'si. Varsayılan olarak resmi MCP kayıt merkezi kullanılır.
        timeout: İşlem zaman aşımı (saniye).

    Returns:
        bool: Kayıt başarılı ise True.
    """
    import aiohttp

    logger = get_logger("mcp_registry")

    # Yetenekleri belirle
    if capabilities is None:
        capabilities = ["text_generation", "embeddings", "function_calling"]

    try:
        logger.info(f"MCP sunucusu kaydediliyor: {server_name} ({server_url})")

        async with aiohttp.ClientSession() as session:
            # MCP.so API formatına uygun payload oluştur
            payload = {
                "url": server_url,
                "name": server_name,
                "type": server_type,
                "description": server_description,
                "capabilities": capabilities,
                "provider": "ZEKA Assistant",
                "timestamp": datetime.now().isoformat(),
                "status": "online",
                "version": "1.0.0"
            }

            # API anahtarı varsa ekle (opsiyonel)
            api_key = os.getenv("MCP_REGISTRY_API_KEY")
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with session.post(registry_url, json=payload, headers=headers, timeout=timeout) as response:
                if response.status in (200, 201, 202):
                    response_data = await response.json()
                    server_id = response_data.get("id", "unknown")
                    logger.info(f"MCP sunucusu başarıyla kaydedildi: {server_name} (ID: {server_id})")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"MCP sunucusu kaydedilemedi: HTTP {response.status} - {error_text}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"MCP sunucusu kaydedilirken ağ hatası: {str(e)}", exc_info=True)
        return False
    except asyncio.TimeoutError:
        logger.error(f"MCP sunucusu kaydedilirken zaman aşımı: {timeout}s")
        return False
    except Exception as e:
        logger.error(f"MCP sunucusu kaydedilirken beklenmeyen hata: {str(e)}", exc_info=True)
        return False

# Test kodu
async def test_mcp():
    """MCP entegrasyonunu test eder."""
    try:
        print("MCP entegrasyonu testi başlatılıyor...")

        # Vektör veritabanı oluştur
        vector_db = VectorDatabase(
            embedding_function_name="sentence_transformer",
            embedding_model_name="all-MiniLM-L6-v2"
        )

        # MCP entegrasyonu oluştur
        integration = MCPIntegration(
            server_name="ZEKA Test MCP Server",
            vector_db=vector_db,
            enable_telemetry=False
        )

        # Sunucuyu başlat
        print("MCP sunucusu başlatılıyor...")
        server_task = await integration.start_server(port=8765)

        # Bağlan
        print("MCP sunucusuna bağlanılıyor...")
        await integration.connect_to_server(
            server_url="http://localhost:8765",
            server_name="Yerel Test Sunucusu",
            server_type="local"
        )

        # Araç çalıştır
        print("MCP aracı çalıştırılıyor...")
        result = await integration.execute_tool(
            "search_web",
            query="Yapay zeka nedir?"
        )
        print(f"Araç sonucu: {result}")

        # Kaynak getir
        print("MCP kaynağı getiriliyor...")
        content = await integration.get_resource("user://123/profile")
        print(f"Kaynak içeriği: {content}")

        # MCP.so sunucularını keşfet
        print("\nMCP.so sunucularını keşfediliyor...")
        try:
            servers = await discover_mcp_servers()
            print(f"{len(servers)} MCP sunucusu bulundu:")
            for i, server in enumerate(servers[:3]):  # İlk 3 sunucuyu göster
                print(f"  {i+1}. {server.get('name')} ({server.get('url')})")
                print(f"     Tür: {server.get('type')}")
                print(f"     Yetenekler: {', '.join(server.get('capabilities', []))}")
        except Exception as e:
            print(f"MCP sunucuları keşfedilirken hata: {str(e)}")

        # MCP.so sunucularına bağlan
        print("\nMCP.so sunucularına bağlanılıyor...")
        try:
            connected_servers = await integration.discover_and_connect_to_servers(
                max_servers=2,  # En fazla 2 sunucuya bağlan
                timeout=10.0
            )
            print(f"{len(connected_servers)} MCP sunucusuna bağlanıldı:")
            for i, server in enumerate(connected_servers):
                print(f"  {i+1}. {server.get('name')} ({server.get('url')})")
        except Exception as e:
            print(f"MCP sunucularına bağlanılırken hata: {str(e)}")

        # Metrikleri göster
        print("\nMCP metrikleri:")
        for key, value in integration.metrics.items():
            print(f"  {key}: {value}")

        # Sunucuyu durdur
        print("\nMCP sunucusu durduruluyor...")
        server_task.cancel()

        print("MCP entegrasyonu testi başarıyla tamamlandı")
    except Exception as e:
        print(f"Test sırasında hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test fonksiyonunu çalıştır
    asyncio.run(test_mcp())
