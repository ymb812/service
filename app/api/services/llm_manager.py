from ollama import AsyncClient
from settings.settings import settings
import json
import re
import logging

logger = logging.getLogger(__name__)


class OllamaService:
    """Сервис для работы с Ollama через AsyncClient"""

    def __init__(self):
        self.client = AsyncClient(host=settings.ollama_url)
        self.model = settings.ollama_model

    async def _generate(
            self,
            prompt: str,
            temperature: float = None,
            num_predict: int = None,
            stream: bool = False
    ) -> str:
        """Базовая генерация текста"""
        options = {
            'temperature': temperature or settings.ollama_temperature,
            'num_predict': num_predict or settings.ollama_num_predict,
        }

        if stream:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options=options,
                stream=True
            )

            full_text = ''
            async for chunk in response:
                full_text += chunk.get('response', '')

            return full_text
        else:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options=options,
                stream=False
            )
            return response['response']

    def _extract_json(self, text: str) -> dict:
        """Умное извлечение JSON из текста LLM"""
        # 1. Попытка найти JSON блок в markdown
        code_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_block:
            text = code_block.group(1)

        # 2. Поиск первой { и последней }
        start = text.find('{')
        end = text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError("No JSON found in response")

        json_str = text[start:end + 1]

        # 3. Парсинг с детальной ошибкой
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error at position {e.pos}:\n{json_str[max(0, e.pos - 50):e.pos + 50]}")
            raise ValueError(f"Invalid JSON: {e.msg}")

    async def check_profession_reality(self, user_message: str) -> dict:
        """
        Проверяет реальность профессии и возвращает:
        {
            "is_real": true/false,
            "profession_name": "Название профессии" или null,
            "alternatives": ["Профессия 1", "Профессия 2", "Профессия 3"] или null
        }
        """
        prompt = f"""Ты - эксперт по профессиям.

Пользователь написал: "{user_message}"

Определи:
1. Это реальная профессия? (да/нет)
2. Если да - как она точно называется?
3. Если нет - предложи 3 похожие реальные профессии

Ответь СТРОГО в формате JSON:
{{
    "is_real": true,
    "profession_name": "Точное название профессии",
    "alternatives": null
}}

ИЛИ если нереальная:
{{
    "is_real": false,
    "profession_name": null,
    "alternatives": ["Профессия 1", "Профессия 2", "Профессия 3"]
}}

Ответ (только JSON):"""

        response = await self._generate(
            prompt,
            temperature=0.3,
            num_predict=200,
            stream=False
        )

        return self._extract_json(response)

    async def generate_profession_detail_question(
            self,
            profession_name: str,
            question_number: int
    ) -> str:
        """
        Генерирует уточняющий вопрос о профессии (до 3 вопросов)
        question_number: 1, 2, или 3
        """
        prompt = f"""Ты уточняешь детали профессии "{profession_name}".

Это вопрос #{question_number} из максимум 3.

Задай ОДИН короткий вопрос, чтобы понять:
- Вопрос 1: Уровень опыта
- Вопрос 2: Специфика работы
- Вопрос 3: Индустрия или технологии

Примеры:
- "Какой у вас опыт: начинающий или уже работали?"
- "Продуктовая команда или аутсорс?"
- "Какая индустрия интересна: финтех, e-commerce?"

Ответь ТОЛЬКО текстом вопроса без кавычек."""

        response = await self._generate(
            prompt,
            temperature=0.5,
            num_predict=50,
            stream=False
        )
        return response.strip().strip('"\'')

    async def generate_vibe_question(self, profession_context: str) -> str:
        """
        Генерирует финальный вопрос про "вайб" работы
        """
        prompt = f"""Контекст профессии: "{profession_context}"

Задай ОДИН вопрос (до 15 слов) про общую атмосферу и стиль работы.

Примеры хороших вопросов:
- "Больше креатива или рутины?"
- "Интенсивный темп или размеренный?"
- "Работа в одиночку или в команде?"
- "Глубокое погружение или широкий охват?"

Ответь ТОЛЬКО текстом вопроса без кавычек."""

        response = await self._generate(
            prompt,
            temperature=0.6,
            num_predict=50,
            stream=False
        )
        return response.strip().strip('"\'')

    async def generate_profile(
            self,
            profession_name: str,
            clarification_history: list,
            vibe_answer: str,
            progress_callback=None
    ) -> dict:
        """
        Генерация карьерного профиля
        clarification_history: [{"question": "...", "answer": "..."}, ...]
        """

        # Формируем контекст из истории уточнений
        context_parts = [f"Q: {item['question']}\nA: {item['answer']}"
                         for item in clarification_history]
        context = "\n\n".join(context_parts)

        prompt = f"""Ты генеришь детальные карьерные профили специалистов.

Профессия: "{profession_name}"

Контекст из уточнений:
{context}

Общий вайб работы: "{vibe_answer}"

Создай профиль в формате JSON:
{{
    "position_title": "Полное название позиции с контекстом (например: Backend-разработчик в финтех-стартапе)",
    "sounds": ["Атмосферный звук 1", "Атмосферный звук 2", "Атмосферный звук 3"],
    "career_growth": "Junior → Middle → Senior → Lead → ...",
    "balance_score": "60/40",
    "benefit": "Главная польза/ценность этой работы (одно предложение)",
    "typical_day": "Подробное текстовое описание типичного рабочего дня от утра до вечера. Начни с времени пробуждения, опиши основные активности с временными метками. Минимум 5-7 предложений, создающих живую картину дня.",
    "real_cases": [
        {{
            "title": "Название реальной задачи 1",
            "description": "Детальное описание задачи и что нужно сделать",
            "difficulty": "easy"
        }},
        {{
            "title": "Название реальной задачи 2",
            "description": "Детальное описание задачи и что нужно сделать",
            "difficulty": "medium"
        }},
        {{
            "title": "Название реальной задачи 3",
            "description": "Детальное описание задачи и что нужно сделать",
            "difficulty": "hard"
        }}
    ],
    "tech_stack": ["Технология 1", "Технология 2", "Технология 3", "Технология 4"],
    "visual": ["Что показать визуально 1", "Что показать визуально 2", "Что показать визуально 3"]
}}

ВАЖНЫЕ ТРЕБОВАНИЯ:

1. **sounds**: Атмосферные звуки рабочего дня (клики мыши, уведомления Slack, zoom-звонки, шум кофемашины)

2. **balance_score**: СТРОГО формат "XX/YY" (например: 70/30, 50/50, 60/40)

3. **typical_day**: Живое описание дня в формате текста. Пример:
   "Утро начинается в 9:00 с проверки метрик в Grafana и прочтения сообщений в Slack. В 10:00 ежедневный стендап на 15 минут, где обсуждаем прогресс. С 10:30 до 13:00 — глубокая работа над фичей: пишу код, делаю ревью PR коллег. Обед в 13:00. После обеда в 14:00 созвон с дизайнером по новому функционалу. С 15:00 до 17:30 дописываю тесты и фиксю баги. В 17:30 отправляю PR на ревью и планирую завтрашний день. День заканчивается в 18:00."

4. **real_cases**: 3 реальные задачи с нарастающей сложностью (easy/medium/hard). Должны быть конкретными и специфичными для профессии.

5. **tech_stack**: 4-6 реальных технологий/инструментов

6. **visual**: Что можно показать на скриншотах (интерфейсы, код, дашборды)

Верни ТОЛЬКО валидный JSON без markdown и пояснений."""

        # Генерация со стримингом и прогрессом
        if progress_callback:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.8,
                    'num_predict': 3072  # Увеличили для подробного описания
                },
                stream=True
            )

            full_text = ''
            import time
            last_update = time.time()
            update_interval = 1.0

            async for chunk in response:
                new_text = chunk.get('response', '')
                full_text += new_text

                current_time = time.time()
                if current_time - last_update >= update_interval:
                    await progress_callback(full_text)
                    last_update = current_time
        else:
            full_text = await self._generate(
                prompt,
                temperature=0.8,
                num_predict=3072,
                stream=False
            )

        # Извлекаем и валидируем JSON
        data = self._extract_json(full_text)

        # Базовая валидация обязательных полей
        required_fields = [
            'position_title', 'sounds', 'career_growth', 'balance_score',
            'benefit', 'typical_day', 'real_cases', 'tech_stack', 'visual'
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Проверяем формат balance_score
        if not re.match(r'^\d+/\d+$', data['balance_score']):
            logger.warning(f"Invalid balance_score format: {data['balance_score']}, fixing to 50/50")
            data['balance_score'] = "50/50"

        # Проверяем real_cases
        if len(data['real_cases']) < 3:
            raise ValueError(f"Need at least 3 real_cases, got {len(data['real_cases'])}")

        for case in data['real_cases']:
            if 'title' not in case or 'description' not in case or 'difficulty' not in case:
                raise ValueError("Invalid real_case structure")

        return data

    async def close(self):
        """Закрытие клиента"""
        pass


# Singleton instance
llm_service = OllamaService()
