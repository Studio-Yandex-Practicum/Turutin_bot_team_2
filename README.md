## Проект Turutin_bot

**Это чат-бот, который проводит вводную часть опроса клиентов, формирует заявки и ведет журнал заявок. В проекте также присутствует административный интерфейс, где операторы и администраторы могут управлять заявками.**

### Описание проекта

Цель проекта — создание бота для предоставления клиентам услуг финансового консалтинга. Бот собирает информацию через опрос и формирует заявку для дальнейшего трекинга и обработки операторами и администраторами.

### Технологии и требования

* Язык программирования: Python 3.11+
* СУБД: PostgreSQL
* Архитектура: Асинхронный код (для повышения производительности)
* ORM: SQLAlchemy, Flask-Admin
* Контейнеризация: Docker
* Стилистика: Ruff и Pre-commit

### Структура проекта

Проект включает несколько ключевых папок и файлов:

```
github/
├── workflows/
│   └── style_check.yml # GitHub Actions для проверки стиля кода
infra/
├── .env.example # Пример переменных окружения
├── docker-compose.yml # Локальный запуск с Docker
└── docker-compose.production.yml # Запуск через CI/CD
src/
├── admin_app/
│   ├── admin/
│   │   ├── templates/
│   │   │   └── admin/
│   │   │       ├── index.html # Главная страница админки
│   │   │       └── my_master.html # Пользовательский шаблон
│   ├── admin.py # Основная логика для админки
│   ├── admin_views.py # Вьюхи для обработки запросов
│   ├── cli_commands.py # Команды CLI для административных задач
│   ├── forms.py # Формы для работы с данными
│   ├── utils.py # Утилиты для вспомогательных операций
│   └── views.py # Вьюхи для отображения данных в админке
│ └── bot_app/
│   ├── bot.py # Основная логика работы с ботом
│   ├── buttons.py # Определение кнопок для интерфейса бота
│   ├── config.py # Конфигурация для бота
│   ├── database.py # Модуль работы с базой данных
│   ├── main.py # Запуск бота и основной функционал
│   └── requirements.txt # Зависимости для работы бота
└── init.py # Инициализация пакета
├── models.py # Модели базы данных
├── .gitignore # Игнорируемые файлы для git
├── .pre-commit-config.yaml # Конфигурация для pre-commit
└── README.md # Документация проекта
├── requirements_style.txt # Зависимости для стилистики
└── ruff.toml # Конфигурация для Ruff
```

### Описание директорий

#### admin_app/

Модуль для административного интерфейса, предоставляющего функционал для операторов и администраторов:

* `admin/` — Шаблоны и базовая логика административной панели.
* `templates/admin/index.html` — Главная страница админки.
* `templates/admin/my_master.html` — Пользовательский шаблон.
* `admin.py` — Основная логика для админки.
* `admin_views.py` — Вьюхи для обработки запросов.
* `cli_commands.py` — Команды CLI для административных задач.
* `forms.py` — Формы для работы с данными.
* `utils.py` — Утилиты для вспомогательных операций.
* `views.py` — Вьюхи для отображения данных в админке.

#### bot_app/

Модуль для функциональности бота, который обрабатывает взаимодействие с клиентами:

* `bot.py` — Основная логика работы с ботом.
* `buttons.py` — Определение кнопок для интерфейса бота.
* `config.py` — Конфигурация для бота.
* `database.py` — Модуль работы с базой данных.
* `main.py` — Запуск бота и основной функционал.
* `requirements.txt` — Зависимости для работы бота.

#### infra/

Директория для настройки окружения и развертывания проекта:

* `docker-compose.yml` — Локальная конфигурация для запуска контейнеров.
* `docker-compose.production.yml` — Конфигурация для запуска проекта в продакшн через CI/CD.
* `.env.example` — Пример переменных окружения для настройки .env.

### Запуск проекта

#### CI/CD

Для развертывания проекта через CI/CD, используйте файл `docker-compose.production.yml` в директории `infra/`. Это позволит вам автоматизировать процесс развертывания и управления проектом в облачной инфраструктуре.

#### Локальный запуск с Docker Compose

1. Скопируйте файл `.env.example` в `.env` и настройте переменные окружения.
2. Убедитесь, что в переменной `BOT_TOKEN` указан токен вашего бота.
3. Запустите проект с помощью команды: `docker compose up`
4. Для фоновго запуска используйте: `docker compose up -d`
5. Для обновления и перезапуска сети после изменений в коде: `docker compose up --build`

#### Создание суперпользователя

Для создания суперпользователя используйте команду: `docker exec -it infra-admin-1 flask create_superuser user password`

### Стилистика

Для стилизации кода используются инструменты Ruff и Pre-commit.

#### Проверка и исправление стиля

* Для проверки стилистики кода используйте команду: `ruff check`
* Для автоматического исправления ошибок: `ruff check --fix`
* Для установки pre-commit hook: `pre-commit install`

### Рекомендации

* **Миграции базы данных:** Убедитесь, что все миграции выполнены. Используйте Alembic для управления миграциями.
* **Тестирование:** Рекомендуется проводить тестирование каждого модуля перед сборкой и запуском.
* **Логирование:** Настройте логирование для диагностики и отладки.
