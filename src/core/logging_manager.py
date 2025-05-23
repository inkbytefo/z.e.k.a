# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Loglama Yönetim Modülü

"""
Bu modül, ZEKA asistanı için merkezi loglama sistemini sağlar.
Farklı bileşenler için yapılandırılabilir loglama yetenekleri sunar.
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

# Renkli konsol çıktısı için ANSI renk kodları
class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

class ColoredFormatter(logging.Formatter):
    """Renkli konsol çıktısı sağlayan özel formatlayıcı."""
    
    COLORS = {
        logging.DEBUG: Colors.BLUE,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD
    }
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelno in self.COLORS:
            log_message = self.COLORS[record.levelno] + log_message + Colors.RESET
        return log_message

class JSONFormatter(logging.Formatter):
    """JSON formatında log çıktısı sağlayan özel formatlayıcı."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Ekstra alanları ekle
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)
            
        # Hata bilgilerini ekle
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        return json.dumps(log_data, ensure_ascii=False)

class LoggingManager:
    """Merkezi loglama yönetim sınıfı."""
    
    def __init__(
        self,
        log_dir: str = "./logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        json_format: bool = True,
        colored_console: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """Loglama yöneticisi başlatıcısı.
        
        Args:
            log_dir: Log dosyalarının saklanacağı dizin
            console_level: Konsol çıktısı için log seviyesi
            file_level: Dosya çıktısı için log seviyesi
            json_format: JSON formatında log tutulsun mu?
            colored_console: Konsol çıktısı renkli olsun mu?
            max_file_size: Maksimum log dosyası boyutu (byte)
            backup_count: Saklanacak eski log dosyası sayısı
        """
        self.log_dir = Path(log_dir)
        self.console_level = console_level
        self.file_level = file_level
        self.json_format = json_format
        self.colored_console = colored_console
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Log dizinini oluştur
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Kök logger'ı yapılandır
        self.root_logger = logging.getLogger("zeka")
        self.root_logger.setLevel(logging.DEBUG)  # En düşük seviye
        
        # Mevcut işleyicileri temizle
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
            
        # Konsol işleyicisi ekle
        self._add_console_handler()
        
        # Dosya işleyicisi ekle
        self._add_file_handler("zeka.log")
        
        # Hata işleyicisi ekle (sadece ERROR ve CRITICAL)
        self._add_file_handler("errors.log", min_level=logging.ERROR)
        
        self.root_logger.info("Loglama sistemi başlatıldı")
        
    def _add_console_handler(self):
        """Konsol işleyicisi ekler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        
        if self.colored_console:
            formatter = ColoredFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            
        console_handler.setFormatter(formatter)
        self.root_logger.addHandler(console_handler)
        
    def _add_file_handler(self, filename: str, min_level: int = None):
        """Dosya işleyicisi ekler.
        
        Args:
            filename: Log dosyası adı
            min_level: Minimum log seviyesi (None ise file_level kullanılır)
        """
        from logging.handlers import RotatingFileHandler
        
        file_path = self.log_dir / filename
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding="utf-8"
        )
        
        file_handler.setLevel(min_level if min_level is not None else self.file_level)
        
        if self.json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            
        file_handler.setFormatter(formatter)
        self.root_logger.addHandler(file_handler)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Belirli bir bileşen için logger döndürür.
        
        Args:
            name: Logger adı (genellikle modül adı)
            
        Returns:
            logging.Logger: Yapılandırılmış logger
        """
        return logging.getLogger(f"zeka.{name}")
    
    def log_exception(self, logger: logging.Logger, exception: Exception, extra: Dict[str, Any] = None):
        """Bir istisnayı detaylı şekilde loglar.
        
        Args:
            logger: Kullanılacak logger
            exception: Loglanan istisna
            extra: Eklenecek ek bilgiler
        """
        extra = extra or {}
        logger.exception(f"İstisna: {str(exception)}", extra=extra)
        
    def log_api_request(self, logger: logging.Logger, api_name: str, endpoint: str, method: str, params: Dict[str, Any] = None):
        """API isteğini loglar.
        
        Args:
            logger: Kullanılacak logger
            api_name: API adı
            endpoint: API endpoint'i
            method: HTTP metodu
            params: İstek parametreleri
        """
        logger.info(
            f"API İsteği: {api_name} - {method} {endpoint}",
            extra={
                "api_name": api_name,
                "endpoint": endpoint,
                "method": method,
                "params": params
            }
        )
        
    def log_api_response(self, logger: logging.Logger, api_name: str, endpoint: str, status_code: int, response_time: float, response_data: Any = None):
        """API yanıtını loglar.
        
        Args:
            logger: Kullanılacak logger
            api_name: API adı
            endpoint: API endpoint'i
            status_code: HTTP durum kodu
            response_time: Yanıt süresi (saniye)
            response_data: Yanıt verisi
        """
        logger.info(
            f"API Yanıtı: {api_name} - {endpoint} - {status_code} ({response_time:.2f}s)",
            extra={
                "api_name": api_name,
                "endpoint": endpoint,
                "status_code": status_code,
                "response_time": response_time,
                "response_data": response_data
            }
        )
        
    def log_task(self, logger: logging.Logger, task_id: str, action: str, status: str, details: Dict[str, Any] = None):
        """Görev bilgisini loglar.
        
        Args:
            logger: Kullanılacak logger
            task_id: Görev ID'si
            action: Görev eylemi (create, assign, complete, vb.)
            status: Görev durumu
            details: Ek görev detayları
        """
        logger.info(
            f"Görev: {action} - {task_id} - {status}",
            extra={
                "task_id": task_id,
                "action": action,
                "status": status,
                "details": details
            }
        )
        
    def log_agent_action(self, logger: logging.Logger, agent_id: str, action: str, details: Dict[str, Any] = None):
        """Ajan eylemini loglar.
        
        Args:
            logger: Kullanılacak logger
            agent_id: Ajan ID'si
            action: Eylem adı
            details: Eylem detayları
        """
        logger.info(
            f"Ajan Eylemi: {agent_id} - {action}",
            extra={
                "agent_id": agent_id,
                "action": action,
                "details": details
            }
        )

# Singleton loglama yöneticisi
_logging_manager = None

def get_logging_manager() -> LoggingManager:
    """Singleton loglama yöneticisini döndürür."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager

def get_logger(name: str) -> logging.Logger:
    """Belirli bir bileşen için logger döndürür."""
    return get_logging_manager().get_logger(name)
