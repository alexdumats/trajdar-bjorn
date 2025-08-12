[1m============================= test session starts ==============================[0m
platform darwin -- Python 3.10.12, pytest-8.1.1, pluggy-1.6.0 -- /Users/alexdumats/.pyenv/versions/3.10.12/bin/python3.10
cachedir: .pytest_cache
metadata: {'Python': '3.10.12', 'Platform': 'macOS-14.7.5-arm64-arm-64bit', 'Packages': {'pytest': '8.1.1', 'pluggy': '1.6.0'}, 'Plugins': {'asyncio': '0.23.8', 'html': '4.1.1', 'xdist': '3.8.0', 'timeout': '2.4.0', 'dash': '2.17.1', 'metadata': '3.1.1', 'cov': '6.2.1', 'mock': '3.14.1', 'anyio': '3.7.1', 'Faker': '37.4.2', 'profiling': '1.8.1'}}
rootdir: /Users/alexdumats/trajdar_bjorn
configfile: pytest.ini
plugins: asyncio-0.23.8, html-4.1.1, xdist-3.8.0, timeout-2.4.0, dash-2.17.1, metadata-3.1.1, cov-6.2.1, mock-3.14.1, anyio-3.7.1, Faker-37.4.2, profiling-1.8.1
asyncio: mode=auto
[1mcollecting ... [0m
[1m----------------------------- live log collection ------------------------------[0m
2025-08-12 09:44:32 [[31m[1m   ERROR[0m] src.notification_service: ❌ Failed to load config: [Errno 2] No such file or directory: '/app/config/production_config.yaml'
2025-08-12 09:44:32 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
2025-08-12 09:44:32 [[32m    INFO[0m] root: ✅ Loaded trading config from /Users/alexdumats/trajdar_bjorn/tests/../config/trading_parameters.yaml
2025-08-12 09:44:32 [[32m    INFO[0m] root: ✅ Merged production config from /Users/alexdumats/trajdar_bjorn/tests/../config/production_config.yaml
collected 116 items

tests/e2e/test_trading_workflows.py::TestCompleteAutomatedTradingWorkflow::test_full_automated_trading_cycle [32mPASSED[0m[32m [  0%][0m
tests/e2e/test_trading_workflows.py::TestCompleteAutomatedTradingWorkflow::test_risk_based_trade_rejection_workflow [32mPASSED[0m[33m [  1%][0m
tests/e2e/test_trading_workflows.py::TestCompleteAutomatedTradingWorkflow::test_market_conditions_override_workflow [32mPASSED[0m[33m [  2%][0m
tests/e2e/test_trading_workflows.py::TestErrorHandlingWorkflows::test_service_failure_recovery_workflow [32mPASSED[0m[33m [  3%][0m
tests/e2e/test_trading_workflows.py::TestErrorHandlingWorkflows::test_database_transaction_rollback_workflow [31mFAILED[0m[31m [  4%][0m
tests/e2e/test_trading_workflows.py::TestPerformanceWorkflows::test_concurrent_orchestration_cycles [32mPASSED[0m[31m [  5%][0m
tests/e2e/test_trading_workflows.py::TestPerformanceWorkflows::test_high_frequency_database_operations [31mFAILED[0m[31m [  6%][0m
tests/integration/test_full_system_e2e.py::test_all_services_healthy [32mPASSED[0m[31m [  6%][0m
tests/integration/test_full_system_e2e.py::test_orchestrator_cycle [31mFAILED[0m[31m [  7%][0m
tests/integration/test_full_system_e2e.py::test_portfolio_updates [31mFAILED[0m[31m [  8%][0m
tests/integration/test_full_system_e2e.py::test_notification_delivery [32mPASSED[0m[31m [  9%][0m
tests/integration/test_full_system_e2e.py::test_mcp_hub_status [32mPASSED[0m[31m    [ 10%][0m
tests/integration/test_service_interactions.py::TestServiceInteractions::test_orchestrator_to_risk_manager_communication [32mPASSED[0m[31m [ 11%][0m
tests/integration/test_service_interactions.py::TestServiceInteractions::test_orchestrator_to_portfolio_trade_execution [32mPASSED[0m[31m [ 12%][0m
tests/integration/test_service_interactions.py::TestServiceInteractions::test_portfolio_to_notification_service_flow [32mPASSED[0m[31m [ 12%][0m
tests/integration/test_service_interactions.py::TestServiceInteractions::test_complete_trading_cycle_integration [32mPASSED[0m[31m [ 13%][0m
tests/integration/test_service_interactions.py::TestServiceHealthChecks::test_orchestrator_health_check_all_services [32mPASSED[0m[31m [ 14%][0m
tests/integration/test_service_interactions.py::TestServiceHealthChecks::test_service_failure_handling [32mPASSED[0m[31m [ 15%][0m
tests/integration/test_service_interactions.py::TestDatabaseInteractions::test_portfolio_database_consistency [32mPASSED[0m[31m [ 16%][0m
tests/integration/test_service_interactions.py::TestDatabaseInteractions::test_concurrent_database_access [31mFAILED[0m[31m [ 17%][0m
tests/performance/test_load_performance.py::TestServiceLoadTesting::test_portfolio_service_load [31mFAILED[0m[31m [ 18%][0m
tests/performance/test_load_performance.py::TestServiceLoadTesting::test_orchestrator_service_load [33mSKIPPED[0m[31m [ 18%][0m
tests/performance/test_load_performance.py::TestServiceLoadTesting::test_database_concurrent_access_performance [32mPASSED[0m[31m [ 19%][0m
tests/performance/test_load_performance.py::TestSystemStressTests::test_sustained_high_load [33mSKIPPED[0m[31m [ 20%][0m
tests/performance/test_load_performance.py::TestSystemStressTests::test_memory_usage_stability [32mPASSED[0m[31m [ 21%][0m
tests/performance/test_load_performance.py::TestFailureRecoveryPerformance::test_graceful_degradation [32mPASSED[0m[31m [ 22%][0m
tests/performance/test_load_performance.py::TestFailureRecoveryPerformance::test_recovery_time_performance [32mPASSED[0m[31m [ 23%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_initialization 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
[31mFAILED[0m[31m                                                                   [ 24%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_load_config 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
[31mFAILED[0m[31m                                                                   [ 25%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_load_config_failure 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.notification_service: ❌ Failed to load config: [Errno 2] No such file or directory: '/nonexistent/config.yaml'
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
[32mPASSED[0m[31m                                                                   [ 25%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_send_slack_message_success 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Slack message sent to #trading-alerts
[31mFAILED[0m[31m                                                                   [ 26%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_send_slack_message_disabled 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
2025-08-12 09:45:26 [[33m WARNING[0m] src.notification_service: 📢 Slack notifications disabled or webhook not configured
[32mPASSED[0m[31m                                                                   [ 27%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_send_slack_message_failure 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.notification_service: ❌ Failed to send Slack message: Connection error
[32mPASSED[0m[31m                                                                   [ 28%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_send_trade_alert 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
[32mPASSED[0m[31m                                                                   [ 29%][0m
tests/unit/test_notification_service.py::TestNotificationManager::test_send_trade_alert_invalid_data 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.notification_service: 📢 Notification Manager initialized
[32mPASSED[0m[31m                                                                   [ 30%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_health_endpoint 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/health "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 31%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_send_slack_notification 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/slack "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 31%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_send_slack_notification_error 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.notification_service: ❌ Error sending Slack notification: Test error
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/slack "HTTP/1.1 500 Internal Server Error"
[32mPASSED[0m[31m                                                                   [ 32%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_send_trade_alert 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/trade_alert "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 33%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_send_trade_alert_error 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.notification_service: ❌ Error sending trade alert: Test error
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/trade_alert "HTTP/1.1 500 Internal Server Error"
[32mPASSED[0m[31m                                                                   [ 34%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_send_test_notification 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/test "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 35%][0m
tests/unit/test_notification_service.py::TestNotificationServiceAPI::test_send_test_notification_error 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.notification_service: ❌ Error sending test notification: Test error
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/test "HTTP/1.1 500 Internal Server Error"
[32mPASSED[0m[31m                                                                   [ 36%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_health_endpoint 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] orchestrator_message_queue: ✅ Connected to Redis message queue for orchestrator
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/health "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 37%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_system_status 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/system-status "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 37%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_start_orchestration 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent orchestration started (interval: 60s)
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.orchestrator_service: ❌ Service call failed http://notification-service:8004/slack: Event loop is closed
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Starting agent orchestration (interval: 60s)
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/start-orchestration "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 38%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_start_orchestration_already_running 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/start-orchestration "HTTP/1.1 400 Bad Request"
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/start-orchestration "HTTP/1.1 400 Bad Request"
[32mPASSED[0m[31m                                                                   [ 39%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_stop_orchestration 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/start-orchestration "HTTP/1.1 400 Bad Request"
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ⏹️ Agent orchestration stopped and client sessions closed
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.orchestrator_service: ❌ Service call failed http://notification-service:8004/slack: Cannot connect to host notification-service:8004 ssl:default [nodename nor servname provided, or not known]
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/stop-orchestration "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 40%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_stop_orchestration_not_running 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/stop-orchestration "HTTP/1.1 400 Bad Request"
[32mPASSED[0m[31m                                                                   [ 41%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_orchestration_status 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/orchestration-status "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 42%][0m
tests/unit/test_orchestrator_service.py::TestOrchestratorService::test_manual_cycle 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Orchestration cycle 1 completed in 0.00s
2025-08-12 09:45:26 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/manual-cycle "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 43%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_orchestrator_initialization 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
[32mPASSED[0m[31m                                                                   [ 43%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_check_service_health_healthy 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] asyncio: Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x12e76c250>
[32mPASSED[0m[31m                                                                   [ 44%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_check_service_health_unhealthy 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
[32mPASSED[0m[31m                                                                   [ 45%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_get_system_status 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] asyncio: Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x12e50ddb0>
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
[32mPASSED[0m[31m                                                                   [ 46%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_call_agent_service_success 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] asyncio: Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x12e77a8c0>
[32mPASSED[0m[31m                                                                   [ 47%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_call_agent_service_failure 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] src.orchestrator_service: ❌ Service call failed http://test-agent:8002/signal: Service unavailable
[32mPASSED[0m[31m                                                                   [ 48%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_orchestration_cycle 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] asyncio: Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x12e76f4c0>
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Orchestration cycle 1 completed in 0.21s
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] asyncio: Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x12e5ff880>
2025-08-12 09:45:26 [[31m[1m   ERROR[0m] asyncio: Unclosed connector
connections: ['[(<aiohttp.client_proto.ResponseHandler object at 0x12e8c6740>, 160631.841706083)]']
connector: <aiohttp.connector.TCPConnector object at 0x12e5fce20>
[32mPASSED[0m[31m                                                                   [ 49%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_agent_scheduling 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: ✅ Configuration loaded
2025-08-12 09:45:26 [[32m    INFO[0m] src.orchestrator_service: 🤖 Agent Orchestrator initialized with scheduling
[32mPASSED[0m[31m                                                                   [ 50%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_mcp_registry_lookup 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.mcp_hub.main: ✅ Loaded 10 MCP server configurations
2025-08-12 09:45:26 [[32m    INFO[0m] src.mcp_hub.main: ✅ Loaded 10 MCP server configurations
[32mPASSED[0m[31m                                                                   [ 50%][0m
tests/unit/test_orchestrator_service.py::TestAgentOrchestrator::test_mcp_client_call 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] src.mcp_hub.main: ✅ Loaded 10 MCP server configurations
[32mPASSED[0m[31m                                                                   [ 51%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_initialization [32mPASSED[0m[31m [ 52%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_init_database [32mPASSED[0m[31m [ 53%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_get_current_price [32mPASSED[0m[31m [ 54%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_get_klines [32mPASSED[0m[31m [ 55%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_calculate_rsi [32mPASSED[0m[31m [ 56%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_get_portfolio [32mPASSED[0m[31m [ 56%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_update_portfolio [32mPASSED[0m[31m [ 57%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_execute_paper_trade_buy [32mPASSED[0m[31m [ 58%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_execute_paper_trade_sell [32mPASSED[0m[31m [ 59%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_execute_paper_trade_insufficient_balance [31mFAILED[0m[31m [ 60%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_check_stop_loss_take_profit [32mPASSED[0m[31m [ 61%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_get_trading_signal [32mPASSED[0m[31m [ 62%][0m
tests/unit/test_paper_trading_engine.py::TestPaperTradingEngine::test_get_performance_summary [32mPASSED[0m[31m [ 62%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_health_endpoint 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:26 [[32m    INFO[0m] message_queue: ✅ Connected to Redis message queue
2025-08-12 09:45:26 [[32m    INFO[0m] circuit_breaker: 🔧 Circuit breaker 'BinanceAPI' initialized: threshold=3, timeout=30s
2025-08-12 09:45:26 [[32m    INFO[0m] circuit_breaker: 🔧 Circuit breaker 'Database' initialized: threshold=5, timeout=60s
2025-08-12 09:45:27 [[32m    INFO[0m] cache: ✅ Connected to Redis cache
2025-08-12 09:45:27 [[32m    INFO[0m] websocket_service: 🔌 WebSocket service initialized
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Configuration reloaded from centralized config
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💰 Portfolio Manager initialized
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmpsq66zzz_.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/health "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 63%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_get_portfolio 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmp5sjlcste.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/portfolio "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 64%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_execute_trade_buy 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmprbj1jm74.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 🌅 New day started! Daily balance reset to $10000.00
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/execute_trade "HTTP/1.1 200 OK"
[31mFAILED[0m[31m                                                                   [ 65%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_execute_trade_sell 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmpt22o6ggu.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/execute_trade "HTTP/1.1 200 OK"
[31mFAILED[0m[31m                                                                   [ 66%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_execute_trade_insufficient_balance 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmptdtxcur6.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: POST http://testserver/execute_trade "HTTP/1.1 200 OK"
[31mFAILED[0m[31m                                                                   [ 67%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_get_performance_metrics 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmp4uzsbfn7.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] message_queue: 📤 Published message to performance_metrics
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/performance "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 68%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_get_trades_history 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmp_y5vdmst.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/trades "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 68%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_get_positions 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmp3h2p5lvw.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/positions "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 69%][0m
tests/unit/test_portfolio_service.py::TestPortfolioService::test_stop_loss_take_profit_check 
[1m-------------------------------- live log setup --------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmpx5lcko02.db
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/check_stop_loss_take_profit "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 70%][0m
tests/unit/test_portfolio_service.py::TestPortfolioManager::test_portfolio_manager_initialization 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Configuration reloaded from centralized config
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Portfolio initialized with $10000.0 USDC
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💰 Portfolio Manager initialized
[32mPASSED[0m[31m                                                                   [ 71%][0m
tests/unit/test_portfolio_service.py::TestPortfolioManager::test_database_initialization 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Configuration reloaded from centralized config
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Portfolio initialized with $10000.0 USDC
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💰 Portfolio Manager initialized
[32mPASSED[0m[31m                                                                   [ 72%][0m
tests/unit/test_portfolio_service.py::TestPortfolioManager::test_calculate_position_size 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Configuration reloaded from centralized config
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Portfolio initialized with $10000.0 USDC
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💰 Portfolio Manager initialized
[32mPASSED[0m[31m                                                                   [ 73%][0m
tests/unit/test_portfolio_service.py::TestPortfolioManager::test_slack_logging_integration 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Configuration reloaded from centralized config
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: ✅ Portfolio initialized with $10000.0 USDC
2025-08-12 09:45:27 [[32m    INFO[0m] src.portfolio_service: 💰 Portfolio Manager initialized
[32mPASSED[0m[31m                                                                   [ 74%][0m
tests/unit/test_signal_service.py::TestSignalService::test_health_endpoint 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[31m[1m   ERROR[0m] src.signal_service: ❌ Failed to load config: [Errno 2] No such file or directory: '/app/config/production_config.yaml'
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/health "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 75%][0m
tests/unit/test_signal_service.py::TestSignalService::test_get_signal_endpoint 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[31m[1m   ERROR[0m] src.signal_service: ❌ Error fetching price: list indices must be integers or slices, not str
2025-08-12 09:45:27 [[31m[1m   ERROR[0m] src.signal_service: ❌ Error fetching price: list indices must be integers or slices, not str
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/risk-assessment "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 75%][0m
tests/unit/test_signal_service.py::TestSignalService::test_get_indicators_endpoint 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] httpx: HTTP Request: GET http://testserver/rsi "HTTP/1.1 200 OK"
[32mPASSED[0m[31m                                                                   [ 76%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_risk_manager_initialization 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] root: ✅ Loaded trading config from /Users/alexdumats/trajdar_bjorn/config/trading_parameters.yaml
2025-08-12 09:45:27 [[32m    INFO[0m] root: ✅ Merged production config from /Users/alexdumats/trajdar_bjorn/config/production_config.yaml
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 77%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_calculate_rsi 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 78%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_calculate_macd 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 79%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_calculate_bollinger_bands 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 80%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_generate_signal_rsi_oversold 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 81%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_generate_signal_rsi_overbought 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 81%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_get_ai_analysis 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 82%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_fetch_market_data_success 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 83%][0m
tests/unit/test_signal_service.py::TestRiskManagerAgent::test_fetch_market_data_failure 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: ✅ Configuration loaded
2025-08-12 09:45:27 [[32m    INFO[0m] src.signal_service: 🛡️ Risk Manager Agent initialized with mistral7b:latest
[32mPASSED[0m[31m                                                                   [ 84%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_initialization [32mPASSED[0m[31m [ 85%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_get_agent_emoji [32mPASSED[0m[31m [ 86%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_get_session [32mPASSED[0m[31m [ 87%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_send_message_success [32mPASSED[0m[31m [ 87%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_send_message_failure [32mPASSED[0m[31m [ 88%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_send_message_exception 
[1m-------------------------------- live log call ---------------------------------[0m
2025-08-12 09:45:27 [[31m[1m   ERROR[0m] src.slack_webhook_logger: Error sending to Slack webhook: Test exception
[32mPASSED[0m[31m                                                                   [ 89%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_log_activity [32mPASSED[0m[31m [ 90%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_log_trade [32mPASSED[0m[31m [ 91%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_log_signal [32mPASSED[0m[31m [ 92%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_log_error [32mPASSED[0m[31m [ 93%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_log_info [32mPASSED[0m[31m [ 93%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_log_success [32mPASSED[0m[31m [ 94%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLogger::test_send_heartbeat [32mPASSED[0m[31m [ 95%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLoggerSync::test_initialization [32mPASSED[0m[31m [ 96%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLoggerSync::test_run_async_with_running_loop [32mPASSED[0m[31m [ 97%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLoggerSync::test_run_async_without_running_loop [32mPASSED[0m[31m [ 98%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLoggerSync::test_run_async_no_event_loop [32mPASSED[0m[31m [ 99%][0m
tests/unit/test_slack_webhook_logger.py::TestSlackWebhookLoggerSync::test_sync_methods [32mPASSED[0m[31m [100%][0m

=================================== FAILURES ===================================
[31m[1m____ TestErrorHandlingWorkflows.test_database_transaction_rollback_workflow ____[0m
[1m[31mtests/e2e/test_trading_workflows.py[0m:395: in test_database_transaction_rollback_workflow
    [0mcursor.execute([33m"[39;49;00m[33mSELECT usdt_balance, btc_balance FROM paper_portfolio WHERE id = 1[39;49;00m[33m"[39;49;00m)[90m[39;49;00m
[1m[31mE   sqlite3.OperationalError: no such column: usdt_balance[0m
[31m[1m_______ TestPerformanceWorkflows.test_high_frequency_database_operations _______[0m
[1m[31mtests/e2e/test_trading_workflows.py[0m:528: in test_high_frequency_database_operations
    [0mfuture.result()[90m[39;49;00m
[1m[31m../.pyenv/versions/3.10.12/lib/python3.10/concurrent/futures/_base.py[0m:458: in result
    [0m[94mreturn[39;49;00m [96mself[39;49;00m.__get_result()[90m[39;49;00m
[1m[31m../.pyenv/versions/3.10.12/lib/python3.10/concurrent/futures/_base.py[0m:403: in __get_result
    [0m[94mraise[39;49;00m [96mself[39;49;00m._exception[90m[39;49;00m
[1m[31m../.pyenv/versions/3.10.12/lib/python3.10/concurrent/futures/thread.py[0m:58: in run
    [0mresult = [96mself[39;49;00m.fn(*[96mself[39;49;00m.args, **[96mself[39;49;00m.kwargs)[90m[39;49;00m
[1m[31mtests/e2e/test_trading_workflows.py[0m:500: in perform_database_operations
    [0mcursor.execute([33m"""[39;49;00m[33m[39;49;00m
[1m[31mE   sqlite3.OperationalError: database is locked[0m
[31m[1m___________________________ test_orchestrator_cycle ____________________________[0m
[1m[31mtests/integration/test_full_system_e2e.py[0m:33: in test_orchestrator_cycle
    [0m[94massert[39;49;00m result[[33m"[39;49;00m[33mstatus[39;49;00m[33m"[39;49;00m] == [33m"[39;49;00m[33mcompleted[39;49;00m[33m"[39;49;00m[90m[39;49;00m
[1m[31mE   KeyError: 'status'[0m
[31m[1m____________________________ test_portfolio_updates ____________________________[0m
[1m[31mtests/integration/test_full_system_e2e.py[0m:44: in test_portfolio_updates
    [0m[94massert[39;49;00m updated[[33m"[39;49;00m[33mportfolio[39;49;00m[33m"[39;49;00m][[33m"[39;49;00m[33mtotal_value[39;49;00m[33m"[39;49;00m] != initial[[33m"[39;49;00m[33mportfolio[39;49;00m[33m"[39;49;00m][[33m"[39;49;00m[33mtotal_value[39;49;00m[33m"[39;49;00m][90m[39;49;00m
[1m[31mE   KeyError: 'portfolio'[0m
[31m[1m___________ TestDatabaseInteractions.test_concurrent_database_access ___________[0m
[1m[31mtests/integration/test_service_interactions.py[0m:429: in test_concurrent_database_access
    [0m[94massert[39;49;00m success_count >= [94m1[39;49;00m, [33mf[39;49;00m[33m"[39;49;00m[33mAt least one thread should succeed. Results: [39;49;00m[33m{[39;49;00mresults[33m}[39;49;00m[33m"[39;49;00m[90m[39;49;00m
[1m[31mE   AssertionError: At least one thread should succeed. Results: ['Thread 0: Error - no such column: usdt_balance', 'Thread 1: Error - no such column: usdt_balance'][0m
[1m[31mE   assert 0 >= 1[0m
----------------------------- Captured stdout call -----------------------------
Concurrent database access results: ['Thread 0: Error - no such column: usdt_balance', 'Thread 1: Error - no such column: usdt_balance']
[31m[1m______________ TestServiceLoadTesting.test_portfolio_service_load ______________[0m
[1m[31mtests/performance/test_load_performance.py[0m:30: in test_portfolio_service_load
    [0mcursor.execute([33m"""[39;49;00m[33m[39;49;00m
[1m[31mE   sqlite3.OperationalError: no such column: usdt_balance[0m
[31m[1m_________________ TestNotificationManager.test_initialization __________________[0m
[1m[31mtests/unit/test_notification_service.py[0m:67: in test_initialization
    [0m[94massert[39;49;00m manager.webhook_url == [33m"[39;49;00m[33mhttps://hooks.slack.com/services/test/webhook[39;49;00m[33m"[39;49;00m[90m[39;49;00m
[1m[31mE   AssertionError: assert 'https://hook...bc5vxgDNpB6c9' == 'https://hook.../test/webhook'[0m
[1m[31mE     [0m
[1m[31mE     - https://hooks.slack.com/services/test/webhook[0m
[1m[31mE     + https://hooks.slack.com/services/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[0m
------------------------------ Captured log call -------------------------------
[32mINFO    [0m src.notification_service:notification_service.py:60 ✅ Configuration loaded
[32mINFO    [0m src.notification_service:notification_service.py:38 📢 Notification Manager initialized
[31m[1m___________________ TestNotificationManager.test_load_config ___________________[0m
[1m[31mtests/unit/test_notification_service.py[0m:84: in test_load_config
    [0m[94massert[39;49;00m manager.webhook_url == [33m"[39;49;00m[33mhttps://hooks.slack.com/services/test/webhook[39;49;00m[33m"[39;49;00m[90m[39;49;00m
[1m[31mE   AssertionError: assert 'https://hook...bc5vxgDNpB6c9' == 'https://hook.../test/webhook'[0m
[1m[31mE     [0m
[1m[31mE     - https://hooks.slack.com/services/test/webhook[0m
[1m[31mE     + https://hooks.slack.com/services/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[0m
------------------------------ Captured log call -------------------------------
[32mINFO    [0m src.notification_service:notification_service.py:60 ✅ Configuration loaded
[32mINFO    [0m src.notification_service:notification_service.py:38 📢 Notification Manager initialized
[31m[1m___________ TestNotificationManager.test_send_slack_message_success ____________[0m
[1m[31mtests/unit/test_notification_service.py[0m:141: in test_send_slack_message_success
    [0m[94massert[39;49;00m args[[94m0[39;49;00m] == [33m"[39;49;00m[33mhttps://hooks.slack.com/services/test/webhook[39;49;00m[33m"[39;49;00m[90m[39;49;00m
[1m[31mE   AssertionError: assert 'https://hook...bc5vxgDNpB6c9' == 'https://hook.../test/webhook'[0m
[1m[31mE     [0m
[1m[31mE     - https://hooks.slack.com/services/test/webhook[0m
[1m[31mE     + https://hooks.slack.com/services/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[0m
------------------------------ Captured log call -------------------------------
[32mINFO    [0m src.notification_service:notification_service.py:60 ✅ Configuration loaded
[32mINFO    [0m src.notification_service:notification_service.py:38 📢 Notification Manager initialized
[32mINFO    [0m src.notification_service:notification_service.py:90 ✅ Slack message sent to #trading-alerts
[31m[1m_____ TestPaperTradingEngine.test_execute_paper_trade_insufficient_balance _____[0m
[1m[31mtests/unit/test_paper_trading_engine.py[0m:333: in test_execute_paper_trade_insufficient_balance
    [0m[94massert[39;49;00m [33m"[39;49;00m[33mInsufficient USDT balance[39;49;00m[33m"[39;49;00m [95min[39;49;00m result[[33m"[39;49;00m[33merror[39;49;00m[33m"[39;49;00m][90m[39;49;00m
[1m[31mE   AssertionError: assert 'Insufficient USDT balance' in 'Insufficient USDC balance'[0m
----------------------------- Captured stdout call -----------------------------
Database initialized at: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmpbs1tmq1j.db
[31m[1m_________________ TestPortfolioService.test_execute_trade_buy __________________[0m
[1m[31mtests/unit/test_portfolio_service.py[0m:52: in test_execute_trade_buy
    [0m[94massert[39;49;00m data[[33m"[39;49;00m[33msuccess[39;49;00m[33m"[39;49;00m] == [94mTrue[39;49;00m[90m[39;49;00m
[1m[31mE   assert False == True[0m
------------------------------ Captured log setup ------------------------------
[32mINFO    [0m src.portfolio_service:portfolio_service.py:190 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmprbj1jm74.db
------------------------------ Captured log call -------------------------------
[32mINFO    [0m src.portfolio_service:portfolio_service.py:693 🌅 New day started! Daily balance reset to $10000.00
[32mINFO    [0m httpx:_client.py:1026 HTTP Request: POST http://testserver/execute_trade "HTTP/1.1 200 OK"
[31m[1m_________________ TestPortfolioService.test_execute_trade_sell _________________[0m
[1m[31mtests/unit/test_portfolio_service.py[0m:83: in test_execute_trade_sell
    [0m[94massert[39;49;00m data[[33m"[39;49;00m[33msuccess[39;49;00m[33m"[39;49;00m] == [94mTrue[39;49;00m[90m[39;49;00m
[1m[31mE   assert False == True[0m
------------------------------ Captured log setup ------------------------------
[32mINFO    [0m src.portfolio_service:portfolio_service.py:190 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmpt22o6ggu.db
------------------------------ Captured log call -------------------------------
[32mINFO    [0m httpx:_client.py:1026 HTTP Request: POST http://testserver/execute_trade "HTTP/1.1 200 OK"
[31m[1m_________ TestPortfolioService.test_execute_trade_insufficient_balance _________[0m
[1m[31mtests/unit/test_portfolio_service.py[0m:98: in test_execute_trade_insufficient_balance
    [0m[94massert[39;49;00m [33m"[39;49;00m[33mNo BTC to sell[39;49;00m[33m"[39;49;00m [95min[39;49;00m data[[33m"[39;49;00m[33merror[39;49;00m[33m"[39;49;00m][90m[39;49;00m
[1m[31mE   AssertionError: assert 'No BTC to sell' in 'Unsupported trading pair: BTCUSDT'[0m
------------------------------ Captured log setup ------------------------------
[32mINFO    [0m src.portfolio_service:portfolio_service.py:190 💾 Database path reset to: /var/folders/qj/6y14l1l93f56tspq06jf_pwr0000gn/T/tmptdtxcur6.db
------------------------------ Captured log call -------------------------------
[32mINFO    [0m httpx:_client.py:1026 HTTP Request: POST http://testserver/execute_trade "HTTP/1.1 200 OK"
================================ tests coverage ================================
______________ coverage: platform darwin, python 3.10.12-final-0 _______________

Name                                   Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
src/cache.py                             214    141    34%   52-55, 73-86, 95-98, 100-102, 122-123, 129-135, 144-152, 164-181, 193-214, 256-257, 273-274, 286-287, 301-302, 336-343, 350-353, 357-373, 377-392, 401-453, 460-492
src/circuit_breaker.py                   105     55    48%   86-90, 97-103, 107-109, 113-115, 120-123, 127-128, 132-142, 146-148, 152-155, 159, 186-217
src/data_service.py                        9      9     0%   5-18
src/enhanced_mutual_scheduler.py         212    212     0%   8-478
src/market_executor_service.py           187    187     0%   8-406
src/mcp_hub/__init__.py                    1      0   100%
src/mcp_hub/main.py                      173    110    36%   46-48, 52-70, 74-108, 112-123, 127-138, 142-162, 166-191, 195-198, 202-205, 209-215, 224, 232, 242, 247, 252-253, 258-259, 264, 269-270, 275-276, 281-291, 294-295
src/message_queue.py                     128     85    34%   46-49, 72-92, 100, 102-104, 118-169, 173-180, 184-190, 194-200, 215-249
src/notification_service.py              279    166    41%   48, 131-244, 249-272, 279-391, 398-423, 430-454, 461-485, 611-622, 638-639
src/orchestrator_message_queue.py         90     61    32%   39-41, 54-70, 83-106, 110-119, 123-126, 130-133, 137-141, 145-148, 155-194
src/orchestrator_service.py              416    202    51%   36-39, 109, 130-134, 150, 172-173, 233-238, 240-242, 253, 265, 280-300, 331-335, 341-424, 428-536, 547-553, 556-557, 561-625, 670-671, 704-705, 707-708, 824-870, 873-874
src/paper_trading_engine.py              294     56    81%   27-31, 37-40, 207, 233-235, 283-285, 332-336, 381-382, 433-437, 452-453, 468-469, 507-511, 547-580
src/parameter_optimizer_service.py       548    548     0%   8-1322
src/parameter_update_handler.py          313    313     0%   8-607
src/performance_metrics_framework.py     192    192     0%   17-393
src/portfolio_service.py                 518    250    52%   30-34, 62-65, 106-107, 111-119, 222-224, 229-248, 274, 298-299, 309, 316-317, 319-320, 322-323, 328-401, 415-423, 428-438, 443-454, 465, 480-501, 546-601, 608-622, 639-640, 663-664, 677, 697-712, 721, 748-754, 765-771, 796-797, 818-820, 832-834, 842-844, 854-856, 879-881, 904-906, 911-916, 921-926, 931-936, 941-948, 953-958, 963-968, 973-983, 988-993, 996-997
src/profit_monitor_service.py            345    345     0%   13-717
src/signal_service.py                    433    178    59%   51-53, 85-89, 101-103, 115-116, 138-140, 144-148, 188-196, 228-229, 262-274, 283-285, 312-320, 327-328, 333-344, 353-354, 377-380, 386-387, 390-392, 394-396, 404-413, 426-427, 452-457, 498-500, 514-519, 523-543, 560-563, 575-577, 580-582, 586-618, 627-713, 736-738, 743-755, 764-765, 768, 790-792, 797-807, 810-811
src/slack_integration_service.py         395    395     0%   8-885
src/slack_webhook_logger.py              116     11    91%   132, 172, 180, 194, 206-209, 254, 261, 265
src/utils/__init__.py                      0      0   100%
src/utils/config_manager.py              144     54    62%   34, 52-53, 68-70, 103, 153, 165-171, 191, 205, 228-265, 269, 292, 302-303, 307-327, 342, 347, 355, 360-378
src/websocket_client.py                  102    102     0%   7-167
src/websocket_service.py                 116     85    27%   36-40, 48-49, 53-58, 65-80, 84-114, 122-164, 168-175, 179-196, 203-208
--------------------------------------------------------------------
TOTAL                                   5330   3757    30%
Coverage HTML written to dir htmlcov
============================= slowest 10 durations =============================
30.20s call     tests/performance/test_load_performance.py::TestSystemStressTests::test_sustained_high_load
12.62s call     tests/performance/test_load_performance.py::TestFailureRecoveryPerformance::test_recovery_time_performance
5.27s call     tests/e2e/test_trading_workflows.py::TestPerformanceWorkflows::test_high_frequency_database_operations
2.34s call     tests/integration/test_full_system_e2e.py::test_portfolio_updates
0.69s call     tests/integration/test_full_system_e2e.py::test_orchestrator_cycle
0.37s call     tests/performance/test_load_performance.py::TestFailureRecoveryPerformance::test_graceful_degradation
0.36s call     tests/performance/test_load_performance.py::TestSystemStressTests::test_memory_usage_stability
0.35s call     tests/unit/test_portfolio_service.py::TestPortfolioService::test_get_portfolio
0.31s call     tests/integration/test_full_system_e2e.py::test_all_services_healthy
0.27s call     tests/integration/test_full_system_e2e.py::test_notification_delivery
[36m[1m=========================== short test summary info ============================[0m
[31mFAILED[0m tests/e2e/test_trading_workflows.py::[1mTestErrorHandlingWorkflows::test_database_transaction_rollback_workflow[0m - sqlite3.OperationalError: no such column: usdt_balance
[31mFAILED[0m tests/e2e/test_trading_workflows.py::[1mTestPerformanceWorkflows::test_high_frequency_database_operations[0m - sqlite3.OperationalError: database is locked
[31mFAILED[0m tests/integration/test_full_system_e2e.py::[1mtest_orchestrator_cycle[0m - KeyError: 'status'
[31mFAILED[0m tests/integration/test_full_system_e2e.py::[1mtest_portfolio_updates[0m - KeyError: 'portfolio'
[31mFAILED[0m tests/integration/test_service_interactions.py::[1mTestDatabaseInteractions::test_concurrent_database_access[0m - AssertionError: At least one thread should succeed. Results: ['Thread 0: Er...
[31mFAILED[0m tests/performance/test_load_performance.py::[1mTestServiceLoadTesting::test_portfolio_service_load[0m - sqlite3.OperationalError: no such column: usdt_balance
[31mFAILED[0m tests/unit/test_notification_service.py::[1mTestNotificationManager::test_initialization[0m - AssertionError: assert 'https://hook...bc5vxgDNpB6c9' == 'https://hook.../t...
[31mFAILED[0m tests/unit/test_notification_service.py::[1mTestNotificationManager::test_load_config[0m - AssertionError: assert 'https://hook...bc5vxgDNpB6c9' == 'https://hook.../t...
[31mFAILED[0m tests/unit/test_notification_service.py::[1mTestNotificationManager::test_send_slack_message_success[0m - AssertionError: assert 'https://hook...bc5vxgDNpB6c9' == 'https://hook.../t...
[31mFAILED[0m tests/unit/test_paper_trading_engine.py::[1mTestPaperTradingEngine::test_execute_paper_trade_insufficient_balance[0m - AssertionError: assert 'Insufficient USDT balance' in 'Insufficient USDC ba...
[31mFAILED[0m tests/unit/test_portfolio_service.py::[1mTestPortfolioService::test_execute_trade_buy[0m - assert False == True
[31mFAILED[0m tests/unit/test_portfolio_service.py::[1mTestPortfolioService::test_execute_trade_sell[0m - assert False == True
[31mFAILED[0m tests/unit/test_portfolio_service.py::[1mTestPortfolioService::test_execute_trade_insufficient_balance[0m - AssertionError: assert 'No BTC to sell' in 'Unsupported trading pair: BTCUSDT'
[31m=========== [31m[1m13 failed[0m, [32m101 passed[0m, [33m2 skipped[0m, [33m30 warnings[0m[31m in 57.53s[0m[31m ============[0m
