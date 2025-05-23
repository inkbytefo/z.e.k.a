# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Masaüstü Denetleyicisi API Rotaları

import os
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query, Body, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.desktop import OSAbstractionLayer, ScreenPerception, KeyboardControl, ApplicationControl, BrowserControl
from core.logging_manager import get_logger
from config import STORAGE_PATH

# Logger
logger = get_logger("desktop_api")

# Router
router = APIRouter(prefix="/desktop", tags=["desktop"])

# Modeller
class CommandRequest(BaseModel):
    command: str = Field(..., description="Çalıştırılacak komut")

class TextExtractionRequest(BaseModel):
    image_data: str = Field(..., description="Base64 kodlanmış görüntü verisi veya dosya yolu")
    is_path: bool = Field(False, description="Görüntü verisi bir dosya yolu mu?")
    language: str = Field("tur+eng", description="OCR dili")

class RegionModel(BaseModel):
    x: int = Field(..., description="X koordinatı")
    y: int = Field(..., description="Y koordinatı")
    width: int = Field(..., description="Genişlik")
    height: int = Field(..., description="Yükseklik")

class CreateFileRequest(BaseModel):
    path: str = Field(..., description="Dosya yolu")
    content: str = Field("", description="Dosya içeriği")

class CreateDirectoryRequest(BaseModel):
    path: str = Field(..., description="Dizin yolu")

class DeleteItemRequest(BaseModel):
    path: str = Field(..., description="Silinecek öğe yolu")
    recursive: bool = Field(False, description="Dizin içeriğiyle birlikte sil (dizinler için)")

class ActivateWindowRequest(BaseModel):
    process_id: int = Field(..., description="İşlem ID'si")

class TerminateProcessRequest(BaseModel):
    process_id: int = Field(..., description="İşlem ID'si")

# Bileşenler
osal = OSAbstractionLayer()
screen_perception = ScreenPerception()
keyboard_control = KeyboardControl()
app_control = ApplicationControl()
browser_control = BrowserControl()

# Ekran görüntüleri için depolama dizini
SCREENSHOTS_DIR = os.path.join(STORAGE_PATH, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Rotalar
@router.get("/system-info")
async def get_system_info():
    """Sistem bilgilerini getirir."""
    try:
        import platform
        import psutil

        # Temel sistem bilgileri
        system_info = {
            "os": platform.system(),
            "version": platform.version(),
            "hostname": platform.node(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().used / (1024 * 1024),  # MB
            "total_memory": psutil.virtual_memory().total / (1024 * 1024),  # MB
            "disk_usage": psutil.disk_usage('/').used / (1024 * 1024),  # MB
            "total_disk": psutil.disk_usage('/').total / (1024 * 1024),  # MB
            "uptime": psutil.boot_time()
        }

        return {
            "success": True,
            "data": system_info
        }
    except Exception as e:
        logger.error(f"Sistem bilgileri alınırken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Sistem bilgileri alınamadı: {str(e)}"
        }

@router.get("/list-directory")
async def list_directory(path: str = Query(..., description="Listelenecek dizin yolu")):
    """Dizin içeriğini listeler."""
    try:
        success, result = await osal.list_directory(path)

        if not success:
            return {
                "success": False,
                "message": result
            }

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Dizin listelenirken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Dizin listelenemedi: {str(e)}"
        }

@router.get("/screenshot")
async def take_screenshot(
    region: Optional[str] = Query(None, description="Ekran bölgesi (JSON formatında: {x, y, width, height})"),
    save_path: Optional[str] = Query(None, description="Kaydedilecek dosya yolu")
):
    """Ekran görüntüsü alır."""
    try:
        # Bölge parametresini işle
        region_dict = None
        if region:
            import json
            region_dict = json.loads(region)
            region_tuple = (region_dict["x"], region_dict["y"], region_dict["width"], region_dict["height"])
        else:
            region_tuple = None

        # Ekran görüntüsü al
        success, screenshot = await screen_perception.capture_screen(region_tuple)

        if not success:
            return {
                "success": False,
                "message": screenshot
            }

        # Dosya yolu oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if save_path:
            file_path = save_path
        else:
            file_path = os.path.join(SCREENSHOTS_DIR, f"screenshot_{timestamp}.png")

        # Ekran görüntüsünü kaydet
        screenshot.save(file_path)

        # Base64 kodlaması
        import io
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {
            "success": True,
            "data": {
                "image_data": img_str,
                "timestamp": datetime.now().isoformat(),
                "path": file_path
            }
        }
    except Exception as e:
        logger.error(f"Ekran görüntüsü alınırken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Ekran görüntüsü alınamadı: {str(e)}"
        }

@router.post("/extract-text")
async def extract_text(request: TextExtractionRequest):
    """Görüntüden metin çıkarır."""
    try:
        if request.is_path:
            # Dosya yolundan görüntü yükle
            from PIL import Image
            image = Image.open(request.image_data)
        else:
            # Base64 kodlanmış veriyi çöz
            image_data = base64.b64decode(request.image_data)
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))

        # Metni çıkar
        success, text = await screen_perception.extract_text(image, request.language)

        if not success:
            return {
                "success": False,
                "message": text
            }

        return {
            "success": True,
            "data": {
                "text": text,
                "language": request.language
            }
        }
    except Exception as e:
        logger.error(f"Metin çıkarılırken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Metin çıkarılamadı: {str(e)}"
        }

