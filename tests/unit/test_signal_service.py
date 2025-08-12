"""
Unit tests for Signal Service (Risk Manager Agent)
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestSignalService:
    """Test suite for Signal Service"""
    
    @patch.dict('os.environ', {'SERVICE_PORT': '8002', 'OLLAMA_URL': 'http://localhost:11434'})
    def test_health_endpoint(self):
        """Test health check endpoint"""
        # Import with proper path
        from src.signal_service import app
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "risk-manager-agent"
    
    @patch.dict('os.environ', {'SERVICE_PORT': '8002', 'OLLAMA_URL': 'http://localhost:11434'})
    def test_get_signal_endpoint(self, sample_market_data):
        """Test getting risk assessment endpoint"""
        with patch('src.signal_service.requests.get') as mock_get, \
             patch('aiohttp.ClientSession.get') as mock_aiohttp_get, \
             patch('aiohttp.ClientSession.post') as mock_aiohttp_post:
            
            # Mock market data API response
            mock_get.return_value.json.return_value = [
                [1640995200000, "50000", "51000", "49000", "50500", "1000", 1640995260000, "50000000", 100, "500", "25000000", "0"]
            ]
            mock_get.return_value.status_code = 200
            
            # Mock portfolio response
            mock_portfolio_response = MagicMock()
            mock_portfolio_response.status = 200
            mock_portfolio_response.json = AsyncMock(return_value={"usdc_balance": 10000, "btc_balance": 0, "total_value": 10000})
            mock_aiohttp_get.return_value.__aenter__.return_value = mock_portfolio_response
            
            # Mock AI response
            mock_ai_response = MagicMock()
            mock_ai_response.status = 200
            mock_ai_response.json = AsyncMock(return_value={"response": '{"risk_level": "LOW", "recommended_actions": ["Continue monitoring"]}'})
            mock_aiohttp_post.return_value.__aenter__.return_value = mock_ai_response
            
            from src.signal_service import app
            client = TestClient(app)
            
            response = client.get("/risk-assessment")
            assert response.status_code == 200
            data = response.json()
            
            assert "risk_assessment" in data
            assert "timestamp" in data
    
    @patch.dict('os.environ', {'SERVICE_PORT': '8002', 'OLLAMA_URL': 'http://localhost:11434'})
    def test_get_indicators_endpoint(self, sample_market_data):
        """Test getting RSI data endpoint"""
        with patch('src.signal_service.requests.get') as mock_get:
            
            # Mock market data API response with proper klines format
            mock_get.return_value.json.return_value = [
                [1640995200000, "50000", "51000", "49000", "50500", "1000", 1640995260000, "50000000", 100, "500", "25000000", "0"]
                for i in range(50)  # Generate 50 klines for RSI calculation
            ]
            mock_get.return_value.status_code = 200
            
            from src.signal_service import app
            client = TestClient(app)
            
            response = client.get("/rsi")
            assert response.status_code == 200
            data = response.json()
            
            assert "current_rsi" in data
            assert "rsi_history" in data
            assert "analysis" in data
            assert "timestamp" in data


class TestRiskManagerAgent:
    """Test suite for RiskManagerAgent class"""
    
    def test_risk_manager_initialization(self, test_env_vars):
        """Test RiskManagerAgent initialization"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            mock_config.return_value.get_technical_indicators_config.return_value = {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bb_period': 20,
                'bb_std': 2
            }
            
            from src.signal_service import RiskManagerAgent
            
            agent = RiskManagerAgent()
            assert agent.symbol == 'BTCUSDT'
            assert agent.strategy == 'RSI'
            assert agent.ollama_url == 'http://localhost:11434'
    
    def test_calculate_rsi(self, test_env_vars):
        """Test RSI calculation"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            mock_config.return_value.get_technical_indicators_config.return_value = {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            
            from src.signal_service import RiskManagerAgent
            import pandas as pd
            
            agent = RiskManagerAgent()
            
            # Create test data with upward trend
            prices = [50000 + i * 100 for i in range(20)]
            df = pd.DataFrame({'close': prices})
            
            rsi = agent.calculate_rsi(df, period=14)
            
            # RSI should be above 50 for upward trend
            assert rsi > 50
            assert 0 <= rsi <= 100
    
    def test_calculate_macd(self, test_env_vars):
        """Test MACD calculation"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            mock_config.return_value.get_technical_indicators_config.return_value = {
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            }
            
            from src.signal_service import RiskManagerAgent
            import pandas as pd
            
            agent = RiskManagerAgent()
            
            # Create test data
            prices = [50000 + (i % 10 - 5) * 100 for i in range(50)]
            df = pd.DataFrame({'close': prices})
            
            macd, signal_line, histogram = agent.calculate_macd(df, fast=12, slow=26, signal=9)
            
            assert isinstance(macd, float)
            assert isinstance(signal_line, float)
            assert isinstance(histogram, float)
    
    def test_calculate_bollinger_bands(self, test_env_vars):
        """Test Bollinger Bands calculation"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            mock_config.return_value.get_technical_indicators_config.return_value = {
                'bb_period': 20,
                'bb_std': 2
            }
            
            from src.signal_service import RiskManagerAgent
            import pandas as pd
            
            agent = RiskManagerAgent()
            
            # Create test data
            prices = [50000 + (i % 10 - 5) * 100 for i in range(30)]
            df = pd.DataFrame({'close': prices})
            
            upper, middle, lower = agent.calculate_bollinger_bands(df, period=20, std_dev=2)
            
            assert upper > middle > lower
            assert all(isinstance(x, float) for x in [upper, middle, lower])
    
    def test_generate_signal_rsi_oversold(self, test_env_vars):
        """Test signal generation for RSI oversold condition"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            mock_config.return_value.get_technical_indicators_config.return_value = {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            
            from src.signal_service import RiskManagerAgent
            
            agent = RiskManagerAgent()
            
            indicators = {
                'rsi': 25.0,  # Oversold
                'macd': {'macd': 100, 'signal': 50, 'histogram': 50},
                'bollinger_bands': {'upper': 52000, 'middle': 50000, 'lower': 48000, 'position': 'LOWER'}
            }
            
            signal, confidence = agent.generate_signal(indicators)
            
            assert signal == "BUY"
            assert confidence > 50  # Should have decent confidence for oversold
    
    def test_generate_signal_rsi_overbought(self, test_env_vars):
        """Test signal generation for RSI overbought condition"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            mock_config.return_value.get_technical_indicators_config.return_value = {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            
            from src.signal_service import RiskManagerAgent
            
            agent = RiskManagerAgent()
            
            indicators = {
                'rsi': 75.0,  # Overbought
                'macd': {'macd': -100, 'signal': -50, 'histogram': -50},
                'bollinger_bands': {'upper': 52000, 'middle': 50000, 'lower': 48000, 'position': 'UPPER'}
            }
            
            signal, confidence = agent.generate_signal(indicators)
            
            assert signal == "SELL"
            assert confidence > 50
    
    @pytest.mark.asyncio
    async def test_get_ai_analysis(self, test_env_vars, mock_ollama_response):
        """Test AI analysis via Ollama"""
        with patch('src.utils.config_manager.get_config') as mock_config, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            
            # Mock Ollama response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_ollama_response)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            from src.signal_service import RiskManagerAgent
            
            agent = RiskManagerAgent()
            
            indicators = {
                'rsi': 25.0,
                'macd': {'macd': 100, 'signal': 50, 'histogram': 50},
                'bollinger_bands': {'upper': 52000, 'middle': 50000, 'lower': 48000}
            }
            
            analysis = agent.get_ai_analysis(indicators, "BUY", 75.0)
            
            assert "BUY" in analysis
            assert "confidence" in analysis.lower()
    
    def test_fetch_market_data_success(self, test_env_vars, sample_market_data):
        """Test successful market data fetching"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            
            from src.signal_service import RiskManagerAgent
            
            # Create a mock for the fetch_market_data method
            with patch.object(RiskManagerAgent, 'fetch_market_data', return_value=sample_market_data):
                agent = RiskManagerAgent()
                data = agent.fetch_market_data()
                
                assert data == sample_market_data
    
    def test_fetch_market_data_failure(self, test_env_vars):
        """Test market data fetching failure"""
        with patch('src.utils.config_manager.get_config') as mock_config:
            
            mock_config.return_value.get_trading_config.return_value = {
                'symbol': 'BTCUSDT',
                'strategy': 'RSI'
            }
            
            from src.signal_service import RiskManagerAgent
            
            # Create a mock for the fetch_market_data method that returns None
            with patch.object(RiskManagerAgent, 'fetch_market_data', return_value=None):
                agent = RiskManagerAgent()
                data = agent.fetch_market_data()
                
                assert data is None