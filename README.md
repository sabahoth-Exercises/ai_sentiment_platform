# AI Sentiment Analysis Platform

## Описание проекта

Данный проект представляет собой  сервис для анализа тональности текста (sentiment analysis) с использованием машинного обучения.

Система реализована в виде микросервисной архитектуры и включает:

- **Backend API** на FastAPI
- **ML-сервис** (3-классовая модель: positive / neutral / negative)
- **Асинхронную обработку задач** через Celery + Redis
- **Базу данных PostgreSQL** с ORM (SQLAlchemy) и миграциями Alembic
- **Веб-интерфейс** на Streamlit
- **Reverse Proxy** (Nginx)

## Архитектура

Сервис состоит из следующих компонентов:
Пользователь → Nginx → (UI / API)

UI (Streamlit) → API (FastAPI)

API → Redis → Celery Worker → ML модель
API → PostgreSQL (история запросов)

Prometheus → собирает метрики с API
Grafana → визуализирует метрики


## Функциональность

- Асинхронный анализ текста
- Поддержка 3 классов тональности:
  - positive
  - neutral
  - negative
- Валидация входных данных (только латиница)
- История запросов
- Визуализация результатов
- Мониторинг API


## Требования

- Docker
- Docker Compose


## Запуск проекта

### 1. Клонирование репозитория

```bash
git clone <ai_sentiment_platform>
cd ai_sentiment_platform```

### 2. Настройка переменных окружения

Создайте файл .env

### 3. Запуск
```bash
docker compose up --build -d```

## Доступ к сервисам
| Сервис             | URL                                                        |
| ------------------ | ---------------------------------------------------------- |
| UI (Streamlit)     | [http://localhost](http://localhost)                       |
| API Docs (Swagger) | [http://localhost/api/docs](http://localhost/api/docs)     |
| Health Check       | [http://localhost/api/health](http://localhost/api/health) |
| Prometheus         | [http://localhost:9090](http://localhost:9090)             |
| Grafana            | [http://localhost:3000](http://localhost:3000)             |


## Примеры API запросов

### Анализ текста

curl -X POST http://localhost/api/predict \
-H "Content-Type: application/json" \
-d '{"text":"I love this application"}'

Ответ:

{
  "task_id": "..."
}

### Получение результата

curl http://localhost/api/result/<task_id>

### История запросов

curl http://localhost/api/history 

### Валидация данных

Поддерживаются только:

- латинские буквы
- цифры
- базовая пунктуация

Пример ошибки:

{
  "error": "Validation error",
  "hint": "Only Latin letters are allowed"
}


## ML модель

Используется классическая модель машинного обучения:

- TF-IDF векторизация
- Linear SVM (LinearSVC)

Модель обучена на датасете Twitter Sentiment (3 класса).

ML-логика полностью изолирована в отдельном модуле (sentiment_model.py).

##  Асинхронная обработка
- Celery используется для выполнения задач
- Redis выступает брокером и backend
- API возвращает task_id
- результат получается через polling или WebSocket


## Работа с базой данных
- SQLAlchemy ORM
- Alembic для миграций
- Таблица:
predictions
alembic_version

При запуске автоматически выполняется:

alembic upgrade head


## Docker архитектура

Используются сервисы:

- api
- worker
- worker2
- redis
- postgres
- nginx
- ui


## Сети
- frontend_net: UI, API, Nginx
- backend_net: API, Redis, Workers, DB

## Volumes
- PostgreSQL data
- Redis data
- ML модель