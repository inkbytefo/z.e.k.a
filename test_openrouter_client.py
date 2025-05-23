#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenRouter Client Test Betiği
Bu betik, src/core/openrouter_client.py modülünü doğrudan test eder.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Çevre değişkenlerini yükle
load_dotenv()

# src dizinini Python yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# OpenRouterClient'ı doğrudan içe aktar
from src.core.openrouter_client import OpenRouterClient

async def test_openrouter():
    """OpenRouter istemcisini test eder."""
    try:
        print("OpenRouter API testi başlatılıyor...")

        # İstemciyi başlat
        client = OpenRouterClient()

        # Metin üret
        print("\nMetin üretiliyor...")
        response = await client.generate_text(
            prompt="Yapay zeka nedir ve günlük hayatta nasıl kullanılır?",
            max_tokens=500,
            temperature=0.7,
            system_prompt="Türkçe yanıt ver ve örnekler kullan."
        )

        print(f"\nYanıt ({response['model']}):")
        print(response["content"])

        # Kullanım bilgilerini göster
        if "usage" in response:
            print(f"\nToken kullanımı: {response['usage']['total_tokens']} token")
            print(f"Yanıt süresi: {response['response_time']:.2f} saniye")

        # Streaming testi
        print("\nStreaming testi yapılıyor...")
        print("Yanıt parçaları:")
        full_text = ""
        async for chunk in client.generate_stream(
            prompt="Yapay zeka teknolojisinin geleceği nasıl olacak?",
            max_tokens=300,
            temperature=0.7,
            system_prompt="Türkçe yanıt ver ve kısa tut."
        ):
            if "content" in chunk and chunk["content"]:
                print(chunk["content"], end="", flush=True)
                full_text += chunk["content"]
            
            if "is_last_chunk" in chunk and chunk["is_last_chunk"]:
                print("\n\nStreaming tamamlandı.")
                print(f"Toplam karakter: {len(full_text)}")
                print(f"Yanıt süresi: {chunk['response_time']:.2f} saniye")

        # Metrikleri göster
        metrics = client.get_metrics()
        print("\nAPI metrikleri:")
        print(f"  Toplam istek sayısı: {metrics['total_requests']}")
        print(f"  Başarılı istek sayısı: {metrics['successful_requests']}")
        print(f"  Başarısız istek sayısı: {metrics['failed_requests']}")
        print(f"  Toplam token sayısı: {metrics['total_tokens']}")
        print(f"  Ortalama yanıt süresi: {metrics['average_response_time']:.2f} saniye")

        print("\nOpenRouter API testi başarıyla tamamlandı")
    except Exception as e:
        print(f"Test sırasında hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test fonksiyonunu çalıştır
    asyncio.run(test_openrouter())
