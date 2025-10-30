from pydantic import BaseModel, Field
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
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    activity: str

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
