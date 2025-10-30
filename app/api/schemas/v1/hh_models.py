from pydantic import BaseModel, Field
from datetime import datetime


class ProfessionalRole(BaseModel):
    """Профессиональная роль"""
    id: str
    name: str

    class Config:
        extra = "ignore"


class Specialization(BaseModel):
    """Специализация"""
    id: str
    name: str
    profarea_id: str | None = None
    profarea_name: str | None = None

    class Config:
        extra = "ignore"


class Salary(BaseModel):
    """Зарплата"""
    from_: int | None = Field(None, alias="from")
    to: int | None = None
    currency: str | None = None
    gross: bool | None = None

    class Config:
        extra = "ignore"
        populate_by_name = True


class Experience(BaseModel):
    """Требуемый опыт работы"""
    id: str
    name: str

    class Config:
        extra = "ignore"


class Employment(BaseModel):
    """Тип занятости"""
    id: str
    name: str

    class Config:
        extra = "ignore"


class Schedule(BaseModel):
    """График работы"""
    id: str
    name: str

    class Config:
        extra = "ignore"


class Area(BaseModel):
    """Регион"""
    id: str
    name: str
    url: str | None = None

    class Config:
        extra = "ignore"


class Employer(BaseModel):
    """Работодатель"""
    id: str
    name: str
    url: str | None = None
    alternate_url: str | None = None
    trusted: bool | None = None

    class Config:
        extra = "ignore"


class Vacancy(BaseModel):
    """Вакансия"""
    id: str
    name: str
    description: str
    professional_roles: list[ProfessionalRole] = []
    key_skills: list[str] = []
    specializations: list[Specialization] = []
    experience: Experience | None = None
    salary: Salary | None = None
    employment: Employment | None = None
    schedule: Schedule | None = None
    area: Area | None = None
    employer: Employer | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    archived: bool = False
    url: str | None = None
    alternate_url: str | None = None

    class Config:
        extra = "ignore"


class CollectionMetadata(BaseModel):
    """Метаданные коллекции вакансий"""
    collection_time: datetime
    source: str = "hh.ru"
    total_vacancies: int = 0
    vacancies_per_profession: int = 10
    version: str = "2.0"

    class Config:
        extra = "ignore"


class VacanciesCollection(BaseModel):
    """Коллекция вакансий"""
    metadata: CollectionMetadata
    vacancies: list[Vacancy] = []

    class Config:
        extra = "ignore"


class CollectionStatistics(BaseModel):
    """Статистика сбора данных"""
    roles_processed: int = 0
    it_professions_processed: int = 0
    total_collected: int = 0
    errors_count: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Длительность сбора в секундах"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    class Config:
        extra = "ignore"


class VacancySearchParams(BaseModel):
    """Параметры поиска вакансий"""
    area: int = 113
    per_page: int = 100
    page: int = 0
    only_with_salary: bool = True
    text: str | None = None
    professional_role: str | None = None
    search_field: str | None = None

    class Config:
        extra = "ignore"


# Модели для статистики
from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, Literal


class SalaryStats(BaseModel):
    """Статистика по зарплатам"""

    avg_from: float = Field(..., description="Средняя зарплата 'от'")
    avg_to: float = Field(..., description="Средняя зарплата 'до'")
    avg_middle: float = Field(..., description="Средняя зарплата (середина диапазона)")
    count: int = Field(..., ge=0, description="Количество вакансий")
    currency: str = Field(..., description="Валюта", max_length=3)

    @validator('currency')
    def validate_currency(cls, v: str) -> str:
        """Валидация валюты (должна быть в верхнем регистре)"""
        return v.upper()

    @validator('avg_from', 'avg_to', 'avg_middle')
    def validate_positive(cls, v: float) -> float:
        """Проверка, что зарплата положительная"""
        if v < 0:
            raise ValueError('Зарплата не может быть отрицательной')
        return round(v, 2)


class SingleStatResponse(BaseModel):
    """Ответ для одиночной статистики (например, автомойщики без опыта)"""

    category: Optional[str] = Field(None, description="Категория (роль, опыт и т.д.)")
    stats: SalaryStats


class GroupedStatsResponse(BaseModel):
    """Ответ для сгруппированной статистики"""

    group_by: Literal["experience", "professional_role", "area"] = Field(
        ...,
        description="Тип группировки"
    )
    data: Dict[str, SalaryStats] = Field(..., description="Данные по группам")
    total_groups: int = Field(..., ge=0, description="Количество групп")

    @validator('total_groups', always=True)
    def validate_total_groups(cls, v: int, values: dict) -> int:
        """Проверка соответствия количества групп"""
        if 'data' in values and len(values['data']) != v:
            return len(values['data'])
        return v


class ComparisonStatsResponse(BaseModel):
    """Ответ для сравнения двух категорий"""

    category_1: str = Field(..., description="Первая категория")
    stats_1: SalaryStats
    category_2: str = Field(..., description="Вторая категория")
    stats_2: SalaryStats
    difference_percent: Optional[float] = Field(
        None,
        description="Процентная разница в средней зарплате"
    )

    @validator('difference_percent', always=True)
    def calculate_difference(cls, v: Optional[float], values: dict) -> float:
        """Автоматический расчёт разницы"""
        if v is not None:
            return v
        if 'stats_1' in values and 'stats_2' in values:
            avg1 = values['stats_1'].avg_middle
            avg2 = values['stats_2'].avg_middle
            if avg2 != 0:
                return round(((avg1 - avg2) / avg2) * 100, 2)
        return 0.0


class CompleteStatsResponse(BaseModel):
    """Полный ответ со всеми статистиками"""

    target_category: Optional[SingleStatResponse] = Field(
        None,
        description="Целевая категория (например, автомойщики без опыта)"
    )
    baseline_category: Optional[SingleStatResponse] = Field(
        None,
        description="Базовая категория для сравнения (например, все без опыта)"
    )
    by_experience: Optional[GroupedStatsResponse] = Field(
        None,
        description="Статистика по опыту работы"
    )
    by_professional_role: Optional[GroupedStatsResponse] = Field(
        None,
        description="Статистика по профессиональным ролям"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "target_category": {
                    "category": "Автомойщики без опыта",
                    "stats": {
                        "avg_from": 66625.0,
                        "avg_to": 85714.29,
                        "avg_middle": 82375.0,
                        "count": 8,
                        "currency": "RUR"
                    }
                }
            }
        }


