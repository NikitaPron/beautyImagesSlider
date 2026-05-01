import streamlit as st
import pandas as pd
import random
import requests
from urllib.parse import urlparse, parse_qs
from io import StringIO
import time
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Казино Важных Дел", page_icon="🎰", layout="wide") # layout wide для удобства колонок

# Инициализация состояния сессии
if 'tasks_df' not in st.session_state:
    st.session_state.tasks_df = None
if 'current_task_index' not in st.session_state:
    st.session_state.current_task_index = None
if 'status_message' not in st.session_state:
    st.session_state.status_message = ""
if 'timer_start' not in st.session_state:
    st.session_state.timer_start = None
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

def get_gid_from_url(url):
    """Извлекает GID (ID листа) из ссылки Google Sheets"""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        gid = query_params.get('gid', ['0'])[0]
        return gid
    except:
        return '0'

def load_tasks_from_gsheet(url):
    """Загружает задачи из Google Sheets."""
    try:
        if '/d/' not in url:
            return None, "Неверная ссылка. Нужна ссылка на Google Таблицу."
        
        sheet_id = url.split('/d/')[1].split('/')[0]
        gid = get_gid_from_url(url)
        
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        
        response = requests.get(csv_url)
        response.raise_for_status() 
        
        csv_string = response.content.decode('utf-8')
        df_raw = pd.read_csv(StringIO(csv_string))
        
        if df_raw.empty:
            return None, "Лист пуст или не удалось прочитать данные."
            
        col_name = None
        cols_lower = {c.strip().lower(): c for c in df_raw.columns}
        
        if 'задачи' in cols_lower:
            col_name = cols_lower['задачи']
        elif 'task' in cols_lower:
            col_name = cols_lower['task']
        else:
            col_name = df_raw.columns[0]
            
        tasks_list = df_raw[col_name].dropna().astype(str).tolist()
        tasks_list = [t.strip() for t in tasks_list if t.strip() and len(t.strip()) > 1 and t.lower() != 'задачи']
        
        if not tasks_list:
            return None, "В колонке не найдено ни одной задачи."
            
        new_df = pd.DataFrame({
            "task": tasks_list,
            "count": [0] * len(tasks_list),
            "time_spent": [""] * len(tasks_list)
        })
        
        return new_df, f"Загружено {len(tasks_list)} задач."
        
    except Exception as e:
        return None, f"Ошибка: {str(e)}"

def get_random_task():
    if st.session_state.tasks_df is None or st.session_state.tasks_df.empty:
        return
    idx = random.randint(0, len(st.session_state.tasks_df) - 1)
    st.session_state.current_task_index = idx
    # Сброс таймера при выборе новой задачи
    st.session_state.timer_start = time.time()
    st.session_state.timer_running = True
    st.session_state.elapsed_time = 0
    st.session_state.last_update = time.time()
    st.session_state.status_message = "🎲 Новая задача выбрана!"

def complete_and_next():
    """Увеличивает счетчик, записывает время выполнения и сразу переключает на новую задачу."""
    if st.session_state.current_task_index is not None:
        idx = st.session_state.current_task_index
        
        # Вычисляем прошедшее время
        current_time = time.time()
        if st.session_state.timer_running and st.session_state.timer_start:
            elapsed = current_time - st.session_state.timer_start + st.session_state.elapsed_time
        else:
            elapsed = st.session_state.elapsed_time
        
        # Форматируем время в ММ:СС
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        time_str = f"{minutes}:{seconds:02d}"
        
        # Обновляем счетчик
        current_count = st.session_state.tasks_df.at[idx, 'count'] + 1
        st.session_state.tasks_df.at[idx, 'count'] = current_count
        
        # Добавляем время в список (через запятую)
        current_times = st.session_state.tasks_df.at[idx, 'time_spent']
        if current_times and str(current_times).strip():
            new_times = f"{current_times}, {time_str}"
        else:
            new_times = time_str
        st.session_state.tasks_df.at[idx, 'time_spent'] = new_times
        
        # Сразу выбираем следующую
        get_random_task()
        
        st.session_state.status_message = f"✅ +1 к карме! Всего: {current_count}. Время: {time_str}. Следующая задача:"
    else:
        get_random_task()

def add_new_task(task_name):
    """Добавляет новую задачу в таблицу."""
    if st.session_state.tasks_df is None:
        # Создаем новый DataFrame если его нет
        st.session_state.tasks_df = pd.DataFrame({
            "task": [task_name],
            "count": [0],
            "time_spent": [""]
        })
    else:
        new_row = pd.DataFrame({
            "task": [task_name],
            "count": [0],
            "time_spent": [""]
        })
        st.session_state.tasks_df = pd.concat([st.session_state.tasks_df, new_row], ignore_index=True)
    
    st.session_state.status_message = f"➕ Задача '{task_name}' добавлена!"

# --- ИНТЕРФЕЙС ---

st.title("🎰 Казино Важных Дел")

