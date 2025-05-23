# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Klavye Kontrol Modülü

import os
import platform
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from ..logging_manager import get_logger

class KeyboardControl:
    """Klavye kontrolü sağlayan sınıf.
    
    Bu sınıf, klavye tuşlarını simüle etme, metin yazma ve klavye kısayollarını
    kullanma işlevlerini sağlar.
    """
    
    def __init__(self):
        """KeyboardControl başlatıcısı."""
        self.logger = get_logger("keyboard_control")
        self.os_type = platform.system()
        
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
    
    async def send_keys(self, keys: str) -> Tuple[bool, str]:
        """Klavye tuşlarını gönderir.
        
        Args:
            keys: Gönderilecek tuşlar
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Tuşlar gönderiliyor: {keys}")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            self.pyautogui.write(keys)
            return True, f"Tuşlar gönderildi: {keys}"
        except Exception as e:
            self.logger.error(f"Tuş gönderme hatası: {str(e)}")
            return False, f"Tuş gönderme hatası: {str(e)}"
    
    async def send_key(self, key: str) -> Tuple[bool, str]:
        """Tek bir klavye tuşu gönderir.
        
        Args:
            key: Gönderilecek tuş
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Tuş gönderiliyor: {key}")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            self.pyautogui.press(key)
            return True, f"Tuş gönderildi: {key}"
        except Exception as e:
            self.logger.error(f"Tuş gönderme hatası: {str(e)}")
            return False, f"Tuş gönderme hatası: {str(e)}"
    
    async def send_shortcut(self, shortcut: str) -> Tuple[bool, str]:
        """Klavye kısayolu gönderir.
        
        Args:
            shortcut: Gönderilecek kısayol (örn. "ctrl+c", "alt+tab")
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Kısayol gönderiliyor: {shortcut}")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            # Kısayolu parçalara ayır
            keys = shortcut.split('+')
            
            # Kısayolu gönder
            self.pyautogui.hotkey(*keys)
            
            return True, f"Kısayol gönderildi: {shortcut}"
        except Exception as e:
            self.logger.error(f"Kısayol gönderme hatası: {str(e)}")
            return False, f"Kısayol gönderme hatası: {str(e)}"
    
    async def type_text(self, text: str, interval: float = 0.0) -> Tuple[bool, str]:
        """Metin yazar.
        
        Args:
            text: Yazılacak metin
            interval: Tuşlar arasındaki bekleme süresi (saniye)
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Metin yazılıyor: {text[:20]}{'...' if len(text) > 20 else ''}")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            self.pyautogui.write(text, interval=interval)
            return True, f"Metin yazıldı: {text[:20]}{'...' if len(text) > 20 else ''}"
        except Exception as e:
            self.logger.error(f"Metin yazma hatası: {str(e)}")
            return False, f"Metin yazma hatası: {str(e)}"
    
    async def press_and_hold(self, key: str, duration: float = 1.0) -> Tuple[bool, str]:
        """Tuşa basılı tutar.
        
        Args:
            key: Basılı tutulacak tuş
            duration: Basılı tutma süresi (saniye)
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Tuş basılı tutuluyor: {key} ({duration} saniye)")
        
        if not self.pyautogui:
            return False, "PyAutoGUI yüklü değil"
        
        try:
            self.pyautogui.keyDown(key)
            await asyncio.sleep(duration)
            self.pyautogui.keyUp(key)
            return True, f"Tuş basılı tutuldu: {key} ({duration} saniye)"
        except Exception as e:
            self.logger.error(f"Tuş basılı tutma hatası: {str(e)}")
            # Hata durumunda tuşu bırakmayı dene
            try:
                self.pyautogui.keyUp(key)
            except:
                pass
            return False, f"Tuş basılı tutma hatası: {str(e)}"
