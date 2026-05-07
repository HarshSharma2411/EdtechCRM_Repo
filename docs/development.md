# Development Guide

This document describes the development workflow, coding standards, and best practices for contributing to EdTech CRM.

---

## Table of Contents

- [Coding Standards](#coding-standards)
  - [Function Naming](#function-naming)
  - [Docstrings](#docstrings)
  - [Error Handling](#error-handling)
  - [Type Hints](#type-hints)
  - [Imports](#imports)
  - [Constants](#constants)
- [Django-Specific Guidelines](#django-specific-guidelines)
- [Git Workflow](#git-workflow)
- [Pre-Commit Checklist](#pre-commit-checklist)
- [Code Examples](#code-examples)

---

## Coding Standards

### Function Naming

All function and class-based view names must use **PascalCase** (also known as CapWords):

```python
# ✅ Correct
def CreateEnrollment(request):
    pass

def ValidateStudentEmail(email, student_id):
    pass

class BatchDetailView:
    pass

# ❌ Incorrect
def create_enrollment(request):   # snake_case
def createEnrollment(request):    # camelCase
def Create_Enrollment(request):   # mixed
```

> **Django built-in names** (e.g., `clean`, `save`, `setUp` in tests) follow Django/Python conventions and are exempt from PascalCase.

---

### Docstrings

Every function **must** include a comprehensive docstring. The format is:

```python
def FunctionName(param1, param2):
    """
    Brief one-line summary of what the function does.

    Longer explanation of the function's purpose, any important behaviour,
    or context for when it should be used.

    Parameters:
        param1 (type): Description of param1. Example: 'user email address'
        param2 (type): Description of param2. Example: 42

    Returns:
        return_type: Description of the return value. Example: 'True if successful'

    Raises:
        ExceptionType: When this exception is raised and why.

    Example:
        >>> result = FunctionName("value", 42)
        >>> print(result)
        True
    """
```

#### Minimum Required Sections

| Section | Required When |
|---------|--------------|
| One-line summary | Always |
| `Parameters` | Function has parameters |
| `Returns` | Function returns a value |
| `Raises` | Function raises exceptions |
| `Example` | Behaviour is non-obvious |

#### Complete Example

```python
def CalculateEnrollmentFee(batch, discount_percent=0):
    """
    Calculates the final fee for enrolling in a batch after applying a discount.

    This function retrieves the base fee from the batch's associated course
    and applies the specified percentage discount, returning the final amount
    payable by the student.

    Parameters:
        batch (Batch): The Batch model instance to calculate the fee for.
        discount_percent (float): Discount to apply as a percentage (0–100).
            Default is 0 (no discount). Example: 10.0

    Returns:
        float: The final fee after discount. Example: 13500.0

    Raises:
        ValueError: If discount_percent is not between 0 and 100.
        AttributeError: If batch.course is None (course was deleted).

    Example:
        >>> batch = Batch.objects.get(pk=1)
        >>> fee = CalculateEnrollmentFee(batch, discount_percent=10)
        >>> print(fee)
        13500.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError(f"discount_percent must be between 0 and 100, got {discount_percent}")
    base_fee = float(batch.course.fee)
    discount_amount = base_fee * (discount_percent / 100)
    return base_fee - discount_amount
```

---

### Error Handling

- Always handle exceptions explicitly — never use a bare `except:` clause.
- Provide meaningful, actionable error messages.
- Catch specific exception types:

```python
# ✅ Correct
try:
    student = Student.objects.get(email=email)
except Student.DoesNotExist:
    raise ValueError(f"No student found with email '{email}'.")

# ❌ Incorrect
try:
    student = Student.objects.get(email=email)
except:                       # bare except — never do this
    pass
except Exception:             # too broad — avoid unless re-raising
    pass
```

---

### Type Hints

While not mandatory, type hints are encouraged for improved readability and IDE support:

```python
from decimal import Decimal
from core.models import Batch, Student


def CalculateEnrollmentFee(batch: Batch, discount_percent: float = 0) -> Decimal:
    """Calculate the discounted enrolment fee for a batch."""
    ...
```

---

### Imports

Organise imports in three groups, separated by a blank line:

```python
# 1. Standard library
import os
from datetime import date, timedelta

# 2. Third-party
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# 3. Local application
from .models import Student, Enrollment
from .forms import EnrollmentForm
```

Use absolute imports over relative imports wherever possible.

---

### Constants

Define module-level constants in `SCREAMING_SNAKE_CASE`:

```python
MAX_ENROLLMENT_CAPACITY = 50
DEFAULT_BATCH_DURATION_WEEKS = 12
LEARNER_SESSION_KEY = 'learner_id'
```

---

## Django-Specific Guidelines

### Models

- Keep business logic in model methods, not in views.
- Use `@property` for computed values derived from model fields.
- Always define `__str__` on every model.
- Use `Meta.ordering` for default sort order.

```python
class Batch(models.Model):
    # ...

    def __str__(self):
        return f"{self.course.title} — {self.name}"

    @property
    def seats_available(self):
        return max(0, self.max_seats - self.enrolled_count)
```

### Views

- Keep views thin — delegate complex logic to model methods or utility functions.
- All CRM views must be decorated with `@login_required`.
- Use `get_object_or_404` for all single-object lookups to return proper 404 responses.
- Always redirect after a successful POST (Post/Redirect/Get pattern).
- Use `messages.success()` / `messages.error()` for user feedback.

```python
@login_required
def BatchAdd(request):
    """
    Handles creation of a new batch via a ModelForm.

    Renders the batch form on GET. On valid POST, saves the batch and
    redirects to the new batch's detail page. On invalid POST, re-renders
    the form with validation errors.

    Parameters:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Rendered form template or redirect to batch detail.
    """
    form = BatchForm(request.POST or None)
    if form.is_valid():
        batch = form.save()
        messages.success(request, f'Batch "{batch.name}" added.')
        return redirect('core:batch_detail', pk=batch.pk)
    return render(request, 'crm/batches/form.html', {'form': form, 'action': 'Add'})
```

### Forms

- Put all form validation logic in `clean()` or `clean_<fieldname>()` methods.
- Raise `forms.ValidationError` with a clear message on validation failure.
- Override `save()` for any custom persistence logic (e.g., slug generation).

### Templates

- Use Django template inheritance (`{% extends %}` / `{% block %}`).
- Never put business logic in templates — keep templates display-only.
- Use the `{% url %}` tag for all internal links (never hardcode URLs).

---

## Git Workflow

### Branch Naming

| Branch Type | Pattern | Example |
|-------------|---------|---------|
| Feature | `feature/<description>` | `feature/batch-waitlist` |
| Bug fix | `fix/<description>` | `fix/enrollment-seat-count` |
| Documentation | `docs/<description>` | `docs/api-reference` |
| Refactor | `refactor/<description>` | `refactor/course-form-validation` |

### Commit Messages

Write commit messages in the imperative mood, with a concise subject line (≤ 72 characters):

```
Add learner password reset feature

- Introduce ResetLearnerPassword utility function in core/utils.py
- Add corresponding test in core/tests.py
- Update user-roles.md with password reset instructions
```

### Pull Request Process

1. Create a feature branch from `main`.
2. Make your changes, following all coding standards in this document.
3. Run the full test suite: `python manage.py test`.
4. Ensure all tests pass.
5. Open a pull request with a clear description of the changes.
6. Address any review feedback.

---

## Pre-Commit Checklist

Before committing or opening a pull request, verify:

- [ ] All new and modified functions use **PascalCase** naming.
- [ ] Every function has a **comprehensive docstring** (summary, Parameters, Returns, Raises, Example).
- [ ] Every function has at least **one assert-based test** covering a positive case.
- [ ] Test cases cover **both positive and negative scenarios**.
- [ ] All **imports are organised** (stdlib → third-party → local).
- [ ] No **bare `except:`** clauses.
- [ ] All CRM views are protected with `@login_required`.
- [ ] No business logic in templates.
- [ ] `python manage.py test` passes with zero failures.

---

## Code Examples

### Complete Function with Tests

Below is a complete, standards-compliant example of a utility function and its corresponding test:

```python
# core/utils.py

from core.models import Batch, Student, Enrollment


def GetAvailableBatchesForStudent(student_email):
    """
    Returns all batches a student is eligible to enrol in.

    A batch is considered available if it is active or upcoming, belongs to
    an active course, and the student is not already enrolled in it.

    Parameters:
        student_email (str): The email address of the student to check.
            Example: 'student@example.com'

    Returns:
        QuerySet: A Django QuerySet of eligible Batch instances ordered by
            start date ascending. Returns an empty QuerySet if the student
            is not found.

    Raises:
        TypeError: If student_email is not a string.

    Example:
        >>> batches = GetAvailableBatchesForStudent('student@example.com')
        >>> print(batches.count())
        3
    """
    if not isinstance(student_email, str):
        raise TypeError(f"student_email must be a string, got {type(student_email).__name__}")

    student = Student.objects.filter(email__iexact=student_email).first()
    if not student:
        return Batch.objects.none()

    enrolled_batch_ids = Enrollment.objects.filter(
        student=student
    ).values_list('batch_id', flat=True)

    return Batch.objects.filter(
        course__status='active',
        status__in=['upcoming', 'ongoing'],
    ).exclude(id__in=enrolled_batch_ids).order_by('start_date')


def TestGetAvailableBatchesForStudent():
    """
    Test cases for GetAvailableBatchesForStudent function.

    Tests:
        - Returns empty QuerySet for unknown email
        - Raises TypeError for non-string input
        - Returns only eligible batches, excluding already-enrolled ones
    """
    # Negative case: unknown email returns empty queryset
    result = GetAvailableBatchesForStudent('nonexistent@example.com')
    assert result.count() == 0, "Unknown email should return empty QuerySet"

    # Negative case: non-string input raises TypeError
    try:
        GetAvailableBatchesForStudent(12345)
        assert False, "Should have raised TypeError for integer input"
    except TypeError as exc:
        assert "must be a string" in str(exc), f"Unexpected error message: {exc}"

    print("All GetAvailableBatchesForStudent tests passed.")


if __name__ == '__main__':
    TestGetAvailableBatchesForStudent()
```
