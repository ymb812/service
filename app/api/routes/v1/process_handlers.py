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
        profession_check = await llm_service.check_profession_reality(request.user_message)

        if not profession_check['is_real']:
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
            clarification_history=[{"question": first_question, "answer": None}],  # ✅ Вот здесь!
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
            session.identified_profession = request.answer
            session.clarification_stage = "profession_details"

            first_question = await llm_service.generate_profession_detail_question(
                profession_name=request.answer,
                question_number=1,
                initial_context=f"{session.initial_message} (выбрана профессия: {request.answer})",
                previous_qa=[]
            )

            history.append({"question": first_question, "answer": None})
            session.clarification_history = history
            await session.save()

            return ClarificationResponse(
                session_id=session.id,
                question=first_question,
                stage="profession_details",
                alternatives=None
            )

        # === Уточнение деталей профессии (до 2 вопросов) ===
        if stage == "profession_details":
            if history and history[-1]['answer'] is None:
                history[-1]['answer'] = request.answer
            else:
                # Это не должно случаться, но на всякий случай
                logger.warning(f"Unexpected state: history={history}, answer={request.answer}")
                history.append({"question": "Unknown question", "answer": request.answer})

            session.clarification_history = history

            # Проверяем, нужны ли ещё вопросы (максимум 2)
            if len(history) < 2:
                # Задаём следующий вопрос с учетом контекста
                next_question = await llm_service.generate_profession_detail_question(
                    profession_name=session.identified_profession,
                    question_number=len(history) + 1,
                    initial_context=session.initial_message,
                    previous_qa=history  # ✅ Теперь здесь правильные вопросы
                )

                # ✅ ИСПРАВЛЕНИЕ: добавляем новый вопрос с его реальным текстом
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


