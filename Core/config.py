
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES:int=90
    ALGORITHM:str='HS256'
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET: str
    S3_REGION:str
    SIGNED_URL_EXPIRE_SECONDS: int = 600
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024
    LLM_API_KEY:str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
