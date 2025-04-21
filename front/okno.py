import streamlit as st
import requests
import time
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

if "session_id" not in st.session_state:
    try:
        response = requests.post(f"{API_URL}/sessions")
        if response.status_code == 200:
            st.session_state.session_id = response.json()["session_id"]
            st.session_state.messages = []
            st.session_state.recommendations = []
            st.session_state.last_update = datetime.now().timestamp()
            st.session_state.debug_info = []
            print(f"Created new session: {st.session_state.session_id}")
    except Exception as e:
        st.error(f"Ошибка создания сессии: {str(e)}")

def fetch_updates():
    if "session_id" in st.session_state:
        try:
            print(f"Fetching updates for session: {st.session_state.session_id}")
            response = requests.get(
                f"{API_URL}/sessions/{st.session_state.session_id}/updates"
            )
            if response.status_code == 200:
                data = response.json()
                
                st.session_state.debug_info.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "messages_count": len(data.get("messages", [])),
                    "messages": data.get("messages", []),
                    "recommendations_count": len(data.get("recommendations", [])),
                    "session_id": st.session_state.session_id
                })
                
                if len(st.session_state.debug_info) > 10:
                    st.session_state.debug_info = st.session_state.debug_info[-10:]
                
                messages = data.get("messages", [])
                for msg in messages:
                    if "role" not in msg:
                        msg["role"] = "user"
                
                st.session_state.messages = messages
                st.session_state.recommendations = data.get("recommendations", [])
                st.session_state.last_update = datetime.now().timestamp()
                return True
            elif response.status_code == 404:
                print(f"Session {st.session_state.session_id} not found")
                st.error("Сессия не найдена. Пожалуйста, создайте новую сессию.")
                return False
        except Exception as e:
            st.error(f"Ошибка получения обновлений: {str(e)}")
            return False
    return False

def send_operator_message(message):
    if "session_id" in st.session_state and message:
        try:
            print(f"Sending message to session: {st.session_state.session_id}")
            response = requests.post(
                f"{API_URL}/sessions/{st.session_state.session_id}/messages",
                json={"content": message, "role": "operator"}
            )
            if response.status_code == 200:
                operator_message = {
                    "content": message,
                    "timestamp": datetime.now().isoformat(),
                    "role": "operator"
                }
                st.session_state.messages.append(operator_message)
                return True
            elif response.status_code == 404:
                print(f"Session {st.session_state.session_id} not found, creating new one")
                new_response = requests.post(f"{API_URL}/sessions")
                if new_response.status_code == 200:
                    st.session_state.session_id = new_response.json()["session_id"]
                    st.session_state.messages = []
                    st.session_state.recommendations = []
                    print(f"Created new session: {st.session_state.session_id}")
                    return send_operator_message(message)
        except Exception as e:
            st.error(f"Ошибка отправки сообщения: {str(e)}")
    return False

st.title("Интерфейс оператора")

with st.sidebar:
    #TODO: убрать айди сессии здесь
    session_id = st.session_state.get('session_id', '')
    st.write(f"ID сессии: {session_id if session_id else 'Нет'}")
    if session_id:
        st.code(session_id, language=None)
        st.markdown(
            f"""
            <button onclick="navigator.clipboard.writeText('{session_id}')"
                    style="padding:6px 12px; border-radius:4px; border:none; background:#1976d2; color:white; cursor:pointer;">
                📋 Скопировать session_id
            </button>
            """,
            unsafe_allow_html=True
        )
    ##
    if st.button("🔄 Принудительное обновление"):
        fetch_updates()
        st.rerun()
    
    if st.button("🔄 Создать новую сессию"):
        try:
            response = requests.post(f"{API_URL}/sessions")
            if response.status_code == 200:
                st.session_state.session_id = response.json()["session_id"]
                st.session_state.messages = []
                st.session_state.recommendations = []
                st.session_state.last_update = datetime.now().timestamp()
                st.success(f"Создана новая сессия: {st.session_state.session_id}")
                st.rerun()
        except Exception as e:
            st.error(f"Ошибка создания сессии: {str(e)}")
   #print(f"session_state: {st.session_state}")
    if st.button("⏹️ Завершить сессию") and "session_id" in st.session_state:
        print(f"Завершение сессии: {st.session_state.session_id}")
        try:
            response = requests.post(
                f"{API_URL}/sessions/{st.session_state.session_id}/complete"
            )
            if response.status_code == 200:
                st.success("Сессия завершена!")
                st.session_state.clear()
            else:
                st.error("Ошибка завершения сессии")
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
    
    with st.expander("Отладочная информация"):
        st.write(f"ID сессии: {st.session_state.get('session_id', 'Нет')}")
        st.write(f"Количество сообщений: {len(st.session_state.get('messages', []))}")
        st.write(f"Последнее обновление: {datetime.fromtimestamp(st.session_state.get('last_update', 0)).strftime('%H:%M:%S')}")
        
        if st.session_state.get("debug_info"):
            st.write("История обновлений:")
            for info in st.session_state.debug_info:
                st.write(f"{info['timestamp']}: {info['messages_count']} сообщений, {info['recommendations_count']} рекомендаций (сессия: {info['session_id']})")
                if info['messages_count'] > 0:
                    st.write(f"Пример сообщения: {info['messages'][0]}")
        
        if st.session_state.get("messages"):
            st.write("Все сообщения:")
            for i, msg in enumerate(st.session_state.messages):
                st.write(f"{i+1}. {msg}")

# Основной интерфейс
col1, col2 = st.columns([2.5, 3])

with col1:
    st.subheader("История диалога")
    if st.session_state.get("messages"):
        for msg in st.session_state.messages:
            # Определяем роль сообщения
            role = msg.get("role", "user")
            
            # Отображаем сообщение
            with st.chat_message(role):
                st.markdown(msg["content"])
                st.caption(datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S"))
    else:
        st.info("Диалог еще не начат")
    
    # Форма для отправки сообщения оператора
    with st.form(key="message_form"):
        operator_message = st.text_input("Ваше сообщение", key="operator_input")
        submit_button = st.form_submit_button(label="Отправить")
        
        if submit_button and operator_message and operator_message.strip():
            if send_operator_message(operator_message):
                st.rerun()

with col2:
    st.subheader("Рекомендации системы")
    if st.session_state.get("recommendations"):
        for i, rec in enumerate(st.session_state.recommendations):
            # Проверяем, является ли рекомендация строкой или словарем
            if isinstance(rec, str):
                with st.expander(f"Рекомендация #{i+1}"):
                    st.write(rec)
            else:
                # Используем реальные поля, которые приходят с бэка
                with st.expander(f"Рекомендация: {rec.get('intern', 'Неизвестно')}"):
                    st.write(f"**Эмоция:** {rec.get('emotinal', 'Неизвестно')}")
                    st.write(f"**Ссылка:** {rec.get('link', 'Нет')}")
                    st.write(f"**Ответ:** {rec.get('ans', 'Нет')}")
                    st.write(f"**Знания:** {rec.get('know', 'Нет данных')}")
    else:
        st.info("Рекомендации пока отсутствуют")

# Автообновление через механизм Streamlit
fetch_updates()

# Устанавливаем таймер для следующего обновления
time.sleep(POLL_INTERVAL)
st.rerun()