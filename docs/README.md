# AI Multi-Agent Trading System - Documentation

## 📁 Documentation Structure

This directory contains comprehensive documentation for the AI Trading System, organized into logical sections for easy navigation.

### 🏗️ Architecture
- **[system_overview.puml](architecture/system_overview.puml)** - High-level system architecture diagram
- **[microservice_interactions.puml](architecture/microservice_interactions.puml)** - Service interaction patterns
- **[data_flow.puml](architecture/data_flow.puml)** - Data flow and integration patterns
- **[agent_boundaries.puml](architecture/agent_boundaries.puml)** - AI agent responsibilities and boundaries

### 📋 API Specifications
- **[orchestrator_api.yaml](schemas/orchestrator_api.yaml)** - Orchestrator service OpenAPI specification
- **[portfolio_api.yaml](schemas/portfolio_api.yaml)** - Portfolio service OpenAPI specification  
- **[risk_manager_api.yaml](schemas/risk_manager_api.yaml)** - Risk Manager service OpenAPI specification

### ⚙️ Configuration Schemas
- **[production_config_schema.json](schemas/production_config_schema.json)** - Main configuration schema
- **[mcp_servers_schema.json](schemas/mcp_servers_schema.json)** - MCP servers configuration schema
- **[trading_parameters_schema.json](schemas/trading_parameters_schema.json)** - Trading parameters schema

### 🗺️ System Mapping
- **[system_map.yaml](schemas/system_map.yaml)** - Centralized external dependency documentation

### 📊 Performance & Operations
- **[PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md)** - Live system performance analysis and metrics
- **[BACKUP_AND_RESTORE.md](BACKUP_AND_RESTORE.md)** - Complete backup and restore procedures
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** - Parameter optimization guide and results

### 🎯 Current System Status
- **Portfolio**: $10,016.21 (+$16.21 profit, +0.16% return)
- **Strategy**: Optimized RSI with proven performance
- **Status**: Active & profitable with 163 completed trades
- **Risk Level**: LOW (conservative optimized parameters)

## 🚀 Quick Start

### Viewing Architecture Diagrams
To view the PlantUML diagrams, you can:
1. Use online PlantUML editor: http://www.plantuml.com/plantuml/uml/
2. Install PlantUML locally: `sudo apt-get install plantuml` (Ubuntu/Debian)
3. Use VS Code with PlantUML extension

### API Documentation
The OpenAPI specifications can be viewed using:
1. Swagger UI: https://editor.swagger.io/
2. Postman (import the YAML files)
3. VS Code with OpenAPI extensions

### Configuration Validation
Use the JSON schemas to validate configuration files:
```bash
# Example with ajv-cli
npm install -g ajv-cli
ajv validate -s docs/schemas/production_config_schema.json -d config/production_config.yaml
```

## 📖 Additional Documentation

For more detailed information, see the following files in the project root:
- **README.md** - Main project documentation
- **DEPLOYMENT_GUIDE.md** - Deployment instructions
- **testing_framework.md** - Testing methodology
- **scripts_documentation.md** - Available scripts and tools

## 🔧 Maintenance

### Updating Documentation
When making system changes:
1. Update relevant architecture diagrams
2. Modify API specifications if endpoints change
3. Update configuration schemas for new parameters
4. Review system_map.yaml for new dependencies

### Health Monitoring
Use the health monitoring script to check system status:
```bash
python3 scripts/health_monitor.py --format console
```

### Automated Cleanup
Setup automated maintenance:
```bash
scripts/setup_cleanup_cron.sh install
```

## 📚 Documentation Standards

### Architecture Diagrams
- Use PlantUML for consistency
- Include legend and notes for clarity
- Update diagrams when system components change

### API Documentation
- Follow OpenAPI 3.0.3 specification
- Include comprehensive examples
- Document all error responses

### Configuration
- Provide JSON schemas for all YAML configs
- Include validation rules and constraints
- Document environment variable mappings

---

*Last updated: 2025-08-12*  
*For questions or updates, refer to the project maintainers*