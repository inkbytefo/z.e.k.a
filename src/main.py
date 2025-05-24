# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ana Uygulama Modülü

import os
import sys
import asyncio
import json
import time
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Proje kök dizinini ekle
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Çekirdek bileşenleri içe aktar
from src.core.orchestrator import Orchestrator
from src.core.memory_manager import MemoryManager
from src.core.user_profile import UserProfile
from src.core.mcp_manager import MCPManager
from src.core.logging_manager import get_logger
from src.core.exceptions import ZEKAError

# Ajanları içe aktar
from src.agents.conversation_agent import ConversationAgent
from src.agents.calendar_agent import CalendarAgent
from src.agents.email_agent import EmailAgent
from src.agents.research_agent import ResearchAgent
# from src.agents.coding_agent import CodingAgent  # Faz 3'te eklenecek

# Yapılandırma
from src.config import USER_ID, MEMORY_PATH, PROFILES_PATH, LOGS_PATH

class ZEKAAssistant:
    """ZEKA Asistanı ana uygulama sınıfı.

    Bu sınıf, tüm bileşenleri bir araya getirir ve asistanın ana işlevselliğini sağlar.
    """

    def __init__(self, user_id: str = USER_ID):
        """ZEKA Asistanı başlatıcısı.

        Args:
            user_id: Kullanıcı tanımlayıcısı
        """
        # Kullanıcı kimliği
        self.user_id = user_id

        # Loglama
        self.logger = get_logger("zeka_assistant")

        # Veri dizinlerini oluştur
        self._create_data_directories()

        # Çekirdek bileşenleri başlat
        self.memory_manager = MemoryManager(storage_path=MEMORY_PATH, vector_db_enabled=True)
        self.user_profile = UserProfile(user_id, storage_path=PROFILES_PATH)
        self.mcp_manager = MCPManager(storage_path=str(project_root / "data" / "mcp"))
        self.orchestrator = Orchestrator()

        # Durum izleme
        self.is_running = False
        self.start_time = time.time()

        # Asenkron görevler
        self.tasks = []

        self.logger.info(f"ZEKA Asistanı başlatıldı. Kullanıcı: {user_id}")

    async def initialize(self):
        """Asistanı asenkron olarak başlatır."""
        try:
            self.logger.info("ZEKA Asistanı başlatılıyor...")

            # Bileşenleri birbirine bağla
            self.orchestrator.set_memory_manager(self.memory_manager)
            await self.orchestrator.set_user_profile(self.user_profile)
            await self.orchestrator.set_mcp_manager(self.mcp_manager)

            # Ajanları kaydet
            await self._register_agents()

            # Durum güncelle
            self.is_running = True

            self.logger.info("ZEKA Asistanı başlatma tamamlandı")
            print(f"ZEKA Asistanı başlatıldı. Kullanıcı: {self.user_id}")

        except Exception as e:
            self.logger.error(f"ZEKA Asistanı başlatılırken hata: {str(e)}", exc_info=True)
            raise ZEKAError(f"ZEKA Asistanı başlatılamadı: {str(e)}")

    def _create_data_directories(self):
        """Gerekli veri dizinlerini oluşturur."""
        try:
            os.makedirs(MEMORY_PATH, exist_ok=True)
            os.makedirs(PROFILES_PATH, exist_ok=True)
            os.makedirs(project_root / "data" / "models", exist_ok=True)
            os.makedirs(LOGS_PATH, exist_ok=True)
            self.logger.debug("Veri dizinleri oluşturuldu")
        except Exception as e:
            self.logger.error(f"Veri dizinleri oluşturulurken hata: {str(e)}", exc_info=True)
            raise ZEKAError(f"Veri dizinleri oluşturulamadı: {str(e)}")

    async def _register_agents(self):
        """Ajanları orkestratöre kaydeder."""
        try:
            self.logger.info("Ajanlar kaydediliyor...")

            # OpenAI istemcisini başlat
            from src.core.openai_client import OpenAIClient
            try:
                # .env dosyasından model bilgisini al, yoksa varsayılan değeri kullan
                default_model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
                self.logger.info(f"Dil modeli başlatılıyor: {default_model}")

                # OpenAI istemcisini başlat
                openai_client = OpenAIClient(
                    default_model=default_model,
                    timeout=120.0,  # 2 dakika zaman aşımı
                    max_retries=3   # 3 kez yeniden deneme
                )
                self.logger.info("OpenAI istemcisi başarıyla başlatıldı")
            except Exception as e:
                self.logger.error(f"OpenAI istemcisi başlatılırken hata: {str(e)}", exc_info=True)
                raise ZEKAError(f"Dil modeli başlatılamadı: {str(e)}")

            # Sohbet ajanı
            conversation_agent = ConversationAgent("conversation_agent", "Sohbet Ajanı", "Genel sohbet ve iletişim")
            conversation_agent.set_memory_access(self.memory_manager.get_access_interface())
            conversation_agent.set_user_profile_access(self.user_profile.get_access_interface())
            conversation_agent.set_mcp_manager(self.mcp_manager)
            conversation_agent.set_language_model(openai_client)  # Dil modelini ayarla
            self.orchestrator.register_agent(
                "conversation_agent",
                conversation_agent,
                capabilities={"conversation", "general_knowledge", "memory_recall"}
            )
            self.logger.debug("Sohbet ajanı kaydedildi")

            # Takvim ajanı
            calendar_agent = CalendarAgent("calendar_agent", "Takvim Ajanı", "Takvim ve toplantı yönetimi")
            calendar_agent.set_memory_access(self.memory_manager.get_access_interface())
            calendar_agent.set_user_profile_access(self.user_profile.get_access_interface())
            calendar_agent.set_mcp_manager(self.mcp_manager)
            # Not: CalendarAgent sınıfında set_language_model metodu yok
            self.orchestrator.register_agent(
                "calendar_agent",
                calendar_agent,
                capabilities={"calendar_management", "scheduling", "time_management"}
            )
            self.logger.debug("Takvim ajanı kaydedildi")

            # E-posta ajanı
            email_agent = EmailAgent("email_agent", "E-posta Ajanı", "E-posta yönetimi ve organizasyonu")
            email_agent.set_memory_access(self.memory_manager.get_access_interface())
            email_agent.set_user_profile_access(self.user_profile.get_access_interface())
            email_agent.set_mcp_manager(self.mcp_manager)
            # Not: EmailAgent sınıfında set_language_model metodu yok
            self.orchestrator.register_agent(
                "email_agent",
                email_agent,
                capabilities={"email_handling", "communication", "contact_management"}
            )
            self.logger.debug("E-posta ajanı kaydedildi")

            # Araştırma ajanı
            research_agent = ResearchAgent("research_agent", "Araştırma Ajanı", "İnternet araştırması ve bilgi toplama")
            research_agent.set_memory_access(self.memory_manager.get_access_interface())
            research_agent.set_user_profile_access(self.user_profile.get_access_interface())
            research_agent.set_mcp_manager(self.mcp_manager)
            # Not: ResearchAgent sınıfında set_language_model metodu yok
            self.orchestrator.register_agent(
                "research_agent",
                research_agent,
                capabilities={"web_search", "information_synthesis", "research"}
            )
            self.logger.debug("Araştırma ajanı kaydedildi")

            self.logger.info("Tüm ajanlar başarıyla kaydedildi")

        except Exception as e:
            self.logger.error(f"Ajanlar kaydedilirken hata: {str(e)}", exc_info=True)
            raise ZEKAError(f"Ajanlar kaydedilemedi: {str(e)}")

    async def process_input(self, user_input: str) -> str:
        """Kullanıcı girdisini işler ve yanıt üretir.

        Args:
            user_input: Kullanıcı girdisi

        Returns:
            str: Asistan yanıtı
        """
        try:
            self.logger.info(f"Kullanıcı girdisi alındı: {user_input[:50]}...")

            # Asistan çalışıyor mu kontrol et
            if not self.is_running:
                self.logger.warning("Asistan henüz başlatılmadı, başlatılıyor...")
                await self.initialize()

            # Orkestratöre yönlendir
            start_time = time.time()
            response = await self.orchestrator.process_request(user_input)
            elapsed_time = time.time() - start_time

            self.logger.info(f"Yanıt üretildi ({elapsed_time:.2f}s): {response[:50]}...")
            return response

        except Exception as e:
            error_msg = f"İstek işlenirken hata: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return f"Üzgünüm, bir hata oluştu: {str(e)}"

    async def update_user_preference(self, preference_type: str, preference_value: Any) -> bool:
        """Kullanıcı tercihini günceller.

        Args:
            preference_type: Tercih türü
            preference_value: Tercih değeri

        Returns:
            bool: Başarılı olursa True
        """
        try:
            self.logger.info(f"Kullanıcı tercihi güncelleniyor: {preference_type}")
            await self.user_profile.set_preference(preference_type, preference_value)
            self.logger.debug(f"Kullanıcı tercihi güncellendi: {preference_type}={preference_value}")
            return True
        except Exception as e:
            self.logger.error(f"Kullanıcı tercihi güncellenirken hata: {str(e)}", exc_info=True)
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Sistem durumunu getirir.

        Returns:
            Dict[str, Any]: Sistem durumu bilgileri
        """
        try:
            # Çalışma süresi
            uptime = time.time() - self.start_time

            # Orkestratör metrikleri
            orchestrator_metrics = self.orchestrator.get_metrics() if hasattr(self.orchestrator, "get_metrics") else {}

            # Durum bilgilerini topla
            status = {
                "status": "running" if self.is_running else "stopped",
                "uptime": f"{uptime:.2f} saniye",
                "uptime_formatted": self._format_uptime(uptime),
                "user_profile": await self.user_profile.get_profile_summary(),
                "registered_agents": list(self.orchestrator.agents.keys()),
                "available_models": self.mcp_manager.list_available_models(),
                "available_capabilities": self.mcp_manager.list_available_capabilities(),
                "available_plugins": self.mcp_manager.list_available_plugins(),
                "metrics": orchestrator_metrics,
                "version": "1.0.0"  # Sürüm bilgisi
            }

            self.logger.debug("Sistem durumu alındı")
            return status

        except Exception as e:
            self.logger.error(f"Sistem durumu alınırken hata: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def _format_uptime(self, seconds: float) -> str:
        """Çalışma süresini formatlar.

        Args:
            seconds: Saniye cinsinden süre

        Returns:
            str: Formatlanmış süre
        """
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        parts = []
        if days > 0:
            parts.append(f"{days} gün")
        if hours > 0:
            parts.append(f"{hours} saat")
        if minutes > 0:
            parts.append(f"{minutes} dakika")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} saniye")

        return ", ".join(parts)

    async def shutdown(self) -> None:
        """Asistanı güvenli bir şekilde kapatır."""
        if not self.is_running:
            self.logger.warning("Asistan zaten kapalı")
            return

        try:
            self.logger.info("ZEKA Asistanı kapatılıyor...")

            # Orkestratörü kapat
            if self.orchestrator:
                await self.orchestrator.shutdown()

            # Bellek yöneticisini kapat
            if self.memory_manager:
                await self.memory_manager.cleanup()

            # Durum güncelle
            self.is_running = False

            # Çalışma süresi
            uptime = time.time() - self.start_time
            self.logger.info(f"ZEKA Asistanı kapatıldı. Çalışma süresi: {self._format_uptime(uptime)}")

        except Exception as e:
            self.logger.error(f"ZEKA Asistanı kapatılırken hata: {str(e)}", exc_info=True)

# Asenkron komut satırı arayüzü
async def async_main():
    """Ana uygulama başlangıç noktası (asenkron)."""
    logger = get_logger("main")
    logger.info("ZEKA Asistanı başlatılıyor...")

    print("ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı")
    print("=" * 60)

    # Kullanıcı kimliğini al
    user_id = input("Kullanıcı adınızı girin (varsayılan: default_user): ").strip() or USER_ID

    # Asistanı başlat
    assistant = ZEKAAssistant(user_id)
    await assistant.initialize()

    print("\nZEKA Asistanı hazır! Çıkmak için 'çıkış' yazın.")

    # Sinyal işleyicileri
    def signal_handler(sig, frame):
        print("\nKapatma sinyali alındı. ZEKA Asistanı kapatılıyor...")
        asyncio.create_task(assistant.shutdown())

    # CTRL+C işleyicisi
    signal.signal(signal.SIGINT, signal_handler)

    # Ana etkileşim döngüsü
    while True:
        try:
            user_input = input("\nSiz: ").strip()

            if user_input.lower() in ["çıkış", "çık", "exit", "quit"]:
                print("ZEKA Asistanı kapatılıyor...")
                await assistant.shutdown()
                break

            # Sistem komutlarını işle
            if user_input.startswith("sistem:"):
                parts = user_input.split(" ", 1)
                command = parts[0][7:]  # "sistem:" önekini kaldır
                args = parts[1] if len(parts) > 1 else ""

                if command == "durum":
                    # Sistem durumunu göster
                    status = await assistant.get_system_status()
                    print("\nSistem Durumu:")
                    print(f"  Durum: {status['status']}")
                    print(f"  Çalışma Süresi: {status['uptime_formatted']}")
                    print(f"  Sürüm: {status['version']}")
                    print("\nAjanlar:")
                    for agent in status['registered_agents']:
                        print(f"  - {agent}")

                    if 'metrics' in status and status['metrics']:
                        print("\nMetrikler:")
                        metrics = status['metrics']
                        print(f"  İstek Sayısı: {metrics.get('request_count', 0)}")
                        print(f"  Başarılı: {metrics.get('success_count', 0)}")
                        print(f"  Hata: {metrics.get('error_count', 0)}")
                        print(f"  Başarı Oranı: {metrics.get('success_rate', 0):.1f}%")
                        print(f"  Ortalama Yanıt Süresi: {metrics.get('avg_response_time', 0):.2f}s")

                elif command == "yardım":
                    # Sistem komut yardımı
                    print("\nSistem Komutları:")
                    print("  sistem:durum - Sistem durumunu göster")
                    print("  sistem:yardım - Bu yardım mesajını göster")
                    print("  çıkış - Uygulamayı kapat")

                else:
                    print(f"Bilinmeyen sistem komutu: {command}")
                    print("Yardım için 'sistem:yardım' yazın.")

            # MCP komutlarını işle
            elif user_input.startswith("mcp:"):
                parts = user_input.split(" ", 1)
                command = parts[0][4:]  # "mcp:" önekini kaldır
                args = parts[1] if len(parts) > 1 else ""

                if command == "servers":
                    # MCP sunucularını listele
                    servers = assistant.mcp_manager.list_servers()
                    print("\nMCP Sunucuları:")
                    for server in servers:
                        default_mark = " (Varsayılan)" if server["is_default"] else ""
                        official_mark = " [Resmi]" if server["is_official"] else ""
                        print(f"  - {server['name']}{default_mark}{official_mark}")
                        print(f"    ID: {server['server_id']}")
                        print(f"    URL: {server['url']}")
                        print(f"    Durum: {server['status']}")
                        print(f"    Açıklama: {server['description']}")
                        print()

                elif command == "add":
                    # MCP sunucusu ekle
                    try:
                        server_data = json.loads(args)

                        name = server_data.get("name", "")
                        url = server_data.get("url", "")
                        api_key = server_data.get("api_key", None)
                        description = server_data.get("description", "")
                        is_official = server_data.get("is_official", False)
                        set_as_default = server_data.get("set_as_default", False)

                        if not name or not url:
                            print("Hata: Sunucu adı ve URL'si gereklidir.")
                            continue

                        server_id = await assistant.mcp_manager.add_server(
                            name=name,
                            url=url,
                            api_key=api_key,
                            description=description,
                            is_official=is_official,
                            set_as_default=set_as_default
                        )

                        print(f"MCP sunucusu eklendi: {name} (ID: {server_id})")

                    except Exception as e:
                        print(f"Hata: MCP sunucusu eklenirken bir sorun oluştu: {e}")
                        print('Kullanım: mcp:add {"name": "Sunucu Adı", "url": "https://sunucu-url.com", "api_key": "opsiyonel-api-anahtari", "description": "Açıklama", "is_official": false, "set_as_default": false}')

                elif command == "remove":
                    # MCP sunucusu kaldır
                    server_id = args.strip()
                    if not server_id:
                        print("Hata: Sunucu ID'si gereklidir.")
                        continue

                    result = await assistant.mcp_manager.remove_server(server_id)
                    if result:
                        print(f"MCP sunucusu kaldırıldı: {server_id}")
                    else:
                        print(f"Hata: MCP sunucusu kaldırılamadı: {server_id}")

                elif command == "default":
                    # Varsayılan MCP sunucusunu ayarla
                    server_id = args.strip()
                    if not server_id:
                        print("Hata: Sunucu ID'si gereklidir.")
                        continue

                    result = await assistant.mcp_manager.set_default_server(server_id)
                    if result:
                        print(f"Varsayılan MCP sunucusu ayarlandı: {server_id}")
                    else:
                        print(f"Hata: Varsayılan MCP sunucusu ayarlanamadı: {server_id}")

                elif command == "models":
                    # Kullanılabilir modelleri listele
                    models = assistant.mcp_manager.list_available_models()
                    print("\nKullanılabilir Modeller:")
                    for model in models:
                        print(f"  - {model}")

                elif command == "capabilities":
                    # Kullanılabilir yetenekleri listele
                    capabilities = assistant.mcp_manager.list_available_capabilities()
                    print("\nKullanılabilir Yetenekler:")
                    for capability in capabilities:
                        print(f"  - {capability}")

                elif command == "help":
                    # MCP komut yardımı
                    print("\nMCP Komutları:")
                    print("  mcp:servers - MCP sunucularını listele")
                    print('  mcp:add {"name": "Sunucu Adı", "url": "https://sunucu-url.com", ...} - MCP sunucusu ekle')
                    print("  mcp:remove <server_id> - MCP sunucusunu kaldır")
                    print("  mcp:default <server_id> - Varsayılan MCP sunucusunu ayarla")
                    print("  mcp:models - Kullanılabilir modelleri listele")
                    print("  mcp:capabilities - Kullanılabilir yetenekleri listele")
                    print("  mcp:help - Bu yardım mesajını göster")

                else:
                    print(f"Bilinmeyen MCP komutu: {command}")
                    print("Yardım için 'mcp:help' yazın.")

            else:
                # Normal kullanıcı girdisini işle
                response = await assistant.process_input(user_input)

                # Yanıtı göster
                if response:
                    print(f"\nZEKA: {response}")
                else:
                    # Yanıt boş veya None ise debug bilgisi göster
                    print("\nZEKA: Üzgünüm, yanıt oluşturulamadı. Lütfen tekrar deneyin.")
                    print(f"\n[DEBUG] Yanıt boş veya None. Yanıt tipi: {type(response)}, Değer: '{response}'")

                    # Sistem durumunu kontrol et
                    try:
                        status = await assistant.get_system_status()
                        print("\n[DEBUG] Sistem durumu:")
                        print(f"  Durum: {status['status']}")
                        print(f"  Ajanlar: {', '.join(status['registered_agents'])}")
                        if 'metrics' in status and status['metrics']:
                            print(f"  Başarılı: {status['metrics'].get('success_count', 0)}")
                            print(f"  Hata: {status['metrics'].get('error_count', 0)}")
                    except Exception as e:
                        print(f"\n[DEBUG] Sistem durumu alınamadı: {str(e)}")

        except KeyboardInterrupt:
            print("\nKullanıcı tarafından durduruldu. ZEKA Asistanı kapatılıyor...")
            await assistant.shutdown()
            break

        except Exception as e:
            logger.error(f"Ana döngüde hata: {str(e)}", exc_info=True)
            print(f"\nHata: {str(e)}")

# Senkron ana fonksiyon
def main():
    """Ana uygulama başlangıç noktası."""
    try:
        # Windows'ta asyncio politikasını ayarla
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Asenkron ana fonksiyonu çalıştır
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nUygulama kapatılıyor...")
    except Exception as e:
        print(f"Kritik hata: {str(e)}")

if __name__ == "__main__":
    main()