# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# İşletim Sistemi Soyutlama Katmanı (OS Abstraction Layer)

import os
import platform
import asyncio
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from ..logging_manager import get_logger

class SystemController:
    """Temel sistem kontrolü sağlayan sınıf.
    
    Bu sınıf, işletim sistemi komutlarını çalıştırma ve uygulamaları açma gibi
    temel işlevleri sağlar.
    """
    
    def __init__(self):
        """SystemController başlatıcısı."""
        self.os_type = platform.system()
        self.logger = get_logger("system_controller")
        
    async def execute_command(self, command: str) -> str:
        """Sistem komutunu çalıştırır.
        
        Args:
            command: Çalıştırılacak komut
            
        Returns:
            str: Komutun çıktısı
            
        Raises:
            Exception: Komut çalıştırma hatası
        """
        self.logger.debug(f"Komut çalıştırılıyor: {command}")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            self.logger.error(f"Komut çalıştırma hatası: {error_msg}")
            raise Exception(f"Komut çalıştırma hatası: {error_msg}")
        
        return stdout.decode()
    
    async def open_application(self, app_name: str) -> str:
        """İşletim sistemine göre uygulama açar.
        
        Args:
            app_name: Açılacak uygulamanın adı
            
        Returns:
            str: İşlem sonucu
        """
        self.logger.info(f"Uygulama açılıyor: {app_name}")
        
        if self.os_type == "Windows":
            return await self.execute_command(f"start {app_name}")
        elif self.os_type == "Darwin":  # macOS
            return await self.execute_command(f"open -a '{app_name}'")
        else:  # Linux
            return await self.execute_command(f"{app_name} &")


