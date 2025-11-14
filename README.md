# YouTube Downloader Bot (aiogram + yt-dlp)

Телеграм-бот, который по ссылке на YouTube:
- показывает варианты качества,
- скачивает выбранный формат,
- отправляет файл пользователю.

Реализовано на:
- [`aiogram 3`](https://docs.aiogram.dev/)
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
- Python 3.11



---

## 1. Настройка `.env`

В корне проекта **создай файл `.env`**:

```env
BOT_TOKEN=ваш_токен_из_BotFather
YOUTUBE_NEXT_FETCH=3
DOWNLOAD_DIR=downloads
````

---

## 2. Локальный запуск

### Установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Запуск бота

```bash
python main.py
```

Бот запустится и начнёт принимать сообщения в Telegram.

---

## 3. Запуск в Docker

### Сборка образа

```bash
docker build -t max2-bot .
```

### Запуск контейнера

```bash
docker run --rm \
  --env-file .env \
  max2-bot
```

Если хочешь сохранять скачанные файлы на хост:

```bash
docker run --rm \
  --env-file .env \
  -v "$(pwd)/downloads:/app/downloads" \
  max2-bot
```


