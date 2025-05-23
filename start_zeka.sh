#!/bin/bash

echo "ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı"
echo "Başlatılıyor..."
echo ""

# Gerekli dizinlerin var olduğundan emin ol
mkdir -p data/profiles
mkdir -p data/memory
mkdir -p data/vector_db
mkdir -p logs

# Ortam değişkenlerini kontrol et
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "UYARI: OPENROUTER_API_KEY ortam değişkeni tanımlanmamış!"
    echo "OpenRouter API anahtarını ayarlayın veya config.py dosyasını düzenleyin."
    echo ""
fi

if [ -z "$OPENWEATHERMAP_API_KEY" ]; then
    echo "UYARI: OPENWEATHERMAP_API_KEY ortam değişkeni tanımlanmamış!"
    echo "OpenWeatherMap API anahtarını ayarlayın veya config.py dosyasını düzenleyin."
    echo ""
fi

# Backend'i başlat
echo "Backend başlatılıyor..."
cd src && python -m api.main &
BACKEND_PID=$!

# Backend'in başlaması için biraz bekle
echo "Backend başlatılıyor, lütfen bekleyin..."
sleep 5

# Frontend'i başlat
echo "Frontend başlatılıyor..."
cd ../src/ui/frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "ZEKA başarıyla başlatıldı!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Kapatmak için Ctrl+C tuşlarına basın."
echo ""

# Tarayıcıyı aç
sleep 2
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi

# Çıkış sinyallerini yakala
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Bekle
wait
