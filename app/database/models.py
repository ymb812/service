from tortoise import fields
from tortoise.models import Model


class Session(Model):
    """Сессия диалога с пользователем"""
    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True)

    # Диалог
    initial_message = fields.TextField()

    # История уточнений (список вопросов и ответов)
    clarification_history = fields.JSONField(default=list)  # [{"question": "...", "answer": "..."}]

    # Текущий этап уточнения
    clarification_stage = fields.CharField(max_length=50, default="profession_check")
    # Значения: profession_check, profession_details, profession_alternatives, vibe_question, completed

    # Определённая профессия
    identified_profession = fields.CharField(max_length=200, null=True)

    # Результат
    result_data = fields.JSONField(null=True)

    # Статус
    status = fields.CharField(max_length=20, default="waiting_answer")  # waiting_answer, completed

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sessions"


class Vacancy(Model):
    """Вакансия - все данные в одной модели"""

    # Основные поля
    id = fields.CharField(max_length=100, pk=True)
    name = fields.CharField(max_length=1000)
    description = fields.TextField(null=True)

    # JSON поля для сложных структур
    professional_roles = fields.JSONField(default=list)  # List[Dict]
    key_skills = fields.JSONField(default=list)  # List[str]
    specializations = fields.JSONField(default=list)  # List[Dict]
    experience = fields.JSONField(default=dict)  # Dict
    salary = fields.JSONField(null=True)  # Dict or None
    employment = fields.JSONField(default=dict)  # Dict
    schedule = fields.JSONField(default=dict)  # Dict

    # Метаданные
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "vacancies"

    def __str__(self):
        return f"Vacancy({self.id}): {self.name}"


class CollectionMetadata(Model):
    """Метаданные сбора данных"""
    id = fields.IntField(pk=True)
    collection_time = fields.DatetimeField()
    source = fields.CharField(max_length=100)
    total_vacancies = fields.IntField()
    vacancies_per_profession = fields.IntField()
    version = fields.CharField(max_length=50)

    # Дополнительные данные в JSON
    extra_data = fields.JSONField(default=dict)

    class Meta:
        table = "collection_metadata"
