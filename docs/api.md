# API Reference

This document covers the REST API endpoints provided by EdTech CRM. All endpoints are under the `/api/auth/` prefix and use JWT (JSON Web Token) authentication.

---

## Table of Contents

- [Authentication Overview](#authentication-overview)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [POST /api/auth/token/](#post-apiauthtoken)
  - [POST /api/auth/token/refresh/](#post-apiauthtokenrefresh)
  - [POST /api/auth/logout/](#post-apiauthlogout)
  - [GET /api/auth/me/](#get-apiauthme)
- [Error Responses](#error-responses)
- [Token Lifecycle](#token-lifecycle)
- [Example: Full Authentication Flow](#example-full-authentication-flow)

---

## Authentication Overview

The REST API uses **JWT Bearer token authentication**:

1. Obtain an access token and a refresh token by posting credentials to `/api/auth/token/`.
2. Include the access token in the `Authorization` header of subsequent requests:
   ```
   Authorization: Bearer <access_token>
   ```
3. When the access token expires (after 8 hours), obtain a new one using the refresh token at `/api/auth/token/refresh/`.
4. On logout, blacklist the refresh token at `/api/auth/logout/` to invalidate the session.

> **Staff only:** Only Django users with `is_staff=True` can obtain tokens. Attempting to authenticate as a non-staff user returns `403 Forbidden`.

---

## Base URL

```
http://127.0.0.1:8000
```

All paths below are relative to this base URL.

---

## Endpoints

### POST /api/auth/token/

Authenticates a staff user and returns a JWT access token and a refresh token.

**Authentication required:** No

**Request body:**

```json
{
  "username": "staff_username",
  "password": "staff_password"
}
```

**Successful response — 200 OK:**

```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>"
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `400 Bad Request` | Missing or invalid credentials | `{"detail": "No active account found with the given credentials"}` |
| `403 Forbidden` | User exists but is not staff | `{"detail": "Staff access only."}` |

**Example (curl):**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'
```

---

### POST /api/auth/token/refresh/

Exchanges a valid refresh token for a new access token. The old refresh token is blacklisted and a new one is returned.

**Authentication required:** No (the refresh token itself authorises the request)

**Request body:**

```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Successful response — 200 OK:**

```json
{
  "access": "<new_jwt_access_token>",
  "refresh": "<new_jwt_refresh_token>"
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `400 Bad Request` | Refresh token is invalid or blacklisted | `{"detail": "Token is invalid or expired", "code": "token_not_valid"}` |
| `400 Bad Request` | Missing `refresh` field | `{"refresh": ["This field is required."]}` |

**Example (curl):**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your_refresh_token>"}'
```

---

### POST /api/auth/logout/

Blacklists the provided refresh token, effectively invalidating the session. Future refresh attempts with the same token will fail.

**Authentication required:** Yes — `Authorization: Bearer <access_token>`

**Request body:**

```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Successful response — 200 OK:**

```json
{
  "detail": "Logged out."
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `400 Bad Request` | Missing `refresh` field | `{"detail": "Refresh token is required."}` |
| `400 Bad Request` | Token is already blacklisted or invalid | `{"detail": "Invalid refresh token."}` |
| `401 Unauthorized` | Missing or invalid access token | `{"detail": "Authentication credentials were not provided."}` |

**Example (curl):**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{"refresh": "<your_refresh_token>"}'
```

---

### GET /api/auth/me/

Returns basic profile information for the currently authenticated staff user.

**Authentication required:** Yes — `Authorization: Bearer <access_token>`

**Request body:** None

**Successful response — 200 OK:**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "is_staff": true,
  "is_superuser": true
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `401 Unauthorized` | Missing or invalid access token | `{"detail": "Authentication credentials were not provided."}` |

**Example (curl):**

```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Error Responses

### Common Error Formats

All API errors follow the DRF (Django REST Framework) standard format:

```json
{
  "detail": "Human-readable error message."
}
```

Or for field-level validation errors:

```json
{
  "field_name": [
    "Validation error message."
  ]
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Request succeeded |
| `400 Bad Request` | Invalid request data |
| `401 Unauthorized` | Authentication token missing or invalid |
| `403 Forbidden` | Authenticated but not authorised (e.g., non-staff user) |
| `404 Not Found` | Resource not found |
| `405 Method Not Allowed` | HTTP method not supported for this endpoint |

---

## Token Lifecycle

| Token | Lifetime | Rotation | Blacklisted on |
|-------|----------|----------|----------------|
| Access token | 8 hours | No | — |
| Refresh token | 7 days | Yes (on each refresh) | Logout or refresh |

- Access tokens cannot be revoked directly — they expire naturally after 8 hours.
- Refresh tokens are **rotated**: each call to `/api/auth/token/refresh/` invalidates the old refresh token and issues a new one.
- Blacklisted tokens are stored in the `token_blacklist_blacklistedtoken` database table.

---

## Example: Full Authentication Flow

The following Python example demonstrates the complete JWT authentication lifecycle:

```python
import requests

BASE_URL = "http://127.0.0.1:8000"


def ObtainTokens(username, password):
    """
    Authenticates a staff user and retrieves JWT tokens.

    Parameters:
        username (str): The Django staff user's username. Example: 'admin'
        password (str): The user's password. Example: 'securepass123'

    Returns:
        dict: A dictionary containing 'access' and 'refresh' token strings.

    Raises:
        requests.HTTPError: If authentication fails.

    Example:
        >>> tokens = ObtainTokens('admin', 'securepass123')
        >>> print(tokens['access'])
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
    """
    response = requests.post(f"{BASE_URL}/api/auth/token/", json={
        "username": username,
        "password": password,
    })
    response.raise_for_status()
    return response.json()


def FetchCurrentUser(access_token):
    """
    Retrieves the authenticated staff user's profile information.

    Parameters:
        access_token (str): A valid JWT access token.

    Returns:
        dict: User profile with keys: id, username, email, first_name, last_name, is_staff, is_superuser.

    Raises:
        requests.HTTPError: If the token is invalid or expired.

    Example:
        >>> user = FetchCurrentUser(tokens['access'])
        >>> print(user['username'])
        'admin'
    """
    response = requests.get(
        f"{BASE_URL}/api/auth/me/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


def RefreshAccessToken(refresh_token):
    """
    Exchanges a refresh token for a new access token.

    Parameters:
        refresh_token (str): A valid JWT refresh token.

    Returns:
        dict: A dictionary containing the new 'access' and 'refresh' token strings.

    Raises:
        requests.HTTPError: If the refresh token is invalid or blacklisted.

    Example:
        >>> new_tokens = RefreshAccessToken(tokens['refresh'])
        >>> print(new_tokens['access'])
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
    """
    response = requests.post(f"{BASE_URL}/api/auth/token/refresh/", json={
        "refresh": refresh_token,
    })
    response.raise_for_status()
    return response.json()


def LogoutUser(access_token, refresh_token):
    """
    Blacklists the refresh token to invalidate the user's session.

    Parameters:
        access_token (str): A valid JWT access token for authorisation.
        refresh_token (str): The refresh token to blacklist.

    Returns:
        dict: A confirmation dictionary with key 'detail': 'Logged out.'

    Raises:
        requests.HTTPError: If the access token is invalid or the refresh token is already blacklisted.

    Example:
        >>> result = LogoutUser(tokens['access'], tokens['refresh'])
        >>> print(result['detail'])
        'Logged out.'
    """
    response = requests.post(
        f"{BASE_URL}/api/auth/logout/",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh": refresh_token},
    )
    response.raise_for_status()
    return response.json()


# Usage example
if __name__ == "__main__":
    tokens = ObtainTokens("admin", "yourpassword")
    print("Access token:", tokens["access"][:20], "...")

    user = FetchCurrentUser(tokens["access"])
    print("Logged in as:", user["username"])

    new_tokens = RefreshAccessToken(tokens["refresh"])
    print("Refreshed access token:", new_tokens["access"][:20], "...")

    result = LogoutUser(new_tokens["access"], new_tokens["refresh"])
    print(result["detail"])  # Logged out.
```
