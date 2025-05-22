# Foodgram

Foodgram — сервис для публикации и поиска рецептов с поддержкой списка покупок, избранного и подписок.

## Локальный запуск только бэкенда (тестирование через Postman)

**Важно**:

* При локальном запуске поднимается SQLite
* При запуске через docker compose поднимается PostgreSQL и приложение уже работает с ним
* После локального запуска не забудьте удалить `backend/media` и `backend/db.sqlite3`

1. Склонируйте репозиторий

2. Создайте и активируйте виртуальное окружение

```shell
cd backend
python -m venv venv
venv\Scripts\activate           # для Windows
source venv/bin/activate        # для Linux/Mac
```

3. Установите зависимости

```shell
pip install -r requirements.txt
```

4. Проведите миграции

```shell
python manage.py makemigrations
python manage.py migrate
```

5. Загрузите ингредиенты

```shell
python manage.py load_ingredients
```

6. Запустите сервер

```shell
python manage.py runserver
```

Бэкенд будет доступен по адресу http://localhost:8000/

## Локальный запуск всего проекта
1. Перейдите в папку infra

```shell
cd infra
```

2. Запустите приложение

```shell
docker compose up
```

В результате будет поднятно 3 контейнера: Django-приложение, nginx и PostgreSQL.

Приложение будет доступно по адресу `http://localhost/`.

Также база данных автоматически заполнится демонстрационными данными, будут созданы
пользователи, рецепты, у некоторых пользователей будет заполнена корзина и т.д.

Данные от тестовых аккаунтов можно найти в `data/users.json`.

Данные для подключения к админке:
* URL: `http://localhost/admin/`
* email: `admin@example.com`
* password: `admin`
