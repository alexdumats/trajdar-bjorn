"""
Unit tests for Paper Trading Engine
"""
import pytest
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime

from src.paper_trading_engine import PaperTradingEngine


class TestPaperTradingEngine:
    """Test suite for PaperTradingEngine"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        mock_config = MagicMock()
        
        # Configure risk management
        mock_config.get_risk_management_config.return_value = {
            'max_position_size': 0.05,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.1,
            'min_usdc_balance': 100.0
        }
        
        # Configure portfolio
        mock_config.get_portfolio_config.return_value = {
            'starting_balance': 10000.0
        }
        
        # Configure RSI
        mock_config.get_rsi_config.return_value = {
            'period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'neutral_value': 50.0
        }
        
        # Configure execution
        mock_config.get_execution_config.return_value = {
            'klines_limit': 50,
            'price_history_limit': 50
        }
        
        return mock_config
    
    def test_initialization(self, temp_db, mock_config):
        """Test initialization with different parameters"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            # Test with explicit db_path
            engine = PaperTradingEngine(db_path=temp_db)
            assert engine.db_path == temp_db
            assert engine.symbol == "BTCUSDC"
            assert engine.position_size_pct == 0.05
            assert engine.stop_loss_pct == 0.05
            assert engine.take_profit_pct == 0.1
            assert engine.starting_balance == 10000.0
    
    def test_init_database(self, temp_db, mock_config):
        """Test database initialization"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Verify tables were created
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # Check portfolio table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_portfolio'")
            assert cursor.fetchone() is not None
            
            # Check trades table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trades'")
            assert cursor.fetchone() is not None
            
            # Check positions table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paper_positions'")
            assert cursor.fetchone() is not None
            
            # Check initial portfolio data
            cursor.execute("SELECT usdc_balance, btc_balance, total_value FROM paper_portfolio WHERE id = 1")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 10000.0  # usdc_balance
            assert row[1] == 0.0      # btc_balance
            assert row[2] == 10000.0  # total_value
            
            conn.close()
    
    def test_get_current_price(self, temp_db, mock_config):
        """Test getting current price"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config), \
             patch('src.paper_trading_engine.requests.get') as mock_get:
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"price": "50000.0"}
            mock_get.return_value = mock_response
            
            engine = PaperTradingEngine(db_path=temp_db)
            price = engine.get_current_price()
            
            assert price == 50000.0
            mock_get.assert_called_once()
            
            # Test error handling
            mock_get.side_effect = Exception("API Error")
            price = engine.get_current_price()
            assert price is None
    
    def test_get_klines(self, temp_db, mock_config):
        """Test getting klines data"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config), \
             patch('src.paper_trading_engine.requests.get') as mock_get:
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_klines = [
                [1640995200000, "50000", "51000", "49000", "50500", "1000", 1640995260000, "50000000", 100, "500", "25000000", "0"]
                for i in range(50)
            ]
            mock_response.json.return_value = mock_klines
            mock_get.return_value = mock_response
            
            engine = PaperTradingEngine(db_path=temp_db)
            klines = engine.get_klines()
            
            assert len(klines) == 50
            assert klines[0][4] == "50500"  # Close price
            mock_get.assert_called_once()
            
            # Test error handling
            mock_get.side_effect = Exception("API Error")
            klines = engine.get_klines()
            assert klines == []
    
    def test_calculate_rsi(self, temp_db, mock_config):
        """Test RSI calculation"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Test with upward trend
            prices = [50000 + i * 100 for i in range(20)]
            rsi = engine.calculate_rsi(prices)
            
            # RSI should be above 50 for upward trend
            assert rsi > 50
            assert 0 <= rsi <= 100
            
            # Test with downward trend
            prices = [50000 - i * 100 for i in range(20)]
            rsi = engine.calculate_rsi(prices)
            
            # RSI should be below 50 for downward trend
            assert rsi < 50
            assert 0 <= rsi <= 100
            
            # Test with insufficient data
            prices = [50000, 50100]
            rsi = engine.calculate_rsi(prices)
            assert rsi == 50.0  # Should return neutral value
    
    def test_get_portfolio(self, temp_db, mock_config):
        """Test getting portfolio data"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Get initial portfolio
            portfolio = engine.get_portfolio()
            assert portfolio["usdc_balance"] == 10000.0
            assert portfolio["btc_balance"] == 0.0
            assert portfolio["total_value"] == 10000.0
            
            # Modify portfolio and check again
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE paper_portfolio
                SET usdc_balance = 5000.0, btc_balance = 0.1, total_value = 10000.0
                WHERE id = 1
            """)
            conn.commit()
            conn.close()
            
            portfolio = engine.get_portfolio()
            assert portfolio["usdc_balance"] == 5000.0
            assert portfolio["btc_balance"] == 0.1
            assert portfolio["total_value"] == 10000.0
    
    def test_update_portfolio(self, temp_db, mock_config):
        """Test updating portfolio data"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Update portfolio
            engine.update_portfolio(5000.0, 0.1, 10000.0)
            
            # Verify update
            portfolio = engine.get_portfolio()
            assert portfolio["usdc_balance"] == 5000.0
            assert portfolio["btc_balance"] == 0.1
            assert portfolio["total_value"] == 10000.0
    
    def test_execute_paper_trade_buy(self, temp_db, mock_config):
        """Test executing a buy trade"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config), \
             patch.object(PaperTradingEngine, 'get_current_price', return_value=50000.0):
            
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Execute buy trade
            result = engine.execute_paper_trade("BUY", "RSI_OVERSOLD", 25.0)
            
            # Verify result
            assert result["success"] is True
            assert result["side"] == "BUY"
            assert result["price"] == 50000.0
            assert abs(result["quantity"] - 0.01) < 0.0001  # 500 / 50000 = 0.01 BTC
            
            # Verify portfolio update
            portfolio = engine.get_portfolio()
            assert abs(portfolio["usdc_balance"] - 9500.0) < 0.01
            assert abs(portfolio["btc_balance"] - 0.01) < 0.0001
            
            # Verify trade record
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE side = 'BUY'")
            count = cursor.fetchone()[0]
            assert count == 1
            
            # Verify position record
            cursor.execute("SELECT COUNT(*) FROM paper_positions WHERE side = 'BUY' AND status = 'OPEN'")
            count = cursor.fetchone()[0]
            assert count == 1
            conn.close()
    
    def test_execute_paper_trade_sell(self, temp_db, mock_config):
        """Test executing a sell trade"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config), \
             patch.object(PaperTradingEngine, 'get_current_price', return_value=50000.0):
            
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Set up portfolio with BTC
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE paper_portfolio
                SET usdc_balance = 5000.0, btc_balance = 0.1, total_value = 10000.0
                WHERE id = 1
            """)
            conn.commit()
            conn.close()
            
            # Execute sell trade
            result = engine.execute_paper_trade("SELL", "RSI_OVERBOUGHT", 75.0)
            
            # Verify result
            assert result["success"] is True
            assert result["side"] == "SELL"
            assert result["price"] == 50000.0
            assert abs(result["quantity"] - 0.1) < 0.0001
            
            # Verify portfolio update
            portfolio = engine.get_portfolio()
            assert abs(portfolio["usdc_balance"] - 10000.0) < 0.01
            assert portfolio["btc_balance"] == 0.0
            
            # Verify trade record
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE side = 'SELL'")
            count = cursor.fetchone()[0]
            assert count == 1
            conn.close()
    
    def test_execute_paper_trade_insufficient_balance(self, temp_db, mock_config):
        """Test executing a trade with insufficient balance"""
        # Create a modified config with a higher position size percentage
        modified_mock_config = MagicMock()
        modified_mock_config.get_risk_management_config.return_value = {
            'max_position_size': 1.0,  # 100% position size
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.1,
            'min_usdc_balance': 100.0  # Require at least 100 USDT
        }
        modified_mock_config.get_portfolio_config.return_value = mock_config.get_portfolio_config.return_value
        modified_mock_config.get_rsi_config.return_value = mock_config.get_rsi_config.return_value
        modified_mock_config.get_execution_config.return_value = mock_config.get_execution_config.return_value
        
        with patch('src.paper_trading_engine.get_config', return_value=modified_mock_config), \
             patch.object(PaperTradingEngine, 'get_current_price', return_value=50000.0):
            
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Set up portfolio with insufficient USDT
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE paper_portfolio
                SET usdc_balance = 10.0, btc_balance = 0.0, total_value = 10.0
                WHERE id = 1
            """)
            conn.commit()
            conn.close()
            
            # Execute buy trade - should fail due to min_usdc_balance requirement
            result = engine.execute_paper_trade("BUY", "RSI_OVERSOLD", 25.0)
            
            # Verify result
            assert result["success"] is False
            assert "Insufficient USDC balance" in result["error"]
            
            # Try sell with no BTC
            result = engine.execute_paper_trade("SELL", "RSI_OVERBOUGHT", 75.0)
            
            # Verify result
            assert result["success"] is False
            assert "No BTC to sell" in result["error"]
    
    def test_check_stop_loss_take_profit(self, temp_db, mock_config):
        """Test stop loss and take profit functionality"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Set up portfolio with BTC
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE paper_portfolio
                SET usdc_balance = 5000.0, btc_balance = 0.1, total_value = 10000.0
                WHERE id = 1
            """)
            
            # Create an open position
            cursor.execute("""
                INSERT INTO paper_positions (symbol, side, quantity, entry_price, stop_loss, take_profit, status)
                VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
            """, ("BTCUSDT", "BUY", 0.1, 50000.0, 47500.0, 55000.0))
            conn.commit()
            conn.close()
            
            # Test stop loss trigger
            with patch.object(PaperTradingEngine, 'get_current_price', return_value=47000.0):
                triggered = engine.check_stop_loss_take_profit()
                assert len(triggered) == 1
                assert triggered[0]["type"] == "STOP_LOSS"
                
                # Verify position was closed
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM paper_positions WHERE status = 'OPEN'")
                count = cursor.fetchone()[0]
                assert count == 0
                conn.close()
            
            # Reset for take profit test
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE paper_portfolio
                SET usdc_balance = 5000.0, btc_balance = 0.1, total_value = 10000.0
                WHERE id = 1
            """)
            
            # Create another open position
            cursor.execute("""
                INSERT INTO paper_positions (symbol, side, quantity, entry_price, stop_loss, take_profit, status)
                VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
            """, ("BTCUSDT", "BUY", 0.1, 50000.0, 47500.0, 55000.0))
            conn.commit()
            conn.close()
            
            # Test take profit trigger
            with patch.object(PaperTradingEngine, 'get_current_price', return_value=56000.0):
                triggered = engine.check_stop_loss_take_profit()
                assert len(triggered) == 1
                assert triggered[0]["type"] == "TAKE_PROFIT"
    
    def test_get_trading_signal(self, temp_db, mock_config):
        """Test trading signal generation"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config), \
             patch.object(PaperTradingEngine, 'get_current_price', return_value=50000.0):
            
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Test oversold condition (BUY signal)
            with patch.object(PaperTradingEngine, 'get_klines') as mock_klines, \
                 patch.object(PaperTradingEngine, 'calculate_rsi', return_value=25.0):
                
                mock_klines.return_value = [
                    [1640995200000, "50000", "51000", "49000", "50500", "1000", 1640995260000, "50000000", 100, "500", "25000000", "0"]
                    for i in range(50)
                ]
                
                signal = engine.get_trading_signal()
                
                assert signal is not None
                assert signal["signal"] == "BUY"
                assert signal["rsi"] == 25.0
                assert "oversold" in signal["reason"].lower()
            
            # Test overbought condition (SELL signal)
            with patch.object(PaperTradingEngine, 'get_klines') as mock_klines, \
                 patch.object(PaperTradingEngine, 'calculate_rsi', return_value=75.0):
                
                mock_klines.return_value = [
                    [1640995200000, "50000", "51000", "49000", "50500", "1000", 1640995260000, "50000000", 100, "500", "25000000", "0"]
                    for i in range(50)
                ]
                
                # Set up portfolio with BTC
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE paper_portfolio
                    SET usdc_balance = 5000.0, btc_balance = 0.1, total_value = 10000.0
                    WHERE id = 1
                """)
                conn.commit()
                conn.close()
                
                signal = engine.get_trading_signal()
                
                assert signal is not None
                assert signal["signal"] == "SELL"
                assert signal["rsi"] == 75.0
                assert "overbought" in signal["reason"].lower()
            
            # Test neutral condition (no signal)
            with patch.object(PaperTradingEngine, 'get_klines') as mock_klines, \
                 patch.object(PaperTradingEngine, 'calculate_rsi', return_value=50.0):
                
                mock_klines.return_value = [
                    [1640995200000, "50000", "51000", "49000", "50500", "1000", 1640995260000, "50000000", 100, "500", "25000000", "0"]
                    for i in range(50)
                ]
                
                signal = engine.get_trading_signal()
                
                assert signal is not None
                assert signal["signal"] is None
                assert signal["rsi"] == 50.0
                assert "neutral" in signal["reason"].lower()
    
    def test_get_performance_summary(self, temp_db, mock_config):
        """Test performance summary generation"""
        with patch('src.paper_trading_engine.get_config', return_value=mock_config):
            engine = PaperTradingEngine(db_path=temp_db)
            
            # Set up portfolio with profit
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE paper_portfolio
                SET usdc_balance = 12000.0, btc_balance = 0.0, total_value = 12000.0
                WHERE id = 1
            """)
            
            # Add some trades
            for i in range(5):
                cursor.execute("""
                    INSERT INTO paper_trades (trade_id, symbol, side, quantity, price, total, signal_type, rsi_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (f"test_{i}", "BTCUSDT", "BUY" if i % 2 == 0 else "SELL", 0.1, 50000.0, 5000.0, "TEST", 50.0))
            
            conn.commit()
            conn.close()
            
            # Get performance summary
            summary = engine.get_performance_summary()
            
            # Verify summary
            assert summary["initial_balance"] == 10000.0
            assert summary["current_balance"] == 12000.0
            assert summary["pnl"] == 2000.0
            assert summary["pnl_percentage"] == 20.0
            assert summary["total_trades"] == 5
            assert len(summary["recent_trades"]) == 5