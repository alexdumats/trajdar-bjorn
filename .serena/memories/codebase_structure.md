# Codebase Structure

## Root Directory Layout
```
trajdar_bjorn/
├── src/                          # Main source code
├── config/                       # Configuration files
├── tests/                        # Test suites
├── scripts/                      # Automation scripts  
├── database/                     # SQLite databases
├── logs/                         # Application logs
├── docs/                         # Documentation
├── docker-compose*.yml           # Container orchestration
├── Dockerfile.*                  # Service-specific containers
├── requirements.txt              # Python dependencies
├── pytest.ini                   # Test configuration
└── README.md                     # Main documentation
```

## Source Code Structure (`src/`)
```
src/
├── orchestrator_service.py      # Main coordination service (Port 8000)
├── portfolio_service.py         # Portfolio management (Port 8001)
├── signal_service.py           # Risk manager (Port 8002)
├── notification_service.py      # Slack alerts (Port 8004)
├── parameter_optimizer_service.py # Strategy optimization (Port 8006)
├── backtesting_engine.py        # Backtesting functionality
├── paper_trading_engine.py      # Paper trading simulation
├── market_analyst/              # Market analysis agent
├── news_analyst/                # News analysis agent
├── mcp_hub/                     # MCP server coordination
└── utils/                       # Shared utilities
    ├── config_manager.py        # Configuration management
    └── __init__.py
```

## Configuration Structure (`config/`)
```
config/
├── production_config.yaml       # Main system configuration
├── message_templates.yaml       # Slack message templates
├── mcp_servers.yaml             # MCP server definitions
├── agent_mcps/                  # Agent-specific MCP configs
│   ├── risk_manager_mcps.yaml
│   ├── market_analyst_mcps.yaml
│   ├── trade_executor_mcps.yaml
│   └── parameter_optimizer_mcps.yaml
├── trading_parameters.yaml      # Strategy parameters (auto-generated)
└── multi_pair_trading.yaml      # Multi-pair trading config
```

## Test Structure (`tests/`)
```
tests/
├── unit/                        # Unit tests (69 tests)
├── integration/                 # Integration tests (15 tests)  
├── e2e/                        # End-to-end tests (7 tests)
├── performance/                 # Performance tests (7 tests)
├── fixtures/                    # Test data
│   ├── market_data.json
│   ├── portfolio_states.json
│   └── trading_signals.json
├── conftest.py                  # Pytest configuration
└── __init__.py
```

## Scripts Directory (`scripts/`)
Key automation scripts:
- `start_agents.sh` / `stop_agents.sh` - Agent lifecycle
- `check_agents.sh` - Health monitoring
- `run_tests.sh` - Test execution
- `deployment_readiness_check.sh` - Pre-deployment validation
- `monitor_system.sh` - System monitoring
- `setup_test_environment.sh` - Test environment setup

## Docker Configuration
- `docker-compose.production.yml` - Production deployment
- `docker-compose.refactored.yml` - Refactored system version
- Individual `Dockerfile.*` for each service

## Key Service Architecture
- **Orchestrator** (8000): Central coordination and decision making
- **Portfolio** (8001): Portfolio management and trade execution  
- **Risk Manager** (8002): Risk assessment and protection
- **Market Analyst** (8003): Technical and fundamental analysis
- **Notification** (8004): Slack alerts and notifications
- **Trade Executor** (8005): Fast trade execution
- **Parameter Optimizer** (8006): Strategy optimization
- **MCP Hub** (9000): MCP server coordination