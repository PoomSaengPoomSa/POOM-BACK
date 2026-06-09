import os
from functools import lru_cache
from pathlib import Path
from typing import List  # 👈 List 타입을 위해 추가

from pydantic_settings import BaseSettings

# 백엔드 루트 폴더(app/의 부모 폴더)의 상위 폴더(최상위 poom 폴더)에 있는 .env 파일의 절대 경로를 계산합니다.
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """애플리케이션 환경 설정"""

    # CORS 관리 👈 추가된 부분
    # .env에 값이 없을 때를 대비해 기본값으로 로컬 주소를 넣어둡니다.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: str = ""
    DB_NAME: str = ""

    ES_HOST: str = ""
    LOGSTASH_HOST: str = ""
    POOM_AI_URL: str = "http://poom-ai:8001"
    
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

    # comma(,)로 구분된 문자열을 파이썬 리스트로 변환
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {
        "env_file": str(ENV_PATH),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()