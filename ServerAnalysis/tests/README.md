# Tests

This directory contains unit tests for the ServerAnalysis application.

## Setup

1. Install testing dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run with coverage report:
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_database_service.py -v
```

### Run specific test method:
```bash
pytest tests/test_database_service.py::TestDatabaseServiceScreenTimeEvents::test_get_screen_time_events_success -v
```

## Test Structure

- `test_database_service.py`: Tests for DatabaseService methods
  - `TestDatabaseServiceScreenTimeEvents`: Unit tests for the `get_screen_time_events_of_a_user` method
  - `TestDatabaseServiceIntegration`: Integration tests (require database setup)

## Test Categories

- **Unit Tests**: Test individual functions with mocked dependencies
- **Integration Tests**: Test with actual database connections (marked with `@pytest.mark.integration`)

To skip integration tests:
```bash
pytest tests/ -m "not integration"
```

To run only integration tests:
```bash
pytest tests/ -m "integration"
```