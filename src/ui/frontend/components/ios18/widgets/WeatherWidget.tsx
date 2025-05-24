"use client"

import { useState, useEffect } from "react"
import { 
  Cloud, 
  CloudRain, 
  Sun, 
  Thermometer, 
  Wind, 
  Droplets,
  CloudLightning,
  CloudSnow,
  CloudFog,
  Umbrella
} from "lucide-react"
import { cn } from "@/lib/utils"
import { getCurrentWeather, getHourlyForecast, type WeatherResponse, type ForecastItem } from "@/lib/api"

interface WeatherWidgetProps {
  className?: string
  size?: "small" | "large"
  location?: string
}

export default function WeatherWidget({
  className,
  size = "large",
  location = "İstanbul"
}: WeatherWidgetProps) {
  const [weatherInfo, setWeatherInfo] = useState<WeatherResponse | null>(null)
  const [forecastInfo, setForecastInfo] = useState<ForecastItem[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load weather data
  useEffect(() => {
    const loadWeatherData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Get current weather
        const weatherData = await getCurrentWeather(location)
        setWeatherInfo(weatherData)

        // Get hourly forecast (next 24 hours)
        const hourlyData = await getHourlyForecast(location, 'metric', 24)
        setForecastInfo(hourlyData)

      } catch (err) {
        console.error("Weather loading error:", err)
        setError("Hava durumu yüklenemedi")
      } finally {
        setIsLoading(false)
      }
    }

    loadWeatherData()
  }, [location])

  // Get weather icon
  const getWeatherIcon = (weatherId: number, iconCode: string, size: number = 24) => {
    const isNight = iconCode.endsWith('n')

    if (weatherId >= 200 && weatherId < 300) {
      return <CloudLightning size={size} className="text-yellow-300" />
    } else if (weatherId >= 300 && weatherId < 400) {
      return <CloudRain size={size} className="text-blue-300" />
    } else if (weatherId >= 500 && weatherId < 600) {
      return <Umbrella size={size} className="text-blue-400" />
    } else if (weatherId >= 600 && weatherId < 700) {
      return <CloudSnow size={size} className="text-blue-100" />
    } else if (weatherId >= 700 && weatherId < 800) {
      return <CloudFog size={size} className="text-gray-300" />
    } else if (weatherId === 800) {
      return <Sun size={size} className="text-yellow-300" />
    } else if (weatherId > 800) {
      return <Cloud size={size} className="text-gray-300" />
    }

    return <Sun size={size} className="text-yellow-300" />
  }

  // Format time
  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr)
    return date.getHours() + ":00"
  }

  const today = new Date()
  const formattedDate = today.toLocaleDateString('tr-TR', { 
    weekday: 'long', 
    day: 'numeric', 
    month: 'long' 
  })

  if (size === "small") {
    return (
      <div className={cn("relative", className)}>
        <div className="w-full h-full flex flex-col items-center justify-center space-y-2">
          <div className="w-8 h-8 flex items-center justify-center">
            {isLoading ? (
              <div className="w-6 h-6 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
            ) : weatherInfo ? (
              getWeatherIcon(weatherInfo.weather_id, weatherInfo.weather_icon, 20)
            ) : (
              <Sun size={20} className="text-yellow-300" />
            )}
          </div>
          <div className="text-center">
            <div className="ios-text-primary text-lg font-semibold">
              {isLoading ? "--" : weatherInfo ? `${weatherInfo.temperature}°` : "24°"}
            </div>
            <div className="ios-text-secondary text-xs">
              {location}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading && !weatherInfo) {
    return (
      <div className={cn("space-y-3", className)}>
        <div className="flex items-center space-x-2">
          <Thermometer size={18} className="ios-text-secondary" />
          <span className="ios-text-primary text-sm font-medium">Hava Durumu</span>
        </div>
        <div className="flex justify-center items-center h-32">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (error && !weatherInfo) {
    return (
      <div className={cn("space-y-3", className)}>
        <div className="flex items-center space-x-2">
          <Thermometer size={18} className="ios-text-secondary" />
          <span className="ios-text-primary text-sm font-medium">Hava Durumu</span>
        </div>
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-red-400 text-xs text-center">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex items-center space-x-2">
        <Thermometer size={18} className="ios-text-secondary" />
        <span className="ios-text-primary text-sm font-medium">Hava Durumu</span>
      </div>

      {/* Current Weather */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/10">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="ios-text-primary font-medium text-base">
              {weatherInfo ? `${weatherInfo.location}, ${weatherInfo.country}` : location}
            </h3>
            <p className="ios-text-secondary text-xs">{formattedDate}</p>
          </div>
          <div className="flex items-center space-x-2">
            {weatherInfo && getWeatherIcon(weatherInfo.weather_id, weatherInfo.weather_icon, 32)}
            <span className="ios-text-primary text-2xl font-light">
              {weatherInfo ? `${weatherInfo.temperature}${weatherInfo.temp_unit}` : "24°C"}
            </span>
          </div>
        </div>

        {/* Weather Details */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="flex items-center space-x-1">
            <Thermometer size={12} className="ios-text-secondary" />
            <span className="ios-text-tertiary">Hissedilen:</span>
            <span className="ios-text-primary font-medium">
              {weatherInfo ? `${weatherInfo.feels_like}${weatherInfo.temp_unit}` : "23°C"}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <Wind size={12} className="ios-text-secondary" />
            <span className="ios-text-tertiary">Rüzgar:</span>
            <span className="ios-text-primary font-medium">
              {weatherInfo ? `${weatherInfo.wind_speed}${weatherInfo.wind_unit}` : "8km/h"}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <Droplets size={12} className="ios-text-secondary" />
            <span className="ios-text-tertiary">Nem:</span>
            <span className="ios-text-primary font-medium">
              {weatherInfo ? `${weatherInfo.humidity}%` : "65%"}
            </span>
          </div>
        </div>
      </div>

      {/* Hourly Forecast */}
      <div className="space-y-2">
        <h4 className="ios-text-primary text-sm font-medium">Saatlik Tahmin</h4>
        <div className="grid grid-cols-4 gap-2">
          {forecastInfo ? (
            forecastInfo.slice(0, 4).map((item, i) => (
              <div 
                key={i} 
                className="p-2 rounded-lg bg-white/5 border border-white/10 text-center hover:bg-white/10 ios-transition"
              >
                <div className="ios-text-tertiary text-xs mb-1">
                  {i === 0 ? "Şimdi" : formatTime(item.datetime)}
                </div>
                <div className="flex justify-center mb-1">
                  {getWeatherIcon(item.weather_id, item.weather_icon, 16)}
                </div>
                <div className="ios-text-primary text-xs font-medium">
                  {item.temperature}{item.temp_unit}
                </div>
              </div>
            ))
          ) : (
            // Default forecast data
            Array.from({ length: 4 }, (_, i) => (
              <div 
                key={i} 
                className="p-2 rounded-lg bg-white/5 border border-white/10 text-center"
              >
                <div className="ios-text-tertiary text-xs mb-1">
                  {i === 0 ? "Şimdi" : `${14 + i * 2}:00`}
                </div>
                <div className="flex justify-center mb-1">
                  <Sun size={16} className="text-yellow-300" />
                </div>
                <div className="ios-text-primary text-xs font-medium">
                  {24 + i}°
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
