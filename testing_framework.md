# AI Trading System - Testing Framework

## Overview
The AI Trading System employs a comprehensive testing framework using pytest to ensure reliability, correctness, and performance of all components. The testing strategy includes unit tests, integration tests, end-to-end tests, and performance tests.

## Testing Framework

### Framework
- **pytest**: Primary testing framework
- **pytest-cov**: Code coverage reporting
- **pytest-asyncio**: Asynchronous test support
- **fastapi.testclient**: Service API testing

### Test Structure
```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── unit/                    # Unit tests for individual components
│   ├── __init__.py
│   ├── test_orchestrator_service.py
│   ├── test_portfolio_service.py
│   └── test_signal_service.py
├── integration/             # Integration tests for service interactions
│   ├── __init__.py
│   └── test_service_interactions.py
├── e2e/                     # End-to-end workflow tests
│   ├── __init__.py
│   └── test_trading_workflows.py
├── performance/             # Performance and load tests
│   ├── __init__.py
│   └── test_load_performance.py
└── fixtures/                # Test data fixtures
    ├── market_data.json
    ├── portfolio_states.json
    └── trading_signals.json
```

## Test Configuration (conftest.py)

### Fixtures
1. **event_loop**: Async event loop for async tests
2. **temp_db**: Temporary SQLite database for testing
3. **test_config**: Test configuration parameters
4. **test_env_vars**: Environment variables for testing
5. **sample_portfolio_data**: Sample portfolio data
6. **sample_trade_data**: Sample trade data
7. **sample_market_data**: Sample market data
8. **sample_signal_data**: Sample trading signal data
9. **aiohttp_session**: Async HTTP session
10. **mock_ollama_response**: Mock AI model response
11. **mock_slack_logger**: Mock Slack logger
12. **Service clients**: Test clients for each service

### Database Fixtures
- **setup_test_database**: Initialize test database with schema and sample data

## Unit Tests

### Test Portfolio Service (test_portfolio_service.py)
- **TestHealthEndpoint**: Health check endpoint validation
- **TestGetPortfolio**: Portfolio data retrieval
- **TestExecuteTradeBuy**: Buy trade execution
- **TestExecuteTradeSell**: Sell trade execution
- **TestExecuteTradeInsufficientBalance**: Insufficient balance handling
- **TestGetPerformanceMetrics**: Performance metrics calculation
- **TestGetTradesHistory**: Trade history retrieval
- **TestGetPositions**: Position tracking
- **TestStopLossTakeProfitCheck**: Risk management features
- **TestPortfolioManager**: PortfolioManager class functionality
- **TestDatabaseInitialization**: Database schema creation
- **TestCalculatePositionSize**: Position size calculation
- **TestSlackLoggingIntegration**: Slack integration

### Test Orchestrator Service (test_orchestrator_service.py)
- **TestHealthEndpoint**: Health check validation
- **TestSystemStatus**: System status reporting
- **TestStartOrchestration**: Orchestration startup
- **TestStopOrchestration**: Orchestration shutdown
- **TestOrchestrationStatus**: Orchestration state tracking
- **TestManualCycle**: Manual cycle execution
- **TestAgentOrchestrator**: AgentOrchestrator class functionality
- **TestInitSession**: HTTP session initialization
- **TestCloseSession**: HTTP session cleanup
- **TestShouldRunAgent**: Agent scheduling logic
- **TestLoadConfig**: Configuration loading
- **TestCallService**: Service communication
- **TestCheckAgentsHealth**: Agent health monitoring
- **TestGetSystemStatus**: System status aggregation
- **TestCheckServiceHealth**: Individual service health
- **TestExecuteOrchestrationCycle**: Orchestration cycle execution

### Test Signal Service (test_signal_service.py)
- **TestHealthEndpoint**: Health check validation
- **TestGetSignal**: Signal generation
- **TestGetIndicators**: Technical indicator calculation
- **TestCalculateRSI**: RSI calculation accuracy
- **TestCalculateMACD**: MACD calculation accuracy
- **TestCalculateBollingerBands**: Bollinger Bands calculation
- **TestAnalyzeMarketConditions**: Market condition analysis
- **TestGenerateTradingSignal**: Signal generation logic
- **TestGetConfidenceScore**: Confidence scoring
- **TestSignalService**: SignalService class functionality

## Integration Tests

### Service Interactions (test_service_interactions.py)
- **TestPortfolioOrchestratorIntegration**: Portfolio-Orchestrator communication
- **TestSignalDataServiceIntegration**: Signal-Data service communication
- **TestNotificationServiceIntegration**: Notification system integration
- **TestEndToEndTradeFlow**: Complete trade execution flow
- **TestDatabaseConsistency**: Database state consistency
- **TestConfigurationPropagation**: Configuration sharing between services

## End-to-End Tests

### Trading Workflows (test_trading_workflows.py)
- **TestCompleteTradingCycle**: Full trading cycle simulation
- **TestPortfolioManagementWorkflow**: Portfolio management flow
- **TestRiskManagementWorkflow**: Risk management execution
- **TestPerformanceOptimizationWorkflow**: Parameter optimization flow
- **TestNotificationWorkflow**: Notification system validation
- **TestErrorHandling**: Error recovery scenarios
- **TestConcurrentOperations**: Concurrent trading operations

## Performance Tests

### Load Performance (test_load_performance.py)
- **TestHighFrequencyTrading**: High-frequency trade execution
- **TestConcurrentUsers**: Multiple user simulation
- **TestDatabasePerformance**: Database operation performance
- **TestAPIResponseTimes**: API latency measurement
- **TestMemoryUsage**: Memory consumption monitoring
- **TestScalability**: System scaling capabilities

## Test Data Fixtures

### Market Data (market_data.json)
- Historical price data
- Volume information
- Market indicators
- Sample trading pairs

### Portfolio States (portfolio_states.json)
- Various portfolio configurations
- Different balance scenarios
- Position tracking data
- Performance metrics

### Trading Signals (trading_signals.json)
- Sample buy/sell signals
- Confidence levels
- Technical indicator values
- Market condition data

## Test Execution

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/unit/test_portfolio_service.py

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test function
python -m pytest tests/unit/test_portfolio_service.py::TestPortfolioService::test_health_endpoint

# Run tests in parallel
python -m pytest -n auto tests/
```

### Test Reports
- **test_results/report.html**: HTML test report
- **test_results/unit_output.log**: Unit test output
- **test_results/all_output.log**: Complete test output
- **test_results/coverage/**: Coverage reports
- **test_results/htmlcov/**: HTML coverage report

## Continuous Integration
- **GitHub Actions**: Automated testing on push/pull request
- **Unit Tests Workflow**: Fast feedback on code changes
- **Integration Tests Workflow**: Service interaction validation
- **Performance Tests Workflow**: Performance regression detection
- **Security Scanning**: Dependency vulnerability checks

## Test Coverage Goals
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: 80%+ coverage
- **E2E Tests**: 70%+ coverage
- **Performance Tests**: Critical paths covered

## Mocking Strategy
- **External APIs**: Mocked to prevent network dependencies
- **Database Operations**: In-memory SQLite for fast testing
- **AI Models**: Mocked responses for consistent testing
- **File System**: Temporary files for isolated testing
- **Time-dependent Functions**: Frozen time for reproducible tests

## Quality Gates
- All unit tests must pass
- Coverage must not decrease
- No critical security issues
- Performance benchmarks maintained
- Integration tests validate service contracts