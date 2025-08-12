# AI Trading System - Testing Guide

## 🧪 Test Suite Overview

This document provides comprehensive testing guidance for the AI Multi-Source Trading System. The test suite includes unit tests, integration tests, end-to-end tests, and performance tests.

## 📁 Test Structure

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── unit/                       # Unit tests for individual components
│   ├── test_portfolio_service.py
│   ├── test_orchestrator_service.py
│   └── test_signal_service.py
├── integration/                # Integration tests for service interactions
│   └── test_service_interactions.py
├── e2e/                       # End-to-end workflow tests
│   └── test_trading_workflows.py
├── performance/               # Performance and load tests
│   └── test_load_performance.py
└── fixtures/                  # Test data fixtures
    ├── market_data.json
    ├── trading_signals.json
    └── portfolio_states.json
```

## 🚀 Quick Start

### 1. Setup Test Environment

```bash
# Install test dependencies and setup environment
./scripts/setup_test_environment.sh

# Or manually install dependencies
pip install pytest pytest-asyncio pytest-mock pytest-html pytest-cov
```

### 2. Run All Tests

```bash
# Run complete test suite
./scripts/run_tests.sh all

# Run with coverage report
./scripts/run_tests.sh all --coverage --html
```

### 3. Run Specific Test Categories

```bash
# Unit tests only
./scripts/run_tests.sh unit

# Integration tests
./scripts/run_tests.sh integration

# End-to-end tests  
./scripts/run_tests.sh e2e

# Performance tests
./scripts/run_tests.sh performance
```

## 🧩 Test Categories

### Unit Tests (`tests/unit/`)

Test individual components and services in isolation:

- **Portfolio Service**: Portfolio management, trade execution, database operations
- **Orchestrator Service**: Agent coordination, orchestration cycles, system status
- **Signal Service**: Technical analysis, AI signal generation, risk assessment

**Run unit tests:**
```bash
pytest tests/unit/ -v
./scripts/run_tests.sh unit --verbose
```

### Integration Tests (`tests/integration/`)

Test interactions between services:

- Service-to-service communication
- Database consistency across services
- Health check propagation
- Concurrent access patterns

**Run integration tests:**
```bash
pytest tests/integration/ -v
./scripts/run_tests.sh integration
```

### End-to-End Tests (`tests/e2e/`)

Test complete trading workflows:

- Full automated trading cycles
- Risk-based trade rejection
- Market condition overrides
- Error handling and recovery

**Run E2E tests:**
```bash
pytest tests/e2e/ -v
./scripts/run_tests.sh e2e
```

### Performance Tests (`tests/performance/`)

Test system performance under load:

- Service load testing
- Database concurrent access
- Sustained high load
- Memory usage stability
- Failure recovery performance

**Run performance tests:**
```bash
pytest tests/performance/ -m performance -v
./scripts/run_tests.sh performance
```

## 🐳 Docker Testing

For containerized testing environments:

### Setup Docker Test Environment

```bash
# Setup and start Docker test environment
./scripts/test_docker_setup.sh setup
./scripts/test_docker_setup.sh start
```

### Run Tests in Docker

```bash
# Run integration tests in containers
./scripts/test_docker_setup.sh test integration

# Run all tests in Docker environment
./scripts/test_docker_setup.sh test all
```

### Docker Test Management

```bash
# Check test environment status
./scripts/test_docker_setup.sh status

# View service logs
./scripts/test_docker_setup.sh logs orchestrator

# Stop test environment
./scripts/test_docker_setup.sh stop

# Clean up everything
./scripts/test_docker_setup.sh clean
```

## 📊 Test Configuration

### Pytest Configuration (`pytest.ini`)

Key configuration options:

```ini
[tool:pytest]
testpaths = tests
markers =
    unit: Unit tests for individual components
    integration: Integration tests for service interactions
    e2e: End-to-end tests for complete workflows
    performance: Performance and load tests
    stress: Stress tests for system limits

addopts = -v --strict-markers --tb=short --color=yes
```

### Test Environment Variables

Set in `.env.test`:

```bash
TESTING=true
DB_PATH=./test_data/test.db
MOCK_EXTERNAL_APIS=true
DISABLE_NOTIFICATIONS=true
LOG_LEVEL=WARNING
```

## 🔧 Test Fixtures and Mocking

### Key Fixtures (`tests/conftest.py`)

- `temp_db`: Temporary SQLite database for testing
- `test_config`: Test configuration data
- `sample_portfolio_data`: Portfolio test data
- `sample_trade_data`: Trade execution test data
- `mock_ollama_response`: Mocked AI model responses

### Mocking External Services

The test suite mocks:

- **Ollama AI API**: Mocked AI model responses
- **Slack API**: Disabled notifications
- **Market Data APIs**: Fixed test data
- **External Trading APIs**: Simulated responses

## 📈 Test Reports and Coverage

### Generate Test Reports

```bash
# HTML test report with coverage
./scripts/run_tests.sh all --html --coverage