# Создаем две колонки: левая (статистика) и правая (управление)
# ratio 1:3 означает, что правая часть в 3 раза шире левой
col_stats, col_main = st.columns([1, 3])

# --- ЛЕВАЯ КОЛОНКА: СТАТИСТИКА ---
with col_stats:
    st.header("📊 Статистика")
    
    # Блок загрузки перенесен сюда же, чтобы не занимать место в центре
    with st.expander("🔗 Настройка таблицы", expanded=(st.session_state.tasks_df is None)):
        default_url = "https://docs.google.com/spreadsheets/d/1gA4o-EH_M_mNLvkE7hAnOaQzpr_zawA_4aL04aELQh8/edit?gid=1160790662#gid=1160790662"
        sheet_url = st.text_input("Ссылка:", value=default_url, label_visibility="collapsed")
        
        if st.button("📥 Загрузить", use_container_width=True):
            with st.spinner("Загрузка..."):
                df, msg = load_tasks_from_gsheet(sheet_url)
                if df is not None:
                    st.session_state.tasks_df = df
                    st.session_state.current_task_index = None
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    # Блок добавления новой задачи
    with st.expander("➕ Добавить задачу", expanded=False):
        new_task_name = st.text_input("Название задачи:", label_visibility="collapsed", placeholder="Введите название задачи")
        if st.button("Добавить", use_container_width=True):
            if new_task_name and new_task_name.strip():
                add_new_task(new_task_name.strip())
                st.rerun()
            else:
                st.warning("Введите название задачи")

    # Отображение таблицы с фиксированной высотой для скролла
    if st.session_state.tasks_df is not None:
        # Переименовываем колонки для отображения
        display_df = st.session_state.tasks_df.rename(columns={
            "task": "Задача", 
            "count": "Счет",
            "time_spent": "Время (М:СС)"
        })
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            height=600  # <-- Высота блока таблицы, внутри будет скролл
        )
    else:
        st.info("Загрузите таблицу, чтобы увидеть список.")

# --- ПРАВАЯ КОЛОНКА: ОСНОВНОЙ ИНТЕРФЕЙС ---
with col_main:
    st.markdown("<br>", unsafe_allow_html=True) # Небольшой отступ сверху
    
    if st.session_state.tasks_df is not None:
        current_idx = st.session_state.current_task_index
        task_container = st.container(border=True)
        
        if current_idx is not None:
            task_name = st.session_state.tasks_df.iloc[current_idx]['task']
            current_count = st.session_state.tasks_df.iloc[current_idx]['count']
            
            # Вычисляем текущее время для отображения
            if st.session_state.timer_running and st.session_state.timer_start:
                current_time = time.time()
                elapsed = current_time - st.session_state.timer_start + st.session_state.elapsed_time
            else:
                elapsed = st.session_state.elapsed_time
            
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            timer_display = f"{minutes}:{seconds:02d}"
            
            task_container.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>ТЕКУЩАЯ ЗАДАЧА:</h3>", unsafe_allow_html=True)
            task_container.markdown(f"<h1 style='text-align: center;'>{task_name}</h1>", unsafe_allow_html=True)
            task_container.markdown(f"<p style='text-align: center; color: gray;'>Выполнено этой задачи: <b>{current_count}</b> раз</p>", unsafe_allow_html=True)
            
            # Отображение таймера
            task_container.markdown(f"<h2 style='text-align: center; color: #2196F3;'>⏱️ Время: {timer_display}</h2>", unsafe_allow_html=True)
            
            # Кнопки управления таймером
            timer_cols = task_container.columns(2)
            with timer_cols[0]:
                if st.session_state.timer_running:
                    if task_container.button("⏸️ Пауза", type="secondary", use_container_width=True, key="btn_pause"):
                        # Сохраняем прошедшее время
                        current_time = time.time()
                        st.session_state.elapsed_time = current_time - st.session_state.timer_start + st.session_state.elapsed_time
                        st.session_state.timer_running = False
                        st.session_state.timer_start = None
                        st.rerun()
                else:
                    if task_container.button("▶️ Продолжить", type="secondary", use_container_width=True, key="btn_resume"):
                        # Запускаем таймер заново
                        st.session_state.timer_start = time.time()
                        st.session_state.timer_running = True
                        st.rerun()
            
            
            # Кнопка выполнения
            if task_container.button("✅ ВЫПОЛНЕНО (И след. задача)", type="primary", use_container_width=True, key="btn_complete"):
                complete_and_next()
                st.rerun()
                
        else:
            task_container.markdown("<h3 style='text-align: center; color: gray;'>Нажмите кнопку ниже, чтобы начать</h3>", unsafe_allow_html=True)
            
        st.divider()
        
        # Кнопка смены задачи без выполнения
        if st.button("🎲 Крутить барабан (без выполнения)", type="secondary", use_container_width=True):
            get_random_task()
            st.rerun()

    else:
        st.info("👈 Сначала загрузите таблицу в меню слева.")

# Показ сообщений (Toast)
if st.session_state.status_message:
    st.toast(st.session_state.status_message)
