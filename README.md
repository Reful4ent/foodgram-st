# Foodgram - Отечественный свой русский и****грам про еду! 🥪🍗🥩🧇

## Описание проекта
Foodgram - это сервис для публикации рецептов. Пользователи могут создавать свои рецепты, добавлять их в избранное, подписываться на других авторов и формировать список покупок для выбранных рецептов.

Проект реализован как REST API с использованием Docker для удобного развертывания.

## Используемые технологии
- Python
- Django
- Django REST Framework
- PostgreSQL
- Nginx
- Docker
- GitHub Actions (CI/CD)

## Требования
- Docker
- Docker Compose

## 1. Клонирование репозитория
```bash
git clone https://github.com/Reful4ent/foodgram-st.git
cd foodgram-st
```

## 2. Добавление .env
```bash
DATABASE_USER=
DATABASE_HOST=
DATABASE_NAME=
DATABASE_PASSWORD=
DATABASE_PORT=
```

## 3. Запуск проекта
### DEV VERSION
### Start front
1. ``npm install`` - Устанавливаем зависимости
2. ``npm run dev`` - Запускаем проект.
### Start back
1. ``pip install -r requirements.txt``
2. ``python manage.py makemigrations``
3. ``python manage.py migrate``
4. ``python manage.py runserver``

### PROD VERSION
``docker-compose up --build`` - запуск контейнеров