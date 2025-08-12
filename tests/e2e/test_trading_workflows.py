"""
End-to-end tests for complete trading workflows
"""
import pytest
import asyncio
import aiohttp
import json
import sqlite3
import time
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor


class TestCompleteAutomatedTradingWorkflow:
    """Test suite for complete automated trading workflow"""
    
    @pytest.mark.asyncio
    async def test_full_automated_trading_cycle(self, setup_test_database, test_config):
        """Test complete automated trading cycle from signal generation to execution"""
        
        # Mock all service responses for a complete cycle
        service_responses = {
            "risk_manager_signal": {
                "signal": "BUY",
                "confidence": 85.0,
                "technical_indicators": {
                    "rsi": 23.5,
                    "macd": {"macd": 150, "signal": 100, "histogram": 50},
                    "bollinger_bands": {"position": "LOWER", "upper": 52000, "middle": 50000, "lower": 48000}
                },
                "ai_analysis": "Strong buy signal: RSI indicates oversold conditions, MACD shows bullish momentum",
                "risk_assessment": "LOW"
            },
            "market_analysis": {
                "trend": "bullish",
                "support_level": 48000,
                "resistance_level": 55000,
                "market_sentiment": "positive",
                "volume_analysis": "increasing",
                "news_sentiment": "bullish"
            },
            "portfolio_execution": {
                "status": "success",
                "trade_id": "e2e_trade_001",
                "side": "BUY",
                "symbol": "BTCUSDT",
                "quantity": 0.125,
                "price": 50000.0,
                "total_value": 6250.0,
                "timestamp": "2024-01-01T12:00:00Z"
            },
            "notification_sent": {
                "status": "sent",
                "message_id": "slack_msg_001",
                "channel": "trading-alerts",
                "timestamp": "2024-01-01T12:00:01Z"
            }
        }
        
        call_sequence = []
        
        @asynccontextmanager
        async def mock_service_call(url, **kwargs):
            call_sequence.append(f"GET {url}")
            
            mock_response = MagicMock()
            mock_response.status = 200
            
            if "/signal" in url and "risk-manager" in url:
                mock_response.json = AsyncMock(return_value=service_responses["risk_manager_signal"])
            elif "/analysis" in url and "market-news-analyst" in url:
                mock_response.json = AsyncMock(return_value=service_responses["market_analysis"])
            elif "/execute_trade" in url and "portfolio" in url:
                mock_response.json = AsyncMock(return_value=service_responses["portfolio_execution"])
            elif "/send" in url and "notification" in url:
                mock_response.json = AsyncMock(return_value=service_responses["notification_sent"])
            elif "/health" in url:
                mock_response.json = AsyncMock(return_value={"status": "healthy"})
            elif "/system-status" in url:
                mock_response.json = AsyncMock(return_value={
                    "services": {"all": "healthy"}, 
                    "orchestration": {"running": False}
                })
            else:
                mock_response.json = AsyncMock(return_value={"status": "ok"})
            
            yield mock_response
        
        @asynccontextmanager
        async def mock_service_call_post(url, **kwargs):
            call_sequence.append(f"POST {url}")
            
            mock_response = MagicMock()
            mock_response.status = 200
            
            if "/execute_trade" in url and "portfolio" in url:
                mock_response.json = AsyncMock(return_value=service_responses["portfolio_execution"])
            elif "/send" in url and "notification" in url:
                mock_response.json = AsyncMock(return_value=service_responses["notification_sent"])
            else:
                mock_response.json = AsyncMock(return_value={"status": "ok"})
            
            yield mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_service_call), \
             patch('aiohttp.ClientSession.post', side_effect=mock_service_call_post):
            
            # Simulate orchestrator running a complete cycle
            async with aiohttp.ClientSession() as session:
                
                # 1. Check system health
                async with session.get('http://orchestrator:8000/system-status') as response:
                    system_status = await response.json()
                    assert system_status["services"]["all"] == "healthy"
                
                # 2. Get risk analysis and signal
                async with session.get('http://risk-manager:8002/signal') as response:
                    risk_analysis = await response.json()
                    assert risk_analysis["signal"] == "BUY"
                    assert risk_analysis["confidence"] >= 80
                    assert risk_analysis["risk_assessment"] == "LOW"
                
                # 3. Get market analysis for confirmation
                async with session.get('http://market-news-analyst:8003/analysis') as response:
                    market_analysis = await response.json()
                    assert market_analysis["trend"] == "bullish"
                    assert market_analysis["market_sentiment"] == "positive"
                
                # 4. Execute trade based on signals alignment
                if (risk_analysis["signal"] == "BUY" and 
                    risk_analysis["confidence"] >= 80 and 
                    market_analysis["trend"] == "bullish"):
                    
                    trade_request = {
                        "side": risk_analysis["signal"],
                        "signal_type": "RSI_OVERSOLD",
                        "rsi_value": risk_analysis["technical_indicators"]["rsi"]
                    }
                    
                    async with session.post('http://portfolio-service:8001/execute_trade', 
                                          json=trade_request) as response:
                        trade_result = await response.json()
                        assert trade_result["status"] == "success"
                        assert trade_result["side"] == "BUY"
                        assert trade_result["trade_id"] == "e2e_trade_001"
                
                # 5. Send notification about trade execution
                notification_payload = {
                    "type": "trade_executed",
                    "message": f"🚀 Trade Executed: {trade_result['side']} {trade_result['quantity']} BTC at ${trade_result['price']:,.2f}",
                    "trade_data": trade_result,
                    "channel": "trading-alerts",
                    "priority": "high"
                }
                
                async with session.post('http://notification-service:8004/send', 
                                      json=notification_payload) as response:
                    notification_result = await response.json()
                    assert notification_result["status"] == "sent"
                    assert notification_result["channel"] == "trading-alerts"
        
        # Verify the complete workflow executed in correct sequence
        expected_calls = [
            "GET http://orchestrator:8000/system-status",
            "GET http://risk-manager:8002/signal", 
            "GET http://market-news-analyst:8003/analysis",
            "POST http://portfolio-service:8001/execute_trade",
            "POST http://notification-service:8004/send"
        ]
        
        for expected_call in expected_calls:
            assert expected_call in call_sequence
    
    @pytest.mark.asyncio
    async def test_risk_based_trade_rejection_workflow(self, setup_test_database):
        """Test workflow when risk analysis suggests rejecting trade"""
        
        # High risk scenario - should not execute trade
        risk_response = {
            "signal": "SELL",
            "confidence": 45.0,  # Low confidence
            "technical_indicators": {
                "rsi": 55.0,  # Neutral
                "macd": {"macd": 10, "signal": 15, "histogram": -5},
                "bollinger_bands": {"position": "MIDDLE"}
            },
            "ai_analysis": "Mixed signals, recommend holding position",
            "risk_assessment": "HIGH"  # High risk
        }
        
        trade_executed = False
        
        @asynccontextmanager
        async def mock_risky_scenario(url, **kwargs):
            nonlocal trade_executed
            
            mock_response = MagicMock()
            mock_response.status = 200
            
            if "/signal" in url and "risk-manager" in url:
                mock_response.json = AsyncMock(return_value=risk_response)
            elif "/execute_trade" in url:
                trade_executed = True
                mock_response.json = AsyncMock(return_value={"status": "rejected", "reason": "High risk assessment"})
            else:
                    mock_response.json = AsyncMock(return_value={"status": "healthy"})
            
            yield mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_risky_scenario), \
             patch('aiohttp.ClientSession.post', side_effect=mock_risky_scenario):
            
            async with aiohttp.ClientSession() as session:
                # Get risk analysis
                async with session.get('http://risk-manager:8002/signal') as response:
                    risk_analysis = await response.json()
                
                # Should NOT execute trade due to high risk and low confidence
                should_trade = (
                    risk_analysis["confidence"] >= 70 and 
                    risk_analysis["risk_assessment"] == "LOW"
                )
                
                assert should_trade == False
                assert risk_analysis["risk_assessment"] == "HIGH"
                assert risk_analysis["confidence"] < 70
                
                # Verify no trade was attempted
                assert trade_executed == False
    
    @pytest.mark.asyncio 
    async def test_market_conditions_override_workflow(self, setup_test_database):
        """Test workflow when market conditions override trading signals"""
        
        # Good technical signal but bad market conditions
        responses = {
            "risk_signal": {
                "signal": "BUY",
                "confidence": 80.0,
                "risk_assessment": "LOW"
            },
            "market_conditions": {
                "trend": "bearish",  # Conflicting with BUY signal
                "market_sentiment": "negative",
                "volatility": "high",
                "news_sentiment": "bearish",
                "volume_analysis": "decreasing"
            }
        }
        
        trade_attempted = False
        
        @asynccontextmanager
        async def mock_conflicting_signals(url, **kwargs):
            nonlocal trade_attempted
            
            mock_response = MagicMock()
            mock_response.status = 200
            
            if "/signal" in url and "risk-manager" in url:
                mock_response.json = AsyncMock(return_value=responses["risk_signal"])
            elif "/analysis" in url and "market-news-analyst" in url:
                mock_response.json = AsyncMock(return_value=responses["market_conditions"])
            elif "/execute_trade" in url:
                trade_attempted = True
                mock_response.json = AsyncMock(return_value={"status": "cancelled", "reason": "Conflicting market signals"})
            else:
                mock_response.json = AsyncMock(return_value={"status": "ok"})
            
            yield mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_conflicting_signals), \
             patch('aiohttp.ClientSession.post', side_effect=mock_conflicting_signals):
            
            async with aiohttp.ClientSession() as session:
                # Get risk signal
                async with session.get('http://risk-manager:8002/signal') as response:
                    risk_signal = await response.json()
                
                # Get market analysis
                async with session.get('http://market-news-analyst:8003/analysis') as response:
                    market_analysis = await response.json()
                
                # Check if signals align
                signals_aligned = (
                    risk_signal["signal"] == "BUY" and 
                    market_analysis["trend"] == "bullish" and
                    market_analysis["market_sentiment"] == "positive"
                )
                
                assert signals_aligned == False
                
                # Should not execute trade due to conflicting signals
                if not signals_aligned:
                    # Trade should be cancelled due to conflicting signals
                    assert trade_attempted == False


