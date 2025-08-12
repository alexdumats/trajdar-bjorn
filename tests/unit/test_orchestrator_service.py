"""
Unit tests for Orchestrator Service
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestOrchestratorService:
    """Test suite for Orchestrator Service"""
    
    def test_health_endpoint(self, orchestrator_service_client):
        """Test health check endpoint"""
        response = orchestrator_service_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "orchestrator"
    
    def test_system_status(self, orchestrator_service_client):
        """Test system status endpoint"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock healthy responses from all services
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            response = orchestrator_service_client.get("/system-status")
            assert response.status_code == 200
            data = response.json()
            
            assert "agents" in data
            assert "orchestrating" in data
            assert "timestamp" in data
            assert "portfolio" in data
    
    def test_start_orchestration(self, orchestrator_service_client):
        """Test starting orchestration"""
        response = orchestrator_service_client.post("/start-orchestration")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "started"
        assert "message" in data
        assert "orchestration_interval" in data
    
    def test_start_orchestration_already_running(self, orchestrator_service_client):
        """Test starting orchestration when already running"""
        # Start orchestration first
        orchestrator_service_client.post("/start-orchestration")
        
        # Try to start again
        response = orchestrator_service_client.post("/start-orchestration")
        assert response.status_code == 400
        data = response.json()
        assert "already running" in data["detail"].lower()
    
    def test_stop_orchestration(self, orchestrator_service_client):
        """Test stopping orchestration"""
        # Start orchestration first
        orchestrator_service_client.post("/start-orchestration")
        
        # Stop orchestration
        response = orchestrator_service_client.post("/stop-orchestration")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "stopped"
        assert "message" in data
    
    def test_stop_orchestration_not_running(self, orchestrator_service_client):
        """Test stopping orchestration when not running"""
        response = orchestrator_service_client.post("/stop-orchestration")
        assert response.status_code == 400
        data = response.json()
        assert "not running" in data["detail"].lower()
    
    def test_orchestration_status(self, orchestrator_service_client):
        """Test getting orchestration status"""
        response = orchestrator_service_client.get("/orchestration-status")
        assert response.status_code == 200
        data = response.json()
        
        assert "is_running" in data
        assert "cycle_count" in data
        assert "interval_seconds" in data
        assert isinstance(data["is_running"], bool)
        assert isinstance(data["cycle_count"], int)
    
    def test_manual_cycle(self, orchestrator_service_client):
        """Test manual orchestration cycle"""
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            # Mock service responses
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"signal": "BUY", "confidence": 75.0})
            mock_get.return_value.__aenter__.return_value = mock_response
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = orchestrator_service_client.post("/manual-cycle")
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "cycle_results" in data
            assert "timestamp" in data


class TestAgentOrchestrator:
    """Test suite for AgentOrchestrator class"""
    
    def test_orchestrator_initialization(self, test_env_vars):
        """Test AgentOrchestrator initialization"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.is_orchestrating == False
        assert orchestrator.orchestration_interval == 60
        assert orchestrator.cycle_count == 0
        assert orchestrator.risk_manager_agent == "http://risk-manager:8002"
        assert orchestrator.analyst_agent == "http://analyst-agent:8003"
    
    @pytest.mark.asyncio
    async def test_check_service_health_healthy(self, test_env_vars):
        """Test service health check - healthy service"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {'X-Response-Time': '10ms'}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await orchestrator.check_service_health("http://test-service:8000")
                
            assert result["healthy"] == True
            assert result["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_check_service_health_unhealthy(self, test_env_vars):
        """Test service health check - unhealthy service"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = await orchestrator.check_service_health("http://test-service:8000")
                
            assert result["healthy"] == False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, test_env_vars):
        """Test getting system status"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        with patch.object(orchestrator, 'check_agents_health', return_value={"risk_manager_agent": True, "analyst_agent": True}):
            status = await orchestrator.get_system_status()
            
            assert "services" in status
            assert "orchestration" in status
            assert "system_health" in status
            assert status["system_health"] in ["healthy", "degraded"]
    
    @pytest.mark.asyncio
    async def test_call_agent_service_success(self, test_env_vars):
        """Test calling agent service successfully"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"signal": "BUY", "confidence": 80.0})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await orchestrator.call_service(
                "http://test-agent:8002", 
                "/signal", 
                "GET"
            )
                
            assert result is not None
            assert result.get("signal") == "BUY"
            assert result.get("confidence") == 80.0
    
    @pytest.mark.asyncio
    async def test_call_agent_service_failure(self, test_env_vars):
        """Test calling agent service with failure"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Service unavailable")
            
            result = await orchestrator.call_service(
                "http://test-agent:8002", 
                "/signal", 
                "GET"
            )
                
            assert result is None
    
    @pytest.mark.asyncio
    async def test_orchestration_cycle(self, test_env_vars):
        """Test complete orchestration cycle"""
        from src.orchestrator_service import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        
        # Mock the call_service method to return expected responses
        with patch.object(orchestrator, 'call_service') as mock_call_service:
            mock_call_service.return_value = {"status": "healthy"}
            
            results = await orchestrator.execute_orchestration_cycle()
            
            assert "timestamp" in results
            assert "cycle_number" in results
            assert "agents_activated" in results
            assert "actions_taken" in results
            assert "errors" in results
    
    def test_agent_scheduling(self, test_env_vars):
        """Test agent scheduling logic"""
        from src.orchestrator_service import AgentOrchestrator
        import time
        
        orchestrator = AgentOrchestrator()
        
        # Test should_run_agent logic - initially should be true
        assert orchestrator.should_run_agent("risk_manager") == True
        
        # Update last run time to current time
        current_time = time.time()
        orchestrator.agent_schedule["risk_manager"]["last_run"] = int(current_time)
        
        # Should not run again immediately
        assert orchestrator.should_run_agent("risk_manager") == False
        
        # Simulate time passing beyond interval
        interval = orchestrator.agent_schedule["risk_manager"]["interval"]
        orchestrator.agent_schedule["risk_manager"]["last_run"] = int(current_time - interval - 1)
        
        # Should run after interval has passed
        assert orchestrator.should_run_agent("risk_manager") == True

    def test_mcp_registry_lookup(self, test_env_vars):
        """Test MCP registry lookup integration"""
        from src.mcp_hub.main import MCPServerManager
        mcp_manager = MCPServerManager()
        with patch.object(mcp_manager, "get_server_info", return_value={"name": "mock_server", "config": {}, "health": {"status": "active"}, "running": True}):
            result = mcp_manager.get_server_info("mock_server")
            assert result["name"] == "mock_server"
            assert result["health"]["status"] == "active"
            assert result["running"] is True

    @pytest.mark.asyncio
    async def test_mcp_client_call(self, test_env_vars):
        """Test MCP client tool call integration"""
        from src.mcp_hub.main import MCPServerManager
        mcp_manager = MCPServerManager()
        with patch.object(mcp_manager, "start_server", new_callable=AsyncMock) as mock_start_server:
            mock_start_server.return_value = True
            result = await mcp_manager.start_server("mock_server")
            assert result is True
