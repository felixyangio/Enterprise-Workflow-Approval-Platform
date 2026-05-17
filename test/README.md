# OA Project Unit Test Guide

## Test Coverage

| Test File | Coverage | Test Cases |
|---|---|---|
| `test_models.py` | Core business models (User, Staff, Absent, Inform, etc.) | 20+ |
| `test_auth_api.py` | Login endpoint, change-password endpoint | 11 |
| `test_absent_api.py` | Leave types, approvers, leave request CRUD & approval flow | 14 |
| `test_inform_api.py` | Announcement list, publish, detail, delete, mark-as-read | 15 |

---

## Dependencies

Tests run with **pytest + pytest-django**. Install the following (make sure the backend virtual environment is activated):

```bash
pip install pytest pytest-django
```

Other backend dependencies (if not yet installed):

```bash
cd oaback
pip install -r requirements.txt
```

---

## Running Tests

### Option 1: Run all tests

```bash
# Execute from the test/ directory
cd test
pytest
```

### Option 2: Run a single test file

```bash
cd test

# Model tests only
pytest test_models.py -v

# Login / change-password API tests only
pytest test_auth_api.py -v

# Leave management API tests only
pytest test_absent_api.py -v

# Announcement API tests only
pytest test_inform_api.py -v
```

### Option 3: Run a specific test class or function

```bash
cd test

# All tests in TestUserModel
pytest test_models.py::TestUserModel -v

# A single test function
pytest test_auth_api.py::TestLoginView::test_login_success_returns_token -v
```

### Option 4: Generate a coverage report

```bash
pip install pytest-cov

cd test
pytest --cov=../oaback --cov-report=term-missing
```

---

## Project Structure

```
test/
├── __init__.py              # Package marker
├── conftest.py              # Adds oaback to sys.path and configures Django Settings
├── pytest.ini               # pytest + pytest-django configuration
├── README.md                # This document
├── test_models.py           # Model unit tests
├── test_auth_api.py         # Authentication API tests
├── test_absent_api.py       # Leave management API tests
└── test_inform_api.py       # Announcement API tests
```

---

## Testing Principles

- **Model tests (test_models.py)**: Verify model creation, default values, `__str__` output, unique constraints, ordering rules, and status constants — no HTTP requests involved.
- **API tests (test_*_api.py)**: Use DRF's `APIClient` to simulate real HTTP requests, covering happy paths, edge cases, and permission checks (401/403/404).
- All tests use a temporary test database (`@pytest.mark.django_db`) that is rolled back after each test, leaving the development database untouched.
- `pytest.fixture` is used to manage test data, keeping test cases independent of each other.

---

## FAQ

**Q: Getting `ModuleNotFoundError: No module named 'oa'` at runtime?**

A: Make sure to run pytest from the `test/` directory. `conftest.py` automatically adds `oaback` to `sys.path`. Alternatively, set it manually:
```bash
set DJANGO_SETTINGS_MODULE=oa.settings  # Windows
export DJANGO_SETTINGS_MODULE=oa.settings  # macOS/Linux
```

**Q: Getting database-related errors at runtime?**

A: Check that `oaback/db.sqlite3` exists, or run migrations inside the `oaback/` directory:
```bash
cd oaback
python manage.py migrate
```
