# User Roles & Permissions

This document explains the two user types in EdTech CRM, their access rights, and how authentication works for each.

---

## Table of Contents

- [Overview](#overview)
- [Role: Staff (CRM User)](#role-staff-crm-user)
- [Role: Learner (Student)](#role-learner-student)
- [Permission Matrix](#permission-matrix)
- [Authentication Mechanisms](#authentication-mechanisms)
- [Creating Staff Users](#creating-staff-users)
- [Managing Learner Accounts](#managing-learner-accounts)

---

## Overview

EdTech CRM has two distinct user roles:

| Role | Identity Model | Authentication Method | Primary Interface |
|------|---------------|----------------------|-------------------|
| **Staff** | Django `User` (`is_staff=True`) | Session or JWT | CRM Dashboard (`/crm/`) and REST API (`/api/auth/`) |
| **Learner** | `core.Student` model | Custom session key | Public Portal (`/`) |

These two roles are completely independent — a learner session does not grant access to the CRM, and a staff session does not grant access to the learner dashboard.

---

## Role: Staff (CRM User)

### Who Are Staff Users?

Staff users are employees or administrators of the educational organisation who manage the day-to-day operations of the CRM. They are Django `User` instances with `is_staff=True`.

### What Can Staff Do?

Staff users have full CRUD (Create, Read, Update, Delete) access to all entities in the CRM:

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Students | ✅ | ✅ | ✅ | ✅ |
| Instructors | ✅ | ✅ | ✅ | ✅ |
| Courses | ✅ | ✅ | ✅ | ✅ |
| Batches | ✅ | ✅ | ✅ | ✅ |
| Enrolments | ✅ | ✅ | ✅ | ✅ |

Staff can also:
- View dashboard summary statistics (active students, ongoing batches, pending enrolments)
- Manage all learner-submitted enrolment requests (approve by changing status to `active`, reject by changing to `cancelled`)
- Access the Django admin panel (superusers only)

### Access Control

All CRM views (`/crm/`) are protected with Django's `@login_required` decorator. The login view additionally checks that `user.is_staff=True` before creating a session:

```python
def CrmLogin(request):
    """
    Authenticates a staff user and creates a Django session.

    This view checks both valid credentials and staff status before granting
    access to the CRM dashboard.

    Parameters:
        request (HttpRequest): The incoming HTTP request object.

    Returns:
        HttpResponse: Redirects to the dashboard on success, or re-renders
            the login form with an error message on failure.

    Example:
        POST /crm/login/ with {'username': 'staff', 'password': 'pass'}
        → 302 redirect to /crm/ on success
        → 200 with error message if credentials invalid or user is not staff
    """
    user = authenticate(request, username=username, password=password)
    if user and user.is_staff:
        login(request, user)
        return redirect('core:dashboard')
    messages.error(request, 'Invalid credentials or insufficient permissions.')
```

---

## Role: Learner (Student)

### Who Are Learners?

Learners are prospective or enrolled students who access the public-facing portal. They are instances of the `core.Student` model, **not** Django `User` instances.

### What Can Learners Do?

| Action | Requires Login |
|--------|---------------|
| Browse course catalogue | No |
| View individual course details | No |
| Register a new account | No |
| Log in to the learner portal | — |
| View personal dashboard | Yes |
| Submit an enrolment request | Yes |

Learners **cannot**:
- Access the CRM dashboard (`/crm/`)
- Modify their own student record directly (must contact staff)
- See other students' data
- Access the REST API

### Access Control

Learner-protected views use a custom `learner_login_required` decorator that checks for a session key:

```python
def LearnerLoginRequired(view_func):
    """
    Decorator that restricts access to views requiring an active learner session.

    Checks for a valid 'learner_id' in the Django session. If not found,
    redirects the user to the learner login page with an error message.
    Attaches the Student instance to request.learner for use in the view.

    Parameters:
        view_func (callable): The view function to protect.

    Returns:
        callable: A wrapped view function that checks for learner authentication.

    Example:
        @LearnerLoginRequired
        def MyProtectedView(request):
            # request.learner is available here
            pass
    """
    def wrapped(request, *args, **kwargs):
        learner = _get_current_learner(request)
        if not learner:
            messages.error(request, 'Please log in to access your dashboard.')
            return redirect('public:learner_login')
        request.learner = learner
        return view_func(request, *args, **kwargs)
    return wrapped
```

### Learner Registration and Approval Workflow

1. Learner self-registers at `/register/` — a `Student` record is created with `status='pending'`.
2. Staff reviews the new student in the CRM (`/crm/students/`).
3. Staff changes the student's `status` to `active` to fully activate the account.
4. Learner can now log in and submit enrolment requests.

> **Note:** Learners can log in to the portal regardless of their `status`. The `pending` status is informational for staff review purposes.

---

## Permission Matrix

| Feature | Anonymous | Learner (logged in) | Staff (logged in) |
|---------|-----------|--------------------|--------------------|
| View homepage | ✅ | ✅ | ✅ |
| View course catalogue | ✅ | ✅ | ✅ |
| View course detail page | ✅ | ✅ | ✅ |
| Register as a learner | ✅ | ✅ | ✅ |
| Learner login | ✅ | — | — |
| View learner dashboard | ❌ | ✅ | ❌ |
| Submit enrolment request | ❌ | ✅ | ❌ |
| Access CRM dashboard | ❌ | ❌ | ✅ |
| Manage students (CRM) | ❌ | ❌ | ✅ |
| Manage instructors (CRM) | ❌ | ❌ | ✅ |
| Manage courses (CRM) | ❌ | ❌ | ✅ |
| Manage batches (CRM) | ❌ | ❌ | ✅ |
| Manage enrolments (CRM) | ❌ | ❌ | ✅ |
| Access REST API (`/api/`) | ❌ | ❌ | ✅ |
| Access Django admin | ❌ | ❌ | ✅ (superusers only) |

---

## Authentication Mechanisms

### Staff Authentication (Session-Based)

- **Login URL:** `/crm/login/`
- **Session duration:** Until browser closes or `SESSION_COOKIE_AGE` expires (Django default: 2 weeks)
- **Logout URL:** `/crm/logout/`

### Staff Authentication (JWT-Based)

Used for programmatic API access:

- **Token URL:** `POST /api/auth/token/`
- **Access token lifetime:** 8 hours
- **Refresh token lifetime:** 7 days (rotated on each refresh)
- **Logout URL:** `POST /api/auth/logout/` (blacklists refresh token)

See the [API Reference](api.md) for full details.

### Learner Authentication (Custom Session)

- **Login URL:** `/login/`
- **Session key:** `learner_id` (stores the `Student.pk`)
- **Password storage:** Django-compatible bcrypt hash in `Student.password_hash`
- **Session cycling:** `request.session.cycle_key()` is called on login to prevent session fixation attacks
- **Logout URL:** `/logout/`

---

## Creating Staff Users

### Via Django Management Command

```bash
python manage.py createsuperuser
```

This creates a user with both `is_staff=True` and `is_superuser=True`.

### Via Django Admin

1. Log in to `/admin/` as a superuser.
2. Navigate to **Authentication and Authorization → Users → Add User**.
3. Set username and password, then tick **Staff status** on the user detail page.

### Via Django Shell

```python
# python manage.py shell

from django.contrib.auth import get_user_model

User = get_user_model()


def CreateStaffUser(username, email, password, is_superuser=False):
    """
    Creates a new staff user account.

    Parameters:
        username (str): Unique login username. Example: 'john_staff'
        email (str): Staff member's email address. Example: 'john@edtech.com'
        password (str): Plaintext password (will be hashed). Example: 'SecurePass123!'
        is_superuser (bool): Whether to grant superuser privileges. Default: False.

    Returns:
        User: The newly created Django User instance.

    Raises:
        ValueError: If a user with the given username already exists.

    Example:
        >>> user = CreateStaffUser('john_staff', 'john@edtech.com', 'SecurePass123!')
        >>> print(user.is_staff)
        True
    """
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_staff=True,
        is_superuser=is_superuser,
    )
    return user


new_staff = CreateStaffUser('coordinator1', 'coord@edtech.com', 'TempPass456!')
print(f'Created staff user: {new_staff.username}')
```

---

## Managing Learner Accounts

### Password Reset

Learners cannot reset their own passwords through the portal. Staff must set a new password via the Django shell:

```python
# python manage.py shell

from core.models import Student


def ResetLearnerPassword(email, new_password):
    """
    Resets a learner's portal password.

    Parameters:
        email (str): The learner's registered email address. Example: 'student@example.com'
        new_password (str): The new plaintext password to set. Example: 'NewSecurePass789!'

    Returns:
        bool: True if the password was reset successfully, False if the student was not found.

    Raises:
        ValueError: If new_password does not meet minimum length requirements.

    Example:
        >>> success = ResetLearnerPassword('student@example.com', 'NewPass789!')
        >>> print(success)
        True
    """
    student = Student.objects.filter(email__iexact=email).first()
    if not student:
        return False
    student.set_password(new_password)
    student.save()
    return True


result = ResetLearnerPassword('student@example.com', 'NewTemporaryPass!')
print('Password reset:', result)
```

### Activating a Pending Learner

```python
# python manage.py shell

from core.models import Student


def ActivateLearner(email):
    """
    Changes a learner's status from 'pending' to 'active'.

    Parameters:
        email (str): The learner's registered email address. Example: 'student@example.com'

    Returns:
        bool: True if activated successfully, False if not found or already active.

    Example:
        >>> success = ActivateLearner('student@example.com')
        >>> print(success)
        True
    """
    updated = Student.objects.filter(email__iexact=email, status='pending').update(status='active')
    return updated > 0


result = ActivateLearner('newstudent@example.com')
print('Activated:', result)
```
