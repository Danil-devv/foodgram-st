# Foodgram

Foodgram — сервис для публикации и поиска рецептов с поддержкой списка покупок, избранного и подписок.

## Локальный запуск только бэкенда (тестирование через Postman)

**Важно**:

* При локальном запуске поднимается SQLite
* При запуске через docker compose поднимается PostgreSQL и приложение уже работает с ним
* После локального запуска не забудьте удалить `backend/media` и `backend/db.sqlite3`

1. Склонируйте репозиторий

```shell
git clone git@github.com:Danil-devv/foodgram-st.git
```

2. Создайте и активируйте виртуальное окружение

```shell
cd foodgram-st-main/backend
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

Бэкенд будет доступен по адресу [http://localhost:8000/](http://localhost:8000/)

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

Также база данных автоматически заполнится демонстрационными данными, будут созданы
пользователи, рецепты, у некоторых пользователей будет заполнена корзина и т.д.

Данные от тестовых аккаунтов можно найти в `data/users.json`.

Доступы к приложению:
- Веб-приложение: [http://localhost/](http://localhost/)
- API Документация: [http://localhost/api/docs/](http://localhost/api/docs/)
- Панель администратора: [http://localhost/admin/](http://localhost/admin/)
- API Endpoints: [http://localhost/api/](http://localhost/api/)

Автор: Даниил Семенов

Email: [s3menovd4nil@yandex.ru](mailto:s3menovd4nil@yandex.ru)
