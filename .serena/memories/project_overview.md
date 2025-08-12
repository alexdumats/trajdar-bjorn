# AI Multi-Agent Trading System - Project Overview

## Purpose
This is an enterprise-ready AI trading platform powered by 6 specialized AI agents with Model Context Protocol (MCP) integration for automated cryptocurrency trading on Binance.

## Core Architecture
- **AI Agent-Based System**: 6 specialized AI agents with distinct trading functions
- **MCP Integration**: 16+ MCP servers for enhanced capabilities
- **Live Trading**: Binance integration with real execution capabilities
- **Economic Intelligence**: Federal Reserve data integration
- **Cloud Management**: Automated Hetzner infrastructure management
- **Real-time Alerts**: Slack integration for notifications

## AI Trading Agents
1. **Risk Manager** (Port 8002) - Portfolio protection and risk assessment
2. **Market Analyst** (Port 8003) - Technical and fundamental analysis
3. **Trade Executor** (Port 8005) - Fast trade execution and compliance
4. **Parameter Optimizer** (Port 8006) - Strategy optimization with ML
5. **News Analyst** - Market sentiment and news interpretation
6. **Orchestrator** (Port 8000) - Main coordination & decision making

## Core Services
- **Orchestrator** (8000): Main coordination & decision making
- **Portfolio** (8001): Portfolio management & trade execution
- **Risk Manager** (8002): Risk assessment & protection
- **Market Analyst** (8003): Technical & fundamental analysis
- **Notification** (8004): Slack alerts & notifications
- **Trade Executor** (8005): Fast trade execution
- **Parameter Optimizer** (8006): Strategy optimization
- **MCP Hub** (9000): Central MCP server coordination

## Key Features
- **Trading Modes**: Paper trading (simulation) and live trading
- **Strategies**: RSI, MACD, Bollinger Bands, Multi-Factor AI-optimized
- **Comprehensive Monitoring**: Real-time metrics and alerts
- **Security**: API key management, rate limiting, compliance checks
- **Testing**: 100% pass rate test suite with unit, integration, e2e tests