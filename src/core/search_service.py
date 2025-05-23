# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Arama Servisi Modülü

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SearchServiceBase(ABC):
    """Arama servisleri için temel soyut sınıf.
    
    Bu sınıf, farklı arama servisleri (Google, Bing)
    için ortak arayüzü tanımlar.
    """
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "web",
        language: Optional[str] = None,
        safe_search: bool = True
    ) -> List[Dict[str, Any]]:
        """Arama gerçekleştirir.
        
        Args:
            query: Arama sorgusu
            limit: Maksimum sonuç sayısı
            search_type: Arama tipi (web, image, news, etc.)
            language: Sonuç dili
            safe_search: Güvenli arama aktif/pasif
            
        Returns:
            List[Dict[str, Any]]: Arama sonuçları
        """
        pass
    
    @abstractmethod
    async def get_suggestions(
        self,
        query: str,
        limit: int = 5,
        language: Optional[str] = None
    ) -> List[str]:
        """Arama önerileri getirir.
        
        Args:
            query: Arama sorgusu
            limit: Maksimum öneri sayısı
            language: Sonuç dili
            
        Returns:
            List[str]: Arama önerileri
        """
        pass

class GoogleSearchService(SearchServiceBase):
    """Google Custom Search servisi implementasyonu."""
    
    def __init__(self, config: Dict[str, Any]):
        """GoogleSearchService başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.api_key = config["google_api_key"]
        self.search_engine_id = config["google_search_engine_id"]
        self.service = None
    
    def _init_service(self):
        """Google Custom Search servisini başlatır."""
        if not self.service:
            self.service = build(
                "customsearch",
                "v1",
                developerKey=self.api_key
            )
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "web",
        language: Optional[str] = None,
        safe_search: bool = True
    ) -> List[Dict[str, Any]]:
        """Google Custom Search ile arama yapar."""
        try:
            self._init_service()
            
            # Arama parametrelerini hazırla
            search_params = {
                'q': query,
                'cx': self.search_engine_id,
                'num': min(limit, 10),  # Google maksimum 10 sonuç döndürür
                'safe': 'high' if safe_search else 'off'
            }
            
            if language:
                search_params['lr'] = f'lang_{language}'
            
            if search_type != "web":
                search_params['searchType'] = search_type
            
            # Aramayı gerçekleştir
            results = []
            start_index = 1
            
            while len(results) < limit:
                search_params['start'] = start_index
                response = self.service.cse().list(**search_params).execute()
                
                if 'items' not in response:
                    break
                    
                for item in response['items']:
                    results.append({
                        'title': item['title'],
                        'snippet': item.get('snippet', ''),
                        'link': item['link'],
                        'type': search_type,
                        'source': 'google'
                    })
                    
                    if len(results) >= limit:
                        break
                
                start_index += len(response['items'])
                if start_index > 100:  # Google'ın maksimum sonuç limiti
                    break
            
            return results
            
        except HttpError as e:
            raise RuntimeError(f"Google arama hatası: {str(e)}")
    
    async def get_suggestions(
        self,
        query: str,
        limit: int = 5,
        language: Optional[str] = None
    ) -> List[str]:
        """Google Suggestions API üzerinden arama önerileri alır."""
        try:
            import requests
            
            # API parametrelerini hazırla
            params = {
                'client': 'chrome',
                'q': query,
                'hl': language or 'en'
            }
            
            # API'ye istek gönder
            response = requests.get(
                'https://suggestqueries.google.com/complete/search',
                params=params
            )
            
            if response.status_code == 200:
                suggestions = json.loads(response.text)[1]
                return suggestions[:limit]
            
            return []
            
        except Exception as e:
            raise RuntimeError(f"Google öneri alma hatası: {str(e)}")

class BingSearchService(SearchServiceBase):
    """Bing Web Search servisi implementasyonu."""
    
    def __init__(self, config: Dict[str, Any]):
        """BingSearchService başlatıcısı.
        
        Args:
            config: Yapılandırma ayarları
        """
        self.config = config
        self.subscription_key = config["bing_subscription_key"]
        self.endpoint = "https://api.bing.microsoft.com/v7.0"
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "web",
        language: Optional[str] = None,
        safe_search: bool = True
    ) -> List[Dict[str, Any]]:
        """Bing Web Search ile arama yapar."""
        try:
            import requests
            
            # Arama URL'sini belirle
            if search_type == "web":
                url = f"{self.endpoint}/search"
            elif search_type == "images":
                url = f"{self.endpoint}/images/search"
            elif search_type == "news":
                url = f"{self.endpoint}/news/search"
            else:
                url = f"{self.endpoint}/search"
            
            # Arama parametrelerini hazırla
            headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
            params = {
                "q": query,
                "count": limit,
                "offset": 0,
                "mkt": language or "en-US",
                "safeSearch": "Strict" if safe_search else "Off"
            }
            
            # API'ye istek gönder
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            search_results = response.json()
            
            # Sonuçları düzenle
            results = []
            
            if search_type == "web":
                items = search_results.get("webPages", {}).get("value", [])
            elif search_type == "images":
                items = search_results.get("value", [])
            elif search_type == "news":
                items = search_results.get("value", [])
            else:
                items = search_results.get("webPages", {}).get("value", [])
            
            for item in items[:limit]:
                result = {
                    'title': item['name'],
                    'snippet': item.get('snippet', ''),
                    'link': item['url'],
                    'type': search_type,
                    'source': 'bing'
                }
                
                # Resim araması için ek bilgiler
                if search_type == "images":
                    result.update({
                        'thumbnail': item.get('thumbnailUrl', ''),
                        'size': {
                            'width': item.get('width', 0),
                            'height': item.get('height', 0)
                        }
                    })
                
                # Haber araması için ek bilgiler
                elif search_type == "news":
                    result.update({
                        'date_published': item.get('datePublished', ''),
                        'provider': item.get('provider', [{}])[0].get('name', '')
                    })
                
                results.append(result)
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Bing arama hatası: {str(e)}")
    
    async def get_suggestions(
        self,
        query: str,
        limit: int = 5,
        language: Optional[str] = None
    ) -> List[str]:
        """Bing Autosuggest API üzerinden arama önerileri alır."""
        try:
            import requests
            
            # API'ye istek gönder
            url = f"{self.endpoint}/Suggestions"
            headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
            params = {
                "q": query,
                "mkt": language or "en-US"
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            suggestions = response.json()
            suggestion_groups = suggestions.get("suggestionGroups", [])
            
            if suggestion_groups:
                search_suggestions = suggestion_groups[0].get("searchSuggestions", [])
                return [
                    suggestion["displayText"]
                    for suggestion in search_suggestions[:limit]
                ]
            
            return []
            
        except Exception as e:
            raise RuntimeError(f"Bing öneri alma hatası: {str(e)}")