@router.post("/execute-command")
async def execute_command(request: CommandRequest):
    """Sistem komutunu çalıştırır."""
    try:
        result = await osal.execute_command(request.command)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Komut çalıştırılırken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Komut çalıştırılamadı: {str(e)}"
        }

@router.get("/list-windows")
async def list_windows():
    """Açık pencereleri listeler."""
    try:
        success, result = await app_control.get_active_window()

        if not success:
            return {
                "success": False,
                "message": result
            }

        # Şimdilik sadece aktif pencereyi döndürüyoruz
        # İlerleyen aşamalarda tüm pencereleri listeleyeceğiz
        return {
            "success": True,
            "data": [result]
        }
    except Exception as e:
        logger.error(f"Pencereler listelenirken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Pencereler listelenemedi: {str(e)}",
            "data": []
        }

@router.post("/create-file")
async def create_file(request: CreateFileRequest):
    """Yeni dosya oluşturur."""
    try:
        # Güvenlik kontrolü - yolun güvenli olup olmadığını kontrol et
        if not is_safe_path(request.path):
            return {
                "success": False,
                "message": "Güvenlik nedeniyle bu yola erişim reddedildi"
            }

        # Dosya oluştur
        with open(request.path, 'w', encoding='utf-8') as f:
            f.write(request.content)

        return {
            "success": True,
            "message": f"Dosya oluşturuldu: {request.path}"
        }
    except Exception as e:
        logger.error(f"Dosya oluşturulurken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Dosya oluşturulamadı: {str(e)}"
        }

@router.post("/create-directory")
async def create_directory(request: CreateDirectoryRequest):
    """Yeni dizin oluşturur."""
    try:
        # Güvenlik kontrolü
        if not is_safe_path(request.path):
            return {
                "success": False,
                "message": "Güvenlik nedeniyle bu yola erişim reddedildi"
            }

        # Dizin oluştur
        success, result = await osal.create_directory(request.path)

        return {
            "success": success,
            "message": result
        }
    except Exception as e:
        logger.error(f"Dizin oluşturulurken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Dizin oluşturulamadı: {str(e)}"
        }

@router.post("/delete-item")
async def delete_item(request: DeleteItemRequest):
    """Dosya veya dizin siler."""
    try:
        # Güvenlik kontrolü
        if not is_safe_path(request.path):
            return {
                "success": False,
                "message": "Güvenlik nedeniyle bu yola erişim reddedildi"
            }

        # Dosya mı dizin mi kontrol et
        if os.path.isdir(request.path):
            success, result = await osal.delete_directory(request.path, request.recursive)
        else:
            success, result = await osal.delete_file(request.path)

        return {
            "success": success,
            "message": result
        }
    except Exception as e:
        logger.error(f"Öğe silinirken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Öğe silinemedi: {str(e)}"
        }

@router.post("/activate-window")
async def activate_window(request: ActivateWindowRequest):
    """Pencereyi etkinleştirir."""
    try:
        # Bu işlev henüz uygulanmadı
        return {
            "success": False,
            "message": "Pencere etkinleştirme işlevi henüz uygulanmadı"
        }
    except Exception as e:
        logger.error(f"Pencere etkinleştirilirken hata: {str(e)}")
        return {
            "success": False,
            "message": f"Pencere etkinleştirilemedi: {str(e)}"
        }

@router.post("/terminate-process")
async def terminate_process(request: TerminateProcessRequest):
    """İşlemi sonlandırır."""
    try:
        # Bu işlev henüz uygulanmadı
        return {
            "success": False,
            "message": "İşlem sonlandırma işlevi henüz uygulanmadı"
        }
    except Exception as e:
        logger.error(f"İşlem sonlandırılırken hata: {str(e)}")
        return {
            "success": False,
            "message": f"İşlem sonlandırılamadı: {str(e)}"
        }

# Güvenlik yardımcı fonksiyonu
def is_safe_path(path: str) -> bool:
    """Dosya yolunun güvenli olup olmadığını kontrol eder."""
    # Örnek güvenlik kontrolü - gerçek uygulamada daha kapsamlı olmalı
    unsafe_patterns = [
        "/etc/", "/var/", "/root/", "/boot/", "/bin/", "/sbin/",
        "C:\\Windows\\", "C:\\Program Files\\", "C:\\Program Files (x86)\\",
        "C:\\ProgramData\\", "C:\\System", "C:\\Users\\All Users\\"
    ]

    # Yolun mutlak olduğundan emin ol
    abs_path = os.path.abspath(path)

    # Tehlikeli yolları kontrol et
    for pattern in unsafe_patterns:
        if pattern.lower() in abs_path.lower():
            logger.warning(f"Güvenlik nedeniyle erişim reddedildi: {abs_path}")
            return False

    return True
