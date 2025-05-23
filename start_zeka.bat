@echo off
echo ZEKA - Kisisellestirilmis Coklu Ajanli Yapay Zeka Asistani
echo Baslatiliyor...
echo.

REM Gerekli dizinlerin var olduğundan emin ol
if not exist "data" mkdir data
if not exist "data\profiles" mkdir data\profiles
if not exist "data\memory" mkdir data\memory
if not exist "data\vector_db" mkdir data\vector_db
if not exist "logs" mkdir logs

REM Ortam değişkenlerini kontrol et
if not defined OPENROUTER_API_KEY (
    echo UYARI: OPENROUTER_API_KEY ortam degiskeni tanimlanmamis!
    echo OpenRouter API anahtarini ayarlayin veya config.py dosyasini duzenleyin.
    echo.
)

if not defined OPENWEATHERMAP_API_KEY (
    echo UYARI: OPENWEATHERMAP_API_KEY ortam degiskeni tanimlanmamis!
    echo OpenWeatherMap API anahtarini ayarlayin veya config.py dosyasini duzenleyin.
    echo.
)

REM Backend'i başlat
echo Backend baslatiliyor...
start cmd /k "cd src && python -m api.main"

REM Backend'in başlaması için biraz bekle
echo Backend baslatiliyor, lutfen bekleyin...
timeout /t 5 /nobreak > nul

REM Frontend'i başlat
echo Frontend baslatiliyor...
start cmd /k "cd src\ui\frontend && npm run dev"

echo.
echo ZEKA basariyla baslatildi!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Kapatmak icin her iki komut penceresini de kapatin.
echo.

REM Tarayıcıyı aç
timeout /t 2 /nobreak > nul
start http://localhost:3000

exit /b 0
