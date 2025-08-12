#!/bin/bash

# AI Trading System - Test Environment Setup
# Sets up isolated test environment with all dependencies

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${CYAN}🔧 AI Trading System - Test Environment Setup${NC}"
echo -e "${CYAN}═════════════════════════════════════════════════${NC}"

# Install Python test dependencies
install_test_dependencies() {
    echo -e "${BLUE}📦 Installing Python test dependencies...${NC}"
    
    pip install -q pytest pytest-asyncio pytest-mock pytest-html pytest-cov pytest-xdist pytest-profiling
    
    echo -e "${GREEN}✅ Python test dependencies installed${NC}"
}

# Setup test database
setup_test_database() {
    echo -e "${BLUE}🗄️  Setting up test database...${NC}"
    
    TEST_DB_DIR="$PROJECT_ROOT/test_data"
    mkdir -p "$TEST_DB_DIR"
    
    # Create test database schema
    python3 << EOF
import sqlite3
import os

db_path = os.path.join('$TEST_DB_DIR', 'test.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create portfolio table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_portfolio (
        id INTEGER PRIMARY KEY,
        usdc_balance REAL NOT NULL,
        btc_balance REAL NOT NULL,
        total_value REAL NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Create trades table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS paper_trades (
        id INTEGER PRIMARY KEY,
        trade_id TEXT UNIQUE NOT NULL,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        total REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        signal_type TEXT,
        rsi_value REAL
    )
''')

# Insert initial test data
cursor.execute('''
    INSERT OR REPLACE INTO paper_portfolio (id, usdc_balance, btc_balance, total_value)
    VALUES (1, 10000.0, 0.0, 10000.0)
''')

conn.commit()
conn.close()

print("Test database setup complete")
EOF
    
    echo -e "${GREEN}✅ Test database setup complete${NC}"
}

# Create test configuration
create_test_config() {
    echo -e "${BLUE}⚙️  Creating test configuration...${NC}"
    
    TEST_CONFIG_DIR="$PROJECT_ROOT/test_config"
    mkdir -p "$TEST_CONFIG_DIR"
    
    cat > "$TEST_CONFIG_DIR/test_config.yaml" << EOF
# Test configuration for AI Trading System
system:
  name: AI Trading System - Test Environment
  version: test
  environment: test

trading:
  symbol: BTCUSDT
  starting_balance: 10000.0
  mode: paper
  strategy: RSI

risk_management:
  max_position_size: 0.25
  stop_loss_pct: 0.05
  take_profit_pct: 0.10

technical_indicators:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  bb_period: 20
  bb_std: 2

services:
  orchestrator_url: http://localhost:8000
  portfolio_url: http://localhost:8001
  risk_manager_url: http://localhost:8002
  market_analyst_url: http://localhost:8003
  notification_url: http://localhost:8004

testing:
  mock_external_apis: true
  disable_notifications: true
  use_test_database: true
  log_level: WARNING
EOF
    
    echo -e "${GREEN}✅ Test configuration created${NC}"
}

# Setup test environment variables
setup_test_env_vars() {
    echo -e "${BLUE}🌍 Setting up test environment variables...${NC}"
    
    cat > "$PROJECT_ROOT/.env.test" << EOF
# Test Environment Variables
TESTING=true
PYTHONPATH=$PROJECT_ROOT

# Database
DB_PATH=$PROJECT_ROOT/test_data/test.db

# Trading Configuration
TRADING_SYMBOL=BTCUSDT
STARTING_BALANCE=10000.0
TRADING_MODE=paper
TRADING_STRATEGY=RSI

# Service URLs (for testing)
ORCHESTRATOR_URL=http://localhost:8000
PORTFOLIO_SERVICE_URL=http://localhost:8001
RISK_MANAGER_URL=http://localhost:8002
ANALYST_AGENT_URL=http://localhost:8003
NOTIFICATION_SERVICE_URL=http://localhost:8004

# External APIs (mocked in tests)
OLLAMA_URL=http://localhost:11434
SLACK_BOT_TOKEN=test-token
NOTION_TOKEN=test-token

# Logging
LOG_LEVEL=WARNING
DISABLE_NOTIFICATIONS=true
MOCK_EXTERNAL_APIS=true

# Test-specific settings
TEST_TIMEOUT=30
MAX_CONCURRENT_TESTS=5
ENABLE_TEST_PROFILING=false
EOF
    
    echo -e "${GREEN}✅ Test environment variables configured${NC}"
}

# Create test data fixtures
create_test_fixtures() {
    echo -e "${BLUE}📊 Creating test data fixtures...${NC}"
    
    FIXTURES_DIR="$PROJECT_ROOT/tests/fixtures"
    mkdir -p "$FIXTURES_DIR"
    
    # Market data fixture
    cat > "$FIXTURES_DIR/market_data.json" << EOF
{
    "symbol": "BTCUSDT",
    "price": "50000.00",
    "volume": "1000000.00",
    "change_24h": "2.5",
    "high_24h": "52000.00",
    "low_24h": "48000.00",
    "timestamp": "2024-01-01T12:00:00Z"
}
EOF
    
    # Trading signal fixture
    cat > "$FIXTURES_DIR/trading_signals.json" << EOF
[
    {
        "signal": "BUY",
        "confidence": 85.0,
        "technical_indicators": {
            "rsi": 25.5,
            "macd": {"macd": 150, "signal": 100, "histogram": 50},
            "bollinger_bands": {"position": "LOWER"}
        },
        "timestamp": "2024-01-01T12:00:00Z"
    },
    {
        "signal": "SELL", 
        "confidence": 80.0,
        "technical_indicators": {
            "rsi": 75.5,
            "macd": {"macd": -150, "signal": -100, "histogram": -50},
            "bollinger_bands": {"position": "UPPER"}
        },
        "timestamp": "2024-01-01T12:05:00Z"
    },
    {
        "signal": "HOLD",
        "confidence": 60.0,
        "technical_indicators": {
            "rsi": 50.0,
            "macd": {"macd": 0, "signal": 0, "histogram": 0},
            "bollinger_bands": {"position": "MIDDLE"}
        },
        "timestamp": "2024-01-01T12:10:00Z"
    }
]
EOF
    
    # Portfolio states fixture
    cat > "$FIXTURES_DIR/portfolio_states.json" << EOF
[
    {
        "name": "initial_state",
        "usdt_balance": 10000.0,
        "btc_balance": 0.0,
        "total_value": 10000.0
    },
    {
        "name": "after_buy",
        "usdt_balance": 5000.0,
        "btc_balance": 0.1,
        "total_value": 10000.0
    },
    {
        "name": "after_sell", 
        "usdt_balance": 10000.0,
        "btc_balance": 0.0,
        "total_value": 10000.0
    }
]
EOF
    
    echo -e "${GREEN}✅ Test fixtures created${NC}"
}

# Setup test reporting directory
setup_test_reporting() {
    echo -e "${BLUE}📈 Setting up test reporting...${NC}"
    
    REPORTS_DIR="$PROJECT_ROOT/test_results"
    mkdir -p "$REPORTS_DIR/coverage"
    mkdir -p "$REPORTS_DIR/performance"
    mkdir -p "$REPORTS_DIR/logs"
    
    # Create index page for test reports
    cat > "$REPORTS_DIR/index.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading System - Test Reports</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .link { display: block; padding: 10px; background: #e9e9e9; margin: 5px 0; text-decoration: none; color: #333; }
        .link:hover { background: #d9d9d9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 AI Trading System - Test Reports</h1>
        <p>Comprehensive testing dashboard for the AI Trading System</p>
    </div>
    
    <div class="section">
        <h2>📊 Test Reports</h2>
        <a href="report.html" class="link">📋 Latest Test Results</a>
        <a href="junit.xml" class="link">🔬 JUnit XML Report</a>
    </div>
    
    <div class="section">
        <h2>📈 Coverage Reports</h2>
        <a href="coverage/index.html" class="link">📊 Code Coverage Report</a>
    </div>
    
    <div class="section">
        <h2>⚡ Performance Reports</h2>
        <a href="performance/" class="link">🚀 Performance Test Results</a>
    </div>
    
    <div class="section">
        <h2>📝 Test Logs</h2>
        <a href="logs/" class="link">📋 Test Execution Logs</a>
    </div>
</body>
</html>
EOF
    
    echo -e "${GREEN}✅ Test reporting setup complete${NC}"
}

# Validate test environment
validate_test_environment() {
    echo -e "${BLUE}✅ Validating test environment...${NC}"
    
    # Check Python and pytest
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 not found${NC}"
        exit 1
    fi
    
    if ! command -v pytest &> /dev/null; then
        echo -e "${RED}❌ pytest not found${NC}"
        exit 1
    fi
    
    # Check test database
    if [[ ! -f "$PROJECT_ROOT/test_data/test.db" ]]; then
        echo -e "${RED}❌ Test database not found${NC}"
        exit 1
    fi
    
    # Check configuration
    if [[ ! -f "$PROJECT_ROOT/test_config/test_config.yaml" ]]; then
        echo -e "${RED}❌ Test configuration not found${NC}"
        exit 1
    fi
    
    # Test database connectivity
    python3 << EOF
import sqlite3
import sys

try:
    conn = sqlite3.connect('$PROJECT_ROOT/test_data/test.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM paper_portfolio")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        print("❌ Test database has no data")
        sys.exit(1)
    else:
        print(f"✅ Test database validated ({count} portfolio record)")
        
except Exception as e:
    print(f"❌ Database validation failed: {e}")
    sys.exit(1)
EOF
    
    echo -e "${GREEN}✅ Test environment validation complete${NC}"
}

# Main setup function
main() {
    echo -e "${BLUE}Starting test environment setup...${NC}"
    echo ""
    
    install_test_dependencies
    setup_test_database
    create_test_config
    setup_test_env_vars
    create_test_fixtures
    setup_test_reporting
    validate_test_environment
    
    echo ""
    echo -e "${GREEN}🎉 Test environment setup complete!${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. Run tests: ${BLUE}./scripts/run_tests.sh${NC}"
    echo -e "  2. Run specific test suite: ${BLUE}./scripts/run_tests.sh unit --coverage${NC}"
    echo -e "  3. View test reports: ${BLUE}open test_results/index.html${NC}"
    echo ""
    echo -e "${YELLOW}Environment files created:${NC}"
    echo -e "  • Test database: test_data/test.db"
    echo -e "  • Test config: test_config/test_config.yaml"
    echo -e "  • Environment vars: .env.test"
    echo -e "  • Test fixtures: tests/fixtures/"
    echo -e "  • Reports directory: test_results/"
}

# Run main function
main "$@"