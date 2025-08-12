# AI Trading System - Scripts Documentation

## Overview
The AI Trading System includes a comprehensive set of automation scripts for system management, deployment, testing, and maintenance. These scripts ensure consistent operations across different environments and reduce manual intervention.

## Script Directory Structure
```
scripts/
├── check_agents.sh                 # Health check for all agents
├── claude_code_setup.sh           # Claude code environment setup
├── cleanup_mcp_servers.py          # MCP server cleanup
├── cleanup_obsolete_files.py       # Obsolete file removal
├── configure_agent_mcps.py        # Agent MCP configuration
├── deploy_hetzner.sh               # Hetzner cloud deployment
├── deploy_with_mcp.py              # MCP-enabled deployment
├── deployment_readiness_check.sh   # Pre-deployment validation
├── monitor_system.sh              # Real-time system monitoring
├── run_tests.sh                    # Execute test suite
├── setup_hetzner_mcp.sh            # MCP server setup for Hetzner
├── setup_test_environment.sh      # Test environment preparation
├── smoke_test.py                  # Basic system functionality check
├── start_agents.sh                # Launch all AI agents
├── stop_agents.sh                 # Stop all services
└── test_docker_setup.sh          # Docker setup validation
```

## System Management Scripts

### start_agents.sh
**Purpose**: Launch all AI agents with proper scheduling and MCP configurations
**Key Features**:
- Color-coded output for better visibility
- Environment variable loading from .env file
- Service health checking before startup
- Background process management with PID tracking
- Ollama availability checking
- Database initialization
- Sequential agent startup with dependencies
- Comprehensive status reporting

**Process Flow**:
1. Load environment variables
2. Check prerequisites (Ollama, database)
3. Start Risk Manager Agent (port 8002)
4. Start Market/News Analyst Agent (port 8003)
5. Start Trade Executor Agent (port 8005)
6. Start Parameter Optimizer (port 8006)
7. Start supporting services (Portfolio, Notification)
8. Start Agent Orchestrator (port 8000)
9. Display service status and management commands

**Management Commands Provided**:
- Start orchestration: `curl -X POST http://localhost:8000/start-orchestration`
- Stop orchestration: `curl -X POST http://localhost:8000/stop-orchestration`
- System status: `curl http://localhost:8000/system-status`
- Stop all services: `./scripts/stop_agents.sh`

### stop_agents.sh
**Purpose**: Gracefully stop all AI trading services
**Key Features**:
- PID-based process termination
- Graceful shutdown with timeout
- Service status verification
- Cleanup of temporary files
- Color-coded status reporting

**Process Flow**:
1. Check for running services via PID files
2. Send termination signals to processes
3. Wait for graceful shutdown
4. Force kill if necessary
5. Clean up PID files
6. Report shutdown status

### check_agents.sh
**Purpose**: Health check for all AI agents and services
**Key Features**:
- Service availability verification
- Port-based health checking
- Detailed status reporting
- Color-coded output
- JSON-formatted results

**Process Flow**:
1. Check each service port for health endpoint
2. Verify MCP server status
3. Check database connectivity
4. Validate configuration files
5. Report overall system health

### monitor_system.sh
**Purpose**: Real-time system monitoring and alerting
**Key Features**:
- Continuous monitoring loop
- Resource usage tracking
- Service health monitoring
- Alert generation for anomalies
- Log file monitoring
- Performance metric collection

**Process Flow**:
1. Initialize monitoring parameters
2. Start continuous monitoring loop
3. Check service health every interval
4. Monitor system resources (CPU, memory, disk)
5. Generate alerts for issues
6. Log monitoring data

## Deployment Scripts

### deploy_hetzner.sh
**Purpose**: Automated deployment to Hetzner cloud infrastructure
**Key Features**:
- Server provisioning
- Docker installation and configuration
- Service deployment
- SSL certificate setup
- Load balancer configuration
- Monitoring setup

**Process Flow**:
1. Authenticate with Hetzner Cloud API
2. Provision server instances
3. Configure networking
4. Install Docker and dependencies
5. Deploy services via docker-compose
6. Configure SSL certificates
7. Set up monitoring and alerting
8. Verify deployment success

### setup_hetzner_mcp.sh
**Purpose**: MCP server setup for Hetzner cloud deployment
**Key Features**:
- MCP server installation
- Configuration file generation
- Service registration
- Health check setup
- Performance optimization

**Process Flow**:
1. Install MCP server dependencies
2. Download and configure MCP servers
3. Generate configuration files
4. Register services with MCP hub
5. Verify MCP server functionality
6. Set up monitoring for MCP services

### deployment_readiness_check.sh
**Purpose**: Pre-deployment validation and environment checking
**Key Features**:
- System requirement validation
- Dependency checking
- Configuration file validation
- Security check
- Performance benchmarking
- Readiness scoring

**Process Flow**:
1. Check system requirements (CPU, memory, disk)
2. Verify dependencies (Docker, Python, etc.)
3. Validate configuration files
4. Check security settings
5. Run performance benchmarks
6. Generate readiness report

### deploy_with_mcp.py
**Purpose**: MCP-enabled deployment orchestration
**Key Features**:
- MCP server integration
- Automated deployment workflow
- Rollback capabilities
- Progress tracking
- Error handling and recovery

