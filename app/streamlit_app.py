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
    page_title="Career Explorer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Кастомные стили
# Кастомные стили с анимациями
st.markdown("""
<style>
    /* Анимации */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }

    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    @keyframes gradientShift {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }

    /* Применение анимаций */
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 3s ease infinite;
    }

    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        margin-bottom: 3rem;
        animation: fadeIn 1s ease-out;
    }

    .card {
        background: rgba(102, 126, 234, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        animation: slideInLeft 0.5s ease-out;
        transition: all 0.3s ease;
    }

    .card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .card h4 {
        color: inherit;
        margin: 0;
    }

    .alternative-card {
        background: rgba(102, 126, 234, 0.05);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-left: 3px solid #667eea;
        animation: fadeIn 0.5s ease-out backwards;
    }

    .alternative-card:nth-child(1) { animation-delay: 0.1s; }
    .alternative-card:nth-child(2) { animation-delay: 0.2s; }
    .alternative-card:nth-child(3) { animation-delay: 0.3s; }
    .alternative-card:nth-child(4) { animation-delay: 0.4s; }
    .alternative-card:nth-child(5) { animation-delay: 0.5s; }

    .alternative-card:hover {
        transform: translateX(10px) scale(1.02);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        border-left-width: 5px;
    }

    .case-card {
        background: rgba(40, 167, 69, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #28a745;
        animation: slideInLeft 0.6s ease-out;
        transition: all 0.3s ease;
    }

    .case-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }

    .case-card.medium {
        background: rgba(255, 193, 7, 0.1);
        border-left-color: #ffc107;
    }

    .case-card.hard {
        background: rgba(220, 53, 69, 0.1);
        border-left-color: #dc3545;
    }

    .case-card h4 {
        color: inherit;
        margin-top: 0.5rem;
    }

    .case-card p {
        color: inherit;
        margin-bottom: 0;
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
        background: #28a745;
        color: white;
    }

    .difficulty-medium {
        background: #ffc107;
        color: #000;
    }

    .difficulty-hard {
        background: #dc3545;
        color: white;
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
        animation: fadeIn 0.5s ease-out backwards;
        transition: all 0.2s ease;
    }

    .tech-badge:hover {
        transform: scale(1.1);
        background: #764ba2;
    }

    .tech-badge:nth-child(1) { animation-delay: 0.1s; }
    .tech-badge:nth-child(2) { animation-delay: 0.15s; }
    .tech-badge:nth-child(3) { animation-delay: 0.2s; }
    .tech-badge:nth-child(4) { animation-delay: 0.25s; }
    .tech-badge:nth-child(5) { animation-delay: 0.3s; }
    .tech-badge:nth-child(6) { animation-delay: 0.35s; }
    .tech-badge:nth-child(7) { animation-delay: 0.4s; }
    .tech-badge:nth-child(8) { animation-delay: 0.45s; }

    .sound-item {
        background: rgba(255, 193, 7, 0.2);
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #ffc107;
        color: inherit;
        animation: slideInLeft 0.5s ease-out backwards;
        transition: all 0.3s ease;
    }

    .sound-item:nth-child(1) { animation-delay: 0.1s; }
    .sound-item:nth-child(2) { animation-delay: 0.2s; }
    .sound-item:nth-child(3) { animation-delay: 0.3s; }

    .sound-item:hover {
        transform: translateX(5px);
        border-left-width: 5px;
    }

    .progress-indicator {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
        animation: fadeIn 0.5s ease-out;
    }

    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 8px;
        border-radius: 4px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        animation: shimmer 2s infinite;
    }

    .typical-day-text {
        background: rgba(102, 126, 234, 0.05);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        line-height: 1.8;
        color: inherit;
        margin: 1rem 0;
        animation: fadeIn 0.8s ease-out;
        transition: all 0.3s ease;
    }

    .typical-day-text:hover {
        background: rgba(102, 126, 234, 0.1);
        transform: scale(1.01);
    }

    .divider-text {
        text-align: center;
        color: #999;
        margin: 1.5rem 0;
        font-size: 0.9rem;
        animation: pulse 2s ease-in-out infinite;
    }

    /* Анимация для кнопок Streamlit */
    .stButton > button {
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }

    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }

    /* Поддержка тёмной темы */
    @media (prefers-color-scheme: dark) {
        .subtitle {
            color: #aaa;
        }

        .card {
            background: rgba(102, 126, 234, 0.15);
        }

        .alternative-card {
            background: rgba(102, 126, 234, 0.1);
        }

        .case-card {
            background: rgba(40, 167, 69, 0.15);
        }

        .case-card.medium {
            background: rgba(255, 193, 7, 0.15);
        }

        .case-card.hard {
            background: rgba(220, 53, 69, 0.15);
        }

        .sound-item {
            background: rgba(255, 193, 7, 0.25);
        }

        .typical-day-text {
            background: rgba(102, 126, 234, 0.1);
        }
    }

    /* Fade-in для всей страницы */
    .main .block-container {
        animation: fadeIn 0.5s ease-out;
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
st.markdown('<div class="subtitle">Узнай вайб различных профессий</div>', unsafe_allow_html=True)

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
            st.markdown(f"**Вопрос:** {st.session_state.question_count}/2")
            progress = st.session_state.question_count / 2
            st.progress(progress)

    st.divider()
    st.caption("Версия 2.0 • Multi-step clarification")

# ===== ШАГ 1: Начальный вопрос =====
if st.session_state.step == 'initial':
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 💬 О какой профессии вы хотите узнать?")

        # Примеры вопросов
        with st.expander("💡 Примеры вопросов"):
            st.markdown("""
            - Каково это — быть frontend-разработчиком в стартапе?
            - Что делает DevOps-инженер в крупной компании?
            - Хочу быть врачом-хирургом
            - Расскажи про профессию учителя математики
            - Интересует работа журналиста в СМИ
            - Как работает шеф-повар в ресторане?
            - Что делает маркетолог в digital-агентстве?
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

            st.markdown("#### Выберите из предложенных:")

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

            # Добавляем разделитель
            st.markdown('<div class="divider-text">— или введите свой вариант —</div>', unsafe_allow_html=True)

            # Поле для ввода своего варианта
            custom_profession = st.text_input(
                "Или введите другую профессию:",
                placeholder="Например: Архитектор, Психолог, Data Scientist...",
                key="custom_profession_input"
            )

            if st.button("✍️ Выбрать свой вариант", type="secondary", use_container_width=True):
                if len(custom_profession.strip()) < 3:
                    st.error("⚠️ Название профессии слишком короткое")
                else:
                    with st.spinner("⏳ Обрабатываю ваш вариант..."):
                        try:
                            result = submit_answer(st.session_state.session_id, custom_profession)

                            # Проверяем, вернулся ли профиль или следующий вопрос
                            if 'position_title' in result:
                                st.session_state.profile = result
                                st.session_state.step = 'result'
                            else:
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
            st.markdown("### 🛠️ Инструменты и навыки")
            for tech in profile['tech_stack']:
                st.markdown(f'<span class="tech-badge">{tech}</span>', unsafe_allow_html=True)

        with col2:
            st.markdown("### 🎨 Что увидишь в работе")
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
