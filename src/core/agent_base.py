# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ajan Temel Sınıfı

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime
import logging

from core.communication import Message, MessageType, TaskStatus, TaskPriority, CommunicationManager
from core.mcp_manager import MCPManager

class Agent(ABC):
    """Tüm ajanlar için temel soyut sınıf.

    Bu sınıf, tüm uzmanlaşmış ajanların uygulaması gereken temel işlevleri tanımlar.
    Her ajan bu sınıftan türetilmelidir. Ajanlar arası iletişim ve görev yönetimi
    yeteneklerini içerir.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: Optional[Set[str]] = None
    ):
        """Ajan temel sınıfının başlatıcısı.

        Args:
            agent_id (str): Ajanın benzersiz tanımlayıcısı
            name (str): Ajanın kullanıcı dostu adı
            description (str): Ajanın işlevinin açıklaması
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or set()
        self.tools = []
        self.memory_access = None
        self.user_profile_access = None
        self.comm_manager = None
        self.mcp_manager = None
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool: Any) -> None:
        """Ajana yeni bir araç ekler.

        Args:
            tool (Tool): Eklenen araç nesnesi
        """
        self.tools.append(tool)

    def set_memory_access(self, memory_access: Any) -> None:
        """Bellek erişimini ayarlar.

        Args:
            memory_access (MemoryAccess): Bellek erişim nesnesi
        """
        self.memory_access = memory_access

    def set_user_profile_access(self, user_profile_access: Any) -> None:
        """Kullanıcı profili erişimini ayarlar.

        Args:
            user_profile_access (UserProfileAccess): Kullanıcı profili erişim nesnesi
        """
        self.user_profile_access = user_profile_access

    def set_communication_manager(self, comm_manager: CommunicationManager) -> None:
        """İletişim yöneticisini ayarlar ve mesaj alıcıyı kaydeder.

        Args:
            comm_manager: İletişim yöneticisi
        """
        self.comm_manager = comm_manager
        self.comm_manager.subscribe(self.agent_id, self._handle_message)

    def set_mcp_manager(self, mcp_manager: MCPManager) -> None:
        """MCP yöneticisini ayarlar.

        Args:
            mcp_manager: MCP yöneticisi
        """
        self.mcp_manager = mcp_manager

    @abstractmethod
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
        pass

    async def _handle_message(self, message: Message) -> None:
        """Gelen mesajı işler.

        Args:
            message: Alınan mesaj
        """
        if message.type == MessageType.TASK_REQUEST:
            # Yeni görev isteği
            task_id = message.content["task_id"]
            self.active_tasks[task_id] = message.content

            try:
                result = await self.process_task(
                    task_id,
                    message.content["description"],
                    message.content["metadata"]
                )

                # Başarılı yanıt gönder
                response = self.comm_manager.create_message(
                    msg_type=MessageType.TASK_RESPONSE,
                    sender_id=self.agent_id,
                    receiver_id=message.sender_id,
                    content={
                        "task_id": task_id,
                        "status": TaskStatus.COMPLETED,
                        "result": result
                    },
                    priority=message.priority,
                    parent_task_id=task_id
                )
            except Exception as e:
                # Hata yanıtı gönder
                response = self.comm_manager.create_message(
                    msg_type=MessageType.ERROR,
                    sender_id=self.agent_id,
                    receiver_id=message.sender_id,
                    content={
                        "task_id": task_id,
                        "status": TaskStatus.FAILED,
                        "error": str(e)
                    },
                    priority=message.priority,
                    parent_task_id=task_id
                )

            await self.comm_manager.send_message(response)
            del self.active_tasks[task_id]

        elif message.type == MessageType.COLLABORATION:
            # İşbirliği isteği, alt sınıflar override edebilir
            pass
        """Ajana verilen görevi işler.

        Args:
            user_request (str): Orijinal kullanıcı isteği
            intent (str): İsteğin tespit edilen amacı
            entities (dict): İstekten çıkarılan varlıklar

        Returns:
            str: İşlenmiş yanıt
        """
        pass

    def get_relevant_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """İlgili bellek öğelerini getirir.

        Args:
            query (str): Arama sorgusu
            limit (int): Getirilecek maksimum öğe sayısı

        Returns:
            list: İlgili bellek öğeleri listesi
        """
        if self.memory_access:
            return self.memory_access.retrieve(query, limit)
        return []

    def get_user_preferences(self, preference_type: Optional[str] = None) -> Dict[str, Any]:
        """Kullanıcı tercihlerini getirir.

        Args:
            preference_type (str, optional): Tercih türü. None ise tüm tercihler getirilir.

        Returns:
            dict: Kullanıcı tercihleri
        """
        if self.user_profile_access:
            return self.user_profile_access.get_preferences(preference_type)
        return {}

    async def use_mcp_model(
        self,
        request_type: str,
        data: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP sunucusundaki bir modeli kullanır.

        Args:
            request_type: İstek türü (generate, embed, chat, vb.)
            data: İstek verileri
            server_id: İsteğin gönderileceği sunucunun ID'si. None ise varsayılan sunucu kullanılır.

        Returns:
            Dict[str, Any]: Sunucu yanıtı

        Raises:
            ValueError: MCP yöneticisi ayarlanmamışsa
            ConnectionError: MCP sunucusuna bağlanılamazsa
            Exception: İstek gönderilirken hata oluşursa
        """
        if not self.mcp_manager:
            raise ValueError("MCP yöneticisi ayarlanmamış.")

        try:
            return await self.mcp_manager.send_request(request_type, data, server_id)
        except Exception as e:
            logging.error(f"MCP modeli kullanılırken hata: {e}")
            raise

    def __str__(self):
        return f"{self.name} ({self.agent_id}): {self.description}"
