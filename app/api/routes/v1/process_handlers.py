import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status
from database.models import Session
from api.schemas.v1.ai_models import (
    InitialQueryRequest,
    ClarificationResponse,
    CareerProfileResponse,
    FinalAnswerRequest,
    DayScheduleItem,
)
from api.services.llm_manager import llm_service
from settings.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Проверка здоровья приложения и Ollama"""
    try:
        # Проверяем доступность Ollama
        test_response = await llm_service.client.generate(
            model=settings.ollama_model,
            prompt="test",
            options={'num_predict': 5},
            stream=False
        )

        return {
            "status": "healthy",
            "ollama": "connected",
            "model": settings.ollama_model
        }
    except Exception as e:
        return {
            "status": "degraded",
            "ollama": "disconnected",
            "error": str(e)
        }


@router.post("/start", response_model=ClarificationResponse, status_code=status.HTTP_200_OK)
async def start_session(request: InitialQueryRequest):
    """
    Шаг 1: Пользователь задаёт вопрос о профессии
    Возвращает уточняющий вопрос
    """
    try:
        # Генерируем уточняющий вопрос
        clarification = await llm_service.generate_clarification(request.user_message)

        # Создаём сессию
        session = await Session.create(
            user_id=request.user_id,
            initial_message=request.user_message,
            clarification_question=clarification,
            status="waiting_answer"
        )

        return ClarificationResponse(
            session_id=session.id,
            question=clarification
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating clarification: {str(e)}"
        )


@router.post("/answer", response_model=CareerProfileResponse, status_code=status.HTTP_200_OK)
async def answer_clarification(request: FinalAnswerRequest):
    """
    Шаг 2: Пользователь отвечает на уточняющий вопрос
    Генерирует и возвращает полный профиль
    """
    # Получаем сессию
    session = await Session.get_or_none(id=request.session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already completed"
        )

    try:
        # Колбэк для отслеживания прогресса (опционально)
        async def progress_callback(current_text: str):
            # Можно логировать или обновлять статус
            print(f"Generated {len(current_text)} characters...")

        # Генерируем профиль
        profile_data = await llm_service.generate_profile(
            session.initial_message,
            request.answer,
            progress_callback=progress_callback if settings.prod_mode else None
        )

        # Сохраняем результат
        session.clarification_answer = request.answer
        session.result_data = profile_data
        session.status = "completed"
        await session.save()

        # Формируем ответ
        return CareerProfileResponse(
            session_id=session.id,
            position_title=profile_data["position_title"],
            sounds=profile_data["sounds"],
            career_growth=profile_data["career_growth"],
            balance_score=profile_data["balance_score"],
            benefit=profile_data["benefit"],
            typical_day=[DayScheduleItem(**item) for item in profile_data["typical_day"]],
            tech_stack=profile_data["tech_stack"],
            visual=profile_data["visual"],
            created_at=session.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating profile: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=CareerProfileResponse)
async def get_session_result(session_id: int):
    """
    Получить результат по ID сессии
    """
    session = await Session.get_or_none(id=session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    if session.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not completed yet"
        )

    profile_data = session.result_data

    return CareerProfileResponse(
        session_id=session.id,
        position_title=profile_data["position_title"],
        sounds=profile_data["sounds"],
        career_growth=profile_data["career_growth"],
        balance_score=profile_data["balance_score"],
        benefit=profile_data["benefit"],
        typical_day=[DayScheduleItem(**item) for item in profile_data["typical_day"]],
        tech_stack=profile_data["tech_stack"],
        visual=profile_data["visual"],
        created_at=session.created_at
    )