class TestErrorHandlingWorkflows:
    """Test suite for error handling in complete workflows"""
    
    @pytest.mark.asyncio
    async def test_service_failure_recovery_workflow(self, setup_test_database):
        """Test workflow recovery when services fail"""
        
        failure_count = 0
        max_failures = 2
        
        @asynccontextmanager
        async def mock_failing_then_recovering(url, **kwargs):
            nonlocal failure_count
            
            mock_response = MagicMock()
            
            if "risk-manager" in url and failure_count < max_failures:
                failure_count += 1
                raise aiohttp.ClientError(f"Service temporarily unavailable (attempt {failure_count})")
            else:
                mock_response.status = 200
                if "/signal" in url:
                    mock_response.json = AsyncMock(return_value={"signal": "HOLD", "confidence": 60.0})
                else:
                    mock_response.json = AsyncMock(return_value={"status": "healthy"})
            
            yield mock_response
        
        with patch('aiohttp.ClientSession.get', side_effect=mock_failing_then_recovering):
            
            async with aiohttp.ClientSession() as session:
                # Simulate retry logic
                max_retries = 3
                retry_count = 0
                signal_data = None
                
                while retry_count < max_retries and signal_data is None:
                    try:
                        async with session.get('http://risk-manager:8002/signal') as response:
                            signal_data = await response.json()
                            break
                    except aiohttp.ClientError:
                        retry_count += 1
                        if retry_count < max_retries:
                            await asyncio.sleep(0.1)  # Brief retry delay
                
                # Should eventually succeed after retries
                assert signal_data is not None
                assert signal_data["signal"] == "HOLD"
                assert retry_count == max_failures  # Took max_failures attempts to succeed
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback_workflow(self, setup_test_database):
        """Test workflow with database transaction rollback on failure"""
        
        db_path = setup_test_database
        
        # Simulate a trade execution that fails mid-process
        def simulate_failed_trade():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                # Update portfolio (this succeeds)
                cursor.execute("""
                    UPDATE paper_portfolio 
                    SET usdc_balance = usdc_balance - 5000,
                        btc_balance = btc_balance + 0.1
                    WHERE id = 1
                """)
                
                # Simulate failure when inserting trade record
                raise Exception("Network error during trade recording")
                
                # This would normally insert the trade record
                cursor.execute("""
                    INSERT INTO paper_trades (trade_id, symbol, side, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("failed_trade", "BTCUSDT", "BUY", 0.1, 50000.0, 5000.0))
                
                conn.commit()
                
            except Exception as e:
                # Rollback on any error
                conn.rollback()
                raise e
            finally:
                conn.close()
        
        # Get initial balances
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT usdc_balance, btc_balance FROM paper_portfolio WHERE id = 1")
        initial_balances = cursor.fetchone()
        conn.close()
        
        # Attempt failed trade
        with pytest.raises(Exception, match="Network error"):
            simulate_failed_trade()
        
        # Verify database state was rolled back
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT usdc_balance, btc_balance FROM paper_portfolio WHERE id = 1")
        final_balances = cursor.fetchone()
        
        # Verify trade record was not inserted
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE trade_id = 'failed_trade'")
        trade_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Balances should be unchanged due to rollback
        assert final_balances == initial_balances
        assert trade_count == 0


class TestPerformanceWorkflows:
    """Test suite for performance aspects of workflows"""
    
    @pytest.mark.asyncio
    async def test_concurrent_orchestration_cycles(self, setup_test_database):
        """Test multiple orchestration cycles running concurrently"""
        
        cycle_results = []
        
        @asynccontextmanager
        async def mock_fast_service(url, **kwargs):
            # Simulate fast service responses
            await asyncio.sleep(0.01)  # Small delay to simulate processing
            
            mock_response = MagicMock()
            mock_response.status = 200
            
            if "/signal" in url:
                mock_response.json = AsyncMock(return_value={"signal": "HOLD", "confidence": 50.0})
            elif "/analysis" in url:
                mock_response.json = AsyncMock(return_value={"trend": "sideways", "sentiment": "neutral"})
            else:
                mock_response.json = AsyncMock(return_value={"status": "ok"})
            
            yield mock_response
        
        async def run_orchestration_cycle(cycle_id):
            """Simulate a single orchestration cycle"""
            start_time = time.time()
            
            with patch('aiohttp.ClientSession.get', side_effect=mock_fast_service):
                async with aiohttp.ClientSession() as session:
                    # Get risk signal
                    async with session.get('http://risk-manager:8002/signal') as response:
                        risk_data = await response.json()
                    
                    # Get market analysis
                    async with session.get('http://market-news-analyst:8003/analysis') as response:
                        market_data = await response.json()
                    
                    end_time = time.time()
                    cycle_time = end_time - start_time
                    
                    cycle_results.append({
                        'cycle_id': cycle_id,
                        'duration': cycle_time,
                        'risk_signal': risk_data['signal'],
                        'market_trend': market_data['trend']
                    })
        
        # Run 5 concurrent orchestration cycles
        tasks = [run_orchestration_cycle(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Verify all cycles completed
        assert len(cycle_results) == 5
        
        # Verify reasonable performance (all cycles under 1 second)
        max_duration = max(result['duration'] for result in cycle_results)
        assert max_duration < 1.0
        
        # Verify all cycles got expected responses
        assert all(result['risk_signal'] == 'HOLD' for result in cycle_results)
        assert all(result['market_trend'] == 'sideways' for result in cycle_results)
    
    def test_high_frequency_database_operations(self, setup_test_database):
        """Test database performance under high frequency operations"""
        
        db_path = setup_test_database
        operation_results = []
        
        def perform_database_operations(thread_id, num_operations=10):
            """Perform multiple database operations in sequence"""
            start_time = time.time()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for i in range(num_operations):
                # Insert a trade record
                cursor.execute("""
                    INSERT INTO paper_trades 
                    (trade_id, symbol, side, quantity, price, total, signal_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"perf_trade_{thread_id}_{i}", "BTCUSDT", "BUY", 0.01, 50000.0, 500.0, "PERFORMANCE_TEST"))
                
                # Update portfolio
                cursor.execute("""
                    UPDATE paper_portfolio 
                    SET usdc_balance = usdc_balance - 500,
                        btc_balance = btc_balance + 0.01
                    WHERE id = 1
                """)
            
            conn.commit()
            conn.close()
            
            end_time = time.time()
            operation_results.append({
                'thread_id': thread_id,
                'duration': end_time - start_time,
                'operations': num_operations
            })
        
        # Run concurrent database operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(perform_database_operations, i, 20) for i in range(3)]
            for future in futures:
                future.result()
        
        # Verify all operations completed
        assert len(operation_results) == 3
        
        # Verify reasonable performance (under 2 seconds per thread)
        max_duration = max(result['duration'] for result in operation_results)
        assert max_duration < 2.0
        
        # Verify database consistency
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE signal_type = 'PERFORMANCE_TEST'")
        trade_count = cursor.fetchone()[0]
        assert trade_count == 60  # 3 threads × 20 operations each
        conn.close()