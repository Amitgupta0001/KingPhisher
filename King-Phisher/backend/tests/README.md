# King-Phisher Tests

This directory contains unit and integration tests for the King-Phisher application.

## Running Tests

### Install test dependencies:
```bash
pip install pytest pytest-flask pytest-cov
```

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_app.py -v
```

### Run specific test class:
```bash
pytest tests/test_app.py::TestPasswordValidation -v
```

## Test Structure

- `test_app.py` - Tests for Flask application, authentication, and API endpoints
- `test_model.py` - Tests for ML model training and evaluation

## Test Coverage

Current test coverage includes:
- ✅ Password validation
- ✅ User authentication (login/register)
- ✅ Rate limiting
- ✅ Database schema and indexes
- ✅ Model training and metrics
- ✅ API endpoints

## Adding New Tests

Follow the existing pattern:
1. Create test class with descriptive name
2. Use pytest fixtures for setup/teardown
3. Write descriptive test names starting with `test_`
4. Add docstrings explaining what each test validates
