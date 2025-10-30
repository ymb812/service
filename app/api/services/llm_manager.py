from ollama import AsyncClient
from settings.settings import settings
import json
import re


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
            # Streaming генерация
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
            # Обычная генерация
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options=options,
                stream=False
            )
            return response['response']

    async def generate_clarification(self, user_message: str) -> str:
        """Генерация уточняющего вопроса"""
        prompt = f"""Ты - карьерный консультант для IT-специалистов.

Пользователь спросил: "{user_message}"

Задай ОДИН короткий уточняющий вопрос (максимум 8-10 слов), чтобы лучше понять контекст.

Примеры хороших вопросов:
- "Больше креатива или рутины?"
- "Удалённо или в офисе?"
- "Продукт или аутсорс?"
- "Стартап или корпорация?"

Ответь ТОЛЬКО текстом вопроса без кавычек и дополнительных пояснений."""

        response = await self._generate(
            prompt,
            temperature=0.5,
            num_predict=50,
            stream=False
        )
        return response.strip().strip('"\'')

    async def generate_profile(
            self,
            initial_message: str,
            clarification_answer: str,
            progress_callback=None
    ) -> dict:
        """
        Генерация карьерного профиля с опциональным прогрессом

        Args:
            initial_message: Первичный вопрос пользователя
            clarification_answer: Ответ на уточнение
            progress_callback: Опциональная функция для отслеживания прогресса
        """
        prompt = f"""Ты генеришь детальные карьерные профили IT-специалистов.

Запрос пользователя: "{initial_message}"
Уточнение: "{clarification_answer}"

Создай профиль в формате JSON со следующей структурой:
{{
    "position_title": "Полное название позиции с контекстом",
    "sounds": ["Звук 1 рабочего дня", "Звук 2", "Звук 3"],
    "career_growth": "Junior -> Senior -> Lead -> ...",
    "balance_score": "X/Y",
    "benefit": "Главная польза/ценность этой работы",
    "typical_day": [
        {{"time": "10:00", "activity": "Описание активности"}},
        {{"time": "12:00", "activity": "Описание активности"}},
        {{"time": "14:00", "activity": "Описание активности"}},
        {{"time": "16:00", "activity": "Описание активности"}}
    ],
    "tech_stack": ["Технология 1", "Технология 2", "Технология 3"],
    "visual": ["Описание визуала 1", "Описание визуала 2", "Описание визуала 3"]
}}

ВАЖНО:
- sounds - атмосферные звуки рабочего дня (клики клавиатуры, zoom-созвоны, уведомления)
- career_growth - реалистичный путь карьеры через стрелки ->
- balance_score - work-life баланс в формате число/число (например 50/50, 60/40)
- typical_day - минимум 4 пункта с разным временем
- visual - что можно показать визуально (скриншоты, фото рабочего места)

Верни ТОЛЬКО валидный JSON без дополнительного текста."""

        # Генерация со стримингом и прогрессом
        if progress_callback:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.8,
                    'num_predict': 2048
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
            # Без стриминга
            full_text = await self._generate(
                prompt,
                temperature=0.8,
                num_predict=2048,
                stream=False
            )

        # Извлекаем JSON из ответа
        json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to extract JSON from LLM response")

        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}\n\nResponse: {full_text[:500]}")

    async def close(self):
        """Закрытие клиента"""
        # AsyncClient от ollama не требует явного закрытия
        pass


# Singleton instance
llm_service = OllamaService()
