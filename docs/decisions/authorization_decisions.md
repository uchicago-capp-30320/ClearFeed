# ClearFeed Authorization Overview  

## Repository

https://github.com/teddykolios11/ClearFeed-Capture

---

# Authentication & User Flow

## New User Sign Up

When accessing the application for the first time, users are automatically redirected to the login page.
From the login popup, users can select **“Create one”** to navigate to the account registration page.

During sign up, users are prompted to provide:
- an email address (used as the account username)
- a password with a minimum length of 8 characters

Once registration is successfully completed:
- the account is created and saved
- the user is automatically authenticated
- the user is redirected to the onboarding/instructions page

---

## Returning User Login

Returning users are automatically directed to the login page upon accessing the application.

After submitting valid authentication credentials, users are redirected to the ClearFeed homepage where they can continue feed ingestion and analysis workflows.

---

## Logout Behavior

Users may log out at any time using the **Logout** button located in the top-right corner of the application.
Authentication sessions persist until users explicitly log out, allowing for smoother back-and-forth usage between:

- browser feed capture
- ingestion workflows
- downstream analysis
---

# Project Changes & Authentication Integration

## `backend/api/views.py`
Implemented a custom signup authentication flow via:

```python
signup(request)
```

### Responsibilities

- Handles new user registration logic
- Processes submitted signup forms
- Saves newly created user accounts
- Automatically authenticates/logs in users after registration
- Redirects users to onboarding/application routes after successful signup

This view utilizes the custom `AppUserCreationForm` defined in:

```python
backend/api/forms.py
```

---

## `backend/api/forms.py`

Created a custom form model:
```python
AppUserCreationForm
```

### Features

- Inherits core functionality from:
```python
django.contrib.auth.forms.UserCreationForm
```

- Adds custom validation and normalization logic for:
  - email formatting
  - email uniqueness enforcement
This form enables email-based authentication workflows while preserving Django’s built-in authentication structure.

---

## `backend/clearfeed_django/urls.py`
Integrated Django’s built-in authentication views from:
```python
django.contrib.auth.views
```

### Added Routes
| Route | Purpose |
|---|---|
| `/login/` | Django login authentication view |
| `/logout/` | Django logout authentication view |
| `/signup/` | Custom user registration flow |

The signup route is connected to the custom signup logic implemented in:
```python
backend/api/views.py
```

---

## `backend/clearfeed_django/settings.py`
Configured Django authentication settings to support the custom application user model and authentication routing.

### Added/Updated Settings

#### Custom User Model

```python
AUTH_USER_MODEL
```
Integrates the custom `AppUser` model with Django’s built-in authentication framework.

---

#### Login URL

```python
LOGIN_URL
```
Defines the default redirect route for views requiring authentication.

---

#### Redirect Configuration

```python
LOGIN_REDIRECT_URL
LOGOUT_REDIRECT_URL
```
Controls routing behavior after:
- successful login
- successful logout

---

# Authentication Templates

## `templates/registration/login.html`

---

## `templates/registration/signup.html`

---

## `templates/registration/logged_out.html`

---

# Summary

This implementation extends Django’s built-in authentication system with:
- email-based account registration
- automatic post-signup authentication
- persistent session handling
- custom authentication templates
- application-specific onboarding routing

while maintaining compatibility with Django’s standard authentication infrastructure.