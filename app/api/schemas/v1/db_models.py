from pydantic import BaseModel, UUID4, Field
from datetime import datetime


class UserFromDB:
    class Request(BaseModel):
        tg_id: int
        tg_username: str | None = None
        name: str | None = None

    class Response(BaseModel):
        class Config:
            from_attributes = True

        id: UUID4
        tg_id: int
        tg_username: str | None = None
        name: str | None = None

        video_balance: int
        is_live_image_generation_available: bool
        template_url: str | None = None
        allow_n_template: bool
        sub_language: str

        created_at: datetime | None = None
        updated_at: datetime | None = None
