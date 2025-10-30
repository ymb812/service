import logging
from fastapi import APIRouter, HTTPException, status
from database.models import Session
from api.schemas.v1.ai_models import (
    InitialQueryRequest,
    ClarificationResponse,
    CareerProfileResponse,
    FinalAnswerRequest,
    RealCaseExample,
)
from api.services.llm_manager import llm_service
from settings.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Проверка здоровья приложения и Ollama"""
    try:
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
    Проверяем реальность профессии
    """
    try:
        # Проверяем реальность профессии
        profession_check = await llm_service.check_profession_reality(request.user_message)

        if not profession_check['is_real']:
            # Профессия нереальная - предлагаем альтернативы
            session = await Session.create(
                user_id=request.user_id,
                initial_message=request.user_message,
                clarification_stage="profession_alternatives",
                clarification_history=[],
                status="waiting_answer"
            )

            question = f"К сожалению, такой профессии не существует. Возможно, вы имели в виду одну из этих?"

            return ClarificationResponse(
                session_id=session.id,
                question=question,
                stage="profession_alternatives",
                alternatives=profession_check['alternatives']
            )

        # Профессия реальная - начинаем уточнения
        # Передаем исходный запрос как контекст
        first_question = await llm_service.generate_profession_detail_question(
            profession_name=profession_check['profession_name'],
            question_number=1,
            initial_context=request.user_message,
            previous_qa=[]
        )

        session = await Session.create(
            user_id=request.user_id,
            initial_message=request.user_message,
            identified_profession=profession_check['profession_name'],
            clarification_stage="profession_details",
            clarification_history=[],
            status="waiting_answer"
        )

        return ClarificationResponse(
            session_id=session.id,
            question=first_question,
            stage="profession_details",
            alternatives=None
        )

    except Exception as e:
        logger.error(f"Error in start_session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/answer", response_model=ClarificationResponse | CareerProfileResponse, status_code=status.HTTP_200_OK)
async def answer_clarification(request: FinalAnswerRequest):
    """
    Шаг 2+: Пользователь отвечает на уточняющий вопрос
    Либо задаём следующий вопрос, либо генерируем профиль
    """
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
        stage = session.clarification_stage
        history = session.clarification_history or []

        # === Обработка выбора альтернативной профессии ===
        if stage == "profession_alternatives":
            # Пользователь выбрал одну из предложенных профессий
            session.identified_profession = request.answer
            session.clarification_stage = "profession_details"

            # Передаем исходный запрос и выбранную профессию как контекст
            first_question = await llm_service.generate_profession_detail_question(
                profession_name=request.answer,
                question_number=1,
                initial_context=f"{session.initial_message} (выбрана профессия: {request.answer})",
                previous_qa=[]
            )

            await session.save()

            return ClarificationResponse(
                session_id=session.id,
                question=first_question,
                stage="profession_details",
                alternatives=None
            )

        # === Уточнение деталей профессии (до 3 вопросов) ===
        if stage == "profession_details":
            # Добавляем последний ответ в историю
            if history:
                history[-1]['answer'] = request.answer
            else:
                # Первый ответ - сохраняем вопрос из предыдущего шага
                history.append({"question": "Детали профессии", "answer": request.answer})

            session.clarification_history = history

            # Проверяем, нужны ли ещё вопросы (максимум 3)
            if len(history) < 3:
                # Задаём следующий вопрос с учетом контекста
                next_question = await llm_service.generate_profession_detail_question(
                    profession_name=session.identified_profession,
                    question_number=len(history) + 1,
                    initial_context=session.initial_message,
                    previous_qa=history  # Передаем всю историю Q&A
                )

                # Добавляем новый вопрос в историю
                history.append({"question": next_question, "answer": None})
                session.clarification_history = history
                await session.save()

                return ClarificationResponse(
                    session_id=session.id,
                    question=next_question,
                    stage="profession_details",
                    alternatives=None
                )
            else:
                # Детали собраны, переходим к вопросу про вайб
                context = f"{session.identified_profession}. " + "; ".join([
                    f"{h['answer']}" for h in history if h.get('answer')
                ])

                vibe_question = await llm_service.generate_vibe_question(context)

                session.clarification_stage = "vibe_question"
                history.append({"question": vibe_question, "answer": None})
                session.clarification_history = history
                await session.save()

                return ClarificationResponse(
                    session_id=session.id,
                    question=vibe_question,
                    stage="vibe_question",
                    alternatives=None
                )

        # === Финальный вопрос про вайб ===
        if stage == "vibe_question":
            # Сохраняем ответ на вопрос про вайб
            history[-1]['answer'] = request.answer
            session.clarification_history = history

            # Генерируем профиль
            profile_data = await llm_service.generate_profile(
                profession_name=session.identified_profession,
                clarification_history=history[:-1],  # Все кроме вопроса про вайб
                vibe_answer=request.answer
            )

            # Сохраняем результат
            session.result_data = profile_data
            session.status = "completed"
            session.clarification_stage = "completed"
            await session.save()

            # Возвращаем профиль
            return CareerProfileResponse(
                session_id=session.id,
                position_title=profile_data["position_title"],
                sounds=profile_data["sounds"],
                career_growth=profile_data["career_growth"],
                balance_score=profile_data["balance_score"],
                benefit=profile_data["benefit"],
                typical_day=profile_data["typical_day"],
                real_cases=[RealCaseExample(**case) for case in profile_data["real_cases"]],
                tech_stack=profile_data["tech_stack"],
                visual=profile_data["visual"],
                created_at=session.created_at
            )

    except Exception as e:
        logger.error(f"Error in answer_clarification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing answer: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=CareerProfileResponse)
async def get_session_result(session_id: int):
    """Получить результат по ID сессии"""
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
        typical_day=profile_data["typical_day"],
        real_cases=[RealCaseExample(**case) for case in profile_data["real_cases"]],
        tech_stack=profile_data["tech_stack"],
        visual=profile_data["visual"],
        created_at=session.created_at
    )
