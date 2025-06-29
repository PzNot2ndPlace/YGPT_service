from datetime import datetime
from pydantic import BaseModel, validator
from typing import List


class GenerateTextRequest(BaseModel):
    user_text: str
    current_time: str
    locations: List[str]

    @validator("current_time")
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
            return v
        except ValueError:
            raise ValueError("Некорректный формат времени. Используйте 'YYYY-MM-DD HH:MM'")
