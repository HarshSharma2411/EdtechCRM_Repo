# Architecture

This document describes the high-level architecture of EdTech CRM, its major components, and how they interact.

---

## Table of Contents

- [Overview](#overview)
- [Component Diagram](#component-diagram)
- [Django Applications](#django-applications)
  - [edtech_crm (project)](#edtech_crm-project)
  - [core](#core)
  - [accounts](#accounts)
- [URL Routing](#url-routing)
- [Authentication Architecture](#authentication-architecture)
- [Data Flow](#data-flow)
- [Template Structure](#template-structure)

---

## Overview

EdTech CRM is a Django monolith with two primary user-facing surfaces:

1. **Public Portal** — An unauthenticated website where prospective learners browse courses, register accounts, and submit enrolment requests.
2. **Staff CRM Dashboard** — A session-authenticated internal application where staff manage students, instructors, courses, batches, and enrolments.

A thin **REST API layer** (`/api/auth/`) provides JWT authentication for programmatic clients (e.g., a future single-page application or mobile app).

```
┌──────────────────────────────────────────────────────────┐
│                        Browser / Client                  │
└──────┬──────────────────┬────────────────────────────────┘
       │                  │                        │
  Public Portal      CRM Dashboard            REST API
  (anonymous)       (session auth)           (JWT auth)
  /  →  core/        /crm/ →  core/         /api/ → accounts/
  public_urls.py     urls.py                urls.py
       │                  │                        │
       └──────────────────┴────────────────────────┘
                          │
              ┌───────────▼──────────┐
              │      Django ORM      │
              └───────────┬──────────┘
                          │
              ┌───────────▼──────────┐
              │   SQLite / PostgreSQL │
              └──────────────────────┘
```

---

## Component Diagram

```
edtech_crm/           ← Project package (settings, root URLs, WSGI)
├── core/             ← Primary app
│   ├── models.py     ← ORM models (Student, Instructor, Course, Batch, Enrollment)
│   ├── views.py      ← CRM staff views (session-authenticated)
│   ├── public_views.py ← Public portal views (anonymous + learner session)
│   ├── forms.py      ← Django ModelForms with server-side validation
│   ├── urls.py       ← /crm/ URL patterns
│   ├── public_urls.py← / URL patterns
│   └── admin.py      ← Django admin registrations
└── accounts/         ← Authentication app
    ├── views.py      ← StaffLoginView, StaffLogoutView, StaffMeView
    └── urls.py       ← /api/auth/ URL patterns
```

---

## Django Applications

### edtech_crm (project)

The project package contains global configuration and the root URL dispatcher.

| File | Responsibility |
|------|---------------|
| `settings.py` | Installed apps, middleware, database, JWT settings, static/media paths |
| `urls.py` | Routes traffic to `core`, `accounts`, and Django admin |
| `wsgi.py` | WSGI entry point for production servers |

### core

The main application that implements all business logic.

| Module | Responsibility |
|--------|---------------|
| `models.py` | Defines `Instructor`, `Course`, `Batch`, `Student`, and `Enrollment` models |
| `views.py` | 25+ CRM views for CRUD operations on all entities; protected by `@login_required` |
| `public_views.py` | Public-facing views: homepage, course catalogue, learner auth, learner dashboard |
| `forms.py` | Validation logic for all ModelForms; includes capacity checks and slug generation |
| `urls.py` | URL patterns under `/crm/` for all CRM operations |
| `public_urls.py` | URL patterns under `/` for the public portal |
| `admin.py` | Django admin panel registrations for back-office access |
| `tests.py` | Automated tests for forms and the public learner flow |

### accounts

A focused app that provides the JWT-based REST API for staff authentication.

| Module | Responsibility |
|--------|---------------|
| `views.py` | `StaffLoginView` (JWT obtain), `StaffLogoutView` (token blacklist), `StaffMeView` (current user info) |
| `urls.py` | URL patterns under `/api/auth/` |

---

## URL Routing

```
/                        → core.public_urls (public portal)
/crm/                    → core.urls (staff CRM dashboard)
/api/auth/               → accounts.urls (JWT REST API)
/admin/                  → Django admin
/media/                  → Served by Django in development
```

### Public Portal Routes (`/`)

| Pattern | View | Description |
|---------|------|-------------|
| `/` | `home` | Homepage with featured courses |
| `/about/` | `about` | About page |
| `/contact/` | `contact` | Contact page |
| `/courses/` | `course_catalog` | Active course listing |
| `/courses/<slug>/` | `course_detail` | Individual course detail |
| `/register/` | `learner_register` | Learner self-registration |
| `/login/` | `learner_login` | Learner login |
| `/logout/` | `learner_logout` | Learner logout |
| `/dashboard/` | `learner_dashboard` | Authenticated learner's dashboard |
| `/enrollment-request/` | `enrollment_request` | Submit an enrolment request |

### CRM Routes (`/crm/`)

| Pattern | Description |
|---------|-------------|
| `login/` | Staff login |
| `logout/` | Staff logout |
| `` (empty) | Dashboard with summary statistics |
| `students/` | Student list, add, detail, edit, delete |
| `instructors/` | Instructor list, add, detail, edit, delete |
| `courses/` | Course list, add, detail, edit, delete |
| `batches/` | Batch list, add, detail, edit, delete |
| `enrollments/` | Enrolment list, add, edit, delete |

### API Routes (`/api/auth/`)

| Pattern | Method | Description |
|---------|--------|-------------|
| `token/` | POST | Obtain JWT access + refresh tokens |
| `token/refresh/` | POST | Refresh an access token |
| `logout/` | POST | Blacklist a refresh token |
| `me/` | GET | Return authenticated staff user details |

---

## Authentication Architecture

EdTech CRM uses **two independent authentication mechanisms**:

### 1. Staff Session Authentication

Used by the CRM dashboard (`/crm/`). Standard Django session-based login via Django's built-in `auth` system. Views are protected with `@login_required`. Only users with `is_staff=True` are granted access.

### 2. Learner Session Authentication

Used by the public portal (`/`). A custom session-key approach stores the learner's primary key in `request.session['learner_id']`. A decorator `learner_login_required` checks this key on protected views. This is completely separate from Django's `User` model — learners are `Student` model instances with a bcrypt-hashed password field.

### 3. JWT Authentication (REST API)

Used by the `/api/auth/` endpoints. Staff users obtain short-lived access tokens (8 hours) and long-lived refresh tokens (7 days). Tokens rotate on refresh and are blacklisted on logout using `rest_framework_simplejwt.token_blacklist`.

---

## Data Flow

### Learner Enrolment Request Flow

```
1. Learner visits /courses/ and browses active courses
2. Learner registers at /register/ → Student record created (status=pending)
3. Learner logs in at /login/
4. Learner submits enrolment request at /enrollment-request/
   → Enrollment record created (status=pending)
5. Staff logs into /crm/ and sees pending enrolments in the dashboard
6. Staff opens /crm/enrollments/<pk>/edit/ and changes status to active
7. Student status remains pending until staff updates it separately
```

### CRM CRUD Flow

```
1. Staff logs in at /crm/login/
2. Staff navigates to entity list (e.g., /crm/students/)
3. Staff creates/edits via form → Django ModelForm validates data
4. On success, redirect to detail view with success flash message
5. On error, re-render form with validation errors
```

---

## Template Structure

```
templates/
├── crm/                          # Staff CRM templates
│   ├── base.html                 # Base layout with navigation
│   ├── dashboard.html            # Dashboard with stats
│   ├── login.html                # Staff login
│   ├── confirm_delete.html       # Generic delete confirmation
│   ├── students/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── form.html
│   ├── instructors/
│   ├── courses/
│   ├── batches/
│   └── enrollments/
└── public/                       # Public portal templates
    ├── base.html
    ├── home.html
    ├── about.html
    ├── contact.html
    ├── courses/
    │   ├── list.html
    │   └── detail.html
    ├── auth/
    │   ├── register.html
    │   └── login.html
    └── learner/
        ├── dashboard.html
        └── enrollment_request.html
```
