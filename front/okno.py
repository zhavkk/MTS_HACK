import streamlit as st
import requests
import time
from datetime import datetime
import os
# Конфигурация
API_URL = os.getenv("API_URL", "http://backend:8000")
POLL_INTERVAL = 2  # seconds

# Инициализация состояния
def init_state():
    if 'client_msgs' not in st.session_state:
        st.session_state.client_msgs = []
    if 'agent_suggestions' not in st.session_state:
        st.session_state.agent_suggestions = {}
    if 'operator_responses' not in st.session_state:
        st.session_state.operator_responses = []
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()

init_state()

# Функции API
def fetch_updates():
    try:
        response = requests.get(
            f"{API_URL}/updates",
            params={"since": st.session_state.last_update}
        )
        if response.status_code == 200:
            data = response.json()
            return data
    except Exception as e:
        st.error(f"Ошибка соединения: {str(e)}")
    return None

def send_operator_response(response_text):
    payload = {
        "message": response_text,
        "suggestions": st.session_state.agent_suggestions.get(
            len(st.session_state.client_msgs)-1, {}
        )
    }
    requests.post(f"{API_URL}/responses", json=payload)

st.title("📞 Контакт-центр: интерфейс оператора")
st.markdown("---")

# Колонки для диалога
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Диалог с клиентом")
    dialog_container = st.container()
    
    with dialog_container:
        for idx, msg in enumerate(st.session_state.client_msgs):
            with st.chat_message("user"):
                st.markdown(f"**Клиент:** {msg['text']}")
                st.caption(msg['timestamp'])
                
            if idx in st.session_state.operator_responses:
                with st.chat_message("assistant"):
                    resp = st.session_state.operator_responses[idx]
                    st.markdown(f"**Оператор:** {resp['text']}")
                    st.caption(resp['timestamp'])

with right_col:
    st.subheader("Рекомендации системы")
    suggestions_container = st.container()
    
    with suggestions_container:
        if st.session_state.agent_suggestions:
            last_idx = max(st.session_state.agent_suggestions.keys())
            suggestion = st.session_state.agent_suggestions[last_idx]
            
            st.json({
                "Интент": suggestion.get('intent', 'не определен'),
                "Эмоция": suggestion.get('emotion', 'не определена'),
                "Рекомендуемые действия": suggestion.get('actions', []),
                "Справка": suggestion.get('knowledge', '')
            })

# Механизм обновления
def update_interface():
    updates = fetch_updates()
    if updates:
        for msg in updates.get('new_messages', []):
            st.session_state.client_msgs.append({
                "text": msg['content'],
                "timestamp": datetime.fromisoformat(msg['timestamp']).strftime("%H:%M:%S")
            })
            st.session_state.agent_suggestions[len(st.session_state.client_msgs)-1] = {
                "intent": msg['metadata']['intent'],
                "emotion": msg['metadata']['emotion'],
                "actions": msg['metadata']['actions'],
                "knowledge": msg['metadata']['knowledge_response']
            }
        st.session_state.last_update = time.time()
        st.experimental_rerun()

# Обработка ответов оператора
response_text = st.chat_input("Введите ваш ответ...")
if response_text:
    send_operator_response(response_text)
    st.session_state.operator_responses.append({
        "text": response_text,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    st.experimental_rerun()

# Автообновление интерфейса
while True:
    update_interface()
    time.sleep(POLL_INTERVAL)