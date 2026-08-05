from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "GPX Accès Secours"
    max_upload_mb: int = 10
    segment_length_m: float = 30
    overpass_urls: str = "https://overpass-api.de/api/interpreter,https://overpass.kumi.systems/api/interpreter,https://overpass.nchc.org.tw/api/interpreter"
    overpass_timeout_seconds: float = 25
    redis_url: str = "redis://redis:6379/0"

settings = Settings()
