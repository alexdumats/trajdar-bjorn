"""
Unit tests for Portfolio Service
"""
import pytest
import json
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestPortfolioService:
    """Test suite for Portfolio Service"""
    
    def test_health_endpoint(self, portfolio_service_client, setup_test_database):
        """Test health check endpoint"""
        response = portfolio_service_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "portfolio"
    
    def test_get_portfolio(self, portfolio_service_client, setup_test_database):
        """Test getting portfolio data"""
        response = portfolio_service_client.get("/portfolio")
        assert response.status_code == 200
        data = response.json()
        
        assert "usdc_balance" in data
        assert "btc_balance" in data
        assert "total_value" in data
        assert "last_updated" in data
        assert data["usdc_balance"] == 10000.0
        assert data["btc_balance"] == 0.0
    
    def test_execute_trade_buy(self, portfolio_service_client, setup_test_database):
        """Test executing a buy trade"""
        trade_request = {
            "side": "BUY",
            "signal_type": "RSI_OVERSOLD", 
            "rsi_value": 25.5
        }
        
        with patch('src.portfolio_service.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"price": "50000.0"}
            mock_get.return_value.status_code = 200
            
            response = portfolio_service_client.post("/execute_trade", json=trade_request)
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] == True
            assert "trade_id" in data
            assert data["side"] == "BUY"
    
    def test_execute_trade_sell(self, portfolio_service_client, setup_test_database):
        """Test executing a sell trade"""
        # First add some BTC to portfolio
        conn = sqlite3.connect(setup_test_database)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE paper_portfolio
            SET btc_balance = 0.2, usdc_balance = 0.0, total_value = 10000.0
            WHERE id = 1
        """)
        conn.commit()
        conn.close()
        
        trade_request = {
            "side": "SELL",
            "signal_type": "RSI_OVERBOUGHT",
            "rsi_value": 75.5
        }
        
        with patch('src.portfolio_service.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"price": "50000.0"}
            mock_get.return_value.status_code = 200
            
            response = portfolio_service_client.post("/execute_trade", json=trade_request)
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] == True
            assert data["side"] == "SELL"
    
    def test_execute_trade_insufficient_balance(self, portfolio_service_client, setup_test_database):
        """Test trade execution with insufficient balance"""
        trade_request = {
            "side": "SELL",
            "signal_type": "RSI_OVERBOUGHT",
            "rsi_value": 75.5
        }
        
        response = portfolio_service_client.post("/execute_trade", json=trade_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "No BTC to sell" in data["error"]
    
    def test_get_performance_metrics(self, portfolio_service_client, setup_test_database):
        """Test getting performance metrics"""
        response = portfolio_service_client.get("/performance")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_trades" in data
        assert "pnl" in data
        assert "pnl_percentage" in data
        assert "current_balance" in data
        assert "portfolio" in data
    
    def test_get_trades_history(self, portfolio_service_client, setup_test_database):
        """Test getting trades history"""
        response = portfolio_service_client.get("/trades")
        assert response.status_code == 200
        data = response.json()
        
        assert "trades" in data
        assert "count" in data
        assert isinstance(data["trades"], list)
        # Initially empty for new test database
        assert data["count"] >= 0
    
    def test_get_positions(self, portfolio_service_client, setup_test_database):
        """Test getting current positions"""
        response = portfolio_service_client.get("/positions")
        assert response.status_code == 200
        data = response.json()
        
        assert "positions" in data
        assert "count" in data
        assert isinstance(data["positions"], list)
    
    def test_stop_loss_take_profit_check(self, portfolio_service_client, setup_test_database):
        """Test stop loss and take profit checking"""
        response = portfolio_service_client.get("/check_stop_loss_take_profit")
        assert response.status_code == 200
        data = response.json()
        
        assert "triggered_trades" in data
        assert isinstance(data["triggered_trades"], list)


class TestPortfolioManager:
    """Test suite for PortfolioManager class"""
    
    def test_portfolio_manager_initialization(self, test_env_vars, temp_db):
        """Test PortfolioManager initialization"""
        with patch('src.portfolio_service.get_config') as mock_config:
            mock_config.return_value.get_risk_management_config.return_value = {
                'max_position_size': 0.25,
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10
            }
            mock_config.return_value.get_portfolio_config.return_value = {
                'starting_balance': 10000.0
            }
            
            from src.portfolio_service import PortfolioManager
            
            manager = PortfolioManager()
            assert manager.db_path == temp_db
            assert manager.symbol == 'BTCUSDT'
            assert manager.position_size_pct == 0.25
            assert manager.starting_balance == 10000.0
    
    def test_database_initialization(self, test_env_vars, temp_db):
        """Test database table creation"""
        with patch('src.portfolio_service.get_config') as mock_config:
            mock_config.return_value.get_risk_management_config.return_value = {
                'max_position_size': 0.25,
                'stop_loss_pct': 0.05, 
                'take_profit_pct': 0.10
            }
            mock_config.return_value.get_portfolio_config.return_value = {
                'starting_balance': 10000.0
            }
            
            from src.portfolio_service import PortfolioManager
            
            manager = PortfolioManager()
            
            # Check that tables were created
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'paper_portfolio' in tables
            assert 'paper_trades' in tables
            conn.close()
    
    def test_calculate_position_size(self, test_env_vars, temp_db):
        """Test position size calculation"""
        with patch('src.portfolio_service.get_config') as mock_config:
            mock_config.return_value.get_risk_management_config.return_value = {
                'max_position_size': 0.25,
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10
            }
            mock_config.return_value.get_portfolio_config.return_value = {
                'starting_balance': 10000.0
            }
            
            from src.portfolio_service import PortfolioManager
            
            manager = PortfolioManager()
            
            # Test position size calculation
            usdc_balance = 10000.0
            btc_price = 50000.0

            position_size = manager.calculate_position_size(usdc_balance, btc_price)
            expected_size = (usdc_balance * 0.25) / btc_price
            
            assert abs(position_size - expected_size) < 1e-6
    
    @patch('src.portfolio_service.SlackWebhookLogger')
    def test_slack_logging_integration(self, mock_slack_logger, test_env_vars, temp_db):
        """Test Slack webhook logger integration"""
        with patch('src.portfolio_service.get_config') as mock_config:
            mock_config.return_value.get_risk_management_config.return_value = {
                'max_position_size': 0.25,
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10
            }
            mock_config.return_value.get_portfolio_config.return_value = {
                'starting_balance': 10000.0
            }
            
            from src.portfolio_service import PortfolioManager
            
            manager = PortfolioManager()
            
            # Verify SlackWebhookLogger was initialized
            mock_slack_logger.assert_called_once_with("portfolio")