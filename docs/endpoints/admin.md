# ClearFeed Endpoints (Administrative)

The following endpoints support administrative and non-analysis-related pages within the ClearFeed application.

---

## `/landing`

### Parameters
- None

### Response
- `home.html`: HTML page displaying the application’s landing page

### Template Context Variables
- None

---

## `/login`

### Parameters
- None

### Response
- `login.html`: HTML page for user login

### Template Context Variables
- None

---

## `/profile`

### Parameters
- `user_id`: Primary key for `AppUser`

### Response
- `profile.html`: HTML page displaying user-specific profile information

### Template Context Variables
- `user`: corresponding `AppUser` object

---

## `/privacy`

### Parameters
- None

### Response
- `privacy.html`: HTML page displaying the application’s privacy policy

### Template Context Variables
- None

---

## `/onboarding`

### Parameters
- None

### Response
- `onboarding.html`: HTML page providing a brief tutorial on using the application and browser extension

### Template Context Variables
- None

## `/signup`

### Parameters
- None

### Response
- `registration/signup.html`: HTML that provides a form for creating an account for the website

### Template Context Variables
- `form` (`AppUserCreationForm`): The user creation form. On `GET`, an unbound empty form instance. On `POST` with invalid data, a bound form instance containing validation errors.