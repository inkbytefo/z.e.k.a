"use client"

import type React from "react"

import { useState, useEffect } from "react"
import {
  CalendarIcon, Cloud, CloudRain, Sun, CheckSquare, Calendar,
  PlusCircle, X, ChevronDown, ChevronUp, Thermometer, Wind, Droplets,
  Mic, Cpu, Database, CloudFog, CloudLightning, CloudSnow, Umbrella,
  Laptop, Server
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import ModelSelector from "@/components/model-selector"
import EmbeddingModelSelector from "@/components/embedding-model-selector"
import DesktopController from "@/components/desktop-controller"
import { getCurrentWeather, getHourlyForecast, type WeatherResponse, type ForecastItem } from "@/lib/api"
import WidgetContainer, { WidgetDefinition } from "./widget-container"
import MCPServerManager from "./mcp-server-manager"
import APIKeyManager from "./api-key-manager"

export default function Widgets({ onModelChange }: { onModelChange?: (model: string) => void }) {
  const [weatherData, setWeatherData] = useState({
    location: "İstanbul",
    temperature: 24,
    condition: "sunny",
    feels_like: 23,
    humidity: 65,
    wind_speed: 8,
    forecast: [
      { time: "Now", icon: <Sun size={16} />, temp: "24°", color: "text-yellow-300" },
      { time: "2PM", icon: <Sun size={16} />, temp: "26°", color: "text-yellow-300" },
      { time: "4PM", icon: <CloudRain size={16} />, temp: "22°", color: "text-blue-300" },
      { time: "6PM", icon: <Cloud size={16} />, temp: "20°", color: "text-gray-300" },
    ]
  })
  const [tasks, setTasks] = useState([
    { id: 1, task: "Project meeting", time: "10:00 AM", completed: true, color: "bg-green-500" },
    { id: 2, task: "Review code PR", time: "1:30 PM", completed: false, color: "bg-orange-500" },
    { id: 3, task: "Update documentation", time: "3:00 PM", completed: false, color: "bg-cyan-500" },
  ])

  // Toggle task completion
  const toggleTaskCompletion = (id: number) => {
    setTasks(tasks.map(task =>
      task.id === id ? { ...task, completed: !task.completed } : task
    ))
  }

  // Available widgets for the container
  const [availableWidgets, setAvailableWidgets] = useState<WidgetDefinition[]>([
    {
      id: "ai-model",
      type: "model-selector",
      title: "AI Model",
      isMaximizable: true,
      isRemovable: false,
      component: (
        <div className="space-y-2">
          <ModelSelector onModelChange={onModelChange} className="w-full" />
          <div className="text-xs text-slate-400">
            Özel model eklemek için + butonuna tıklayın
          </div>
        </div>
      )
    },
    {
      id: "api-keys",
      type: "custom",
      title: "API Anahtarları",
      isMaximizable: true,
      isRemovable: true,
      component: (
        <div className="space-y-2">
          <APIKeyManager className="w-full" />
          <div className="text-xs text-slate-400">
            AI sağlayıcıları için API anahtarlarını yönetin
          </div>
        </div>
      )
    },
    {
      id: "embedding-model",
      type: "embedding-selector",
      title: "Embedding Model",
      isMaximizable: true,
      isRemovable: true,
      component: (
        <div className="space-y-2">
          <EmbeddingModelSelector className="w-full" />
          <div className="text-xs text-slate-400">
            Vektör veritabanı için kullanılan embedding modelini değiştirin
          </div>
        </div>
      )
    },
    {
      id: "weather-widget",
      type: "weather",
      title: "Weather",
      isMaximizable: true,
      isRemovable: true,
      component: <WeatherWidget data={weatherData} />
    },
    {
      id: "tasks-widget",
      type: "tasks",
      title: "Tasks",
      isMaximizable: true,
      isRemovable: true,
      component: <TasksWidget tasks={tasks} onToggleTask={toggleTaskCompletion} />
    },
    {
      id: "calendar-widget",
      type: "calendar",
      title: "Calendar",
      isMaximizable: true,
      isRemovable: true,
      component: <CalendarWidget />
    },
    {
      id: "voice-recognition",
      type: "voice-recognition",
      title: "Voice Recognition",
      isMaximizable: false,
      isRemovable: true,
      component: (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-slate-400 text-sm">Web Speech API</div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-emerald-400 rounded-full mr-1"></div>
              <span className="text-xs text-emerald-400">Active</span>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Konuşma arayüzünde mikrofon simgesine tıklayarak ses tanımayı kullanabilirsiniz
          </div>
          <div className="mt-2 flex space-x-1">
            <div className="w-1 h-2 bg-sky-800/50 rounded-full"></div>
            <div className="w-1 h-3 bg-sky-800/50 rounded-full"></div>
            <div className="w-1 h-1 bg-sky-800/50 rounded-full"></div>
            <div className="w-1 h-2 bg-sky-800/50 rounded-full"></div>
            <div className="w-1 h-4 bg-sky-800/50 rounded-full"></div>
          </div>
        </div>
      )
    },
    {
      id: "mcp-server",
      type: "mcp-server",
      title: "MCP Servers",
      isMaximizable: true,
      isRemovable: true,
      component: <MCPServerManager />
    },
    {
      id: "desktop-controller",
      type: "custom",
      title: "Desktop Controller",
      isMaximizable: true,
      isRemovable: true,
      component: <DesktopController />
    }
  ])

  // Handle adding a new widget
  const handleAddWidget = () => {
    // In a real implementation, this would show a modal to select widget type
    alert("Bu özellik henüz geliştirme aşamasındadır. Yakında kullanıma sunulacaktır.")
  }

  // Handle removing a widget
  const handleRemoveWidget = (id: string) => {
    setAvailableWidgets(availableWidgets.filter(w => w.id !== id))
  }

  // Handle reordering widgets
  const handleReorderWidgets = (widgets: WidgetDefinition[]) => {
    setAvailableWidgets(widgets)
  }

  return (
    <WidgetContainer
      widgets={availableWidgets}
      onAddWidget={handleAddWidget}
      onRemoveWidget={handleRemoveWidget}
      onReorderWidgets={handleReorderWidgets}
    />
  )
}

function TabButton({ active, icon, onClick }: { active: boolean; icon: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "p-2 rounded-md transition-all duration-300",
        active ? "bg-sky-900/50 text-sky-300 border border-sky-700/30" : "text-slate-400 hover:text-sky-400 hover:bg-sky-900/20",
      )}
    >
      {icon}
    </button>
  )
}

