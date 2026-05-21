from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 환경 설정"""

    # Database
    DB_USER: str = "fisaai6"
    DB_PASSWORD: str = "Woorifisa!6"
    DB_HOST: str = "118.67.131.22"
    DB_PORT: str = "3306"
    DB_NAME: str = "poom"

    # External API Keys
    ECOS_API_KEY: str = ""
    FRED_API_KEY: str = ""
    REB_API_KEY: str = ""

    # JWT
    JWT_SECRET_KEY: str = "poom-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
