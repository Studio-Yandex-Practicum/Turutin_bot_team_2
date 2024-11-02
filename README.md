# Шаблон для проектов со стилизатором Ruff

## Основное

1. Базовая версия Python - 3.11.
2. В файле `requirements_style.txt` находятся зависимости для стилистики.
3. В каталоге `src` находится базовая структура проекта
4. В файле `srd/requirements.txt` прописываются базовые зависимости.
5. В каталоге `infra` находятся настроечные файлы проекта. Здесь же размещать файлы для docker compose.

## Запуск docker-compose на локальном порту 127.0.0.1
### Админ-зона: 127.0.0.1:5000/admin
### Бот заработает, если указать BOT_TOKEN в .env

Запуск в терминале с логами
```shell
docker compose up
```
Фоновый запуск
```shell
docker compose up -d
```

Обновить и поднять сеть после ваших локальных изменений в коде:
```shell
docker compose up --build
```
Команда для удаления ВСЕХ компонентов Docker:
если надо почитсить систему быстро
(docker compose up будет работать как в первый раз)
```shell
docker system prune -a
```


## Запуск docker-compose на локальном порту 127.0.0.1:8000 (для пользователей Windows)
### Проверить, что файлы dockerfile, start.sh, docker-compose - LF (для админки)
### Для выполенения следующих команд использовать среду выполнения Linux - WSL 
1) Обновить список доступных пакетов из репозиториев, чтобы получить последние версии пакетов
```
sudo apt-get update
```
2) Обновить все установленные пакеты до их последних версий
```
sudo apt-get upgrade
```
3) Установить виртуальное окружение Python, которое помогает изолировать пакеты для проекта
```
sudo apt install python3-venv
```
4) Создать новое виртуальное окружение Python с именем 'venv'
```
python3 -m venv venv
```
5) Активировать виртуальное окружение Python, чтобы все установленные пакеты были доступны только в данном окружении
```
source venv/bin/activate
```
6) Перейти в директорию с файлом docker-compose.yml
```
cd/infra
```
7) Запустить все сервисы, указанные в docker-compose.yml с обновленными образами
```
docker compose up --build
```
8) Запустить интерактивную оболочку bash внутри контейнера с именем 'infra-admin-1' и создать суперпользователя с именем 'user' и паролем 'password'
```
docker exec -it infra-admin-1 flask create_superuser user password
```
9) Открыть админку по ссылке http://127.0.0.1:8000
10) Открыть бота в тг и запустить его командой "/start"


## Стилистика

Для стилизации кода используется пакеты `Ruff` и `Pre-commit`

Проверка стилистики кода осуществляется командой
```shell
ruff check
```

Если одновременно надо пофиксить то, что можно поиксить автоматически, то добавляем параметр `--fix`
```shell
ruff check --fix
```

Что бы стилистика автоматически проверялась и поправлялась при комитах надо добавить hook pre-commit к git

```shell
pre-commit install
```
