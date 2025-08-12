"""
Test configuration and fixtures for the AI Trading System
"""
import pytest
import asyncio
import tempfile
import os
import sqlite3
import yaml
from pathlib import Path
from typing import Generator, Dict, Any
import aiohttp
from fastapi.testclient import TestClient
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'trading': {
            'symbol': 'BTCUSDC',
            'starting_balance': 10000.0,
            'mode': 'paper'
        },
        'risk_management': {
            'max_position_size': 0.25,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.10
        },
        'services': {
            'orchestrator': {'port': 8000},
            'portfolio': {'port': 8001},
            'risk_manager': {'port': 8002},
            'market_analyst': {'port': 8003},
            'notification': {'port': 8004},
            'trade_executor': {'port': 8005}
        }
    }

@pytest.fixture
def test_env_vars(temp_db, test_config):
    """Set up test environment variables"""
    project_root = os.path.join(os.path.dirname(__file__), '..')
    env_vars = {
        'DB_PATH': temp_db,
        'TRADING_SYMBOL': test_config['trading']['symbol'],
        'STARTING_BALANCE': str(test_config['trading']['starting_balance']),
        'TRADING_MODE': test_config['trading']['mode'],
        'SERVICE_PORT': '8001',
        'OLLAMA_URL': 'http://localhost:11434',
        'SLACK_BOT_TOKEN': 'test-token',
        'PYTHONPATH': project_root,
        'CONFIG_PATH': os.path.join(project_root, 'config', 'production_config.yaml'),
        'TEMPLATES_PATH': os.path.join(project_root, 'config', 'message_templates.yaml'),
        'RISK_MANAGER_URL': 'http://risk-manager:8002',
        'ANALYST_AGENT_URL': 'http://analyst-agent:8003'
    }
    
    # Set environment variables
    original_env = {}
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env_vars
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing"""
    return {
        'usdc_balance': 10000.0,
        'btc_balance': 0.0,
        'eth_balance': 0.0,
        'sol_balance': 0.0,
        'total_value': 10000.0
    }

@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return {
        'side': 'BUY',
        'signal_type': 'RSI_OVERSOLD',
        'rsi_value': 25.5,
        'quantity': 0.1,
        'price': 50000.0
    }

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'symbol': 'BTCUSDT',
        'price': 50000.0,
        'volume': 1000000.0,
        'change_24h': 2.5,
        'timestamp': '2024-01-01T12:00:00Z'
    }

@pytest.fixture
def sample_signal_data():
    """Sample trading signal data"""
    return {
        'signal': 'BUY',
        'confidence': 75.0,
        'rsi': 25.5,
        'macd': 0.5,
        'bollinger_position': 'LOWER',
        'timestamp': '2024-01-01T12:00:00Z'
    }

@pytest.fixture
async def aiohttp_session():
    """Create an aiohttp session for testing"""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        'model': 'mistral',
        'response': 'Based on the technical indicators, I recommend a BUY signal with high confidence due to oversold RSI conditions.',
        'done': True
    }

class MockSlackLogger:
    """Mock Slack logger for testing"""
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.messages = []
    
    def log_info(self, message: str):
        self.messages.append(('info', message))
    
    def log_error(self, message: str):
        self.messages.append(('error', message))
    
    def log_trade(self, trade_data: dict):
        self.messages.append(('trade', trade_data))

@pytest.fixture
def mock_slack_logger():
    """Mock Slack logger fixture"""
    return MockSlackLogger

# Service test fixtures
@pytest.fixture
def portfolio_service_client(test_env_vars, setup_test_database):
    """Create TestClient for portfolio service"""
    # Ensure the DB_PATH environment variable is set to the test database
    os.environ['DB_PATH'] = setup_test_database
    from src.portfolio_service import app, portfolio_manager
    
    # Reset the global portfolio manager to use the test database
    portfolio_manager.reset_database_path(setup_test_database)
    
    return TestClient(app)

@pytest.fixture
def orchestrator_service_client(test_env_vars, setup_test_database):
    """Create TestClient for orchestrator service"""
    # Ensure the DB_PATH environment variable is set to the test database
    os.environ['DB_PATH'] = setup_test_database
    from src.orchestrator_service import app
    return TestClient(app)

@pytest.fixture
def notification_service_client(test_env_vars, setup_test_database):
    """Create TestClient for notification service"""
    # Ensure the DB_PATH environment variable is set to the test database
    os.environ['DB_PATH'] = setup_test_database
    from src.notification_service import app
    return TestClient(app)

# Database fixtures
@pytest.fixture
def setup_test_database(temp_db, sample_portfolio_data):
    """Set up test database with initial data"""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Create portfolio table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id INTEGER PRIMARY KEY,
            usdc_balance REAL NOT NULL,
            btc_balance REAL NOT NULL,
            eth_balance REAL NOT NULL,
            sol_balance REAL NOT NULL,
            total_value REAL NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert initial portfolio data
    cursor.execute("""
        INSERT INTO paper_portfolio (id, usdc_balance, btc_balance, eth_balance, sol_balance, total_value)
        VALUES (1, ?, ?, ?, ?, ?)
    """, (sample_portfolio_data['usdc_balance'],
          sample_portfolio_data['btc_balance'],
          sample_portfolio_data.get('eth_balance', 0.0),
          sample_portfolio_data.get('sol_balance', 0.0),
          sample_portfolio_data['total_value']))
    
    # Create trades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT UNIQUE NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            signal_type TEXT,
            rsi_value REAL,
            status TEXT DEFAULT 'FILLED',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create positions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL,
            take_profit REAL,
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    return temp_db