from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    APP_NAME: str = "SecureFlow AI"

    APP_VERSION: str = "0.1.0"

    ENV: str = "development"

    DATABASE_URL: str = (
        "postgresql://secureflow:secureflow@localhost:5432/secureflow"
    )

    JWT_SECRET: str = (
        "dev-secret-change-in-production"
    )

    REDIS_URL: str = (
        "redis://localhost:6379/0"
    )

    SIGNING_PRIVATE_KEY_PATH: str = (
        "./storage/signing/private_key.pem"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()