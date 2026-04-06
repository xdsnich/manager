"""
Фикс путей для Celery тасков.
Импортировать в начале каждого таска.
"""
import sys
import os

API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.dirname(API_DIR)

# api/ первый в path
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

# Убираем корень чтобы не подхватывался tg_manager/config.py
while ROOT_DIR in sys.path:
    sys.path.remove(ROOT_DIR)

# Сбрасываем кеш если загружен неправильный config
if 'config' in sys.modules:
    loaded = getattr(sys.modules['config'], '__file__', '')
    if 'api' not in loaded:
        del sys.modules['config']