from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Teacher-Manage 板書備課與難度評分系統"
    SECRET_KEY: str = "teacher-manage-dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_URL: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'teacher_manage.db'}"
    GENERATED_PDF_DIR: Path = Path(__file__).resolve().parent.parent / "generated_pdfs"
    CHROME_EXECUTABLE_PATH: str = "/usr/bin/google-chrome"


settings = Settings()
settings.GENERATED_PDF_DIR.mkdir(parents=True, exist_ok=True)
