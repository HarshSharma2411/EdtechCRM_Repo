# EdTech CRM - Coding Guidelines

## Overview
This document outlines the best practices and coding standards for the EdTech CRM project. All developers should follow these guidelines to ensure code consistency, maintainability, and quality.

---

## 1. Function Naming Convention

All function names must follow **PascalCase** (also known as CapWords) format, where each word is capitalized with no underscores separating them.

### Examples:
- ✅ `HomePage()`
- ✅ `CreateStudent()`
- ✅ `FetchBatchDetails()`
- ✅ `UpdateEnrollmentStatus()`
- ✅ `ValidateEmailAddress()`
- ✅ `ProcessBatchPayment()`

### Incorrect Examples:
- ❌ `home_page()` (snake_case)
- ❌ `homepage()` (lowercase)
- ❌ `Home_Page()` (mixed case with underscores)

---

## 2. Docstring Requirements

Every function **must** include a comprehensive docstring that clearly documents its purpose, parameters, return values, and any potential exceptions.

### Docstring Format:

```python
def FunctionName(param1, param2):
    """
    Brief description of what this function does.
    
    This function performs [specific action]. It is used when [context/scenario].
    
    Parameters:
        param1 (type): Description of param1. Example: 'user email address'
        param2 (type): Description of param2. Example: 'student ID as integer'
    
    Returns:
        return_type: Description of return value. Example: 'Boolean True if operation successful, False otherwise'
    
    Raises:
        ExceptionType: Description of when this exception is raised
        AnotherException: Description of when this exception is raised
    
    Example:
        >>> result = FunctionName("user@example.com", 123)
        >>> print(result)
        True
    """
    # Function implementation
    pass
```

### Docstring Example:

```python
def ValidateStudentEmail(email, student_id):
    """
    Validates if an email address is unique for a given student.
    
    This function checks whether the provided email address is already
    registered in the system for another student to prevent duplicate registrations.
    
    Parameters:
        email (str): The email address to validate. Example: 'john.doe@example.com'
        student_id (int): The unique identifier of the student. Example: 42
    
    Returns:
        dict: A dictionary containing:
            - 'is_valid' (bool): True if email is unique, False if already exists
            - 'message' (str): Descriptive message about validation result
            - 'student_email' (str): The validated email address
    
    Raises:
        ValueError: If email format is invalid
        TypeError: If student_id is not an integer
    
    Example:
        >>> result = ValidateStudentEmail("jane@example.com", 15)
        >>> print(result)
        {'is_valid': True, 'message': 'Email is unique', 'student_email': 'jane@example.com'}
    """
    # Function implementation
    pass
```

### Minimum Docstring Sections:
- **Description**: What the function does
- **Parameters**: Type and explanation for each parameter
- **Returns**: Type and description of return value
- **Raises** (if applicable): Exceptions that may be raised
- **Example** (if applicable): Real usage example

---

## 3. Testing with Assert-Based Testing

Every function **must** have at least one corresponding test case using Python's `assert` statement. We do not use any testing frameworks; all tests should use simple `assert` statements.

### Testing Conventions:

1. Create test functions with the naming convention: `Test<FunctionName>()`
2. Test functions should be placed in the same file or in a dedicated test section
3. Use `assert` statements to verify expected behavior
4. Include both positive and negative test cases

### Test Function Format:

```python
def Test<FunctionName>():
    """
    Test case for <FunctionName> function.
    
    Tests:
        - Positive case: [what is being tested]
        - Negative case: [what is being tested]
        - Edge case: [what is being tested]
    """
    # Arrange - Set up test data
    test_input = "test_value"
    expected_output = "expected_result"
    
    # Act - Execute the function
    result = FunctionName(test_input)
    
    # Assert - Verify the result
    assert result == expected_output, f"Expected {expected_output}, got {result}"
    
    # Test negative case
    invalid_input = None
    try:
        FunctionName(invalid_input)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected behavior
```

### Testing Example:

```python
def CreateStudent(name, email, enrollment_date):
    """
    Creates a new student record in the system.
    
    Parameters:
        name (str): Full name of the student. Example: 'John Doe'
        email (str): Email address of the student. Example: 'john@example.com'
        enrollment_date (str): Date of enrollment in YYYY-MM-DD format. Example: '2026-05-07'
    
    Returns:
        dict: Created student object with 'id', 'name', 'email', 'enrollment_date'
    
    Raises:
        ValueError: If name is empty or email format is invalid
        TypeError: If parameters are of incorrect type
    """
    if not name or not isinstance(name, str):
        raise TypeError("Name must be a non-empty string")
    if not email or "@" not in email:
        raise ValueError("Invalid email format")
    
    student = {
        'id': 1,
        'name': name,
        'email': email,
        'enrollment_date': enrollment_date
    }
    return student


def TestCreateStudent():
    """
    Test case for CreateStudent function.
    
    Tests:
        - Positive case: Create student with valid data
        - Negative case: Create student with invalid email
        - Negative case: Create student with empty name
    """
    # Test positive case
    result = CreateStudent("John Doe", "john@example.com", "2026-05-07")
    assert result['name'] == "John Doe", "Student name not set correctly"
    assert result['email'] == "john@example.com", "Student email not set correctly"
    
    # Test invalid email
    try:
        CreateStudent("Jane Doe", "invalid-email", "2026-05-07")
        assert False, "Should have raised ValueError for invalid email"
    except ValueError as e:
        assert "Invalid email format" in str(e)
    
    # Test empty name
    try:
        CreateStudent("", "test@example.com", "2026-05-07")
        assert False, "Should have raised TypeError for empty name"
    except TypeError:
        pass  # Expected behavior
```

