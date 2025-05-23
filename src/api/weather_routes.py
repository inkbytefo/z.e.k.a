# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Hava Durumu API Rotaları

import os
import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from core.weather_service import WeatherService
from core.auth.auth_dependencies import get_current_active_user

# API modellerini tanımla
class WeatherResponse(BaseModel):
    """Hava durumu yanıt modeli."""
    location: str
    country: str
    temperature: int
    feels_like: int
    temp_unit: str
    humidity: int
    pressure: int
    wind_speed: float
    wind_unit: str
    wind_direction: int
    clouds: int
    weather_id: int
    weather_main: str
    weather_description: str
    weather_icon: str
    sunrise: str
    sunset: str
    timestamp: str

class ForecastItem(BaseModel):
    """Hava durumu tahmini öğe modeli."""
    datetime: str
    date: str
    time: str
    temperature: int
    feels_like: int
    temp_unit: str
    humidity: int
    pressure: int
    wind_speed: float
    wind_unit: str
    wind_direction: int
    clouds: int
    weather_id: int
    weather_main: str
    weather_description: str
    weather_icon: str

class ForecastResponse(BaseModel):
    """Hava durumu tahmini yanıt modeli."""
    location: str
    country: str
    forecasts: List[ForecastItem]

# Router oluştur
router = APIRouter(prefix="/api/weather", tags=["weather"])

# Hava durumu servisi
weather_service = WeatherService(api_key=os.getenv("OPENWEATHERMAP_API_KEY"))

# Loglama
logger = logging.getLogger("weather_routes")

@router.get("/current", response_model=WeatherResponse)
async def get_current_weather(
    location: str = Query(..., description="Konum adı (şehir, ilçe, vb.)"),
    units: str = Query("metric", description="Birim sistemi (metric, imperial, standard)")
):
    """Mevcut hava durumunu getirir.
    
    Args:
        location: Konum adı (şehir, ilçe, vb.)
        units: Birim sistemi (metric, imperial, standard)
        
    Returns:
        WeatherResponse: Hava durumu verileri
        
    Raises:
        HTTPException: Hava durumu alınamazsa
    """
    try:
        # Hava durumunu al
        weather_data = await weather_service.get_current_weather(location, units)
        
        # Verileri formatla
        formatted_data = weather_service.format_current_weather(weather_data, units)
        
        return formatted_data
        
    except ValueError as e:
        logger.error(f"Hava durumu alma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Hava durumu alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hava durumu alınamadı: {str(e)}")

@router.get("/forecast", response_model=ForecastResponse)
async def get_weather_forecast(
    location: str = Query(..., description="Konum adı (şehir, ilçe, vb.)"),
    units: str = Query("metric", description="Birim sistemi (metric, imperial, standard)"),
    days: int = Query(1, description="Tahmin günü sayısı (maksimum 5)")
):
    """Hava durumu tahminini getirir.
    
    Args:
        location: Konum adı (şehir, ilçe, vb.)
        units: Birim sistemi (metric, imperial, standard)
        days: Tahmin günü sayısı (maksimum 5)
        
    Returns:
        ForecastResponse: Hava durumu tahmini verileri
        
    Raises:
        HTTPException: Hava durumu tahmini alınamazsa
    """
    try:
        # Gün sayısını kontrol et
        if days < 1 or days > 5:
            raise ValueError("Tahmin günü sayısı 1-5 arasında olmalıdır")
            
        # Hava durumu tahminini al
        forecast_data = await weather_service.get_forecast(location, units, days)
        
        # Verileri formatla
        formatted_forecasts = weather_service.format_forecast(forecast_data, units)
        
        # Yanıt oluştur
        response = {
            "location": forecast_data["city"]["name"],
            "country": forecast_data["city"]["country"],
            "forecasts": formatted_forecasts
        }
        
        return response
        
    except ValueError as e:
        logger.error(f"Hava durumu tahmini alma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Hava durumu tahmini alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hava durumu tahmini alınamadı: {str(e)}")

@router.get("/hourly", response_model=List[ForecastItem])
async def get_hourly_forecast(
    location: str = Query(..., description="Konum adı (şehir, ilçe, vb.)"),
    units: str = Query("metric", description="Birim sistemi (metric, imperial, standard)"),
    hours: int = Query(24, description="Saat sayısı (maksimum 48)")
):
    """Saatlik hava durumu tahminini getirir.
    
    Args:
        location: Konum adı (şehir, ilçe, vb.)
        units: Birim sistemi (metric, imperial, standard)
        hours: Saat sayısı (maksimum 48)
        
    Returns:
        List[ForecastItem]: Saatlik hava durumu tahmini verileri
        
    Raises:
        HTTPException: Hava durumu tahmini alınamazsa
    """
    try:
        # Saat sayısını kontrol et
        if hours < 1 or hours > 48:
            raise ValueError("Saat sayısı 1-48 arasında olmalıdır")
            
        # Gün sayısını hesapla
        days = (hours + 23) // 24  # En az 1, en fazla 2 gün
        
        # Hava durumu tahminini al
        forecast_data = await weather_service.get_forecast(location, units, days)
        
        # Verileri formatla
        formatted_forecasts = weather_service.format_forecast(forecast_data, units)
        
        # Saat sayısına göre filtrele
        hourly_forecast = formatted_forecasts[:hours]
        
        return hourly_forecast
        
    except ValueError as e:
        logger.error(f"Saatlik hava durumu tahmini alma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Saatlik hava durumu tahmini alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Saatlik hava durumu tahmini alınamadı: {str(e)}")

@router.get("/daily", response_model=List[ForecastItem])
async def get_daily_forecast(
    location: str = Query(..., description="Konum adı (şehir, ilçe, vb.)"),
    units: str = Query("metric", description="Birim sistemi (metric, imperial, standard)"),
    days: int = Query(5, description="Gün sayısı (maksimum 5)")
):
    """Günlük hava durumu tahminini getirir.
    
    Args:
        location: Konum adı (şehir, ilçe, vb.)
        units: Birim sistemi (metric, imperial, standard)
        days: Gün sayısı (maksimum 5)
        
    Returns:
        List[ForecastItem]: Günlük hava durumu tahmini verileri
        
    Raises:
        HTTPException: Hava durumu tahmini alınamazsa
    """
    try:
        # Gün sayısını kontrol et
        if days < 1 or days > 5:
            raise ValueError("Gün sayısı 1-5 arasında olmalıdır")
            
        # Hava durumu tahminini al
        forecast_data = await weather_service.get_forecast(location, units, days)
        
        # Verileri formatla
        formatted_forecasts = weather_service.format_forecast(forecast_data, units)
        
        # Günlük tahminleri oluştur (her gün için öğle vakti)
        daily_forecasts = []
        current_date = None
        
        for forecast in formatted_forecasts:
            date = forecast["date"]
            time = forecast["time"]
            
            # Yeni bir gün ise ve öğle vakti ise (12:00-15:00 arası)
            if date != current_date and "12:" in time or "13:" in time or "14:" in time:
                daily_forecasts.append(forecast)
                current_date = date
                
                # Gün sayısına ulaşıldıysa döngüden çık
                if len(daily_forecasts) >= days:
                    break
        
        return daily_forecasts
        
    except ValueError as e:
        logger.error(f"Günlük hava durumu tahmini alma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Günlük hava durumu tahmini alma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Günlük hava durumu tahmini alınamadı: {str(e)}")
