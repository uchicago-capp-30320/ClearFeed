# ClearFeed Endpoints (Administrative)

The following endpoints support administrative and non-analysis-related pages within the ClearFeed application.

---

## `GET /landing/`

Renders the public landing page. No authentication required.

### Response
- `landing.html`

---

## `GET /login/`

Django's built-in login view.

### Response
- `registration/login.html`

---

## `POST /login/`

Authenticates the user and redirects on success.

### Parameters (form body)
- `username`: User email
- `password`: User password

---

## `GET /logout/`

Logs the current user out via Django's built-in logout view.

---

## `GET /signup/`

Renders the account creation form.

### Response
- `registration/signup.html`

### Template Context
- `form` (`AppUserCreationForm`): Unbound empty form instance.

---

## `POST /signup/`

Creates a new `AppUser`, logs them in, and redirects to `/onboarding/`.

### Parameters (form body)
- `email`: New user's email address
- `password1`, `password2`: Password and confirmation

### Template Context (on validation failure)
- `form` (`AppUserCreationForm`): Bound form instance containing validation errors.

---

## `GET /onboarding/`

Renders the onboarding page. No authentication required.

### Response
- `onboarding.html`

---

## `GET /profile/`

Placeholder profile view. Reads `user_id` from session.

### Response
- `profile.html`

### Template Context
- `user`: Corresponding `AppUser` object

---

## `GET /privacy/`

Renders the privacy policy page. No authentication required.

### Response
- `privacy.html`

---

## `GET /topics/`

Renders the topics page.

### Response
- `topics.html`

---

## `GET /wordcloud/`

Renders the word cloud page. Requires authentication (`@login_required`).

### Response
- `wordcloud.html`