# 1. Базовый Python
FROM python:3.11-slim

# 2. Логи без буферизации
ENV PYTHONUNBUFFERED=1

# 3. Рабочая директория внутри контейнера
WORKDIR /app

# 4. Устанавливаем ffmpeg (для yt-dlp) и чистим мусор
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# 5. Сначала копируем только requirements.txt (чтобы кешировалась установка пакетов)
COPY requirements.txt .

# 6. Ставим зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 7. Копируем весь проект
COPY . .

# 8. Стартовая команда — запуск бота
CMD ["python", "main.py"]
