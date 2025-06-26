from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    chroma_path: str = "chroma"
    model_name: str = "deepseek-r1:8b"
    temperature: float = 0.3
    top_k: int = 3
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'