# Testing Guide

This document describes how to run existing tests, write new tests, and understand the test structure in EdTech CRM.

---

## Table of Contents

- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Existing Test Cases](#existing-test-cases)
- [Writing New Tests](#writing-new-tests)
  - [Test Naming Convention](#test-naming-convention)
  - [Assert-Based Unit Tests](#assert-based-unit-tests)
  - [Django TestCase for Integration Tests](#django-testcase-for-integration-tests)
- [Test Data Setup](#test-data-setup)
- [Testing Forms](#testing-forms)
- [Testing Views](#testing-views)
- [Testing Models](#testing-models)
- [Testing the REST API](#testing-the-rest-api)

---

## Running Tests

Run the full test suite from the project root:

```bash
python manage.py test
```

Run tests for a specific app:

```bash
python manage.py test core
python manage.py test accounts
```

Run a specific test class:

```bash
python manage.py test core.tests.CoreFormTests
```

Run a specific test method:

```bash
python manage.py test core.tests.CoreFormTests.test_course_form_generates_unique_slug
```

Run with verbose output:

```bash
python manage.py test --verbosity=2
```

Expected output for a clean codebase:

```
Found 9 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.........
----------------------------------------------------------------------
Ran 9 tests in 0.432s

OK
Destroying test database for alias 'default'...
```

---

## Test Structure

Tests are located in each Django application's `tests.py` file:

```
core/tests.py       # Form validation tests + public learner flow tests
accounts/tests.py   # Authentication API tests
```

### Test Classes

| Class | Location | Coverage |
|-------|----------|---------|
| `CoreFormTests` | `core/tests.py` | `CourseForm`, `BatchForm`, `EnrollmentForm` validation |
| `PublicLearnerFlowTests` | `core/tests.py` | Learner registration, login, enrolment request flow |

---

## Existing Test Cases

### CoreFormTests

**`test_course_form_generates_unique_slug`**
Verifies that saving a `CourseForm` with a duplicate title generates a unique slug (e.g., `python-basics-2`).

**`test_batch_form_rejects_reversed_dates`**
Verifies that `BatchForm` raises a validation error when `end_date < start_date`.

**`test_enrollment_form_rejects_full_batch`**
Verifies that `EnrollmentForm` raises a validation error when a batch has no remaining seats.

### PublicLearnerFlowTests

**`test_course_catalog_lists_only_active_courses`**
Verifies the public course catalogue only shows courses with `status='active'`.

**`test_registration_creates_pending_learner_and_separate_session_auth`**
Verifies learner registration creates a `Student` with `status='pending'`, that the learner can then log in, and that the learner session does not grant CRM access.

**`test_enrollment_request_creates_pending_enrollment_visible_in_crm_records`**
Verifies that a logged-in learner can submit an enrolment request and that the resulting `Enrollment` record has `status='pending'`.

---

## Writing New Tests

### Test Naming Convention

Test function and class names must follow **PascalCase** for standalone `assert`-based tests:

```python
def TestCalculateEnrollmentFee():
    """Test cases for CalculateEnrollmentFee function."""
    ...
```

Django `TestCase` methods use the `test_` prefix (Django's standard convention, which uses snake_case for test method names):

```python
class EnrollmentFormTests(TestCase):
    def test_form_rejects_duplicate_enrollment(self):
        ...
```

---

### Assert-Based Unit Tests

For pure Python utility functions, use simple `assert` statements — no test framework required:

```python
def TestCalculateEnrollmentFee():
    """
    Test cases for CalculateEnrollmentFee function.

    Tests:
        - Positive case: valid batch and zero discount
        - Positive case: valid batch with 10% discount
        - Negative case: discount over 100% raises ValueError
        - Negative case: negative discount raises ValueError
    """
    from decimal import Decimal
    from core.models import Batch, Course, Instructor
    from datetime import date, timedelta

    # Arrange
    instructor = Instructor(first_name='Test', last_name='Instructor', email='t@example.com')
    course = Course(title='Test Course', fee=Decimal('15000.00'))
    batch = Batch(name='Test Batch', course=course, start_date=date.today(),
                  end_date=date.today() + timedelta(weeks=10))

    # Act & Assert — positive case, no discount
    result = CalculateEnrollmentFee(batch, discount_percent=0)
    assert result == 15000.0, f"Expected 15000.0, got {result}"

    # Act & Assert — positive case, 10% discount
    result = CalculateEnrollmentFee(batch, discount_percent=10)
    assert result == 13500.0, f"Expected 13500.0, got {result}"

    # Negative case: discount > 100 raises ValueError
    try:
        CalculateEnrollmentFee(batch, discount_percent=150)
        assert False, "Should have raised ValueError for discount_percent > 100"
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)

    # Negative case: negative discount raises ValueError
    try:
        CalculateEnrollmentFee(batch, discount_percent=-5)
        assert False, "Should have raised ValueError for negative discount_percent"
    except ValueError:
        pass  # Expected behaviour

    print("All CalculateEnrollmentFee tests passed.")


if __name__ == '__main__':
    TestCalculateEnrollmentFee()
```

---

### Django TestCase for Integration Tests

Use `django.test.TestCase` when your tests need database access, Django's test client, or any Django infrastructure:

```python
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from core.models import Batch, Course, Instructor, Student, Enrollment


class BatchViewTests(TestCase):
    """
    Integration tests for CRM batch management views.
    """

    def setUp(self):
        """
        Set up shared test fixtures.

        Creates a staff user, an instructor, and an active course
        for use across test methods in this class.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.staff_user = User.objects.create_user(
            username='stafftest',
            password='TestPass123!',
            is_staff=True,
        )
        self.instructor = Instructor.objects.create(
            first_name='Test',
            last_name='Instructor',
            email='tinstructor@example.com',
        )
        self.course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            duration_weeks=8,
            fee='10000.00',
            instructor=self.instructor,
            status='active',
        )

    def test_batch_list_requires_login(self):
        """
        Verify that unauthenticated users are redirected from the batch list.
        """
        response = self.client.get(reverse('core:batch_list'))
        assert response.status_code == 302
        assert '/crm/login/' in response.url

    def test_batch_list_accessible_for_staff(self):
        """
        Verify that logged-in staff can access the batch list.
        """
        self.client.login(username='stafftest', password='TestPass123!')
        response = self.client.get(reverse('core:batch_list'))
        assert response.status_code == 200

    def test_batch_add_creates_record(self):
        """
        Verify that submitting a valid batch form creates a Batch record.
        """
        self.client.login(username='stafftest', password='TestPass123!')
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=70)

        response = self.client.post(reverse('core:batch_add'), {
            'name': 'New Test Batch',
            'course': self.course.pk,
            'instructor': self.instructor.pk,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'max_seats': 20,
            'status': 'upcoming',
        })

        assert response.status_code == 302, f"Expected redirect, got {response.status_code}"
        assert Batch.objects.filter(name='New Test Batch').exists(), "Batch was not created"
```

---

## Test Data Setup

Always use `setUp` for test fixtures that are shared across multiple test methods. Use descriptive variable names to make test intent clear:

```python
class EnrollmentTests(TestCase):
    def setUp(self):
        """
        Creates a minimal valid set of test data:
        - One instructor
        - One active course
        - One upcoming batch with 1 seat
        - Two students
        """
        self.instructor = Instructor.objects.create(
            first_name='Instructor',
            last_name='One',
            email='instructor1@example.com',
        )
        self.course = Course.objects.create(
            title='Test Course',
            slug='test-course-enroll',
            duration_weeks=6,
            fee='8000.00',
            instructor=self.instructor,
            status='active',
        )
        self.full_batch = Batch.objects.create(
            name='Full Batch',
            course=self.course,
            instructor=self.instructor,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=42),
            max_seats=1,           # Only 1 seat — easy to fill for testing
            status='ongoing',
        )
        self.student_a = Student.objects.create(
            first_name='Student', last_name='Alpha', email='alpha@example.com',
        )
        self.student_b = Student.objects.create(
            first_name='Student', last_name='Beta', email='beta@example.com',
        )
```

---

## Testing Forms

Test form validation by constructing a form with data and checking `is_valid()` and `non_field_errors()`:

```python
def test_enrollment_form_rejects_duplicate_enrollment(self):
    """Verify a student cannot enrol in the same batch twice."""
    # Create an existing enrolment
    Enrollment.objects.create(
        student=self.student_a,
        batch=self.full_batch,
        status='active',
    )

    form = EnrollmentForm(data={
        'student': self.student_a.pk,   # Same student...
        'batch': self.full_batch.pk,    # ...same batch
        'enrolled_on': date.today().isoformat(),
        'status': 'active',
        'notes': '',
    })

    assert not form.is_valid(), "Form should be invalid for duplicate enrolment"
    assert 'already enrolled' in str(form.non_field_errors())
```

---

## Testing Views

Use `self.client.get()` and `self.client.post()` to simulate HTTP requests:

```python
def test_student_delete_requires_post(self):
    """Verify a GET request to the delete URL shows a confirmation page, not delete."""
    self.client.login(username='stafftest', password='TestPass123!')
    student = Student.objects.create(
        first_name='To', last_name='Delete', email='todelete@example.com',
    )

    # GET should show confirm page, not delete the record
    response = self.client.get(reverse('core:student_delete', kwargs={'pk': student.pk}))
    assert response.status_code == 200
    assert Student.objects.filter(pk=student.pk).exists(), "GET should NOT delete the student"

    # POST should delete
    response = self.client.post(reverse('core:student_delete', kwargs={'pk': student.pk}))
    assert response.status_code == 302
    assert not Student.objects.filter(pk=student.pk).exists(), "POST should delete the student"
```

---

## Testing Models

Test model properties and methods directly without HTTP:

```python
def test_batch_seats_available_decrements_on_active_enrollment(self):
    """Verify SeatsAvailable reflects active enrolments only."""
    assert self.full_batch.seats_available == 1

    Enrollment.objects.create(
        student=self.student_a,
        batch=self.full_batch,
        status='active',
    )

    # Refresh from database to clear cached properties
    self.full_batch.refresh_from_db()
    assert self.full_batch.seats_available == 0

def test_pending_enrollment_does_not_reduce_available_seats(self):
    """Verify pending enrolments do not consume seats."""
    Enrollment.objects.create(
        student=self.student_a,
        batch=self.full_batch,
        status='pending',   # pending — should not count as a taken seat
    )

    self.full_batch.refresh_from_db()
    assert self.full_batch.seats_available == 1, \
        "Pending enrolments should not reduce available seats"
```

---

## Testing the REST API

Use Django's test client to test the JWT API endpoints:

```python
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class JwtAuthApiTests(TestCase):
    def setUp(self):
        """Creates a staff user for authentication tests."""
        self.staff_user = User.objects.create_user(
            username='apiteststaff',
            password='ApiTestPass123!',
            is_staff=True,
        )
        self.non_staff_user = User.objects.create_user(
            username='regularuser',
            password='RegularPass123!',
            is_staff=False,
        )

    def test_staff_user_can_obtain_tokens(self):
        """Verify a staff user receives access and refresh tokens."""
        response = self.client.post(
            reverse('token_obtain_pair'),
            data=json.dumps({'username': 'apiteststaff', 'password': 'ApiTestPass123!'}),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data

    def test_non_staff_user_receives_403(self):
        """Verify a non-staff user cannot obtain tokens."""
        response = self.client.post(
            reverse('token_obtain_pair'),
            data=json.dumps({'username': 'regularuser', 'password': 'RegularPass123!'}),
            content_type='application/json',
        )
        assert response.status_code == 403

    def test_me_endpoint_returns_user_data(self):
        """Verify the /me/ endpoint returns the authenticated user's details."""
        # First obtain a token
        token_response = self.client.post(
            reverse('token_obtain_pair'),
            data=json.dumps({'username': 'apiteststaff', 'password': 'ApiTestPass123!'}),
            content_type='application/json',
        )
        access_token = token_response.json()['access']

        # Then call the /me/ endpoint
        me_response = self.client.get(
            reverse('auth_me'),
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert me_response.status_code == 200
        data = me_response.json()
        assert data['username'] == 'apiteststaff'
        assert data['is_staff'] is True
```
