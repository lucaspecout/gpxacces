from celery import Celery
from .config import settings
celery=Celery("gpxaccess",broker=settings.redis_url,backend=settings.redis_url)

