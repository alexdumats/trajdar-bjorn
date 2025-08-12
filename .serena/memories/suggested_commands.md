# Suggested Commands for Development

## System Requirements Check
```bash
# Check Python version
python --version  # Should be 3.10+

# Check Docker
docker --version
docker-compose --version
```

## Environment Setup
```bash
# Copy environment template
cp .env.production .env.production.local

# Make scripts executable
chmod +x scripts/*.sh
```

## Testing Commands
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/           # Unit tests (69 tests)
python -m pytest tests/integration/    # Integration tests (15 tests)
python -m pytest tests/e2e/           # End-to-end tests (7 tests)
python -m pytest tests/performance/   # Performance tests (7 tests)

# Run with verbose output
python -m pytest -v

# Run with coverage (if pytest-cov installed)
python -m pytest --cov=src --cov-report=html --cov-report=term-missing
```

## System Control
```bash
# Start all services
docker-compose up -d

# Start with production configuration
docker-compose -f docker-compose.production.yml up -d

# Check system health
curl http://localhost:8000/health

# Check all service health
curl http://localhost:8000/system-status

# View real-time logs
docker-compose logs -f orchestrator
docker-compose logs -f portfolio
docker-compose logs -f risk-manager
```

## Trading Operations
```bash
# Start automated trading
curl -X POST http://localhost:8000/start-orchestration

# Stop automated trading
curl -X POST http://localhost:8000/stop-orchestration

# Execute manual trading cycle
curl -X POST http://localhost:8000/manual-cycle

# Check orchestration status
curl http://localhost:8000/orchestration-status
```

## Portfolio and Performance
```bash
# Get current portfolio
curl http://localhost:8001/portfolio

# Get performance metrics
curl http://localhost:8001/performance

# Get trade history
curl http://localhost:8001/trades

# Get risk analysis
curl http://localhost:8002/risk-analysis
```

## MCP Server Management
```bash
# Check MCP servers status
curl http://localhost:9000/status

# List all MCP servers
curl http://localhost:9000/servers

# Start all MCP servers
curl -X POST http://localhost:9000/servers/start-all
```

## System Maintenance
```bash
# Update services
docker-compose pull && docker-compose up -d

# Backup database
cp database/paper_trading.db database/backup_$(date +%Y%m%d).db

# Monitor system
./scripts/monitor_system.sh

# Run system checks
./scripts/deployment_readiness_check.sh
```

## Development Workflow
```bash
# Run tests before deployment
python -m pytest

# Check Python version compatibility
./scripts/check_python_version.sh

# Setup test environment
./scripts/setup_test_environment.sh

# Cleanup old data
./scripts/cleanup_obsolete_files.py
```

## Backtesting
```bash
# Run backtesting
python run_backtesting.py

# Results are saved to files like:
# - backtest_results_YYYYMMDD_HHMMSS.json
# - optimization_results_YYYYMMDD_HHMMSS.json
```

## Utility Scripts
```bash
# Available in scripts/ directory:
./scripts/start_agents.sh          # Start all agent services
./scripts/stop_agents.sh           # Stop all agent services  
./scripts/check_agents.sh          # Check agent health
./scripts/run_tests.sh            # Execute test suite
./scripts/smoke_test.py           # Quick system validation
```

## Environment Variables
Key variables to configure in .env.production.local:
- TRADING_MODE=paper|live
- TRADING_SYMBOL=BTCUSDT
- TRADE_API_KEY, TRADE_SECRET (Binance)
- FRED_API_KEY (Federal Reserve data)
- SLACK_BOT_TOKEN, SLACK_WEBHOOK_URL
- HETZNER_API_TOKEN