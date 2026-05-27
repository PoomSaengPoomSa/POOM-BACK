import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# 백엔드 루트 폴더(app/의 부모 폴더)에 있는 .env 파일의 절대 경로를 계산합니다.
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """애플리케이션 환경 설정"""

    # Database
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: str = ""
    DB_NAME: str = ""

    ES_HOST: str = ""
    
    # External API Keys
    ECOS_API_KEY: str = ""
    FRED_API_KEY: str = ""
    REB_API_KEY: str = ""

    openai_api_key: str | None = None

    langchain_tracing_v2: str | None = None
    langchain_endpoint: str | None = None
    langchain_api_key: str | None = None
    langchain_project: str | None = None

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {
        "env_file": str(ENV_PATH),
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
