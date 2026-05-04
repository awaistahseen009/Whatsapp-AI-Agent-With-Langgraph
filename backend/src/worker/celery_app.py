from celery import Celery
from config import Config

celery_app = Celery(
    "riley_worker",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=["src.worker.tasks"]
)
