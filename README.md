

# 🎬 MAX Downloader Bot  
### Хакатон VK × MAX • 2025

Умный чат-бот, который превращает обычную YouTube-ссылку в готовый mp4 файл.
<div align="center">
<br/>

<img width="70" src="https://upload.wikimedia.org/wikipedia/commons/7/75/Max_logo_2025.png" alt="preview" />

<br/><br/>
<div align="left">

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

Бот запустится и начнёт принимать сообщения в MAX.

---

## 3. Запуск в Docker

### Сборка образа и заупск

```
docker-compose up --build
```