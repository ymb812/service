from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class InitialQueryRequest(BaseModel):
    """Первичный запрос пользователя"""
    user_message: str = Field(..., min_length=5, max_length=500)
    user_id: Optional[int] = None


class ClarificationResponse(BaseModel):
    """Уточняющий вопрос"""
    session_id: int
    question: str
    stage: str  # profession_check, profession_details, profession_alternatives, vibe_question
    alternatives: Optional[List[str]] = None  # Если профессия нереальная


class FinalAnswerRequest(BaseModel):
    """Ответ на уточняющий вопрос"""
    session_id: int
    answer: str = Field(..., min_length=1, max_length=500)


class RealCaseExample(BaseModel):
    """Пример реальной задачи"""
    title: str
    description: str
    difficulty: str  # easy, medium, hard

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Оптимизация SQL запроса",
                "description": "Ускорить выборку из таблицы на 10М записей с 30 сек до 2 сек",
                "difficulty": "medium"
            }
        }


class ChatExample(BaseModel):
    """Пример диалога с коллегой в чате"""
    colleague: str = Field(..., description="Имя и роль коллеги")
    request: str = Field(..., description="Сообщение-запрос от коллеги")
    your_response: str = Field(..., description="Твой ответ")
    vibe: str = Field(..., description="Эмоциональный окрас ситуации")

    class Config:
        json_schema_extra = {
            "example": {
                "colleague": "Саша (Backend-разработчик)",
                "request": "Слушай, у меня API возвращает 500 на запрос профиля. Можешь глянуть фронт?",
                "your_response": "Щас чекну. А логи бэка смотрел? Может там ошибка сериализации?",
                "vibe": "Обычный дебаг в паре — так работает команда"
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
    typical_day: str
    real_cases: List[RealCaseExample]
    tech_stack: List[str]
    visual: List[str]
    chat_examples: List[ChatExample]
    day_images: List[str]
    audio_files: list[str]
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": 1,
                "position_title": "Backend-разработчик в финтехе",
                "sounds": ["Звук клавиатуры", "Пинги из Slack", "Алерты мониторинга"],
                "career_growth": "Junior → Middle → Senior → Team Lead",
                "balance_score": "60/40",
                "benefit": "Твой код обрабатывает миллионы транзакций",
                "typical_day": "Утро начинается с проверки алертов и дейли в 10:00...",
                "real_cases": [
                    {
                        "title": "Оптимизация платёжного API",
                        "description": "Снизить latency с 500ms до 100ms",
                        "difficulty": "hard"
                    }
                ],
                "tech_stack": ["Python", "PostgreSQL", "Redis"],
                "visual": ["open laptop with tasks", "work of analytics", "a lot of notifications"],
                "chat_examples": [
                    {
                        "colleague": "Лена (Product Manager)",
                        "request": "Можем сделать фичу до пятницы?",
                        "your_response": "Если без тестов — да. С тестами — нет шансов",
                        "vibe": "Вечное противостояние скорости и качества"
                    }
                ],
                "created_at": "2024-01-01T12:00:00"
            }
        }
