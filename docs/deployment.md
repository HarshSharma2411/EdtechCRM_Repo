# Deployment Guide

This document explains how to deploy EdTech CRM to a production environment.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Database Setup (PostgreSQL)](#database-setup-postgresql)
- [Static Files](#static-files)
- [Application Server (Gunicorn)](#application-server-gunicorn)
- [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
- [Process Management (systemd)](#process-management-systemd)
- [Security Checklist](#security-checklist)
- [Deployment Steps (Summary)](#deployment-steps-summary)
- [Updating the Application](#updating-the-application)

---

## Overview

The recommended production stack is:

```
Internet → Nginx (reverse proxy) → Gunicorn (WSGI server) → Django
                                                           ↓
                                                       PostgreSQL
```

| Component | Role |
|-----------|------|
| **Nginx** | Serves static/media files directly; proxies dynamic requests to Gunicorn |
| **Gunicorn** | Production WSGI server; manages Django worker processes |
| **PostgreSQL** | Robust production-grade relational database |
| **systemd** | Manages the Gunicorn process (auto-restart, logging) |

---

## Prerequisites

- A Linux server (Ubuntu 22.04 LTS recommended)
- Python 3.11+ installed
- PostgreSQL 14+ installed and running
- Nginx installed
- A domain name pointing to the server (for HTTPS)

---

## Environment Variables

Never hard-code sensitive settings in `settings.py`. Use environment variables or a `.env` file (loaded via `python-dotenv` or your deployment tool).

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | A 50+ character random string |
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames | `edtech.example.com,www.edtech.example.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@localhost:5432/edtech_crm` |
| `DJANGO_STATIC_ROOT` | Absolute path to collect static files | `/var/www/edtech_crm/staticfiles` |
| `DJANGO_MEDIA_ROOT` | Absolute path for media uploads | `/var/www/edtech_crm/media` |

### Generating a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(50))"
```

### Updating settings.py for Production

Add the following pattern to `edtech_crm/settings.py` to read from environment variables:

```python
import os

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

# PostgreSQL via DATABASE_URL
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}')
    )
}

STATIC_ROOT = os.environ.get('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles')
MEDIA_ROOT = os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media')
```

> **Note:** Install `dj-database-url` if using this pattern: `pip install dj-database-url psycopg2-binary`

---

## Database Setup (PostgreSQL)

```bash
# Install PostgreSQL client library
pip install psycopg2-binary

# Create the database and user
sudo -u postgres psql <<EOF
CREATE DATABASE edtech_crm;
CREATE USER edtech_user WITH PASSWORD 'strong_db_password';
ALTER ROLE edtech_user SET client_encoding TO 'utf8';
ALTER ROLE edtech_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE edtech_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE edtech_crm TO edtech_user;
EOF
```

---

## Static Files

Collect all static files into `STATIC_ROOT` for Nginx to serve:

```bash
python manage.py collectstatic --no-input
```

This copies files from `static/` and all app `static/` directories into the configured `STATIC_ROOT`.

---

## Application Server (Gunicorn)

### Installation

```bash
pip install gunicorn
```

### Test Run

```bash
gunicorn edtech_crm.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

### Recommended Worker Count

```
workers = (2 × CPU_cores) + 1
```

For a 2-core server: `workers = 5`.

---

## Reverse Proxy (Nginx)

Create `/etc/nginx/sites-available/edtech_crm`:

```nginx
server {
    listen 80;
    server_name edtech.example.com www.edtech.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name edtech.example.com www.edtech.example.com;

    ssl_certificate /etc/letsencrypt/live/edtech.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/edtech.example.com/privkey.pem;

    # Static files
    location /static/ {
        alias /var/www/edtech_crm/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/edtech_crm/media/;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/edtech_crm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d edtech.example.com -d www.edtech.example.com
```

---

## Process Management (systemd)

Create `/etc/systemd/system/edtech_crm.service`:

```ini
[Unit]
Description=EdTech CRM Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edtech_crm
EnvironmentFile=/var/www/edtech_crm/.env
ExecStart=/var/www/edtech_crm/.venv/bin/gunicorn \
    edtech_crm.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 5 \
    --timeout 60 \
    --access-logfile /var/log/edtech_crm/access.log \
    --error-logfile /var/log/edtech_crm/error.log
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo mkdir -p /var/log/edtech_crm
sudo systemctl daemon-reload
sudo systemctl enable edtech_crm
sudo systemctl start edtech_crm
sudo systemctl status edtech_crm
```

---

## Security Checklist

Before going live, verify all of the following:

- [ ] `DEBUG = False` in production settings
- [ ] `SECRET_KEY` is a long, unique, random string (never committed to version control)
- [ ] `ALLOWED_HOSTS` contains only your actual domain names
- [ ] HTTPS is enabled and HTTP redirects to HTTPS
- [ ] `SECURE_SSL_REDIRECT = True` in Django settings
- [ ] `SESSION_COOKIE_SECURE = True` (cookies only sent over HTTPS)
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `X_FRAME_OPTIONS = 'DENY'` (prevents clickjacking)
- [ ] `SECURE_HSTS_SECONDS = 31536000` (enable HSTS for 1 year once HTTPS is confirmed stable)
- [ ] Database user has minimal required privileges
- [ ] Media directory is outside the web root or Nginx is configured to block script execution in it
- [ ] `python manage.py check --deploy` reports no critical issues

### Django Production Settings Additions

Add these to `settings.py` for production:

```python
# Security headers (production only)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
```

---

## Deployment Steps (Summary)

```bash
# 1. Pull latest code
cd /var/www/edtech_crm
git pull origin main

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install/update dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --no-input

# 6. Run tests to verify nothing is broken
python manage.py test

# 7. Restart application server
sudo systemctl restart edtech_crm

# 8. Verify the service is running
sudo systemctl status edtech_crm
```

---

## Updating the Application

For routine updates (new features, bug fixes):

```bash
cd /var/www/edtech_crm
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py collectstatic --no-input
python manage.py test
sudo systemctl restart edtech_crm
```

For zero-downtime deployments on high-traffic sites, consider using a blue-green deployment strategy or a tool like Fabric or Ansible to automate the above steps.