**Process Flow**:
1. Initialize MCP connections
2. Validate deployment configuration
3. Execute deployment steps
4. Monitor deployment progress
5. Handle errors and rollback if needed
6. Generate deployment report

## Testing Scripts

### run_tests.sh
**Purpose**: Execute the complete test suite
**Key Features**:
- Test environment setup
- Parallel test execution
- Coverage reporting
- Result aggregation
- HTML report generation

**Process Flow**:
1. Set up test environment
2. Run unit tests
3. Run integration tests
4. Run end-to-end tests
5. Run performance tests
6. Generate coverage reports
7. Create HTML test report

### setup_test_environment.sh
**Purpose**: Test environment preparation and configuration
**Key Features**:
- Database initialization
- Sample data loading
- Configuration file setup
- Environment variable configuration
- Service mocking setup

**Process Flow**:
1. Create test database
2. Load sample data
3. Generate test configuration files
4. Set up environment variables
5. Start mock services if needed
6. Verify test environment

### smoke_test.py
**Purpose**: Basic system functionality verification
**Key Features**:
- Quick health checks
- Critical path validation
- Service connectivity testing
- Minimal resource usage

**Process Flow**:
1. Check system health endpoints
2. Verify database connectivity
3. Test critical service APIs
4. Validate configuration loading
5. Report smoke test results

### test_docker_setup.sh
**Purpose**: Docker environment validation
**Key Features**:
- Docker daemon check
- Image availability verification
- Volume mounting validation
- Network configuration testing
- Permission checking

**Process Flow**:
1. Verify Docker installation
2. Check Docker daemon status
3. Validate required images
4. Test volume mounting
5. Verify network configuration
6. Check user permissions

## Configuration and Cleanup Scripts

### configure_agent_mcps.py
**Purpose**: Agent MCP configuration management
**Key Features**:
- MCP server configuration generation
- Capability mapping
- Environment variable setup
- Configuration validation

**Process Flow**:
1. Load agent configurations
2. Generate MCP server configurations
3. Set up capability mappings
4. Configure environment variables
5. Validate configurations
6. Apply configurations to services

### cleanup_mcp_servers.py
**Purpose**: MCP server cleanup and maintenance
**Key Features**:
- Orphaned process cleanup
- Temporary file removal
- Cache clearing
- Log rotation
- Resource deallocation

**Process Flow**:
1. Identify running MCP processes
2. Terminate unnecessary processes
3. Clean up temporary files
4. Clear caches and logs
5. Release system resources
6. Generate cleanup report

### cleanup_obsolete_files.py
**Purpose**: Obsolete file and data removal
**Key Features**:
- Log file rotation
- Database cleanup
- Temporary file removal
- Backup management
- Disk space optimization

**Process Flow**:
1. Identify obsolete files
2. Archive important data
3. Remove temporary files
4. Clean up old logs
5. Optimize database storage
6. Report cleanup results

### claude_code_setup.sh
**Purpose**: Claude code environment setup
**Key Features**:
- Development environment configuration
- Code quality tool setup
- IDE integration
- Documentation generation
- Testing framework setup

**Process Flow**:
1. Install development dependencies
2. Configure code quality tools
3. Set up IDE integrations
4. Generate documentation
5. Initialize testing framework
6. Verify development environment

## Automation Patterns

### Error Handling
- Try-catch blocks for Python scripts
- Exit code checking for shell scripts
- Graceful degradation
- Rollback mechanisms
- Detailed error logging

### Logging and Monitoring
- Structured logging
- Color-coded console output
- File-based logging
- Performance metrics collection
- Alert generation

### Configuration Management
- Environment variable support
- Configuration file templates
- Runtime parameter validation
- Secure credential handling
- Configuration inheritance

### Process Management
- Background process execution
- PID file management
- Graceful shutdown handling
- Resource cleanup
- Process monitoring

## Best Practices Implemented

### Security
- Secure credential handling
- Environment variable isolation
- File permission management
- Input validation
- Audit logging

### Reliability
- Idempotent operations
- Graceful error handling
- Rollback capabilities
- Health checking
- Status reporting

### Maintainability
- Modular script design
- Clear documentation
- Consistent naming conventions
- Configuration separation
- Version control friendly

### Performance
- Efficient resource usage
- Parallel processing where appropriate
- Caching strategies
- Progress tracking
- Performance monitoring

## Usage Guidelines

### Development Workflow
1. Set up development environment: `./scripts/claude_code_setup.sh`
2. Configure test environment: `./scripts/setup_test_environment.sh`
3. Run tests: `./scripts/run_tests.sh`
4. Verify with smoke test: `./scripts/smoke_test.py`

### Deployment Workflow
1. Check deployment readiness: `./scripts/deployment_readiness_check.sh`
2. Deploy to Hetzner: `./scripts/deploy_hetzner.sh`
3. Set up MCP servers: `./scripts/setup_hetzner_mcp.sh`
4. Configure agents: `./scripts/configure_agent_mcps.py`

### Operations Workflow
1. Start system: `./scripts/start_agents.sh`
2. Monitor system: `./scripts/monitor_system.sh`
3. Check health: `./scripts/check_agents.sh`
4. Stop system: `./scripts/stop_agents.sh`

### Maintenance Workflow
1. Run cleanup: `./scripts/cleanup_mcp_servers.py`
2. Remove obsolete files: `./scripts/cleanup_obsolete_files.py`
3. Validate Docker setup: `./scripts/test_docker_setup.sh`