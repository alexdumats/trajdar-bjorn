"""
Unit tests for Slack Webhook Logger
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.slack_webhook_logger import SlackWebhookLogger, SlackWebhookLoggerSync


class TestSlackWebhookLogger:
    """Test suite for SlackWebhookLogger"""
    
    def test_initialization(self):
        """Test initialization with different parameters"""
        # Test with explicit webhook URL
        webhook_url = "https://hooks.slack.com/services/test/webhook"
        logger = SlackWebhookLogger("test_agent", webhook_url)
        assert logger.agent_id == "test_agent"
        assert logger.webhook_url == webhook_url
        assert logger.session is None
        
        # Test with environment variable
        with patch.dict('os.environ', {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/env/webhook'}):
            logger = SlackWebhookLogger("test_agent")
            assert logger.webhook_url == 'https://hooks.slack.com/services/env/webhook'
    
    def test_get_agent_emoji(self):
        """Test _get_agent_emoji method"""
        # Test known agent IDs
        logger = SlackWebhookLogger("orchestrator")
        assert logger._get_agent_emoji() == ":robot_face:"
        
        logger = SlackWebhookLogger("portfolio")
        assert logger._get_agent_emoji() == ":moneybag:"
        
        logger = SlackWebhookLogger("signal")
        assert logger._get_agent_emoji() == ":chart_with_upwards_trend:"
        
        # Test unknown agent ID
        logger = SlackWebhookLogger("unknown_agent")
        assert logger._get_agent_emoji() == ":gear:"
    
    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test _get_session method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # First call should create a new session
        session = await logger._get_session()
        assert session is not None
        assert logger.session is not None
        
        # Second call should return the same session
        session2 = await logger._get_session()
        assert session2 is session
        
        # Clean up
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test send_message method - success case"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the session and response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Patch the _get_session method
        with patch.object(logger, '_get_session', return_value=mock_session):
            result = await logger.send_message("Test message")
            
            # Verify the result
            assert result is True
            
            # Verify the session was called correctly
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args[0]
            assert call_args[0] == "https://example.com"
            
            # Verify the payload
            payload = mock_session.post.call_args[1]['json']
            assert payload["text"] == "Test message"
            assert payload["username"] == "Test_Agent Agent"
            assert "icon_emoji" in payload
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Test send_message method - failure case"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the session and response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 500
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Patch the _get_session method
        with patch.object(logger, '_get_session', return_value=mock_session):
            result = await logger.send_message("Test message")
            
            # Verify the result
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_message_exception(self):
        """Test send_message method - exception case"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the session to raise an exception
        mock_session = MagicMock()
        mock_session.post.side_effect = Exception("Test exception")
        
        # Patch the _get_session method
        with patch.object(logger, '_get_session', return_value=mock_session):
            result = await logger.send_message("Test message")
            
            # Verify the result
            assert result is False
    
    @pytest.mark.asyncio
    async def test_log_activity(self):
        """Test log_activity method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the send_message method
        with patch.object(logger, 'send_message', return_value=True) as mock_send:
            # Test with minimal details
            result = await logger.log_activity("info", {"message": "Test info"})
            assert result is True
            
            # Verify send_message was called with correct parameters
            mock_send.assert_called_once()
            text_arg = mock_send.call_args[0][0]
            blocks_arg = mock_send.call_args[0][1]
            
            assert "INFO" in text_arg
            assert len(blocks_arg) >= 2  # Should have at least header and fields sections
            
            # Test with additional details
            mock_send.reset_mock()
            details = {
                "price": 50000.0,
                "quantity": 0.1,
                "total": 5000.0,
                "status": "completed"
            }
            await logger.log_activity("trade", details)
            
            # Verify details were included in blocks
            blocks_arg = mock_send.call_args[0][1]
            details_text = blocks_arg[2]["text"]["text"] if len(blocks_arg) > 2 else ""
            
            assert "$50,000.00" in details_text  # Formatted price
            assert "0.100000" in details_text     # Formatted quantity
            assert "$5,000.00" in details_text    # Formatted total
            assert "completed" in details_text    # Regular text field
    
    @pytest.mark.asyncio
    async def test_log_trade(self):
        """Test log_trade method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the log_activity method
        with patch.object(logger, 'log_activity', return_value=True) as mock_log:
            # Test basic trade logging
            result = await logger.log_trade("BUY", 0.1, 50000.0, 5000.0)
            assert result is True
            
            # Verify log_activity was called with correct parameters
            mock_log.assert_called_once()
            activity_type = mock_log.call_args[0][0]
            details = mock_log.call_args[0][1]
            level = mock_log.call_args[0][2]
            
            assert activity_type == "trade"
            assert details["side"] == "BUY"
            assert details["quantity"] == 0.1
            assert details["price"] == 50000.0
            assert details["total"] == 5000.0
            assert "timestamp" in details
            assert level == "info"
            
            # Test with additional details
            mock_log.reset_mock()
            additional = {"signal_type": "RSI_OVERSOLD", "confidence": 0.85}
            await logger.log_trade("BUY", 0.1, 50000.0, 5000.0, additional)
            
            details = mock_log.call_args[0][1]
            assert details["signal_type"] == "RSI_OVERSOLD"
            assert details["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_log_signal(self):
        """Test log_signal method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the log_activity method
        with patch.object(logger, 'log_activity', return_value=True) as mock_log:
            # Test basic signal logging
            result = await logger.log_signal("BUY", 0.75, "RSI oversold")
            assert result is True
            
            # Verify log_activity was called with correct parameters
            mock_log.assert_called_once()
            activity_type = mock_log.call_args[0][0]
            details = mock_log.call_args[0][1]
            
            assert activity_type == "signal"
            assert details["signal_type"] == "BUY"
            assert details["confidence"] == "75.0%"
            assert details["reason"] == "RSI oversold"
            assert "timestamp" in details
    
    @pytest.mark.asyncio
    async def test_log_error(self):
        """Test log_error method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the log_activity method
        with patch.object(logger, 'log_activity', return_value=True) as mock_log:
            # Test error logging
            result = await logger.log_error("Test error")
            assert result is True
            
            # Verify log_activity was called with correct parameters
            mock_log.assert_called_once()
            activity_type = mock_log.call_args[0][0]
            details = mock_log.call_args[0][1]
            level = mock_log.call_args[0][2]
            
            assert activity_type == "error"
            assert details["error_message"] == "Test error"
            assert level == "error"
    
    @pytest.mark.asyncio
    async def test_log_info(self):
        """Test log_info method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the log_activity method
        with patch.object(logger, 'log_activity', return_value=True) as mock_log:
            # Test info logging
            result = await logger.log_info("Test info")
            assert result is True
            
            # Verify log_activity was called with correct parameters
            mock_log.assert_called_once()
            activity_type = mock_log.call_args[0][0]
            details = mock_log.call_args[0][1]
            level = mock_log.call_args[0][2]
            
            assert activity_type == "info"
            assert details["message"] == "Test info"
            assert level == "info"
    
    @pytest.mark.asyncio
    async def test_log_success(self):
        """Test log_success method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the log_activity method
        with patch.object(logger, 'log_activity', return_value=True) as mock_log:
            # Test success logging
            result = await logger.log_success("Test success")
            assert result is True
            
            # Verify log_activity was called with correct parameters
            mock_log.assert_called_once()
            activity_type = mock_log.call_args[0][0]
            details = mock_log.call_args[0][1]
            level = mock_log.call_args[0][2]
            
            assert activity_type == "success"
            assert details["message"] == "Test success"
            assert level == "success"
    
    @pytest.mark.asyncio
    async def test_send_heartbeat(self):
        """Test send_heartbeat method"""
        logger = SlackWebhookLogger("test_agent", "https://example.com")
        
        # Mock the log_activity method
        with patch.object(logger, 'log_activity', return_value=True) as mock_log:
            # Test heartbeat
            result = await logger.send_heartbeat()
            assert result is True
            
            # Verify log_activity was called with correct parameters
            mock_log.assert_called_once()
            activity_type = mock_log.call_args[0][0]
            details = mock_log.call_args[0][1]
            
            assert activity_type == "heartbeat"
            assert details["status"] == "alive"
            
            # Test with metrics
            mock_log.reset_mock()
            metrics = {"cpu": 25, "memory": 512}
            await logger.send_heartbeat("running", metrics)
            
            details = mock_log.call_args[0][1]
            assert details["status"] == "running"
            assert details["cpu"] == 25
            assert details["memory"] == 512


class TestSlackWebhookLoggerSync:
    """Test suite for SlackWebhookLoggerSync"""
    
    def test_initialization(self):
        """Test initialization"""
        webhook_url = "https://hooks.slack.com/services/test/webhook"
        logger = SlackWebhookLoggerSync("test_agent", webhook_url)
        
        assert logger.async_logger.agent_id == "test_agent"
        assert logger.async_logger.webhook_url == webhook_url
    
    def test_run_async_with_running_loop(self):
        """Test _run_async method with running loop"""
        logger = SlackWebhookLoggerSync("test_agent", "https://example.com")
        
        # Mock asyncio.get_event_loop and asyncio.create_task
        with patch('asyncio.get_event_loop') as mock_get_loop, \
             patch('asyncio.create_task') as mock_create_task:
            
            # Mock loop.is_running to return True
            mock_loop = MagicMock()
            mock_loop.is_running.return_value = True
            mock_get_loop.return_value = mock_loop
            
            # Create a mock coroutine
            mock_coro = MagicMock()
            
            # Call _run_async
            result = logger._run_async(mock_coro)
            
            # Verify create_task was called
            mock_create_task.assert_called_once_with(mock_coro)
            assert result is None
    
    def test_run_async_without_running_loop(self):
        """Test _run_async method without running loop"""
        logger = SlackWebhookLoggerSync("test_agent", "https://example.com")
        
        # Mock asyncio.get_event_loop
        with patch('asyncio.get_event_loop') as mock_get_loop:
            # Mock loop.is_running to return False
            mock_loop = MagicMock()
            mock_loop.is_running.return_value = False
            mock_loop.run_until_complete.return_value = "test_result"
            mock_get_loop.return_value = mock_loop
            
            # Create a mock coroutine
            mock_coro = MagicMock()
            
            # Call _run_async
            result = logger._run_async(mock_coro)
            
            # Verify run_until_complete was called
            mock_loop.run_until_complete.assert_called_once_with(mock_coro)
            assert result == "test_result"
    
    def test_run_async_no_event_loop(self):
        """Test _run_async method with no event loop"""
        logger = SlackWebhookLoggerSync("test_agent", "https://example.com")
        
        # Mock asyncio.get_event_loop to raise RuntimeError
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No event loop")), \
             patch('asyncio.run', return_value="test_result") as mock_run:
            
            # Create a mock coroutine
            mock_coro = MagicMock()
            
            # Call _run_async
            result = logger._run_async(mock_coro)
            
            # Verify asyncio.run was called
            mock_run.assert_called_once_with(mock_coro)
            assert result == "test_result"
    
    def test_sync_methods(self):
        """Test synchronous wrapper methods"""
        logger = SlackWebhookLoggerSync("test_agent", "https://example.com")
        
        # Mock _run_async method
        with patch.object(logger, '_run_async') as mock_run_async:
            # Test log_activity
            logger.log_activity("info", {"message": "Test"})
            assert mock_run_async.call_count == 1
            
            # Test log_error
            logger.log_error("Test error")
            assert mock_run_async.call_count == 2
            
            # Test log_info
            logger.log_info("Test info")
            assert mock_run_async.call_count == 3
            
            # Test log_trade
            logger.log_trade("BUY", 0.1, 50000.0, 5000.0)
            assert mock_run_async.call_count == 4
            
            # Test send_heartbeat
            logger.send_heartbeat()
            assert mock_run_async.call_count == 5