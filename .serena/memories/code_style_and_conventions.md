# Code Style and Conventions

## Python Code Style
Based on analysis of the orchestrator service and project structure:

### Class Naming
- **Classes**: PascalCase (e.g., `AgentOrchestrator`, `AdvancedBacktestingEngine`)
- **Methods**: snake_case (e.g., `execute_orchestration_cycle`, `load_config`)
- **Variables**: snake_case (e.g., `is_orchestrating`, `cycle_count`)
- **Constants**: UPPER_SNAKE_CASE (e.g., environment variables)

### Method Structure
- **Async methods**: Extensively used throughout the codebase
- **Type hints**: Used for method parameters and return types (`-> Optional[Dict]`, `-> Dict[str, Any]`)
- **Docstrings**: Present for method descriptions (`"""Execute one complete agent orchestration cycle"""`)

### Configuration Management
- **Environment Variables**: Extensive use with defaults (`os.getenv("ORCHESTRATION_INTERVAL", "60")`)
- **YAML Configuration**: Config files in `config/` directory
- **Path Management**: Relative paths with fallbacks to absolute paths

### Logging Conventions
- **Logger**: Module-level logger with emoji prefixes for different message types
  - ✅ `logger.info("\u2705 Configuration loaded")`
  - ❌ `logger.error("\u274c Failed to load config: {e}")`
  - 🤖 `logger.info("\ud83e\udd16 Agent Orchestrator initialized")`

### Error Handling
- **Try-catch blocks**: Comprehensive exception handling
- **Graceful degradation**: Default values when services fail
- **Error propagation**: Errors collected in result dictionaries

### Service Architecture
- **Port-based services**: Each service runs on dedicated ports (8000-8006, 9000)
- **Health checks**: All services provide `/health` endpoints
- **HTTP client sessions**: Reused aiohttp sessions with timeouts

### File Organization
- **Source code**: `src/` directory with service-specific files
- **Configuration**: `config/` directory with YAML files
- **Tests**: `tests/` with unit, integration, e2e, performance subdirectories
- **Scripts**: `scripts/` for automation and deployment

### Naming Patterns
- **Services**: `{name}_service.py` (e.g., `orchestrator_service.py`)
- **Agents**: Agent-specific directories and files
- **Config files**: Descriptive YAML names (e.g., `production_config.yaml`)

### Dependencies and Imports
- **Standard libraries**: `asyncio`, `os`, `time`, `datetime`
- **Third-party**: FastAPI, aiohttp, requests, pandas
- **Local imports**: Relative imports for project modules