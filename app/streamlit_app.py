import streamlit as st
import requests
from typing import Optional
import json
from settings.settings import settings
from datetime import datetime

# Конфигурация
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-API-KEY": f"{settings.x_auth_token.get_secret_value()}"
}

# Настройка страницы
st.set_page_config(
    page_title="IT Career Explorer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Кастомные стили (оставляем как есть)
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 3rem;
    }

    .card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }

    .card h4 {
        color: #2c3e50;
        margin: 0;
    }

    .alternative-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s;
        border-left: 3px solid #667eea;
    }

    .alternative-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .case-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
    }

    .case-card.medium {
        border-left-color: #ffc107;
    }

    .case-card.hard {
        border-left-color: #dc3545;
    }

    .difficulty-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .difficulty-easy {
        background: #d4edda;
        color: #155724;
    }

    .difficulty-medium {
        background: #fff3cd;
        color: #856404;
    }

    .difficulty-hard {
        background: #f8d7da;
        color: #721c24;
    }

    .tech-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.9rem;
        font-weight: 500;
    }

    .sound-item {
        background: #fff3cd;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #ffc107;
        color: #856404;
    }

    .progress-indicator {
        background: #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }

    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 8px;
        border-radius: 4px;
        transition: width 0.3s;
    }

    .typical-day-text {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        line-height: 1.8;
        color: #2c3e50;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# API функции
def check_api_health() -> bool:
    """Проверка доступности API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5, headers=HEADERS)
        return response.status_code == 200
    except:
        return False


def start_session(user_message: str, user_id: Optional[int] = None) -> dict:
    """Начать новую сессию"""
    payload = {
        "user_message": user_message,
        "user_id": user_id
    }
    response = requests.post(f"{API_BASE_URL}/start", json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def submit_answer(session_id: int, answer: str) -> dict:
    """Отправить ответ на уточняющий вопрос"""
    payload = {
        "session_id": session_id,
        "answer": answer
    }
    response = requests.post(f"{API_BASE_URL}/answer", json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


# Инициализация состояния
if 'step' not in st.session_state:
    st.session_state.step = 'initial'
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = None
if 'alternatives' not in st.session_state:
    st.session_state.alternatives = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'initial_message' not in st.session_state:
    st.session_state.initial_message = ""
if 'question_count' not in st.session_state:
    st.session_state.question_count = 0


def reset_session():
    """Сброс сессии"""
    st.session_state.step = 'initial'
    st.session_state.session_id = None
    st.session_state.current_question = None
    st.session_state.current_stage = None
    st.session_state.alternatives = None
    st.session_state.profile = None
    st.session_state.initial_message = ""
    st.session_state.question_count = 0


def get_stage_emoji(stage: str) -> str:
    """Получить emoji для стадии"""
    emojis = {
        'profession_check': '🔍',
        'profession_alternatives': '🔄',
        'profession_details': '📋',
        'vibe_question': '✨'
    }
    return emojis.get(stage, '❓')


def get_stage_label(stage: str) -> str:
    """Получить название стадии"""
    labels = {
        'profession_check': 'Проверка профессии',
        'profession_alternatives': 'Выбор альтернативы',
        'profession_details': 'Уточнение деталей',
        'vibe_question': 'Общий вайб'
    }
    return labels.get(stage, 'Уточнение')


def get_difficulty_class(difficulty: str) -> str:
    """Получить CSS класс для сложности"""
    return f"difficulty-{difficulty}"


# Заголовок
st.markdown('<div class="main-title">🚀 Career Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Узнай вайб различных IT-профессий</div>', unsafe_allow_html=True)

# Проверка API
with st.sidebar:
    st.header("⚙️ Настройки")

    if check_api_health():
        st.success("✅ API доступен")
    else:
        st.error("❌ API недоступен")
        st.info(f"Проверьте, что сервер запущен на {API_BASE_URL}")

    if st.button("🔄 Начать заново"):
        reset_session()
        st.rerun()

    # Показываем прогресс, если не на начальной стадии
    if st.session_state.step != 'initial' and st.session_state.step != 'result':
        st.divider()
        st.markdown("### 📊 Прогресс")

        stage = st.session_state.current_stage
        stage_label = get_stage_label(stage) if stage else "Начало"

        st.markdown(f"**Текущий этап:** {get_stage_emoji(stage)} {stage_label}")

        if stage == 'profession_details':
            st.markdown(f"**Вопрос:** {st.session_state.question_count}/3")
            progress = st.session_state.question_count / 3
            st.progress(progress)

    st.divider()
    st.caption("Версия 2.0 • Multi-step clarification")

# ===== ШАГ 1: Начальный вопрос =====
if st.session_state.step == 'initial':
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 💬 О какой IT-профессии вы хотите узнать?")

        # Примеры вопросов
        with st.expander("💡 Примеры вопросов"):
            st.markdown("""
            - Каково это — быть frontend-разработчиком в стартапе?
            - Что делает DevOps-инженер в крупной компании?
            - Как работает Data Scientist в продуктовой команде?
            - Расскажи про карьеру QA-автоматизатора
            - Хочу быть backend-разработчиком
            - Интересует ML-инженер в финтехе
            """)

        user_question = st.text_area(
            "Ваш вопрос:",
            height=100,
            placeholder="Например: Хочу быть DevOps-инженером в стартапе",
            max_chars=500,
            value=st.session_state.initial_message
        )

        if st.button("🔍 Узнать подробности", type="primary", use_container_width=True):
            if len(user_question.strip()) < 10:
                st.error("⚠️ Вопрос слишком короткий. Напишите хотя бы 10 символов.")
            else:
                with st.spinner("🤔 Анализирую профессию..."):
                    try:
                        result = start_session(user_question)
                        st.session_state.session_id = result['session_id']
                        st.session_state.current_question = result['question']
                        st.session_state.current_stage = result['stage']
                        st.session_state.alternatives = result.get('alternatives')
                        st.session_state.initial_message = user_question
                        st.session_state.question_count = 1 if result['stage'] == 'profession_details' else 0
                        st.session_state.step = 'clarification'
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")

# ===== ШАГ 2: Уточняющие вопросы =====
elif st.session_state.step == 'clarification':
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Показываем текущий вопрос
        stage_emoji = get_stage_emoji(st.session_state.current_stage)
        stage_label = get_stage_label(st.session_state.current_stage)

        st.markdown(f"### {stage_emoji} {stage_label}")

        # Если есть альтернативы (нереальная профессия)
        if st.session_state.alternatives:
            st.markdown(f"**{st.session_state.current_question}**")
            st.markdown("---")

            for alt in st.session_state.alternatives:
                if st.button(
                    f"🎯 {alt}",
                    key=f"alt_{alt}",
                    use_container_width=True
                ):
                    with st.spinner("⏳ Обрабатываю выбор..."):
                        try:
                            result = submit_answer(st.session_state.session_id, alt)

                            # Проверяем, вернулся ли профиль или следующий вопрос
                            if 'position_title' in result:
                                # Это профиль
                                st.session_state.profile = result
                                st.session_state.step = 'result'
                            else:
                                # Это следующий вопрос
                                st.session_state.current_question = result['question']
                                st.session_state.current_stage = result['stage']
                                st.session_state.alternatives = result.get('alternatives')

                                if result['stage'] == 'profession_details':
                                    st.session_state.question_count += 1

                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ошибка: {str(e)}")

        # Обычный вопрос
        else:
            st.markdown(f"**{st.session_state.current_question}**")

            user_answer = st.text_input(
                "Ваш ответ:",
                placeholder="Напишите ваш ответ...",
                key="answer_input"
            )

            if st.button("➡️ Ответить", type="primary", use_container_width=True):
                if len(user_answer.strip()) < 1:
                    st.error("⚠️ Пожалуйста, введите ответ")
                else:
                    with st.spinner("⏳ Обрабатываю ответ..."):
                        try:
                            result = submit_answer(st.session_state.session_id, user_answer)

                            # Проверяем, вернулся ли профиль или следующий вопрос
                            if 'position_title' in result:
                                # Это финальный профиль
                                st.session_state.profile = result
                                st.session_state.step = 'result'
                            else:
                                # Это следующий вопрос
                                st.session_state.current_question = result['question']
                                st.session_state.current_stage = result['stage']
                                st.session_state.alternatives = result.get('alternatives')

                                if result['stage'] == 'profession_details':
                                    st.session_state.question_count += 1

                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ошибка: {str(e)}")

# ===== ШАГ 3: Результат =====
elif st.session_state.step == 'result':
    if st.session_state.profile:
        profile = st.session_state.profile

        # Заголовок профессии
        st.markdown(f"## 🎯 {profile['position_title']}")
        st.markdown("---")

        # Основная информация в 3 колонки
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 🎵 Звуки рабочего дня")
            for sound in profile['sounds']:
                st.markdown(f'<div class="sound-item">🔊 {sound}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown("### 📈 Карьерный рост")
            st.markdown(f'<div class="card"><h4>{profile["career_growth"]}</h4></div>', unsafe_allow_html=True)

        with col3:
            st.markdown("### ⚖️ Work-Life Balance")
            st.markdown(f'<div class="card"><h4>{profile["balance_score"]}</h4></div>', unsafe_allow_html=True)

        # Польза
        st.markdown("### 💎 Главная ценность")
        st.info(profile['benefit'])

        # Типичный день
        st.markdown("### 📅 Типичный рабочий день")
        st.markdown(f'<div class="typical-day-text">{profile["typical_day"]}</div>', unsafe_allow_html=True)

        # Реальные задачи
        st.markdown("### 🎯 Реальные задачи")
        for case in profile['real_cases']:
            difficulty_class = get_difficulty_class(case['difficulty'])
            st.markdown(f"""
            <div class="case-card {case['difficulty']}">
                <span class="difficulty-badge {difficulty_class}">{case['difficulty'].upper()}</span>
                <h4>{case['title']}</h4>
                <p>{case['description']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Технологии и визуал
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🛠️ Технологический стек")
            for tech in profile['tech_stack']:
                st.markdown(f'<span class="tech-badge">{tech}</span>', unsafe_allow_html=True)

        with col2:
            st.markdown("### 🎨 Что увидишь на экране")
            for visual in profile['visual']:
                st.markdown(f"- {visual}")

        # Кнопка для нового поиска
        st.markdown("---")
        if st.button("🔍 Изучить другую профессию", type="primary", use_container_width=True):
            reset_session()
            st.rerun()

    else:
        st.error("Профиль не найден")
        if st.button("🔄 Начать заново"):
            reset_session()
            st.rerun()