# JUnit XML for CI/CD
./scripts/run_tests.sh all --junit

# Performance profiling
./scripts/run_tests.sh performance --profile
```

### View Reports

After running tests with reporting enabled:

```bash
# Open HTML report
open test_results/report.html

# Open coverage report  
open test_results/htmlcov/index.html

# View all reports
open test_results/index.html
```

## ⚡ Performance Testing

### Load Testing

Tests service performance under concurrent load:

```python
# Example: Portfolio service load test
@pytest.mark.performance
async def test_portfolio_service_load():
    concurrent_requests = 50
    # Execute 50 concurrent requests
    # Assert response times and success rates
```

### Stress Testing

Tests system limits and failure recovery:

```python
# Example: Sustained high load test
@pytest.mark.stress  
async def test_sustained_high_load():
    duration_seconds = 30
    request_rate = 5  # requests per second per service
    # Run sustained load for 30 seconds
    # Assert system stability
```

### Memory and Resource Testing

```python
# Example: Memory stability test
@pytest.mark.performance
async def test_memory_usage_stability():
    iterations = 1000
    # Process 1000 iterations of memory-intensive operations
    # Assert no memory leaks
```

## 🔄 Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Test Environment
        run: ./scripts/setup_test_environment.sh
      - name: Run Unit Tests
        run: ./scripts/run_tests.sh unit --junit --coverage
      - name: Run Integration Tests  
        run: ./scripts/run_tests.sh integration --junit
      - name: Upload Test Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

## 🛠️ Advanced Testing

### Custom Test Markers

Add custom markers for specific test categories:

```python
# pytest.ini
markers = 
    slow: Tests that take longer than 10 seconds
    external: Tests requiring external services
    database: Tests requiring database
```

Run specific markers:

```bash
# Run only database tests
pytest -m database

# Skip slow tests
pytest -m "not slow"
```

### Parameterized Tests

Test multiple scenarios:

```python
@pytest.mark.parametrize("signal,confidence,expected", [
    ("BUY", 85.0, True),
    ("SELL", 80.0, True), 
    ("HOLD", 60.0, False),
])
def test_trading_decision(signal, confidence, expected):
    # Test different trading scenarios
```

### Property-Based Testing

Use hypothesis for property-based testing:

```bash
pip install hypothesis

# Example property-based test
from hypothesis import given, strategies as st

@given(st.floats(min_value=0, max_value=100))
def test_rsi_bounds(rsi_value):
    # Test RSI calculation properties
    assert 0 <= rsi_value <= 100
```

## 🚨 Troubleshooting

### Common Test Issues

1. **Database locked errors**: Ensure proper connection cleanup in tests
2. **Port conflicts**: Use different ports for test services
3. **Async test failures**: Ensure proper `@pytest.mark.asyncio` usage
4. **Mock issues**: Verify mock patches are correctly applied

### Debug Test Failures

```bash
# Run with verbose output and no capture
pytest tests/unit/test_portfolio_service.py::TestPortfolioService::test_execute_trade_buy -v -s

# Run single test with debugging
pytest --pdb tests/unit/test_portfolio_service.py::test_specific_test

# View test output
pytest --tb=long --showlocals
```

### Test Data Cleanup

```bash
# Clean test data
rm -rf test_data/ test_results/

# Reset test environment
./scripts/setup_test_environment.sh
```

## 📚 Best Practices

### Writing Good Tests

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Test One Thing**: Each test should verify one specific behavior
3. **Use Descriptive Names**: Test names should describe what they test
4. **Mock External Dependencies**: Keep tests isolated and fast
5. **Clean Up Resources**: Use fixtures for setup/teardown

### Test Organization

1. **Group Related Tests**: Use test classes to group related functionality
2. **Use Fixtures**: Share common setup across tests
3. **Mark Tests Appropriately**: Use pytest markers for categorization
4. **Document Complex Tests**: Add docstrings for complex test scenarios

### Performance Testing Guidelines

1. **Set Realistic Expectations**: Base assertions on actual requirements
2. **Account for Variance**: Allow for some performance variance
3. **Test Under Load**: Verify performance degrades gracefully
4. **Monitor Resources**: Check CPU, memory, and I/O usage

## 🔗 Related Documentation

- [Project README](README.md) - Main project documentation
- [Configuration Guide](config/README.md) - System configuration
- [API Documentation](docs/api.md) - Service API reference
- [Deployment Guide](docs/deployment.md) - Production deployment

## 📞 Support

For testing questions or issues:

1. Check this testing guide
2. Review test logs in `test_results/logs/`
3. Run tests with verbose output for debugging
4. Check service logs for integration test failures

---

**Happy Testing!** 🎉