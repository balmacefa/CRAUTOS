from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://crautos_user:crautos_pass@localhost:5432/crautos_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "crautos_db"
    DB_USER:  str = "crautos_user"
    DB_PASSWORD: str = "crautos_pass"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_WORKERS: int = 4
    PROJECT_NAME: str = "CRAutos Market Intelligence API"
    VERSION: str = "1.0.0"
    
    # Scraper
    SCRAPER_HEADLESS: bool = True
    SCRAPER_MAX_PAGES: int = 50
    SCRAPER_DELAY_SECONDS: int = 2
    SCRAPER_TIMEOUT: int = 30
    
    # CRAutos URLs
    CRAUTOS_BASE_URL: str = "https://crautos.com"
    CRAUTOS_SEARCH_URL: str = "https://crautos.com/autosusados/searchresults.cfm"
    CRAUTOS_USED_CARS_URL: str = "https://crautos.com/autosusados/"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/crautos.log"
    
    # Scheduler
    SCRAPER_SCHEDULE_HOUR: int = 2
    REPORT_SCHEDULE_HOUR: int = 8
    
    # Directories
    REPORTS_DIR: str = "reports"
    LOGS_DIR: str = "logs"
    DATA_DIR: str = "data"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()