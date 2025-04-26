FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Команда запуска
CMD ["streamlit", "run", "okno.py", "--server.port=8501", "--server.address=0.0.0.0"]