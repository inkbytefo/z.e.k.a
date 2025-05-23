# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ekran Algılama Modülü (Screen Perception Module)

import os
import platform
import asyncio
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging

from ..logging_manager import get_logger

class ScreenPerception:
    """Ekran algılama ve analiz işlevlerini sağlayan sınıf.
    
    Bu sınıf, ekran görüntüsü alma, OCR ile metin tanıma ve ekran analizi
    işlevlerini sağlar.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """ScreenPerception başlatıcısı.
        
        Args:
            tesseract_path: Tesseract OCR yürütülebilir dosyasının yolu (Windows için)
        """
        self.logger = get_logger("screen_perception")
        self.os_type = platform.system()
        
        # Tesseract yolunu ayarla
        if tesseract_path:
            self.tesseract_path = tesseract_path
        elif self.os_type == "Windows":
            self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        else:
            self.tesseract_path = None
        
        # Bağımlılıkları kontrol et ve yükle
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Gerekli bağımlılıkları kontrol eder ve yükler."""
        try:
            # PyAutoGUI
            import pyautogui
            self.pyautogui = pyautogui
            self.logger.debug("PyAutoGUI başarıyla içe aktarıldı")
        except ImportError:
            self.logger.error("PyAutoGUI yüklü değil. 'pip install pyautogui' komutu ile yükleyin.")
            self.pyautogui = None
        
        try:
            # Pillow (PIL)
            from PIL import Image
            self.Image = Image
            self.logger.debug("Pillow (PIL) başarıyla içe aktarıldı")
        except ImportError:
            self.logger.error("Pillow yüklü değil. 'pip install Pillow' komutu ile yükleyin.")
            self.Image = None
        
        try:
            # Tesseract OCR
            import pytesseract
            self.pytesseract = pytesseract
            
            # Tesseract yolunu ayarla (Windows için)
            if self.tesseract_path and self.os_type == "Windows":
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
            self.logger.debug("PyTesseract başarıyla içe aktarıldı")
        except ImportError:
            self.logger.error("PyTesseract yüklü değil. 'pip install pytesseract' komutu ile yükleyin.")
            self.pytesseract = None
    
    async def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[bool, Any]:
        """Ekran görüntüsü alır.
        
        Args:
            region: Ekran bölgesi (x, y, genişlik, yükseklik)
            
        Returns:
            Tuple[bool, Any]: (Başarı durumu, Görüntü nesnesi veya hata mesajı)
        """
        self.logger.debug(f"Ekran görüntüsü alınıyor: {region if region else 'tam ekran'}")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            if region:
                screenshot = self.pyautogui.screenshot(region=region)
            else:
                screenshot = self.pyautogui.screenshot()
            return True, screenshot
        except Exception as e:
            self.logger.error(f"Ekran görüntüsü alma hatası: {str(e)}")
            return False, f"Ekran görüntüsü alma hatası: {str(e)}"
    
    async def save_screenshot(self, path: str, region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[bool, str]:
        """Ekran görüntüsünü dosyaya kaydeder.
        
        Args:
            path: Kaydedilecek dosya yolu
            region: Ekran bölgesi (x, y, genişlik, yükseklik)
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Ekran görüntüsü kaydediliyor: {path}")
        
        success, result = await self.capture_screen(region)
        if not success:
            return False, result
        
        try:
            result.save(path)
            return True, f"Ekran görüntüsü kaydedildi: {path}"
        except Exception as e:
            self.logger.error(f"Ekran görüntüsü kaydetme hatası: {str(e)}")
            return False, f"Ekran görüntüsü kaydetme hatası: {str(e)}"
    
    async def extract_text(self, image, lang: str = "tur+eng") -> Tuple[bool, str]:
        """Görüntüden metin çıkarır.
        
        Args:
            image: Görüntü nesnesi veya dosya yolu
            lang: OCR dil kodu(ları)
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Çıkarılan metin veya hata mesajı)
        """
        self.logger.debug("Görüntüden metin çıkarılıyor")
        
        if not self.pytesseract:
            return False, "PyTesseract yüklü değil"
        
        try:
            text = self.pytesseract.image_to_string(image, lang=lang)
            return True, text
        except Exception as e:
            self.logger.error(f"Metin çıkarma hatası: {str(e)}")
            return False, f"Metin çıkarma hatası: {str(e)}"
    
    async def capture_and_extract_text(self, region: Optional[Tuple[int, int, int, int]] = None, lang: str = "tur+eng") -> Tuple[bool, str]:
        """Ekran görüntüsü alır ve metin çıkarır.
        
        Args:
            region: Ekran bölgesi (x, y, genişlik, yükseklik)
            lang: OCR dil kodu(ları)
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Çıkarılan metin veya hata mesajı)
        """
        self.logger.debug("Ekran görüntüsü alınıp metin çıkarılıyor")
        
        success, screenshot = await self.capture_screen(region)
        if not success:
            return False, screenshot
        
        return await self.extract_text(screenshot, lang)
    
    async def find_text_on_screen(self, text: str, region: Optional[Tuple[int, int, int, int]] = None, lang: str = "tur+eng") -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Ekranda belirli bir metni arar.
        
        Args:
            text: Aranacak metin
            region: Ekran bölgesi (x, y, genişlik, yükseklik)
            lang: OCR dil kodu(ları)
            
        Returns:
            Tuple[bool, Union[Dict[str, Any], str]]: (Başarı durumu, Sonuç bilgisi veya hata mesajı)
        """
        self.logger.debug(f"Ekranda metin aranıyor: {text}")
        
        success, screen_text = await self.capture_and_extract_text(region, lang)
        if not success:
            return False, screen_text
        
        if text.lower() in screen_text.lower():
            return True, {
                "found": True,
                "text": text,
                "screen_text": screen_text
            }
        else:
            return True, {
                "found": False,
                "text": text,
                "screen_text": screen_text
            }
    
    async def get_screen_info(self) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Ekran bilgilerini alır.
        
        Returns:
            Tuple[bool, Union[Dict[str, Any], str]]: (Başarı durumu, Ekran bilgisi veya hata mesajı)
        """
        self.logger.debug("Ekran bilgileri alınıyor")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            screen_width, screen_height = self.pyautogui.size()
            return True, {
                "width": screen_width,
                "height": screen_height,
                "resolution": f"{screen_width}x{screen_height}"
            }
        except Exception as e:
            self.logger.error(f"Ekran bilgisi alma hatası: {str(e)}")
            return False, f"Ekran bilgisi alma hatası: {str(e)}"