interface WeatherData {
  location: string
  temperature: number
  condition: string
  feels_like: number
  humidity: number
  wind_speed: number
  forecast: {
    time: string
    icon: React.ReactNode
    temp: string
    color: string
  }[]
}

function WeatherWidget({ data }: { data: WeatherData }) {
  const [weatherInfo, setWeatherInfo] = useState<WeatherResponse | null>(null)
  const [forecastInfo, setForecastInfo] = useState<ForecastItem[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [location, setLocation] = useState(data.location)

  // Hava durumu verilerini yükle
  useEffect(() => {
    const loadWeatherData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Mevcut hava durumunu al
        const weatherData = await getCurrentWeather(location)
        setWeatherInfo(weatherData)

        // Saatlik tahminleri al (sonraki 24 saat)
        const hourlyData = await getHourlyForecast(location, 'metric', 24)
        setForecastInfo(hourlyData)

      } catch (err) {
        console.error("Hava durumu yüklenirken hata:", err)
        setError("Hava durumu yüklenemedi")
      } finally {
        setIsLoading(false)
      }
    }

    loadWeatherData()
  }, [location])

  // Hava durumu ikonunu seç
  const getWeatherIcon = (weatherId: number, iconCode: string) => {
    // Gece mi kontrol et (n ile biten ikonlar gece)
    const isNight = iconCode.endsWith('n')

    // Hava durumu koduna göre ikon seç
    // https://openweathermap.org/weather-conditions
    if (weatherId >= 200 && weatherId < 300) {
      return <CloudLightning size={24} className="text-yellow-300" />
    } else if (weatherId >= 300 && weatherId < 400) {
      return <CloudRain size={24} className="text-blue-300" />
    } else if (weatherId >= 500 && weatherId < 600) {
      return <Umbrella size={24} className="text-blue-400" />
    } else if (weatherId >= 600 && weatherId < 700) {
      return <CloudSnow size={24} className="text-blue-100" />
    } else if (weatherId >= 700 && weatherId < 800) {
      return <CloudFog size={24} className="text-gray-300" />
    } else if (weatherId === 800) {
      return <Sun size={24} className="text-yellow-300" />
    } else if (weatherId > 800) {
      return <Cloud size={24} className="text-gray-300" />
    }

    // Varsayılan ikon
    return <Sun size={24} className="text-yellow-300" />
  }

  // Tahmin ikonunu seç
  const getForecastIcon = (weatherId: number, iconCode: string) => {
    // Gece mi kontrol et (n ile biten ikonlar gece)
    const isNight = iconCode.endsWith('n')

    // Hava durumu koduna göre ikon ve renk seç
    if (weatherId >= 200 && weatherId < 300) {
      return {
        icon: <CloudLightning size={16} />,
        color: "text-yellow-300"
      }
    } else if (weatherId >= 300 && weatherId < 400) {
      return {
        icon: <CloudRain size={16} />,
        color: "text-blue-300"
      }
    } else if (weatherId >= 500 && weatherId < 600) {
      return {
        icon: <Umbrella size={16} />,
        color: "text-blue-400"
      }
    } else if (weatherId >= 600 && weatherId < 700) {
      return {
        icon: <CloudSnow size={16} />,
        color: "text-blue-100"
      }
    } else if (weatherId >= 700 && weatherId < 800) {
      return {
        icon: <CloudFog size={16} />,
        color: "text-gray-300"
      }
    } else if (weatherId === 800) {
      return {
        icon: <Sun size={16} />,
        color: "text-yellow-300"
      }
    } else if (weatherId > 800) {
      return {
        icon: <Cloud size={16} />,
        color: "text-gray-300"
      }
    }

    // Varsayılan ikon
    return {
      icon: <Sun size={16} />,
      color: "text-yellow-300"
    }
  }

  // Saati formatla
  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr)
    return date.getHours() + ":00"
  }

  const today = new Date()
  const formattedDate = today.toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' })

  // Yükleniyor durumu
  if (isLoading && !weatherInfo) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-500"></div>
      </div>
    )
  }

  // Hata durumu
  if (error && !weatherInfo) {
    return (
      <div className="text-center py-4">
        <p className="text-rose-400">{error}</p>
        <button
          onClick={() => setLocation(data.location)}
          className="mt-2 px-3 py-1.5 bg-sky-900/30 hover:bg-sky-800/40 rounded-md text-xs text-sky-300 transition-colors border border-sky-700/30"
        >
          Tekrar Dene
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-white font-medium">
            {weatherInfo ? `${weatherInfo.location}, ${weatherInfo.country}` : data.location}
          </h3>
          <p className="text-slate-400 text-xs">{formattedDate}</p>
        </div>
        <div className="text-amber-300 flex items-center">
          {weatherInfo ?
            getWeatherIcon(weatherInfo.weather_id, weatherInfo.weather_icon) :
            <Sun size={24} className="mr-2" />
          }
          <span className="text-xl ml-2">
            {weatherInfo ? `${weatherInfo.temperature}${weatherInfo.temp_unit}` : `${data.temperature}°C`}
          </span>
        </div>
      </div>

      <div className="mt-3 flex items-center space-x-4 text-xs text-slate-300">
        <div className="flex items-center">
          <Thermometer size={14} className="mr-1 text-sky-400" />
          <span>Hissedilen: {weatherInfo ? `${weatherInfo.feels_like}${weatherInfo.temp_unit}` : `${data.feels_like}°C`}</span>
        </div>
        <div className="flex items-center">
          <Wind size={14} className="mr-1 text-sky-400" />
          <span>Rüzgar: {weatherInfo ? `${weatherInfo.wind_speed}${weatherInfo.wind_unit}` : `${data.wind_speed}km/h`}</span>
        </div>
        <div className="flex items-center">
          <Droplets size={14} className="mr-1 text-sky-400" />
          <span>Nem: {weatherInfo ? `${weatherInfo.humidity}%` : `${data.humidity}%`}</span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-4 gap-2">
        {forecastInfo ? (
          // API'den gelen tahmin verileri
          forecastInfo.slice(0, 4).map((item, i) => {
            const iconInfo = getForecastIcon(item.weather_id, item.weather_icon)
            return (
              <div key={i} className="flex flex-col items-center p-2 rounded-md hover:bg-sky-900/10 transition-colors border border-sky-900/10">
                <span className="text-xs text-slate-400">{i === 0 ? "Şimdi" : formatTime(item.datetime)}</span>
                <div className={`my-1 ${iconInfo.color}`}>{iconInfo.icon}</div>
                <span className="text-xs text-white">{item.temperature}{item.temp_unit}</span>
              </div>
            )
          })
        ) : (
          // Varsayılan tahmin verileri
          data.forecast.map((item, i) => (
            <div key={i} className="flex flex-col items-center p-2 rounded-md hover:bg-sky-900/10 transition-colors border border-sky-900/10">
              <span className="text-xs text-slate-400">{item.time}</span>
              <div className={`my-1 ${item.color}`}>{item.icon}</div>
              <span className="text-xs text-white">{item.temp}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

interface Task {
  id: number
  task: string
  time: string
  completed: boolean
  color: string
}

interface TasksWidgetProps {
  tasks: Task[]
  onToggleTask: (id: number) => void
}

function TasksWidget({ tasks, onToggleTask }: TasksWidgetProps) {
  const [newTask, setNewTask] = useState("")
  const [showInput, setShowInput] = useState(false)

  return (
    <div className="space-y-2">
      <h3 className="text-white font-medium">Today's Tasks</h3>

      {tasks.map((item) => (
        <div key={item.id} className="flex items-center justify-between p-2.5 rounded-md hover:bg-sky-900/10 transition-colors border border-sky-900/10">
          <div className="flex items-center">
            <button
              onClick={() => onToggleTask(item.id)}
              className={`w-3 h-3 rounded-full mr-2 ${item.color} cursor-pointer hover:opacity-80 transition-opacity`}
            ></button>
            <span className={cn(item.completed ? "text-slate-500 line-through" : "text-white")}>{item.task}</span>
          </div>
          <span className="text-xs text-slate-400">{item.time}</span>
        </div>
      ))}

      {showInput ? (
        <div className="flex items-center mt-2">
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            placeholder="New task..."
            className="flex-1 bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-1.5 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
            autoFocus
          />
          <button
            onClick={() => setShowInput(false)}
            className="ml-2 text-slate-400 hover:text-rose-400 transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowInput(true)}
          className="text-xs text-sky-400 mt-2 hover:text-sky-300 transition-colors flex items-center"
        >
          <PlusCircle size={12} className="mr-1" /> Add new task
        </button>
      )}
    </div>
  )
}

function CalendarWidget() {
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-white font-medium">May 2025</h3>
        <div className="flex space-x-1">
          <button className="text-slate-400 hover:text-sky-400 p-1 transition-colors">◀</button>
          <button className="text-slate-400 hover:text-sky-400 p-1 transition-colors">▶</button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center text-xs">
        {["S", "M", "T", "W", "T", "F", "S"].map((day, i) => (
          <div key={i} className="text-slate-500">
            {day}
          </div>
        ))}

        {Array.from({ length: 31 }, (_, i) => i + 1).map((date) => (
          <div
            key={date}
            className={cn(
              "p-1 rounded-md transition-colors border",
              date === 22
                ? "bg-sky-500 text-white border-sky-600"
                : date === 15
                  ? "bg-amber-500/50 text-white border-amber-600/50"
                  : date === 8
                    ? "bg-emerald-500/50 text-white border-emerald-600/50"
                    : "hover:bg-sky-900/20 text-white border-transparent",
            )}
          >
            {date}
          </div>
        ))}
      </div>

      <div className="mt-2 text-xs text-slate-400">
        <div className="flex items-center">
          <CalendarIcon size={12} className="mr-1 text-sky-400" />
          <span>2 events today</span>
        </div>
      </div>
    </div>
  )
}
