from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "SQL Editor Backend"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Kerberos
    KRB5_CONFIG_PATH: str = "/etc/krb5.conf"
    KEYTAB_DIR: Path = Path("./keytabs")
    TICKET_CACHE_DIR: Path = Path("./ticket_cache")
    
    # SQL Execution
    MAX_EXECUTION_TIME: int = 3600  # seconds
    DEFAULT_FETCH_SIZE: int = 1000
    MAX_HISTORY_SIZE: int = 10000
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

# Create directories
settings.KEYTAB_DIR.mkdir(parents=True, exist_ok=True)
settings.TICKET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
