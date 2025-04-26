# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы в контейнер
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем оставшийся код
COPY . .

# Открываем порт
EXPOSE 8005

# Запускаем приложение
CMD ["python3", "app/main.py"]