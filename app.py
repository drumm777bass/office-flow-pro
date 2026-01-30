import streamlit as st
import pandas as pd
import os
import plotly.express as px
from io import BytesIO
import socket
from datetime import date

# --- 0. СИСТЕМА ПАРОЛЯ ---
def check_password():
    """Возвращает True, если введен правильный пароль."""
    def password_entered():
        # ЗДЕСЬ МОЖНО ИЗМЕНИТЬ ПАРОЛЬ
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Удаляем пароль из состояния для безопасности
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Экран первого входа
        st.title("🔐 Доступ ограничен")
        st.text_input("Введите пароль для работы с Office Flow", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Экран при ошибке
        st.title("🔐 Доступ ограничен")
        st.text_input("Неверный пароль. Попробуйте еще раз", type="password", on_change=password_entered, key="password")
        st.error("😕 Доступ запрещен")
        return False
    else:
        # Пароль верный
        return True

if not check_password():
    st.stop() # Останавливаем выполнение кода, пока нет пароля

# --- 1. СЕТЕВОЙ АДРЕС ---
def get_office_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

# --- 2. КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Office Flow Pro", layout="wide")

# --- 3. ДИЗАЙН (SLATE & AZURE) ---
with st.sidebar:
    st.markdown("### 🎨 Тема оформления")
    theme_mode = st.toggle("Светлая тема", value=False)
    if st.button("🚪 Выйти из системы"):
        st.session_state.clear()
        st.rerun()

if theme_mode:
    bg_style, text_color, accent_color, table_bg = "#f8fafc", "#1e293b", "#3b82f6", "#ffffff"
    card_bg, border_color = "rgba(0, 0, 0, 0.02)", "#e2e8f0"
else:
    bg_style, text_color, accent_color, table_bg = "#0f172a", "#f1f5f9", "#60a5fa", "#1e293b"
    card_bg, border_color = "rgba(255, 255, 255, 0.03)", "#334155"

st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; color: {text_color}; }}
    div[data-testid="stDataEditor"] {{ background-color: {table_bg} !important; border-radius: 8px; border: 1px solid {border_color}; }}
    .stTabs [data-baseweb="tab-list"] button p {{ font-size: 18px !important; font-weight: 600 !important; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {card_bg} !important; border: 1px solid {border_color} !important;
        border-radius: 12px !important; padding: 20px !important;
    }}
    .stButton>button {{
        height: 45px !important; border-radius: 8px !important; width: 100%;
        background: {accent_color}10 !important; color: {accent_color} !important;
        border: 1px solid {accent_color} !important; font-weight: 600;
    }}
    [data-testid="stMetricValue"] {{ color: {accent_color} !important; font-weight: 800; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. ДАННЫЕ ---
DB_FILE = 'tasks.csv'
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if 'Дедлайн' not in df.columns: df['Дедлайн'] = str(date.today())
        df['Дедлайн'] = pd.to_datetime(df['Дедлайн']).dt.date
        return df
    return pd.DataFrame(columns=['Задача', 'Исполнитель', 'Статус', 'Приоритет', 'Дедлайн'])

if 'df' not in st.session_state:
    st.session_state.df = load_data()
all_data = st.session_state.df

# --- 5. УПРАВЛЕНИЕ (БОКОВАЯ ПАНЕЛЬ) ---
with st.sidebar:
    st.info(f"🔗 Доступ: http://{get_office_ip()}:8501")
    if not all_data.empty:
        st.divider()
        st.markdown("### ⚙️ Администрирование")
        all_emps = sorted(all_data['Исполнитель'].unique())

        with st.expander("📝 Переименовать"):
            target = st.selectbox("Сотрудник", all_emps, key="r1")
            new_n = st.text_input("Новое имя")
            if st.button("ОБНОВИТЬ"):
                all_data.loc[all_data['Исполнитель'] == target, 'Исполнитель'] = new_n
                all_data.to_csv(DB_FILE, index=False); st.session_state.df = all_data; st.rerun()

        with st.expander("🔄 Перенос задач"):
            f_e = st.selectbox("От кого:", all_emps, key="m1")
            emp_tasks = all_data[all_data['Исполнитель'] == f_e]['Задача'].tolist()
            if emp_tasks:
                task_to_move = st.selectbox("Задача:", emp_tasks, key="m_task")
                t_e = st.selectbox("Кому:", all_emps, key="m2")
                if st.button("ПЕРЕНЕСТИ ВЫБРАННУЮ ЗАДАЧУ"):
                    idx = all_data[(all_data['Исполнитель'] == f_e) & (all_data['Задача'] == task_to_move)].index[0]
                    all_data.at[idx, 'Исполнитель'] = t_e
                    all_data.to_csv(DB_FILE, index=False); st.session_state.df = all_data; st.rerun()
            else:
                st.warning("Нет активных задач.")

        with st.expander("🗑️ Удаление сотрудника"):
            d_e = st.selectbox("Выбрать", all_emps, key="d1")
            if st.checkbox("Подтверждаю") and st.button("УДАЛИТЬ"):
                all_data = all_data[all_data['Исполнитель'] != d_e]
                all_data.to_csv(DB_FILE, index=False); st.session_state.df = all_data; st.rerun()

# --- 6. ОСНОВНОЙ ИНТЕРФЕЙС ---
st.title("📊 Office Flow Professional Watafa Pepe")
tab_tasks, tab_charts = st.tabs(["📋 ПАНЕЛЬ ЗАДАЧ", "📈 АНАЛИТИКА"])

with tab_tasks:
    all_data['Дедлайн'] = pd.to_datetime(all_data['Дедлайн']).dt.date
    active_tasks = all_data[all_data['Статус'] != '🟢 Выполнено'].copy()
    archived_tasks = all_data[all_data['Статус'] == '🟢 Выполнено'].copy()

    col_l, col_r = st.columns([1, 2.5], gap="large")
    with col_l:
        with st.container(border=True):
            st.markdown("#### ➕ Новая задача")
            n_t = st.text_input("Название")
            n_u = st.text_input("Исполнитель")
            n_d = st.date_input("Дедлайн", value=date.today())
            n_p = st.selectbox("Важность", ["Высокий 🔥", "Средний ⚡", "Низкий 🧊"], index=1)
            if st.button("СОЗДАТЬ"):
                if n_t and n_u:
                    new_row = pd.DataFrame([{'Задача': n_t, 'Исполнитель': n_u, 'Статус': '🔴 Ожидает', 'Приоритет': n_p, 'Дедлайн': n_d}])
                    all_data = pd.concat([all_data, new_row], ignore_index=True)
                    all_data.to_csv(DB_FILE, index=False); st.session_state.df = all_data; st.rerun()

    with col_r:
        if not active_tasks.empty:
            emps = sorted(active_tasks['Исполнитель'].unique())
            user_tabs = st.tabs(emps)
            for i, emp in enumerate(emps):
                with user_tabs[i]:
                    p_df = active_tasks[active_tasks['Исполнитель'] == emp].copy()
                    p_df = p_df.drop(columns=['Исполнитель'])
                    p_map = {'Высокий 🔥': 0, 'Средний ⚡': 1, 'Низкий 🧊': 2}
                    p_df['rank'] = p_df['Приоритет'].map(p_map)
                    p_df = p_df.sort_values('rank').drop(columns=['rank'])

                    edited = st.data_editor(p_df, use_container_width=True, num_rows="dynamic", key=f"e_{emp}",
                        column_config={
                            "Статус": st.column_config.SelectboxColumn(options=["🔴 Ожидает", "🟡 В работе", "🟢 Выполнено"]),
                            "Приоритет": st.column_config.SelectboxColumn(options=["Высокий 🔥", "Средний ⚡", "Низкий 🧊"]),
                            "Дедлайн": st.column_config.DateColumn("Дедлайн", format="DD.MM.YYYY")
                        })

                    if st.button("💾 СОХРАНИТЬ", key=f"s_{emp}"):
                        edited['Исполнитель'] = emp
                        others = all_data[all_data['Исполнитель'] != emp]
                        emp_arch = archived_tasks[archived_tasks['Исполнитель'] == emp]
                        updated = pd.concat([others, emp_arch, edited], ignore_index=True)
                        updated.to_csv(DB_FILE, index=False); st.session_state.df = updated; st.rerun()
        else:
            st.info("Активных задач нет.")

    st.divider()
    with st.expander("📦 АРХИВ И ПОИСК"):
        if not archived_tasks.empty:
            search = st.text_input("🔍 Поиск по архиву:", "").lower()
            filt_arch = archived_tasks[archived_tasks['Задача'].str.lower().str.contains(search, na=False) |
                                       archived_tasks['Исполнитель'].str.lower().str.contains(search, na=False)]
            ed_arch = st.data_editor(filt_arch, use_container_width=True, num_rows="dynamic", key="ae")
            if st.button("🔄 ПРИМЕНИТЬ ИЗМЕНЕНИЯ"):
                others = all_data.drop(archived_tasks.index)
                final = pd.concat([others, ed_arch], ignore_index=True)
                final.to_csv(DB_FILE, index=False); st.session_state.df = final; st.rerun()

with tab_charts:
    if not all_data.empty:
        st.markdown("### 📊 Общая статистика")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Всего", len(all_data))
        m2.metric("В работе", len(active_tasks))
        m3.metric("Завершено", len(archived_tasks))
        m4.metric("Срочные", len(all_data[all_data['Приоритет'] == "Высокий 🔥"]))

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(all_data, names='Статус', hole=0.4, title="Статусы", color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        with c2:
            if not active_tasks.empty:
                load = active_tasks['Исполнитель'].value_counts().reset_index()
                st.plotly_chart(px.bar(load, x='Исполнитель', y='count', title="Нагрузка", color_discrete_sequence=[accent_color]), use_container_width=True)

        st.divider()
        st.markdown("### 📥 Экспорт данных")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            all_data.to_excel(writer, index=False, sheet_name='Задачи')

        st.download_button(label="📊 СКАЧАТЬ EXCEL", data=output.getvalue(), file_name=f"report_{date.today()}.xlsx")
