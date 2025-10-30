from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class InitialQueryRequest(BaseModel):
    """Первичный запрос пользователя"""
    user_message: str = Field(..., min_length=10, max_length=500)
    user_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_message": "Каково это - быть frontend-разработчиком в стартапе?",
                "user_id": 123
            }
        }


class ClarificationResponse(BaseModel):
    """Уточняющий вопрос"""
    session_id: int
    question: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "question": "Больше креатива или рутины?"
            }
        }


class FinalAnswerRequest(BaseModel):
    """Ответ на уточняющий вопрос"""
    session_id: int
    answer: str = Field(..., min_length=1, max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "answer": "Больше креатива"
            }
        }


class DayScheduleItem(BaseModel):
    """Элемент расписания"""
    time: str
    activity: str

    @field_validator('time')
    @classmethod
    def normalize_time(cls, v: str) -> str:
        """Нормализация времени к формату HH:MM"""
        v = v.strip()

        # Если время уже в правильном формате
        if len(v) == 5 and v[2] == ':':
            return v

        # Если формат H:MM (например 9:00)
        if len(v) == 4 and v[1] == ':':
            return f"0{v}"

        # Если формат HH:M (например 10:5)
        if len(v) == 4 and v[2] == ':':
            return f"{v[:3]}0{v[3]}"

        # Если формат H:M (например 9:5)
        if len(v) == 3 and v[1] == ':':
            return f"0{v[0]}:0{v[2]}"

        # Если вообще не похоже на время, возвращаем как есть
        # (пусть дальше упадет с ошибкой, если что)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "time": "10:00",
                "activity": "Daily-митинг с командой"
            }
        }


class CareerProfileResponse(BaseModel):
    """Финальный профиль карьеры"""
    session_id: int
    position_title: str
    sounds: List[str]
    career_growth: str
    balance_score: str
    benefit: str
    typical_day: List[DayScheduleItem]
    tech_stack: List[str]
    visual: List[str]
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "position_title": "Frontend-разработчик в стартапе",
                "sounds": [
                    "Текстурные клики клавиатуры",
                    "Обрывки диалогов из Zoom",
                    "Уведомления из GitHub"
                ],
                "career_growth": "Junior -> Senior -> Tech Lead",
                "balance_score": "50/50",
                "benefit": "Твой код влияет на продукт",
                "typical_day": [
                    {"time": "10:00", "activity": "Daily-митинг"},
                    {"time": "11:30", "activity": "Вёрстка компонента"}
                ],
                "tech_stack": ["JavaScript", "React", "Figma"],
                "visual": ["Скриншоты Figma", "VS Code с кодом"],
                "created_at": "2024-01-01T12:00:00"
            }
        }
