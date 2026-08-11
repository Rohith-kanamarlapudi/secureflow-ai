from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "SecureFlow AI"
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"

    DATABASE_URL: str = (
        "postgresql://secureflow:secureflow@localhost:5432/secureflow"
    )

    class Config:
        env_file = ".env"


settings = Settings()