### Running Tests:

All test functions can be executed directly by calling them:

```python
# At the end of your module or in a test runner
if __name__ == "__main__":
    TestCreateStudent()
    print("All tests passed!")
```

---

## 4. Additional Best Practices

### 4.1 Code Organization
- Keep functions focused and single-purpose (Single Responsibility Principle)
- Group related functions together in logical sections
- Use comments to separate different sections of code

### 4.2 Error Handling
- Always handle exceptions explicitly
- Provide meaningful error messages
- Never use bare `except:` clauses

### 4.3 Type Hints (Python 3.5+)
While not mandatory, consider using type hints for better code clarity:

```python
def CalculateGPA(scores: list, weights: list) -> float:
    """Calculate weighted GPA from scores and weights."""
    return sum(s * w for s, w in zip(scores, weights)) / sum(weights)
```

### 4.4 Django-Specific Guidelines
- Keep business logic out of views; use models or utility functions
- Use model methods for database-related operations
- Keep views clean and focused on request/response handling
- Name Django views following the same PascalCase convention

### 4.5 Code Comments
- Add comments for complex logic only, not for obvious code
- Use meaningful comments that explain "why", not "what"

### 4.6 Imports
- Group imports in this order: standard library, third-party, local
- Use absolute imports over relative imports

### 4.7 Constants
- Define constants in UPPERCASE with underscores
- Example: `MAX_ENROLLMENT_CAPACITY = 50`

---

## 5. Example Complete Function with Test

Here's a complete example following all guidelines:

```python
def CalculateStudentGrade(total_marks, max_marks):
    """
    Calculates the percentage grade for a student.
    
    This function computes the percentage grade by dividing total marks
    obtained by the maximum possible marks and multiplying by 100.
    
    Parameters:
        total_marks (int or float): Marks obtained by student. Example: 85.5
        max_marks (int or float): Maximum possible marks. Example: 100
    
    Returns:
        float: Percentage grade. Example: 85.5
    
    Raises:
        ValueError: If total_marks > max_marks or if max_marks is 0
        TypeError: If parameters are not numeric
    
    Example:
        >>> grade = CalculateStudentGrade(85, 100)
        >>> print(grade)
        85.0
    """
    if not isinstance(total_marks, (int, float)) or not isinstance(max_marks, (int, float)):
        raise TypeError("Both parameters must be numeric")
    
    if max_marks == 0:
        raise ValueError("Maximum marks cannot be zero")
    
    if total_marks > max_marks:
        raise ValueError("Total marks cannot exceed maximum marks")
    
    percentage = (total_marks / max_marks) * 100
    return percentage


def TestCalculateStudentGrade():
    """
    Test case for CalculateStudentGrade function.
    
    Tests:
        - Positive case: Valid marks within range
        - Negative case: Total marks exceeding maximum
        - Negative case: Maximum marks as zero
        - Negative case: Invalid data types
    """
    # Test valid calculation
    result = CalculateStudentGrade(85, 100)
    assert result == 85.0, f"Expected 85.0, got {result}"
    
    # Test different valid inputs
    result = CalculateStudentGrade(45.5, 100)
    assert result == 45.5, f"Expected 45.5, got {result}"
    
    # Test total marks exceeding maximum
    try:
        CalculateStudentGrade(150, 100)
        assert False, "Should raise ValueError when total > max"
    except ValueError as e:
        assert "cannot exceed" in str(e)
    
    # Test maximum marks as zero
    try:
        CalculateStudentGrade(50, 0)
        assert False, "Should raise ValueError when max is 0"
    except ValueError as e:
        assert "cannot be zero" in str(e)
    
    # Test invalid type
    try:
        CalculateStudentGrade("85", 100)
        assert False, "Should raise TypeError for string input"
    except TypeError:
        pass  # Expected behavior
```

---

## 6. Checklist Before Committing Code

- [ ] All functions follow **PascalCase** naming convention
- [ ] Every function has a **comprehensive docstring** with parameters, returns, and raises
- [ ] Every function has at least **one test case** using `assert`
- [ ] Test cases cover **positive and negative scenarios**
- [ ] All **imports are organized** properly
- [ ] No bare `except:` clauses
- [ ] Code is **properly commented** (comments explain "why", not "what")
- [ ] All **test functions pass** without errors

---

## 7. Questions?

If you have questions about these guidelines or need clarification, please consult the project lead or the senior developers.

---

**Last Updated**: May 7, 2026  
**Version**: 1.0
