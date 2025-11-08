#!/bin/bash
# Автоматический скрипт установки форума на Ubuntu 22.04

set -e

echo "=================================="
echo "Установка Forum на Ubuntu 22.04"
echo "=================================="

# Проверка root прав
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите с правами root (sudo)"
    exit 1
fi

# Обновление системы
echo "Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo "Установка необходимых пакетов..."
apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    docker.io \
    docker-compose

# Запуск сервисов
echo "Запуск сервисов..."
systemctl start postgresql
systemctl enable postgresql
systemctl start redis-server
systemctl enable redis-server

# Настройка PostgreSQL
echo "Настройка PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE forum_db;
CREATE USER forum_user WITH PASSWORD 'forum_password';
ALTER ROLE forum_user SET client_encoding TO 'utf8';
ALTER ROLE forum_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE forum_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE forum_db TO forum_user;
\q
EOF

# Клонирование репозитория (если нужно)
echo "Настройка проекта..."
PROJECT_DIR="/var/www/forum"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p $PROJECT_DIR
    echo "Скопируйте файлы проекта в $PROJECT_DIR"
fi

cd $PROJECT_DIR

# Создание .env файла
if [ ! -f ".env" ]; then
    echo "Создание .env файла..."
    cat > .env << EOF
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,YOUR_DOMAIN

DB_ENGINE=django.db.backends.postgresql
DB_NAME=forum_db
DB_USER=forum_user
DB_PASSWORD=forum_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

REDIS_URL=redis://127.0.0.1:6379/0

SITE_NAME=Forum Community
EOF
    echo "⚠️  Отредактируйте .env файл и добавьте ваш домен в ALLOWED_HOSTS"
fi

echo "=================================="
echo "Установка завершена!"
echo "=================================="
echo ""
echo "Для запуска через Docker:"
echo "  cd $PROJECT_DIR"
echo "  docker-compose up -d"
echo ""
echo "Для запуска без Docker:"
echo "  1. Создайте виртуальное окружение: python3 -m venv venv"
echo "  2. Активируйте: source venv/bin/activate"
echo "  3. Установите зависимости: pip install -r requirements.txt"
echo "  4. Выполните миграции: python manage.py migrate"
echo "  5. Создайте суперпользователя: python manage.py createsuperuser"
echo "  6. Соберите статику: python manage.py collectstatic"
echo "  7. Запустите сервер: gunicorn forumsite.wsgi:application --bind 0.0.0.0:8000"
echo ""
echo "Доступ к форуму: http://YOUR_SERVER_IP:8000"
echo "Админ-панель: http://YOUR_SERVER_IP:8000/admin"
echo ""