from database.models import CollectionMetadata, Vacancy
import json
import database
from datetime import datetime
@router.post('/db')
async def load_vacancies_from_json(json_file_path: str) -> dict:
    """
    Загружает вакансии из JSON файла в базу данных.
    Все данные записываются в одну модель Vacancy.

    Args:
        json_file_path: путь к JSON файлу с вакансиями

    Returns:
        dict: статистика загрузки
    """
    print(f"Начинаем загрузку данных из {json_file_path}...")

    # Читаем JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stats = {
        'vacancies_created': 0,
        'vacancies_updated': 0,
        'vacancies_skipped': 0,
        'errors': []
    }

    # Сохраняем метаданные
    metadata = data.get('metadata', {})
    if metadata:
        try:
            collection_time_str = metadata.get('collection_time', '')
            # Парсим ISO формат datetime
            if collection_time_str:
                collection_time = datetime.fromisoformat(collection_time_str)
            else:
                collection_time = datetime.now()

            await CollectionMetadata.create(
                collection_time=collection_time,
                source=metadata.get('source', 'hh.ru'),
                total_vacancies=metadata.get('total_vacancies', 0),
                vacancies_per_profession=metadata.get('vacancies_per_profession', 0),
                version=metadata.get('version', '1.0'),
                extra_data=metadata
            )
            print("✓ Метаданные сохранены")
        except Exception as e:
            print(f"✗ Ошибка при сохранении метаданных: {e}")

    # Обрабатываем вакансии
    vacancies_data = data.get('vacancies', [])
    total = len(vacancies_data)

    print(f"\nНачинаем обработку {total} вакансий...\n")

    for idx, vacancy_data in enumerate(vacancies_data, 1):
        try:
            vacancy_id = vacancy_data.get('id')

            if not vacancy_id:
                stats['vacancies_skipped'] += 1
                stats['errors'].append(f"Вакансия #{idx}: отсутствует ID")
                continue

            # Подготавливаем данные
            vacancy_dict = {
                'id': vacancy_id,
                'name': vacancy_data.get('name', ''),
                'description': vacancy_data.get('description'),
                'professional_roles': vacancy_data.get('professional_roles', []),
                'key_skills': vacancy_data.get('key_skills', []),
                'specializations': vacancy_data.get('specializations', []),
                'experience': vacancy_data.get('experience', {}),
                'salary': vacancy_data.get('salary'),
                'employment': vacancy_data.get('employment', {}),
                'schedule': vacancy_data.get('schedule', {}),
            }

            # Проверяем существование вакансии
            existing_vacancy = await Vacancy.filter(id=vacancy_id).first()

            if existing_vacancy:
                # Обновляем существующую вакансию
                for key, value in vacancy_dict.items():
                    if key != 'id':  # ID не обновляем
                        setattr(existing_vacancy, key, value)

                await existing_vacancy.save()
                stats['vacancies_updated'] += 1

            else:
                # Создаём новую вакансию
                await Vacancy.create(**vacancy_dict)
                stats['vacancies_created'] += 1

            # Прогресс каждые 100 вакансий
            if idx % 100 == 0:
                print(f"Прогресс: {idx}/{total} "
                      f"(создано: {stats['vacancies_created']}, "
                      f"обновлено: {stats['vacancies_updated']}, "
                      f"ошибок: {len(stats['errors'])})")

        except Exception as e:
            error_msg = f"Вакансия #{idx} (ID: {vacancy_data.get('id', 'N/A')}): {str(e)}"
            stats['errors'].append(error_msg)
            print(f"✗ {error_msg}")

    # Итоговая статистика
    print("\n" + "=" * 60)
    print("СТАТИСТИКА ЗАГРУЗКИ")
    print("=" * 60)
    print(f"✓ Вакансий создано:   {stats['vacancies_created']}")
    print(f"↻ Вакансий обновлено: {stats['vacancies_updated']}")
    print(f"⊘ Вакансий пропущено: {stats['vacancies_skipped']}")
    print(f"✗ Ошибок:             {len(stats['errors'])}")
    print("=" * 60)

    if stats['errors']:
        print("\nПервые 10 ошибок:")
        for i, error in enumerate(stats['errors'][:10], 1):
            print(f"  {i}. {error}")

        if len(stats['errors']) > 10:
            print(f"  ... и ещё {len(stats['errors']) - 10} ошибок")

    return stats


from typing import Dict, Optional, Any
from pydantic import ValidationError


async def calculate_average_salary(
        professional_role: Optional[str] = None,
        experience_id: Optional[str] = None,
        currency: str = "RUR"
) -> Dict[str, Any]:
    """
    Подсчет средней зарплаты по вакансиям с фильтрацией.

    Args:
        professional_role: Название профессиональной роли (например, "Автомойщик")
        experience_id: ID требуемого опыта (например, "noExperience", "between1And3")
        currency: Валюта для расчета (по умолчанию RUR)

    Returns:
        Dict с полями:
        - avg_from: средняя минимальная зарплата
        - avg_to: средняя максимальная зарплата
        - avg_middle: средняя зарплата (среднее между from и to)
        - count: количество вакансий в выборке
        - currency: валюта
    """

    # Получаем все вакансии (фильтрация по JSON-полям будет в Python)
    vacancies = await Vacancy.all()

    # Фильтруем вакансии в Python
    filtered_vacancies = []
    for vacancy in vacancies:
        # Пропускаем вакансии без зарплаты
        if not vacancy.salary:
            continue

        # Фильтр по профессиональной роли
        if professional_role:
            roles = vacancy.professional_roles or []
            role_match = any(role.get("name") == professional_role for role in roles)
            if not role_match:
                continue

        # Фильтр по опыту
        if experience_id:
            exp = vacancy.experience or {}
            if exp.get("id") != experience_id:
                continue

        # Фильтр по валюте
        if vacancy.salary.get("currency") != currency:
            continue

        filtered_vacancies.append(vacancy)

    # Собираем данные по зарплатам
    salary_from_list = []
    salary_to_list = []
    middle_salaries = []

    for vacancy in filtered_vacancies:
        salary = vacancy.salary

        from_val = salary.get("from")
        to_val = salary.get("to")

        # Собираем from
        if from_val is not None:
            salary_from_list.append(float(from_val))

        # Собираем to
        if to_val is not None:
            salary_to_list.append(float(to_val))

        # Вычисляем среднюю для вакансии
        if from_val is not None and to_val is not None:
            middle_salaries.append((float(from_val) + float(to_val)) / 2)
        elif from_val is not None:
            middle_salaries.append(float(from_val))
        elif to_val is not None:
            middle_salaries.append(float(to_val))

    # Расчет средних значений
    avg_from = sum(salary_from_list) / len(salary_from_list) if salary_from_list else 0.0
    avg_to = sum(salary_to_list) / len(salary_to_list) if salary_to_list else 0.0
    avg_middle = sum(middle_salaries) / len(middle_salaries) if middle_salaries else 0.0

    return {
        "avg_from": round(avg_from, 2),
        "avg_to": round(avg_to, 2),
        "avg_middle": round(avg_middle, 2),
        "count": len(middle_salaries),
        "currency": currency
    }


