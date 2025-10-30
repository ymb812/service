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
        prompt = f"""Ты - эксперт по профессиям в любых сферах деятельности.

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
            question_number: int,
            initial_context: str = "",
            previous_qa: list = None
    ) -> str:
        """
        Генерирует уточняющий вопрос о профессии (до 3 вопросов)
        question_number: 1, 2, или 3
        initial_context: исходное сообщение пользователя для учета контекста
        previous_qa: предыдущие вопросы и ответы [{"question": "...", "answer": "..."}]
        """
        # Формируем контекст из уже известной информации
        context_parts = []

        if initial_context:
            context_parts.append(f"Исходный запрос пользователя: '{initial_context}'")

        if previous_qa:
            qa_text = "\n".join([f"- Вопрос: {qa['question']}\n  Ответ: {qa['answer']}"
                                 for qa in previous_qa if qa.get('answer')])
            if qa_text:
                context_parts.append(f"Уже известная информация:\n{qa_text}")

        context_block = "\n\n".join(context_parts) if context_parts else "Контекст отсутствует."

        prompt = f"""Ты уточняешь детали профессии "{profession_name}".

{context_block}

Это вопрос #{question_number} из максимум 3.

ВАЖНО: 
- НЕ задавай вопросы, на которые уже есть ответ в контексте выше
- НЕ дублируй информацию, которую пользователь уже упомянул
- Задавай только новые, релевантные вопросы

Приоритет тем для вопросов:
1. Уровень опыта/квалификация (если не известно из контекста)
2. Специфика работы (тип организации, формат, направление)
3. Индустрия, сфера применения или специализация

Анализируй контекст и задай ОДИН короткий вопрос (до 15 слов), который еще НЕ был задан и на который нет ответа в контексте.

Ответь ТОЛЬКО текстом вопроса без кавычек."""

        response = await self._generate(
            prompt,
            temperature=0.5,
            num_predict=80,
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
- "Стабильность или постоянные изменения?"
- "Следование протоколам или свобода действий?"

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
        Генерация карьерного профиля для любой профессии
        clarification_history: [{"question": "...", "answer": "..."}, ...]
        """

        # Формируем контекст из истории уточнений
        context_parts = [f"Q: {item['question']}\nA: {item['answer']}"
                         for item in clarification_history]
        context = "\n\n".join(context_parts)

        prompt = f"""Ты генеришь детальные карьерные профили специалистов любых профессий.

Профессия: "{profession_name}"

Контекст из уточнений:
{context}

Общий вайб работы: "{vibe_answer}"

Создай профиль в формате JSON:
{{
    "position_title": "Полное название позиции с контекстом (например: Backend-разработчик в финтех-стартапе, Врач-хирург в частной клинике)",
    "sounds": ["Атмосферный звук 1", "Атмосферный звук 2", "Атмосферный звук 3"],
    "career_growth": "Начало → Развитие → Опытный → Эксперт → ...",
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
    "tech_stack": ["Инструмент/Навык 1", "Инструмент/Навык 2", "Инструмент/Навык 3", "Инструмент/Навык 4"],
    "visual": ["Что показать визуально 1", "Что показать визуально 2", "Что показать визуально 3"]
}}

ВАЖНЫЕ ТРЕБОВАНИЯ:

1. **sounds**: Атмосферные звуки рабочего дня, специфичные для профессии
   - IT: клики мыши, уведомления Slack, zoom-звонки
   - Медицина: звуки аппаратуры, шаги по коридору, разговоры пациентов
   - Образование: звонок на урок, шум в классе, скрип мела
   - Ресторан: шипение на сковороде, стук ножей, заказы официантов

2. **balance_score**: СТРОГО формат "XX/YY" (например: 70/30, 50/50, 60/40)
   где первая цифра - работа, вторая - личная жизнь

3. **typical_day**: Живое описание дня в формате текста. Пример:
   "Утро начинается в 9:00 с проверки метрик в Grafana и прочтения сообщений в Slack. В 10:00 ежедневный стендап на 15 минут..."

4. **real_cases**: 3 реальные задачи с нарастающей сложностью (easy/medium/hard). Должны быть конкретными и специфичными для профессии.

5. **tech_stack**: 4-6 реальных инструментов/навыков/технологий, необходимых в профессии
   - IT: языки программирования, фреймворки, инструменты
   - Медицина: медицинское оборудование, препараты, методики
   - Образование: педагогические методики, учебные материалы, системы оценки
   - Ресторан: кухонное оборудование, техники приготовления, ингредиенты

6. **visual**: Что можно показать на фото/скриншотах из рабочего процесса

Верни ТОЛЬКО валидный JSON без markdown и пояснений."""

        # Генерация со стримингом и прогрессом
        if progress_callback:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.8,
                    'num_predict': 3072
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
