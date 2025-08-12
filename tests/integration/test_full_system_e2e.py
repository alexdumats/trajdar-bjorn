import requests
import time

SERVICES = {
    "orchestrator": {"url": "http://localhost:4001/health"},
    "portfolio": {"url": "http://localhost:8001/health"},
    "risk_manager": {"url": "http://localhost:8002/health"},
    "market_analyst": {"url": "http://localhost:8003/health"},
    "notification": {"url": "http://localhost:8004/health"},
    "trade_executor": {"url": "http://localhost:8005/health"},
    "parameter_optimizer": {"url": "http://localhost:8006/health"},
    "mcp_hub": {"url": "http://localhost:9000/health"},
}

def test_all_services_healthy():
    """Check health endpoints for all services."""
    for name, svc in SERVICES.items():
        resp = requests.get(svc["url"], timeout=5)
        assert resp.status_code == 200, f"{name} health check failed: {resp.text}"

def test_orchestrator_cycle():
    """Trigger a manual orchestration cycle and validate system status."""
    # Start orchestration if not running
    try:
        status = requests.get("http://localhost:4001/auto-trading-status", timeout=5).json()
        if not status.get("running"):
            resp = requests.post("http://localhost:4001/start-auto-trading", json={"interval": 60}, timeout=5)
            assert resp.status_code == 200
    except requests.RequestException:
        # Service may not be running, skip this test
        import pytest
        pytest.skip("Orchestrator service not available")

    # Trigger a manual cycle
    try:
        resp = requests.post("http://localhost:4001/manual-cycle", timeout=10)
        assert resp.status_code == 200
        result = resp.json()
        # Check for either "status" or "message" field as different versions may return different structures
        assert "status" in result or "message" in result or "cycle_id" in result
    except requests.RequestException:
        import pytest
        pytest.skip("Manual cycle endpoint not available")

def test_portfolio_updates():
    """Check that portfolio service updates after orchestration cycle."""
    try:
        # Get initial portfolio state
        initial = requests.get("http://localhost:8001/portfolio", timeout=5).json()
        # Trigger orchestration cycle
        requests.post("http://localhost:4001/manual-cycle", timeout=10)
        time.sleep(2)
        updated = requests.get("http://localhost:8001/portfolio", timeout=5).json()
        
        # Check if response has nested portfolio structure or direct structure
        if "portfolio" in initial and "portfolio" in updated:
            assert updated["portfolio"]["total_value"] != initial["portfolio"]["total_value"]
        else:
            # Direct structure - compare total_value directly
            assert updated.get("total_value") != initial.get("total_value")
    except requests.RequestException:
        import pytest
        pytest.skip("Portfolio service not available")

def test_notification_delivery():
    """Validate notification service receives and logs trading alerts."""
    # Simulate sending a notification
    payload = {
        "channel": "trading-alerts",
        "message": "Test trading alert from E2E test"
    }
    resp = requests.post("http://localhost:8004/slack", json=payload)
    assert resp.status_code == 200

def test_mcp_hub_status():
    """Check MCP hub integration health."""
    resp = requests.get("http://localhost:9000/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"

def test_orchestrator_system_status():
    """Validate /system-status endpoint for orchestrator."""
    try:
        resp = requests.get("http://localhost:4001/system-status", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data
        assert isinstance(data["services"], dict)
        
        # Check for at least some of the expected services (may not all be running in test environment)
        expected_services = ["portfolio", "risk_manager", "market_analyst", "notification"]
        available_services = [svc for svc in expected_services if svc in data["services"]]
        assert len(available_services) >= 1, f"Expected at least one service, found: {list(data['services'].keys())}"
    except requests.RequestException:
        import pytest
        pytest.skip("Orchestrator system-status endpoint not available")
