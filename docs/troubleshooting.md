# Troubleshooting Guide

This document covers common issues encountered when developing, running, and deploying EdTech CRM, along with their solutions.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [Authentication Issues](#authentication-issues)
- [Form Validation Issues](#form-validation-issues)
- [Static and Media Files](#static-and-media-files)
- [Test Failures](#test-failures)
- [REST API Issues](#rest-api-issues)
- [Production Issues](#production-issues)
- [Getting More Help](#getting-more-help)

---

## Installation Issues

### `ModuleNotFoundError: No module named 'PIL'`

**Cause:** Pillow is not installed or the virtual environment is not activated.

**Solution:**

```bash
# Ensure your virtual environment is active
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows

pip install pillow
```

---

### `ModuleNotFoundError: No module named 'rest_framework'`

**Cause:** Dependencies are not installed.

**Solution:**

```bash
pip install -r requirements.txt
```

---

### `django.core.exceptions.ImproperlyConfigured: SECRET_KEY ...`

**Cause:** The `SECRET_KEY` setting is empty or missing.

**Solution:** Ensure `edtech_crm/settings.py` contains a non-empty `SECRET_KEY`. For production, set it via an environment variable (see [Deployment Guide](deployment.md)).

---

## Database Issues

### `django.db.utils.OperationalError: no such table: ...`

**Cause:** Migrations have not been applied.

**Solution:**

```bash
python manage.py migrate
```

If the problem persists after running migrations, try:

```bash
python manage.py showmigrations          # List migration status
python manage.py migrate --run-syncdb    # Sync unmigrated apps
```

---

### `django.db.utils.IntegrityError: UNIQUE constraint failed: core_student.email`

**Cause:** Attempting to create a student with an email address that already exists.

**Solution:** Check whether a student with that email already exists before creating a new record:

```python
if Student.objects.filter(email=email).exists():
    # Handle duplicate — update or show error
    pass
```

---

### `django.db.utils.IntegrityError: UNIQUE constraint failed: core_enrollment.student_id, core_enrollment.batch_id`

**Cause:** Attempting to enrol a student in a batch they are already enrolled in.

**Solution:** The `EnrollmentForm` validates this automatically. If you are inserting records programmatically, check for existing enrolments first:

```python
if not Enrollment.objects.filter(student=student, batch=batch).exists():
    Enrollment.objects.create(student=student, batch=batch, status='active')
```

---

### `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Cause:** The database contains migration records that do not match the current migration files. This can happen after switching branches.

**Solution (development only — deletes all data):**

```bash
# Remove the SQLite database and re-migrate
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## Authentication Issues

### CRM Login Fails with "Invalid credentials or insufficient permissions"

**Cause 1:** Wrong username or password.

**Solution:** Verify the credentials. Reset the password via Django admin or the management command:

```bash
python manage.py changepassword <username>
```

**Cause 2:** The user account does not have `is_staff=True`.

**Solution:** Grant staff status via the Django admin panel:

1. Go to `/admin/auth/user/`.
2. Click the user.
3. Tick **Staff status** and save.

Or via the shell:

```python
# python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='your_username')
user.is_staff = True
user.save()
```

---

### Learner Cannot Log In to the Public Portal

**Cause 1:** Wrong email or password.

**Cause 2:** The student record does not have a `password_hash` set (e.g., imported records).

**Solution:** Reset the learner's password via the shell:

```python
# python manage.py shell
from core.models import Student
student = Student.objects.get(email='learner@example.com')
student.set_password('NewPassword123!')
student.save()
```

---

### JWT Token Returns 401 After Login

**Cause:** The access token has expired (lifetime: 8 hours).

**Solution:** Use the refresh token to obtain a new access token:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your_refresh_token>"}'
```

---

### JWT Token Returns 403 "Staff access only"

**Cause:** The user exists in the database but does not have `is_staff=True`.

**Solution:** See [CRM Login Fails](#crm-login-fails-with-invalid-credentials-or-insufficient-permissions) above to grant staff status.

---

## Form Validation Issues

### "End date cannot be earlier than the start date."

**Cause:** The batch `end_date` is set to a date before `start_date`.

**Solution:** Ensure `end_date >= start_date` when creating or editing a batch.

---

### "No seats are available in the selected batch."

**Cause:** The batch has reached its `max_seats` limit (counted by `active` enrolments).

**Solution:** Either:
- Increase the batch's `max_seats` in the CRM (`/crm/batches/<pk>/edit/`).
- Change some existing enrolments to `completed`, `dropped`, or `cancelled` to free up seats.

---

### "This student is already enrolled in the selected batch."

**Cause:** An `Enrollment` record already exists for this student + batch combination.

**Solution:** Edit the existing enrolment instead of creating a new one.

---

### Slug Not Being Generated for New Course

**Cause:** The course was created directly via `Course.objects.create()` without using `CourseForm`.

**Solution:** Always use `CourseForm` to create courses, or manually generate the slug:

```python
from django.utils.text import slugify
from core.models import Course

course = Course(title='My New Course', ...)
course.slug = slugify(course.title)
course.save()
```

---

## Static and Media Files

### Static Files Return 404 in Development

**Cause 1:** `DEBUG=False` in development. Django does not serve static files when `DEBUG=False`.

**Solution:** Set `DEBUG=True` in `settings.py` for local development.

**Cause 2:** The `static/` directory does not exist.

**Solution:** Create the directory:

```bash
mkdir -p static
```

---

### Uploaded Images Not Displaying

**Cause 1:** `MEDIA_ROOT` directory does not exist.

**Solution:**

```bash
mkdir -p media
```

**Cause 2:** `MEDIA_URL` and `MEDIA_ROOT` are not configured in `settings.py`.

**Solution:** Verify these settings are present:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

And that the root `urls.py` includes:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [...] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Test Failures

### Tests Fail with `django.test.utils.DatabaseBlockedError`

**Cause:** A test is trying to access the database without inheriting from `django.test.TestCase`.

**Solution:** Ensure all database-accessing test classes inherit from `TestCase`:

```python
from django.test import TestCase

class MyTests(TestCase):
    ...
```

---

### Test Database Not Being Reset Between Tests

**Cause:** Each `TestCase` class runs in a transaction that is rolled back after each test. If you are using `TransactionTestCase` or raw database connections, data may persist.

**Solution:** Use `django.test.TestCase` (not `TransactionTestCase`) for standard tests.

---

### `AssertionError: 302 != 200` in View Tests

**Cause:** The view is redirecting (e.g., to the login page) because the test client is not authenticated.

**Solution:** Log in before making the request:

```python
self.client.login(username='stafftest', password='TestPass123!')
response = self.client.get(reverse('core:dashboard'))
assert response.status_code == 200
```

---

## REST API Issues

### `{"detail": "Authentication credentials were not provided."}`

**Cause:** The `Authorization` header is missing or malformed.

**Solution:** Include the header in your request:

```
Authorization: Bearer <your_access_token>
```

---

### `{"detail": "Token is invalid or expired", "code": "token_not_valid"}`

**Cause:** The access token has expired or has been tampered with.

**Solution:** Use the refresh token to obtain a new access token (see [JWT Token Returns 401](#jwt-token-returns-401-after-login)).

---

### CORS Error in Browser

**Cause:** The frontend origin is not in `CORS_ALLOWED_ORIGINS` in `settings.py`.

**Solution:** Add your frontend's origin:

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',    # React dev server
    'https://app.edtech.example.com',
]
```

---

## Production Issues

### `500 Internal Server Error` After Deployment

**Step 1:** Check Gunicorn error logs:

```bash
sudo journalctl -u edtech_crm -n 50
# or
tail -50 /var/log/edtech_crm/error.log
```

**Step 2:** Run Django's deployment check:

```bash
python manage.py check --deploy
```

**Step 3:** Temporarily enable `DEBUG=True` on the server to see the detailed error page (revert immediately after diagnosing).

---

### Static Files Return 404 in Production

**Cause:** `collectstatic` was not run or Nginx is not configured to serve the static root.

**Solution:**

```bash
python manage.py collectstatic --no-input
sudo systemctl reload nginx
```

Verify Nginx's `location /static/` block points to the correct `STATIC_ROOT` path.

---

### Gunicorn Workers Failing or Timing Out

**Cause:** Long-running requests or insufficient worker processes.

**Solution:**

- Increase the number of workers in the systemd service file.
- Increase the `--timeout` value for Gunicorn.
- Profile slow database queries with Django Debug Toolbar (development only).

---

## Getting More Help

If the above solutions do not resolve your issue:

1. Check Django's official documentation: [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
2. Search the Django REST Framework docs: [https://www.django-rest-framework.org/](https://www.django-rest-framework.org/)
3. Review the project's existing test cases in `core/tests.py` for examples of expected behaviour.
4. Open an issue in the repository with a clear description of the problem, the steps to reproduce it, and the full error traceback.
