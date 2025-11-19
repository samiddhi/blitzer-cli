# Testing

Comprehensive test suite for Blitzer CLI functionality.

## Run all tests:
```bash
python tests/run_tests.py
```

## Run with coverage:
```bash
python tests/run_tests.py --coverage
```

## Test multiple Python versions:
```bash
pip install tox
tox
```

## Python versions supported: 3.8-3.12

## Test Configuration Isolation
All tests run with isolated configuration directories to ensure consistent results regardless of your personal Blitzer config. Tests use temporary directories instead of ~/.config/blitzer.