async def calculate_salary_by_groups(
        group_by: str = "experience",  # "experience" или "professional_role"
        currency: str = "RUR"
) -> Dict[str, Dict[str, Any]]:
    """
    Группировка и подсчет средней зарплаты по различным параметрам.

    Args:
        group_by: Параметр для группировки ("experience" или "professional_role")
        currency: Валюта для расчета

    Returns:
        Dict с результатами по каждой группе
    """

    vacancies = await Vacancy.all()

    groups = {}

    for vacancy in vacancies:
        salary = vacancy.salary

        # Пропускаем вакансии без зарплаты или с неподходящей валютой
        if not salary or salary.get("currency") != currency:
            continue

        # Определяем ключ группировки
        if group_by == "experience":
            exp = vacancy.experience or {}
            group_key = exp.get("name", "Не указано")
        elif group_by == "professional_role":
            roles = vacancy.professional_roles or []
            group_key = roles[0]["name"] if roles else "Не указано"
        else:
            continue

        # Инициализируем группу
        if group_key not in groups:
            groups[group_key] = {
                "from_list": [],
                "to_list": [],
                "middle_list": []
            }

        # Собираем данные
        from_val = salary.get("from")
        to_val = salary.get("to")

        if from_val is not None:
            groups[group_key]["from_list"].append(float(from_val))
        if to_val is not None:
            groups[group_key]["to_list"].append(float(to_val))

        # Вычисляем среднюю для вакансии
        if from_val is not None and to_val is not None:
            groups[group_key]["middle_list"].append((float(from_val) + float(to_val)) / 2)
        elif from_val is not None:
            groups[group_key]["middle_list"].append(float(from_val))
        elif to_val is not None:
            groups[group_key]["middle_list"].append(float(to_val))

    # Вычисляем средние для каждой группы
    result = {}
    for group_key, data in groups.items():
        result[group_key] = {
            "avg_from": round(sum(data["from_list"]) / len(data["from_list"]), 2) if data["from_list"] else 0.0,
            "avg_to": round(sum(data["to_list"]) / len(data["to_list"]), 2) if data["to_list"] else 0.0,
            "avg_middle": round(sum(data["middle_list"]) / len(data["middle_list"]), 2) if data["middle_list"] else 0.0,
            "count": len(data["middle_list"]),
            "currency": currency
        }

    return result


