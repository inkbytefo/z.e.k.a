# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Görev Yönetim Modülü

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import asyncio
import uuid
import time

from .communication import Message, MessageType, TaskStatus, TaskPriority, CommunicationManager

@dataclass
class Task:
    """Ajanlar tarafından işlenecek görev yapısı."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assigned_agent: Optional[str]
    parent_task_id: Optional[str]
    subtasks: List[str]  # Task ID'leri
    dependencies: List[str]  # Bağımlı olduğu Task ID'leri
    created_at: datetime
    deadline: Optional[datetime]
    metadata: Dict[str, Any]

class TaskManager:
    """Görev yönetimi ve dağıtımını sağlayan sınıf."""

    def __init__(self, communication_manager: CommunicationManager):
        """Görev yöneticisi başlatıcısı.

        Args:
            communication_manager: İletişim yöneticisi
        """
        self.comm_manager = communication_manager
        self.tasks: Dict[str, Task] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_workload: Dict[str, int] = {}
        self.task_queue = asyncio.PriorityQueue()

        # Görev yanıtlarını işlemek için abone ol
        self.comm_manager.subscribe("task_manager", self._handle_message)

    def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority,
        parent_task_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        deadline: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Yeni bir görev oluşturur.

        Args:
            title: Görev başlığı
            description: Görev açıklaması
            priority: Öncelik seviyesi
            parent_task_id: Üst görev ID'si (varsa)
            dependencies: Bağımlı olduğu görevlerin ID'leri
            deadline: Bitiş tarihi (varsa)
            metadata: Ek meta veriler

        Returns:
            Task: Oluşturulan görev
        """
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            assigned_agent=None,
            parent_task_id=parent_task_id,
            subtasks=[],
            dependencies=dependencies or [],
            created_at=datetime.now(),
            deadline=deadline,
            metadata=metadata or {}
        )

        self.tasks[task.id] = task
        asyncio.create_task(self._schedule_task(task))

        return task

    def register_agent_capabilities(self, agent_id: str, capabilities: Set[str]) -> None:
        """Bir ajanın yeteneklerini kaydeder.

        Args:
            agent_id: Ajan ID'si
            capabilities: Yetenekler kümesi
        """
        self.agent_capabilities[agent_id] = capabilities
        self.agent_workload[agent_id] = 0

    async def _schedule_task(self, task: Task) -> None:
        """Görevi öncelik sırasına göre planlar.

        Args:
            task: Planlanacak görev
        """
        # Öncelik değeri ne kadar düşükse o kadar öncelikli
        priority_value = task.priority.value
        await self.task_queue.put((priority_value, task.id))

    async def process_tasks(self) -> None:
        """Görev kuyruğunu sürekli işler."""
        while True:
            _, task_id = await self.task_queue.get()
            task = self.tasks[task_id]

            if not self._can_process_task(task):
                # Bağımlılıkları henüz tamamlanmamış, tekrar kuyruğa al
                asyncio.create_task(self._schedule_task(task))
                continue

            assigned_agent = self._select_best_agent(task)
            if assigned_agent:
                await self._assign_task(task, assigned_agent)
            else:
                # Uygun ajan bulunamadı, tekrar kuyruğa al
                asyncio.create_task(self._schedule_task(task))

    def _can_process_task(self, task: Task) -> bool:
        """Görevin işlenmeye hazır olup olmadığını kontrol eder.

        Args:
            task: Kontrol edilecek görev

        Returns:
            bool: Görev işlenmeye hazırsa True
        """
        # Tüm bağımlı görevlerin tamamlanmış olması gerekir
        return all(
            self.tasks[dep_id].status == TaskStatus.COMPLETED
            for dep_id in task.dependencies
        )

    def _select_best_agent(self, task: Task) -> Optional[str]:
        """Görev için en uygun ajanı seçer.

        Args:
            task: İşlenecek görev

        Returns:
            Optional[str]: Seçilen ajanın ID'si veya None
        """
        best_agent = None
        min_workload = float('inf')

        required_capabilities = task.metadata.get('required_capabilities', set())

        for agent_id, capabilities in self.agent_capabilities.items():
            # Ajan gerekli yeteneklere sahip mi?
            if not required_capabilities.issubset(capabilities):
                continue

            # En az yüklü ajanı seç
            workload = self.agent_workload[agent_id]
            if workload < min_workload:
                min_workload = workload
                best_agent = agent_id

        return best_agent

    async def _assign_task(self, task: Task, agent_id: str) -> None:
        """Görevi bir ajana atar.

        Args:
            task: Atanacak görev
            agent_id: Ajan ID'si
        """
        task.assigned_agent = agent_id
        task.status = TaskStatus.IN_PROGRESS
        self.agent_workload[agent_id] += 1

        # Görev atama zamanını kaydet
        task.metadata["assigned_time"] = time.time()

        # Görev mesajı oluştur ve gönder
        message = self.comm_manager.create_message(
            msg_type=MessageType.TASK_REQUEST,
            sender_id="task_manager",
            receiver_id=agent_id,
            content={
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "metadata": task.metadata
            },
            priority=task.priority
        )

        await self.comm_manager.send_message(message)

    async def _handle_message(self, message: Message) -> None:
        """Gelen mesajları işler.

        Args:
            message: Alınan mesaj
        """
        if message.type == MessageType.TASK_RESPONSE:
            # Görev yanıtı
            task_id = message.content.get("task_id")
            status = message.content.get("status", TaskStatus.COMPLETED)
            result = message.content.get("result", {})

            if task_id and task_id in self.tasks:
                # Görev sonucunu metadata'ya ekle
                self.tasks[task_id].metadata["result"] = result
                # Görev durumunu güncelle
                await self.update_task_status(task_id, status)

        elif message.type == MessageType.ERROR:
            # Hata mesajı
            task_id = message.content.get("task_id")
            error = message.content.get("error", "Bilinmeyen hata")

            if task_id and task_id in self.tasks:
                # Hata bilgisini metadata'ya ekle
                self.tasks[task_id].metadata["error"] = error
                # Görev durumunu güncelle
                await self.update_task_status(task_id, TaskStatus.FAILED)

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Görev durumunu günceller.

        Args:
            task_id: Görev ID'si
            status: Yeni durum
            result: Görev sonucu (varsa)
        """
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        old_status = task.status
        task.status = status

        # Sonuç varsa metadata'ya ekle
        if result:
            task.metadata["result"] = result

        # Tamamlanan görev için ajan iş yükünü azalt
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            if task.assigned_agent:
                self.agent_workload[task.assigned_agent] -= 1

        # Üst görevi güncelle
        if task.parent_task_id:
            parent_task = self.tasks[task.parent_task_id]
            if status == TaskStatus.COMPLETED:
                # Tüm alt görevler tamamlandıysa üst görevi de tamamla
                if all(self.tasks[sub_id].status == TaskStatus.COMPLETED
                      for sub_id in parent_task.subtasks):
                    await self.update_task_status(
                        task.parent_task_id,
                        TaskStatus.COMPLETED
                    )

    def split_task(
        self,
        task_id: str,
        subtask_definitions: List[Dict[str, Any]]
    ) -> List[str]:
        """Bir görevi alt görevlere böler.

        Args:
            task_id: Bölünecek görev ID'si
            subtask_definitions: Alt görev tanımlamaları listesi

        Returns:
            List[str]: Oluşturulan alt görev ID'leri
        """
        if task_id not in self.tasks:
            return []

        parent_task = self.tasks[task_id]
        subtask_ids = []

        for subtask_def in subtask_definitions:
            subtask = self.create_task(
                title=subtask_def["title"],
                description=subtask_def["description"],
                priority=parent_task.priority,
                parent_task_id=task_id,
                metadata=subtask_def.get("metadata", {})
            )
            subtask_ids.append(subtask.id)

        parent_task.subtasks.extend(subtask_ids)
        return subtask_ids

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Görev detaylarını getirir.

        Args:
            task_id: Görev ID'si

        Returns:
            Optional[Dict[str, Any]]: Görev detayları veya None
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "assigned_agent": task.assigned_agent,
            "parent_task_id": task.parent_task_id,
            "subtasks": [self.get_task_details(sub_id) for sub_id in task.subtasks],
            "dependencies": task.dependencies,
            "created_at": task.created_at,
            "deadline": task.deadline,
            "metadata": task.metadata
        }
