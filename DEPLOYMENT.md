# Руководство по развертыванию Forum

Полное руководство по развертыванию форума на Ubuntu 22.04 с использованием Docker или без него.

## 📋 Содержание

1. [Требования](#требования)
2. [Быстрое развертывание с Docker](#быстрое-развертывание-с-docker)
3. [Ручная установка на Ubuntu 22.04](#ручная-установка-на-ubuntu-2204)
4. [Настройка домена и SSL](#настройка-домена-и-ssl)
5. [Обслуживание](#обслуживание)
6. [Устранение неполадок](#устранение-неполадок)

## Требования

### Минимальные требования сервера

- **ОС**: Ubuntu 22.04 LTS
- **RAM**: Минимум 2GB (рекомендуется 4GB)
- **CPU**: 1 ядро (рекомендуется 2+)
- **Диск**: 20GB свободного пространства
- **Python**: 3.10+
- **PostgreSQL**: 13+ (или SQLite для небольших форумов)
- **Redis**: 6+

### Программное обеспечение

```bash
- Docker & Docker Compose (для Docker развертывания)
- Python 3.10
- PostgreSQL
- Redis
- Nginx
- Git
```

## Быстрое развертывание с Docker

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt-get update && sudo apt-get upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt-get install docker-compose -y

# Проверка установки
docker --version
docker-compose --version
```

### 2. Клонирование проекта

```bash
cd /var/www
sudo git clone https://github.com/cheltenhemm-jpg/forum2.git
cd forum2
```

### 3. Настройка окружения

```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование .env
nano .env
```

Основные параметры в `.env`:

```env
SECRET_KEY=<генерируйте-сложный-ключ>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=forum_db
DB_USER=forum_user
DB_PASSWORD=<сложный-пароль>
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

SITE_NAME=Your Forum Name
SITE_DOMAIN=yourdomain.com
```

### 4. Запуск

```bash
# Сборка и запуск контейнеров
sudo docker-compose up -d --build

# Проверка статуса
sudo docker-compose ps

# Просмотр логов
sudo docker-compose logs -f web
```

Форум будет доступен на порту 80. Учетные данные по умолчанию: `admin/admin` (измените сразу!)

### 5. Создание администратора

```bash
sudo docker-compose exec web python manage.py createsuperuser
```

## Ручная установка на Ubuntu 22.04

### 1. Автоматическая установка

```bash
cd /tmp
wget https://raw.githubusercontent.com/cheltenhemm-jpg/forum2/main/install.sh
sudo bash install.sh
```

### 2. Ручная установка (детально)

#### 2.1 Установка зависимостей

```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip python3-venv \
    postgresql postgresql-contrib redis-server nginx git
```

#### 2.2 Настройка PostgreSQL

```bash
sudo -u postgres psql << EOF
CREATE DATABASE forum_db;
CREATE USER forum_user WITH PASSWORD 'secure_password_here';
ALTER ROLE forum_user SET client_encoding TO 'utf8';
ALTER ROLE forum_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE forum_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE forum_db TO forum_user;
\q
EOF
```

#### 2.3 Клонирование и настройка проекта

```bash
cd /var/www
sudo git clone https://github.com/cheltenhemm-jpg/forum2.git
cd forum2

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.4 Настройка окружения

```bash
cp .env.example .env
nano .env
# Отредактируйте параметры
```

#### 2.5 Миграции и статика

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### 2.6 Настройка Gunicorn

Создайте systemd service:

```bash
sudo nano /etc/systemd/system/forum.service
```

```ini
[Unit]
Description=Forum Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/forum2
Environment="PATH=/var/www/forum2/venv/bin"
ExecStart=/var/www/forum2/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/forum2/forum.sock \
          forumsite.wsgi:application

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl start forum
sudo systemctl enable forum
sudo systemctl status forum
```

#### 2.7 Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/forum
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/forum2/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/forum2/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/forum2/forum.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/forum /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Настройка домена и SSL

### Получение SSL сертификата с Let's Encrypt

```bash
# Установка Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Получение сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

### Настройка DNS

Добавьте A-записи для вашего домена:

```
A    @        YOUR_SERVER_IP
A    www      YOUR_SERVER_IP
```

## Обслуживание

### Резервное копирование

#### База данных

```bash
# PostgreSQL
sudo -u postgres pg_dump forum_db > backup_$(date +%Y%m%d).sql

# Восстановление
sudo -u postgres psql forum_db < backup_YYYYMMDD.sql
```

#### Медиа файлы

```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz /var/www/forum2/media/
```

### Обновление форума

```bash
cd /var/www/forum2
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart forum
```

### Мониторинг

```bash
# Логи приложения
sudo journalctl -u forum -f

# Логи Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Логи Docker (если используется)
sudo docker-compose logs -f web
```

## Устранение неполадок

### Проблема: "502 Bad Gateway"

**Решение:**
```bash
# Проверка статуса Gunicorn
sudo systemctl status forum

# Проверка socket файла
ls -l /var/www/forum2/forum.sock

# Перезапуск сервисов
sudo systemctl restart forum
sudo systemctl restart nginx
```

### Проблема: Статические файлы не загружаются

**Решение:**
```bash
python manage.py collectstatic --noinput
sudo chown -R www-data:www-data /var/www/forum2/staticfiles
sudo chmod -R 755 /var/www/forum2/staticfiles
```

### Проблема: Database connection failed

**Решение:**
```bash
# Проверка PostgreSQL
sudo systemctl status postgresql

# Проверка подключения
psql -U forum_user -d forum_db -h localhost

# Проверка .env файла
cat .env | grep DB_
```

### Проблема: Redis connection error

**Решение:**
```bash
# Проверка Redis
sudo systemctl status redis-server

# Тест подключения
redis-cli ping

# Если нужен рестарт
sudo systemctl restart redis-server
```

## Оптимизация производительности

### 1. Настройка PostgreSQL

```bash
sudo nano /etc/postgresql/13/main/postgresql.conf
```

```conf
# Для сервера с 4GB RAM
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
```

### 2. Настройка Redis

```bash
sudo nano /etc/redis/redis.conf
```

```conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 3. Gunicorn workers

Рекомендуемое количество workers: `(2 × CPU_cores) + 1`

```bash
# Для 2 ядер
--workers 5
```

## Безопасность

### Checklst безопасности

- [ ] `DEBUG=False` в production
- [ ] Сложный `SECRET_KEY`
- [ ] Firewall настроен (ufw)
- [ ] SSL сертификат установлен
- [ ] Регулярные обновления безопасности
- [ ] Резервное копирование настроено
- [ ] Fail2ban установлен
- [ ] Пароли баз данных изменены
- [ ] Права файлов настроены корректно

### Настройка Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### Установка Fail2ban

```bash
sudo apt-get install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

##  Поддержка и контакты

- **GitHub Issues**: https://github.com/cheltenhemm-jpg/forum2/issues
- **Документация**: https://github.com/cheltenhemm-jpg/forum2

---

**Внимание**: Всегда тестируйте развертывание на тестовом сервере перед production!
