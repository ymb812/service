# File: streamlit_app.py

import streamlit as st
import requests
from typing import Optional
from settings.settings import settings
import random

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
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Оптимизированные стили
st.markdown("""
<style>
    /* CSS переменные */
    :root {
        --primary: #667eea;
        --primary-light: rgba(102, 126, 234, 0.08);
        --primary-border: rgba(102, 126, 234, 0.3);
        --success: #28a745;
        --warning: #ffc107;
        --danger: #dc3545;
        --text-secondary: #6c757d;
        --border-radius: 12px;
        --spacing: 1.5rem;
        --transition: all 0.2s ease;
    }

    /* Базовая типографика */
    .main .block-container {
        max-width: 920px;
        padding: 2rem 1rem;
    }

    /* Заголовки */
    .app-header {
        text-align: center;
        margin-bottom: 3rem;
    }

    .app-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .app-subtitle {
        font-size: 1.15rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    /* Универсальная карточка */
    .info-card {
        background: var(--primary-light);
        border: 1px solid var(--primary-border);
        border-radius: var(--border-radius);
        padding: var(--spacing);
        margin: 1rem 0;
        transition: var(--transition);
        overflow-wrap: break-word;
        word-wrap: break-word;
        word-break: break-word;
    }

    .info-card:hover {
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.12);
        border-color: var(--primary);
    }

    /* Метрики (вместо st.metric) */
    .metric-card {
        background: white;
        border: 1px solid var(--primary-border);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        text-align: center;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--primary);
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    /* Секции профиля */
    .section {
        margin: 2.5rem 0;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--primary);
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid var(--primary-light);
    }

    /* Звуки */
    .sounds-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.75rem;
        margin-top: 1rem;
    }

    .sound-item {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 152, 0, 0.1) 100%);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 8px;
        padding: 0.875rem;
        font-size: 0.95rem;
        transition: var(--transition);
        text-align: center;
    }

    .sound-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(255, 193, 7, 0.2);
    }

    /* Типичный день */
    .day-description {
        background: white;
        border: 1px solid var(--primary-border);
        border-left: 4px solid var(--primary);
        border-radius: var(--border-radius);
        padding: var(--spacing);
        line-height: 1.8;
        font-size: 1.05rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        white-space: pre-wrap;
        word-wrap: break-word;
        min-height: 400px;
    }

    /* Типичный день */
    .day-description {
        background: white;
        border: 1px solid var(--primary-border);
        border-left: 4px solid var(--primary);
        border-radius: var(--border-radius);
        padding: var(--spacing);
        line-height: 1.8;
        font-size: 1.05rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        white-space: pre-wrap;
        word-wrap: break-word;
        height: 600px; /* Фиксированная высота */
        overflow-y: auto; /* Прокрутка, если текст длинный */
    }
    
    .day-description::-webkit-scrollbar {
        width: 6px;
    }
    
    .day-description::-webkit-scrollbar-track {
        background: var(--primary-light);
        border-radius: 3px;
    }
    
    .day-description::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 3px;
    }
    
    /* Стили для изображений в контейнере */
    [data-testid="stVerticalBlock"] img {
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 12px;
        transition: var(--transition);
    }
    
    [data-testid="stVerticalBlock"] img:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }


    /* Диалоги */
    .dialog-card {
        background: white;
        border: 1px solid var(--primary-border);
        border-radius: var(--border-radius);
        padding: var(--spacing);
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }

    .dialog-header {
        font-weight: 600;
        color: var(--primary);
        margin-bottom: 1rem;
        font-size: 1.05rem;
    }

    .dialog-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.75rem 0;
        line-height: 1.6;
    }

    .dialog-request {
        background: #f8f9fa;
        border-left: 3px solid var(--primary);
    }

    .dialog-request strong {
        color: var(--primary);
    }

    .dialog-response {
        background: var(--primary-light);
        border-left: 3px solid var(--success);
    }

    .dialog-response strong {
        color: var(--success);
    }

    .dialog-vibe {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-style: italic;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
    }

    /* Задачи */
    .task-card {
        background: white;
        border: 1px solid #dee2e6;
        border-left-width: 4px;
        border-radius: var(--border-radius);
        padding: 1.25rem;
        margin: 0.875rem 0;
        transition: var(--transition);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }

    .task-card:hover {
        transform: translateX(6px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    .task-card.easy { border-left-color: var(--success); }
    .task-card.medium { border-left-color: var(--warning); }
    .task-card.hard { border-left-color: var(--danger); }

    .task-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .task-title {
        font-weight: 600;
        font-size: 1.05rem;
        margin: 0.5rem 0;
        color: #2c3e50;
    }

    .task-description {
        color: var(--text-secondary);
        line-height: 1.7;
    }

    /* Бейджи */
    .badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .badge-primary { background: var(--primary); color: white; }
    .badge-success { background: var(--success); color: white; }
    .badge-warning { background: var(--warning); color: #000; }
    .badge-danger { background: var(--danger); color: white; }

    /* Технологии */
    .tech-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.75rem;
    }

    .tech-tag {
        background: var(--primary);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        transition: var(--transition);
    }

    .tech-tag:hover {
        background: #5568d3;
        transform: scale(1.05);
    }

    /* Списки */
    .styled-list {
        background: white;
        border: 1px solid var(--primary-border);
        border-radius: var(--border-radius);
        padding: 1.25rem 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }

    .styled-list ul {
        margin: 0;
        padding-left: 1.5rem;
    }

    .styled-list li {
        margin: 0.625rem 0;
        line-height: 1.7;
    }

    /* Прогресс в сайдбаре */
    .progress-info {
        background: var(--primary-light);
        border-radius: 8px;
        padding: 0.75rem;
        text-align: center;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }

    /* Альтернативы */
    .alternative-option {
        background: white;
        border: 2px solid var(--primary-border);
        border-radius: var(--border-radius);
        padding: 1rem 1.25rem;
        margin: 0.625rem 0;
        cursor: pointer;
        transition: var(--transition);
        font-size: 1rem;
    }

    .alternative-option:hover {
        border-color: var(--primary);
        background: var(--primary-light);
        transform: translateX(6px);
    }

    /* Streamlit компоненты */
    .stButton > button {
        border-radius: var(--border-radius);
        font-weight: 500;
        transition: var(--transition);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: var(--border-radius);
    }

    /* Разделители */
    hr {
        border: none;
        border-top: 1px solid var(--primary-border);
        margin: 2rem 0;
    }

    /* Адаптивность */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2rem;
        }

        .sounds-grid {
            grid-template-columns: 1fr;
        }

        .metric-value {
            font-size: 1.1rem;
        }

        .images-scroll-container {
            max-height: 400px;
        }
    }

    /* Тёмная тема */
    @media (prefers-color-scheme: dark) {
        .metric-card,
        .day-description,
        .dialog-card,
        .task-card,
        .styled-list,
        .alternative-option {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.1);
        }

        .dialog-request {
            background: rgba(255, 255, 255, 0.03);
        }

        .task-title {
            color: #e0e0e0;
        }
    }

    /* Фикс переполнения */
    * {
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)


# API функции
def check_api_health() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5, headers=HEADERS)
        return response.status_code == 200
    except:
        return False


def start_session(user_message: str, user_id: Optional[int] = None) -> dict:
    payload = {"user_message": user_message, "user_id": user_id}
    response = requests.post(f"{API_BASE_URL}/start", json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def submit_answer(session_id: int, answer: str) -> dict:
    payload = {"session_id": session_id, "answer": answer}
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
    st.session_state.step = 'initial'
    st.session_state.session_id = None
    st.session_state.current_question = None
    st.session_state.current_stage = None
    st.session_state.alternatives = None
    st.session_state.profile = None
    st.session_state.initial_message = ""
    st.session_state.question_count = 0


def get_stage_label(stage: str) -> str:
    labels = {
        'profession_check': 'Проверка профессии',
        'profession_alternatives': 'Выбор альтернативы',
        'profession_details': 'Уточнение деталей',
        'vibe_question': 'Общий вайб'
    }
    return labels.get(stage, 'Уточнение')


# Заголовок приложения (показываем только НЕ на странице результата)
if st.session_state.step != 'result':
    st.markdown('''
    <div class="app-header">
        <div class="app-title">🎯 Career Explorer</div>
        <div class="app-subtitle">Узнай реальный вайб различных профессий</div>
    </div>
    ''', unsafe_allow_html=True)

# Сайдбар
with st.sidebar:
    st.markdown("### ⚙️ Настройки")

    if check_api_health():
        st.success("✅ API доступен")
    else:
        st.error("❌ API недоступен")

    if st.button("🔄 Начать заново", use_container_width=True):
        reset_session()
        st.rerun()

    # Прогресс
    if st.session_state.step not in ['initial', 'result']:
        st.divider()
        st.markdown("**📊 Прогресс**")

        if st.session_state.current_stage:
            stage_label = get_stage_label(st.session_state.current_stage)
            st.info(stage_label)

        if st.session_state.current_stage == 'profession_details':
            st.progress(st.session_state.question_count / 2)
            st.caption(f"Вопрос {st.session_state.question_count} из 2")

# ===== ШАГ 1: Начальный вопрос =====
if st.session_state.step == 'initial':
    st.markdown("### 💬 О какой профессии хотите узнать?")

    with st.expander("💡 Примеры вопросов"):
        st.markdown("""
        - **Frontend-разработчик** в стартапе
        - **DevOps-инженер** в крупной компании
        - **UX/UI дизайнер** в продуктовой команде
        - **Product Manager** в B2B сегменте
        - **Data Scientist** в финтехе
        - **Backend-разработчик** на Python
        """)

    user_question = st.text_area(
        "Ваш вопрос:",
        height=120,
        placeholder="Например: Хочу быть DevOps-инженером в стартапе...",
        value=st.session_state.initial_message,
        max_chars=500
    )

    if st.button("🔍 Узнать подробности", type="primary", use_container_width=True):
        if len(user_question.strip()) < 5:
            st.error("⚠️ Вопрос слишком короткий (минимум 5 символов)")
        else:
            with st.spinner("🔄 Анализирую профессию..."):
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
    stage_label = get_stage_label(st.session_state.current_stage)
    st.markdown(f"### 📋 {stage_label}")

    st.markdown(f"**{st.session_state.current_question}**")
    st.divider()

    # Альтернативы (если профессия нереальная)
    if st.session_state.alternatives:
        st.info("Выберите одну из реальных профессий:")

        for alt in st.session_state.alternatives:
            if st.button(f"🎯 {alt}", key=f"alt_{alt}", use_container_width=True):
                with st.spinner("⏳ Обрабатываю выбор..."):
                    try:
                        result = submit_answer(st.session_state.session_id, alt)

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

        st.divider()

        custom_profession = st.text_input(
            "Или введите свой вариант:",
            placeholder="Например: Data Analyst, Product Designer...",
            max_chars=100
        )

        if st.button("✍️ Выбрать свой вариант", type="secondary", use_container_width=True):
            if len(custom_profession.strip()) < 3:
                st.error("⚠️ Название слишком короткое")
            else:
                with st.spinner("⏳ Обрабатываю..."):
                    try:
                        result = submit_answer(st.session_state.session_id, custom_profession)

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
                        st.error(f"❌ {str(e)}")

    # Обычный вопрос
    else:
        user_answer = st.text_input(
            "Ваш ответ:",
            placeholder="Введите ваш ответ...",
            max_chars=300
        )

        if st.button("➡️ Ответить", type="primary", use_container_width=True):
            if not user_answer.strip():
                st.error("⚠️ Пожалуйста, введите ответ")
            else:
                with st.spinner("⏳ Обрабатываю ответ..."):
                    try:
                        result = submit_answer(st.session_state.session_id, user_answer)

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
                        st.error(f"❌ {str(e)}")


# ===== ШАГ 3: Результат =====
elif st.session_state.step == 'result':
    if not st.session_state.profile:
        st.error("❌ Профиль не найден")
        if st.button("🔄 Начать заново"):
            reset_session()
            st.rerun()
    else:
        profile = st.session_state.profile

        # Заголовок профессии
        st.markdown(f"## 🎯 {profile['position_title']}")
        st.divider()

        # ============================================================
        # БЛОК 1: ВАЙБ ПРОФЕССИИ
        # ============================================================
        st.markdown('''
        <div style="text-align: center; margin: 2rem 0;">
            <h2 style="color: var(--primary); font-size: 2rem; margin-bottom: 0.5rem;">
                ✨ Вайб профессии
            </h2>
            <p style="color: var(--text-secondary); font-size: 1.1rem;">
                Атмосфера и ощущения от работы
            </p>
        </div>
        ''', unsafe_allow_html=True)

        # Главная польза (расширенный дизайн)
        st.markdown(f'''
        <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                    border: 2px solid var(--primary-border);
                    border-radius: 16px;
                    padding: 2rem;
                    margin: 1.5rem 0;
                    text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">💎</div>
            <div style="font-size: 1.3rem; font-weight: 600; color: var(--primary); margin-bottom: 0.75rem;">
                Главная ценность профессии
            </div>
            <div style="font-size: 1.1rem; line-height: 1.7; color: #2c3e50;">
                {profile['benefit']}
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Типичный день
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📅 Типичный рабочий день</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: var(--text-secondary); margin-bottom: 1rem;">Как выглядит твой день от утреннего кофе до вечера</p>',
            unsafe_allow_html=True)

        # Получаем изображения из профиля или используем дефолтные
        day_images = profile.get('day_images', [
            "https://im.runware.ai/image/ws/2/ii/ff54db2f-e0d2-4877-b0af-b2590726b8f6.jpg",
            "https://im.runware.ai/image/ws/2/ii/9d30009a-3ef0-4d80-8934-4e5e962d1852.jpg",
            "https://im.runware.ai/image/ws/2/ii/721af4ac-0ae9-41da-aad3-abd8c110cfef.jpg"
        ])

        # Создаём две колонки
        col_text, col_images = st.columns([1.8, 1])

        with col_text:
            st.markdown(f'<div class="day-description">{profile["typical_day"]}</div>', unsafe_allow_html=True)

        with col_images:
            # Используем st.container с height для прокрутки
            with st.container(height=600):
                for idx, img_url in enumerate(day_images, 1):
                    st.image(
                        img_url,
                        use_container_width=True,
                    )

        st.markdown('</div>', unsafe_allow_html=True)

        # Атмосфера рабочего дня (бывшие "Звуки")
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎧 Атмосфера рабочего дня</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: var(--text-secondary); margin-bottom: 1rem;">Что создаёт настроение и ритм твоего дня</p>',
            unsafe_allow_html=True)

        sounds_html = '<div class="sounds-grid">'
        for sound in profile['sounds']:
            sounds_html += f'<div class="sound-item">{sound}</div>'
        sounds_html += '</div>'

        st.markdown(sounds_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Диалоги с коллегами
        if 'chat_examples' in profile and profile['chat_examples']:
            st.markdown('<div class="section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">💬 Живое общение с коллегами</div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="color: var(--text-secondary); margin-bottom: 1rem;">Реальные диалоги, которые показывают стиль коммуникации</p>',
                unsafe_allow_html=True)

            for chat in profile['chat_examples'][:2]:
                st.markdown(f'''
                <div class="dialog-card">
                    <div class="dialog-header">👤 {chat['colleague']}</div>
                    <div class="dialog-message dialog-request">
                        <strong>📨 Запрос:</strong><br>
                        {chat['request']}
                    </div>
                    <div class="dialog-message dialog-response">
                        <strong>💬 Твой ответ:</strong><br>
                        {chat['your_response']}
                    </div>
                    <div class="dialog-vibe">💭 {chat['vibe']}</div>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # РАЗДЕЛИТЕЛЬ МЕЖДУ БЛОКАМИ
        # ============================================================
        st.markdown('''
        <div style="margin: 4rem 0 3rem 0; text-align: center;">
            <hr style="border: none; border-top: 2px solid var(--primary-border); margin-bottom: 2rem;">
            <div style="display: inline-block; background: white; padding: 1rem 2rem; border-radius: 50px; 
                        border: 2px solid var(--primary); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">📊</span>
                <span style="font-size: 1.3rem; font-weight: 600; color: var(--primary);">
                    Технические детали
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # ============================================================
        # БЛОК 2: ТЕХНИЧЕСКИЕ ДЕТАЛИ
        # ============================================================

        # Ключевые метрики
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📈 Ключевые показатели</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">📈 Карьерный рост</div>
                <div class="metric-value">{profile['career_growth']}</div>
            </div>
            ''', unsafe_allow_html=True)

        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">⚖️ Work-Life Balance</div>
                <div class="metric-value">{profile['balance_score']}</div>
            </div>
            ''', unsafe_allow_html=True)

        with col3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">💸 Средняя З/П</div>
                <div class="metric-value">{random.randint(50, 300)}К</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Реальные задачи
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Реальные задачи</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: var(--text-secondary); margin-bottom: 1rem;">Что именно ты будешь делать каждый день</p>',
            unsafe_allow_html=True)

        difficulty_config = {
            "easy": {"emoji": "🟢", "label": "ЛЕГКО"},
            "medium": {"emoji": "🟡", "label": "СРЕДНЕ"},
            "hard": {"emoji": "🔴", "label": "СЛОЖНО"}
        }

        for i, case in enumerate(profile['real_cases'], 1):
            diff = difficulty_config.get(case['difficulty'], {"emoji": "⚪", "label": "?"})

            st.markdown(f'''
            <div class="task-card {case['difficulty']}">
                <div class="task-header">
                    <span style="font-size: 1.3rem;">{diff['emoji']}</span>
                    <span class="badge badge-{case['difficulty'][:4]}">{diff['label']}</span>
                </div>
                <div class="task-title">#{i}. {case['title']}</div>
                <div class="task-description">{case['description']}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Технологии и визуал
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🛠️ Технологии</div>', unsafe_allow_html=True)
            st.markdown('<p style="color: var(--text-secondary); margin-bottom: 1rem;">Инструменты твоей работы</p>',
                        unsafe_allow_html=True)

            tech_html = '<div class="tech-tags">'
            for tech in profile['tech_stack']:
                tech_html += f'<span class="tech-tag">{tech}</span>'
            tech_html += '</div>'

            st.markdown(tech_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="section">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🎨 Рабочее окружение</div>', unsafe_allow_html=True)
            st.markdown('<p style="color: var(--text-secondary); margin-bottom: 1rem;">Что будет на твоём экране</p>',
                        unsafe_allow_html=True)

            visual_html = '<div class="styled-list"><ul>'
            for visual in profile['visual']:
                visual_html += f'<li>{visual}</li>'
            visual_html += '</ul></div>'

            st.markdown(visual_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Честно о профессии
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💬 Честно о профессии</div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: var(--text-secondary); margin-bottom: 1rem;">Взвешенный взгляд на плюсы и минусы</p>',
            unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            pros = profile.get('pros', 'Творчество, развитие, результат')
            st.success(f"**✅ За что полюбишь**\n\n{pros}")

        with col2:
            cons = profile.get('cons', 'Дедлайны, правки, стресс')
            st.warning(f"**⚠️ К чему готовиться**\n\n{cons}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Кнопка для нового поиска
        st.divider()
        if st.button("🔍 Изучить другую профессию", type="primary", use_container_width=True):
            reset_session()
            st.rerun()