# Оптимизированная версия с использованием list comprehension
async def calculate_average_salary_optimized(
        professional_role: Optional[str] = None,
        experience_id: Optional[str] = None,
        currency: str = "RUR"
) -> Dict[str, Any]:
    """
    Оптимизированная версия подсчета средней зарплаты.
    Использует генераторы и list comprehension для лучшей производительности.
    """

    vacancies = await Vacancy.all()

    # Функция фильтрации
    def passes_filters(vacancy):
        if not vacancy.salary or vacancy.salary.get("currency") != currency:
            return False

        if professional_role:
            roles = vacancy.professional_roles or []
            if not any(role.get("name") == professional_role for role in roles):
                return False

        if experience_id:
            exp = vacancy.experience or {}
            if exp.get("id") != experience_id:
                return False

        return True

    # Фильтруем вакансии
    filtered = [v for v in vacancies if passes_filters(v)]

    # Извлекаем зарплаты
    salary_from = [float(v.salary["from"]) for v in filtered if v.salary.get("from") is not None]
    salary_to = [float(v.salary["to"]) for v in filtered if v.salary.get("to") is not None]

    # Вычисляем средние для каждой вакансии
    middle_salaries = []
    for v in filtered:
        from_val = v.salary.get("from")
        to_val = v.salary.get("to")

        if from_val is not None and to_val is not None:
            middle_salaries.append((float(from_val) + float(to_val)) / 2)
        elif from_val is not None:
            middle_salaries.append(float(from_val))
        elif to_val is not None:
            middle_salaries.append(float(to_val))

    return {
        "avg_from": round(sum(salary_from) / len(salary_from), 2) if salary_from else 0.0,
        "avg_to": round(sum(salary_to) / len(salary_to), 2) if salary_to else 0.0,
        "avg_middle": round(sum(middle_salaries) / len(middle_salaries), 2) if middle_salaries else 0.0,
        "count": len(middle_salaries),
        "currency": currency
    }


from pydantic import BaseModel
from typing import List, Dict, Any

from typing import Optional
from fastapi import HTTPException, status
from fastapi.responses import PlainTextResponse



@router.get('/stats/full')
async def get_full_stats_print(
        target_role: Optional[str] = "Автомойщик",
        target_experience: Optional[str] = "noExperience",
        baseline_experience: Optional[str] = "noExperience"
):
    """
    Получение полной статистики в текстовом формате (как print).

    Args:
        target_role: Целевая профессиональная роль для первой строки
        target_experience: Опыт для целевой роли
        baseline_experience: Опыт для базовой статистики

    Returns:
        Форматированный текст со всей статистикой
    """
    try:
        output_lines = []

        # 1. Целевая категория (например, Автомойщики без опыта)
        if target_role and target_experience:
            target_result = await calculate_average_salary(
                professional_role=target_role,
                experience_id=target_experience
            )

            # Получаем название опыта для красивого вывода
            exp_name = {
                "noExperience": "без опыта",
                "between1And3": "от 1 до 3 лет",
                "between3And6": "от 3 до 6 лет",
                "moreThan6": "более 6 лет"
            }.get(target_experience, target_experience)

            output_lines.append(
                f"{target_role} {exp_name}: {target_result}"
            )

        # 2. Базовая категория (все вакансии без опыта)
        if baseline_experience:
            baseline_result = await calculate_average_salary(
                experience_id=baseline_experience
            )

            exp_name = {
                "noExperience": "без опыта",
                "between1And3": "от 1 до 3 лет",
                "between3And6": "от 3 до 6 лет",
                "moreThan6": "более 6 лет"
            }.get(baseline_experience, baseline_experience)

            output_lines.append(
                f"Все вакансии {exp_name}: {baseline_result}"
            )

        # 3. По опыту работы
        output_lines.append("\nПо опыту работы:")
        experience_data = await calculate_salary_by_groups(group_by="experience")

        for exp_name, stats in experience_data.items():
            if stats["count"] > 0:  # Показываем только непустые группы
                output_lines.append(f"  {exp_name}: {stats}")

        # 4. По профессиональным ролям
        output_lines.append("\nПо ролям:")
        role_data = await calculate_salary_by_groups(group_by="professional_role")

        for role_name, stats in role_data.items():
            if stats["count"] > 0:  # Показываем только непустые группы
                output_lines.append(f"  {role_name}: {stats}")

        # Объединяем все строки
        result_text = "\n".join(output_lines)

        return {
            "text": result_text,
            "lines": output_lines
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при формировании статистики: {str(e)}"
        )


