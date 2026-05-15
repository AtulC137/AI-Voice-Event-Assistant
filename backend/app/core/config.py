'''
Why We Need This Instead of:

os.getenv(...)

everywhere,
we centralize all config in one place. Production standard.

What Happens Here BaseSettings Automatically loads variables from .env

settings = Settings()

Creates global config object. Later we can do:

        from app.core.config import settings
        print(settings.DATABASE_URL)

'''



from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    DATABASE_URL: str

    SARVAM_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()