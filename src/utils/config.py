import os
import json
from dotenv import load_dotenv

def load_config():
    """
    Uygulama konfigürasyonunu yükle
    """
    # .env dosyasını yükle
    load_dotenv()
    
    # Varsayılan konfigürasyon
    config = {
        'app_name': 'AI Dil Öğretmeni',
        'version': '1.0.0',
        'supported_languages': ['en', 'de', 'fr', 'es'],
        'default_language': 'en',
        'speech_recognition': {
            'timeout': 5,
            'language': 'en-US'
        },
        'models': {
            'grammar': 'vennify/t5-base-grammar-correction',
            'conversation': 'facebook/blenderbot-400M-distill'
        },
        'database': {
            'path': 'progress.json'
        }
    }
    
    # Özel konfigürasyon dosyası varsa yükle
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
                config.update(custom_config)
        except Exception as e:
            print(f"Konfigürasyon yüklenirken hata: {str(e)}")
    
    return config

def save_config(config):
    """
    Konfigürasyonu kaydet
    """
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Konfigürasyon kaydedilirken hata: {str(e)}")

def get_env_var(key, default=None):
    """
    Çevresel değişkeni al
    """
    return os.getenv(key, default) 