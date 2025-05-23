# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# OpenRouter Entegrasyon Örneği

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# OpenAI SDK ile OpenRouter kullanımı
from openai import OpenAI

# Alternatif olarak doğrudan HTTP istekleri ile kullanım
import requests

# Alternatif olarak python-open-router paketi ile kullanım
# Not: openrouter-client paketi PyPI'da mevcut olmadığı için python-open-router kullanıyoruz
try:
    from python_open_router import OpenRouter
    HAS_PYTHON_OPEN_ROUTER = True
except ImportError:
    HAS_PYTHON_OPEN_ROUTER = False

# Yapılandırma
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SITE_URL = "https://zeka.pro"  # Uygulamanızın URL'si
SITE_NAME = "Z.E.K.A AI Asistant"  # Uygulamanızın adı

# Loglama
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("openrouter_example")

def openai_sdk_example(prompt: str, model: str = "openai/gpt-4o") -> str:
    """OpenAI SDK kullanarak OpenRouter ile sohbet tamamlama.

    Args:
        prompt: Kullanıcı mesajı
        model: Kullanılacak model (varsayılan: openai/gpt-4o)

    Returns:
        str: Model yanıtı
    """
    try:
        # OpenAI istemcisini OpenRouter'a yönlendir
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        # Sohbet tamamlama isteği
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": SITE_URL,  # İsteğe bağlı. OpenRouter sıralamaları için site URL'si.
                "X-Title": SITE_NAME,  # İsteğe bağlı. OpenRouter sıralamaları için site adı.
            },
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Yanıtı döndür
        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenAI SDK ile OpenRouter hatası: {str(e)}")
        return f"Hata: {str(e)}"

def direct_api_example(prompt: str, model: str = "openai/gpt-4o") -> str:
    """Doğrudan API isteği kullanarak OpenRouter ile sohbet tamamlama.

    Args:
        prompt: Kullanıcı mesajı
        model: Kullanılacak model (varsayılan: openai/gpt-4o)

    Returns:
        str: Model yanıtı
    """
    try:
        # API isteği
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": SITE_URL,  # İsteğe bağlı. OpenRouter sıralamaları için site URL'si.
                "X-Title": SITE_NAME,  # İsteğe bağlı. OpenRouter sıralamaları için site adı.
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )

        # Yanıtı kontrol et
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            error_msg = f"API hatası: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        logger.error(f"Doğrudan API ile OpenRouter hatası: {str(e)}")
        return f"Hata: {str(e)}"

def python_open_router_example(prompt: str, model: str = "openai/gpt-4o") -> str:
    """python-open-router paketi kullanarak OpenRouter ile sohbet tamamlama.

    Args:
        prompt: Kullanıcı mesajı
        model: Kullanılacak model (varsayılan: openai/gpt-4o)

    Returns:
        str: Model yanıtı
    """
    if not HAS_PYTHON_OPEN_ROUTER:
        return "python-open-router paketi yüklü değil. 'pip install python-open-router' komutu ile yükleyebilirsiniz."

    try:
        # OpenRouter istemcisi oluştur
        client = OpenRouter(api_key=OPENROUTER_API_KEY)

        # Sohbet tamamlama isteği
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            extra_headers={  # python-open-router'da headers yerine extra_headers kullanılır
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME
            }
        )

        # Yanıtı döndür
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"python-open-router ile OpenRouter hatası: {str(e)}")
        return f"Hata: {str(e)}"

def get_available_models() -> List[Dict[str, Any]]:
    """OpenRouter'da kullanılabilir modelleri listeler.

    Returns:
        List[Dict[str, Any]]: Kullanılabilir modeller listesi
    """
    try:
        # API isteği
        response = requests.get(
            url="https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
        )

        # Yanıtı kontrol et
        if response.status_code == 200:
            return response.json()["data"]
        else:
            logger.error(f"Model listesi alınamadı: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Model listesi alınırken hata: {str(e)}")
        return []

if __name__ == "__main__":
    # API anahtarını kontrol et
    if not OPENROUTER_API_KEY:
        print("HATA: OPENROUTER_API_KEY çevre değişkeni ayarlanmamış.")
        print("Lütfen .env dosyasına OPENROUTER_API_KEY=your_api_key ekleyin.")
        exit(1)

    # Kullanıcı mesajı
    user_prompt = "Merhaba! Sen kimsin ve ne yapabilirsin?"

    print("\n=== OpenAI SDK ile OpenRouter Örneği ===")
    response = openai_sdk_example(user_prompt)
    print(f"Yanıt: {response}")

    print("\n=== Doğrudan API ile OpenRouter Örneği ===")
    response = direct_api_example(user_prompt)
    print(f"Yanıt: {response}")

    if HAS_PYTHON_OPEN_ROUTER:
        print("\n=== python-open-router ile OpenRouter Örneği ===")
        response = python_open_router_example(user_prompt)
        print(f"Yanıt: {response}")

    print("\n=== Kullanılabilir Modeller ===")
    models = get_available_models()
    for model in models[:5]:  # İlk 5 modeli göster
        print(f"- {model['id']}: {model.get('pricing', {}).get('prompt', '?')} / {model.get('pricing', {}).get('completion', '?')}")

    print(f"\nToplam {len(models)} model bulundu.")
