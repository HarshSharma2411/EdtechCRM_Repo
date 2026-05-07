# Database Schema

This document describes every data model in EdTech CRM, including field definitions, constraints, and entity relationships.

---

## Table of Contents

- [Entity Relationship Diagram](#entity-relationship-diagram)
- [Models](#models)
  - [Instructor](#instructor)
  - [Course](#course)
  - [Batch](#batch)
  - [Student](#student)
  - [Enrollment](#enrollment)
- [Indexes and Constraints](#indexes-and-constraints)
- [Status Enumerations](#status-enumerations)

---

## Entity Relationship Diagram

```
Instructor
  │
  ├──< Course (instructor FK, nullable)
  │       │
  │       └──< Batch (course FK)
  │               │
  └──< Batch      └──< Enrollment (batch FK)
  (instructor FK)         │
                  Student ─┘
                  (student FK)
```

**Cardinalities:**

- One `Instructor` → many `Course` records (optional; a course may have no instructor)
- One `Instructor` → many `Batch` records (optional)
- One `Course` → many `Batch` records
- One `Batch` → many `Enrollment` records
- One `Student` → many `Enrollment` records
- A `Student` + `Batch` combination is **unique** (a student cannot enrol in the same batch twice)

---

## Models

### Instructor

Represents a teaching professional who can be assigned to courses and batches.

**Table:** `core_instructor`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PK, auto-increment | Primary key |
| `first_name` | `VARCHAR(100)` | NOT NULL | Instructor's given name |
| `last_name` | `VARCHAR(100)` | NOT NULL | Instructor's family name |
| `email` | `VARCHAR(254)` | NOT NULL, UNIQUE | Contact email address |
| `phone` | `VARCHAR(20)` | Optional | Contact phone number |
| `bio` | `TEXT` | Optional | Professional biography |
| `photo` | `VARCHAR(100)` | Optional | Path to uploaded profile photo |
| `joined_on` | `DATE` | Default: today | Date the instructor joined |
| `is_active` | `BOOLEAN` | Default: `True` | Whether the instructor is currently active |
| `created_at` | `DATETIME` | Auto set on create | Record creation timestamp |
| `updated_at` | `DATETIME` | Auto set on update | Record last-modified timestamp |

**Default ordering:** `last_name`, `first_name`

**Computed properties:**

```python
def FullName(instructor):
    """
    Returns the instructor's full display name.

    Parameters:
        instructor (Instructor): The Instructor model instance.

    Returns:
        str: Full name in 'First Last' format. Example: 'Priya Sharma'
    """
    return f"{instructor.first_name} {instructor.last_name}"
```

---

### Course

Represents an educational programme offered by the organisation.

**Table:** `core_course`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PK, auto-increment | Primary key |
| `title` | `VARCHAR(200)` | NOT NULL | Course name |
| `slug` | `SLUG` | NOT NULL, UNIQUE | URL-safe identifier; auto-generated from `title` |
| `description` | `TEXT` | Optional | Full course description |
| `duration_weeks` | `INTEGER` | NOT NULL, ≥ 0, Default: 0 | Course length in weeks |
| `fee` | `DECIMAL(10, 2)` | NOT NULL, Default: 0 | Course fee in local currency |
| `instructor_id` | `INTEGER` | FK → `core_instructor`, nullable | Assigned instructor |
| `status` | `VARCHAR(20)` | NOT NULL, Default: `draft` | Lifecycle status |
| `thumbnail` | `VARCHAR(100)` | Optional | Path to uploaded course thumbnail |
| `created_at` | `DATETIME` | Auto set on create | Record creation timestamp |
| `updated_at` | `DATETIME` | Auto set on update | Record last-modified timestamp |

**Status values:** `draft`, `active`, `archived`

**Default ordering:** `title`

**Slug generation:** When a course is saved via `CourseForm`, the form's `save()` method auto-generates a URL-safe slug from the title. If the slug already exists, a numeric suffix is appended (e.g., `python-basics`, `python-basics-2`).

---

### Batch

Represents a scheduled run of a course with a fixed date range and seat capacity.

**Table:** `core_batch`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PK, auto-increment | Primary key |
| `name` | `VARCHAR(100)` | NOT NULL | Batch label (e.g., "June 2026 Weekend") |
| `course_id` | `INTEGER` | FK → `core_course`, CASCADE | Associated course |
| `instructor_id` | `INTEGER` | FK → `core_instructor`, nullable | Assigned instructor (may differ from course instructor) |
| `start_date` | `DATE` | NOT NULL | First day of the batch |
| `end_date` | `DATE` | NOT NULL | Last day of the batch |
| `max_seats` | `INTEGER` | NOT NULL, ≥ 0, Default: 30 | Maximum number of active enrolments |
| `status` | `VARCHAR(20)` | NOT NULL, Default: `upcoming` | Lifecycle status |
| `created_at` | `DATETIME` | Auto set on create | Record creation timestamp |

**Status values:** `upcoming`, `ongoing`, `completed`, `cancelled`

**Default ordering:** `-start_date` (most recent first)

**Computed properties:**

```python
def EnrolledCount(batch):
    """
    Returns the number of active enrolments for a batch.

    Parameters:
        batch (Batch): The Batch model instance.

    Returns:
        int: Count of active Enrollment records linked to this batch.

    Example:
        >>> count = EnrolledCount(batch_instance)
        >>> print(count)
        12
    """
    return batch.enrollments.filter(status='active').count()


def SeatsAvailable(batch):
    """
    Returns the number of remaining open seats in a batch.

    Parameters:
        batch (Batch): The Batch model instance.

    Returns:
        int: max_seats minus the count of active enrolments. Never negative.

    Example:
        >>> seats = SeatsAvailable(batch_instance)
        >>> print(seats)
        13
    """
    return max(0, batch.max_seats - EnrolledCount(batch))
```

**Validation:** `BatchForm.clean()` rejects batches where `end_date < start_date`.

---

### Student

Represents a learner who is or wants to be enrolled in a course.

**Table:** `core_student`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PK, auto-increment | Primary key |
| `first_name` | `VARCHAR(100)` | NOT NULL | Student's given name |
| `last_name` | `VARCHAR(100)` | NOT NULL | Student's family name |
| `email` | `VARCHAR(254)` | NOT NULL, UNIQUE | Login email and contact address |
| `phone` | `VARCHAR(20)` | Optional | Contact phone number |
| `date_of_birth` | `DATE` | Optional | Date of birth |
| `gender` | `VARCHAR(1)` | Optional | Gender code (`M`, `F`, `O`, `N`) |
| `address` | `TEXT` | Optional | Postal address |
| `photo` | `VARCHAR(100)` | Optional | Path to uploaded student photo |
| `status` | `VARCHAR(20)` | NOT NULL, Default: `pending` | Student lifecycle status |
| `password_hash` | `VARCHAR(128)` | Optional | Bcrypt-hashed password for learner portal login |
| `enrolled_on` | `DATE` | Default: today | Date of first enrolment |
| `created_at` | `DATETIME` | Auto set on create | Record creation timestamp |
| `updated_at` | `DATETIME` | Auto set on update | Record last-modified timestamp |

**Status values:** `pending`, `active`, `inactive`, `graduated`, `dropped`

**Gender codes:** `M` (Male), `F` (Female), `O` (Other), `N` (Prefer not to say)

**Default ordering:** `last_name`, `first_name`

**Security note:** `password_hash` stores a Django-compatible hashed password used exclusively for learner portal authentication. It is independent of Django's `User` model.

**Password methods:**

```python
def SetPassword(student, raw_password):
    """
    Hashes a plaintext password and stores it on the student instance.

    Parameters:
        student (Student): The Student model instance to update.
        raw_password (str): The plaintext password to hash. Example: 'SecurePass123!'

    Returns:
        None: Updates student.password_hash in place; does not save to the database.

    Example:
        >>> student = Student.objects.get(email='learner@example.com')
        >>> SetPassword(student, 'NewPassword456!')
        >>> student.save()
    """
    student.password_hash = make_password(raw_password)


def CheckPassword(student, raw_password):
    """
    Verifies a plaintext password against the stored hash.

    Parameters:
        student (Student): The Student model instance to check.
        raw_password (str): The plaintext password attempt.

    Returns:
        bool: True if the password matches, False otherwise (including when no hash is set).

    Example:
        >>> is_valid = CheckPassword(student, 'SecurePass123!')
        >>> print(is_valid)
        True
    """
    if not student.password_hash:
        return False
    return check_password(raw_password, student.password_hash)
```

---

### Enrollment

Represents a student's registration in a specific batch.

**Table:** `core_enrollment`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PK, auto-increment | Primary key |
| `student_id` | `INTEGER` | FK → `core_student`, CASCADE | Enrolled student |
| `batch_id` | `INTEGER` | FK → `core_batch`, CASCADE | Target batch |
| `enrolled_on` | `DATE` | Default: today | Formal enrolment date |
| `status` | `VARCHAR(20)` | NOT NULL, Default: `active` | Enrolment lifecycle status |
| `notes` | `TEXT` | Optional | Free-text notes (e.g., payment notes, special requirements) |
| `created_at` | `DATETIME` | Auto set on create | Record creation timestamp |
| `updated_at` | `DATETIME` | Auto set on update | Record last-modified timestamp |

**Status values:** `pending`, `active`, `completed`, `dropped`, `cancelled`

**Default ordering:** `-enrolled_on` (most recent first)

---

## Indexes and Constraints

| Table | Constraint | Details |
|-------|-----------|---------|
| `core_instructor` | UNIQUE | `email` |
| `core_course` | UNIQUE | `slug` |
| `core_student` | UNIQUE | `email` |
| `core_enrollment` | UNIQUE TOGETHER | `(student_id, batch_id)` — a student may only enrol once per batch |
| `core_enrollment` | FK CASCADE | Deleting a `Student` deletes their `Enrollment` records |
| `core_enrollment` | FK CASCADE | Deleting a `Batch` deletes its `Enrollment` records |
| `core_batch` | FK CASCADE | Deleting a `Course` deletes its `Batch` records |
| `core_course` | FK SET NULL | Deleting an `Instructor` sets `course.instructor = NULL` |
| `core_batch` | FK SET NULL | Deleting an `Instructor` sets `batch.instructor = NULL` |

---

## Status Enumerations

### Course Status

| Value | Meaning |
|-------|---------|
| `draft` | In preparation; not visible on the public portal |
| `active` | Published and discoverable by learners |
| `archived` | No longer offered; hidden from the public portal |

### Batch Status

| Value | Meaning |
|-------|---------|
| `upcoming` | Scheduled but not yet started |
| `ongoing` | Currently in progress |
| `completed` | Finished |
| `cancelled` | Cancelled before or during the batch |

### Student Status

| Value | Meaning |
|-------|---------|
| `pending` | Registered but not yet verified/approved by staff |
| `active` | Verified and currently enrolled |
| `inactive` | Temporarily inactive |
| `graduated` | Successfully completed their programme |
| `dropped` | Left the programme before completion |

### Enrollment Status

| Value | Meaning |
|-------|---------|
| `pending` | Requested by learner; awaiting staff approval |
| `active` | Approved; student is attending the batch |
| `completed` | Batch ended; student completed the course |
| `dropped` | Student withdrew from the batch |
| `cancelled` | Enrolment cancelled before the batch started |
