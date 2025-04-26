FROM python:3.10-slim

WORKDIR /app

# Установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY app/ app/
# Копируем data прямо в /app/data
COPY app/data/ data/

# Открываем порт
EXPOSE 8004

CMD ["python3", "app/main.py"]