from pydantic_settings import BaseSettings
from pathlib import Path

# 项目根目录（config/ 的父目录）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "SQL Editor Backend"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'sql_editor.db'}"
    
    # Kerberos
    KRB5_CONFIG_PATH: str = "/etc/krb5.conf"
    KEYTAB_DIR: Path = BASE_DIR / "data" / "keytabs"
    TICKET_CACHE_DIR: Path = BASE_DIR / "data" / "ticket_cache"
    
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
