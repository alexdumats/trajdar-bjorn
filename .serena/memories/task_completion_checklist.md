# Task Completion Checklist

When completing development tasks in this AI trading system, follow these steps:

## Pre-Development Checks
- [ ] Verify all required services are healthy: `curl http://localhost:8000/system-status`
- [ ] Ensure test environment is set up: `./scripts/setup_test_environment.sh`
- [ ] Check Python version compatibility: `./scripts/check_python_version.sh`

## During Development
- [ ] Follow established code style and conventions (see code_style_and_conventions memory)
- [ ] Use environment variables for configuration (no hardcoded values)
- [ ] Implement proper error handling with try-catch blocks
- [ ] Add appropriate logging with emoji prefixes (✅ ❌ 🤖)
- [ ] Use type hints for method parameters and return types
- [ ] Follow async/await patterns for service calls

## Testing Requirements
- [ ] Run all tests: `python -m pytest`
- [ ] Ensure 100% pass rate across all test categories:
  - [ ] Unit tests: `python -m pytest tests/unit/`
  - [ ] Integration tests: `python -m pytest tests/integration/`
  - [ ] E2E tests: `python -m pytest tests/e2e/`
- [ ] Add new tests for new functionality
- [ ] Verify test coverage if using pytest-cov

## System Integration
- [ ] Test service health endpoints work
- [ ] Verify service-to-service communication
- [ ] Check MCP server integration: `curl http://localhost:9000/status`
- [ ] Test Slack notifications (if applicable)

## Pre-Deployment Validation
- [ ] Run deployment readiness check: `./scripts/deployment_readiness_check.sh`
- [ ] Verify Docker containers build successfully
- [ ] Test with paper trading mode before live trading
- [ ] Check all environment variables are properly configured

## Documentation Updates
- [ ] Update relevant configuration files if needed
- [ ] Document any new API endpoints or service changes
- [ ] Update memory files if architecture changes

## Final Verification
- [ ] System health check passes: `curl http://localhost:8000/health`
- [ ] All agents are responding: `./scripts/check_agents.sh`
- [ ] Portfolio service operational: `curl http://localhost:8001/portfolio`
- [ ] Risk manager operational: `curl http://localhost:8002/risk-analysis`

## Safe Trading Practices
- [ ] Always test in paper mode first
- [ ] Verify risk limits are properly configured
- [ ] Ensure stop-loss mechanisms are working
- [ ] Monitor system logs after deployment

## Rollback Plan
- [ ] Have backup of database: `cp database/paper_trading.db database/backup_$(date +%Y%m%d).db`
- [ ] Know how to stop orchestration: `curl -X POST http://localhost:8000/stop-orchestration`
- [ ] Can revert to previous Docker images if needed