from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY:str
    ANTHROPIC_API_KEY:str
    ANTHROPIC_MODEL:str = "claude-sonnet-4-6"
    ELEVEN_LABS_API_KEY:str
    ELEVEN_LABS_MODEL_ID:str
    ELEVEN_LABS_VOICE_ID:str
    OCR_MODEL:str
    GROQ_MODEL:str
    ZOOM_CLIENT_ID:str
    ZOOM_CLIENT_SECRET:str
    ZOOM_ACCOUNT_ID:str
    GOOGLE_PROJECT_ID:str
    GOOGLE_PRIVATE_KEY_ID:str
    GOOGLE_PRIVATE_KEY:str
    GOOGLE_CLIENT_EMAIL:str
    GOOGLE_CLIENT_ID:str
    GOOGLE_TOKEN_URI:str
    GOOGLE_CALENDAR_ID:str
    GOOGLE_CALENDAR_OWNER_EMAIL:str
    DATABASE_URL:str
    LANGGRAPH_CHECKPOINT_DB_URL:str
    SQL_ECHO: bool = False
    OPENAI_API_KEY:str
    CHROMA_HOST:str
    CHROMA_PORT:int
    AGENT_TIMEZONE:str = "Asia/Karachi"
    REDIS_PORT:str
    REDIS_HOST:str

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    CHROMA_HOST:str
    CHROMA_PORT:int
    AGENT_TIMEZONE:str = "Asia/Karachi"
    REDIS_PORT:str
    REDIS_HOST:str

    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    WHATSAPP_VERIFY_TOKEN:str = "my_custom_verify_token"
    WHATSAPP_TOKEN:str = ""
    WHATSAPP_PHONE_ID:str = ""
    JWT_KEY:str = "riley-estate-secret-key-change-in-production"
    JWT_ALGORITHM:str = "HS256"

    model_config = SettingsConfigDict(
        env_file="../.env", 
        extra="ignore"
    )

Config = Settings()
