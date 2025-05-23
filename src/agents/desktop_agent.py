# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Masaüstü Ajanı

import os
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from core.agent_base import Agent
from core.desktop.os_abstraction import OSAbstractionLayer
from core.desktop.screen_perception import ScreenPerception
from core.logging_manager import get_logger

class DesktopAgent(Agent):
    """Masaüstü etkileşimlerini yöneten ajan.

    Bu ajan, kullanıcının masaüstü ortamıyla etkileşimini sağlar. Dosya/klasör
    işlemleri, uygulama kontrolü, ekran algılama gibi işlevleri sunar.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        memory_access=None,
        comm_manager=None
    ):
        """DesktopAgent başlatıcısı.

        Args:
            agent_id: Ajan tanımlayıcısı
            name: Ajan adı
            description: Ajan açıklaması
            memory_access: Bellek erişim nesnesi
            comm_manager: İletişim yöneticisi
        """
        super().__init__(agent_id, name, description, memory_access, comm_manager)

        # Masaüstü bileşenlerini başlat
        self.osal = OSAbstractionLayer()
        self.screen_perception = ScreenPerception()

        # Loglama
        self.logger = get_logger("desktop_agent")

        # Yetenekler
        self.capabilities = {
            "execute_command": "Sistem komutlarını çalıştırma",
            "open_application": "Uygulamaları açma",
            "file_operations": "Dosya ve klasör işlemleri",
            "screen_capture": "Ekran görüntüsü alma",
            "text_recognition": "Ekrandan metin tanıma"
        }

        self.logger.info(f"Masaüstü Ajanı başlatıldı: {name}")

    async def process_request(self, user_request: str, intent: str, entities: Dict[str, Any]) -> str:
        """Kullanıcı isteğini işler.

        Args:
            user_request: Kullanıcı isteği
            intent: Tespit edilen niyet
            entities: Çıkarılan varlıklar

        Returns:
            str: İşlenmiş yanıt
        """
        self.logger.debug(f"İstek işleniyor: {intent} - {entities}")

        # Uygulama açma
        if intent == "open_application":
            return await self._handle_open_application(entities)

        # Komut çalıştırma
        elif intent == "execute_command":
            return await self._handle_execute_command(entities)

        # Ekran okuma
        elif intent == "read_screen":
            return await self._handle_read_screen(entities)

        # Dosya işlemleri
        elif intent == "file_operation":
            return await self._handle_file_operation(entities)

        # Bilinmeyen niyet
        else:
            self.logger.warning(f"Bilinmeyen niyet: {intent}")
            return f"Üzgünüm, '{intent}' niyetini nasıl işleyeceğimi bilmiyorum."

    async def _handle_open_application(self, entities: Dict[str, Any]) -> str:
        """Uygulama açma isteğini işler.

        Args:
            entities: Çıkarılan varlıklar

        Returns:
            str: İşlem sonucu
        """
        app_name = entities.get("app_name")
        if not app_name:
            return "Açılacak uygulama adı belirtilmedi."

        try:
            result = await self.osal.open_application(app_name)
            return f"{app_name} uygulaması açıldı."
        except Exception as e:
            self.logger.error(f"Uygulama açma hatası: {str(e)}")
            return f"Uygulama açılırken bir hata oluştu: {str(e)}"

    async def _handle_execute_command(self, entities: Dict[str, Any]) -> str:
        """Komut çalıştırma isteğini işler.

        Args:
            entities: Çıkarılan varlıklar

        Returns:
            str: İşlem sonucu
        """
        command = entities.get("command")
        if not command:
            return "Çalıştırılacak komut belirtilmedi."

        try:
            result = await self.osal.execute_command(command)
            return f"Komut çalıştırıldı. Sonuç:\n{result}"
        except Exception as e:
            self.logger.error(f"Komut çalıştırma hatası: {str(e)}")
            return f"Komut çalıştırılırken bir hata oluştu: {str(e)}"

    async def _handle_read_screen(self, entities: Dict[str, Any]) -> str:
        """Ekran okuma isteğini işler.

        Args:
            entities: Çıkarılan varlıklar

        Returns:
            str: İşlem sonucu
        """
        region = entities.get("region")

        try:
            success, screenshot = await self.screen_perception.capture_screen(region)
            if not success:
                return f"Ekran görüntüsü alınamadı: {screenshot}"

            success, text = await self.screen_perception.extract_text(screenshot)
            if not success:
                return f"Metin çıkarılamadı: {text}"

            if not text.strip():
                return "Ekranda okunabilir metin bulunamadı."

            return f"Ekranda şunlar yazıyor:\n{text}"
        except Exception as e:
            self.logger.error(f"Ekran okuma hatası: {str(e)}")
            return f"Ekran okunurken bir hata oluştu: {str(e)}"

    async def _handle_file_operation(self, entities: Dict[str, Any]) -> str:
        """Dosya işlemi isteğini işler.

        Args:
            entities: Çıkarılan varlıklar

        Returns:
            str: İşlem sonucu
        """
        operation = entities.get("operation")
        path = entities.get("path")

        if not operation:
            return "Yapılacak dosya işlemi belirtilmedi."

        if not path:
            return "Dosya veya klasör yolu belirtilmedi."

        try:
            if operation == "list":
                success, result = await self.osal.list_directory(path)
                if not success:
                    return f"Dizin listelenirken hata oluştu: {result}"

                # Sonucu formatla
                formatted_result = "\n".join([
                    f"[{'Klasör' if item['type'] == 'directory' else 'Dosya'}] {item['name']}"
                    for item in result
                ])

                return f"{path} içeriği:\n{formatted_result}"

            elif operation == "create_dir":
                success, result = await self.osal.create_directory(path)
                return result

            elif operation == "delete":
                if os.path.isdir(path):
                    success, result = await self.osal.delete_directory(path, recursive=entities.get("recursive", False))
                else:
                    success, result = await self.osal.delete_file(path)
                return result

            elif operation == "move":
                destination = entities.get("destination")
                if not destination:
                    return "Hedef yol belirtilmedi."

                success, result = await self.osal.move_file(path, destination)
                return result

            elif operation == "copy":
                destination = entities.get("destination")
                if not destination:
                    return "Hedef yol belirtilmedi."

                success, result = await self.osal.copy_file(path, destination)
                return result

            else:
                return f"Bilinmeyen dosya işlemi: {operation}"

        except Exception as e:
            self.logger.error(f"Dosya işlemi hatası: {str(e)}")
            return f"Dosya işlemi sırasında bir hata oluştu: {str(e)}"
