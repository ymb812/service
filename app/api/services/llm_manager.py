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
        Генерирует уточняющий вопрос о профессии (до 2 вопросов)
        Фокус: понять ОЩУЩЕНИЕ работы, а не технические детали
        """
        context_parts = []

        if initial_context:
            context_parts.append(f"Исходный запрос: '{initial_context}'")

        if previous_qa:
            qa_text = "\n".join([
                f"- Вопрос: {qa['question']}\n  Ответ: {qa['answer']}"
                for qa in previous_qa if qa.get('answer')
            ])
            if qa_text:
                context_parts.append(f"Уже известно:\n{qa_text}")

        context_block = "\n\n".join(context_parts) if context_parts else "Контекст отсутствует."

        prompt = f"""Ты помогаешь студентам и начинающим специалистам понять, как "ощущается" работа в профессии "{profession_name}".

    {context_block}

    Это вопрос #{question_number} из максимум 2.

    ВАЖНО: Твоя цель — понять АТМОСФЕРУ и БУДНИ, а не технические детали.

    Приоритеты для вопросов (задавай ТО, что ещё НЕ выяснено):
    1. Размер и тип компании (это кардинально меняет ощущения):
       - Стартап
       - Продуктовая компания
       - Корпорация
       - Фриланс

    2. Уровень опыта (если ещё не ясен):
       - Без опыта
       - Средний
       - Старший

    ЗАПРЕЩЕНО спрашивать:
    - Технические детали (языки программирования, инструменты — это узнаешь позже)
    - Сложные концепции, которые новичок не поймёт
    - Вопросы, на которые уже есть ответ в контексте

    Формат ответа: ОДИН короткий вопрос (до 15 слов) с вариантами ответа в скобках.

    Примеры ХОРОШИХ вопросов:
    - "В какой компании хотите работать? (Стартап / Продуктовая / Корпорация / Фриланс)"
    - "Какой уровень опыта вас интересует? (Junior / Middle / Senior / Team Lead)"
    - "Какое направление ближе? (Продуктовая аналитика / Маркетинговая / Финансовая)"

    Твой вопрос:"""

        response = await self._generate(
            prompt,
            temperature=0.1,
            num_predict=200,
            stream=False
        )
        return response.strip().strip('"\'')

    async def generate_vibe_question(self, profession_context: str) -> str:
        """
        Генерирует финальный вопрос про "вайб" работы
        """
        prompt = f"""Контекст профессии: "{profession_context}"

