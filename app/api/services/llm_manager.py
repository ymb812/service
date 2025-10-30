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

    def _normalize_time(self, time_str: str) -> str:
        """Нормализация времени к формату HH:MM"""
        time_str = time_str.strip()

        # Убираем лишние пробелы
        time_str = re.sub(r'\s+', '', time_str)

        # Если уже в формате HH:MM
        if re.match(r'^\d{2}:\d{2}$', time_str):
            return time_str

        # Если H:MM -> 0H:MM
        if re.match(r'^\d:\d{2}$', time_str):
            return f"0{time_str}"

        # Если HH:M -> HH:0M
        if re.match(r'^\d{2}:\d$', time_str):
            return f"{time_str}0"

        # Если H:M -> 0H:0M
        if re.match(r'^\d:\d$', time_str):
            parts = time_str.split(':')
            return f"0{parts[0]}:0{parts[1]}"

        return time_str

    def _clean_profile_data(self, data: dict) -> dict:
        """Очистка и нормализация данных профиля"""
        # Нормализуем время в расписании
        if 'typical_day' in data and isinstance(data['typical_day'], list):
            for item in data['typical_day']:
                if 'time' in item:
                    item['time'] = self._normalize_time(item['time'])

        # Убеждаемся, что все поля - списки строк
        list_fields = ['sounds', 'tech_stack', 'visual']
        for field in list_fields:
            if field in data:
                if not isinstance(data[field], list):
                    data[field] = [str(data[field])]
                else:
                    data[field] = [str(item) for item in data[field]]

        # Проверяем balance_score
        if 'balance_score' in data:
            score = str(data['balance_score'])
            # Если нет формата X/Y, пытаемся исправить
            if '/' not in score:
                data['balance_score'] = "50/50"  # Дефолтное значение

        return data

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
        """
        prompt = f"""Ты генеришь детальные карьерные профили IT-специалистов.

Запрос пользователя: "{initial_message}"
Уточнение: "{clarification_answer}"

Создай профиль в формате JSON со следующей структурой:
{{
    "position_title": "Полное название позиции с контекстом",
    "sounds": ["Звук 1 рабочего дня", "Звук 2", "Звук 3"],
    "career_growth": "Junior -> Senior -> Lead -> ...",
    "balance_score": "50/50",
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
- balance_score - work-life баланс ОБЯЗАТЕЛЬНО в формате число/число (например: 50/50, 60/40, 70/30)
- typical_day - минимум 4 пункта, время СТРОГО в формате ЧЧ:ММ (например: 09:00, 14:30)
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
            data = json.loads(json_match.group())
            # Очищаем и нормализуем данные
            data = self._clean_profile_data(data)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}\n\nResponse: {full_text[:500]}")

    async def close(self):
        """Закрытие клиента"""
        pass


# Singleton instance
llm_service = OllamaService()