class OSAbstractionLayer:
    """İşletim Sistemi Soyutlama Katmanı.
    
    Bu sınıf, farklı işletim sistemleri arasında tutarlı bir arayüz sağlar ve
    dosya/klasör işlemleri, pencere yönetimi gibi işlevleri sunar.
    """
    
    def __init__(self):
        """OSAbstractionLayer başlatıcısı."""
        self.os_type = platform.system()
        self.system_controller = SystemController()
        self.logger = get_logger("os_abstraction")
        
    async def execute_command(self, command: str) -> str:
        """Sistem komutunu çalıştırır.
        
        Args:
            command: Çalıştırılacak komut
            
        Returns:
            str: Komutun çıktısı
        """
        return await self.system_controller.execute_command(command)
        
    async def open_application(self, app_name: str) -> str:
        """Uygulamayı açar.
        
        Args:
            app_name: Açılacak uygulamanın adı
            
        Returns:
            str: İşlem sonucu
        """
        return await self.system_controller.open_application(app_name)
        
    async def create_directory(self, path: str) -> Tuple[bool, str]:
        """Dizin oluşturur.
        
        Args:
            path: Oluşturulacak dizinin yolu
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Dizin oluşturuluyor: {path}")
        
        try:
            os.makedirs(path, exist_ok=True)
            return True, f"Dizin oluşturuldu: {path}"
        except Exception as e:
            self.logger.error(f"Dizin oluşturma hatası: {str(e)}")
            return False, f"Dizin oluşturma hatası: {str(e)}"
            
    async def list_directory(self, path: str) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Dizin içeriğini listeler.
        
        Args:
            path: Listelenecek dizinin yolu
            
        Returns:
            Tuple[bool, Union[List[Dict[str, Any]], str]]: (Başarı durumu, İçerik listesi veya hata mesajı)
        """
        self.logger.debug(f"Dizin listeleniyor: {path}")
        
        try:
            items = os.listdir(path)
            result = []
            for item in items:
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                result.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "path": item_path
                })
            return True, result
        except Exception as e:
            self.logger.error(f"Dizin listeleme hatası: {str(e)}")
            return False, f"Dizin listeleme hatası: {str(e)}"
    
    async def delete_file(self, path: str) -> Tuple[bool, str]:
        """Dosyayı siler.
        
        Args:
            path: Silinecek dosyanın yolu
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Dosya siliniyor: {path}")
        
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                    return True, f"Dosya silindi: {path}"
                else:
                    return False, f"Belirtilen yol bir dosya değil: {path}"
            else:
                return False, f"Dosya bulunamadı: {path}"
        except Exception as e:
            self.logger.error(f"Dosya silme hatası: {str(e)}")
            return False, f"Dosya silme hatası: {str(e)}"
    
    async def delete_directory(self, path: str, recursive: bool = False) -> Tuple[bool, str]:
        """Dizini siler.
        
        Args:
            path: Silinecek dizinin yolu
            recursive: Dizin içeriğiyle birlikte silinsin mi?
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Dizin siliniyor: {path} (recursive={recursive})")
        
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    if recursive:
                        shutil.rmtree(path)
                    else:
                        os.rmdir(path)
                    return True, f"Dizin silindi: {path}"
                else:
                    return False, f"Belirtilen yol bir dizin değil: {path}"
            else:
                return False, f"Dizin bulunamadı: {path}"
        except Exception as e:
            self.logger.error(f"Dizin silme hatası: {str(e)}")
            return False, f"Dizin silme hatası: {str(e)}"
    
    async def move_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """Dosyayı taşır veya yeniden adlandırır.
        
        Args:
            source: Kaynak dosya yolu
            destination: Hedef dosya yolu
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Dosya taşınıyor: {source} -> {destination}")
        
        try:
            if os.path.exists(source):
                if os.path.isfile(source):
                    shutil.move(source, destination)
                    return True, f"Dosya taşındı: {source} -> {destination}"
                else:
                    return False, f"Belirtilen kaynak bir dosya değil: {source}"
            else:
                return False, f"Kaynak dosya bulunamadı: {source}"
        except Exception as e:
            self.logger.error(f"Dosya taşıma hatası: {str(e)}")
            return False, f"Dosya taşıma hatası: {str(e)}"
    
    async def copy_file(self, source: str, destination: str) -> Tuple[bool, str]:
        """Dosyayı kopyalar.
        
        Args:
            source: Kaynak dosya yolu
            destination: Hedef dosya yolu
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Dosya kopyalanıyor: {source} -> {destination}")
        
        try:
            if os.path.exists(source):
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                    return True, f"Dosya kopyalandı: {source} -> {destination}"
                else:
                    return False, f"Belirtilen kaynak bir dosya değil: {source}"
            else:
                return False, f"Kaynak dosya bulunamadı: {source}"
        except Exception as e:
            self.logger.error(f"Dosya kopyalama hatası: {str(e)}")
            return False, f"Dosya kopyalama hatası: {str(e)}"
    
    async def get_active_window(self) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Aktif pencere bilgisini alır.
        
        Returns:
            Tuple[bool, Union[Dict[str, Any], str]]: (Başarı durumu, Pencere bilgisi veya hata mesajı)
        """
        self.logger.debug("Aktif pencere bilgisi alınıyor")
        
        try:
            if self.os_type == "Windows":
                # Windows için aktif pencere bilgisini al
                # Not: Bu işlev için pywin32 kütüphanesi gereklidir
                # Şimdilik sadece bir yer tutucu olarak boş bırakıyoruz
                return False, "Windows için aktif pencere algılama henüz uygulanmadı"
            elif self.os_type == "Darwin":  # macOS
                # macOS için aktif pencere bilgisini al
                return False, "macOS için aktif pencere algılama henüz uygulanmadı"
            else:  # Linux
                # Linux için aktif pencere bilgisini al
                return False, "Linux için aktif pencere algılama henüz uygulanmadı"
        except Exception as e:
            self.logger.error(f"Aktif pencere bilgisi alma hatası: {str(e)}")
            return False, f"Aktif pencere bilgisi alma hatası: {str(e)}"
