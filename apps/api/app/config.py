from pydantic import BaseModel

class Settings(BaseModel):
    app_timezone: str = "Asia/Jakarta"
    sentiment_method: str = "rule_based"

settings = Settings()
