#!/usr/bin/env python3
"""
Z.E.K.A OpenAI API Örnek Kullanımı

Bu dosya, Z.E.K.A projesinde OpenAI API'sinin nasıl kullanılacağını gösterir.
Farklı kullanım senaryoları ve örnekler içerir.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Proje kök dizinini ekle
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.openai_client import OpenAIClient, OpenAIAPIError

# Yapılandırma
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Loglama
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("openai_example")


async def basic_text_generation_example():
    """Temel metin üretme örneği"""
    print("\n=== Temel Metin Üretme Örneği ===")
    
    try:
        client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            default_model="gpt-4o-mini"
        )
        
        response = await client.generate_text(
            prompt="Yapay zeka teknolojisinin geleceği hakkında kısa bir değerlendirme yaz.",
            temperature=0.7,
            max_tokens=200,
            system_prompt="Sen teknoloji konularında uzman bir analistin. Objektif ve bilgilendirici yanıtlar veriyorsun."
        )
        
        print(f"Model: {response['model']}")
        print(f"Yanıt: {response['response']}")
        print(f"Token Kullanımı: {response['usage']}")
        
    except OpenAIAPIError as e:
        logger.error(f"OpenAI API hatası: {e}")
    except Exception as e:
        logger.error(f"Genel hata: {e}")


async def streaming_example():
    """Streaming yanıt örneği"""
    print("\n=== Streaming Yanıt Örneği ===")
    
    try:
        client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            default_model="gpt-4o-mini"
        )
        
        print("Streaming yanıt başlıyor...")
        print("Yanıt: ", end="", flush=True)
        
        async for chunk in client.generate_stream(
            prompt="Türkiye'nin en güzel 5 şehrini ve özelliklerini anlat.",
            temperature=0.8,
            max_tokens=500,
            system_prompt="Sen bir turizm rehberisin. Şehirler hakkında ilginç ve çekici bilgiler veriyorsun."
        ):
            if chunk.get("content"):
                print(chunk["content"], end="", flush=True)
        
        print("\n\nStreaming tamamlandı!")
        
    except OpenAIAPIError as e:
        logger.error(f"OpenAI API hatası: {e}")
    except Exception as e:
        logger.error(f"Genel hata: {e}")


async def chat_completion_example():
    """Sohbet tamamlama örneği"""
    print("\n=== Sohbet Tamamlama Örneği ===")
    
    try:
        client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            default_model="gpt-4o"
        )
        
        # Sohbet geçmişi
        messages = [
            {"role": "system", "content": "Sen yardımcı ve dostane bir AI asistanısın. Türkçe konuşuyorsun."},
            {"role": "user", "content": "Merhaba! Bugün nasılsın?"},
            {"role": "assistant", "content": "Merhaba! Ben bir AI olduğum için duygularım yok ama size yardım etmeye hazırım. Size nasıl yardımcı olabilirim?"},
            {"role": "user", "content": "Python programlama dili hakkında bilgi verebilir misin?"}
        ]
        
        response = await client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        print(f"Model: {response['model']}")
        print(f"Asistan Yanıtı: {response['response']}")
        print(f"Token Kullanımı: {response['usage']}")
        
    except OpenAIAPIError as e:
        logger.error(f"OpenAI API hatası: {e}")
    except Exception as e:
        logger.error(f"Genel hata: {e}")


async def model_management_example():
    """Model yönetimi örneği"""
    print("\n=== Model Yönetimi Örneği ===")
    
    try:
        client = OpenAIClient(api_key=OPENAI_API_KEY)
        
        # Kullanılabilir modelleri listele
        models = await client.list_available_models()
        print("Kullanılabilir Modeller:")
        for model in models:
            print(f"  - {model['id']}: {model['name']} ({model['provider']})")
            print(f"    Açıklama: {model['description']}")
            print(f"    Max Token: {model['max_tokens']}")
            print(f"    Streaming: {'Evet' if model['supports_streaming'] else 'Hayır'}")
            print()
        
        # Model bilgisi al
        model_info = client.get_model_info("gpt-4o-mini")
        if model_info:
            print(f"GPT-4o Mini Bilgileri: {model_info}")
        
        # Model desteği kontrol et
        is_supported = client.is_model_supported("gpt-4")
        print(f"GPT-4 destekleniyor mu? {'Evet' if is_supported else 'Hayır'}")
        
    except OpenAIAPIError as e:
        logger.error(f"OpenAI API hatası: {e}")
    except Exception as e:
        logger.error(f"Genel hata: {e}")


async def different_models_comparison():
    """Farklı modelleri karşılaştırma örneği"""
    print("\n=== Farklı Modeller Karşılaştırması ===")
    
    models_to_test = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o"]
    prompt = "Quantum bilgisayarların avantajlarını 3 maddede özetle."
    
    for model in models_to_test:
        try:
            client = OpenAIClient(
                api_key=OPENAI_API_KEY,
                default_model=model
            )
            
            print(f"\n--- {model} ---")
            response = await client.generate_text(
                prompt=prompt,
                temperature=0.5,
                max_tokens=150
            )
            
            print(f"Yanıt: {response['response']}")
            print(f"Token Kullanımı: {response['usage']['total_tokens']}")
            
        except OpenAIAPIError as e:
            logger.error(f"{model} için hata: {e}")
        except Exception as e:
            logger.error(f"{model} için genel hata: {e}")


async def error_handling_example():
    """Hata yönetimi örneği"""
    print("\n=== Hata Yönetimi Örneği ===")
    
    # Geçersiz API anahtarı ile test
    try:
        client = OpenAIClient(api_key="invalid-key")
        await client.generate_text("Test mesajı")
    except OpenAIAPIError as e:
        print(f"Beklenen API hatası yakalandı: {e}")
    
    # Desteklenmeyen model ile test
    try:
        client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            default_model="nonexistent-model"
        )
        print(f"İstemci varsayılan modeli: {client.default_model}")  # Otomatik düzeltme
    except Exception as e:
        print(f"Model hatası: {e}")


async def interactive_chat():
    """Etkileşimli sohbet örneği"""
    print("\n=== Etkileşimli Sohbet Örneği ===")
    print("Çıkmak için 'çıkış' yazın.")
    
    try:
        client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            default_model="gpt-4o-mini"
        )
        
        messages = [
            {"role": "system", "content": "Sen yardımcı bir AI asistanısın. Kısa ve öz yanıtlar veriyorsun."}
        ]
        
        while True:
            user_input = input("\nSiz: ").strip()
            if user_input.lower() in ['çıkış', 'exit', 'quit']:
                print("Sohbet sonlandırıldı!")
                break
            
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            response = await client.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            assistant_response = response['response']
            messages.append({"role": "assistant", "content": assistant_response})
            
            print(f"Asistan: {assistant_response}")
            
            # Sohbet geçmişini sınırla (son 10 mesaj)
            if len(messages) > 11:  # sistem mesajı + 10 mesaj
                messages = messages[:1] + messages[-10:]
    
    except KeyboardInterrupt:
        print("\nSohbet kullanıcı tarafından sonlandırıldı!")
    except Exception as e:
        logger.error(f"Sohbet hatası: {e}")


async def main():
    """Ana fonksiyon - tüm örnekleri çalıştırır"""
    print("Z.E.K.A OpenAI API Örnekleri")
    print("=" * 50)
    
    if not OPENAI_API_KEY:
        print("HATA: OPENAI_API_KEY çevre değişkeni ayarlanmamış!")
        print("Lütfen .env dosyasında OPENAI_API_KEY değişkenini ayarlayın.")
        return
    
    # Örnekleri çalıştır
    await basic_text_generation_example()
    await streaming_example()
    await chat_completion_example()
    await model_management_example()
    await different_models_comparison()
    await error_handling_example()
    
    # Etkileşimli sohbet (opsiyonel)
    response = input("\nEtkileşimli sohbet başlatmak ister misiniz? (e/h): ").strip().lower()
    if response in ['e', 'evet', 'y', 'yes']:
        await interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
