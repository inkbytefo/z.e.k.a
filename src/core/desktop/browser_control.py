# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Tarayıcı Kontrol Modülü

import os
import platform
import asyncio
import webbrowser
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from ..logging_manager import get_logger

class BrowserControl:
    """Tarayıcı kontrolü sağlayan sınıf.
    
    Bu sınıf, web tarayıcılarını kontrol etme, URL açma, web araması yapma
    gibi işlevleri sağlar.
    """
    
    def __init__(self):
        """BrowserControl başlatıcısı."""
        self.logger = get_logger("browser_control")
        self.os_type = platform.system()
        
        # Desteklenen tarayıcılar
        self.browsers = {
            "chrome": webbrowser.get("chrome") if self._is_browser_available("chrome") else None,
            "firefox": webbrowser.get("firefox") if self._is_browser_available("firefox") else None,
            "edge": webbrowser.get("edge") if self._is_browser_available("edge") else None,
            "safari": webbrowser.get("safari") if self._is_browser_available("safari") else None,
            "default": webbrowser.get()
        }
        
        # Desteklenen arama motorları
        self.search_engines = {
            "google": "https://www.google.com/search?q={}",
            "bing": "https://www.bing.com/search?q={}",
            "yahoo": "https://search.yahoo.com/search?p={}",
            "duckduckgo": "https://duckduckgo.com/?q={}",
            "yandex": "https://yandex.com/search/?text={}"
        }
        
        # Bağımlılıkları kontrol et ve yükle
        self._check_dependencies()
    
    def _is_browser_available(self, browser_name: str) -> bool:
        """Tarayıcının kullanılabilir olup olmadığını kontrol eder.
        
        Args:
            browser_name: Tarayıcı adı
            
        Returns:
            bool: Tarayıcı kullanılabilir mi?
        """
        try:
            webbrowser.get(browser_name)
            return True
        except webbrowser.Error:
            return False
    
    def _check_dependencies(self) -> None:
        """Gerekli bağımlılıkları kontrol eder ve yükler."""
        # Selenium
        try:
            import selenium
            self.selenium_available = True
            self.logger.debug("Selenium başarıyla içe aktarıldı")
        except ImportError:
            self.selenium_available = False
            self.logger.warning("Selenium yüklü değil. Gelişmiş tarayıcı kontrolü için 'pip install selenium' komutu ile yükleyin.")
        
        # Playwright
        try:
            import playwright
            self.playwright_available = True
            self.logger.debug("Playwright başarıyla içe aktarıldı")
        except ImportError:
            self.playwright_available = False
            self.logger.warning("Playwright yüklü değil. Gelişmiş tarayıcı kontrolü için 'pip install playwright' komutu ile yükleyin.")
    
    async def open_url(self, url: str, browser: str = "default") -> Tuple[bool, str]:
        """URL'yi tarayıcıda açar.
        
        Args:
            url: Açılacak URL
            browser: Kullanılacak tarayıcı
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"URL açılıyor: {url} (Tarayıcı: {browser})")
        
        # URL'nin geçerli olup olmadığını kontrol et
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        try:
            # Belirtilen tarayıcıyı kullan
            if browser in self.browsers and self.browsers[browser]:
                self.browsers[browser].open(url)
            else:
                # Varsayılan tarayıcıyı kullan
                webbrowser.open(url)
            
            return True, f"URL açıldı: {url}"
        except Exception as e:
            self.logger.error(f"URL açma hatası: {str(e)}")
            return False, f"URL açma hatası: {str(e)}"
    
    async def search_web(self, query: str, search_engine: str = "google") -> Tuple[bool, str]:
        """Web'de arama yapar.
        
        Args:
            query: Arama sorgusu
            search_engine: Kullanılacak arama motoru
            
        Returns:
            Tuple[bool, str]: (Başarı durumu, Mesaj)
        """
        self.logger.debug(f"Web'de arama yapılıyor: {query} (Arama motoru: {search_engine})")
        
        try:
            # Arama motorunu kontrol et
            if search_engine not in self.search_engines:
                search_engine = "google"
            
            # Arama URL'sini oluştur
            search_url = self.search_engines[search_engine].format(urllib.parse.quote(query))
            
            # URL'yi aç
            return await self.open_url(search_url)
        except Exception as e:
            self.logger.error(f"Web arama hatası: {str(e)}")
            return False, f"Web arama hatası: {str(e)}"
    
    async def get_available_browsers(self) -> List[str]:
        """Kullanılabilir tarayıcıları listeler.
        
        Returns:
            List[str]: Kullanılabilir tarayıcılar listesi
        """
        return [browser for browser, instance in self.browsers.items() if instance is not None]
    
    async def get_available_search_engines(self) -> List[str]:
        """Kullanılabilir arama motorlarını listeler.
        
        Returns:
            List[str]: Kullanılabilir arama motorları listesi
        """
        return list(self.search_engines.keys())
