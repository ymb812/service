from tortoise import fields
from tortoise.models import Model


class Session(Model):
    """Сессия диалога с пользователем"""
    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=True)

    # Диалог
    initial_message = fields.TextField()
    clarification_question = fields.TextField()
    clarification_answer = fields.TextField(null=True)

    # Результат
    result_data = fields.JSONField(null=True)

    # Статус
    status = fields.CharField(max_length=20, default="waiting_answer")  # waiting_answer, completed

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sessions"
