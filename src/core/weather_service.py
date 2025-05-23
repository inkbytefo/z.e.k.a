# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Hava Durumu Servisi

import os
import json
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class WeatherService:
    """Hava durumu servisi.
    
    Bu sınıf, OpenWeatherMap API'sini kullanarak hava durumu
    bilgilerini getirir ve işler.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 1800):
        """Hava durumu servisi başlatıcısı.
        
        Args:
            api_key: OpenWeatherMap API anahtarı
            cache_ttl: Önbellek süresi (saniye)
        """
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeatherMap API anahtarı gerekli")
            
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geo_url = "https://api.openweathermap.org/geo/1.0"
        self.cache = {}  # Önbellek
        self.cache_ttl = cache_ttl  # Önbellek süresi (saniye)
        self.logger = logging.getLogger("weather_service")
        
    async def get_coordinates(self, location: str) -> Tuple[float, float]:
        """Konum adından koordinatları getirir.
        
        Args:
            location: Konum adı (şehir, ilçe, vb.)
            
        Returns:
            Tuple[float, float]: Enlem ve boylam
            
        Raises:
            ValueError: Konum bulunamazsa
        """
        cache_key = f"geo_{location}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_data["timestamp"] < self.cache_ttl:
                return cache_data["data"]
                
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": location,
                    "limit": 1,
                    "appid": self.api_key
                }
                
                async with session.get(f"{self.geo_url}/direct", params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Konum arama hatası: {error_text}")
                        raise ValueError(f"Konum arama hatası: {response.status}")
                        
                    data = await response.json()
                    
                    if not data:
                        raise ValueError(f"Konum bulunamadı: {location}")
                        
                    lat = data[0]["lat"]
                    lon = data[0]["lon"]
                    
                    # Önbelleğe ekle
                    self.cache[cache_key] = {
                        "data": (lat, lon),
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    return lat, lon
                    
        except Exception as e:
            self.logger.error(f"Konum arama hatası: {str(e)}")
            raise ValueError(f"Konum arama hatası: {str(e)}")
            
    async def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """Mevcut hava durumunu getirir.
        
        Args:
            location: Konum adı (şehir, ilçe, vb.)
            units: Birim sistemi (metric, imperial, standard)
            
        Returns:
            Dict[str, Any]: Hava durumu verileri
            
        Raises:
            ValueError: Hava durumu alınamazsa
        """
        cache_key = f"current_{location}_{units}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_data["timestamp"] < self.cache_ttl:
                return cache_data["data"]
                
        try:
            # Koordinatları al
            lat, lon = await self.get_coordinates(location)
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "lat": lat,
                    "lon": lon,
                    "units": units,
                    "appid": self.api_key,
                    "lang": "tr"  # Türkçe açıklamalar için
                }
                
                async with session.get(f"{self.base_url}/weather", params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Hava durumu alma hatası: {error_text}")
                        raise ValueError(f"Hava durumu alma hatası: {response.status}")
                        
                    data = await response.json()
                    
                    # Önbelleğe ekle
                    self.cache[cache_key] = {
                        "data": data,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    return data
                    
        except Exception as e:
            self.logger.error(f"Hava durumu alma hatası: {str(e)}")
            raise ValueError(f"Hava durumu alma hatası: {str(e)}")
            
    async def get_forecast(self, location: str, units: str = "metric", days: int = 5) -> Dict[str, Any]:
        """Hava durumu tahminini getirir.
        
        Args:
            location: Konum adı (şehir, ilçe, vb.)
            units: Birim sistemi (metric, imperial, standard)
            days: Tahmin günü sayısı (maksimum 5)
            
        Returns:
            Dict[str, Any]: Hava durumu tahmini verileri
            
        Raises:
            ValueError: Hava durumu tahmini alınamazsa
        """
        cache_key = f"forecast_{location}_{units}_{days}"
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now().timestamp() - cache_data["timestamp"] < self.cache_ttl:
                return cache_data["data"]
                
        try:
            # Koordinatları al
            lat, lon = await self.get_coordinates(location)
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "lat": lat,
                    "lon": lon,
                    "units": units,
                    "appid": self.api_key,
                    "lang": "tr",  # Türkçe açıklamalar için
                    "cnt": days * 8  # Her gün için 8 veri noktası (3 saatte bir)
                }
                
                async with session.get(f"{self.base_url}/forecast", params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Hava durumu tahmini alma hatası: {error_text}")
                        raise ValueError(f"Hava durumu tahmini alma hatası: {response.status}")
                        
                    data = await response.json()
                    
                    # Önbelleğe ekle
                    self.cache[cache_key] = {
                        "data": data,
                        "timestamp": datetime.now().timestamp()
                    }
                    
                    return data
                    
        except Exception as e:
            self.logger.error(f"Hava durumu tahmini alma hatası: {str(e)}")
            raise ValueError(f"Hava durumu tahmini alma hatası: {str(e)}")
            
    def format_current_weather(self, data: Dict[str, Any], units: str = "metric") -> Dict[str, Any]:
        """Mevcut hava durumu verilerini formatlar.
        
        Args:
            data: Hava durumu verileri
            units: Birim sistemi (metric, imperial, standard)
            
        Returns:
            Dict[str, Any]: Formatlanmış hava durumu verileri
        """
        try:
            # Sıcaklık birimi
            temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
            
            # Rüzgar hızı birimi
            wind_unit = "km/h" if units == "metric" else "mph" if units == "imperial" else "m/s"
            
            # Ana hava durumu
            weather = data["weather"][0]
            
            # Formatlanmış veri
            formatted = {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "temp_unit": temp_unit,
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_unit": wind_unit,
                "wind_direction": data["wind"]["deg"],
                "clouds": data["clouds"]["all"],
                "weather_id": weather["id"],
                "weather_main": weather["main"],
                "weather_description": weather["description"],
                "weather_icon": weather["icon"],
                "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M"),
                "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Hava durumu formatlarken hata: {str(e)}")
            return data  # Hata durumunda orijinal veriyi döndür
            
    def format_forecast(self, data: Dict[str, Any], units: str = "metric") -> List[Dict[str, Any]]:
        """Hava durumu tahmini verilerini formatlar.
        
        Args:
            data: Hava durumu tahmini verileri
            units: Birim sistemi (metric, imperial, standard)
            
        Returns:
            List[Dict[str, Any]]: Formatlanmış hava durumu tahmini verileri
        """
        try:
            # Sıcaklık birimi
            temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
            
            # Rüzgar hızı birimi
            wind_unit = "km/h" if units == "metric" else "mph" if units == "imperial" else "m/s"
            
            # Formatlanmış tahminler
            forecasts = []
            
            for item in data["list"]:
                # Tarih ve saat
                dt = datetime.fromtimestamp(item["dt"])
                
                # Ana hava durumu
                weather = item["weather"][0]
                
                # Formatlanmış tahmin
                forecast = {
                    "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": dt.strftime("%Y-%m-%d"),
                    "time": dt.strftime("%H:%M"),
                    "temperature": round(item["main"]["temp"]),
                    "feels_like": round(item["main"]["feels_like"]),
                    "temp_unit": temp_unit,
                    "humidity": item["main"]["humidity"],
                    "pressure": item["main"]["pressure"],
                    "wind_speed": item["wind"]["speed"],
                    "wind_unit": wind_unit,
                    "wind_direction": item["wind"]["deg"],
                    "clouds": item["clouds"]["all"],
                    "weather_id": weather["id"],
                    "weather_main": weather["main"],
                    "weather_description": weather["description"],
                    "weather_icon": weather["icon"]
                }
                
                forecasts.append(forecast)
                
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Hava durumu tahmini formatlarken hata: {str(e)}")
            return data["list"]  # Hata durumunda orijinal veriyi döndür