@router.get('/stats/full/plain', response_class=PlainTextResponse)
async def get_full_stats_plain_text(
        target_role: Optional[str] = "Автомойщик",
        target_experience: Optional[str] = "noExperience",
        baseline_experience: Optional[str] = "noExperience"
):
    """
    Получение полной статистики в виде обычного текста (content-type: text/plain).
    Удобно для копирования в консоль или текстовый файл.
    """
    result = await get_full_stats_print(
        target_role=target_role,
        target_experience=target_experience,
        baseline_experience=baseline_experience
    )
    return result["text"]



from pydantic import BaseModel, Field
class FullStatsTextResponse(BaseModel):
    """Полная статистика в текстовом формате"""

    text: str = Field(..., description="Полный текст статистики")
    lines: List[str] = Field(..., description="Массив строк для программной обработки")
    data: Dict[str, Any] = Field(..., description="Структурированные данные")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Автомойщики без опыта: {...}\nВсе вакансии без опыта: {...}",
                "lines": [
                    "Автомойщики без опыта: {...}",
                    "Все вакансии без опыта: {...}"
                ],
                "data": {
                    "target": {"avg_from": 66625.0, "count": 8},
                    "baseline": {"avg_from": 76378.17, "count": 501}
                }
            }
        }


@router.get('/stats/full/structured', response_model=FullStatsTextResponse)
async def get_full_stats_structured(
        target_role: Optional[str] = "Автомойщик",
        target_experience: Optional[str] = "noExperience",
        baseline_experience: Optional[str] = "noExperience"
):
    """
    Получение полной статистики в структурированном формате
    с текстом, массивом строк и данными.
    """
    try:
        output_lines = []
        structured_data = {}

        # 1. Целевая категория
        if target_role and target_experience:
            target_result = await calculate_average_salary(
                professional_role=target_role,
                experience_id=target_experience
            )

            exp_name = {
                "noExperience": "без опыта",
                "between1And3": "от 1 до 3 лет",
                "between3And6": "от 3 до 6 лет",
                "moreThan6": "более 6 лет"
            }.get(target_experience, target_experience)

            line = f"{target_role} {exp_name}: {target_result}"
            output_lines.append(line)
            structured_data["target"] = target_result

        # 2. Базовая категория
        if baseline_experience:
            baseline_result = await calculate_average_salary(
                experience_id=baseline_experience
            )

            exp_name = {
                "noExperience": "без опыта",
                "between1And3": "от 1 до 3 лет",
                "between3And6": "от 3 до 6 лет",
                "moreThan6": "более 6 лет"
            }.get(baseline_experience, baseline_experience)

            line = f"Все вакансии {exp_name}: {baseline_result}"
            output_lines.append(line)
            structured_data["baseline"] = baseline_result

        # 3. По опыту
        output_lines.append("\nПо опыту работы:")
        experience_data = await calculate_salary_by_groups(group_by="experience")

        filtered_exp = {k: v for k, v in experience_data.items() if v["count"] > 0}
        structured_data["by_experience"] = filtered_exp

        for exp_name, stats in filtered_exp.items():
            output_lines.append(f"  {exp_name}: {stats}")

        # 4. По ролям
        output_lines.append("\nПо ролям:")
        role_data = await calculate_salary_by_groups(group_by="professional_role")

        filtered_roles = {k: v for k, v in role_data.items() if v["count"] > 0}
        structured_data["by_professional_role"] = filtered_roles

        for role_name, stats in filtered_roles.items():
            output_lines.append(f"  {role_name}: {stats}")

        result_text = "\n".join(output_lines)

        return FullStatsTextResponse(
            text=result_text,
            lines=output_lines,
            data=structured_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при формировании статистики: {str(e)}"
        )
