import os
from celery import Celery
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env_path = BASE_DIR / '.env'

if env_path.exists():
    environ.Env.read_env(env_path)
    print("!!! ARQUIVO .ENV LIDO PELO CELERY !!!") # Log de prova
else:
    print("!!! AVISO DO CELERY: arquivo .env não encontrado !!!")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoDownloader.settings')
app = Celery('videoDownloader')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()