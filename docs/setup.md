# Setup & Installation Guide

This guide walks you through setting up a local development environment for EdTech CRM from scratch.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1 — Clone the Repository](#step-1--clone-the-repository)
- [Step 2 — Create a Virtual Environment](#step-2--create-a-virtual-environment)
- [Step 3 — Install Dependencies](#step-3--install-dependencies)
- [Step 4 — Configure Environment Variables](#step-4--configure-environment-variables)
- [Step 5 — Apply Database Migrations](#step-5--apply-database-migrations)
- [Step 6 — Create a Superuser](#step-6--create-a-superuser)
- [Step 7 — Load Sample Data (Optional)](#step-7--load-sample-data-optional)
- [Step 8 — Run the Development Server](#step-8--run-the-development-server)
- [Verifying the Installation](#verifying-the-installation)
- [Common Setup Issues](#common-setup-issues)

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|----------------|-------|
| Python | 3.11 | 3.12+ also supported |
| pip | 23+ | Bundled with Python 3.11 |
| git | Any recent version | For cloning the repo |

> **Note:** A virtual environment tool (`venv`, `virtualenv`, or `conda`) is strongly recommended to keep project dependencies isolated.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/HarshSharma2411/EdtechCRM_Repo.git
cd EdtechCRM_Repo
```

---

## Step 2 — Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (Command Prompt)

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your terminal prompt when the environment is active.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---------|---------|
| `django>=6.0` | Core web framework |
| `djangorestframework>=3.17` | REST API toolkit |
| `djangorestframework-simplejwt>=5.5` | JWT authentication |
| `django-cors-headers>=4.9` | CORS header management |
| `pillow>=12.0` | Image upload processing |

---

## Step 4 — Configure Environment Variables

The project ships with sane development defaults in `edtech_crm/settings.py`. For local development, no additional configuration is required. However, before going to production, the following values **must** be overridden via environment variables or a `.env` file:

| Setting | Default | Production Recommendation |
|---------|---------|--------------------------|
| `SECRET_KEY` | Insecure placeholder | Generate a long random string with `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DEBUG` | `True` | Set to `False` |
| `ALLOWED_HOSTS` | `['localhost', '127.0.0.1']` | Add your domain(s) |
| `DATABASES` | SQLite | Use PostgreSQL (see [Deployment Guide](deployment.md)) |

> See [Deployment Guide](deployment.md) for production environment configuration.

---

## Step 5 — Apply Database Migrations

```bash
python manage.py migrate
```

This creates the SQLite database file (`db.sqlite3`) in the project root and applies all migrations, including creating the JWT token blacklist tables.

---

## Step 6 — Create a Superuser

A Django superuser is required to access the CRM dashboard and the admin panel.

```bash
python manage.py createsuperuser
```

You will be prompted for a username, email address, and password. This account will have `is_staff=True` and `is_superuser=True`, granting full CRM access.

---

## Step 7 — Load Sample Data (Optional)

If you want to explore the application with pre-populated data, you can create sample records through the Django admin panel or directly via the CRM dashboard after logging in.

Example using the Django shell:

```python
# Run: python manage.py shell

from core.models import Instructor, Course, Batch, Student
from datetime import date, timedelta

# Create an instructor
instructor = Instructor.objects.create(
    first_name='Priya',
    last_name='Sharma',
    email='priya@example.com',
    bio='Senior Data Science instructor with 8 years of experience.',
    is_active=True,
)

# Create a course
course = Course.objects.create(
    title='Python for Data Science',
    slug='python-for-data-science',
    description='A comprehensive introduction to Python for data analysis.',
    duration_weeks=10,
    fee=15000,
    instructor=instructor,
    status='active',
)

# Create a batch
batch = Batch.objects.create(
    name='June 2026 Weekend',
    course=course,
    instructor=instructor,
    start_date=date.today() + timedelta(days=7),
    end_date=date.today() + timedelta(days=77),
    max_seats=25,
    status='upcoming',
)

print(f'Created: {instructor}, {course}, {batch}')
```

---

## Step 8 — Run the Development Server

```bash
python manage.py runserver
```

The server starts at `http://127.0.0.1:8000/` by default. To use a different port:

```bash
python manage.py runserver 8080
```

---

## Verifying the Installation

Open a browser and verify the following URLs are reachable:

| URL | Expected Result |
|-----|----------------|
| `http://127.0.0.1:8000/` | Public portal homepage with "Featured Courses" section |
| `http://127.0.0.1:8000/courses/` | Course catalogue (empty if no courses added) |
| `http://127.0.0.1:8000/crm/login/` | CRM staff login form |
| `http://127.0.0.1:8000/admin/` | Django admin login |
| `http://127.0.0.1:8000/api/auth/token/` | Returns 405 Method Not Allowed on GET (correct — POST only) |

Log in to the CRM at `/crm/login/` using the superuser credentials you created in Step 6.

---

## Common Setup Issues

### `ModuleNotFoundError: No module named 'PIL'`

Pillow was not installed correctly.

```bash
pip install pillow
```

### `django.db.utils.OperationalError: no such table: ...`

Migrations have not been applied.

```bash
python manage.py migrate
```

### `TemplateDoesNotExist` error

The `TEMPLATES` setting requires `BASE_DIR / 'templates'` to exist. Confirm the `templates/` directory is present in the project root.

### Static files not loading

In development, static files are served automatically when `DEBUG=True`. Ensure `STATICFILES_DIRS` includes `BASE_DIR / 'static'` and that the `static/` directory exists.

### Port 8000 already in use

```bash
python manage.py runserver 8080
```

Or find and kill the process using port 8000:

```bash
# macOS / Linux
lsof -ti:8000 | xargs kill -9

# Windows PowerShell
netstat -ano | findstr :8000
# then: taskkill /PID <PID> /F
```
