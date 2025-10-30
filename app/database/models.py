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
