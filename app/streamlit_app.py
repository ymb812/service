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

# Кастомные стили
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

    .schedule-item {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #2c3e50;
    }

    .schedule-item strong {
        color: #667eea;
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
if 'clarification_question' not in st.session_state:
    st.session_state.clarification_question = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'initial_message' not in st.session_state:
    st.session_state.initial_message = ""


def reset_session():
    """Сброс сессии"""
    st.session_state.step = 'initial'
    st.session_state.session_id = None
    st.session_state.clarification_question = None
    st.session_state.profile = None
    st.session_state.initial_message = ""


# Заголовок
st.markdown('<div class="main-title">🚀 IT Career Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Узнай, каково это — работать в IT</div>', unsafe_allow_html=True)

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

    st.divider()
    st.caption("Версия 1.0")

# ===== ШАГ 1: Начальный вопрос =====
if st.session_state.step == 'initial':
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 💬 Что вы хотите узнать о карьере в IT?")

        # Примеры вопросов
        with st.expander("💡 Примеры вопросов"):
            st.markdown("""
            - Каково это — быть frontend-разработчиком в стартапе?
            - Что делает DevOps-инженер в крупной компании?
            - Как работает Data Scientist в продуктовой команде?
            - Расскажи про карьеру QA-автоматизатора
            - Что входит в обязанности Tech Lead?
            """)

        user_question = st.text_area(
            "Ваш вопрос:",
            height=100,
            placeholder="Например: Каково это — быть backend-разработчиком в стартапе?",
            max_chars=500,
            value=st.session_state.initial_message
        )

        if st.button("🔍 Узнать подробности", type="primary", use_container_width=True):
            if len(user_question.strip()) < 10:
                st.error("⚠️ Вопрос слишком короткий. Напишите хотя бы 10 символов.")
            else:
                with st.spinner("🤔 Формирую уточняющий вопрос..."):
                    try:
                        result = start_session(user_question)
                        st.session_state.session_id = result['session_id']
                        st.session_state.clarification_question = result['question']
                        st.session_state.initial_message = user_question
                        st.session_state.step = 'clarification'
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")

# ===== ШАГ 2: Уточняющий вопрос =====
elif st.session_state.step == 'clarification':
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🎯 Уточните детали")

        st.info(f"**Ваш вопрос:** {st.session_state.initial_message}")

        st.markdown(f"""
        <div class="card">
            <h4>❓ {st.session_state.clarification_question}</h4>
        </div>
        """, unsafe_allow_html=True)

        user_answer = st.text_input(
            "Ваш ответ:",
            placeholder="Например: Больше креатива",
            max_chars=200
        )

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state.step = 'initial'
                st.rerun()

        with col_b:
            if st.button("✨ Создать профиль", type="primary", use_container_width=True):
                if len(user_answer.strip()) < 1:
                    st.error("⚠️ Пожалуйста, ответьте на вопрос.")
                else:
                    with st.spinner("🎨 Создаю ваш карьерный профиль... Это может занять до минуты."):
                        try:
                            profile = submit_answer(
                                st.session_state.session_id,
                                user_answer
                            )
                            st.session_state.profile = profile
                            st.session_state.step = 'result'
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ошибка: {str(e)}")

# ===== ШАГ 3: Результат =====
elif st.session_state.step == 'result':
    profile = st.session_state.profile

    # Заголовок профиля
    st.markdown(f"## 💼 {profile['position_title']}")

    st.divider()

    # Основная информация
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Карьерный путь")
        st.markdown(f"""
        <div class="card">
            <h4>{profile['career_growth']}</h4>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚖️ Work-Life Balance")
        balance = profile['balance_score']
        st.markdown(f"""
        <div class="card">
            <h2 style="text-align: center; color: #667eea;">{balance}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🎁 Главная польза")
        st.markdown(f"""
        <div class="card">
            <h4>{profile['benefit']}</h4>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Звуки рабочего дня
    st.markdown("### 🔊 Звуки рабочего дня")
    for sound in profile['sounds']:
        st.markdown(f"""
        <div class="sound-item">
            🎵 {sound}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Типичный день
    st.markdown("### 📅 Типичный рабочий день")

    for item in profile['typical_day']:
        st.markdown(f"""
        <div class="schedule-item">
            <strong>⏰ {item['time']}</strong><br>
            {item['activity']}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Технологии
    st.markdown("### 🛠️ Технологический стек")
    tech_html = "".join([f'<span class="tech-badge">{tech}</span>' for tech in profile['tech_stack']])
    st.markdown(tech_html, unsafe_allow_html=True)

    st.divider()

    # Визуализация
    st.markdown("### 🎨 Визуальная составляющая")
    for visual in profile['visual']:
        st.markdown(f"- 🖼️ {visual}")

    st.divider()

    # Действия
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Новый запрос", use_container_width=True):
            reset_session()
            st.rerun()

    with col2:
        # Экспорт в JSON
        json_data = json.dumps(profile, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Скачать JSON",
            data=json_data,
            file_name=f"career_profile_{profile['session_id']}.json",
            mime="application/json",
            use_container_width=True
        )

    with col3:
        # Копирование ID сессии
        if st.button("📋 ID сессии", use_container_width=True):
            st.code(f"Session ID: {profile['session_id']}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #999; padding: 2rem;">
    Made with ❤️ using Streamlit & Ollama<br>
    <small>Powered by AI for IT professionals</small>
</div>
""", unsafe_allow_html=True)
