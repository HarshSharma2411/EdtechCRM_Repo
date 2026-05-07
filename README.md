# EdTech CRM

A Customer Relationship Management (CRM) system purpose-built for educational technology organisations. EdTech CRM enables staff to manage students, instructors, courses, batches, and enrolments through a secure internal dashboard while also providing a public-facing website where prospective learners can discover courses and submit enrolment requests.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Running Tests](#running-tests)
- [Contributing](#contributing)

---

## Features

| Area | Capabilities |
|------|-------------|
| **Student Management** | Add, view, edit, delete students; status tracking (pending → active → graduated / dropped) |
| **Instructor Management** | Profile management with bio and photo; active/inactive toggling |
| **Course Catalogue** | Draft / Active / Archived lifecycle; automatic unique slug generation |
| **Batch Scheduling** | Link batches to courses and instructors; seat-capacity enforcement |
| **Enrolment Workflow** | Learners request enrolment via the public site; staff review and approve/reject in the CRM |
| **Public Portal** | Homepage, course catalogue, learner registration, and learner dashboard |
| **REST API** | JWT-authenticated endpoints for staff authentication (`/api/auth/`) |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Django 6+ |
| REST API | Django REST Framework + SimpleJWT |
| Database | SQLite (development) — swap to PostgreSQL for production |
| Image handling | Pillow |
| CORS | django-cors-headers |
| Frontend | Django Templates (server-rendered HTML) |

---

## Quick Start

### Prerequisites

- Python 3.11 or newer
- `pip` and `venv` (or any virtual-environment tool)

### 1 — Clone the repository

```bash
git clone https://github.com/HarshSharma2411/EdtechCRM_Repo.git
cd EdtechCRM_Repo
```

### 2 — Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Apply migrations

```bash
python manage.py migrate
```

### 5 — Create a superuser (CRM admin)

```bash
python manage.py createsuperuser
```

### 6 — Start the development server

```bash
python manage.py runserver
```

Open your browser:

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | Public portal homepage |
| `http://127.0.0.1:8000/crm/` | Staff CRM dashboard (requires login) |
| `http://127.0.0.1:8000/admin/` | Django admin panel |
| `http://127.0.0.1:8000/api/auth/token/` | JWT token endpoint |

---

## Project Structure

```
EdtechCRM_Repo/
├── edtech_crm/           # Django project configuration
│   ├── settings.py       # Application settings
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI entry point
├── core/                 # Main application (CRM + public portal)
│   ├── models.py         # Data models: Student, Instructor, Course, Batch, Enrollment
│   ├── views.py          # CRM (staff) views
│   ├── public_views.py   # Public portal views
│   ├── forms.py          # Django forms
│   ├── urls.py           # CRM URL patterns (/crm/...)
│   ├── public_urls.py    # Public URL patterns (/...)
│   ├── admin.py          # Django admin registrations
│   └── tests.py          # Automated test suite
├── accounts/             # Authentication application
│   ├── views.py          # JWT auth API views
│   └── urls.py           # Auth URL patterns (/api/auth/...)
├── templates/            # HTML templates
│   ├── crm/              # Staff dashboard templates
│   └── public/           # Public portal templates
├── static/               # Static assets (CSS, JS, images)
├── media/                # User-uploaded files (photos, thumbnails)
├── requirements.txt      # Python dependencies
├── manage.py             # Django management script
└── docs/                 # Project documentation
```

---

## Documentation

Detailed documentation is located in the [`docs/`](docs/) directory:

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture and component overview |
| [Setup Guide](docs/setup.md) | Detailed installation and configuration instructions |
| [Database Schema](docs/database.md) | Data models, fields, and relationships |
| [API Reference](docs/api.md) | REST API endpoints and usage |
| [User Roles & Permissions](docs/user-roles.md) | Access levels and permission model |
| [Development Guide](docs/development.md) | Coding standards, workflow, and best practices |
| [Testing Guide](docs/testing.md) | How to write and run tests |
| [Deployment Guide](docs/deployment.md) | Production deployment instructions |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |

---

## Running Tests

```bash
python manage.py test
```

Expected output: all tests pass. See [Testing Guide](docs/testing.md) for details on writing new tests.

---

## Contributing

1. Follow the coding guidelines in [Development Guide](docs/development.md).
2. All functions must use **PascalCase** naming and include a comprehensive docstring.
3. Every function must have at least one corresponding `assert`-based test.
4. Run `python manage.py test` before submitting a pull request.