Задай ОДИН вопрос (до 15 слов) про общую атмосферу и стиль работы - нужно спросить пожелание пользователя.

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
            temperature=0.3,
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
        Генерация карьерного профиля с фокусом на ОЩУЩЕНИЕ работы
        """
        context_parts = [f"Q: {item['question']}\nA: {item['answer']}"
                         for item in clarification_history]
        context = "\n\n".join(context_parts)

        prompt = f"""Ты создаёшь ЖИВОЕ описание профессии для студентов и начинающих специалистов.

    Твоя цель: передать **ОЩУЩЕНИЕ** работы, а не сухие факты из должностной инструкции.

    Профессия: "{profession_name}"

    Контекст:
    {context}

    Общий вайб: "{vibe_answer}"

    ---

    Создай профиль в JSON:

    {{
        "position_title": "Название + контекст (например: 'Junior Frontend-разработчик в стартапе финтеха')",

        "sounds": [
            "Звук 1 (например: 'Треск механической клавиатуры в open space')",
            "Звук 2 (например: 'Пинги в Slack каждые 5 минут')",
            "Звук 3 (например: 'Голос PM: А можно ещё одну фичу до релиза?')"
        ],

        "career_growth": "Реалистичный путь с временными рамками (например: 'Junior (0-2 года) → Middle (2-4 года) → Senior (4-6 лет) → Team Lead (6+ лет)')",

        "balance_score": "XX/YY (где X — работа, Y — личная жизнь)",

        "benefit": "Главная эмоциональная ценность работы. Не 'высокая зарплата', а ЧТО даёт кайф: 'Ты создаёшь интерфейс, которым пользуются миллионы людей каждый день'",

        "typical_day": "ДЕТАЛЬНОЕ описание дня от пробуждения до сна. Минимум 7-10 предложений. Пример:

        'Просыпаешься в 9:00, потому что дедлайнов нет — спринт только начался. Включаешь ноутбук, заходишь в Figma — дизайнер обновил макеты главной страницы. Открываешь VS Code, запускаешь dev-сервер, пьёшь кофе. В 10:00 дейли: PM говорит, что клиент хочет изменить UX формы регистрации. Ты закатываешь глаза, но понимаешь — так и работает стартап. До обеда кодишь новую форму, параллельно гуглишь, как правильно валидировать email в React Hook Form. После обеда — код-ревью от сеньора: 15 комментариев. Исправляешь, учишься. В 17:00 — созвон с бэкендером: API снова возвращает не те данные. Дебажите вместе. В 18:30 пушишь код, создаёшь PR. В 19:00 закрываешь ноутбук, идёшь гулять — завтра продолжишь.'",

        "real_cases": [
            {{
                "title": "Конкретная задача (не 'разработка фичи', а 'Сделать адаптивное меню для мобилок')",
                "description": "Детальное описание: ЧТО нужно сделать, КАКИЕ сложности, ЧТО может пойти не так",
                "difficulty": "easy"
            }},
            {{
                "title": "...",
                "description": "...",
                "difficulty": "medium"
            }},
            {{
                "title": "...",
                "description": "...",
                "difficulty": "hard"
            }}
        ],

        "tech_stack": [
            "Инструмент 1 (с контекстом: не просто 'React', а 'React — пишешь компоненты по 8 часов в день')",
            "Инструмент 2",
            "Инструмент 3",
            "Инструмент 4"
        ],

        "visual": [
            "ЧТО увидишь на экране (например: 'Код в VS Code с темой Dracula')",
            "ЧТО увидишь вокруг (например: 'Open space с 30 разработчиками, стол с двумя мониторами')",
            "ЧТО увидишь в результате (например: 'Твоя кнопка на продакшене, которую нажимают 10К раз в день')"
        ]
    }}

    ---

    КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:

    1. **sounds** — это НЕ метафоры, а РЕАЛЬНЫЕ звуки рабочего дня:
       - Плохо: "Звук успеха" ❌
       - Хорошо: "Уведомление 'Build failed' в CI/CD" ✅

    2. **typical_day** — это ИСТОРИЯ, а не список задач:
       - Плохо: "Утром проверяю почту, потом пишу код" ❌
       - Хорошо: "В 9:30 открываешь Jira — там 23 непрочитанных уведомления. Первым делом проверяешь, не сломался ли прод ночью..." ✅

    3. **real_cases** — КОНКРЕТНЫЕ задачи с РЕАЛЬНЫМИ сложностями:
       - Плохо: "Разработка новой функции" ❌
       - Хорошо: "Сделать бесконечный скролл на React, но так, чтобы не лагало на старых iPhone. Проблема: у тебя нет старого iPhone для теста" ✅

    4. **benefit** — ЭМОЦИЯ, а не факт:
       - Плохо: "Хорошая зарплата" ❌
       - Хорошо: "В 2 часа ночи просыпаешься от мысли, как красиво решить задачу — и это кайф" ✅

    5. **visual** — описывай так, чтобы человек мог ПРЕДСТАВИТЬ картинку:
       - Плохо: "Рабочее место" ❌
       - Хорошо: "MacBook Pro с наклейками, второй монитор 27', стол у окна с видом на город, наушники Sony WH-1000XM4 — без них в open space не выжить" ✅

    Верни ТОЛЬКО JSON без markdown блоков и пояснений."""

        # Генерация со стримингом и прогрессом
        if progress_callback:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
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
                temperature=0.3,
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
