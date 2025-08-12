# Tech Stack and Dependencies

## Programming Languages
- **Python 3.10+**: Main application language
- **Go 1.19+**: For Slack MCP server
- **Node.js 18+**: For npm-based MCP servers

## Core Python Dependencies
- **FastAPI 0.104.1**: Web framework for REST APIs
- **uvicorn 0.24.0**: ASGI server
- **requests 2.31.0**: HTTP client library
- **aiohttp 3.9.1**: Async HTTP client/server
- **pandas 2.1.3**: Data analysis and manipulation
- **numpy 1.25.2**: Numerical computing
- **python-binance 1.0.19**: Binance API integration
- **PyYAML 6.0.1**: YAML configuration parsing
- **python-dotenv 1.0.0**: Environment variable management

## Testing Framework
- **pytest 8.1.1**: Testing framework
- **pytest configuration**: Comprehensive test discovery, markers, and output

## Communication & Integration
- **websockets 12.0**: WebSocket support
- **slack-sdk 3.27.0**: Slack integration
- **redis 5.0.1**: Caching and message queuing
- **httpx 0.27.0**: Modern HTTP client

## Infrastructure & Deployment
- **Docker & Docker Compose**: Containerization
- **System Requirements**: 4GB RAM minimum, 8GB recommended

## External APIs Required
- **Binance API**: For cryptocurrency trading
- **FRED API**: Federal Reserve economic data (free)
- **Slack API**: For notifications and alerts
- **Hetzner Cloud API**: For infrastructure management
- **Notion API**: Optional documentation integration

## MCP Server Ecosystem (16+ Servers)
### Financial Data & Trading
- Trade Agent MCP, YFinance MCP, Coinpaprika MCP, FRED MCP, SQLite MCP

### AI & Analytics  
- Phoenix ML MCP, Chronulus AI MCP, Optuna MCP

### Infrastructure & Communication
- Slack MCP, Hetzner Cloud MCP