# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Orkestratör Modülü

from typing import Dict, List, Optional, Any, Set, Tuple, Union
import asyncio
import logging
from datetime import datetime
import time

from .communication import CommunicationManager, MessageType, TaskStatus, TaskPriority
from .task_manager import TaskManager, Task
from .memory_manager import MemoryManager
from .user_profile import UserProfile
from .mcp_manager import MCPManager
from .exceptions import ZEKAError, TaskError, AgentError
from .logging_manager import get_logger

class Orchestrator:
    """Çoklu ajan sistemini koordine eden merkezi orkestratör sınıfı.

    Bu sınıf, farklı uzmanlaşmış ajanlar arasındaki iletişimi ve görev dağılımını yönetir.
    Kullanıcı isteklerini analiz eder, görevleri oluşturur ve uygun ajanlara yönlendirir.
    """

    def __init__(self):
        """Orkestratör sınıfının başlatıcısı."""
        self.agents = {}
        self.memory_manager = None
        self.user_profile = None
        self.mcp_manager = None
        self.comm_manager = CommunicationManager()
        self.task_manager = TaskManager(self.comm_manager)

        # Asenkron event loop
        self.loop = asyncio.get_event_loop()
        self.running_tasks = set()

        # Loglama
        self.logger = get_logger("orchestrator")

        # Performans metrikleri
        self.metrics = {
            "request_count": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_response_time": 0,
            "total_response_time": 0
        }

    def register_agent(self, agent_id: str, agent: Any, capabilities: Optional[Set[str]] = None) -> None:
        """Sisteme yeni bir ajan ekler.

        Args:
            agent_id: Ajanın benzersiz tanımlayıcısı
            agent: Ajan nesnesi
            capabilities: Ajanın yetenekleri
        """
        try:
            # Ajan zaten kayıtlı mı kontrol et
            if agent_id in self.agents:
                self.logger.warning(f"Ajan zaten kayıtlı: {agent_id}. Güncelleniyor.")

            self.agents[agent_id] = agent

            # Ajan yeteneklerini kaydet
            if capabilities:
                self.task_manager.register_agent_capabilities(agent_id, capabilities)

            # İletişim yöneticisini ayarla
            agent.set_communication_manager(self.comm_manager)

            self.logger.info(f"Ajan başarıyla kaydedildi: {agent_id}")
        except Exception as e:
            self.logger.error(f"Ajan kaydedilirken hata oluştu: {agent_id}", exc_info=True)
            raise AgentError(f"Ajan kaydedilemedi: {str(e)}", agent_id=agent_id)

    def set_memory_manager(self, memory_manager: MemoryManager) -> None:
        """Bellek yöneticisini ayarlar.

        Args:
            memory_manager: Bellek yönetici nesnesi
        """
        try:
            self.memory_manager = memory_manager
            self.logger.info("Bellek yöneticisi ayarlandı")

            # Tüm ajanlara bellek erişimi sağla
            for agent_id, agent in self.agents.items():
                try:
                    agent.set_memory_access(memory_manager)
                    self.logger.debug(f"Bellek erişimi ayarlandı: {agent_id}")
                except Exception as e:
                    self.logger.error(f"Ajan için bellek erişimi ayarlanırken hata: {agent_id}", exc_info=True)
        except Exception as e:
            self.logger.error("Bellek yöneticisi ayarlanırken hata oluştu", exc_info=True)
            raise ZEKAError(f"Bellek yöneticisi ayarlanamadı: {str(e)}")

    async def set_user_profile(self, user_profile: UserProfile) -> None:
        """Kullanıcı profilini ayarlar.

        Args:
            user_profile: Kullanıcı profil nesnesi
        """
        try:
            self.user_profile = user_profile
            self.logger.info(f"Kullanıcı profili ayarlandı: {user_profile.user_id}")

            # Tüm ajanlara profil erişimi sağla
            for agent_id, agent in self.agents.items():
                try:
                    agent.set_user_profile_access(user_profile)
                    self.logger.debug(f"Kullanıcı profil erişimi ayarlandı: {agent_id}")
                except Exception as e:
                    self.logger.error(f"Ajan için kullanıcı profil erişimi ayarlanırken hata: {agent_id}", exc_info=True)
        except Exception as e:
            self.logger.error("Kullanıcı profili ayarlanırken hata oluştu", exc_info=True)
            raise ZEKAError(f"Kullanıcı profili ayarlanamadı: {str(e)}")

    async def set_mcp_manager(self, mcp_manager: MCPManager) -> None:
        """MCP yöneticisini ayarlar.

        Args:
            mcp_manager: MCP yönetici nesnesi
        """
        try:
            self.mcp_manager = mcp_manager
            self.logger.info("MCP yöneticisi ayarlandı")

            # Tüm ajanlara MCP erişimi sağla
            for agent_id, agent in self.agents.items():
                try:
                    agent.set_mcp_manager(mcp_manager)
                    self.logger.debug(f"MCP erişimi ayarlandı: {agent_id}")
                except Exception as e:
                    self.logger.error(f"Ajan için MCP erişimi ayarlanırken hata: {agent_id}", exc_info=True)
        except Exception as e:
            self.logger.error("MCP yöneticisi ayarlanırken hata oluştu", exc_info=True)
            raise ZEKAError(f"MCP yöneticisi ayarlanamadı: {str(e)}")

    async def process_request(self, user_request: str) -> str:
        """Kullanıcı isteğini işler ve uygun ajanlara yönlendirir.

        Args:
            user_request: Kullanıcı isteği metni

        Returns:
            str: İşlenmiş yanıt
        """
        start_time = time.time()
        self.metrics["request_count"] += 1

        try:
            self.logger.info(f"İstek alındı: {user_request[:50]}...")

            # İsteği analiz et
            intent, entities, required_capabilities = await self._analyze_request(user_request)
            self.logger.debug(f"İstek analizi: intent={intent}, capabilities={required_capabilities}")

            # Görev oluştur
            task = self.task_manager.create_task(
                title=f"Process: {intent}",
                description=user_request,
                priority=self._determine_priority(intent, entities),
                metadata={
                    "intent": intent,
                    "entities": entities,
                    "required_capabilities": required_capabilities
                }
            )
            self.logger.info(f"Görev oluşturuldu: {task.id} ({intent})")

            # Görev işlemeyi başlat
            processing_task = self.loop.create_task(self.task_manager.process_tasks())
            self.running_tasks.add(processing_task)
            processing_task.add_done_callback(self.running_tasks.discard)

            # Görev tamamlanana kadar bekle (zaman aşımı ile)
            timeout = 300  # 300 saniye (5 dakika) zaman aşımı
            start_wait = time.time()

            # Görev durumunu düzenli olarak kontrol et
            while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                await asyncio.sleep(0.1)

                # Görev durumunu güncelle
                task_history = self.comm_manager.get_task_history(task.id)
                if task_history:
                    # En son mesajı al
                    last_message = task_history[-1]

                    if last_message.type == MessageType.TASK_RESPONSE:
                        # Yanıtı metadata'ya ekle
                        task.metadata["result"] = last_message.content.get("result", {})
                        # Görev durumunu güncelle
                        await self.task_manager.update_task_status(task.id, TaskStatus.COMPLETED)
                        self.logger.debug(f"Görev tamamlandı: {task.id}")

                    elif last_message.type == MessageType.ERROR:
                        # Hata bilgisini metadata'ya ekle
                        task.metadata["error"] = last_message.content.get("error", "Bilinmeyen hata")
                        # Görev durumunu güncelle
                        await self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
                        self.logger.debug(f"Görev başarısız oldu: {task.id}")

                # Görev atanmış ama yanıt gelmiyorsa, ajanı kontrol et
                elif task.assigned_agent and task.status == TaskStatus.IN_PROGRESS:
                    # Görev atanma zamanını kontrol et
                    assigned_time = task.metadata.get("assigned_time", 0)
                    if assigned_time and (time.time() - assigned_time > 60):  # 60 saniye bekle
                        # Ajan yanıt vermiyorsa, görevi yeniden planla
                        self.logger.warning(f"Ajan yanıt vermiyor, görev yeniden planlanıyor: {task.id}")
                        # Görevi serbest bırak
                        await self.task_manager.update_task_status(task.id, TaskStatus.PENDING)
                        # Ajan iş yükünü güncelle
                        if task.assigned_agent in self.task_manager.agent_workload:
                            self.task_manager.agent_workload[task.assigned_agent] -= 1
                        # Ajan atamasını temizle
                        task.assigned_agent = None
                        # Görev işlemeyi yeniden başlat
                        processing_task = self.loop.create_task(self.task_manager.process_tasks())
                        self.running_tasks.add(processing_task)
                        processing_task.add_done_callback(self.running_tasks.discard)

                # Zaman aşımı kontrolü
                if time.time() - start_wait > timeout:
                    self.logger.warning(f"Görev zaman aşımına uğradı: {task.id}")
                    task.metadata["error"] = "Görev zaman aşımına uğradı"
                    await self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
                    raise TimeoutError(f"İstek zaman aşımına uğradı: {task.id}")

            # Sonucu belleğe kaydet
            if self.memory_manager and task.status == TaskStatus.COMPLETED:
                # Yanıtı al
                result = task.metadata.get("result", {})

                # Yanıt bir sözlük ise "response" veya "content" alanını al
                if isinstance(result, dict):
                    response = result.get("response", result.get("content", ""))
                else:
                    response = str(result)

                # Debug log ekle
                self.logger.debug(f"Görev sonucu: {result}")
                self.logger.debug(f"Yanıt: {response}")

                # Belleğe kaydet
                await self.memory_manager.store_interaction(
                    user_input=user_request,
                    system_response=response,
                    agent_id=task.assigned_agent,
                    metadata={
                        "intent": intent,
                        "task_id": task.id,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                self.logger.debug(f"Etkileşim belleğe kaydedildi: {task.id}")

                # Metrikleri güncelle
                self.metrics["success_count"] += 1
                elapsed_time = time.time() - start_time
                self.metrics["total_response_time"] += elapsed_time
                self.metrics["avg_response_time"] = (
                    self.metrics["total_response_time"] / self.metrics["success_count"]
                )

                self.logger.info(f"İstek başarıyla tamamlandı: {task.id} ({elapsed_time:.2f}s)")
                return response
            else:
                error_msg = f"Görev başarısız oldu: {task.id}"
                self.logger.error(error_msg)
                self.metrics["error_count"] += 1
                return "Üzgünüm, bu isteği şu anda işleyemiyorum."

        except Exception as e:
            elapsed_time = time.time() - start_time
            self.metrics["error_count"] += 1
            self.logger.error(f"İstek işlenirken hata oluştu ({elapsed_time:.2f}s): {str(e)}", exc_info=True)
            return f"Üzgünüm, bir hata oluştu: {str(e)}"

    async def _analyze_request(self, request: str) -> tuple[str, dict, set]:
        """Kullanıcı isteğini analiz eder ve amacını belirler.

        Args:
            request: Kullanıcı isteği

        Returns:
            tuple: (intent, entities, required_capabilities) üçlüsü
        """
        try:
            # Gelecekte NLP servisi entegrasyonu yapılacak
            # Şimdilik basit bir analiz:
            request_lower = request.lower()

            # MCP kullanarak analiz etmeyi dene
            if self.mcp_manager and self.mcp_manager.get_server():
                try:
                    # MCP üzerinden analiz yapmayı dene
                    self.logger.debug("MCP ile istek analizi deneniyor")
                    mcp_result = await self._analyze_with_mcp(request)
                    if mcp_result:
                        self.logger.info("İstek MCP ile analiz edildi")
                        return mcp_result
                except Exception as e:
                    self.logger.warning(f"MCP ile analiz başarısız oldu, yerel analiz kullanılıyor: {str(e)}")
                    # MCP hatası metriklerini güncelle
                    self.metrics["mcp_error_count"] = self.metrics.get("mcp_error_count", 0) + 1

            # Yerel analiz
            # Intent ve entity tespiti
            if "takvim" in request_lower or "toplantı" in request_lower:
                intent = "calendar"
                entities = {"action": "check" if "kontrol" in request_lower else "create"}
                capabilities = {"calendar_management"}
            elif "e-posta" in request_lower or "mail" in request_lower:
                intent = "email"
                entities = {"action": "read" if "oku" in request_lower else "send"}
                capabilities = {"email_handling"}
            elif "araştır" in request_lower or "bul" in request_lower:
                intent = "research"
                entities = {"query": request}
                capabilities = {"web_search", "information_synthesis"}
            elif "kod" in request_lower or "programlama" in request_lower:
                intent = "coding"
                entities = {"language": await self._detect_programming_language(request)}
                capabilities = {"code_generation", "code_analysis"}
            else:
                intent = "general"
                entities = {"text": request}
                capabilities = {"conversation"}

            self.logger.debug(f"İstek yerel olarak analiz edildi: {intent}")
            return intent, entities, capabilities

        except Exception as e:
            self.logger.error(f"İstek analizi sırasında hata: {str(e)}", exc_info=True)
            # Hata durumunda varsayılan değerler
            return "general", {"text": request, "error": str(e)}, {"conversation"}

    async def _analyze_with_mcp(self, request: str) -> Optional[tuple[str, dict, set]]:
        """MCP kullanarak isteği analiz eder.

        Args:
            request: Kullanıcı isteği

        Returns:
            Optional[tuple]: (intent, entities, required_capabilities) üçlüsü veya None
        """
        try:
            # MCP sunucusuna istek gönder (zaman aşımı süresini artırarak)
            response = await self.mcp_manager.send_request(
                "analyze",
                {
                    "text": request,
                    "analysis_type": "intent_detection"
                },
                timeout=30.0  # 30 saniye zaman aşımı
            )

            # Yanıt None ise (bağlantı hatası durumunda), yerel analiz için None döndür
            if response is None:
                self.logger.debug("MCP sunucusundan yanıt alınamadı, yerel analiz kullanılacak")
                return None

            if "result" in response:
                result = response["result"]
                return (
                    result.get("intent", "general"),
                    result.get("entities", {"text": request}),
                    set(result.get("capabilities", ["conversation"]))
                )
            return None
        except Exception as e:
            self.logger.error(f"MCP ile analiz sırasında hata: {str(e)}", exc_info=True)
            return None

    async def _detect_programming_language(self, request: str) -> Optional[str]:
        """İstekteki programlama dilini tespit eder.

        Args:
            request: Kullanıcı isteği

        Returns:
            Optional[str]: Tespit edilen programlama dili veya None
        """
        try:
            # Basit dil tespiti, gelecekte geliştirilecek
            common_languages = {
                "python": ["python", "pip", "django", "flask", "numpy", "pandas"],
                "javascript": ["javascript", "js", "node", "react", "vue", "angular", "typescript", "npm"],
                "java": ["java", "spring", "maven", "gradle", "android"],
                "csharp": ["c#", "csharp", ".net", "dotnet", "asp.net", "xamarin"],
                "go": ["golang", "go"],
                "rust": ["rust", "cargo", "rustc"],
                "php": ["php", "laravel", "symfony", "composer"],
                "ruby": ["ruby", "rails", "gem"],
                "swift": ["swift", "ios", "xcode"],
                "kotlin": ["kotlin", "android studio"]
            }

            request_lower = request.lower()

            # Önce tam eşleşmeleri kontrol et
            for lang, keywords in common_languages.items():
                if lang in request_lower:
                    self.logger.debug(f"Programlama dili tespit edildi (tam eşleşme): {lang}")
                    return lang

            # Sonra anahtar kelimeleri kontrol et
            for lang, keywords in common_languages.items():
                if any(keyword in request_lower for keyword in keywords):
                    self.logger.debug(f"Programlama dili tespit edildi (anahtar kelime): {lang}")
                    return lang

            self.logger.debug("Programlama dili tespit edilemedi")
            return None
        except Exception as e:
            self.logger.error(f"Programlama dili tespiti sırasında hata: {str(e)}", exc_info=True)
            return None

    def _determine_priority(self, intent: str, entities: Dict[str, Any]) -> TaskPriority:
        """Görev önceliğini belirler.

        Args:
            intent: İsteğin amacı
            entities: İstekten çıkarılan varlıklar

        Returns:
            TaskPriority: Belirlenen öncelik seviyesi
        """
        try:
            # Acil kelimeler kontrolü
            urgent_keywords = {"acil", "hemen", "önemli", "kritik", "acele"}

            # Metin içinde acil kelimeler var mı?
            text = entities.get("text", "")
            if isinstance(text, str) and any(keyword in text.lower() for keyword in urgent_keywords):
                self.logger.debug(f"Kritik öncelikli görev tespit edildi: {intent}")
                return TaskPriority.CRITICAL

            # İntent bazlı öncelik belirleme
            high_priority_intents = {"email", "calendar"}
            if intent in high_priority_intents:
                self.logger.debug(f"Yüksek öncelikli görev tespit edildi: {intent}")
                return TaskPriority.HIGH

            # Eylem bazlı öncelik belirleme
            action = entities.get("action", "")
            if action in {"send", "create", "delete", "update"}:
                self.logger.debug(f"Yüksek öncelikli eylem tespit edildi: {action}")
                return TaskPriority.HIGH

            self.logger.debug(f"Orta öncelikli görev: {intent}")
            return TaskPriority.MEDIUM

        except Exception as e:
            self.logger.error(f"Öncelik belirlenirken hata: {str(e)}", exc_info=True)
            return TaskPriority.MEDIUM

    async def shutdown(self) -> None:
        """Orkestratörü güvenli bir şekilde kapatır."""
        self.logger.info("Orkestratör kapatılıyor...")

        try:
            # Aktif görevlerin tamamlanmasını bekle
            if self.running_tasks:
                self.logger.debug(f"{len(self.running_tasks)} aktif görev tamamlanıyor...")
                await asyncio.gather(*self.running_tasks)

            # Ajanları temizle
            for agent_id, agent in self.agents.items():
                try:
                    if hasattr(agent, 'cleanup'):
                        self.logger.debug(f"Ajan temizleniyor: {agent_id}")
                        await agent.cleanup()
                except Exception as e:
                    self.logger.error(f"Ajan temizlenirken hata: {agent_id} - {str(e)}", exc_info=True)

            # Bellek yöneticisini temizle
            if self.memory_manager and hasattr(self.memory_manager, 'cleanup'):
                self.logger.debug("Bellek yöneticisi temizleniyor...")
                await self.memory_manager.cleanup()

            # Performans metriklerini logla
            self.logger.info(
                f"Performans metrikleri: "
                f"İstek sayısı={self.metrics['request_count']}, "
                f"Başarılı={self.metrics['success_count']}, "
                f"Hata={self.metrics['error_count']}, "
                f"Ortalama yanıt süresi={self.metrics['avg_response_time']:.2f}s"
            )

            self.logger.info("Orkestratör başarıyla kapatıldı")
        except Exception as e:
            self.logger.error(f"Orkestratör kapatılırken hata: {str(e)}", exc_info=True)

    def get_metrics(self) -> Dict[str, Any]:
        """Performans metriklerini döndürür.

        Returns:
            Dict[str, Any]: Performans metrikleri
        """
        return {
            "request_count": self.metrics["request_count"],
            "success_count": self.metrics["success_count"],
            "error_count": self.metrics["error_count"],
            "success_rate": (
                self.metrics["success_count"] / self.metrics["request_count"] * 100
                if self.metrics["request_count"] > 0 else 0
            ),
            "avg_response_time": self.metrics["avg_response_time"],
            "agent_count": len(self.agents),
            "active_tasks": len(self.running_tasks)
        }
